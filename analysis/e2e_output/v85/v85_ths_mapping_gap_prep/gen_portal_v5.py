#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 enhanced_review_portal_v4_mapping.md 门户 v5"""
import json, csv
from pathlib import Path
from datetime import datetime

BASE = Path('/home/ubuntu/framework-tree/analysis/e2e_output/v85')
MAPPING_DIR = BASE / 'v85_ths_mapping_gap_prep'
OUT = MAPPING_DIR / 'enhanced_review_portal_v4_mapping.md'

rows = list(csv.DictReader(open(MAPPING_DIR / 'ths_candidate_mapping.csv', encoding='utf-8-sig')))
summary = json.load(open(MAPPING_DIR / 'ths_mapping_summary.json', encoding='utf-8'))
total = summary['total_series']
var_dist = summary['variety_distribution']

high_conf = [r for r in rows if r['match_category'] == '高置信']
fuzzy = [r for r in rows if r['match_category'] == '模糊待人工确认']
none = [r for r in rows if r['match_category'] == '无候选/低置信']


def bar(n, mx):
    l = int(n / mx * 30) if mx else 0
    return '█' * l


mx_var = max(var_dist.values()) if var_dist else 1

L = []
L.append('# V85 图表模板评审门户 · 增强版 v5 (含 THS 指标候选映射预览)')
L.append('')
L.append('> 工单: `HERMES_V85_THS_INDICATOR_MAPPING_PREP_AND_GATE_GAP_PLAN`')
L.append('> 生成时间: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
L.append('> 分支: `feature/v85-chart-template` @ `357e98b`')
L.append('> 状态: 测试环境评审材料，未上线')
L.append('> v5 新增: THS 指标候选映射预览面板 + 批量导出待匹配清单 + 映射统计')
L.append('')
L.append('> 上一版: `enhanced_review_portal.md` v4 (v85_portal_enhance_render_sim/)')
L.append('')
L.append('---')
L.append('')
L.append('## A. THS 指标候选映射预览面板')
L.append('')
L.append('### A.0 映射统计总览')
L.append('')
L.append('| 分类 | 数量 | 占比 | 处理动作 |')
L.append('|------|------|------|---------|')
L.append(f'| 高置信 (≥70分) | {len(high_conf)} | {len(high_conf)*100//total}% | 可批量回写, 人工抽样复核 |')
L.append(f'| 模糊待人工确认 (40-69分) | {len(fuzzy)} | {len(fuzzy)*100//total}% | 需人工逐条确认 |')
L.append(f'| 完全无候选 (<40分) | {len(none)} | {len(none)*100//total}% | 需额外发散/外部源补充 |')
L.append(f'| **合计 series** | **{total}** | **100%** | |')
L.append('')
L.append('> 说明: 候选为文本相似度召回(品种过滤+同义词归一), 非最终确定。')
L.append('> 高置信 = 库内名称强匹配; 模糊 = 名称部分匹配; 无候选 = 库内无近似。')
L.append('')
L.append('### A.1 品种分布')
L.append('')
L.append('| 品种 | series数 | 分布 |')
L.append('|------|---------|------|')
for v, n in sorted(var_dist.items(), key=lambda x: -x[1]):
    L.append(f'| {v} | {n} | {bar(n, mx_var)} |')
L.append('')
L.append('### A.2 候选映射示例 (高置信 top15)')
L.append('')
L.append('| 模板 | 品种 | 原始THS名 | 最佳候选 | 得分 | zhiji_id |')
L.append('|------|------|-----------|---------|------|----------|')
for r in high_conf[:15]:
    L.append(f"| {r['ths_chart_id']} | {r['variety']} | {r['original_ths_name'][:20]} | {r['best_match_name'][:22]} | {r['best_match_score']} | {r['best_match_zhiji_id']} |")
L.append('')
L.append('### A.3 候选映射示例（模糊待确认 top10）')
L.append('')
L.append('| 模板 | 品种 | 原始THS名 | 候选列表 | 得分 |')
L.append('|------|------|-----------|---------|------|')
for r in fuzzy[:10]:
    L.append(f"| {r['ths_chart_id']} | {r['variety']} | {r['original_ths_name'][:20]} | {r['candidate_names'][:40]} | {r['candidate_scores']} |")
L.append('')
L.append('### A.4 无候选指标清单（需外部补充, 前10）')
L.append('')
L.append('| 模板 | 品种 | 原始THS名 | 说明 |')
L.append('|------|------|-----------|------|')
for r in none[:10]:
    L.append(f"| {r['ths_chart_id']} | {r['variety']} | {r['original_ths_name'][:25]} | 无库内近似指标 |")
L.append('')
L.append('---')
L.append('')
L.append('## B. 批量导出待人工匹配清单')
L.append('')
L.append('> 导出入口: 运行 `mapping_fill_helper.py --export unfilled` 可生成待匹配清单 CSV。')
L.append('> 清单含: 无候选 + 模糊待确认 全部 series, 供人工填写 zhiji_id 后回写。')
L.append('')
L.append('| 导出类型 | 文件 | 用途 |')
L.append('|---------|------|------|')
L.append('| 高置信清单 | `ths_candidate_highconf.csv` | 批量回填候选 |')
L.append('| 待人工匹配清单 | `ths_match_unfilled.csv` | 人工填写zhiji_id |')
L.append('')
L.append('---')
L.append('')
L.append('## C. 人工映射操作区')
L.append('')
L.append('| 操作 | 方式 | 说明 |')
L.append('|------|------|------|')
L.append('| 查看候选 | 打开 `ths_candidate_mapping.csv` | 全量候选(含候选id/得分/zhiji) |')
L.append('| 填写匹配 | 在CSV填 primer字段 | 填写人工确认的 zhiji_id |')
L.append('| 回写 | 运行回写脚本 | 回写进 manifest |')
L.append('| 校验 | 脚本自带 schema 校验 | 非法 id 拒写 |')
L.append('')
L.append('---')
L.append('')
L.append('## D. 原有 v4 功能概述 (完整版见 enhanced_review_portal.md)')
L.append('')
L.append('- **维度筛选**: 按品种/风险/来源/模板状态筛选')
L.append('- **详情弹窗**: 模板级 series 风险明细')
L.append('- **全局大盘**: 渲染队列占比 + 品种分布')
L.append('- **PDF/THS 对比**: 双源模板对照')
L.append('- **人工评审区**: 评审结论记录 + 回写')
L.append('')
L.append('> 本 v5 版聚焦 THS 候选映射预览, PDF 侧多维筛选/评审沿用 v4。')
L.append('> 完整 v4 内容见: `v85_portal_enhance_render_sim/enhanced_review_portal.md`')
L.append('')

OUT.write_text('\n'.join(L), encoding='utf-8')
print(f'OK portal: {OUT} ({OUT.stat().st_size} bytes)')
print(f'   高置信={len(high_conf)} 模糊={len(fuzzy)} 无候选={len(none)}')