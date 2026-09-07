#!/usr/bin/env python3
"""
白名单渲染器：从 knowledge_base.json 提取指定品种+板块的可用指标，
输出 markdown 表格，嵌入同花顺 prompt 作为规则8白名单约束。

用法：
  python3 scripts/render_whitelist.py --variety CU --board price
  python3 scripts/render_whitelist.py --variety CU --board all
  python3 scripts/render_whitelist.py --variety CU  # 所有板块

输出：markdown 表格（| ID | 指标名 | 频率 | 单位 | 数据点数 | 最近日期 |）
"""
import json, sys, argparse
from pathlib import Path

KB_PATH = Path(__file__).parent.parent / 'analysis' / 'knowledge_base.json'

# 板块中文名
BOARD_CN = {
    'price': '价格',
    'supply': '供给',
    'inventory': '库存',
    'demand': '需求',
    'trade': '进出口',
    'cost': '成本',
    'balance': '平衡',
    'other': '其他',
}

def load_kb():
    if not KB_PATH.exists():
        print(f"[!] knowledge_base.json 不存在: {KB_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def render_board(items, board_cn):
    """渲染单个板块的 markdown 表格"""
    if not items:
        return f"**{board_cn}板块**：暂无已验证可用指标。\n"
    
    lines = [f"**{board_cn}板块**（已验证 {len(items)} 条）：\n"]
    lines.append("| 知几ID | 指标标准名称 | 频率 | 单位 | 数据点数 | 最近数据日期 |")
    lines.append("|--------|-------------|------|------|---------|------------|")
    for item in items:
        pts = item.get('points', '?')
        last = item.get('last_date', '?')
        freq = item.get('freq', '?')
        unit = item.get('unit', '?')
        lines.append(f"| {item['id']} | {item['name']} | {freq} | {unit} | {pts} | {last} |")
    lines.append("")
    return '\n'.join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--variety', required=True, help='品种代码 CU/AL/ZN/NI/SN/SI/LI/PB')
    ap.add_argument('--board', default='all', help='板块: price/supply/inventory/demand/trade/cost/balance/all')
    args = ap.parse_args()
    
    v = args.variety.upper()
    kb = load_kb()
    
    if v not in kb:
        print(f"[!] 品种 {v} 不在 knowledge_base.json 中", file=sys.stderr)
        sys.exit(1)
    
    boards = list(BOARD_CN.keys()) if args.board == 'all' else [args.board]
    
    output_parts = []
    for board in boards:
        if board == 'other':
            continue
        items = kb[v].get(board, [])
        board_cn = BOARD_CN.get(board, board)
        output_parts.append(render_board(items, board_cn))
    
    whitelist_text = '\n'.join(output_parts)
    print(whitelist_text)

if __name__ == '__main__':
    main()
