# 评审门户操作手册

> 工单: `HERMES_V85_REVIEW_PORTAL_ENHANCE_AND_RENDER_SIMULATION`  
> 适用版本: 评审门户 v4 (`enhanced_review_portal.md`)

---

## 1. 概述

本手册介绍 V85 图表模板评审门户 v4 的全部功能使用方法，包括：
1. 多维度批量筛选
2. 模板详情弹窗查看
3. 人工评审标记
4. CSV 导出
5. DSHB 动态加载

**约束**: 门户为静态 Markdown 文档，所有操作通过命令行 + CSV/JSON 文件完成，不依赖 Web 服务器。

---

## 2. 多维度批量筛选

### 2.1 筛选维度

| 维度 | 可选值 | 说明 |
|------|--------|------|
| 来源 | PDF / THS | 模板来源 |
| 风险等级 | P0 / P1 / CLEAN | 模板级风险等级 |
| 品种 | AL / AO / CU / LC / LI / NI / SI / SN / ZN | 品种代码 |
| 图表类型 | 单折线 / 多折线 / 堆叠柱状 / 复合混合 | 图表渲染类型 |

### 2.2 筛选命令

```bash
# 按来源 + 风险等级筛选
python3 -c "
import json
bound = json.load(open('chart_risk_bound_all.json'))
filtered = [t for t in bound['templates'] if t['source']=='PDF' and t['template_risk_level']=='P0']
print('筛选结果:', len(filtered), '条')
for t in filtered[:10]:
    print(' ', t['template_id'], t['variety'], t['template_risk_level'])
"
```

### 2.3 批量导出 CSV

```bash
python3 -c "
import json, csv
bound = json.load(open('chart_risk_bound_all.json'))
# 筛选条件: PDF + P0
filtered = [t for t in bound['templates'] if t['source']=='PDF' and t['template_risk_level']=='P0']
with open('filtered_export.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['template_id','source','variety','chart_type','template_risk_level','p0_count','p1_count','series_count'])
    w.writeheader()
    for t in filtered:
        w.writerow({k: t.get(k,'') for k in w.fieldnames})
print(f'导出 {len(filtered)} 条到 filtered_export.csv')
"
```

---

## 3. 模板详情弹窗

### 3.1 查看单张模板详情

在 `enhanced_review_portal.md` 的 §2 和 §4 中，点击 `<details>` 标签展开模板详情。

### 3.2 编程方式查看详情

```bash
# 查看指定模板的完整风险明细
python3 -c "
import json
bound = json.load(open('chart_risk_bound_all.json'))
target = 'TPL-LC-091'
for t in bound['templates']:
    if t['template_id'] == target:
        print(json.dumps(t, ensure_ascii=False, indent=2))
        break
"
```

### 3.3 详情字段说明

| 字段 | 说明 |
|------|------|
| template_id | 模板ID |
| source | 来源 (PDF/THS) |
| variety | 品种 |
| chart_type | 图表类型 |
| template_risk_level | 模板级风险等级 |
| p0_count | P0冲突系列数 |
| p1_count | P1冲突系列数 |
| series_risks | 每条series的风险明细 |
| series_risks[].risk_level | 系列级风险等级 |
| series_risks[].group_id | 黑名单规则编号 |
| series_risks[].hit_words_a | 系列名命中关键词 |
| series_risks[].hit_words_b | zhiji名命中关键词 |
| series_risks[].reason | 冲突根因 |

---

## 4. 人工评审标记

### 4.1 评审流程

```
1. 筛选需要评审的模板（按 P0/P1 筛选）
2. 逐张查看详情弹窗
3. 决定评审结果（通过/驳回/临时白名单放行）
4. 填写 review_decisions.csv
5. 提交
```

### 4.2 评审 CSV 格式

创建 `review_decisions.csv`：

```csv
template_id,source,reviewer,review_time,decision,remark,previous_risk_level,new_status
TPL-LC-091,PDF,张三,2026-09-30 16:00:00,驳回,产量vs销量冲突确认,P0,REJECTED
TPL-AO-020,PDF,李四,2026-09-30 16:05:00,临时白名单放行,堆场口径待复核但业务确认,P0,WHITELISTED
TPL-SN-034,PDF,王五,2026-09-30 16:10:00,通过,拟合vs指数口径差异在可接受范围,P1,APPROVED
```

### 4.3 评审结果字段

| 字段 | 说明 | 可选值 |
|------|------|--------|
| decision | 评审结果 | 通过 / 驳回 / 临时白名单放行 |
| new_status | 新状态 | APPROVED / REJECTED / WHITELISTED |
| remark | 备注 | 自由文本 |
| previous_risk_level | 原风险等级 | P0 / P1 / CLEAN |

---

## 5. DSHB 动态加载

### 5.1 加载 DSHB CSV

当 DSHB 提交 `unified_indicator_risk_db.csv` 后，执行：

```bash
cd analysis/e2e_output/v85/v85_portal_enhance_render_sim

python3 enhanced_auto_semantic_check.py \
  --load-dshb unified_indicator_risk_db.csv \
  --refresh \
  --blacklist ../review_package/blacklist_update/semantic_blacklist_hermes_fixed.json
```

### 5.2 预期输出

- 加载成功: `status: LOADED`，显示 CSV 行数、识别的列名、新增关键词数、冲突条目数
- 刷新风险标签: `status: REFRESHED`，显示扫描的模板数、标签变更数
- CSV 不存在: `status: NOT_FOUND`

### 5.3 CSV 兼容格式

CSV 自动识别以下列名（不区分大小写）：

| 必需列（任一） | 可选列 |
|----------------|--------|
| indicator_id | series_name |
| template_id | zhiji_name |
| chart_id | risk_level / severity |
| | group_id |
| | label |
| | keywords |

---

## 6. 渲染仿真

### 6.1 查看仿真结果

```bash
# 查看仿真统计
cat render_simulation_stats.json | python3 -m json.tool

# 查看仿真日志（CSV）
head -5 render_simulation_log.csv

# 筛选仿真失败案例
python3 -c "
import csv
with open('render_simulation_log.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        if row['final_status'] not in ('RENDERED', 'QUEUED_FOR_REVIEW'):
            print(row['template_id'], row['final_status'], row.get('failure_desc',''))
" | head -20
```

### 6.2 仿真日志字段

| 字段 | 说明 |
|------|------|
| stage1_load_ms | 模板加载耗时(ms) |
| stage2_schema_ms | Schema校验耗时(ms) |
| stage3_semantic_ms | 语义校验耗时(ms) |
| stage4_route_ms | 任务路由耗时(ms) |
| stage5_render_ms | 渲染引擎耗时(ms) |
| final_status | 最终状态 |
| failure_scenario | 失败场景 |
| failure_desc | 失败描述 |

---

## 7. 结构化校验日志

### 7.1 查看校验日志

```bash
# 日志为 JSONL 格式，每行一条
head -3 render_scan_log.jsonl

# 统计事件类型
python3 -c "
import json
from collections import Counter
events = Counter()
for line in open('render_scan_log.jsonl'):
    e = json.loads(line)
    events[e['event']] += 1
for k, v in events.most_common():
    print(f'  {k}: {v}')
"
```

### 7.2 日志事件类型

| 事件 | 说明 |
|------|------|
| BLACKLIST_LOADED | 黑名单加载完成 |
| SEMANTIC_CHECK | 单条语义校验 |
| VERIFY_CASES | P0回归测试 |
| DSHB_CSV_LOADED | DSHB CSV加载 |
| DSHB_CSV_NOT_FOUND | DSHB CSV不存在 |
| RISK_LABEL_CHANGED | 风险标签变更 |
| RISK_LABELS_REFRESHED | 风险标签刷新完成 |
