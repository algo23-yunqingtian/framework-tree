# 交付物④：Key-Name错配标记（N3修复）

> 工单：DSH_B_P3_FIX_20260924 | 日期：2026-09-24

---

## 1. 修复概况

| 项目 | 数值 |
|------|------|
| 标记条目数 | 4 |
| 标记方式 | `indicators_v1.json` 内写入 `_flag: FLAGGED_FOR_REVIEW` |
| 文档记录 | 本文件 |
| 标记完成度 | 4/4 (100%) |

---

## 2. 4条错配条目详情

### 2.1 `al_2_scrap_al_import_source`

| 字段 | 值 |
|------|-----|
| name | 易拉罐盖料：产量：中国（年） |
| _flag | **FLAGGED_FOR_REVIEW** |
| _nodes | ['2.'] |
| ids | `{"al": "ID01668771"}` |
| series_slice |  |
### 2.2 `li_52_battery`

| 字段 | 值 |
|------|-----|
| name | 动力电池装车量宁德时代（月） |
| _flag | **FLAGGED_FOR_REVIEW** |
| _nodes | ['5.2'] |
| ids | `{"LI": "ID01660879"}` |
| series_slice | battery |
### 2.3 `li_52_ev_sales`

| 字段 | 值 |
|------|-----|
| name | SMM新能源汽车销量（月） |
| _flag | **FLAGGED_FOR_REVIEW** |
| _nodes | ['5.2'] |
| ids | `{"LI": "a12775570"}` |
| series_slice |  |
### 2.4 `ni_45_output_2`

| 字段 | 值 |
|------|-----|
| name | MHP：以金属量计：产量：印尼（月） |
| _flag | **FLAGGED_FOR_REVIEW** |
| _nodes | ['4.5'] |
| ids | `{"ni": "ID01525680"}` |
| series_slice |  |
---

## 3. FLAGGED_FOR_REVIEW标记机制

### 3.1 标记方式

在 `indicators_v1.json` 中，4条错配条目已写入独立 `_flag` 字段：

```json
{{
  "al_2_scrap_al_import_source": {{
    "name": "...",
    "ids": {{...}},
    "_flag": "FLAGGED_FOR_REVIEW"
  }}
}}
```

### 3.2 标记含义

`FLAGGED_FOR_REVIEW` 表示：
1. key与name语义存在不匹配
2. 需要FT主脑/人工复核确认正确归类
3. 当前标记为临时状态，待裁决后可能重命名或修正name

### 3.3 后续处理

待FT主脑裁决后：
- 若确认key正确：移除 `_flag` 字段
- 若需重命名：更新key并保留 `_renamed_from` 记录
- 若需修正name：更新name字段

---

*生成时间：2026-09-25 17:21*
