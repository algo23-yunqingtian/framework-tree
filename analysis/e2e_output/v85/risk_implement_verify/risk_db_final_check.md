# 统一风险数据库完整性校验报告

**生成时间**: 2026-10-01 03:36:54
**任务**: DSH-B_V85_RISK_IMPLEMENT_VERIFY_AND_RISKDB_OFFICIAL_LANDING
**输入文件**: unified_indicator_risk_db.csv (50 条原始数据)
**输出文件**: unified_indicator_risk_db_final.csv (50 条数据)

---

## 1. 完整性校验总览

| 校验项 | 预期值 | 实际值 | 结果 |
|--------|--------|--------|------|
| 原始数据总条数 | 50 | 50 | ✓ |
| 去重后独立条目 | 41 | 41 | ✓ |
| 重复条目 | 9 | 9 | ✓ |
| P0 阻塞项 | 25 | 25 | ✓ |
| P1 警告项 | 16 | 16 | ✓ |
| 根因类别 A | 37 | 37 | ✓ |
| 根因类别 B | 3 | 3 | ✓ |
| 根因类别 C | 1 | 1 | ✓ |

---

## 2. 字段补全校验

### 2.1 补全字段清单

| 字段名 | 说明 | 补全率 |
|--------|------|--------|
| root_cause_category | 根因分类 (A/B/C) | 41/41 |
| root_cause_explanation | 根因说明 | 41/41 |
| fix_option_1 | 修复方案1 | 41/41 |
| fix_option_2 | 修复方案2 | 41/41 |
| fix_option_3 | 修复方案3 | 41/41 |
| primary_fix | 主修复方案 | 41/41 |
| fix_cost | 修复成本 | 41/41 |
| fix_priority | 修复优先级 | 41/41 |
| can_automate | 是否可自动化 | 41/41 |
| requires_manual | 是否需要人工 | 41/41 |
| recommended_fix | 推荐修复方案 | 41/41 |
| gate_blocking | Gate阻塞标记 | 41/41 |
| can_whitelist | 是否可白名单 | 41/41 |
| gate_status | Gate状态 | 41/41 |

### 2.2 缺失字段明细

**无缺失字段** — 全部 41 条独立风险条目的所有补全字段均已填充。

---

## 3. 根因分类对齐校验

### 3.1 分类分布

| 根因类别 | 数量 | 占比 | P0 | P1 | 与报告对齐 |
|----------|------|------|-----|-----|-----------|
| A: 算法缺陷 | 37 | 90.2% | 24 | 13 | ✓ |
| B: 术语歧义 | 3 | 7.3% | 0 | 3 | ✓ |
| C: 上游问题 | 1 | 2.4% | 1 | 0 | ✓ |

### 3.2 根因×Gate状态交叉

| 根因 | Gate Blocked | Gate Pass | Gate Conditional |
|------|-------------|-----------|------------------|
| A | 24 | 13 | 0 |
| B | 0 | 3 | 0 |
| C | 0 | 0 | 1 |

---

## 4. 黑名单规则对齐校验

| 规则ID | 原始触发数 | 最终库中数量 | 对齐 |
|--------|-----------|-------------|------|
| BL-002 | 1 | 1 | ✓ |
| BL-003 | 1 | 1 | ✓ |
| BL-005 | 1 | 1 | ✓ |
| BL-009 | 1 | 1 | ✓ |
| BL-012 | 12 | 12 | ✓ |
| BL-015 | 1 | 1 | ✓ |
| BL-016 | 4 | 4 | ✓ |
| BL-018 | 7 | 7 | ✓ |
| BL-019 | 1 | 1 | ✓ |
| BL-020 | 1 | 1 | ✓ |
| BL-021 | 1 | 1 | ✓ |
| BL-022 | 7 | 7 | ✓ |
| BL-025 | 3 | 3 | ✓ |

---

## 5. 重复条目去重校验

| 重复组 | 原始ID | 重复标记ID | 去重后保留 | 对齐 |
|--------|--------|-----------|-----------|------|
| PDF:TPL-LC-084 | PDF:TPL-LC-084 | RISK-004, RISK-008 | PDF:TPL-LC-084 | ✓ |
| PDF:TPL-LC-087 | PDF:TPL-LC-087 | RISK-009 | PDF:TPL-LC-087 | ✓ |
| PDF:TPL-LC-091 | PDF:TPL-LC-091 | RISK-007 | PDF:TPL-LC-091 | ✓ |
| PDF:TPL-SI-014 | PDF:TPL-SI-014 | RISK-012 | PDF:TPL-SI-014 | ✓ |
| THS:THS-NI-3.1 | THS:THS-NI-3.1 | RISK-018, RISK-019 | THS:THS-NI-3.1 | ✓ |
| THS:THS-SI-3.1.3 | THS:THS-SI-3.1.3 | RISK-023 | THS:THS-SI-3.1.3 | ✓ |
| THS:THS-SN-5.1 | THS:THS-SN-5.1 | RISK-049 | THS:THS-SN-5.1 | ✓ |

---

## 6. 校验结论

| 校验维度 | 结果 |
|----------|------|
| 条目完整性 | ✓ 41条独立风险条目全部入库，无丢失 |
| 重复去重 | ✓ 9条重复条目正确标记 |
| 字段补全 | ✓ 全部补全字段已填充 |
| 根因分类对齐 | ✓ 与risk_rootcause_detail.csv严格对齐 |
| P0/P1分级对齐 | ✓ P0=25, P1=16，与报告一致 |
| 黑名单规则对齐 | ✓ 所有13条规则覆盖完整 |
| Gate标记 | ✓ P0=BLOCKED/CONDITIONAL, P1=PASS |

**最终结论**: ✓ **完整性校验通过** — unified_indicator_risk_db_final.csv 可正式交付。

---

**约束声明**: NO_SOURCE_MODIFICATION=true, NO_GT_MODIFICATION=true, NO_RULE_MODIFICATION=true
