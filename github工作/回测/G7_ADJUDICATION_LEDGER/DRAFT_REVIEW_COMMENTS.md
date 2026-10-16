# G7_FACTOR_ADJUDICATION_DRAFT.md · 条件草稿审阅意见

> **审阅人**: DSHA-P54  
> **审阅时间**: 2026-10-16 GMT+8  
> **审阅对象**: `G7_FACTOR_ADJUDICATION_DRAFT.md`  
> **文档 ID**: DSHA-P54-工单-A-工单-A-G7-DRAFT-REVIEW-001  
> **GATE**: CLOSED/HOLD  
> **Wind API**: 0 调用  
> **分支**: PHASE48_BASELINE  
> **Release Permit**: NOT_ISSUED  

---

## 0. 审阅结论总览

| 审阅项 | 结果 | 严重级 |
|--------|------|--------|
| 缺失文档清单 | ❌ 有严重事实错误 | 🔴 CRITICAL |
| 7 因子初步判定 | ✅ 无异议 | — |
| WL006~WL014 白名单评估 | ❌ 存在根本性语义冲突 | 🔴 CRITICAL |
| P66_KB_SECOND_REVIEW_REPORT.md | ❌ 确认为缺失 | 🟡 HIGH |
| 风险汇总 | ✅ 无异议 | — |
| 治理不变量 | ✅ 无异议 | — |

**总评**: 条件草稿存在 **2 项 CRITICAL 级异议**，需在正式裁决前修正。

---

## 1. 缺失文档清单 · 事实核验

### 1.1 DSHC 草稿声明 (§1)

DSHC 草稿 §1 列明 **4 份文档全部缺失**:

| DSHC 声明缺失 | DSHA 实际交付状态 | 位置 | SHA256 |
|---|---|---|---|
| `P66_KB_SECOND_REVIEW_REPORT.md` | ❌ **确属缺失** | 未找到 | — |
| `poll39_main_audit_report.md` | ✅ **已交付** | `G7_ADJUDICATION_LEDGER/` | `B328A408B889D6CB...` |
| `poll39_factor_leakage_risk_appendix.md` | ✅ **已交付** | `G7_ADJUDICATION_LEDGER/` | `2E8377D02604C5DD...` |
| `FL01_FL02_manual_review.md` | ✅ **已交付** | `G7_ADJUDICATION_LEDGER/` | `EB8689D71B29F582...` |

### 1.2 核验证据

- 已交付文档均位于 `G7_ADJUDICATION_LEDGER/` 目录，SHA256 校验值见 `SHA256_CHECKSUMS.txt`。
- `G7_ADJUDICATION_PACKAGE_MANIFEST.json` 已记录 3/4 文档已复制、1/4 缺失。
- 审计事件 `DSHA-P54-工单-A-G7-ADJUDICATION-PACKAGE-001` (event #20-21) 已记录材料包交付。
- **唯一确属缺失**: `P66_KB_SECOND_REVIEW_REPORT.md` — 已确认工作空间不存在此文件（已搜索 `**/P66*` 及 `**/*SECOND*REVIEW*` 模式，未命中）。

### 1.3 ⚠️ CRITICAL 异议 #1: 缺失文档清单状态错误

> **问题**: DSHC 草稿将 4 份文档全部标记为"缺失"，但 DSHA 已于 2026-10-16 将其中 3 份交付至 `G7_ADJUDICATION_LEDGER/`，且附有 SHA256 校验值。DSHC 草稿生成时间 (2026-10-16 GMT+8) 与 DSHA 交付时间 (2026-10-16 13:03 GMT+8) 几乎同步，可能存在信息时序不同步。
>
> **影响**: 若按 DSHC 草稿执行，将导致已交付的 3 份文档被错误地视为缺失，重复要求补交，浪费裁决周期。
>
> **DSHA 建议**:
> 1. 更新 §1 缺失文档清单，将 3 份已交付文档状态改为 `DELIVERED + SHA256_VERIFIED`。
> 2. 仅保留 `P66_KB_SECOND_REVIEW_REPORT.md` 为真正的缺失项。
> 3. 在草稿中注明 DSHC 草稿生成时间早于 DSHA 交付时间，信息时序需对齐。

---

## 2. 7 因子初步裁决 · 逐项核对

### 2.1 核验对照表

| 因子 | DSHC 草稿 | KB 基线 (DSHA-P54) | 一致性 | 主要依据核验 |
|------|-----------|---------------------|--------|-------------|
| FACTOR-001 | HOLD | HOLD | ✅ | 合成数据零信号，真实 Wind 数据未到位 |
| FACTOR-002 | HOLD | HOLD | ✅ | 合成数据零信号，真实 Wind 数据未到位 |
| FACTOR-003 | HOLD | HOLD | ✅ | 合成数据零信号，真实 Wind 数据未到位 |
| FACTOR-004 | CONDITIONAL_PASS | CONDITIONAL_PASS | ✅ | G1 阈值稳定性缺陷，需真实数据验证 |
| FACTOR-005 | HOLD | HOLD | ✅ | ICIR 指标定义需重设计 |
| FACTOR-006 | CONDITIONAL_PASS | CONDITIONAL_PASS | ✅ | 泄漏边界误报风险；LOCK-01 匹配 |
| FACTOR-007 | CONDITIONAL_PASS | CONDITIONAL_PASS | ✅ | 多窗口不稳定；35-100 日窗口约束 |

### 2.2 核验结论

> ✅ **DSHA 确认**: 7 因子初步判定与 KB 基线 **完全一致** (4 HOLD / 3 CONDITIONAL_PASS)。
>
> - FACTOR-001/002/003 HOLD 理由充分：P49-SYNTHETIC-V1 数据下零信号，真实 Wind 数据未到位。
> - FACTOR-004/006/007 CONDITIONAL_PASS 条件合理：均有明确的技术缺陷或审计依赖项。
> - FACTOR-005 HOLD 理由充分：ICIR 指标定义问题为 KB 已知缺陷。
> - 草稿 §3 中"当前无任何因子满足正式生效放行条件"的结论**无异议**。

### 2.3 补充说明

以下补充信息供 DSHC 参考，不构成对草稿结论的修改：

1. **FACTOR-006**: Poll39 审计 (DSHD-P61) 已确认为 `PASS_CONDITIONAL`，7 因子代码级泄漏检查干净，FL-01/FL-02 全部 42 次命中经人工复核确认为 **0 DEFECT**。FACTOR-006 的泄漏边界误报风险已获实质性证据支持。
2. **FACTOR-004**: G1 阈值稳定性缺陷为已知条件项，非阻断性缺陷。CONDITIONAL_PASS 处理合理。
3. **FACTOR-007**: 35-100 日窗口约束为已知条件项，非阻断性缺陷。CONDITIONAL_PASS 处理合理。

---

## 3. WL006~WL014 白名单评估 · 语义冲突核验

### 3.1 ⚠️ CRITICAL 异议 #2: 白名单语义根本性冲突

DSHC 草稿 §5 的 WL006~WL014 定义与 DSHA 已交付的 `WL006_WL014_whitelist_draft.md` **存在根本性语义差异**。两者虽共享相同的 ID 编号 (WL006~WL014)，但指向完全不同的对象。

#### 对照表

| ID | DSHC 草稿定义 | DSHA 交付定义 | 冲突程度 |
|----|-------------|-------------|---------|
| WL006 | FACTOR-004 G1 阈值稳定性 | BFILL_PREPROCESSING (FL-01 × 2) | 🔴 完全冲突 |
| WL007 | FACTOR-005 ICIR 指标重设计 | SHIFT_DIAGNOSTIC_METRIC (FL-01 × 10) | 🔴 完全冲突 |
| WL008 | FACTOR-006 G7 泄漏边界 | DOC_PSEUDOCODE_UNEXECUTABLE (FL-01 × 1) | 🔴 完全冲突 |
| WL009 | FACTOR-007 多窗口稳定性 | ILOCS_LAYER_METRIC (FL-02 × 2) | 🔴 完全冲突 |
| WL010 | FACTOR-001/002/003 真实数据验证 | SCAFFOLD_WIND_NOTIMPLEMENTED (FL-02 × 15) | 🔴 完全冲突 |
| WL011 | DSHC KB 二次验收 | UTIL_TRADINGCALENDAR (FL-02 × 3) | 🔴 完全冲突 |
| WL012 | DSHD Poll39 主审计 | DOC_COMMENT_PARAM (FL-02 × 3) | 🔴 完全冲突 |
| WL013 | 泄漏风险附录 | SENSITIVITY_IC_COMPUTE (FL-01 × 1) | 🔴 完全冲突 |
| WL014 | FL01/FL02 人工复核 | STRESS_G7_COMPUTE (FL-01 × 2) | 🔴 完全冲突 |

#### 语义差异分析

**DSHC 草稿语义**: WL006~WL014 被定义为 **因子级问题白名单**，每一项对应一个因子的特定风险或待办事项。本质是"因子放行条件跟踪表"。

**DSHA 交付语义**: WL006~WL014 被定义为 **代码层泄漏扫描白名单**，每一项对应 FL-01/FL-02 扫描中某一类假阳性命中的白名单归类。本质是"代码扫描误报分类表"。

**根本性差异**:
- DSHC 的 WL006~WL014 粒度为 **因子级** (一个因子对应一个或零个条目)
- DSHA 的 WL006~WL014 粒度为 **代码层** (一个代码模式对应一个条目，可覆盖多次命中)
- 两者不可互通，也不应混用同一编号空间

### 3.2 冲突影响

> **问题**: 若按 DSHC 草稿执行，将导致 WL006~WL014 编号空间出现歧义——同一编号指向两个完全不同含义的白名单条目，引发审批混乱。
>
> **影响**:
> 1. DSHC 逐条审批 WL006~WL014 时，审批对象不明确（因子级还是代码级）。
> 2. 已交付的 `WL006_WL014_whitelist_draft.md` 中 9 个条目的审批状态将无法被正确引用。
> 3. 正式裁决报告中的白名单部分可能出现编号冲突。

### 3.3 DSHA 建议

DSHA 提出以下 **3 种方案**供 DSHC 选择:

#### 方案 A: 编号空间分离 (推荐)

| 范围 | 用途 | 状态 |
|------|------|------|
| WL-001 ~ WL-005 | 现有白名单 (已生效) | 保留 |
| WL-006 ~ WL-014 | **代码层泄漏扫描白名单** (FL-01/FL-02 分类) | DSHA 已交付，待审批 |
| WL-A001 ~ WL-A00N | **因子级放行条件跟踪** (DSHC 草稿原意) | 需 DSHC 新建 |

**优点**: 语义清晰，编号空间不冲突，双方职责明确  
**缺点**: 需 DSHC 重新定义因子级白名单编号

#### 方案 B: 统一采用代码层白名单

| 范围 | 用途 |
|------|------|
| WL-001 ~ WL-005 | 现有白名单 (已生效) |
| WL-006 ~ WL-014 | 代码层泄漏扫描白名单 (DSHA 已交付) |

因子级放行条件跟踪改用其他机制 (如 G7 裁决报告附录)，不占用白名单编号。

**优点**: 减少编号总量，利用现有交付物  
**缺点**: 因子级跟踪需要另建机制

#### 方案 C: 统一采用因子级白名单

| 范围 | 用途 |
|------|------|
| WL-001 ~ WL-005 | 现有白名单 (已生效) |
| WL-006 ~ WL-014 | 因子级放行条件跟踪 (DSHC 草稿定义) |

代码层泄漏扫描白名单改用 FL-006 ~ FL-014 或其他命名空间。

**优点**: 保留 DSHC 草稿结构  
**缺点**: 需 DSHA 重新编号并重新交付 WL 文档

#### DSHA 推荐: 方案 A

**理由**:
1. 保留 DSHA 已交付的 WL-006~WL-014 白名单文档完整性 (42/42 命中 100% 覆盖)。
2. 保留 DSHC 草稿中因子级跟踪的语义完整性。
3. 两个编号空间各司其职，避免审批混淆。
4. WL-A001 等新编号空间对 DSHC 草稿改动最小 (仅替换 ID 前缀)。

---

## 4. P66_KB_SECOND_REVIEW_REPORT.md · 缺失确认

### 4.1 搜索记录

| 搜索模式 | 结果 |
|----------|------|
| `**/P66*SECOND*REVIEW*` | ❌ 未找到 |
| `**/P66*` | 命中 10 个文件，均不含 SECOND_REVIEW |
| 全局文本搜索 | ❌ 未找到任何匹配 |

### 4.2 相关现有文件

工作空间中存在 `P66_KB_INTEGRATION_ACCEPT_SUMMARY.md`，但该文件是 **知识库静态站点接入验收摘要** (P66)，非"知识库二次验收正式报告" (SECOND_REVIEW)。

| 文件 | 内容 | 是否等同 SECOND_REVIEW |
|------|------|----------------------|
| `P66_KB_INTEGRATION_ACCEPT_SUMMARY.md` | 知识库 GitHub Pages 接入验收 (PASS) | ❌ 不等 |
| `P66_FACTOR_VERSION_AUDIT_TEST_REPORT.json` | 因子版本审计 8 组测试 | ❌ 不等 |
| `P66_FULL_SITE_LINK_VERIFICATION_REPORT.json` | 全站链接校验 | ❌ 不等 |

### 4.3 DSHA 正式申请

> **申请对象**: DSHC  
> **申请内容**: 请提供 `P66_KB_SECOND_REVIEW_REPORT.md` 原始文件及 SHA256 校验值  
> **申请原因**: 该文件为 G7 正式裁决的 4 项必备文档之一 (DSHC 草稿 §1)  
> **当前状态**: 工作空间不存在此文件，DSHA 无法自行生成  
> **建议**: 若 DSHC 已有该报告但未交付至工作空间，请提供文件路径；若尚未生成，请安排生成  
> **替代方案**: 若 P66_KB_INTEGRATION_ACCEPT_SUMMARY.md 可作为 SECOND_REVIEW 的替代，请 DSHC 明确指定

---

## 5. 风险汇总 · 核验

### 5.1 DSHC 草稿 §4 核验

| 风险项 | DSHC 草稿级别 | DSHA 核验 |
|--------|-------------|-----------|
| 合成数据零信号 | 高 | ✅ 确认 — P49-SYNTHETIC-V1 下 FACTOR-001/002/003 IC=0.0 |
| 阈值稳定性缺陷 | 高 | ✅ 确认 — FACTOR-004 G1 阈值稳定性为已知条件项 |
| 泄漏边界误报 | 高 | ✅ 确认 — Poll39 审计 + FL01/FL02 人工复核已覆盖，0 DEFECT |
| 多窗口不稳定 | 中高 | ✅ 确认 — FACTOR-007 35-100 日窗口约束为已知条件项 |
| 文档缺口 | 高 | ⚠️ 部分修正 — 实际仅缺 1 份 (P66_KB_SECOND_REVIEW_REPORT.md)，非 4 份 |
| GATE 解除风险 | 高 | ✅ 确认 — 草稿阶段禁止解除 |

### 5.2 补充说明

- 泄漏边界误报风险 (FACTOR-006) 已获得实质证据支持：Poll39 审计 7 因子代码干净 + FL-01/FL-02 全部 42 次命中 0 DEFECT。风险级别可考虑从"高"调整为"中"。
- 文档缺口风险范围缩小：实际仅缺 1 份文档，而非 DSHC 草稿声称的 4 份。

---

## 6. 治理不变量 · 核验

| 不变量 | DSHC 草稿 | DSHA 核验 | 一致 |
|--------|-----------|-----------|------|
| Gate | CLOSED/HOLD | CLOSED/HOLD | ✅ |
| Wind API Calls | 0 | 0 | ✅ |
| Release Permit | NOT_ISSUED | NOT_ISSUED | ✅ |
| P49/P53 基线 | 未修改 | 未修改 | ✅ |
| 审计账本 | 未修改 | 未修改 | ✅ |
| 裁决生效性 | 非正式 | 非正式 | ✅ |

> ✅ **DSHA 确认**: 治理不变量全部一致，无异议。

---

## 7. 附录 · DSHC 草稿其他核验点

### 7.1 草稿 §6 结论

> "7 因子中，FACTOR-004/006/007 仅可获得条件通过草稿，其余因子维持 HOLD。"

**DSHA 确认**: ✅ 与 KB 基线一致，无异议。

### 7.2 草稿 §2 当前状态

> "Gate: CLOSED/HOLD | Wind API: 0 | Release Permit: NOT_ISSUED"

**DSHA 确认**: ✅ 全部一致，无异议。

### 7.3 草稿 §7 交付与审阅

> "草稿提交对象：调度、DSHA"

**DSHA 确认**: ✅ 本审阅意见即为对草稿的正式审阅回复。

---

## 8. 汇总 · DSHA 对 DSHC 草稿的意见

| # | 事项 | 严重级 | DSHA 意见 | 需 DSHC 行动 |
|---|------|--------|-----------|-------------|
| 1 | 缺失文档清单状态 | 🔴 CRITICAL | 3/4 文档已交付，仅 1/4 缺失 | 更新 §1 状态 |
| 2 | WL006~WL014 语义冲突 | 🔴 CRITICAL | 因子级 vs 代码级，根本性冲突 | 选择编号方案 (推荐方案 A) |
| 3 | P66_KB_SECOND_REVIEW_REPORT.md | 🟡 HIGH | 确认缺失，正式申请获取 | 提供文件或明确替代 |
| 4 | 7 因子初步判定 | ✅ | 完全一致，无异议 | 无需行动 |
| 5 | 风险汇总 | ✅ | 基本一致，泄漏风险可调低 | 可选调整 |
| 6 | 治理不变量 | ✅ | 全部一致，无异议 | 无需行动 |

---

## 9. 下一步行动建议

### DSHA 待办 (当前执行)
1. ✅ 本审阅意见已生成
2. ⏳ 向 DSHC 正式申请 `P66_KB_SECOND_REVIEW_REPORT.md`
3. ⏳ 接收文件后更新 `G7_ADJUDICATION_PACKAGE_MANIFEST.json` 和 `SHA256_CHECKSUMS.txt`
4. ⏳ 追加审计事件，更新 KB 快照至 v1.7.0
5. ⏳ 待命等待正式 G7 裁决

### DSHC 待办 (需确认)
1. 修正 §1 缺失文档清单 (3/4 已交付)
2. 回复 WL006~WL014 编号方案选择 (方案 A/B/C)
3. 提供 `P66_KB_SECOND_REVIEW_REPORT.md` 或明确替代方案
4. 确认 7 因子初步判定无异议后，推进正式裁决

---

> **DSHA-P54 审阅签名**: 2026-10-16 GMT+8  
> **审阅结论**: 条件草稿存在 **2 项 CRITICAL 异议** (缺失文档清单状态 + 白名单语义冲突)，需修正后方可进入正式裁决。7 因子判定、风险汇总、治理不变量均无异议。  
> **治理不变量**: GATE=CLOSED/HOLD ✅ | Wind=0 ✅ | Release Permit=NOT_ISSUED ✅ | P53 未修改 ✅ | 上游写入=0 ✅ | 因子公式固定 ✅
