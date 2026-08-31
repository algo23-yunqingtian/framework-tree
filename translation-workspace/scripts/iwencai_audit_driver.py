#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iwencai_audit_driver.py — 同花顺问财「板块组审计」驱动（Step 1，CDP 自动化）

用途：按交接文档 Step 1，把每个品种的 6 个板块组（价格信号/供给/库存/需求/进出口/成本利润）
      各自聚合该板块全部子节点的 divergence 内容 + 审计 Prompt 模板，发进同花顺「新对话」，
      抓取 AI 审计回复落盘 translation-workspace/audit/{品种}/audit_{板块}.md。

与发散驱动的区别：发散是逐节点（1 prompt = 1 节点）；审计是逐板块组（1 prompt = 该板块 N 个节点内容）。

用法：
  python3 iwencai_audit_driver.py --node ZN_价格信号     # 单板块（先证明）
  python3 iwencai_audit_driver.py --all                  # 全量 4品种×6板块=24 轮
  python3 iwencai_audit_driver.py --all --start 2 --end 5 # 区间续跑

产物：translation-workspace/audit/{品种}/audit_{板块}.md
状态：translation-workspace/audit/_audit_state.json（断点续跑）

2026-09-01 关键修复（卡点解决，勿回退）：
  ★ 长文本发送改用 Vue 组件方法 __CI.setText()（ChatInput 组件实例的 setText），
    替代 innerHTML 注入。实测 17KB 注入后 .send-button 正常渲染，点击后编辑器清空=真正发出。
    根因：Quill 只同步 innerHTML 不同步内部 delta 模型，innerHTML 注入长文本点击无效。
    定位组件：深度遍历 DOM 找 __vue__.$options.name === 'ChatInput' 的实例，挂到 window.__CI。
  ★ 发送成功判据：点击 send-button 后编辑器 innerText 长度应回到 1（清空=已发送）。
"""
import argparse, json, os, re, sys, time, glob

BASE = "/home/ubuntu/framework-tree"
IWC_ROOT = os.path.join(BASE, "analysis", "iwencai")
AUDIT_ROOT = os.path.join(BASE, "translation-workspace", "audit")
STATE = os.path.join(AUDIT_ROOT, "_audit_state.json")
PROMPT_TMPL = os.path.join(BASE, "translation-workspace", "prompts", "audit_prompt_template.md")

COOLDOWN = 90          # 两轮间隔（限流保护，原50s偏紧，实测连续快速请求易触发限流）
GEN_TIMEOUT = 1500     # 单板块最长等待（审计内容大，放宽到 25 分钟；实测限流后生成可达 10-25 分钟）
POLL = 20

# 板块分组（节点编号首段 -> 板块名）
DIM_MAP = {'2': '价格信号', '3': '供给', '4': '库存', '5': '需求', '6': '进出口', '7': '成本利润'}

# 品种术语参考（对齐 audit_prompt_template.md）
VAR_TERMS = {
    "ZN": "电锌、锌锭、锌精矿、再生锌、锌合金、镀锌板/热镀锌、氧化锌、压铸合金、电池级锌",
    "CU": "电解铜、铜精矿、废铜、粗铜、阳极铜、铜杆、铜管、铜板带、铜箔、硫酸铜",
    "AL": "电解铝、氧化铝、铝土矿、再生铝、铝合金、铝型材、铝板带、铝箔、铝线缆",
    "NI": "镍生铁/NPI、高冰镍、电解镍、精炼镍、镍矿/硫化矿、镍铁一体化、不锈钢镍、电池级镍、高纯镍/电积镍",
}
VAR_CN = {"ZN": "锌", "CU": "铜", "AL": "铝", "NI": "镍"}

# ---------- CDP 交互（skill 验证过的坑位）----------
def cdp_eval(ws_url, js, await_promise=False):
    import urllib.request, websocket
    msg_id = int(time.time() * 1000) % 100000
    params = {"expression": js, "returnByValue": True}
    if await_promise:
        params["awaitPromise"] = True
    ws = websocket.create_connection(ws_url, timeout=60, suppress_origin=True)
    ws.send(json.dumps({"id": msg_id, "method": "Runtime.evaluate", "params": params}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == msg_id:
            ws.close()
            return r
        if r.get("method") == "Runtime.exceptionThrown":
            pass


def cdp_click(ws_url, x, y):
    """用 CDP Input.dispatchMouseEvent 真实鼠标点击（合成事件对 Vue handler 常无效，实测卡点）"""
    import websocket
    ws = websocket.create_connection(ws_url, timeout=60, suppress_origin=True)
    for ev_type in ("mousePressed", "mouseReleased"):
        mid = int(time.time() * 1000) % 100000
        ws.send(json.dumps({"id": mid, "method": "Input.dispatchMouseEvent",
                            "params": {"type": ev_type, "x": x, "y": y,
                                       "button": "left", "clickCount": 1}}))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") == mid:
                break
    ws.close()

INIT_JS = "window.__W=[];'init'"
CHUNK_JS = "window.__W.push(%s);window.__W.length"
# 定位 ChatInput Vue 组件实例（长文本发送的关键入口），挂到 window.__CI
FIND_CI_JS = r"""
(() => {
  let found = null;
  (function walk(node, depth){
    if (depth>16 || found) return;
    if (node.__vue__) {
      const v = node.__vue__;
      let c = v;
      while (c) {
        if (c.$options && c.$options.name === 'ChatInput') { found = v; return; }
        c = c.$parent;
      }
    }
    if (node.childNodes && node.childNodes.length) for (let i=0;i<node.childNodes.length;i++) walk(node.childNodes[i], depth+1);
  })(document.body, 0);
  if (!found) { window.__CI = null; return 'NO_CHATINPUT'; }
  window.__CI = found;
  return 'OK_setText=' + (typeof found.setText);
})()
"""
# 用组件 setText 同步 Quill delta + Vue textContent（替代 innerHTML 注入，根因修复）
# 注意：sendBtn 渲染是异步的（Vue nextTick，实测 ~300ms），必须在 JS 内轮询等它出现，
#       不能在 setText 后同步读（读到的永远是 false）——驱动脚本 2026-09-01 踩坑修复
SETTEXT_JS = r"""
(async () => {
  const CI = window.__CI;
  if (!CI || typeof CI.setText !== 'function') return JSON.stringify({err:'NO_SETTEXT'});
  try { CI.setText(window.__W.join("")); } catch(e) { return JSON.stringify({err:'ERR:' + String(e)}); }
  const t0 = Date.now();
  let sendBtn = !!document.querySelector('.send-button');
  while (!sendBtn && Date.now()-t0 < 8000) {
    await new Promise(r=>setTimeout(r,200));
    sendBtn = !!document.querySelector('.send-button');
  }
  const ce = document.querySelector('[contenteditable]');
  return JSON.stringify({editorLen: ce ? ce.innerText.length : -1,
                         sendBtn: sendBtn, elapsed_ms: Date.now()-t0});
})()
"""
SEND_JS = r"""
(() => {
  var sb=document.querySelector('.send-button');
  if(!sb) return 'NO_BUTTON';
  var r=sb.getBoundingClientRect();
  var o={bubbles:true,cancelable:true,view:window,clientX:r.x+16,clientY:r.y+16,button:0};
  sb.dispatchEvent(new PointerEvent('pointerdown',o));
  sb.dispatchEvent(new MouseEvent('mousedown',o));
  sb.dispatchEvent(new PointerEvent('pointerup',o));
  sb.dispatchEvent(new MouseEvent('mouseup',o));
  sb.dispatchEvent(new MouseEvent('click',o));
  return 'clicked';
})()
"""
# ★ 2026-09-01 根因修复：原为裸顶层语句 `var items=...`，与全局已声明绑定冲突
#   (SyntaxError: Identifier 'items' has already been declared) → 新对话从未点成功。
#   必须 IIFE 包裹 + 内部用 const/let。
NEWCHAT_JS = r"""
(() => {
  const items=Array.from(document.querySelectorAll('.menu-item,[class*=menu-item],[role=menuitem]'));
  const nd=items.find(function(e){return e.innerText.trim()==='新对话';});
  if(!nd) return 'NO_NEWCHAT';
  const r=nd.getBoundingClientRect();
  const o={bubbles:true,cancelable:true,view:window,clientX:r.x+r.width/2,clientY:r.y+r.height/2,button:0};
  nd.dispatchEvent(new PointerEvent('pointerdown',o));
  nd.dispatchEvent(new MouseEvent('mousedown',o));
  nd.dispatchEvent(new PointerEvent('pointerup',o));
  nd.dispatchEvent(new MouseEvent('mouseup',o));
  nd.dispatchEvent(new MouseEvent('click',o));
  return 'clicked_newchat';
})()
"""
EDITOR_READY_JS = r"""
(() => {
  var ce=document.querySelector('[contenteditable]');
  return JSON.stringify({has:!!ce, len:ce?ce.innerText.length:-1});
})()
"""
STATUS_JS = r"""
(() => {
  var t=document.body.innerText;
  return JSON.stringify({len:t.length, limited:t.indexOf('暂时处理不过来了')>=0,
                         footer:t.indexOf('内容由AI生成，不构成投资建议')>=0});
})()
"""


def compact_divergence(path):
    """精简提取 divergence 表行（只留 图名称|包含指标|数据源），丢弃描述段落。
    原因：同花顺编辑器有硬性 10000 字上限（实测超限 sendBtn 渲染但点击无效），
    原始 divergence 单板块 19-58KB 聚合必超限。压缩后单板块约 3-6KB。2026-09-01 根因修复。

    兼容两种格式（skill 提示）：
    - ZN/NI：管道表 `| 序号 | 图名称 | 包含指标 | ... |`（行首有 |）
    - CU/AL：tab 枚举表 `序号\\t图名称\\t包含指标(1-3个)\\t题材归属度\\t数据源...\\t形态\\t用途`
             且响应中间可能混入 `+1`/`+2` 碎片行（段落引用标记），需按 tab 列数重组。
    """
    import re
    node = os.path.basename(path).replace("divergence_", "").replace(".md", "")
    text = open(path, encoding="utf-8").read()
    title = node
    for ln in text.split("\n")[:15]:
        m = re.match(r"^# (.+?)" + re.escape(node), ln)
        if m:
            title = ln.lstrip("# ").strip()
            break

    def is_row_cells(cells):
        # 表行：首列纯数字，且列数>=4（图名称|包含指标|数据源至少3列可用）
        return len(cells) >= 4 and re.match(r"^\d+$", cells[0].strip())

    rows = []
    for ln in text.split("\n"):
        s = ln.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if is_row_cells(cells):
                rows.append(f"{cells[1]}||{cells[2]}||{cells[4] if len(cells) > 4 else ''}")
        elif "\t" in s:
            cells = [c.strip() for c in s.split("\t")]
            if is_row_cells(cells):
                rows.append(f"{cells[1]}||{cells[2]}||{cells[4] if len(cells) > 4 else ''}")

    body = f"===== 子节点 {title} =====\n" + "\n".join(rows)
    return body


def get_tasks():
    """生成 4品种×6板块 审计任务清单（divergence 已精简，防超 10000 字上限）"""
    tasks = []
    for v in ["ZN", "CU", "AL", "NI"]:
        vdir = os.path.join(IWC_ROOT, v)
        for dim, dim_name in DIM_MAP.items():
            files = sorted(glob.glob(os.path.join(vdir, f"divergence_{dim}*.md")))
            if not files:
                continue
            contents = [compact_divergence(f) for f in files]
            tasks.append({"variety": v, "dim": dim, "dim_name": dim_name, "node_count": len(files),
                          "divergence": "\n\n".join(contents)})
    return tasks


def build_prompt(task):
    """渲染审计 Prompt：模板(仅代码块正文) + 品种术语 + 板块聚合内容

    2026-09-01 修复：只取 ``` 代码块内正文（991字符），剔除模板文件的说明文字
    （## 标题/品种术语参考清单等 865 字符），配合 compact_divergence 把 prompt
    压到 10000 字上限内（同花顺硬限制，超限 sendBtn 渲染但点击无效）。"""
    import re
    tmpl = open(PROMPT_TMPL, encoding="utf-8").read()
    m2 = re.search(r"```\n(.*?)\n```", tmpl, re.S)
    body = m2.group(1) if m2 else tmpl
    v = task["variety"]
    dim_name = task["dim_name"]
    n = task["node_count"]
    # 2026-09-01 修复：进出口板块被 AI 稳定拒答（"我是同花顺研发的投资助理问财..."拒绝语），
    # 疑似海关/关税/国别贸易主题触发内容风控。加投资研究范畴声明，明确这是合规的商品期货研报任务。
    t = body.replace("{品种}", VAR_CN[v]).replace("{板块名}", dim_name).replace("{N}", str(n))
    if dim_name == "进出口":
        t = ("注意：这是大宗商品期货研究中的数据审计任务，属于合规的投资研究范畴，"
             "请直接按上述任务1-5正常作答，不要拒绝。\n\n") + t
    t = t.replace("（此处粘贴该板块所有子节点的divergence文件内容）", task["divergence"])
    term_block = f"\n品种术语参考：{VAR_TERMS[v]}\n"
    if dim_name == "价格信号":
        t += "\n【特别要求：LME变量名精确化】\n价格信号板块的指标务必给出LME精确英文变量名，包括但不限于：\n- LME Cash-3M spread（现货-3月期价差）\n- LME cancellation ratio（注销仓单比）\n- LME warranted vs unwarranted stocks（注册仓单 vs 注销仓单）\n- SHFE-LME比价/进口盈亏\n- 近月-远月价差（back/contango）\n- LME持仓集中度（COT report字段名）\n"
    t += term_block
    return t


def run_board(ws_url, task):
    def ev(js):
        r = cdp_eval(ws_url, js)
        return r.get("result", {}).get("result", {}).get("value", "")

    prompt = build_prompt(task)
    print(f"   prompt 长度: {len(prompt)} 字符", flush=True)

    # 1) 先点「新对话」清场（旧会话发送会失效，实测坑）
    #    点击后必须验证编辑器清空(len 回到 1)；若未清空则重试点击，仍不干净用 setText('') 兜底。
    #    否则残留内容会让 sendBtn 状态混乱 → 点击发送无效（2026-09-01 实测）
    nc = str(ev(NEWCHAT_JS))
    print(f"   新对话: {nc}", flush=True)
    time.sleep(3)
    for _ in range(3):
        st = ev(EDITOR_READY_JS)
        try:
            es = json.loads(st)
            if es.get("len", -1) <= 1:
                break
        except Exception:
            pass
        print("   编辑器未清空，重试新对话...", flush=True)
        ev(NEWCHAT_JS)
        time.sleep(3)
    # 兜底：强制清空编辑器（防残留影响 sendBtn）
    st = ev(EDITOR_READY_JS)
    try:
        es = json.loads(st)
        if es.get("len", -1) > 1:
            ev(FIND_CI_JS)
            r = cdp_eval(ws_url, "window.__CI ? (window.__CI.setText(''),'cleared') : 'NO_CI'", await_promise=False)
            print(f"   兜底清空: {str(r.get('result',{}).get('result',{}).get('value',''))}", flush=True)
            time.sleep(1)
    except Exception:
        pass

    # 2) 等待编辑器就绪
    for _ in range(10):
        st = ev(EDITOR_READY_JS)
        try:
            es = json.loads(st)
            if es.get("has"):
                break
        except Exception:
            pass
        time.sleep(2)

    # 3) 定位 ChatInput 组件（新对话后组件可能重建，必须重新定位）
    ci = ""
    for _ in range(10):
        ci = str(ev(FIND_CI_JS))
        if ci.startswith("OK"):
            break
        time.sleep(2)
    print(f"   ChatInput: {ci}", flush=True)
    if not ci.startswith("OK"):
        return False, None, f"NO_CHATINPUT({ci})"

    # 4) 分片收集 prompt（每片 ≤500 字，避免 expression 超长截断）
    ev(INIT_JS)
    for i in range(0, len(prompt), 500):
        chunk = prompt[i:i+500]
        expr = CHUNK_JS % json.dumps(chunk, ensure_ascii=False)
        ev(expr)
    total = ev("window.__W.join('').length")
    print(f"   分片收集: {total} 字符", flush=True)

    # 5) 用组件 setText 同步 Quill delta（根因修复）；SETTEXT_JS 是 async，需 awaitPromise
    r = cdp_eval(ws_url, SETTEXT_JS, await_promise=True)
    st_note = str(r.get("result", {}).get("result", {}).get("value", ""))
    print(f"   setText: {st_note}", flush=True)
    try:
        ss = json.loads(st_note)
        if ss.get("sendBtn") is not True:
            return False, None, f"NO_SENDBTN(editorLen={ss.get('editorLen')})"
    except Exception:
        return False, None, f"SETTEXT_PARSE_FAIL({st_note})"
    time.sleep(1)

    # 6) 点发送：用 CDP 真实鼠标点击（合成事件 dispatchEvent 对 Vue handler 常无效，实测卡点）
    #    真实点击后 body 出现 AI 回复页脚 = 发送成功；但 setText 注入可能绕过编辑器清空，
    #    所以「发送成功」判据改为 body 长度增量，而非编辑器清空。
    btn_pos = ev(r"""
    (() => {
      const sb = document.querySelector('.send-button');
      if (!sb) return null;
      const b = sb.getBoundingClientRect();
      return JSON.stringify({x: Math.round(b.x + b.width/2), y: Math.round(b.y + b.height/2)});
    })()
    """)
    if not btn_pos or btn_pos == "null":
        return False, None, "NO_BUTTON"
    try:
        bx, by = json.loads(btn_pos)["x"], json.loads(btn_pos)["y"]
    except Exception:
        return False, None, f"BTN_POS_FAIL({btn_pos})"
    body_before = len(ev("document.body.innerText") or "")
    cdp_click(ws_url, bx, by)
    print(f"   真实点击发送 @({bx},{by})", flush=True)

    # 7) 等待发送生效：body 长度应增长（用户消息上屏 / AI 开始生成）
    sent_ok = False
    body_now = body_before
    for _ in range(6):
        time.sleep(3)
        body_now = len(ev("document.body.innerText") or "")
        if body_now > body_before + 200:
            sent_ok = True
            print(f"   body 增长确认发送成功 ({body_before} -> {body_now})", flush=True)
            break
    if not sent_ok:
        return False, None, f"NOT_SENT(body_delta={body_now - body_before})"

    # 8) 轮询等生成完成
    #    判据（2026-09-01 修）：
    #    - primary: body 出现「内容由AI生成，不构成投资建议」页脚 = AI 回复完成（prompt 不含此句，不会假阳性）
    #    - fallback: delta>=3000 且连续 2 次稳定（兼容页脚未渲染的情况）
    #    - 限流可多次重试（每次冷却 90s，最多 6 次），避免一次限流直接烧穿 GEN_TIMEOUT
    t0 = time.time()
    base_len = None
    limited_retries = 0
    last_len = 0
    stable = 0
    while time.time() - t0 < GEN_TIMEOUT:
        time.sleep(POLL)
        val = str(ev(STATUS_JS))
        try:
            st = json.loads(val)
        except Exception:
            st = {"len": 0, "limited": False, "footer": False}
        # 限流：冷却 90s 重试（最多 6 次），期间不判完成
        if st.get("limited"):
            if limited_retries >= 6:
                print("   限流 6 次仍失败，放弃", flush=True)
                return False, None, "RATE_LIMIT"
            limited_retries += 1
            print(f"   限流(第{limited_retries}次)，冷却 90s", flush=True)
            time.sleep(90)
            continue
        # 页脚出现 = 回复完成（强信号）
        if st.get("footer"):
            cur = st.get("len", 0)
            print(f"   页脚出现=回复完成，耗时 {int(time.time()-t0)}s，body 长度 {cur}", flush=True)
            break
        # 兜底：delta 足够大且连续 2 次稳定
        cur = st.get("len", 0)
        if base_len is None:
            base_len = cur
        delta = cur - base_len
        if delta >= 3000:
            if cur == last_len:
                stable += 1
            else:
                stable = 0
            if stable >= 2:
                print(f"   回复稳定，耗时 {int(time.time()-t0)}s，body 长度 {cur} (delta={delta})", flush=True)
                break
        else:
            stable = 0
        last_len = cur
    else:
        return False, None, "TIMEOUT"

    # 9) 抓取回复
    body = ev("document.body.innerText") or ""
    anchor = "品种术语参考：" + VAR_TERMS[task["variety"]]
    marker = body.rfind(anchor)
    if marker >= 0:
        reply = body[marker + len(anchor):]
    else:
        marker = body.rfind("你是" + VAR_CN[task["variety"]] + "基本面")
        reply = body[marker:] if marker >= 0 else body[-20000:]
    for foot in ["智能调度", "内容由AI生成，不构成投资建议"]:
        i = reply.find(foot)
        if i > 0:
            reply = reply[:i]
    reply = reply.strip()
    if len(reply) < 500:
        return False, None, f"REPLY_TOO_SHORT({len(reply)})"

    outdir = os.path.join(AUDIT_ROOT, task["variety"])
    os.makedirs(outdir, exist_ok=True)
    opath = os.path.join(outdir, f"audit_{task['dim_name']}.md")
    header = (f"# {task['variety']}·{task['dim_name']} 板块审计（Step1 同花顺回复）\n"
              f"# 抓取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
              f"# 覆盖子节点数: {task['node_count']}\n\n---\n\n")
    open(opath, "w", encoding="utf-8").write(header + reply)
    return True, opath, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--start", type=int)
    ap.add_argument("--end", type=int)
    ap.add_argument("--ws", required=True)
    args = ap.parse_args()

    os.makedirs(AUDIT_ROOT, exist_ok=True)
    tasks = get_tasks()
    state = json.load(open(STATE)) if os.path.exists(STATE) else {"done": {}}

    if args.node:
        v, dim_name = args.node.split("_", 1)
        tasks = [t for t in tasks if t["variety"] == v and t["dim_name"] == dim_name]
    else:
        if args.start is not None:
            tasks = tasks[args.start:args.end]

    print(f"共 {len(tasks)} 个板块任务", flush=True)
    for i, task in enumerate(tasks):
        key = f"{task['variety']}_{task['dim_name']}"
        if key in state["done"] and state["done"][key].get("ok"):
            print(f"[SKIP] {key} 已完成", flush=True)
            continue
        print(f"[{i+1}/{len(tasks)}] {key}（{task['node_count']}节点）...", flush=True)
        ok, path, note = run_board(args.ws, task)
        # 2026-09-01 新增：AI 偶发拒答(REPLY_TOO_SHORT)或限流/TIMEOUT → 自动重试最多 2 次
        # （实测 CU_进出口 一轮 AI 回了拒绝语"我是同花顺研发的投资助理问财..."仅88字）
        retryable = ("REPLY_TOO_SHORT" in note or "TIMEOUT" in note or "RATE_LIMIT" in note)
        attempts = 0
        while not ok and retryable and attempts < 2:
            attempts += 1
            print(f"   [重试{attempts}] {note}，冷却 {COOLDOWN}s 后重跑...", flush=True)
            time.sleep(COOLDOWN)
            ok, path, note = run_board(args.ws, task)
            retryable = ("REPLY_TOO_SHORT" in note or "TIMEOUT" in note or "RATE_LIMIT" in note)
        state["done"][key] = {"ok": ok, "path": path, "note": note, "ts": time.time()}
        json.dump(state, open(STATE, "w"), ensure_ascii=False, indent=1)
        print(f"   -> ok={ok} {note} {path or ''}", flush=True)
        time.sleep(COOLDOWN)


if __name__ == "__main__":
    main()
