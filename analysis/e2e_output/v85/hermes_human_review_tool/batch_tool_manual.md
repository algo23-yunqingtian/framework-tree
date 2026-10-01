# 批量回填工具使用手册 (batch_tool_manual.md)

> 工单: `HERMES_V85_HUMAN_REVIEW_TOOL_ENHANCE_AND_BATCH_DATA_PREP`
> 适用脚本: `batch_export_import_v2.py`
> 依赖: `indicator_alias_library.csv`、`high_risk_confusion_pairs.csv`

---

## 1. 工具概述

`batch_export_import_v2.py` 是升级版批量导入导出工具，支持：
- 批量导出待评审条目（按批次/品种/风险筛选）
- 批量导入评审结果（含跨品种校验+别名校验+混淆预警）
- P0风险工作表导出/导入/处置
- 回填变更日志自动生成

---

## 2. 命令速查

### 2.1 导出操作

```bash
# 导出Batch-A（可直接+高置信）
python3 batch_export_import_v2.py --export-batch batch_A --out batch_a_export.csv

# 导出Batch-B（THS待匹配155条）
python3 batch_export_import_v2.py --export-batch batch_B --out ths_to_fill.csv

# 导出Batch-C（阻塞/复核/降级）
python3 batch_export_import_v2.py --export-batch batch_C --out blocked_review.csv

# 按品种+风险筛选
python3 batch_export_import_v2.py --export-batch batch_C --filter variety=NI,risk_level=P0 --out ni_p0.csv
```

### 2.2 P0风险导出

```bash
# 导出全部P0风险工作表
python3 batch_export_import_v2.py --export-risk --out all_p0_risks.csv

# 筛选P0阻塞风险
python3 batch_export_import_v2.py --filter-risk blocked --out p0_blocked.csv

# 按品种筛选P0风险
python3 batch_export_import_v2.py --filter-risk variety=NI --out ni_p0.csv
```

### 2.3 导入操作

```bash
# 导入评审结果（含跨品种校验）
python3 batch_export_import_v2.py --import ths_filled.csv --apply --manifest manifest.json

# 指定输出路径
python3 batch_export_import_v2.py --import ths_filled.csv --apply --manifest manifest.json --out manifest_v6.json
```

---

## 3. 回填校验规则

### 3.1 跨品种风险强提醒（BL-022）

回填时自动检查指标名是否含其他品种关键词：

| 检查 | 规则 | 动作 |
|------|------|------|
| 指标名含"铜"但模板品种为NI | BL-022 跨品种 | **阻止回填**，需人工确认 |
| 指标名含"镍"但模板品种为CU | BL-022 跨品种 | **阻止回填** |
| 指标名含"锂"但模板品种为SI | BL-022 跨品种 | **阻止回填** |

品种关键词映射：

| 品种 | 关键词 |
|------|--------|
| AL | 铝/氧化铝/电解铝 |
| AO | 氧化铝/铝土矿 |
| CU | 铜/精铜/电解铜 |
| LC | 碳酸锂/锂/磷酸铁锂 |
| LI | 锂/碳酸锂/氢氧化锂 |
| NI | 镍/电解镍/硫酸镍 |
| SI | 硅/工业硅/多晶硅 |
| SN | 锡/精锡/焊锡 |
| ZN | 锌/精锌/氧化锌 |

### 3.2 别名库校验

回填时自动匹配 `indicator_alias_library.csv`（864条）：
- 匹配成功：记录 `alias_matched: true`
- 匹配失败：不阻止回填，但在日志中标记

### 3.3 高危混淆对校验

回填时自动检查 `high_risk_confusion_pairs.csv`（13条）：
- 命中P0混淆对：记录预警，不阻止回填
- 命中P1混淆对：记录预警（BL-021已修复的3条自动跳过）

### 3.4 zhiji_id格式校验

正则: `^[A-Za-z][A-Za-z0-9_]+$`
- 合规：应用回填
- 不合规：跳过+警告

---

## 4. 变更日志

每次导入操作自动生成变更日志：

```
manifest_v6_updated_change_log.json
[
  {
    "timestamp": "2026-10-01T15:30:00",
    "type": "APPLY",
    "template_id": "THS-NI-2.3",
    "series_index": "0",
    "zhiji_id": "ID01001761",
    "decision": "通过",
    "alias_matched": true,
    "confusion_count": 0
  },
  {
    "timestamp": "2026-10-01T15:30:01",
    "type": "CROSS_VARIETY_BLOCK",
    "template_id": "THS-NI-2.3",
    "indicator": "COMEX铜持仓量",
    "variety": "NI",
    "warnings": [{"severity": "P0", "message": "指标名含\"铜\"(品种CU)..."}]
  }
]
```

---

## 5. CSV格式

### 5.1 评审结果CSV

```csv
template_id,series_index,manual_zhiji_id,decision,remark,reviewer,review_time
THS-NI-2.3,0,ID01001761,通过,别名匹配正确,张三,2026-10-01 15:00:00
THS-NI-3.1,1,,驳回,跨品种风险,李四,2026-10-01 15:05:00
```

### 5.2 P0风险处置CSV

```csv
risk_id,template_id,variety,human_disposal,human_remark,reviewer,review_time
RISK-006,TPL-LC-091,LC,修复,替换为产量指标,张三,2026-10-01 15:00:00
RISK-014,THS-NI-2.3,NI,观察,BL-022已拦截,李四,2026-10-01 15:05:00
```
