#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iwencai_batch_driver.py — 同花顺问财批量发散驱动（CDP 自动化）

用途：按逐节点方式，把 v18/v19 prompt 逐个发进同花顺「新对话」，
      抓取 AI 回复落盘，供下游做自检/取舍/知几验证。

为什么用 CDP：60 节点若逐个用对话内 browser_* 工具，上下文会爆且极慢；
CDP 让脚本自治，只在完成时回报摘要。

依赖：CDP ws endpoint（由 browser 工具 attach 后通过 Target.getTargets 反查不到 wsUrl，
      故本脚本走 CDP over HTTP 的 Runtime.evaluate 无状态调用亦可；这里用 websocket-client）。

用法：
  python3 iwencai_batch_driver.py --node CU_2.1          # 单节点（证明）
  python3 iwencai_batch_driver.py --all                  # 按 manifest 全量
  python3 iwencai_batch_driver.py --all --start 3 --end 8  # 区间续跑

产物：analysis/iwencai/<品种>/divergence_<节点>.md
状态：analysis/iwencai/_driver_state.json（断点续跑）
"""
import argparse, json, os, re, sys, time, hashlib

BASE = os.environ.get("FRAMEWORK_TREE", "/home/ubuntu/framework-tree")
OUT_ROOT = os.path.join(BASE, "analysis", "iwencai")
STATE = os.path.join(OUT_ROOT, "_driver_state.json")
MANIFEST = os.path.join(OUT_ROOT, "CU_AL_manifest.json")
PROMPT_DIR = os.path.join(OUT_ROOT, "prompts")
os.makedirs(PROMPT_DIR, exist_ok=True)

COOLDOWN = 50          # 两个 prompt 间隔（限流保护，skill 建议 >=45s）
GEN_TIMEOUT = 420      # 单节点生成最长等待
POLL = 20              # 轮询间隔


# ---------- prompt 渲染（内联通用模板，与 prompt_v18_generic.md 同源）----------
def render_prompt(variety_cn, dim_label, subdirs_str, positive, boundary="", usage=""):
    """逐节点：subdirs_str 只含 1 个子类。positive/boundary/usage 为分号分隔串。"""
    p = (positive or "").split(";")
    usage_p = (usage or "").split(";")
    boundary_p = (boundary or "").split(";")
    return (
        f"角色：你是有色金属产业研究的「题材精准枚举器·复合图设计师」。你的唯一职责：对「{variety_cn}·{dim_label}」"
        f"目录下的固定子类，精准枚举每个子类最核心的独立基础指标，并设计最能说明问题的**单图或多指标复合图**，"
        "数量严格受控，每张图给出名称、形态与观测用途。\n\n"
        f"【目录】固定以下子类，只按子类输出，不要输出子类外的内容：\n{subdirs_str}\n\n"
        "【核心规则——务必逐条遵守】\n\n"
        "**规则1：数量硬约束**\n"
        "每个子类只输出 6-8 个\"本子类直接相关\"的指标，最多 10 个。少比多好，宁缺勿滥。\n\n"
        "**规则2：独立基础指标原则**\n"
        "只枚举原始的可量化基础指标（绝对量/结构占比/持有者/分地区/在途量/持有天数等），不要枚举派生形态。\n"
        "\"日增减/周环比/月环比/同比/去化速度/累库幅度/环比率/分位数/变化方向/月度高点/低点/增速\"——这些全部是同一指标的呈现方式，"
        "不是独立指标，一律不要单列。\n"
        "举例：如果列了\"库存总量\"，就不要再列它的\"周度环比增减/环比率/分位数\"。\n\n"
        "**规则3：题材对象一致原则（通用归属判断）**\n"
        "每个子类都有一个明确的题材对象——子类名即对象定义，无需额外说明。\n"
        "判定一个指标是否属于本子类，唯一标准：该指标是否直接描述本子类的题材对象。\n"
        "派生形态（环比/同比/增速/去化/分位/日增减）不构成独立指标，归入该原始指标的呈现方式。\n"
        "若某指标描述的对象不属于本子类，则不删除，在表格末尾标注\"与其他子类更相关 + 应归属环节\"。你只需判断归属，无需人为删减。\n\n"
        "**规则4：允许指标类型（正例关键词）**\n" + "\n".join(f"- {x}" for x in p if x) + "\n\n"
        "**规则5：图表形态——支持复合图，鼓励一图多指标**\n"
        "1. 允许并鼓励\"复合图\"：一张图内放 2-3 个**同主题强相关**的指标，比拆成多张单指标图更能说明问题时，优先设计复合图。\n"
        "2. 单指标图可选形态：季节性图（强季节属性首选）/历史时序/分位带图/柱状图（结构占比、分地区）/热力图。\n"
        "3. 复合图形态：**双轴联动**（不同量纲，左右轴）或 **多指标叠加图**（一图多线/多柱，标注主指标与辅指标）。\n"
        "4. **形态分布硬约束**：整个目录输出中\"季节性图\"至少 2 个；每个子类至少 1 张复合图（≥2 个指标）。\n\n"
        "**规则6：每张图必须给出\"观测用途\"**\n"
        "用一句人话说明这张图主要用来看什么、回答什么问题时会翻开它。不要写套话。\n\n"
        "【工作方法】对每个子类：\n"
        "1. 按规则 1-4 枚举 6-8 个独立基础指标。\n"
        "2. 按规则 5 判断哪些可合并为复合图，哪些必须单指标呈现。\n"
        "3. 每张图给出：数据源(渠道/频率/可得性) + 典型呈现形态 + 观测用途。\n\n"
        "【输出格式】每子类一张表格：\n"
        "| 序号 | 图名称 | 包含指标(1-3个) | 题材归属度 | 数据源(渠道/频率/可得性) | 典型呈现形态 | 观测用途 |\n\n"
        "每子类末尾一行汇总：\n"
        f"\"本子类共 {{N}} 个直接相关指标，合并为 {{K}} 张图，{{M}} 个归属其他子类（{{归属环节}}）。\"\n\n"
        "【输出结尾】输出：\n"
        f"\"本维度（{dim_label}）合计 {{N}} 个直接相关指标，合并为 {{K}} 张图，{{M}} 个归属其他子类待后续维度启用。\"\n"
    )


# ---------- CDP 连接层 ----------
# 本机 Chrome 未开 --remote-allow-origins：
#   - 带 origin="https://www.iwencai.com" -> 403 Rejected
#   - suppress_origin=True（完全省略 Origin 头）-> 成功
# 实测验证通过（editor:true, btn:true）。
def cdp_eval(ws_url, expression, suppress_origin=True):
    import websocket
    ws = websocket.create_connection(ws_url, timeout=60, suppress_origin=suppress_origin)
    try:
        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                            "params": {"expression": expression, "returnByValue": True}}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == 1:
                return msg
    finally:
        ws.close()


# ---------- 分片注入 + 发送（skill 验证过的坑位）----------
INIT_JS = "window.__W=[];'init'"
CHUNK_JS = "window.__W.push(%s);window.__W.length"
FLUSH_JS = r"""
var txt=window.__W.join("");
var ce=document.querySelector('[contenteditable]');
if(!ce){'NO_EDITOR';}else{
ce.innerHTML='<p>'+txt.replace(/\n/g,'<br>')+'</p>';
ce.focus();
ce.dispatchEvent(new InputEvent('input',{bubbles:true,cancelable:false,data:'x',inputType:'insertText'}));
ce.dispatchEvent(new KeyboardEvent('keydown',{key:'a',code:'KeyA',bubbles:true}));
ce.dispatchEvent(new KeyboardEvent('keyup',{key:'a',code:'KeyA',bubbles:true}));
ce.dispatchEvent(new Event('blur',{bubbles:true}));
'len='+txt.length;
}"""
SEND_JS = r"""
var sb=document.querySelector('.send-button');
if(!sb){'NO_BUTTON';}else{
var r=sb.getBoundingClientRect();
var o={bubbles:true,cancelable:true,view:window,clientX:r.x+16,clientY:r.y+16,button:0};
sb.dispatchEvent(new PointerEvent('pointerdown',o));
sb.dispatchEvent(new MouseEvent('mousedown',o));
sb.dispatchEvent(new PointerEvent('pointerup',o));
sb.dispatchEvent(new MouseEvent('mouseup',o));
sb.dispatchEvent(new MouseEvent('click',o));
'clicked x='+r.x+' y='+r.y;
}"""
STATUS_JS = r"""
var t=document.body.innerText;
var done=t.indexOf('模型答案生成完成')>=0;
var limited=t.indexOf('暂时处理不过来了')>=0;
JSON.stringify({len:t.length,done:done,limited:limited});"""


def run_node(ws_url, task, var_cn_map):
    """发一个节点，返回 (ok, path, note)。"""
    vn = var_cn_map[task["variety"]]

    def ev(js):
        """在 /chat 页执行 JS，返回 value（ws_url 已是 page 级，无需 targetId）。"""
        r = cdp_eval(ws_url, js)
        return r.get("result", {}).get("result", {}).get("value", "")

    # 正例关键词：按维度给最小集（占位符法，换维度只改这里）
    POS = {
        "price": "期货主力合约收盘价,基差,现货升贴水,沪伦比,进口盈亏,持仓量,成交量,期限结构,月差,仓单注册量,冶炼利润,估值分位,多空持仓比",
        "supply": "矿产量,精炼产量,开工率,产能利用率,检修量,加工费TC,进口量,再生产量,产能,开工天数,进口量分国别",
        "inventory": "交易所库存,社会库存,厂内库存,仓单,注销仓单,在途库存,隐性库存,库存天数,注销占比,库存分地区",
        "demand": "表观消费,开工率,产量,库存,订单量,排产计划,社会库存,需求增速,消费占比,终端产量",
        "trade": "进口量,出口量,净进口量,保税区库存,保税区仓单,注销仓单分地区,海外发运,发运天数,进出口金额,关税税率",
        "cost": "冶炼成本,加工成本,电解成本,现金成本,分位成本,冶炼利润,加工费,能源成本,电价,原料成本",
    }
    dim = task["dim"]
    if not dim:   # --node 模式未带 dim，按节点编号反查
        code0 = task["node_code"].split(".")[0]
        dim = {"2": "price", "3": "supply", "4": "inventory", "5": "demand",
               "6": "trade", "7": "cost"}.get(code0, "inventory")
    pos = POS[dim]
    label = task["label"] or {"price": "价格信号", "supply": "供给", "inventory": "库存",
                              "demand": "需求", "trade": "进出口", "cost": "成本·利润"}[dim]
    node_name = task["node_name"] or ""
    q = task.get("q", "")
    if not node_name:   # --node 模式未带名，从 manifest/tree_config 反查
        try:
            mp = MANIFEST
            man = json.load(open(mp))
            for t in man["tasks"]:
                if t["variety"] == task["variety"] and t["node_code"] == task["node_code"]:
                    node_name = t["node_name"]
                    q = t.get("q", "") or q
                    break
        except Exception:
            pass
    # 逐节点发：子类列表只 1 条，带名称，约束模型不扩散
    prompt = render_prompt(vn, label, f"1. {task['node_code']} {node_name}（{q}）", pos)
    ppath = os.path.join(PROMPT_DIR, f"{task['variety']}_{task['node_code']}.md")
    open(ppath, "w", encoding="utf-8").write(prompt)

    # 分片注入（每片 <=600 字）
    ev(INIT_JS)
    for i in range(0, len(prompt), 600):
        chunk = prompt[i:i+600]
        expr = CHUNK_JS % json.dumps(chunk, ensure_ascii=False)
        ev(expr)
    flush_note = str(ev(FLUSH_JS))
    if "NO_EDITOR" in flush_note:
        return False, None, "NO_EDITOR"

    send_note = str(ev(SEND_JS))
    if "NO_BUTTON" in send_note:
        return False, None, "NO_BUTTON"

    # 轮询等生成完成
    t0 = time.time()
    while time.time() - t0 < GEN_TIMEOUT:
        time.sleep(POLL)
        val = str(ev(STATUS_JS))
        try:
            st = json.loads(val)
        except Exception:
            st = {"len": 0, "done": False, "limited": False}
        if st.get("limited"):
            time.sleep(60)   # 限流，冷却后重试一次
            val = str(ev(STATUS_JS))
            st = json.loads(val) if val.startswith("{") else {}
        if st.get("done"):
            break

    # 抓取回复
    body = ev("document.body.innerText") or ""

    # 只保留最后一轮（本轮 prompt + 答案），避免串历史
    cut = body.rfind("本维度")
    marker = body.rfind("角色：你是有色金属产业研究的")
    reply = body[marker:] if marker >= 0 else body[-12000:]

    outdir = os.path.join(OUT_ROOT, task["variety"])
    os.makedirs(outdir, exist_ok=True)
    opath = os.path.join(outdir, f"divergence_{task['node_code']}.md")
    header = (f"# {task['variety']}·{task['label']}·{task['node_code']} {task['node_name']}\n"
              f"# 抓取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n")
    open(opath, "w", encoding="utf-8").write(header + reply)
    return True, opath, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--start", type=int)
    ap.add_argument("--end", type=int)
    ap.add_argument("--manifest", default=None, help="manifest 路径, 默认 CU_AL_manifest.json")
    ap.add_argument("--ws", required=True, help="CDP page websocket endpoint")
    args = ap.parse_args()

    var_cn_map = {"CU": "铜", "AL": "铝", "PB": "铅", "ZN": "锌", "NI": "镍", "SN": "锡", "SI": "硅", "LI": "锂", "LC": "碳酸锂", "FE": "铁矿石"}
    mtag = os.path.basename(args.manifest or "CU_AL_manifest.json").replace("_manifest", "").replace(".json", "")
    S = STATE.replace("_driver_state", f"_driver_state_{mtag}")
    state = json.load(open(S)) if os.path.exists(S) else {"done": {}}

    if args.node:
        v, code = args.node.split("_")
        t = {"variety": v, "dim": None, "label": "", "node_code": code, "node_name": "", "q": ""}
        tasks = [t]
    else:
        mp = args.manifest or MANIFEST
        man = json.load(open(mp))
        tasks = man["tasks"]
        if args.start is not None:
            tasks = tasks[args.start: args.end]

    for i, task in enumerate(tasks):
        key = f"{task['variety']}_{task['node_code']}"
        if key in state["done"] and state["done"][key].get("ok"):
            print(f"[SKIP] {key} 已完成", flush=True)
            continue
        print(f"[{i+1}/{len(tasks)}] {key} ...", flush=True)
        ok, path, note = run_node(args.ws, task, var_cn_map)
        state["done"][key] = {"ok": ok, "path": path, "note": note, "ts": time.time()}
        json.dump(state, open(S, "w"), ensure_ascii=False, indent=1)
        print(f"   -> ok={ok} {note} {path or ''}", flush=True)
        time.sleep(COOLDOWN)


if __name__ == "__main__":
    main()
