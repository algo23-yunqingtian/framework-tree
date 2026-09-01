#!/usr/bin/env python3
"""图表质量审计脚本 - 扫描所有页面检测三类问题: SAME_AXIS / WRONG_NODE / FOOTER_FOREIGN"""
import os, re, json

os.chdir('/home/ubuntu/framework-tree')
all_html = [f for f in os.listdir('.') if f.endswith('.html') and f != 'index.html' and 'overview' not in f]
id_pat = re.compile(r'(?:ni|zn|cu|al|sn|si|li|pb)_\d+\w*')

report = {'same_axis': [], 'wrong_node': [], 'footer_foreign': []}

for f in sorted(all_html):
    prefix = f.split('_')[0]
    parts = f.replace('.html','').split('_')
    node_num = '_'.join(parts[1:])
    content = open(f, encoding='utf-8').read()

    # SAME_AXIS: left == right in "A vs B" chart titles
    for left, right in re.findall(r'>\s*([^<]{10,80}?)\s+vs\s+([^<]{10,80}?)\s*<', content):
        if left.strip() == right.strip():
            report['same_axis'].append({'file': f, 'title': left.strip()[:80]})

    # Chart zone vs footer zone
    footer_idx = content.find('<footer>')
    chart_zone = content[:footer_idx] if footer_idx > 0 else content

    all_chart_ids = set(id_pat.findall(chart_zone))
    foreign_chart = sorted(i for i in all_chart_ids if not i.startswith(prefix))
    if foreign_chart:
        report['footer_foreign'].append({'file': f, 'ids': foreign_chart[:5]})

    native_ids = set(i for i in all_chart_ids if i.startswith(prefix))
    expected = prefix + '_' + node_num.replace('_', '')
    wrong = sorted(i for i in native_ids if not i.startswith(expected))
    if wrong and len(wrong) > len(native_ids) * 0.4:
        report['wrong_node'].append({'file': f, 'wrong_ids': wrong[:5], 'ratio': f'{len(wrong)}/{len(native_ids)}'})

with open('audit_chart_quality_report.json', 'w') as out:
    json.dump(report, out, ensure_ascii=False, indent=2)

print(f"SAME_AXIS: {len(report['same_axis'])}")
print(f"WRONG_NODE: {len(report['wrong_node'])}")
print(f"FOOTER_FOREIGN: {len(report['footer_foreign'])}")
print("Report saved to audit_chart_quality_report.json")
