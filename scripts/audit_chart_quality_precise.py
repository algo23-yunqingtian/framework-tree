#!/usr/bin/env python3
"""精确 P1/P2/P3 图表质量审计 v2

判定标准（对齐旧审计报告的口径）：

P1 WRONG_NODE（指标串节点）：
    页面 chart 区出现的指标 ID（如 cu_321_import、al_62_import）中，
    若品种前缀与页面所属品种不一致 → 记为"跨品种串节点"。
    这是最硬性的 bug——铜页出现铝的指标 ID，属于真串台。
    ⚠️ 部分历史页（如 cu_6_2）的跨品种指标已被明确标注为"跨金属辅助参照"，
       这些不算 P1 bug，归类为 P3 信息项。
       判定规则：页面 NOTE 区若出现 "跨金属辅助参照" 字样 → 该跨品种 mid 豁免。

P2 FOOTER_FOREIGN（页脚跨品种）：
    <footer> 元素内出现的品种中文名，若与本页品种不一致，且不是通用名称。
    这是页脚文案生成的模板错误，属于批量引擎的模板串台。

P3 CROSS_VARIETY（chart 区跨品种，无 NOTE 声明）：
    跨品种 mid 出现但页面没有"跨金属辅助参照"等明确声明 → 需核查。
    这类应视为待人工确认项，不算 P1 硬性 bug，但需要补声明或换指标。
"""
import os, re, json, collections

os.chdir('/home/ubuntu/framework-tree')
all_html = [f for f in os.listdir('.') if f.endswith('.html')
            and f != 'index.html' and 'overview' not in f and 'export' not in f]

# 完整的指标 ID 正则：
# 严格要求 mid 前一个字符不是字母（避免 al_25_close_quantile 误抓 "cu"）
# mid 结构：品种(2-4字母) + 数字 + 可选 字母/下划线/数字 后缀
MID_PAT = re.compile(r'(?<![a-z0-9_])(?:zn|ni|cu|al|sn|si|li|pb)_\d+(?:_\w+)?')
VARIETY_CN = {'zn':'锌','ni':'镍','cu':'铜','al':'铝','sn':'锡','si':'硅','li':'锂','pb':'铅'}
# 页脚里的品种名可能是 "铜(CU)"、"铝(AL)"、"锡(SN)" 等
VARIETY_IN_FOOTER = re.compile(r'(铜|铝|铅|锌|镍|锡|硅)\(([A-Z]{1,3})\)')

def page_variety(f):
    return f.split('_')[0]

p1 = []   # 跨品种串节点（硬 bug）
p2 = []   # footer 跨品种
p3 = []   # chart 区跨品种但已声明辅助（信息项）
p3_undisc = []  # chart 区跨品种但无声明（待核查）

for f in sorted(all_html):
    prefix = page_variety(f)
    content = open(f, encoding='utf-8').read()

    footer_start = content.lower().rfind('<footer')
    footer_end = content.lower().rfind('</footer>')
    if footer_start >= 0 and footer_end > footer_start:
        chart_zone = content[:footer_start]
        footer_zone = content[footer_start:footer_end+8]
    else:
        chart_zone = content
        footer_zone = ''

    note_zone = chart_zone.lower()

    # 声明检查
    declared_cross_metal = '跨金属辅助参照' in note_zone or '跨金属辅助' in note_zone

    # 所有 chart 区的指标 ID
    chart_mids = MID_PAT.findall(chart_zone)
    chart_mids_unique = list(set(chart_mids))
    mid_varieties = collections.Counter(m.split('_')[0] for m in chart_mids_unique)

    # P1：跨品种 mid（硬 bug）
    foreign_mids = [m for m in chart_mids_unique if m.split('_')[0] != prefix]
    if foreign_mids:
        if declared_cross_metal:
            p3.append({'file': f, 'expected': prefix,
                       'foreign_mids': foreign_mids, 'status': 'declared'})
        else:
            p1.append({'file': f, 'expected': prefix,
                       'foreign_mids': foreign_mids,
                       'status': 'UNDISCLOSED',
                       'need_action': '补"跨金属辅助参照"声明 或 换成本品种指标'})
            p3_undisc.append(f)

    # P2：footer 跨品种（页脚文案）
    footer_varieties = VARIETY_IN_FOOTER.findall(footer_zone)
    footer_varieties_clean = [m[1] for m in footer_varieties]  # CU, AL 等
    expected_upper = prefix.upper()
    # 特殊映射
    upper_map = {'zn':'ZN','ni':'NI','cu':'CU','al':'AL','sn':'SN','si':'SI','li':'LI','pb':'PB'}
    expected_upper = upper_map.get(prefix, prefix.upper())
    foreign_footer = [v for v in footer_varieties_clean if v != expected_upper]
    if foreign_footer:
        p2.append({'file': f, 'expected': expected_upper,
                   'footer_varieties': footer_varieties_clean[:5],
                   'foreign': foreign_footer})

report = {
    'P1_wrong_node': p1,
    'P2_footer_foreign': p2,
    'P3_declared_cross': p3,
    'counts': {
        'P1': len(p1),
        'P2': len(p2),
        'P3_declared': len(p3)
    }
}

with open('audit_chart_quality_precise.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("=" * 60)
print(f"P1 WRONG_NODE (硬bug):     {report['counts']['P1']} 页")
print(f"P2 FOOTER_FOREIGN:        {report['counts']['P2']} 页")
print(f"P3 DECLARED CROSS(信息):   {report['counts']['P3_declared']} 页")
print("=" * 60)
print("\n--- P1 样本 (前10) ---")
for r in p1[:10]:
    print(f"  {r['file']} | 期望={r['expected']} | 跨品种={r['foreign_mids']}")
print(f"\n--- P2 样本 (前10) ---")
for r in p2[:10]:
    print(f"  {r['file']} | footer含={r['footer_varieties']} | foreign={r['foreign']}")
print(f"\n--- P3 declared 样本 (前5) ---")
for r in p3[:5]:
    print(f"  {r['file']} | 期望={r['expected']} | 跨品种={r['foreign_mids']}")