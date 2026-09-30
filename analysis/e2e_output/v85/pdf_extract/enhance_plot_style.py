#!/usr/bin/env python3
"""
DSH-B_PLOT_STYLE_ENHANCE_OPTIMIZE_TASK
======================================
Enhance plot_style recognition with 4 new enums:
  - 复合混合(折线+柱状)
  - 双Y轴复合
  - 堆叠柱状
  - 堆叠面积

Re-identify 30 multi-legend charts based on legend structure clues.

Output: pdf_chart_meta_all_v2.json / .csv
"""
import json
import csv
import re
from collections import Counter

INPUT_JSON = "pdf_chart_meta_all.json"
INPUT_CSV = "pdf_chart_meta_all.csv"
OUTPUT_JSON = "pdf_chart_meta_all_v2.json"
OUTPUT_CSV = "pdf_chart_meta_all_v2.csv"

# ═══════════════════════════════════════════════════════════
# NOISE FILTERING
# ═══════════════════════════════════════════════════════════

UNIT_EXACT = frozenset({
    # Chinese units
    "元", "吨", "万元", "万吨", "亿元", "亿", "千吨", "%", "％",
    "GWh", "MWh", "GW", "MW", "kW", "kVA", "MVA", "Gwh", "MWH",
    "万金属吨", "万实物吨", "万t", "pp", "bp", "bps",
    "元/吨", "元/吨元/吨", "元/50基吨", "元/镍点", "元/度吨",
    "元/湿吨", "美元/湿吨", "美元/吨", "美元/磅", "元/千克",
    "美元/吨·日", "美元/吨·周", "美元/吨·月", "美元/吨·年",
    "元/吨·日", "元/吨·周", "元/吨·月", "元/吨·年",
    "万实物吨万金属吨", "万金属吨万金属吨", "吨吨", "万吨万吨",
    "万万吨吨万吨", "天万吨", "亿个GW", "亿个",
    "0万吨", "0吨", "0美元/吨",
    "%%%", "%%%/金属吨", "%/金属吨100", "%/金属吨",
    "元/吨/吨", "元/吨·日", "元/吨·天", "元/吨·月",
    "日度", "周度", "月度", "累计",
    "MWHMWH", "MWHMWHMWH",
})

# Noise regex patterns
NOISE_RE = [
    re.compile(r'^[a-zA-Z%/()：.·、，。\-—\s]+$'),
    re.compile(r'^[0-9%.,\s\-—()+／/]*[a-zA-Z]*$'),
    re.compile(r'[。！？；]'),
    re.compile(r'[，；：]'),
    re.compile(r'^汇总.*$'),
]

# Known real series names that look like noise
REAL_SERIES = frozenset({
    "Risk", "Reversal", "Curve", "SPX", "vs",
    "Cash", "连续合约", "连一", "连二", "连三", "连四", "连五",
    "India", "Russia", "Russia2021年", "0万吨",
    "总消费", "交通运输", "房屋建筑", "家电", "电力", "净出口",
})

def is_noise(t):
    """Return True if legend entry is noise (unit/label/paragraph fragment)."""
    t = t.strip()
    if not t or t in UNIT_EXACT:
        return True
    if t in REAL_SERIES:
        return False
    # Pure ASCII/punctuation
    if re.match(r'^[a-zA-Z%/()：.·、，。\-—\s0-9]+$', t):
        return True
    # Trailing colon
    if t.endswith(':') or t.endswith('：'):
        return True
    # Number + unit
    if re.match(r'^[\d.]+\s*(万吨|万元|亿|吨|元|%|％|GWh|MWh|GW|MW)$', t):
        return True
    # Chinese sentence fragments (comma/period/semicolon) — but NOT DSH indicator names with colons
    for pat in NOISE_RE:
        if pat.search(t):
            # Exception: DSH indicator names use Chinese colons as delimiters
            # If the text has 2+ Chinese-colon-separated segments with Chinese chars, it's likely a valid indicator
            if pat.pattern == r'[，；：]':
                segments = t.split('：')
                chinese_segments = [s for s in segments if s.strip() and any('\u4e00' <= ch <= '\u9fff' for ch in s)]
                if len(chinese_segments) >= 2:
                    continue  # This is a DSH indicator name, not noise
            return True
    # Contains 图：or 图图
    if '图：' in t or '图图' in t:
        return True
    # Parenthetical unit
    if re.search(r'（[a-zA-Z%/·]+）$', t):
        return True
    # Starts with "汇总"
    if t.startswith('汇总'):
        return True
    # Pure numbers with unit
    if re.match(r'^[\d.]+[a-zA-Z%‰]+$', t):
        return True
    return False

def real_legends(ll):
    return [x for x in ll if not is_noise(x)]


# ═══════════════════════════════════════════════════════════
# PLOT STYLE IDENTIFICATION
# ═══════════════════════════════════════════════════════════

def classify(chart):
    """
    Enhanced plot_style classification.
    Returns (new_style, new_axis, reason).
    """
    title = chart.get('chart_title', '')
    legends = chart.get('legend_list', [])
    old_axis = chart.get('axis_info', '单Y轴')
    old_style = chart.get('plot_style', '单折线')
    rl = real_legends(legends)
    n = len(rl)

    # Single or zero real legend → keep as-is (single line)
    if n <= 1:
        return (old_style, old_axis, f"有效图例={n}")

    # Score each candidate type
    scores = {}
    reasons = {}

    # ── 双Y轴复合 ──
    dy = 0
    dy_r = []
    if '双Y轴' in old_axis:
        dy += 10; dy_r.append("axis双Y轴")
    if '百分比轴' in old_axis:
        dy += 2; dy_r.append("百分比轴")
    for l in rl:
        if '右轴' in l or '右Y' in l:
            dy += 10; dy_r.append(f"图例右轴:{l[:20]}")
        if '左轴' in l or '左Y' in l:
            dy += 5; dy_r.append(f"图例左轴:{l[:20]}")
    # Title suggests dual axis
    if re.search(r'双轴|双Y|复合', title):
        dy += 5; dy_r.append("标题含双轴/复合")
    # Risk/Reversal pattern (option pricing → dual scale)
    if any(l in ('Risk', 'Reversal') for l in rl) and n >= 2:
        dy += 3; dy_r.append("Risk/Reversal双轴")
    # Explicit axis labels in legends (e.g., "万吨" as separate legend)
    has_unit_legend = any(is_noise(x) for x in legends)
    if n >= 2 and has_unit_legend:
        dy += 2; dy_r.append("含单位类图例")
    # Percentage + volume coexistence
    has_pct = any(re.search(r'%|同比|环比|占比|渗透率', l) for l in rl)
    has_vol = any(re.search(r'[数]\s*(万吨|亿元|元/吨|销量|产量|出口|进口)', l) for l in rl)
    if has_pct and has_vol:
        dy += 2; dy_r.append("百分比+体积混合")
    scores['双Y轴复合'] = dy
    reasons['双Y轴复合'] = '; '.join(dy_r)

    # ── 堆叠柱状 ──
    sb = 0
    sb_r = []
    # Consumption breakdown
    if re.search(r'终端消费|下游消费', title):
        sb += 6; sb_r.append("标题含终端消费")
    consumption_cats = ['总消费', '交通运输', '房屋建筑', '家电', '电力', '净出口']
    matched_cats = [c for c in consumption_cats if c in rl]
    if len(matched_cats) >= 2:
        sb += len(matched_cats) * 2; sb_r.append(f"消费分类{matched_cats}")
    # Export by destination
    if re.search(r'出口', title) and n >= 2:
        dest_patterns = ['中东', 'EU', '北美', '东南亚', '欧盟']
        found_dest = [d for d in dest_patterns if d in ' '.join(rl)]
        if found_dest:
            sb += len(found_dest) * 2; sb_r.append(f"出口目的地{found_dest}")
    # LME warehouse origin
    if 'LME仓单' in title and '原产地' in ' '.join(rl):
        sb += 8; sb_r.append("LME仓单原产地")
    # Production/inventory/export by type breakdown
    if re.search(r'动力电池.*产量|动力电池.*装车|动力电池.*装机|动力电池.*出口', title) and n >= 3:
        sb += 5; sb_r.append("动力电池分类")
    vehicle_types = ['重型货车', '中型货车', '轻型货车', '半挂牵引车', '微型货车']
    found_vehicles = [v for v in vehicle_types if v in ' '.join(rl)]
    if found_vehicles:
        sb += len(found_vehicles); sb_r.append(f"车辆类型{found_vehicles}")
    # Import by country
    if re.search(r'进口', title) and n >= 2:
        countries = ['几内亚', '澳大利亚', '塞拉利昂', '津巴布韦', '中国']
        found_c = [c for c in countries if c in ' '.join(rl)]
        if found_c:
            sb += len(found_c) * 2; sb_r.append(f"进口国{found_c}")
    # Inventory by location
    if '库存' in title and n >= 2:
        locations = ['社库', '厂库', '交割库', '现货库', '四川', '江苏', '天津', '昆明', '成都', '矿山']
        found_l = [l for l in locations if l in ' '.join(rl)]
        if found_l:
            sb += len(found_l) * 2; sb_r.append(f"库存位置{found_l}")
    # Inventory total + breakdown (合计 + sub-items)
    if '合计' in title and '库存' in title and n >= 2:
        sb += 3; sb_r.append("库存合计+分项")
    # 锂矿样本库存 by source
    if '锂矿' in title and '库存' in title and n >= 2:
        sb += 4; sb_r.append("锂矿库存分项")
    # Multi-warehouse stacked
    if '仓单' in title and '原产地' in ' '.join(rl):
        sb += 4; sb_r.append("仓单分类")
    # 社库+厂库 pattern (even if in title, not legends)
    if '社库' in title and '厂库' in title:
        sb += 5; sb_r.append("标题含社库+厂库")
    # 社库+厂库 in legends
    if '社库' in ' '.join(rl) and '厂库' in ' '.join(rl):
        sb += 5; sb_r.append("图例含社库+厂库")
    # Vehicle type production breakdown (商用车分类)
    if '商用车' in ' '.join(rl) and n >= 3:
        sb += 4; sb_r.append("商用车分类")
    # 装车电量:纯电动 with vehicle types
    if '装车电量' in title and n >= 2:
        sb += 3; sb_r.append("装车电量分类")
    scores['堆叠柱状'] = sb
    reasons['堆叠柱状'] = '; '.join(sb_r)

    # ── 复合混合(折线+柱状) ──
    cb = 0
    cb_r = []
    # Export ratio + volume
    if re.search(r'出口占比', title) and n >= 2:
        cb += 6; cb_r.append("出口占比复合")
    # Import ratio
    if re.search(r'进口.*占比', title):
        cb += 4; cb_r.append("进口占比复合")
    # Volume with trend percentage
    if re.search(r'铝水比例|铝棒月产量', title) and n >= 2:
        cb += 4; cb_r.append("产量比例复合")
    # 利润与出口量 (explicit dual purpose)
    if re.search(r'出口利润.*出口量|利润.*出口', title):
        cb += 5; cb_r.append("利润+出口量复合")
    # Has both volume and ratio patterns in legends
    if n >= 2:
        pct_legends = [l for l in rl if re.search(r'%|占比|同比|环比|渗透率', l)]
        vol_legends = [l for l in rl if re.search(r'[数]\s*(万吨|亿元|元/吨|销量|产量)', l)]
        if pct_legends and vol_legends:
            cb += 3; cb_r.append("图例含百分比+体积")
    # 开工率 with percentage axis (production + rate overlay)
    if re.search(r'开工率', title) and '百分比轴' in old_axis:
        cb += 3; cb_r.append("开工率+百分比轴")
    # 周度产量 with percentage axis (production volume + utilization rate)
    if re.search(r'周度产量|月度产量', title) and '百分比轴' in old_axis:
        cb += 3; cb_r.append("产量+百分比轴")
    # 开工率 with multiple legends (different sources)
    if re.search(r'开工率', title) and n >= 2 and not re.search(r'碳酸锂', title):
        cb += 2; cb_r.append("开工率复合")
    scores['复合混合(折线+柱状)'] = cb
    reasons['复合混合(折线+柱状)'] = '; '.join(cb_r)

    # ── 堆叠面积 ──
    sa = 0
    sa_r = []
    # LME stock with Russia layer (clear stacking: Russia2021 + other stock)
    if 'LME' in title and '库存' in title and n >= 2:
        if any('Russia' in l for l in rl):
            sa += 8; sa_r.append("LME库存+Russia分层")
    # Warehouse warrant origin stacking (clear stacked area of origins)
    if '仓单' in title and '原产地' in ' '.join(rl):
        sa += 6; sa_r.append("仓单原产地堆叠")
    # Multi-country inventory layering
    if '库存' in title and n >= 3 and 'Russia' in ' '.join(rl):
        sa += 4; sa_r.append("多国库存分层")
    scores['堆叠面积'] = sa
    reasons['堆叠面积'] = '; '.join(sa_r)

    # ── Decide best match ──
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        # No enhancement signal → keep original
        return (old_style, old_axis, f"有效图例={n},无增强信号")

    # Threshold: need at least 3 points to override
    if scores[best] < 3:
        return (old_style, old_axis, f"最高{scores[best]}<3,保持原值")

    # Check: if current is already the best match, no change needed
    if best == old_style:
        return (old_style, old_axis, f"已匹配({best}={scores[best]})")

    new_style = best

    # Update axis_info
    new_axis = old_axis
    if best == '双Y轴复合':
        if '双Y轴' not in old_axis:
            if '百分比轴' in old_axis:
                new_axis = '双Y轴(百分比)'
            else:
                new_axis = '双Y轴'
    elif best == '堆叠柱状' and '百分比轴' in old_axis:
        # Keep axis info, it's already meaningful
        pass

    # Build reason
    reason_parts = [f"有效图例={n}"]
    for k, v in sorted(scores.items(), key=lambda x: -x[1]):
        if v > 0:
            r = reasons.get(k, '')
            reason_parts.append(f"{k}({v}pts){'['+r+']' if r else ''}")
    reason = ' | '.join(reason_parts)

    return (new_style, new_axis, reason)


def main():
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    charts = data['charts']
    print(f"Loaded {len(charts)} charts from {INPUT_JSON}")

    # ── Pass 1: classify all charts ──
    reclassified = []
    stats = {'reclassified': 0}

    old_dist = Counter(c['plot_style'] for c in charts)
    old_axis_dist = Counter(c['axis_info'] for c in charts)
    new_dist = Counter()
    new_axis_dist = Counter()

    for c in charts:
        old_style = c['plot_style']
        old_axis = c['axis_info']
        new_style, new_axis, reason = classify(c)

        # Count new distributions
        new_dist[new_style] += 1
        new_axis_dist[new_axis] += 1

        if new_style != old_style or new_axis != old_axis:
            reclassified.append({
                'chart_local_id': c['chart_local_id'],
                'source_file': c['source_file'],
                'page_num': c['page_num'],
                'chart_title': c['chart_title'],
                'old_style': old_style,
                'new_style': new_style,
                'old_axis': old_axis,
                'new_axis': new_axis,
                'n_real_legends': len(real_legends(c['legend_list'])),
                'reason': reason,
            })
            c['plot_style'] = new_style
            c['axis_info'] = new_axis
            stats['reclassified'] += 1

    # Update note fields
    for c in charts:
        note_parts = [
            f"绘图类型:{c['plot_style']}",
            f"轴信息:{c['axis_info']}",
            f"图例数:{len(c['legend_list'])}",
        ]
        if c['plot_style'] in ('双Y轴复合', '堆叠柱状', '复合混合(折线+柱状)', '堆叠面积'):
            note_parts.append(f"★增强识别({len(real_legends(c['legend_list']))}有效图例)")
        if c['plot_style'] == '多折线' and len(real_legends(c['legend_list'])) >= 3:
            note_parts.append(f"复合图({len(c['legend_list'])}图例,{len(real_legends(c['legend_list']))}有效)")
        c['note'] = ' | '.join(note_parts)

    # ── Write JSON ──
    data['work_order'] = 'DSH-B_PLOT_STYLE_ENHANCE_OPTIMIZE_TASK'
    data['description'] = 'Enhanced plot_style recognition with 4 new enums: 复合混合(折线+柱状)|双Y轴复合|堆叠柱状|堆叠面积'
    data['total_charts'] = len(charts)
    data['plot_style_enums'] = [
        '单折线', '多折线', '季节图', '表格截面',
        '复合混合(折线+柱状)', '双Y轴复合', '堆叠柱状', '堆叠面积'
    ]
    data['enhancement_info'] = {
        'reclassified_count': len(reclassified),
        'new_enums': ['复合混合(折线+柱状)', '双Y轴复合', '堆叠柱状', '堆叠面积'],
        'old_style_distribution': dict(old_dist),
        'new_style_distribution': dict(new_dist),
        'old_axis_distribution': dict(old_axis_dist),
        'new_axis_distribution': dict(new_axis_dist),
    }

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON: {OUTPUT_JSON}")

    # ── Write CSV ──
    fieldnames = [
        'source_file', 'page_num', 'chart_local_id', 'chart_title',
        'plot_style', 'axis_info', 'legend_list', 'extracted_indicator_list',
        'missing_in_legend', 'note'
    ]
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        w.writeheader()
        for c in charts:
            row = {k: c.get(k, '') for k in fieldnames}
            for k in ['legend_list', 'extracted_indicator_list', 'missing_in_legend']:
                if isinstance(row[k], list):
                    row[k] = '|'.join(row[k])
            w.writerow(row)
    print(f"✅ CSV: {OUTPUT_CSV}")

    # ── Summary ──
    print(f"\n{'='*72}")
    print("ENHANCEMENT SUMMARY")
    print(f"{'='*72}")
    print(f"\nOld style distribution:")
    for s, cnt in old_dist.most_common():
        print(f"  {s}: {cnt}")
    print(f"\nNew style distribution:")
    for s, cnt in new_dist.most_common():
        print(f"  {s}: {cnt}")
    print(f"\nReclassified: {stats['reclassified']} charts")

    # ── New enum charts ──
    new_enum_charts = [r for r in reclassified
                       if r['new_style'] in ('复合混合(折线+柱状)', '双Y轴复合', '堆叠柱状', '堆叠面积')]
    print(f"\n{'='*72}")
    print(f"NEW ENUM CLASSIFICATIONS ({len(new_enum_charts)})")
    print(f"{'='*72}")
    for r in new_enum_charts:
        sf = r['source_file'][:8]
        print(f"  [{sf}] {r['chart_local_id']} | {r['chart_title'][:40]}")
        print(f"    {r['old_style']} → {r['new_style']}")
        if r['old_axis'] != r['new_axis']:
            print(f"    axis: {r['old_axis']} → {r['new_axis']}")
        print(f"    real_legends={r['n_real_legends']}")
        print(f"    reason: {r['reason']}")

    # ── Style changes (not new enums) ──
    style_change_charts = [r for r in reclassified
                          if r['new_style'] not in ('复合混合(折线+柱状)', '双Y轴复合', '堆叠柱状', '堆叠面积')
                          and r['old_style'] != r['new_style']]
    if style_change_charts:
        print(f"\n{'='*72}")
        print(f"STYLE UPDATES ({len(style_change_charts)})")
        print(f"{'='*72}")
        for r in style_change_charts:
            sf = r['source_file'][:8]
            print(f"  [{sf}] {r['chart_local_id']} | {r['chart_title'][:40]}")
            print(f"    {r['old_style']} → {r['new_style']}")
            if r['old_axis'] != r['new_axis']:
                print(f"    axis: {r['old_axis']} → {r['new_axis']}")
            print(f"    reason: {r['reason']}")

    # ── Axis-only changes ──
    axis_only = [r for r in reclassified if r['old_style'] == r['new_style']]
    if axis_only:
        print(f"\n{'='*72}")
        print(f"AXIS UPDATES ({len(axis_only)})")
        print(f"{'='*72}")
        for r in axis_only:
            print(f"  [{r['source_file'][:8]}] {r['chart_local_id']} | {r['chart_title'][:40]}")
            print(f"    axis: {r['old_axis']} → {r['new_axis']}")

    # ── Full reclass log ──
    with open('plot_style_reclass_log.json', 'w', encoding='utf-8') as f:
        json.dump(reclassified, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Reclass log: plot_style_reclass_log.json ({len(reclassified)} entries)")
    print(f"\nDone!")


if __name__ == '__main__':
    main()
