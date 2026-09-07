#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
白名单约束批量发散驱动器
从 knowledge_base.json 逐品种×板块渲染带规则8白名单的prompt，
通过CDP注入同花顺问财，自治运行+断点续跑+限流冷却。
"""
import json, os, sys, time, subprocess, re, urllib.request, socket
import websocket  # websocket-client

BASE = os.environ.get("FRAMEWORK_TREE", "/home/ubuntu/framework-tree")
KB_PATH = os.path.join(BASE, "analysis", "knowledge_base.json")
OUT_DIR = os.path.join(BASE, "analysis", "iwencai_whitelist")
STATE_FILE = os.path.join(OUT_DIR, "_whitelist_state.json")
CDP_PORT = 9222

# 维度→板块
DIM_BOARD = {
    "价格": "price", "供应": "supply", "库存": "inventory",
    "需求": "demand", "进出口": "trade", "成本": "cost", "平衡": "balance",
}
BOARD_DIM = {v: k for k, v in DIM_BOARD.items()}

# 板块→子类
BOARD_SUBDIRS = {
    "price": "盘面结构|现货与升贴水|海外价格|价差体系|估值与利润|持仓席位观察",
    "supply": "海外矿·财报产量|海外矿·分国别总量|国内矿产量|矿进口量与分国别|TC加工费|精炼产量|开工率与检修|再生/二次供应|冶炼利润→供应弹性",
    "inventory": "交易所库存|仓单|社会库存|工厂库存|隐性·在途",
    "demand": "初级消费|终端细分消费|需求先行指标",
    "trade": "原料进口|精炼金属进出口|制品出口|海外对华发运",
    "cost": "成本曲线与分位|日度利润测算|能源/原料成本",
    "balance": "年度锚（行业协会）|自建平衡表|表观消费拟合",
}

# 品种中文名
VAR_CN = {"CU": "铜", "AL": "铝", "ZN": "锌", "NI": "镍",
          "SN": "锡", "SI": "硅", "LI": "锂", "PB": "铅"}

VARIETIES = ['CU', 'AL', 'ZN', 'NI', 'SN', 'SI', 'LI', 'PB']

def load_kb():
    with open(KB_PATH, encoding='utf-8') as f:
        return json.load(f)

def get_ws_url():
    """从CDP /json端点自动发现chat页的WebSocket"""
    try:
        d = json.load(urllib.request.urlopen(f'http://127.0.0.1:{CDP_PORT}/json', timeout=5))
        for t in d:
            if t.get('type') == 'page' and '/chat' in t.get('url', ''):
                return t['webSocketDebuggerUrl']
    except Exception as e:
        print(f"[!] CDP发现失败: {e}")
    return None

def _cdp(ws_url, method, params=None, timeout=30):
    """CDP调用包装器（32位id + suppress_origin + error检查）"""
    conn = websocket.create_connection(ws_url, timeout=timeout+5, suppress_origin=True)
    socket.setdefaulttimeout(timeout)
    id_ = int(time.time()) % 2000000000
    conn.send(json.dumps({"id": id_, "method": method, "params": params or {}}))
    got = None
    while True:
        try:
            raw = conn.recv()
            msg = json.loads(raw)
        except Exception:
            break
        if msg.get("id") == id_:
            got = msg
            break
    conn.close()
    if got and "error" in got:
        raise RuntimeError(f"CDP {method}: {got['error'].get('message')}")
    return got

def eval_js(ws_url, expression, timeout=30):
    """在页面上下文执行JS"""
    result = _cdp(ws_url, "Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True,
    }, timeout=timeout)
    val = result.get("result", {}).get("result", {}).get("value")
    return val

def render_whitelist_prompt(variety, board):
    """渲染带白名单约束的prompt"""
    kb = load_kb()
    v_cn = VAR_CN.get(variety, variety)
    dim_cn = BOARD_DIM.get(board, board)
    subdirs = BOARD_SUBDIRS.get(board, "")
    
    items = kb.get(variety, {}).get(board, [])
    
    # 白名单表格
    if not items:
        return None
    
    wl_lines = [
        f"\n以下 {len(items)} 条指标已在钢联(Mysteel)/有色网(SMM)数据库中验证存在，",
        f"有连续数据序列。你只能从这些指标中选择，禁止推荐清单之外的指标名称：\n",
        "| 知几ID | 指标标准名称 | 频率 | 单位 | 数据点数 | 最近数据日期 |",
        "|--------|-------------|------|------|---------|------------|",
    ]
    for item in items:
        pts = item.get('points', '?')
        last = item.get('last_date', '?')
        freq = item.get('freq', '?')
        unit = item.get('unit', '?')
        wl_lines.append(f"| {item['id']} | {item['name']} | {freq} | {unit} | {pts} | {last} |")
    wl_lines.append("")
    whitelist_text = '\n'.join(wl_lines)
    
    subdir_list = '\n'.join(f"{i+1}. {s}" for i, s in enumerate(subdirs.split('|')))
    
    prompt = f"""角色：你是有色金属产业研究的「题材精准枚举器·复合图设计师」。你的唯一职责：对「{v_cn}·{dim_cn}」目录下的固定子类，精准枚举每个子类最核心的独立基础指标，并设计最能说明问题的**单图或多指标复合图**，数量严格受控。

【目录】固定以下子类：
{subdir_list}

【核心规则】
**规则1**：每个子类6-8个指标，最多10个。少比多好。
**规则2**：只枚举原始基础指标，不列环比/同比/增速等派生形态。
**规则3**：指标必须直接描述本子类题材对象。
**规则4**：每张图给出名称、形态与观测用途。

**规则8：数据源白名单约束（最高优先级）**
你只能从以下指标中选择和组合，禁止推荐清单之外的任何指标名称。白名单不足6个就有几个输出几个，不编造补数。

**规则8.1：必须回显知几ID（强制，便于自动校验）**
你引用的每个指标，必须在「包含指标」列里用「指标名（知几ID）」格式标注，例如「SHFE镍主力合约收盘价（FU00014997）」。
多指标用「+」连接，每个都带ID。禁止只写中文业务名而不带ID——否则下游无法自动核验该指标是否真在白名单内。

{whitelist_text}

【输出格式】每子类一张表格：
| 序号 | 图名称 | 包含指标(1-3个，每项标注知几ID) | 题材归属度 | 数据源 | 形态 | 观测用途 |"""
    return prompt

def inject_and_send(ws_url, prompt_text):
    """分片注入prompt + setText发送"""
    # 初始化
    eval_js(ws_url, "window.__W=[];'init'", timeout=10)
    
    # 分片注入
    chunk_size = 500
    chunks = [prompt_text[i:i+chunk_size] for i in range(0, len(prompt_text), chunk_size)]
    import json as j
    for chunk in chunks:
        js = f"window.__W.push({j.dumps(chunk)});window.__W.length"
        eval_js(ws_url, js, timeout=10)
    
    # setText注入
    set_text_js = """
(() => {
function findCI(root) {
    var stack = [root];
    while (stack.length) {
        var n = stack.shift();
        if (n.$options && n.$options.name === 'ChatInput') return n;
        if (n.$children) n.$children.forEach(function(c) { stack.push(c) });
    }
    return null;
}
var txt = window.__W.join('');
var app = document.querySelector('#app');
var root = app.__vue__ || app.__vue_app__;
var ci = findCI(root);
if (ci) { ci.setText(txt); return 'CI_OK'; }
// 降级：innerHTML
var ce = document.querySelector('[contenteditable]');
if (ce) {
    ce.innerHTML = '<p>' + txt.replace(/\\n/g, '<br>') + '</p>';
    ce.dispatchEvent(new InputEvent('input', {bubbles: true, data: 'x', inputType: 'insertText'}));
    return 'HTML_OK';
}
return 'NO_EDITOR';
})()
"""
    result = eval_js(ws_url, set_text_js, timeout=15)
    if result not in ('CI_OK', 'HTML_OK'):
        return False, f"注入失败: {result}"
    
    time.sleep(2)  # 等sendBtn渲染
    
    # CDP真实鼠标点击send-button
    rect_js = """
(() => {
var sb = document.querySelector('.send-button');
if (!sb) return null;
var r = sb.getBoundingClientRect();
return JSON.stringify({x: r.x + r.width/2, y: r.y + r.height/2});
})()
"""
    rect_str = eval_js(ws_url, rect_js, timeout=10)
    if not rect_str:
        return False, "send-button未渲染"
    
    import json as j
    coords = j.loads(rect_str) if isinstance(rect_str, str) else rect_str
    
    # CDP Input.dispatchMouseEvent
    _cdp(ws_url, "Input.dispatchMouseEvent", {
        "type": "mousePressed",
        "x": coords['x'], "y": coords['y'],
        "button": "left", "clickCount": 1
    }, timeout=10)
    _cdp(ws_url, "Input.dispatchMouseEvent", {
        "type": "mouseReleased",
        "x": coords['x'], "y": coords['y'],
        "button": "left", "clickCount": 1
    }, timeout=10)
    
    return True, "sent"

def wait_for_completion(ws_url, timeout=300):
    """等待AI生成完成（4条件：页脚+模型答案完成+答案关键词+长度稳定）"""
    start = time.time()
    prev_len = 0
    stable_count = 0
    
    while time.time() - start < timeout:
        status_js = """
(() => {
var t = document.body.innerText;
return JSON.stringify({
    len: t.length,
    done: t.lastIndexOf('模型答案生成完成') >= 0,
    footer: t.lastIndexOf('内容由AI生成') >= 0,
    hasContent: t.indexOf('图名称') >= 0 || t.indexOf('序号') >= 0
});
})()
"""
        try:
            result = eval_js(ws_url, status_js, timeout=15)
            import json as j
            s = j.loads(result) if isinstance(result, str) else result
            body_len = s.get('len', 0)
            done = s.get('done', False)
            footer = s.get('footer', False)
            has_content = s.get('hasContent', False)
            
            # 4条件同时满足
            if done and footer and has_content:
                if body_len == prev_len:
                    stable_count += 1
                    if stable_count >= 2:  # 连续2次稳定（~30秒）
                        return True, "完成"
                else:
                    stable_count = 0
                prev_len = body_len
            
            # 限流检测
            t = document_body(ws_url)
            if '暂时处理不过来' in t or '请稍后再试' in t:
                return False, "限流"
        except Exception as e:
            pass
        
        time.sleep(15)
    
    return False, "超时"

def document_body(ws_url):
    """获取body文本"""
    js = "document.body.innerText"
    return eval_js(ws_url, js, timeout=15) or ""

def extract_reply(ws_url, prompt_anchor="规则8"):
    """提取AI回复（去掉prompt回显）"""
    body = document_body(ws_url)
    # 用rfind找最后一次出现的完成标记
    done_idx = body.rfind('模型答案生成完成')
    if done_idx < 0:
        return body[-5000:] if len(body) > 5000 else body
    
    reply = body[done_idx + len('模型答案生成完成'):]
    footer_idx = reply.rfind('内容由AI生成')
    if footer_idx > 0:
        reply = reply[:footer_idx]
    
    return reply.strip()

def click_new_chat(ws_url):
    """点新对话清场"""
    new_chat_js = """
(() => {
    var items = document.querySelectorAll('.menu-item');
    for (var item of items) {
        if (item.textContent.indexOf('新对话') >= 0) {
            var r = item.getBoundingClientRect();
            var x = r.x + r.width/2, y = r.y + r.height/2;
            return JSON.stringify({x: x, y: y});
        }
    }
    return null;
})()
"""
    import json as j
    coords_str = eval_js(ws_url, new_chat_js, timeout=10)
    if not coords_str:
        return False
    
    coords = j.loads(coords_str) if isinstance(coords_str, str) else coords_str
    _cdp(ws_url, "Input.dispatchMouseEvent", {
        "type": "mousePressed", "x": coords['x'], "y": coords['y'],
        "button": "left", "clickCount": 1
    }, timeout=10)
    _cdp(ws_url, "Input.dispatchMouseEvent", {
        "type": "mouseReleased", "x": coords['x'], "y": coords['y'],
        "button": "left", "clickCount": 1
    }, timeout=10)
    time.sleep(3)
    return True

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {"done": [], "failed": []}

def save_state(state):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=1)

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true', help='全量跑')
    ap.add_argument('--variety', help='只跑指定品种')
    ap.add_argument('--board', help='只跑指定板块')
    ap.add_argument('--ws', help='WebSocket URL（不传则自动发现）')
    args = ap.parse_args()
    
    os.makedirs(OUT_DIR, exist_ok=True)
    
    # 构建任务列表
    kb = load_kb()
    tasks = []
    for v in VARIETIES:
        if v not in kb:
            continue
        if args.variety and v != args.variety:
            continue
        for dim_cn, board in DIM_BOARD.items():
            if args.board and board != args.board:
                continue
            items = kb.get(v, {}).get(board, [])
            if len(items) < 3:
                continue
            tasks.append({'variety': v, 'board': board, 'dim': dim_cn})
    
    state = load_state()
    
    print(f"任务总数: {len(tasks)}")
    print(f"已完成: {len(state['done'])}")
    print(f"已失败: {len(state['failed'])}")
    
    for i, task in enumerate(tasks):
        task_id = f"{task['variety']}_{task['board']}"
        
        if task_id in state['done']:
            print(f"[{i+1}/{len(tasks)}] {task_id} SKIP (已完成)")
            continue
        
        print(f"\n[{i+1}/{len(tasks)}] {task_id} 开始...")
        
        # 渲染prompt
        prompt = render_whitelist_prompt(task['variety'], task['board'])
        if not prompt:
            print(f"  跳过：白名单为空")
            continue
        
        # 确认prompt长度
        if len(prompt) > 10000:
            print(f"  ⚠️ Prompt {len(prompt)}字符超10000限制，跳过")
            continue
        
        # 获取WS URL
        ws_url = args.ws
        if not ws_url:
            ws_url = get_ws_url()
        if not ws_url:
            print(f"  [!] 无法获取CDP WebSocket，等待10秒重试...")
            time.sleep(10)
            ws_url = get_ws_url()
            if not ws_url:
                print(f"  [!] 仍然无法连接，跳过")
                state['failed'].append(task_id)
                save_state(state)
                continue
        
        try:
            # 点新对话清场
            click_new_chat(ws_url)
            time.sleep(3)
            
            # 注入+发送
            ok, msg = inject_and_send(ws_url, prompt)
            if not ok:
                print(f"  发送失败: {msg}")
                state['failed'].append(task_id)
                save_state(state)
                time.sleep(45)
                continue
            
            print(f"  发送成功，等待AI生成...")
            
            # 等待完成
            ok, msg = wait_for_completion(ws_url, timeout=300)
            if not ok:
                print(f"  生成失败: {msg}")
                state['failed'].append(task_id)
                save_state(state)
                time.sleep(60)
                continue
            
            # 提取回复
            reply = extract_reply(ws_url)
            
            # 保存
            out_file = os.path.join(OUT_DIR, f"{task_id}_whitelist.md")
            with open(out_file, 'w', encoding='utf-8') as f:
                f.write(f"> 品种: {task['variety']} ({VAR_CN.get(task['variety'],'')})\n")
                f.write(f"> 板块: {task['dim']}\n")
                f.write(f"> 白名单指标数: {len(kb.get(task['variety'],{}).get(task['board'],[]))}\n")
                f.write(f"> 抓取时间: {time.strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"> 方式: 白名单约束发散 v1\n\n")
                f.write(reply)
            
            print(f"  ✅ 保存: {out_file} ({len(reply)}字符)")
            state['done'].append(task_id)
            save_state(state)
            
        except Exception as e:
            print(f"  [!] 异常: {e}")
            state['failed'].append(task_id)
            save_state(state)
        
        # 冷却
        cooldown = 50
        if (i + 1) % 5 == 0:
            cooldown = 120  # 每5轮额外冷却
        print(f"  冷却 {cooldown}秒...")
        time.sleep(cooldown)
    
    print(f"\n=== 完成 ===")
    print(f"成功: {len(state['done'])}")
    print(f"失败: {len(state['failed'])}")
    if state['failed']:
        print(f"失败列表: {state['failed']}")

if __name__ == '__main__':
    main()
