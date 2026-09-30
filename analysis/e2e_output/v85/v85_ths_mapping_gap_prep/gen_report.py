#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 ths_mapping_prep_report.md 汇总报告"""
import json, csv
from pathlib import Path
from datetime import datetime
from collections import Counter

BASE = Path('/home/ubuntu/framework-tree/analysis/e2e_output/v85')
MAPPING_DIR = BASE / 'v85_ths_mapping_gap_prep'

rows = list(csv.DictReader(open(MAPPING_DIR / 'ths_candidate_mapping.csv', encoding='utf-8-sig')))
summary = json.load(open(MAPPING_DIR / 'ths_mapping_summary.json', encoding='utf-8'))
total = summary['total_series']
ind_count = summary['indicator_library_count']
var_dist = summary['variety_distribution']

cats = Counter(r['match_category'] for r in rows)
var_cat = Counter((r['variety'], r['match_category']) for r in rows)
var_total = Counter(r['variety'] for r in rows)

hc = cats.get('高置信', 0)
fm = cats.get('模糊待人工确认', 0)
nc = cats.get('无候选/低置信', 0)
with_candidates = hc + fm


def pct(n):
    return n * 100 // total if total else 0


L = []
L.append('# THS 指标映射预处理汇总报告')
L.append('')
L.append('> 工单: `HERMES_V85_THS_INDICATOR_MAPPING_PREP_AND_GATE_GAP_PLAN`')
L.append('> 生成时间: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
L.append('> 分支: `feature/v85-chart-template` @ `357e98b`')
L.append(f'> 输入: ths_adapted_all.json (155模板) + indicators_v1.json ({ind_count}指标)')
L.append('')
L.append('## 一、总览')
L.append('')
L.append(f'共处理 **{total}** 条 THS series（来自 155 个 THS 模板）。')
L.append(f'指标库共 **{ind_count}** 个指标参与相似度候选召回。')
L.append('')
L.append('| 分类 | 数量 | 占比 | 说明 |')
L.append('|------|------|------|------|')
L.append(f"| 高置信 (≥70分) | {hc} | {pct(hc)}% | 库内名称强匹配，可批量回写(需人工抽样复核) |")
L.append(f"| 模糊待确认 (40-69分) | {fm} | {pct(fm)}% | 名称部分匹配，需人工逐条确认 |")
L.append(f"| 无候选 (<40分) | {nc} | {pct(nc)}% | 库内无近似指标，需外部发散 |")
L.append(f"| **有候选合计** | **{with_candidates}** | **{pct(with_candidates)}%** | 可通过候选召回辅助人工匹配 |")
L.append('')
L.append('> 候选召回为静态文本相似度(品种过滤+同义词归一)，高置信不等于语义等价，需人工最终确认。')
L.append('')
L.append('---')
L.append('')
L.append('## 二、品种×分类分布')
L.append('')
L.append('| 品种 | 高置信 | 模糊 | 无候选 | 合计 |')
L.append('|------|-------|------|--------|------|')
for v, tot in sorted(var_total.items(), key=lambda x: -x[1]):
    h = var_cat.get((v, '高置信'), 0)
    f = var_cat.get((v, '模糊待人工确认'), 0)
    n = var_cat.get((v, '无候选/低置信'), 0)
    L.append(f'| {v} | {h} | {f} | {n} | {tot} |')
L.append('')
L.append('---')
L.append('')
L.append('## 三、匹配质量评估')
L.append('')
L.append('### 3.1 高置信样例 (前8，供人工抽样复核)')
L.append('')
L.append('| 模板 | 品种 | 原始THS名 | 最佳候选 | 得分 |')
L.append('|------|------|-----------|---------|------|')
high = [r for r in rows if r['match_category'] == '高置信']
for r in high[:8]:
    L.append(f"| {r['ths_chart_id']} | {r['variety']} | {r['original_ths_name'][:20]} | {r['best_match_name'][:24]} | {r['best_match_score']} |")
L.append('')
L.append('### 3.2 模糊样例 (为人工确认提供参考)')
L.append('')
L.append('| 模板 | 品种 | 原始THS名 | 候选列表 |')
L.append('|------|------|-----------|---------|')
fuz = [r for r in rows if r['match_category'] == '模糊待人工确认']
for r in fuz[:8]:
    L.append(f"| {r['ths_chart_id']} | {r['variety']} | {r['original_ths_name'][:20]} | {r['candidate_names'][:40]} |")
L.append('')
L.append('### 3.3 典型误匹配类型')
L.append('''- **品种维度**: THS名含"全球/海外/中国"等全局词时, 品种检测降级, 会召回他品种指标(已用品种过滤抑制)
- **利润率 vs 产量**: "碳酸锂利润" 可能附近有 "碳酸锂产量"(词汇高度重叠)
- **区域农批**: "广东铝棒价" vs "河南铝棒价"(同称不同地, 需人工核实区域)
- **单位换算**: "万吨LCE" vs "吨" 未纳入换算, 名称相似但量纲不同''')
L.append('')
L.append('## 四、产物清单')
L.append('')
L.append('| 文件 | 大小 | 说明 |')
L.append('|------|------|------|')
L.append('| ths_candidate_mapping.csv | 871KB | 全量候选召回(2360条, top5候选+得分+zhiji) |')
L.append('| ths_match_highconf.csv | - | 高置信候选(864条, 供批量回写) |')
L.append('| ths_match_unfilled.csv | - | 待人工匹配清单(1495条 = 1188模糊+307无候选) |')
L.append('| ths_mapping_summary.json | - | 统计摘要 |')
L.append('| mapping_fill_helper.py | - | 人工回写脚本(verify+apply) |')
L.append('')
L.append('## 五、后续动作')
L.append('')
L.append('1. **高置信批量回写**: 864条候选经人工抽样复核后, 用 mapping_fill_helper --apply 批量回写')
L.append('2. **模糊人工确认**: 1188条需人工基于候选列表确认 final zhiji_id')
L.append('3. **无候选外部发散**: 307条(13%)需额外查询知识库或外部source补充')
L.append('4. **完成标准**: THS zhiji_id 匹配率 ≥80% 解除 Gate 1.3/5-🚫1 硬性条件')
L.append('')

OUT = MAPPING_DIR / 'ths_mapping_prep_report.md'
OUT.write_text('\n'.join(L), encoding='utf-8')
print(f'OK report: {OUT} ({OUT.stat().st_size} bytes)')
print(f'   高置信={hc}({pct(hc)}%) 模糊={fm}({pct(fm)}%) 无候选={nc}({pct(nc)}%) 有候选={with_candidates}({pct(with_candidates)}%)')