# G7 条件放行临时凭证

> **凭证 ID**: DSHC-P66-G7-CONDITIONAL-RELEASE-001  
> **关联正式裁决**: `G7_FACTOR_ADJUDICATION_REPORT.md`  
> **关联台账**: `G7_ADJUDICATION_PACKAGE_MANIFEST.json`  
> **生成时间**: 2026-10-16 GMT+8  
> **分支**: PHASE48_BASELINE  
> **Global GATE**: CLOSED/HOLD  
> **Release Permit**: NOT_ISSUED  
> **Git push**: NOT_EXECUTED  
> **用途声明**: 本文件仅用于受限灰度条件放行，不构成全局 Release Permit，不授权任何 HOLD 因子计算、数据读取、Wind 拉取或回测触发。

---

## 1. 条件放行范围

| 项目 | 值 |
|---|---|
| 条件放行状态 | RESTRICTED_GRAY_CONDITIONAL_PASS_ONLY |
| 可进入回测管线的因子数 | 3 |
| 因子清单 | FACTOR-004 / FACTOR-006 / FACTOR-007 |
| 禁止触发因子数 | 4 |
| 禁止触发因子清单 | FACTOR-001 / FACTOR-002 / FACTOR-003 / FACTOR-005 |
| 回测管线允许范围 | 仅限受限灰度链路 |
| 全局 GATE | CLOSED/HOLD |
| 全局 Release Permit | NOT_ISSUED |

## 2. 条件边界

### 2.1 允许事项

1. 仅允许 3 个 `CONDITIONAL_PASS` 因子进入受限灰度回测管线。
2. 仅允许在已登记的条件约束下运行验证性回测。
3. 仅允许记录与审计，不允许扩展到其他因子。
4. 仅允许把结果作为灰度前置条件验证依据。

### 2.2 禁止事项

1. 禁止任何 HOLD 因子执行计算、数据读取、Wind 拉取或回测触发。
2. 禁止把本凭证解读为生产放行、灰度全量放行或全局放行。
3. 禁止修改 P49/P53 基线。
4. 禁止修改不可变审计账本中的既有正式裁决与基线记录。
5. 禁止触发 `git push`。

### 2.3 撤销条件

出现任一情况，立即撤销本临时凭证并关闭条件通道：

1. 触及 HOLD 因子计算或数据读取。
2. 出现新的代码层泄漏证据。
3. 灰度链路日志出现越界访问或越权写入。
4. 因子结果超出预设约束边界。
5. 调度或 DSHD 审计发现异常并要求暂停。

---

## 3. 约束矩阵

| 因子ID | 因子名称 | 状态 | 约束条件 | 允许进入受限灰度 |
|---|---|---|---|---|
| FACTOR-004 | G1 IC 入场阈值因子 | CONDITIONAL_PASS | IC 稳定性验证通过 + 多窗口阈值验证 | YES |
| FACTOR-006 | G7 泄漏率因子 | CONDITIONAL_PASS | 真实数据下复核 G7 边界 | YES |
| FACTOR-007 | SchemeD 冻结权重合成因子 | CONDITIONAL_PASS | 35~100 日窗口稳定性验证 | YES |
| FACTOR-001 | F19 热钱权重因子 | HOLD | 合成数据零信号 | NO |
| FACTOR-002 | F20 注意力权重因子 | HOLD | 合成数据零信号 | NO |
| FACTOR-003 | CF003 投机持仓权重因子 | HOLD | 合成数据零信号 | NO |
| FACTOR-005 | G3 ICIR 稳定性阈值因子 | HOLD | ICIR 指标重设计并验证 | NO |

---

## 4. 签署与约束

| 角色 | 签名 | 说明 |
|---|---|---|
| 凭证签发 | DSHC-P66 | 仅限条件灰度 |
| 审计确认 | DSHA/DSHD | 仅允许 3 个因子进入受限链路 |
| 全局 Release Permit | NOT_ISSUED | 不变 |
| 全局 GATE | CLOSED/HOLD | 不变 |

---

> **最终声明**: 本凭证是临时、有限、可撤销的条件放行凭证；不代表生产放行，不改变全局 Gate，不签发完整 Release Permit。
