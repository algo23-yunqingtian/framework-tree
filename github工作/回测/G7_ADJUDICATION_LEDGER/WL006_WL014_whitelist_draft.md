# WL006~WL014 白名单扩展草案

> **草案 ID**: DSHA-P54-WL-EXTENSION-DRAFT-001  
> **生成时间**: 2026-10-16T13:03:46.885301+08:00  
> **来源**: FL01_FL02_manual_review.md §4.2  
> **状态**: 草案 / 待 DSHC 逐条审批  
> **GATE**: CLOSED/HOLD  
> **Wind API**: 0 调用  
> **分支**: PHASE48_BASELINE  

---

## 1. 现有白名单 (WL-001 ~ WL-005)

| ID | 名称 | 覆盖范围 | 状态 |
|----|------|---------|------|
| WL-001 | G7_LEAKAGE_NOISE | G7 泄漏率边界告警噪声（31 次误报） | 已生效 |
| WL-002 | SYNTHETIC_DATA_ZERO_SIGNAL | 合成数据零信号 IC=0.0 | 已生效 |
| WL-003 | CROSS_VARIETY_IC | 跨品种 IC 计算 | 已生效 |
| WL-004 | WINDOW_BOUNDARY_ARTIFACT | 窗口边界伪影 | 已生效 |
| WL-005 | SHIFT_T1_ALIGNMENT | T+1 对齐 shift(-1) | 已生效 |

---

## 2. 建议新增白名单 (WL-006 ~ WL-014)

### WL-006 · BFILL_PREPROCESSING

| 属性 | 值 |
|------|----|
| **ID** | WL-006 |
| **名称** | BFILL_PREPROCESSING |
| **覆盖范围** | 数据预处理阶段 bfill 缺失值填充，非因子值计算 |
| **覆盖命中** | FL-01 × 2 |
| **涉及脚本** | `P49_data_cleaning_pipeline.py:148`, `P49_dryrun_pipeline.py:449` |
| **分类** | 数据预处理层 |
| **风险评估** | LOW — bfill 为行业标准缺失值填充策略 |
| **建议** | ✅ APPROVE |

### WL-007 · SHIFT_DIAGNOSTIC_METRIC

| 属性 | 值 |
|------|----|
| **ID** | WL-007 |
| **名称** | SHIFT_DIAGNOSTIC_METRIC |
| **覆盖范围** | 诊断检测用 shift(-1)（IC/ICIR/G7/G4 等指标计算），非因子值生成 |
| **覆盖命中** | FL-01 × 10 |
| **涉及脚本** | `P49_dryrun_pipeline.py:895,961,1051,1196,1230`, `P49_sensitivity_test.py:239`, `P49_threshold_stress.py:303,333`, `P49_backtest_audit/build_p54_kb.py:1053` |
| **分类** | 诊断检测层 |
| **风险评估** | LOW — shift(-1) 用于 T+1 收益计算，非因子值生成 |
| **建议** | ✅ APPROVE |

### WL-008 · DOC_PSEUDOCODE_UNEXECUTABLE

| 属性 | 值 |
|------|----|
| **ID** | WL-008 |
| **名称** | DOC_PSEUDOCODE_UNEXECUTABLE |
| **覆盖范围** | Markdown 文档代码块内伪代码，不可执行 |
| **覆盖命中** | FL-01 × 1 |
| **涉及脚本** | `P49_backtest_audit/build_p54_kb.py:1053` (Markdown pseudocode) |
| **分类** | 文档层 |
| **风险评估** | NONE — 不可执行的文档代码块 |
| **建议** | ✅ APPROVE |

### WL-009 · ILOCS_LAYER_METRIC

| 属性 | 值 |
|------|----|
| **ID** | WL-009 |
| **名称** | ILOCS_LAYER_METRIC |
| **覆盖范围** | 分层收益指标 iloc 提取（G11 多空收益计算），非因子值生成 |
| **覆盖命中** | FL-02 × 2 |
| **涉及脚本** | `P49_dryrun_pipeline.py:1512`, `P49_sensitivity_test.py` (iloc) |
| **分类** | 诊断检测层 |
| **风险评估** | LOW — iloc 用于分层统计，非时间截断越界 |
| **建议** | ✅ APPROVE |

### WL-010 · SCAFFOLD_WIND_NOTIMPLEMENTED

| 属性 | 值 |
|------|----|
| **ID** | WL-010 |
| **名称** | SCAFFOLD_WIND_NOTIMPLEMENTED |
| **覆盖范围** | Wind API 脚手架占位函数，标注 NOT_IMPLEMENTED，未被调用 |
| **覆盖命中** | FL-02 × 15 |
| **涉及脚本** | `factor_retest_real_data.py` (3), `factor_risk_review.py` (3), `P49_real_data_preprocessing.py` (12) |
| **分类** | 工具脚手架层 |
| **风险评估** | NONE — 函数体为 `raise NotImplementedError`，未被调用 |
| **建议** | ✅ APPROVE |

### WL-011 · UTIL_TRADINGCALENDAR

| 属性 | 值 |
|------|----|
| **ID** | WL-011 |
| **名称** | UTIL_TRADINGCALENDAR |
| **覆盖范围** | 交易日历生成工具函数，不参与因子计算 |
| **覆盖命中** | FL-02 × 3 |
| **涉及脚本** | `P49_real_data_preprocessing.py` (load_trading_calendar) |
| **分类** | 工具函数层 |
| **风险评估** | LOW — 日历生成不涉及因子值计算 |
| **建议** | ✅ APPROVE |

### WL-012 · DOC_COMMENT_PARAM

| 属性 | 值 |
|------|----|
| **ID** | WL-012 |
| **名称** | DOC_COMMENT_PARAM |
| **覆盖范围** | 文档注释/Docstring 参数描述中的时间范围描述 |
| **覆盖命中** | FL-02 × 3 |
| **涉及脚本** | `P49_real_backtest_pipeline.py` (time_range docstring), `P49_real_data_preprocessing.py` (docstring) |
| **分类** | 文档层 |
| **风险评估** | NONE — 文档注释不参与代码执行 |
| **建议** | ✅ APPROVE |

### WL-013 · SENSITIVITY_IC_COMPUTE

| 属性 | 值 |
|------|----|
| **ID** | WL-013 |
| **名称** | SENSITIVITY_IC_COMPUTE |
| **覆盖范围** | 敏感性测试 IC 指标计算中的 shift(-1)，非因子值生成 |
| **覆盖命中** | FL-01 × 1 |
| **涉及脚本** | `P49_sensitivity_test.py:239` |
| **分类** | 诊断检测层 |
| **风险评估** | LOW — 敏感性测试为诊断工具 |
| **建议** | ✅ APPROVE |

### WL-014 · STRESS_G7_COMPUTE

| 属性 | 值 |
|------|----|
| **ID** | WL-014 |
| **名称** | STRESS_G7_COMPUTE |
| **覆盖范围** | 阈值压力测试 G7 泄漏率 + 复合 IC 计算中的 shift(-1) |
| **覆盖命中** | FL-01 × 2 |
| **涉及脚本** | `P49_threshold_stress.py:303,333` |
| **分类** | 诊断检测层 |
| **风险评估** | LOW — 压力测试为诊断工具 |
| **建议** | ✅ APPROVE |

---

## 3. 白名单覆盖汇总

| 白名单 | 覆盖次数 | 覆盖类型 | 风险评估 |
|--------|---------|---------|---------|
| WL-006 | 2 | FL-01 bfill | LOW |
| WL-007 | 10 | FL-01 shift diagnostic | LOW |
| WL-008 | 1 | FL-01 doc pseudocode | NONE |
| WL-009 | 2 | FL-02 iloc metric | LOW |
| WL-010 | 15 | FL-02 scaffold Wind | NONE |
| WL-011 | 3 | FL-02 trading calendar | LOW |
| WL-012 | 3 | FL-02 doc comment | NONE |
| WL-013 | 1 | FL-01 sensitivity IC | LOW |
| WL-014 | 2 | FL-01 stress G7 | LOW |
| **合计** | **42** | — | — |

**覆盖率**: 42/42 (100%) ✅

---

## 4. 去重优化建议

WL-005 (`SHIFT_T1_ALIGNMENT`) 与 WL-007 (`SHIFT_DIAGNOSTIC_METRIC`) 存在部分重叠。

| 方案 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| A (推荐) | 合并为 `WL-005_SHIFT_ANY_CONTEXT` | 简化白名单管理 | 失去上下文细分 |
| B | 保留分拆 | 保留语义区分 | 需维护两条 |

---

## 5. DSHC 审批栏位

| 白名单 | DSHC 裁决 | 签名 | 时间 |
|--------|----------|------|------|
| WL-006 | ⏳ 待审批 | ⏳ 待填 | ⏳ 待填 |
| WL-007 | ⏳ 待审批 | ⏳ 待填 | ⏳ 待填 |
| WL-008 | ⏳ 待审批 | ⏳ 待填 | ⏳ 待填 |
| WL-009 | ⏳ 待审批 | ⏳ 待填 | ⏳ 待填 |
| WL-010 | ⏳ 待审批 | ⏳ 待填 | ⏳ 待填 |
| WL-011 | ⏳ 待审批 | ⏳ 待填 | ⏳ 待填 |
| WL-012 | ⏳ 待审批 | ⏳ 待填 | ⏳ 待填 |
| WL-013 | ⏳ 待审批 | ⏳ 待填 | ⏳ 待填 |
| WL-014 | ⏳ 待审批 | ⏳ 待填 | ⏳ 待填 |

---

## 6. 治理不变量

| 不变量 | 状态 |
|--------|------|
| Wind API 调用 | 0 ✅ |
| 回测执行 | false ✅ |
| 因子公式改动 | 无 ✅ |
| GATE | CLOSED/HOLD ✅ |
| Release Permit | NOT_ISSUED ✅ |
| 上游写入 | 0 ✅ |
| P53 基线修改 | 无 ✅ |

---

> **签名**  
> DSHA-P54 (自动): 2026-10-16T13:03:46.885301+08:00  
> DSHC 审批: ⏳ 待填  
