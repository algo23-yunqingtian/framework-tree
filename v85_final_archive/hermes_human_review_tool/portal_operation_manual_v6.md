# V85 评审门户 v6 操作手册

> 工单: `HERMES_V85_HUMAN_REVIEW_TOOL_ENHANCE_AND_BATCH_DATA_PREP`
> 适用门户: `enhanced_review_portal_v5_review_workbench.md`
> v6新增: 人工评审工作台操作教程 + Gate进度看板 + P0风险批量处置

---

## 1. 门户入口

```bash
# 工作台门户文档
cat analysis/e2e_output/v85/hermes_human_review_tool/enhanced_review_portal_v5_review_workbench.md

# 上一版门户（v5）
cat analysis/e2e_output/v85/hermes_portal_gate_final/enhanced_review_portal_v5_full.md
```

---

## 2. 人工评审工作台（v6新增）

### 2.1 进入工作台

打开门户 §12 人工评审工作台面板。

### 2.2 P0风险筛选

```bash
# 筛选所有P0阻塞风险
python3 batch_export_import_v2.py --filter-risk blocked --out p0_blocked.csv

# 按品种筛选
python3 batch_export_import_v2.py --filter-risk variety=NI --out ni_p0.csv

# 按RISK-ID筛选
grep "RISK-006" v85_p0_risk_human_workbook.csv
```

### 2.3 批量处置操作

#### 步骤1: 导出待处置风险

```bash
python3 batch_export_import_v2.py --export-risk --out risk_to_fill.csv
```

#### 步骤2: 人工填写处置结论

在CSV中填写：
- `human_disposal`: 修复 / 白名单 / 观察
- `human_remark`: 处置理由
- `reviewer`: 评审人
- `review_time`: 评审时间

#### 步骤3: 导入处置结果

```bash
python3 batch_export_import_v2.py --import risk_filled.csv --apply
```

#### 步骤4: 查看关联回放

```bash
# 查看模板回放结果
grep "TPL-LC-091" dshb_full_integrate/full_488_template_playback_result.csv
```

#### 步骤5: 快速跳转模板series

```bash
grep "TPL-LC-091" review_batches_v6/batch_C_review_v6.csv
```

### 2.4 处置结论说明

| 处置 | 说明 | 后续动作 |
|------|------|---------|
| 修复 | 替换正确指标 | 更新模板series zhiji_id |
| 白名单 | 临时放行 | 记录白名单条目+过期日期 |
| 观察 | 暂不处置，持续监控 | 标记为观察项 |

---

## 3. Gate进度看板（v6新增）

### 3.1 查看Gate进度

打开门户 §13 Gate阻塞进度看板。

### 3.2 Gate状态说明

| 状态 | 说明 |
|------|------|
| ✅ PASS | Gate通过 |
| ⚠ PARTIAL | 部分通过 |
| ❌ BLOCKED | 阻塞未通过 |

### 3.3 查看Gate跟踪表

```bash
cat gate_block_tracker.csv
```

### 3.4 Gate预校验

人工评审完成后，一键重跑Gate自检：

```bash
python3 gate_pre_check.py
```

---

## 4. THS批量回填操作（v6新增）

### 4.1 导出待回填THS条目

```bash
python3 batch_export_import_v2.py --export-batch B --out ths_to_fill.csv
```

### 4.2 人工回填zhiji_id

在CSV中填写 `manual_zhiji_id` 字段。

### 4.3 导入回填结果

```bash
python3 batch_export_import_v2.py --import ths_filled.csv --apply --manifest manifest.json
```

### 4.4 跨品种风险预警

回填时自动校验：
- 别名库匹配（indicator_alias_library.csv）
- 高危混淆对（high_risk_confusion_pairs.csv）
- 跨品种风险（BL-022 跨品种规则）

---

## 5. 批次v6评审操作

### 5.1 查看批次

| 批次 | 范围 | 数量 | 文件 |
|------|------|------|------|
| Batch-A | 可直接+高置信 | 97 | batch_A_review_v6.csv |
| Batch-B | THS待匹配 | 155 | batch_B_review_v6.csv |
| Batch-C | 阻塞/复核/降级 | 236 | batch_C_review_v6.csv |

### 5.2 v6新增字段

| 字段 | 说明 |
|------|------|
| risk_id | 关联P0风险ID |
| disposal_suggestion | 处置建议(阻塞待处置/复核/可直接放行) |
| gate_blocked | Gate阻塞标记(YES/NO) |
| inconsistent_risk | DSHB不一致风险根因 |
| human_review_result | 人工评审结果占位列 |

---

## 6. 归档规范（v6新增）

人工评审完成后按规范归档：

```bash
# 目录结构
hermes_human_review_tool/
├── review_archive/
│   ├── batch_A_completed_YYYYMMDD.csv
│   ├── batch_B_completed_YYYYMMDD.csv
│   ├── batch_C_completed_YYYYMMDD.csv
│   └── archive_manifest.md
```

详见 `human_review_archive_spec.md`。
