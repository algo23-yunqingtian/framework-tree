#!/usr/bin/env python3
"""
同花顺问财 · 分类范式批量驱动脚本 v1
用途：8品种 × 6板块 = 48轮，让同花顺对每个"品种×板块"做总→分分类+重点指标推荐
用法：
  python3 iwencai_classify_batch.py --ws <ws_url>              # 全量跑
  python3 iwencai_classify_batch.py --ws <ws_url> --only PB,库存  # 指定品种+板块
  python3 iwencai_classify_batch.py --ws <ws_url> --resume      # 断点续跑
产物：analysis/iwencai_classify/{品种}_{板块}.md
状态：analysis/iwencai_classify/_classify_state.json
"""
import json, time, sys, os, re, argparse, urllib.parse, urllib.request, websocket, socket, pathlib

# ===== 配置 =====
FRAMEWORK_TREE = os.environ.get("FRAMEWORK_TREE", "/home/ubuntu/framework-tree")
OUTPUT_DIR = os.path.join(FRAMEWORK_TREE, "analysis", "iwencai_classify")
STATE_FILE = os.path.join(OUTPUT_DIR, "_classify_state.json")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 8品种 × 6板块
VARIETIES = [
    {"code": "CU", "name": "铜", "cn": "铜"},
    {"code": "AL", "name": "铝", "cn": "铝"},
    {"code": "ZN", "name": "锌", "cn": "锌"},
    {"code": "PB", "name": "铅", "cn": "铅"},
    {"code": "NI", "name": "镍", "cn": "镍"},
    {"code": "SN", "name": "锡", "cn": "锡"},
    {"code": "SI", "name": "工业硅", "cn": "硅"},
    {"code": "LC", "name": "碳酸锂", "cn": "碳酸锂"},
]

BOARDS = ["价格信号", "供给", "库存", "需求", "进出口", "成本利润"]

# 板块→首选分类维度
BOARD_DIM = {
    "价格信号": "口径+形态",
    "供给": "工艺+地区",
    "库存": "地区+口径",
    "需求": "产业链环节+地区",
    "进出口": "地区流向+口径",
    "成本利润": "工艺+原料形态",
}

# 品种特异性提示（帮助同花顺聚焦）
VARIETY_HINT = {
    "CU": "铜：火法+湿法精炼，智利/秘鲁/刚果矿端，TC加工费是边际",
    "AL": "铝：电解铝(火电/水电/网电)+再生铝，4500万吨天花板，铝水转化率是关键",
    "ZN": "锌：火法ISP/湿法冶炼+再生锌，TC加工费是边际，镀锌是最大需求",
    "PB": "铅：原生铅(矿→粗铅→电解)+再生铅(废电瓶→熔炼)，再生铅是边际调节器，废电瓶成本刚性",
    "NI": "镍：NPI(火法RKEF)/MHP(湿法HPAL)/电解镍，印尼RKAB是核心，硫磺价格影响MHP成本",
    "SN": "锡：原生锡矿+再生锡，缅甸佤邦占中国进口72-85%，佤邦复产是核心变量",
    "SI": "工业硅：化学级(多晶硅/有机硅)+冶金级(铝合金)，新疆/云南/四川产能分布",
    "LC": "碳酸锂：盐湖(青海/南美)+云母(江西宜春)+辉石(澳洲/四川)+回收，云母是边际出清者",
}

# ===== CDP 工具 =====
def discover_ws(debug_host="127.0.0.1:9222"):
    tabs = json.loads(urllib.request.urlopen(f"http://{debug_host}/json", timeout=8).read())
    for t in tabs:
        if t.get("type") == "page" and "iwencai" in t.get("url", "") and "/chat" in t.get("url", ""):
            return t["webSocketDebuggerUrl"], t.get("id", t.get("targetId", ""))
    return None, None

def cdp_eval(ws_url, expression, timeout=30):
    """stateless CDP Runtime.evaluate"""
    ws = websocket.create_connection(ws_url, timeout=timeout+5, suppress_origin=True)
    socket.setdefaulttimeout(timeout)
    id_ = int(time.time()) % 2000000000
    ws.send(json.dumps({"id": id_, "method": "Runtime.evaluate",
                        "params": {"expression": expression, "returnByValue": True}}))
    got = None
    while True:
        try:
            raw = ws.recv()
            msg = json.loads(raw)
        except Exception:
            break
        if isinstance(msg, dict) and msg.get("id") == id_:
            got = msg
            break
    ws.close()
    if got and "error" in got:
        raise RuntimeError(f"CDP error: {got['error'].get('message')}")
    return (got or {}).get("result", {}).get("result", {}).get("value")

def cdp_click(ws_url, x, y, target_id=None):
    """CDP Input.dispatchMouseEvent 真实鼠标点击"""
    ws = websocket.create_connection(ws_url, timeout=15, suppress_origin=True)
    socket.setdefaulttimeout(15)
    id_ = int(time.time()) % 2000000000
    for evt_type in ["mousePressed", "mouseReleased"]:
        params = {"button": "left", "clickCount": 1, "type": evt_type, "x": x, "y": y}
        ws.send(json.dumps({"id": id_, "method": "Input.dispatchMouseEvent", "params": params}))
        id_ += 1
        time.sleep(0.1)
        try:
            ws.recv()
        except:
            pass
    ws.close()

# ===== 同花顺操作 =====
def new_chat(ws_url):
    """点新对话清场"""
    coords = cdp_eval(ws_url, """(()=>{var items=document.querySelectorAll('[role=menuitem]');for(var i=0;i<items.length;i++){if(items[i].innerText.indexOf('新对话')>=0){var r=items[i].getBoundingClientRect();return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)})}}return 'NOT_FOUND'})()""")
    if coords and coords != 'NOT_FOUND':
        c = json.loads(coords)
        cdp_click(ws_url, c["x"], c["y"])
        time.sleep(3)
        return True
    return False

def inject_and_send(ws_url, prompt_text):
    """用 ChatInput.setText 注入 + CDP 点击发送"""
    # 分片存入 window.__W
    chunks = []
    for i in range(0, len(prompt_text), 500):
        chunk = prompt_text[i:i+500]
        chunks.append(chunk)
    
    # 初始化
    cdp_eval(ws_url, "window.__W=[];'init'")
    
    # 分片注入
    for chunk in chunks:
        safe = json.dumps(chunk)
        cdp_eval(ws_url, f"window.__W.push({safe});window.__W.length")
    
    # 合并 + setText
    js = """(()=>{function findCI(root){var stack=[root];while(stack.length){var n=stack.shift();if(n.$options&&n.$options.name==='ChatInput'){return n}if(n.$children){n.$children.forEach(function(c){stack.push(c)})}}return null}var app=document.querySelector('#app');var root=app.__vue__||app.__vue_app__;if(!root)return'NO_ROOT';var ci=findCI(root);if(ci){ci.setText(window.__W.join('\\n'));return'CI_SET_OK'}return'NO_CI_FOUND'})()"""
    result = cdp_eval(ws_url, js)
    if result != 'CI_SET_OK':
        # 降级：innerHTML 注入
        txt = prompt_text.replace('\n', '<br>')
        js2 = f"""(()=>{{var ce=document.querySelector('[contenteditable]');if(!ce)return'NO_EDITOR';ce.innerHTML='<p>{txt}</p>';ce.focus();ce.dispatchEvent(new InputEvent('input',{{bubbles:true,cancelable:false,data:'x',inputType:'insertText'}}));return'FALLBACK_OK'}})()"""
        result = cdp_eval(ws_url, js2)
    
    time.sleep(2)
    
    # 查 send-button 坐标
    coords = cdp_eval(ws_url, """(()=>{var sb=document.querySelector('.send-button');if(!sb)return'NO_BTN';var r=sb.getBoundingClientRect();return JSON.stringify({x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)})})()""")
    if not coords or coords == 'NO_BTN':
        return False, "NO_SEND_BUTTON"
    
    c = json.loads(coords)
    cdp_click(ws_url, c["x"], c["y"])
    
    # 验证发送
    time.sleep(2)
    ce_len = cdp_eval(ws_url, "(()=>{var ce=document.querySelector('[contenteditable]');return ce?ce.innerText.length:999})()")
    return ce_len == 1, f"ceLen={ce_len}"

def wait_for_completion(ws_url, timeout=300):
    """轮询页脚判据 + 答案长度稳定检测（修 v2：解决提前判定导致答案未生成完就提取）"""
    prev_len = 0
    stable_count = 0
    for i in range(timeout // 5):
        time.sleep(5)
        result = cdp_eval(ws_url, """(()=>{var t=document.body.innerText;return JSON.stringify({len:t.length,footer:t.indexOf('内容由AI生成')>=0,done:t.indexOf('模型答案生成完成')>=0,limited:t.indexOf('暂时处理过来不了')>=0,hasAnswer:t.indexOf('结论先行')>=0||t.indexOf('任务1')>=0||t.indexOf('拆分树')>=0||t.indexOf('一、')>=0})})()""")
        if not result:
            continue
        d = json.loads(result)
        if d.get("limited"):
            return False, "RATE_LIMITED"
        # 必须同时满足：footer 出现 + done 出现 + hasAnswer + 长度稳定（连续3次不变）
        if d.get("footer") and d.get("done") and d.get("hasAnswer"):
            if d["len"] == prev_len:
                stable_count += 1
                if stable_count >= 3:
                    return True, f"bodyLen={d['len']}"
            else:
                stable_count = 0
            prev_len = d["len"]
    return False, "TIMEOUT"

def extract_reply(ws_url):
    """提取回复正文：只取最后一次'模型答案生成完成'之后到'内容由AI生成'之前的内容"""
    text = cdp_eval(ws_url, "document.body.innerText", timeout=10)
    if not text:
        return ""
    # 用 lastIndexOf 确保取最后一轮回复（不是历史聊天里的）
    done_idx = text.rfind("模型答案生成完成")
    footer_idx = text.rfind("内容由AI生成")
    if done_idx >= 0 and footer_idx >= 0 and footer_idx > done_idx:
        return text[done_idx:footer_idx]
    elif done_idx >= 0:
        # 有 done 但无 footer，取 done 之后全部
        return text[done_idx:]
    elif footer_idx >= 0:
        # 有 footer 但无 done，取 footer 之前最后一段
        return text[:footer_idx]
    return ""

# ===== Prompt 生成 =====
def make_prompt(variety, board):
    """根据品种+板块生成分类范式 prompt"""
    v = next(x for x in VARIETIES if x["name"] == variety or x["code"] == variety)
    dim = BOARD_DIM[board]
    hint = VARIETY_HINT.get(v["code"], "")
    
    prompt = f"""我是有色金属大宗商品产业研究分析师。我要建立{v['name']}的"{board}"板块从总量到分类的指标研究体系。

品种背景：{hint}

请你做4件事：

【任务1：分类维度选择】
{v['name']}的"{board}"板块，总量应该按什么维度拆分子类？首选维度：{dim}。
请给出拆分树：总量→子类→孙类，标注优先级（必看/重要/可选）。

【任务2：重点地区/工艺识别】
在{v['name']}的"{board}"板块里，哪些地区/产地/工艺是最重要的？判断标准是什么？
如果是库存板块：外盘LME重点看哪些仓点？国内重点看哪些地区？为什么选这些而不是其他？
如果是供给板块：按工艺怎么分？各工艺占比多少？哪个是边际定价工艺？

【任务3：重点指标推荐】
每个子类各推荐1-3个具体指标，给出：指标名+数据源+频率+为什么重要。

【任务4：优先级排序】
把所有子类指标按必看→重要→可选→不看排序，说明排序依据。

请直接回答用拆分树+表格不要空话。每个子类至少给1个具体指标名。"""
    return prompt

# ===== 状态管理 =====
def load_state():
    if os.path.exists(STATE_FILE):
        return json.loads(open(STATE_FILE).read())
    return {"completed": {}, "failed": {}}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# ===== 主流程 =====
def run_one(ws_url, variety_code, board, state):
    key = f"{variety_code}_{board}"
    if key in state["completed"]:
        print(f"  SKIP {key} (已完成)")
        return True
    
    v = next(x for x in VARIETIES if x["code"] == variety_code)
    prompt = make_prompt(v["name"], board)
    
    print(f"  [{key}] 注入prompt({len(prompt)}字)...")
    
    # 新对话清场
    new_chat(ws_url)
    time.sleep(2)
    
    # 注入+发送
    ok, msg = inject_and_send(ws_url, prompt)
    if not ok:
        print(f"  [{key}] 发送失败: {msg}")
        state["failed"][key] = f"send_failed: {msg}"
        save_state(state)
        return False
    
    # 等生成完成
    print(f"  [{key}] 等待AI生成...")
    ok, msg = wait_for_completion(ws_url, timeout=180)
    if not ok:
        print(f"  [{key}] 生成失败: {msg}")
        if "RATE_LIMITED" in msg:
            print(f"  [{key}] 限流，等90秒后继续...")
            time.sleep(90)
        state["failed"][key] = msg
        save_state(state)
        return False
    
    # 提取回复
    reply = extract_reply(ws_url)
    if len(reply) < 200:
        print(f"  [{key}] 回复太短({len(reply)}字)，可能拒答")
        state["failed"][key] = f"reply_too_short: {len(reply)}"
        save_state(state)
        return False
    
    # 落盘
    output_file = os.path.join(OUTPUT_DIR, f"{variety_code}_{board}.md")
    header = f"# {v['name']}({variety_code}) · {board} · 分类范式\n\n> 来源：同花顺问财批量分类范式脚本\n> 日期：{time.strftime('%Y-%m-%d')}\n> prompt字数：{len(prompt)}\n\n---\n\n"
    with open(output_file, "w") as f:
        f.write(header + reply)
    
    state["completed"][key] = {
        "file": output_file,
        "reply_len": len(reply),
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_state(state)
    print(f"  [{key}] ✅ 完成({len(reply)}字) → {output_file}")
    
    # 冷却
    time.sleep(45)
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ws", help="WebSocket URL (自动发现可不填)")
    parser.add_argument("--only", help="只跑指定品种+板块，格式：PB,库存")
    parser.add_argument("--resume", action="store_true", help="断点续跑")
    args = parser.parse_args()
    
    # 发现 WS
    ws_url = args.ws
    if not ws_url:
        ws_url, target_id = discover_ws()
    if not ws_url:
        print("❌ 未找到 iwencai.com/chat 页面，请先在 Chrome 打开")
        sys.exit(1)
    print(f"WS: {ws_url[:60]}...")
    
    state = load_state() if args.resume else {"completed": {}, "failed": {}}
    
    # 确定任务列表
    if args.only:
        parts = args.only.split(",")
        tasks = [(parts[0], parts[1])]
    else:
        tasks = [(v["code"], b) for v in VARIETIES for b in BOARDS]
    
    print(f"共 {len(tasks)} 个任务")
    
    for i, (vcode, board) in enumerate(tasks):
        print(f"\n[{i+1}/{len(tasks)}] {vcode} · {board}")
        try:
            run_one(ws_url, vcode, board, state)
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            state["failed"][f"{vcode}_{board}"] = str(e)
            save_state(state)
            time.sleep(10)
        
        # 每5轮冷却120秒
        if (i + 1) % 5 == 0 and i + 1 < len(tasks):
            print(f"  >>> 5轮完成，冷却120秒...")
            time.sleep(120)
    
    # 汇总
    print(f"\n{'='*50}")
    print(f"完成: {len(state['completed'])} | 失败: {len(state['failed'])}")
    if state["failed"]:
        print(f"失败列表: {list(state['failed'].keys())}")

if __name__ == "__main__":
    main()
