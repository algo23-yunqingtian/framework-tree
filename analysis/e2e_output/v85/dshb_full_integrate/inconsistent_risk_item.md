# 风险库与黑名单规则一致性校验报告

**生成时间**: 2026-10-01 12:00:18
**任务**: DSH-B_V85_FULL_CHAIN_INTEGRATE_VALIDATE_AND_FINAL_GATE_PREP
**输入**: unified_indicator_risk_db_final.csv (25条P0风险条目)
**输出**: inconsistent_risk_items.csv + inconsistent_risk_item.md

---

## 1. 一致性校验总览

| 校验项 | 数量 | 结果 |
|--------|------|------|
| P0风险条目总数 | 25 | — |
| 可被新版规则命中 | 20 | ✓ |
| 无法被规则命中 | 5 | ⚠ 需分析 |
| 命中覆盖率 | 20/25 (80.0%) | — |

---

## 2. 无法命中的风险条目分析

| 风险ID | 模板ID | 品种 | 指标名称 | 匹配名称 | 黑名单ID | 根因分析 |
|--------|--------|------|----------|----------|-----------|----------|
| RISK-002 | TPL-LC-054 | LC | 碳酸锂 三元523需求 | SMM: 碳酸锂现金生产利润: 外购三元极片黑粉（Li: 5 | BL-009 | 黑名单规则BL-009存在但指标名称差异导致无法命中，需检查left_patterns/right_patterns覆盖率 |
| RISK-005 | TPL-LC-087 | LC | 磷酸铁锂 电池 国内销量 |  | BL-015 | 黑名单规则BL-015存在但指标名称差异导致无法命中，需检查left_patterns/right_patterns覆盖率 |
| RISK-010 | TPL-NI-008 | NI | 中国电解镍净进口量 |  | BL-022 | 黑名单规则BL-022存在但指标名称差异导致无法命中，需检查left_patterns/right_patterns覆盖率 |
| RISK-011 | TPL-SI-014 | SI | 工业硅样本工厂库存(SMM) |  | BL-020 | 黑名单规则BL-020存在但指标名称差异导致无法命中，需检查left_patterns/right_patterns覆盖率 |
| RISK-013 | TPL-SI-019 | SI | 工业硅供需平衡 |  | BL-021 | 黑名单规则BL-021存在但指标名称差异导致无法命中，需检查left_patterns/right_patterns覆盖率 |

---

## 3. 可命中的风险条目汇总

| 黑名单规则 | 命中数量 | 覆盖案例 |
|-----------|----------|----------|
| BL-002 | 1 | RISK-006 |
| BL-003 | 1 | RISK-003 |
| BL-005 | 1 | RISK-001 |
| BL-018 | 7 | RISK-024, RISK-025, RISK-026, RISK-027, RISK-028, RISK-029, RISK-030 |
| BL-018a | 7 | RISK-024, RISK-025, RISK-026, RISK-027, RISK-028, RISK-029, RISK-030 |
| BL-018b | 2 | RISK-031, RISK-032 |
| BL-019 | 1 | RISK-022 |
| BL-022 | 6 | RISK-014, RISK-015, RISK-016, RISK-017, RISK-020, RISK-021 |
| BL-025 | 3 | RISK-031, RISK-032, RISK-033 |
| BL-025a | 1 | RISK-033 |

---

## 4. 校验结论

| 维度 | 结果 |
|------|------|
| P0命中覆盖率 | 20/25 (80.0%) |
| 无法命中条目 | 5条 |
| 整体评估 | ⚠ 需人工处理 |

**结论**: ⚠ 存在不一致条目，需人工分析根因

---

**约束声明**: NO_SOURCE_MODIFICATION=true, NO_GT_MODIFICATION=true
