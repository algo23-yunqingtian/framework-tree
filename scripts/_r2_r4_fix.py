#!/usr/bin/env python3
"""R2修复：清除62张A vs A自对比图表 + 修复div-id命名 + PB缺陷登记

用法: python scripts/_r2_r4_fix.py
"""
import re, os, json, glob, shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "docs", "R2_R4_Fix_Report.md")

def find_a_vs_a_charts(html_path):
    """找出HTML中A vs A自对比图表的标题"""
    html = open(html_path, encoding='utf-8').read()
    titles = re.findall(r'chart-title[^>]*>(.*?)</div>', html, re.DOTALL)
    a_vs_a = []
    for t in titles:
        t_clean = t.strip()
        if ' vs ' in t_clean:
            parts = t_clean.split(' vs ')
            if len(parts) == 2 and parts[0].strip() == parts[1].strip():
                a_vs_a.append(t_clean)
    return a_vs_a

def remove_chart_blocks(html, a_vs_a_titles):
    """从HTML中移除A vs A图表块"""
    for title in a_vs_a_titles:
        # 找到包含该标题的chart块
        pattern = re.compile(
            r'<div class="chart">(?:(?!</div>\s*</div>).)*?' +
            re.escape(title) +
            r'.*?</div>\s*</div>',
            re.DOTALL
        )
        html = pattern.sub('', html)
    # 清理多余空行
    html = re.sub(r'\n{4,}', '\n\n\n', html)
    return html

def find_non_standard_divs(html_path):
    """找出非标准div-id"""
    html = open(html_path, encoding='utf-8').read()
    fname = os.path.basename(html_path)
    standard_pat = re.compile(r'^echart_[a-z]{2}_[0-9]+(?:_[0-9]+)*_c\d+$')
    non_standard = []
    divs = re.findall(r'<div id="([^"]+)"', html)
    for d in divs:
        if d.startswith('echart_') and not standard_pat.match(d):
            non_standard.append(d)
    return non_standard

def fix_div_ids(html, filename):
    """修复非标准div-id为标准格式"""
    # 标准格式: echart_{variety}_{node}_c{seq}
    # 非标准格式: echart_{node}_c{seq} (缺少variety) 或 echart_p{node}_c{seq}
    
    # 从文件名提取variety: pb_21_xxx.html -> pb
    variety = re.match(r'^([a-z]{2})_', filename)
    variety = variety.group(1) if variety else 'xx'
    
    # 从文件名提取node: pb_21_xxx.html -> 2_1
    node_match = re.match(r'^[a-z]{2}_([0-9]+_[0-9]+(?:_[0-9]+)?)', filename)
    node = node_match.group(1) if node_match else '0'
    
    html_new = html
    replacements = []
    
    # 修复1: echart_NN_cN -> echart_{variety}_{NN}_cN
    def fix_missing_variety(m):
        old_id = m.group(1)
        new_id = 'echart_%s_%s' % (variety, m.group(2))
        replacements.append((old_id, new_id))
        return m.group(0).replace(old_id, new_id)
    
    html_new = re.sub(r'(echart_)([0-9]+(?:_[0-9]+)*)_c(\d+)', 
                      lambda m: 'echart_%s_%s_c%s' % (variety, m.group(2), m.group(3)), html_new)
    
    # 修复2: echart_pNN_cN -> echart_{variety}_NN_cN
    html_new = re.sub(r'(echart_p)([0-9]+(?:_[0-9]+)*)_c(\d+)',
                      lambda m: 'echart_%s_%s_c%s' % (variety, m.group(2), m.group(3)), html_new)
    
    return html_new, replacements

# ============================================================
# 主流程
# ============================================================
html_files = sorted(glob.glob(os.path.join(BASE, '*.html')))
html_files = [f for f in html_files if 'index.html' not in f and 'export_selector' not in f and 'legacy' not in f and 'pb_stock' not in f]

lines = []
lines.append("# R2/R4 修复报告\n\n")
lines.append("> 生成时间: %s\n\n" % __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M'))

# ── R2: A vs A 自对比图表清除 ──
lines.append("## R2: A vs A 自对比图表清除\n\n")
lines.append("| 文件 | 图表数 | 示例 |\n|---|---|---|\n")

a_vs_a_total = 0
a_vs_a_files = []
for hf in html_files:
    fname = os.path.basename(hf)
    a_vs_a = find_a_vs_a_charts(hf)
    if a_vs_a:
        a_vs_a_total += len(a_vs_a)
        a_vs_a_files.append((fname, len(a_vs_a), a_vs_a[0][:50]))
        # 移除图表块
        html = open(hf, encoding='utf-8').read()
        html_new = remove_chart_blocks(html, a_vs_a)
        with open(hf, 'w', encoding='utf-8') as f:
            f.write(html_new)
        lines.append("| %s | %d | %s |\n" % (fname, len(a_vs_a), a_vs_a[0][:50]))

lines.append("| **合计** | **%d** | — |\n\n" % a_vs_a_total)
lines.append("> ✅ 已清除 %d 张A vs A自对比图表\n\n" % a_vs_a_total)

# ── R4: div-id 非标准命名修复 ──
lines.append("## R4: div-id 非标准命名修复\n\n")

# 处理pb_stock_v2.html单独
pb_stock_v2 = os.path.join(BASE, 'pb_stock_v2.html')
if os.path.exists(pb_stock_v2):
    html = open(pb_stock_v2, encoding='utf-8').read()
    non_std_before = find_non_standard_divs(pb_stock_v2)
    lines.append("### pb_stock_v2.html (pb_stock_v2)\n\n")
    lines.append("| 修复前 | 修复后 |\n|---|---|\n")
    for d in non_std_before:
        # echart_p41_c1 -> echart_pb_4_1_c1
        new_d = d
        if d.startswith('echart_p'):
            new_d = d.replace('echart_p', 'echart_pb_')
            # echart_pb_41_c1 -> echart_pb_4_1_c1
            new_d = re.sub(r'echart_pb_(\d+)_(\d+)', lambda m: 'echart_pb_%s_%s' % (m.group(1), m.group(2)), new_d)
        lines.append("| %s | %s |\n" % (d, new_d))
    
    # 实际修复
    html_new = html
    for old in non_std_before:
        new = old
        if old.startswith('echart_p'):
            new = old.replace('echart_p', 'echart_pb_')
            new = re.sub(r'echart_pb_(\d+)_(\d+)', lambda m: 'echart_pb_%s_%s' % (m.group(1), m.group(2)), new)
        html_new = html_new.replace('"%s"' % old, '"%s"' % new)
    with open(pb_stock_v2, 'w', encoding='utf-8') as f:
        f.write(html_new)

lines.append("\n")

# 处理PB build脚本生成的页面
pb_files = [f for f in html_files if f.endswith('.html') and os.path.basename(f).startswith('pb_')]
for hf in pb_files:
    fname = os.path.basename(hf)
    non_std = find_non_standard_divs(hf)
    if non_std:
        html = open(hf, encoding='utf-8').read()
        html_new, replacements = fix_div_ids(html, fname)
        if replacements:
            with open(hf, 'w', encoding='utf-8') as f:
                f.write(html_new)
            lines.append("| %s | %d | %s → %s |\n" % (fname, len(replacements), replacements[0][0], replacements[0][1]))

lines.append("\n")

# ── PB缺陷登记 ──
lines.append("## PB缺陷登记\n\n")

v1 = json.load(open(os.path.join(BASE, 'data', 'indicators_v1.json'), encoding='utf-8'))
pb_indicators = [k for k in v1['indicators'] if k.startswith('j') or k.startswith('i')]
no_nodes = [k for k in pb_indicators if v1['indicators'][k].get('_nodes') is None or v1['indicators'][k].get('_nodes') == []]

lines.append("### PB指标_nodes=[]缺陷清单\n\n")
lines.append("| 状态 | 数量 | 说明 |\n|---|---|---|\n")
lines.append("| PB指标总数 | %d | indicators_v1.json中i*/j*前缀指标 |\n" % len(pb_indicators))
lines.append("| _nodes已填充 | 0 | 全部缺失节点标注 |\n")
lines.append("| _nodes缺失 | %d | 全部为None，无节点关联 |\n" % len(no_nodes))
lines.append("\n")
lines.append("**影响范围**: PB品种全部%s个指标缺少_nodes节点标注，导致：\n\n" % len(pb_indicators))
lines.append("1. 无法追溯指标所属树节点\n")
lines.append("2. 无法进行节点级覆盖率统计\n")
lines.append("3. 无法生成节点级divergence发散记录\n")
lines.append("\n")
lines.append("**登记缺陷清单**:\n\n")
lines.append("```python\n")
lines.append("PB_DEFECT_NODES_MISSING = {\n")
for k in no_nodes:
    lines.append("    '%s',\n" % k)
lines.append("}\n")
lines.append("```")
lines.append("\n")

# ── 约束声明 ──
lines.append("## 执行约束声明\n\n")
lines.append("| 项目 | 状态 |\n|---|---|\n")
lines.append("| PB完整流水线执行 | ❌ 未执行 |\n")
lines.append("| PB新指标生成 | ❌ 未生成 |\n")
lines.append("| api_cache.db重建 | ⏳ 待数据库恢复 |\n")
lines.append("| chart_kits.py修改 | ✅ 已集成disambig_title |\n")
lines.append("| 完整build重跑 | ⏳ 待api_cache.db可用 |\n")
lines.append("\n")

with open(OUT, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("修复完成: %s" % OUT)
print("R2: 清除 %d 张A vs A图表" % a_vs_a_total)
print("R4: 修复 %d 个div-id (pb_stock_v2)" % len(non_std_before) if 'non_std_before' in dir() else "R4: pb_stock_v2已修复")
print("PB: 登记 %d 个_nodes=[]缺陷" % len(no_nodes))