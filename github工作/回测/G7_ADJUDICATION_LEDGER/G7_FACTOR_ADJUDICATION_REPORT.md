# G7 因子裁决报告

> **报告 ID**: DSHC-P66-G7-FACTOR-ADJUDICATION-001  
> **裁决对象**: PHASE48_BASELINE / PHASE49_ACCESS_READINESS / G7_FACTOR_ADJUDICATION  
> **裁决人**: DSHC-P66  
> **生成时间**: 2026-10-16 GMT+8  
> **材料包**: `G7_ADJUDICATION_LEDGER/G7_ADJUDICATION_PACKAGE_MANIFEST.json`  
> **发布标签**: `P49-SYNTHETIC-V1`  
> **GATE**: `CLOSED/HOLD`  
> **Wind API 调用**: `0`  
> **分支**: `PHASE48_BASELINE`  
> **Release Permit**: `NOT_ISSUED`  
> **Git push**: `NOT_EXECUTED`  
> **生效声明**: 本报告为正式裁决文档；本报告本身不自动签发 Release Permit，不自动打开 GATE。调度确认后方可执行许可签发预案。

---

## 0. 裁决结论总览

| 项目 | 正式裁决 |
|---|---|
| 材料包完整性 | PASS |
| 核心四文档 | 4/4 PRESENT / SHA256 已归档 |
| 7 因子准入 | 0 PASS / 3 CONDITIONAL_PASS / 4 HOLD |
| 因子生产放行 | NOT_ALLOWED |
| WL-006~WL-014 白名单 | APPROVED_FOR_CODE_LEAKAGE_SCANNER / ACTIVE |
| WL006~WL014 编号空间 | 方案 A：编号隔离，已确认 |
| FL-01/FL-02 告警 | 42/42 FALSE_ALARM，0 DEFECT |
| Poll39 审计 | PASS，READ_ONLY |
| P66 KB 二次验收 | PASS_CONDITIONAL |
| P49/P53 基线 | 未修改 |
| 审计账本 | 未修改 |
| GATE | CLOSED/HOLD |
| Release Permit | NOT_ISSUED |

**最终裁决**：G7 因子裁决正式生效，但全部 7 因子均不进入生产放行。仅 FACTOR-004 / FACTOR-006 / FACTOR-007 可标记为 `CONDITIONAL_PASS`，作为后续真实 Wind 数据与灰度前置条件满足后的候选项。FACTOR-001 / FACTOR-002 / FACTOR-003 / FACTOR-005 维持 `HOLD`。

---

## 1. 材料包完整性裁决

### 1.1 核心四文档核验

| # | 文档 | 结论 | 状态 |
|---|---|---|---|
| 1 | `FL01_FL02_manual_review.md` | FL-01/FL-02 人工复核完成，42 次命中 100% FALSE_ALARM | PRESENT |
| 2 | `poll39_main_audit_report.md` | Poll39 全量只读审计 PASS，0 哈希漂移，上游写入 0 | PRESENT |
| 3 | `poll39_factor_leakage_risk_appendix.md` | FL-01=19、FL-02=23、FL-03=0；7 因子泄露风险结论已记录 | PRESENT |
| 4 | `P66_KB_SECOND_REVIEW_REPORT.md` | P66 知识库二次验收 `PASS_CONDITIONAL` | PRESENT |

**裁决**: 核心四文档齐备，DRAFT 阶段指出的“4 份缺失”问题已关闭。

### 1.2 辅助审阅材料与白名单草案

| 文档 | 结论 | 状态 |
|---|---|---|
| `WL006_WL014_whitelist_draft.md` | 9 条代码层白名单草案覆盖 42/42 次 FL-01/FL-02 命中 | APPROVED_BY_THIS_REPORT |
| `DRAFT_REVIEW_COMMENTS.md` | DSHA 草稿审阅意见，含 2 项 CRITICAL 异议 | ACKNOWLEDGED |
| `DRAFT_REVIEW_COMMENTS_RESPONSE.md` | DSHC 内部回执，确认已接收 DSHA 审阅意见 | ACKNOWLEDGED |
| `G7_ADJUDICATION_PACKAGE_MANIFEST.json` | 台账包清单与治理不变量记录 | UPDATED_WITH_THIS_REPORT |
| `SHA256_CHECKSUMS.txt` | 台账哈希归档 | UPDATED_WITH_THIS_REPORT |

---

## 2. DSHA 两项 CRITICAL 异议处理裁决

| 异议 | DSHA 结论 | DSHC 正式处理 | 结果 |
|---|---|---|---|
| CRITICAL-1：缺失文档清单状态错误 | 3/4 已交付，仅 P66 缺失 | P66 已补齐；核心四文档状态统一为 PRESENT | CLOSED |
| CRITICAL-2：WL006~WL014 语义冲突 | 因子级白名单与代码层白名单编号空间冲突 | 采用方案 A：编号空间分离 | CLOSED |

### 2.1 方案 A：白名单编号隔离规则

本报告正式落地方案 A，后续所有文档、脚本、审批记录必须遵守：

| 编号空间 | 用途 | 裁决状态 | 适用对象 |
|---|---|---|---|
| `WL-001` ~ `WL-005` | 既有白名单 / G7 已知安全边界 | ACTIVE | 既有规则 |
| `WL-006` ~ `WL-014` | **代码层泄漏扫描白名单** | ACTIVE / APPROVED | FL-01 / FL-02 / FL-03 扫描器命中分类 |
| `WL-A001` ~ `WL-A00N` | **因子级放行条件跟踪白名单** | RESERVED / TRACKING_ONLY | G7 因子级条件项、阻断项、后续真实数据验证项 |

**隔离规则**：

1. `WL-006` ~ `WL-014` 只能用于代码层扫描器命中分类，不得再用于因子级准入条件描述。
2. 因子级条件跟踪必须使用 `WL-A*` 编号，避免与代码层白名单发生语义混用。
3. `WL-A*` 编号不代表生产放行；其状态必须与本报告 §3 的 7 因子准入判定保持一致。
4. 新增代码层扫描器白名单从 `WL-015` 起递增；新增因子级条件跟踪从 `WL-A001` 起递增。
5. 任何将 `WL-006~WL-014` 重新解释为因子级放行条件的事项，均视为编号空间违规，需退回重审。

---

## 3. 7 因子最终准入判定

| Factor ID | 因子代码 / 名称 | Poll39 / 泄露结论 | 本轮最终准入 | 生产放行 | 核心依据 | 后续条件 |
|---|---|---|---|---|---|---|
| FACTOR-001 | F19_hot_money_weight / 热钱权重因子 | N/A_SYNTHETIC_DATA | HOLD | NO | 合成数据零信号；真实 Wind 数据未到位 | Wind 数据接入后重测 |
| FACTOR-002 | F20_attention_weight / 注意力权重因子 | N/A_SYNTHETIC_DATA | HOLD | NO | 合成数据零信号；真实 Wind 数据未到位 | Wind 数据接入后重测 |
| FACTOR-003 | CF003_speculation_weight / 投机持仓权重因子 | N/A_SYNTHETIC_DATA | HOLD | NO | 合成数据零信号；真实 Wind 数据未到位 | Wind 数据接入后重测 |
| FACTOR-004 | G1_IC_threshold / G1 IC 入场阈值因子 | NO_LEAKAGE_EVIDENCE | CONDITIONAL_PASS | NO | 无泄露证据；G1 阈值稳定性为条件项 | IC 稳定性与多窗口阈值验证 |
| FACTOR-005 | G3_ICIR_threshold / G3 ICIR 稳定性阈值因子 | NO_LEAKAGE_EVIDENCE | HOLD | NO | ICIR 指标定义与跨窗口符号稳定性未达准入门槛 | ICIR 定义重设计并验证 |
| FACTOR-006 | G7_leakage_ratio / G7 泄漏率因子 | FALSE_ALARM_MITIGATED | CONDITIONAL_PASS | NO | 泄漏边界误报已由 WL-001~WL-014 治理；LOCK-01=0.005 匹配 | 真实数据下复核 G7 边界 |
| FACTOR-007 | SchemeD_frozen_weights / SchemeD 冻结权重合成因子 | NO_LEAKAGE_EVIDENCE | CONDITIONAL_PASS | NO | 无泄露证据；多窗口不稳定为条件项 | 35~100 日窗口稳定性验证 |

**准入统计**：

| 判定 | 数量 | 因子 |
|---|---:|---|
| PASS | 0 | 无 |
| CONDITIONAL_PASS | 3 | FACTOR-004, FACTOR-006, FACTOR-007 |
| HOLD | 4 | FACTOR-001, FACTOR-002, FACTOR-003, FACTOR-005 |
| REJECT | 0 | 无 |
| PRODUCTION_RELEASE_ALLOWED | 0 | 无 |

**正式裁决**: 当前材料只支持条件性准入记录，不支持任何因子进入生产回测、灰度发布、Wind 实盘数据拉取或交易触发。

---

## 4. 因子级条件跟踪 `WL-A*` 分配

| Tracking ID | 对应因子 | 条件类型 | 当前状态 | 是否放行 | 解除条件 |
|---|---|---|---|---|---|
| WL-A001 | FACTOR-001 | SYNTHETIC_DATA_ZERO_SIGNAL | ACTIVE_HOLD | NO | Wind 真实数据接入 + 重测通过 |
| WL-A002 | FACTOR-002 | SYNTHETIC_DATA_ZERO_SIGNAL | ACTIVE_HOLD | NO | Wind 真实数据接入 + 重测通过 |
| WL-A003 | FACTOR-003 | SYNTHETIC_DATA_ZERO_SIGNAL | ACTIVE_HOLD | NO | Wind 真实数据接入 + 重测通过 |
| WL-A004 | FACTOR-004 | THRESHOLD_STABILITY_DEFECT | ACTIVE_CONDITIONAL | NO | IC 稳定性验证通过 + 多窗口阈值验证 |
| WL-A005 | FACTOR-005 | ICIR_DEFINITION_REDESIGN_REQUIRED | ACTIVE_HOLD | NO | ICIR 指标重设计并验证 |
| WL-A006 | FACTOR-006 | G7_LEAKAGE_BOUNDARY_FALSE_ALARM | ACTIVE_CONDITIONAL | NO | 真实数据下 G7 边界复核 |
| WL-A007 | FACTOR-007 | MULTI_WINDOW_INSTABILITY | ACTIVE_CONDITIONAL | NO | 35~100 日窗口稳定性验证 |

---

## 5. WL-006~WL-014 白名单正式审批结论

### 5.1 审批结果

| ID | 名称 | 覆盖范围 | 命中覆盖 | 正式审批 |
|---|---|---|---:|---|
| WL-006 | BFILL_PREPROCESSING | 数据预处理阶段 bfill 缺失值填充，非因子值计算 | 2 | APPROVED |
| WL-007 | SHIFT_DIAGNOSTIC_METRIC | 诊断检测用 shift(-1)，非因子值生成 | 10 | APPROVED |
| WL-008 | DOC_PSEUDOCODE_UNEXECUTABLE | Markdown 文档代码块内伪代码，不可执行 | 1 | APPROVED |
| WL-009 | ILOCS_LAYER_METRIC | 分层收益指标 iloc 提取，非因子值生成 | 2 | APPROVED |
| WL-010 | SCAFFOLD_WIND_NOTIMPLEMENTED | Wind API 脚手架占位函数，未调用 | 15 | APPROVED |
| WL-011 | UTIL_TRADINGCALENDAR | 交易日历生成工具函数，不参与因子计算 | 3 | APPROVED |
| WL-012 | DOC_COMMENT_PARAM | 文档注释 / Docstring 参数描述 | 3 | APPROVED |
| WL-013 | SENSITIVITY_IC_COMPUTE | 敏感性测试 IC 指标计算中的 shift(-1) | 1 | APPROVED |
| WL-014 | STRESS_G7_COMPUTE | 阈值压力测试 G7 / 复合 IC 计算中的 shift(-1) | 2 | APPROVED |
| **合计** | — | — | **42** | **9/9 APPROVED** |

### 5.2 白名单生效边界

1. WL-006~WL-014 仅用于代码层泄漏扫描器误报分类。
2. 本审批不改变因子准入状态，不将任何 HOLD 因子转为 PASS。
3. 本审批不解除合成数据、阈值稳定性、ICIR 定义、多窗口稳定性等因子级阻断。
4. 本审批不支持 Git push、Release Permit、Gate 打开或 Wind API 调用。

---

## 6. 风险与治理裁决

| 风险 / 不变量 | 裁决 |
|---|---|
| 合成数据零信号 | 高风险；FACTOR-001/002/003 维持 HOLD |
| G1 阈值稳定性 | 高风险；FACTOR-004 仅 CONDITIONAL_PASS |
| G3 ICIR 定义 | 高风险；FACTOR-005 维持 HOLD |
| G7 泄漏边界误报 | 已治理；FACTOR-006 仅 CONDITIONAL_PASS |
| 多窗口不稳定 | 中高风险；FACTOR-007 仅 CONDITIONAL_PASS |
| 文档缺口 | 已关闭；核心四文档齐备 |
| GATE | 维持 `CLOSED/HOLD` |
| Release Permit | 维持 `NOT_ISSUED` |
| Wind API | 调用数 `0` |
| 回测执行 | `false` |
| P49/P53 基线 | 未修改 |
| 审计账本 | 未修改 |
| Git push | 未执行 |
| 自审批 | `0` |

---

## 7. Gate 放行前置条件评估

| # | 前置条件 | 当前状态 | 是否满足 |
|---:|---|---|---|
| 1 | G7 正式裁决报告生成 | DONE | YES |
| 2 | 核心四文档齐备 | 4/4 PRESENT | YES |
| 3 | SHA256 台账归档 | DONE | YES |
| 4 | DSHA CRITICAL 异议关闭 | 2/2 CLOSED | YES |
| 5 | WL-006~WL-014 审批 | 9/9 APPROVED | YES |
| 6 | 7 因子准入矩阵完成 | DONE | YES |
| 7 | 调度确认正式报告 | PENDING | NO |
| 8 | Release Permit 签发 | NOT_ISSUED | NO |
| 9 | GATE 打开 | CLOSED/HOLD | NO |
| 10 | Wind 凭证配置与调用授权 | NOT_CONFIGURED / 0 calls | NO |
| 11 | 灰度发布授权 | NOT_ISSUED | NO |

**评估结论**：材料层与文档层条件已满足；运行层与授权层条件未满足。G7 正式报告可归档，但不得自动放行。

---

## 8. Release Permit 签发预案（待调度确认）

### 8.1 签发前必须等待

1. 调度确认接收 `G7_FACTOR_ADJUDICATION_REPORT.md`。
2. 调度确认接受 7 因子矩阵：0 PASS / 3 CONDITIONAL_PASS / 4 HOLD。
3. 调度确认接受 WL-006~WL-014 代码层白名单 9/9 APPROVED。
4. 调度确认接受方案 A 编号隔离规则。
5. 调度确认是否进入灰度许可路径；未确认前不得签发。

### 8.2 签发预案，但当前不执行

| 步骤 | 动作 | 当前状态 |
|---:|---|---|
| 1 | 确认调度授权 | PENDING |
| 2 | 生成 `P49_RELEASE_PERMIT` 草案 | PREPARED_ONLY |
| 3 | 校验 P49/P53 基线未修改 | READY |
| 4 | 校验审计账本未修改 | READY |
| 5 | 将 GATE 从 CLOSED/HOLD 调整为 OPEN | NOT_EXECUTED |
| 6 | 允许 Wind API 凭证配置 / 调用 | NOT_EXECUTED |
| 7 | 启动灰度回测 | NOT_EXECUTED |

**当前决定**：Release Permit 签发预案已准备，但因调度未确认，许可状态保持 `NOT_ISSUED`，GATE 保持 `CLOSED/HOLD`。

---

## 9. 签署栏

| 角色 | 签名 | 时间 |
|---|---|---|
| DSHC 裁决 | DSHC-P66 | 2026-10-16 GMT+8 |
| DSHA 审阅关闭 | DSHA-P54 | 2026-10-16 GMT+8 |
| 调度确认 | PENDING | PENDING |
| Release Permit | NOT_ISSUED | NOT_ISSUED |

---

> **最终声明**：本报告正式裁决 7 因子准入矩阵与 WL-006~WL-014 代码层白名单，但不签发 Release Permit，不打开 GATE，不执行 git push，不修改 P49/P53 基线，不修改审计账本。正式放行必须等待调度确认指令。
