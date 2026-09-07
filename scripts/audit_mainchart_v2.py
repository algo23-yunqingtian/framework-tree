#!/usr/bin/env python3
"""audit_mainchart_v2.py — 第二代主图质量审计器
系统性检测所有已建页的主图问题，输出三类：
  [PLACEHOLDER] 价格万能占位（非价格板块主图却是价格类）
  [WRONG-MAIN]  主图≠同花顺A级正主 / 板块错配
  [SCOPE-ISSUE] 口径缩水（地名分库被当总量用）
  [OK-REVIEWED] 已修正/对题（含 MAIN_METRIC 显式覆盖）
用法: python3 scripts/audit_mainchart_v2.py [--json out.json]
"""
import re, os, glob, json, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CORR_DIR = "translation-workspace/correction"
cidmap = {'CU':'cu','AL':'al','NI':'ni','SN':'sn','SI':'si','LI':'li','ZN':'zn','PB':'pb'}

# ---------- 1. 解析 indicators_v1.json ----------
ind = json.load(open('data/indicators_v1.json', encoding='utf-8'))['indicators']

# ---------- 2. 解析 correction 文档 -> (variety, node) -> list of A级正主 ----------
iwcs = defaultdict(list)
for f in sorted(glob.glob(f"{CORR_DIR}/**/*_correction*.md", recursive=True)):
    v = os.path.basename(os.path.dirname(f))
    for line in open(f, encoding='utf-8'):
        if not line.strip().startswith('|'): continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) < 8 or not re.match(r'^\d+$', cells[0]): continue
        node, graph = cells[1], cells[2]
        if not re.match(r'^\d', node): continue
        zhiji_id = cells[4] if re.search(r'ID\d|a1\d|FU\d', cells[4], re.I) else \
                   (cells[5] if len(cells)>5 and re.search(r'ID\d|a1\d|FU\d', cells[5], re.I) else '')
        zhiji_name = cells[5] if len(cells) > 5 and '：' in cells[5] else ''
        level = cells[-2] if len(cells) >= 8 else '?'
        iwcs[(v, node)].append({'graph': graph, 'id': zhiji_id, 'zhiji_name': zhiji_name, 'level': level})

# ---------- 3. 板块主题 / 关键词 ----------
def board_of(node):
    for k,b in [('2.','价格'),('3.','供给'),('4.','库存'),('5.','需求'),('6.','进出口'),('7.','成本')]:
        if node.startswith(k): return b
    return '?'

PRICE_KW = ['主力','收盘价','结算价','开盘价','最高价','最低价','升贴水','基差','月差','价差','溢价','比价','压价','贴水','premium','basis','spread']
BOARD_KW = {
    '价格':   ['收盘','结算','持仓','月差','升贴水','基差','溢价','席位','比价','套利'],
    '供给':   ['矿产','产量','开工','产能','冶炼','加工费','TC','矿','检修','再生','弹性'],
    '库存':   ['库存','仓单','注销','在途','隐性','厂内'],
    '需求':   ['消费','需求','表观','开工率','订单','排产'],
    '进出口': ['进口','出口','发运','到港','通关','海关'],
    '成本':   ['成本','利润','加工费','TC','电价','硫酸','毛利','净利','现金成本'],
}
# 口径缩水：地名分库（非总量）
SCOPE_CITY = ['迪拜','香港','埃及','巴林','光阳','鹿特丹','釜山','新加坡','马来西亚','印尼','缅甸']
SCOPE_TOTAL_KW = ['总量','总计','总库','全口径','全部','global','total','总库存','合计']
def scope_issue(name):
    """若名字含地名分库（且不含总量词），判定口径缩水"""
    if not name: return False
    has_city = any(c in name for c in SCOPE_CITY)
    is_total = any(t in name for t in SCOPE_TOTAL_KW)
    return has_city and not is_total

# ---------- 4. 逐节点审计 ----------
def page_main_metric(cid, node):
    """读页面主图 (mid, name)。解析 chart-title / chart-sub"""
    f = f"{cid}_{node.replace('.','_')}.html"
    if not os.path.isfile(f): return None, None, None
    h = open(f, encoding='utf-8').read()
    # 主图块：chart-title ...（主图·XXX）
    m = re.search(r'chart-title">([^<]*?)（主图', h)
    main_name = m.group(1).strip() if m else None
    # chart-sub 里的 mid
    m2 = re.search(r'chart-title">[^<]*?（主图[^<]*</div><div class="chart-sub">([a-z0-9_]+)', h)
    main_mid = m2.group(1) if m2 else None
    return main_mid, main_name, f

def analyze(verbose=True):
    results = []
    pages_done = set()
    for (v,node), corr in sorted(iwcs.items()):
        cid = cidmap.get(v)
        if not cid: continue
        mid, name, f = page_main_metric(cid, node)
        if f is None: 
            continue  # 缺页不审计
        pages_done.add(f)
        bl = board_of(node)
        if not mid:
            results.append({'variety':v,'node':node,'status':'UNPARSED','main_mid':mid,'main_name':name,'note':'主图解析失败','board':bl})
            continue
        # 判定
        is_price = any(k in (name or '') for k in PRICE_KW)
        status = None; note = ''
        # 1) 价格万能占位
        if is_price and bl != '价格':
            status = 'PLACEHOLDER'
            note = '非价格板块主图是价格类'
        # 2) 口径缩水
        elif scope_issue(name):
            status = 'SCOPE-ISSUE'
            note = '口径缩水：地名分库可能被当总量'
        # 3) 对照同花顺 A 级正主（ID 或图名关键词）
        else:
            a_grade = [c for c in corr if c['level'] in ('A','A ')]
            matched = False
            for c in a_grade:
                cidv = c['id']
                if cidv:
                    # 页面主图 mid 对应指标的 ids 是否含同花顺 ID
                    mmeta = ind.get(mid, {})
                    ids_all = {str(x).upper() for x in mmeta.get('ids', {}).values()}
                    if cidv.upper() in ids_all:
                        matched = True; break
                gn = re.sub(r'\s+','', c['graph'])
                nn = re.sub(r'\s+','', name or '')
                if gn and (gn in nn or (len(gn)>=4 and gn[:4] in nn)):
                    matched = True; break
            if matched:
                status = 'OK-A'
                note = '主图=同花顺A级正主'
            elif a_grade:
                status = 'WRONG-MAIN'
                a_names = ' / '.join(c['graph'][:20] for c in a_grade[:3])
                note = f'同花顺A级正主: {a_names}'
            else:
                status = 'OK-FALLBACK'
                note = '无A级对照（correction无该节点A级）'
        results.append({'variety':v,'node':node,'status':status,'main_mid':mid,
                        'main_name':name,'note':note,'board':bl})
    
    # 汇总统计
    stat = defaultdict(int)
    for r in results: stat[r['status']] += 1
    if verbose:
        print(f"=== 主图质量审计 v2（{len(results)} 节点, 页面 {len(pages_done)}）===")
        print(f"状态分布: {dict(stat)}")
        print("\n--- 需要处理 ---")
        for r in results:
            if r['status'] in ('PLACEHOLDER','WRONG-MAIN','SCOPE-ISSUE','UNPARSED'):
                print(f"[{r['status']}] {r['variety']}.{r['node']} ({r['board']}) 主图={r['main_name']} | {r['note']}")
        print(f"\n--- 已修正/OK ({stat.get('OK-A',0)+stat.get('OK-FALLBACK',0)}) ---")
        for r in results:
            if r['status'] in ('OK-A','OK-FALLBACK'):
                print(f"[{r['status']}] {r['variety']}.{r['node']} {r['main_name'][:36]}")
    return results, dict(stat)

if __name__ == '__main__':
    results, stat = analyze()
    if '--json' in sys.argv:
        i = sys.argv.index('--json')
        json.dump(results, open(sys.argv[i+1],'w',encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f"\nJSON 已存 {sys.argv[i+1]}")