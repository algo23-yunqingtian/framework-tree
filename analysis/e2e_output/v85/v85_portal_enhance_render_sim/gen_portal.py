#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_enhanced_portal.py — 生成评审门户v4 enhanced_review_portal.md
"""
import json, os, csv
from pathlib import Path
from datetime import datetime

BASE = Path("/home/ubuntu/framework-tree/analysis/e2e_output/v85")
INT_BASE = BASE / "v85_final_integrate"
SIM_BASE = BASE / "v85_portal_enhance_render_sim"

with open(INT_BASE / "chart_risk_bound_all.json", encoding="utf-8") as f:
    bound = json.load(f)
with open(INT_BASE / "ths_render_task_manifest.json", encoding="utf-8") as f:
    manifest = json.load(f)
with open(SIM_BASE / "render_simulation_stats.json", encoding="utf-8") as f:
    sim_stats = json.load(f)

stats = bound["statistics"]
var_dist = bound["variety_distribution"]

pdf_var = {}
ths_var = {}
for t in bound["templates"]:
    v = t.get("variety", "UNKNOWN")
    src = t.get("source", "")
    if src == "PDF":
        pdf_var[v] = pdf_var.get(v, 0) + 1
    else:
        ths_var[v] = ths_var.get(v, 0) + 1

all_varieties = sorted(set(list(pdf_var.keys()) + list(ths_var.keys())))

pdf_ct = {}
ths_ct = {}
for t in bound["templates"]:
    ct = t.get("chart_type", "")
    src = t.get("source", "")
    if ct:
        if src == "PDF":
            pdf_ct[ct] = pdf_ct.get(ct, 0) + 1
        else:
            ths_ct[ct] = ths_ct.get(ct, 0) + 1

all_ct = sorted(set(list(pdf_ct.keys()) + list(ths_ct.keys())))

risk_type_dist = {"P0": 0, "P1": 0, "CLEAN": 0}
for t in bound["templates"]:
    rl = t.get("template_risk_level", "CLEAN")
    if rl in risk_type_dist:
        risk_type_dist[rl] += 1

render_groups = manifest.get("summary", {})
total_templates = stats["total_templates"]

pdf_only_var = sorted(set(pdf_var.keys()) - set(ths_var.keys()))
ths_only_var = sorted(set(ths_var.keys()) - set(pdf_var.keys()))
both_var = sorted(set(pdf_var.keys()) & set(ths_var.keys()))

# 品种柱状图
max_var = max(var_dist.values(), key=lambda d: d["total"])["total"]
variety_bars = ""
for v in sorted(var_dist.keys()):
    d = var_dist[v]
    bar_len = int(d["total"] * 30 / max_var)
    variety_bars += "%-4s | %s %d (P0:%d P1:%d CLEAN:%d)\n" % (v, "\u2588" * bar_len, d["total"], d.get("P0",0), d.get("P1",0), d.get("CLEAN",0))

# 风险分布柱
risk_bars = ""
for lvl in ["P0", "P1", "CLEAN"]:
    cnt = risk_type_dist[lvl]
    bar_len = int(cnt * 30 / total_templates) if total_templates > 0 else 0
    risk_bars += "%-6s | %s %d\n" % (lvl, "\u2588" * bar_len, cnt)

# 饼图
can_pct = render_groups['can_render'] * 100 // total_templates
rev_pct = render_groups['review_first'] * 100 // total_templates
blk_pct = render_groups['blocked'] * 100 // total_templates

# 品种筛选表
variety_filter_rows = ""
for v in all_varieties:
    d = var_dist.get(v, {"total": 0, "P0": 0, "P1": 0, "CLEAN": 0})
    variety_filter_rows += "| %s | %d | %d | %d | %d | %d | %d |\n" % (v, d['total'], pdf_var.get(v,0), ths_var.get(v,0), d.get('P0',0), d.get('P1',0), d.get('CLEAN',0))

# 图表类型筛选
ct_filter_rows = ""
for ct in all_ct:
    p = pdf_ct.get(ct, 0)
    t = ths_ct.get(ct, 0)
    ct_filter_rows += "| %s | %d | %d | %d |\n" % (ct, p, t, p+t)

# 差异对比
ct_diff_rows = ""
for ct in all_ct:
    p = pdf_ct.get(ct, 0)
    t = ths_ct.get(ct, 0)
    diff = p - t
    diff_str = "PDF 多 %d" % diff if diff > 0 else ("THS 多 %d" % (-diff) if diff < 0 else "一致")
    ct_diff_rows += "| %s | %d | %d | %s |\n" % (ct, p, t, diff_str)

pdf_render = sum(1 for t in manifest['render_groups']['can_render']['tasks'] if t['source']=='PDF')
ths_render = sum(1 for t in manifest['render_groups']['can_render']['tasks'] if t['source']=='THS')
pdf_blocked = sum(1 for t in manifest['render_groups']['blocked']['tasks'] if t['source']=='PDF')
ths_blocked = sum(1 for t in manifest['render_groups']['blocked']['tasks'] if t['source']=='THS')
pdf_avg_series = sum(t.get('series_count',0) for t in bound['templates'] if t['source']=='PDF') // max(stats['pdf_total'],1)
ths_avg_series = sum(t.get('series_count',0) for t in bound['templates'] if t['source']=='THS') // max(stats['ths_total'],1)

# 阻塞模板前20
blocked_rows = ""
for t in manifest["render_groups"]["blocked"]["tasks"][:20]:
    rt = t.get('risk_tags',{})
    blocked_rows += "| `%s` | %s | %s | %s | %d | %d | 查看详情后决定 |\n" % (t['template_id'], t['source'], t.get('variety',''), t['risk_level'], rt.get('p0_count',0), rt.get('p1_count',0))

review_rows = ""
for t in manifest["render_groups"]["review_first"]["tasks"][:20]:
    rt = t.get('risk_tags',{})
    review_rows += "| `%s` | %s | %s | %s | %d | %d | 复核后决定 |\n" % (t['template_id'], t['source'], t.get('variety',''), t['risk_level'], rt.get('p0_count',0), rt.get('p1_count',0))

md = """# V85 图表模板评审门户 · 增强版 v4

> 工单: `HERMES_V85_REVIEW_PORTAL_ENHANCE_AND_RENDER_SIMULATION`  
> 生成时间: %s  
> 分支: `feature/v85-chart-template` @ `5012efa`  
> 状态: 测试环境评审材料，未上线  
> v4 增强: 多维筛选 + 详情弹窗 + 全局可视化大盘 + PDF/THS 差异对比 + 人工评审操作区

> 上一版: `final_integrated_review_portal.md` v3

---

## 0. 全局可视化大盘

### 0.1 渲染队列占比

```
%s 可直接渲染 (%d, %d%%)
%s 人工复核 (%d, %d%%)
%s 阻塞 (%d, %d%%)
```

| 分组 | 数量 | 占比 |
|------|------|------|
| 可直接渲染 | %d | %d%% |
| 人工复核后渲染 | %d | %d%% |
| 阻塞不渲染 | %d | %d%% |
| **合计** | **%d** | **100%%** |

### 0.2 品种分布柱状图

```
%s
```

### 0.3 风险类型分布

```
%s
```

| 风险等级 | 数量 | 占比 | 处置 |
|---------|------|------|------|
| P0 | %d | %d%% | 拦截渲染 |
| P1 | %d | %d%% | 人工复核 |
| CLEAN | %d | %d%% | 可直接渲染 |

### 0.4 仿真跑批结果摘要

| 指标 | 值 |
|------|-----|
| 仿真任务总数 | %d |
| 渲染成功 | %d |
| P0 阻塞 | %d |
| THS 待匹配 | %d |
| 平均耗时/任务 | %sms |

---

## 1. 多维度批量筛选功能

### 1.1 筛选维度

| 维度 | 可选值 | 说明 |
|------|--------|------|
| 来源 | PDF / THS | 模板来源 |
| 风险等级 | P0 / P1 / CLEAN | 模板级风险等级 |
| 品种 | %s | 品种代码 |
| 图表类型 | %s | 图表渲染类型 |

### 1.2 批量导出

筛选后可批量导出模板明细为 CSV。导出命令见 `portal_operation_manual.md`。

### 1.3 按来源筛选

| 来源 | 模板数 | P0 | P1 | CLEAN |
|------|--------|----|----|-------|
| PDF | %d | %d | %d | %d |
| THS | %d | %d | %d | %d |

### 1.4 按品种筛选

| 品种 | 总数 | PDF | THS | P0 | P1 | CLEAN |
|------|------|-----|-----|----|----|-------|
%s

### 1.5 按图表类型筛选

| 图表类型 | PDF | THS | 合计 |
|---------|-----|-----|------|
%s

---

## 2. 模板详情弹窗

### 2.1 弹窗内容结构

| 区域 | 内容 | 数据来源 |
|------|------|---------|
| 基本信息 | 模板ID、来源标签、品种、图表类型、节点代码 | chart_risk_bound_all.json |
| 图表样式 | 复合绘图样式、Y轴配置、图例位置 | 原始模板 series[].style |
| 指标列表 | 每条 series 的 name、zhiji_id、verify_status、unit、axis | 原始模板 series[] |
| 风险说明 | 每条指标对应的风险等级、冲突组ID、黑名单规则编号、冲突根因 | chart_risk_bound_all.json series_risks[] |
| 渲染状态 | 渲染分组、失败处理策略 | ths_render_task_manifest.json |

### 2.2 风险说明字段

| 字段 | 说明 | 示例 |
|------|------|------|
| risk_level | 风险等级 | P0 / P1 / CLEAN / INFO / BLOCKED |
| risk_type | 风险类型 | semantic_conflict / invalid_zhiji_id |
| group_id | 黑名单规则编号 | G01_output_vs_consumption |
| group_label | 冲突组描述 | 产量 vs 消费量/销量 |
| hit_words_a | 系列名命中关键词 | ['产量'] |
| hit_words_b | zhiji名命中关键词 | ['销量'] |
| reason | 冲突根因 | 语义互斥: A命中['产量'] B命中['销量'] |
| conflict_root_cause | 冲突根因预留字段 | （待 DSHB 交付后填充） |

### 2.3 详情弹窗示例

<details>
<summary>点击展开 TPL-LC-091 详情（P0 产量vs销量冲突）</summary>

| 字段 | 值 |
|------|-----|
| 模板ID | TPL-LC-091 |
| 来源 | PDF |
| 品种 | LC (碳酸锂) |
| 模板风险等级 | P0 |
| 渲染分组 | 阻塞 |
| 失败策略 | 修复风险后重新评估 |

指标风险明细:

| # | 系列名 | zhiji名 | 风险等级 | 冲突组 | 命中词 | 根因 |
|---|--------|---------|---------|--------|--------|------|
| 0 | 新能源乘用车 产量 | 国产乘用车销量-新能源汽车 | P0 | G01 | 产量/销量 | 供给端vs需求端 |

</details>

---

## 3. PDF vs THS 差异对比面板

### 3.1 品种覆盖对比

| 类别 | 品种 | 说明 |
|------|------|------|
| PDF 独有 | %s | 仅 PDF 模板覆盖 |
| THS 独有 | %s | 仅 THS 模板覆盖 |
| 双源覆盖 | %s | PDF 和 THS 均有 |

### 3.2 图表类型分布差异

| 图表类型 | PDF | THS | 差异 |
|---------|-----|-----|------|
%s

### 3.3 指标体系对比

| 维度 | PDF | THS |
|------|-----|-----|
| 模板总数 | %d | %d |
| zhiji_id 匹配率 | ~98%% | 0%% |
| 可直接渲染 | %d | %d |
| P0 阻塞 | %d | %d |
| 平均 series/模板 | %d | %d |

---

## 4. 人工评审操作区

### 4.1 评审标记规则

| 标记 | 含义 | 后续动作 |
|------|------|---------|
| 通过 | 评审通过 | 移入可渲染队列 |
| 驳回 | 评审不通过 | 移入阻塞队列 |
| 临时白名单放行 | 临时放行 | 限期7天复核 |

### 4.2 评审记录字段

| 字段 | 说明 |
|------|------|
| template_id | 模板ID |
| source | 来源 |
| reviewer | 评审人 |
| review_time | 评审时间 |
| decision | 通过/驳回/临时白名单放行 |
| remark | 备注 |
| previous_risk_level | 原风险等级 |
| new_status | APPROVED/REJECTED/WHITELISTED |

### 4.3 待评审模板清单

<details>
<summary>P0 阻塞模板（%d 个，点击展开前20条）</summary>

| 模板ID | 来源 | 品种 | 风险等级 | P0数 | P1数 | 评审建议 |
|--------|------|------|---------|------|------|---------|
%s
</details>

<details>
<summary>P1 复核模板（%d 个，点击展开前20条）</summary>

| 模板ID | 来源 | 品种 | 风险等级 | P0数 | P1数 | 评审建议 |
|--------|------|------|---------|------|------|---------|
%s
</details>

---

## 5. 语义冲突风险标记

> 风险库: semantic_blacklist_hermes_fixed.json v2.0-fixed (10组 G01-G10)
> 校验器: enhanced_auto_semantic_check.py v3.0
> DSHB动态加载: 预留入口, CSV提交后一键刷新

### 5.1 冲突组速查

| 组ID | 严重度 | 语义对立 |
|------|--------|---------|
| G01 | P0 | 产量 vs 消费量/销量 |
| G02 | P0 | 场内库存 vs 非仓单/场外库存 |
| G03 | P0 | 库存 vs 在途/堆场 |
| G04 | P1 | 拟合/估算 vs 官方指数 |
| G05 | P1 | 折镍价 vs 折合价 |
| G06 | P1 | 社会库存 vs 期货仓单 |
| G07 | P1 | 开工率 vs 产量 |
| G08 | P1 | 价格 vs 成本 |
| G09 | P0 | 出口 vs 进口 |
| G10 | P0 | 国产 vs 进口/海外 |

### 5.2 已知 P0 冲突（8条）

| 模板ID | 系列名 | zhiji名 | 冲突组 |
|--------|--------|---------|--------|
| TPL-AO-020/026 | 氧化铝库存-堆场站台 | 氧化铝在途&站台堆积 | G03 |
| TPL-LC-084/086/099 | 电池销量 | 电池产量 | G01 |
| TPL-LC-091/092 | 新能源乘用车产量 | 乘用车销量-新能源汽车 | G01 |
| TPL-AL-013 | LME场内库存 | LME非仓单库存 | G02 |

### 5.3 已知 P1 冲突（2条）

| 模板ID | 系列名 | zhiji名 | 冲突组 |
|--------|--------|---------|--------|
| TPL-SN-034 | 汽车端消费用锡拟合 | 消费指数 | G04 |
| TPL-NI-004 | 折镍价 | 折合镍铁价格 | G05 |

---

## 6. DSHB 动态加载入口

DSHB CSV 提交后一键加载:

    python3 enhanced_auto_semantic_check.py --load-dshb unified_indicator_risk_db.csv --refresh

CSV 兼容格式（自动识别列名）:
- 必需: indicator_id / template_id / chart_id（任一）
- 可选: series_name, zhiji_name, risk_level, group_id, keywords

---

## 7. 产物索引

| # | 文件 | 说明 |
|---|------|------|
| 1 | enhanced_review_portal.md | 本文件 |
| 2 | portal_operation_manual.md | 操作手册 |
| 3 | render_simulation_report.md | 仿真评估报告 |
| 4 | render_simulation_log.csv | 仿真日志(488行) |
| 5 | enhanced_auto_semantic_check.py | 校验器v3.0 |
| 6 | portal_changelog.md | 变更记录 |
| 7 | render_scan_log.jsonl | 结构化校验日志(10050条) |
| 8 | render_simulation_stats.json | 仿真统计 |

---

## 8. 约束声明

- 分支: feature/v85-chart-template, 禁止合并main, 禁止生产部署
- 全程禁止调用zhiji接口: 仅仿真模拟与静态增强
- 不修改原始绑定文件: chart_risk_bound_all.json等只读
- 不修改配置: indicators_v1.json, tree_config.json只读
- 仅新增文件, 禁止覆盖历史产物
- DSHB CSV: unified_indicator_risk_db.csv 仍未落地本机, 已预留动态加载入口
""" % (
    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "\u2588" * (render_groups['can_render'] * 40 // total_templates), render_groups['can_render'], can_pct,
    "\u2588" * (render_groups['review_first'] * 40 // total_templates), render_groups['review_first'], rev_pct,
    "\u2588" * (render_groups['blocked'] * 40 // total_templates), render_groups['blocked'], blk_pct,
    render_groups['can_render'], can_pct,
    render_groups['review_first'], rev_pct,
    render_groups['blocked'], blk_pct,
    total_templates,
    variety_bars,
    risk_bars,
    risk_type_dist['P0'], risk_type_dist['P0']*100//total_templates,
    risk_type_dist['P1'], risk_type_dist['P1']*100//total_templates,
    risk_type_dist['CLEAN'], risk_type_dist['CLEAN']*100//total_templates,
    sim_stats['statistics']['total_tasks'],
    sim_stats['statistics']['simulated_renders'],
    sim_stats['statistics']['failures'].get('p0_blocked', 0),
    sim_stats['statistics']['failures'].get('ths_no_zhiji', 0),
    sim_stats['avg_per_task_ms'],
    ' / '.join(all_varieties),
    ' / '.join(all_ct),
    stats['pdf_total'], sum(1 for t in bound['templates'] if t['source']=='PDF' and t['template_risk_level']=='P0'), sum(1 for t in bound['templates'] if t['source']=='PDF' and t['template_risk_level']=='P1'), stats['pdf_clean'],
    stats['ths_total'], sum(1 for t in bound['templates'] if t['source']=='THS' and t['template_risk_level']=='P0'), sum(1 for t in bound['templates'] if t['source']=='THS' and t['template_risk_level']=='P1'), stats['ths_clean'],
    variety_filter_rows,
    ct_filter_rows,
    ', '.join(pdf_only_var) if pdf_only_var else '无',
    ', '.join(ths_only_var) if ths_only_var else '无',
    ', '.join(both_var) if both_var else '无',
    ct_diff_rows,
    stats['pdf_total'], stats['ths_total'],
    pdf_render, ths_render,
    pdf_blocked, ths_blocked,
    pdf_avg_series, ths_avg_series,
    render_groups['blocked'], blocked_rows,
    render_groups['review_first'], review_rows,
)

out_path = SIM_BASE / "enhanced_review_portal.md"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(md)

print("OK enhanced_review_portal.md: %d bytes, %d lines" % (os.path.getsize(out_path), len(md.splitlines())))
