# FACTOR-007 窗口参数基线定义 · F007 Window Parameter Baseline

> **文档ID**: DSHA-P54-F007-PARAM-BASELINE-001
> **生成时间**: 2026-10-16 GMT+8
> **Agent**: DSHA-P54
> **Branch**: feature/v88-g1
> **GATE**: CLOSED/HOLD
> **Wind API Calls**: 0
> **声明**: 纯离线文档，消除 P49_factor_version_diff_report.md 中标注的 F007 窗口参数差异 (S1: 35~100d, S4: 60d固定)。

---

## 0. 问题背景

### 0.1 差异来源

| 来源 | 窗口参数 | 定义方式 |
|---|---|---|
| S1: G7_FACTOR_ADJUDICATION_REPORT.md | 35~100日 | 条件约束：35~100日窗口稳定性验证 |
| S4: wind_excel_automation.py | 60日 | 代码常量 `window_days: 60` |

### 0.2 差异性质

此差异为**可接受差异**——60日是基准值（baseline），35~100日是验证范围。代码当前仅使用基准值，多窗口验证应在数据拉取后执行。本文档正式定义此关系，消除歧义。

---

## 1. 基准值定义

### 1.1 基准窗口参数

| 参数 | 值 | 单位 | 定义 |
|---|---|---|---|
| window_days | **60** | 天 | 合成因子计算的标准滚动窗口 |
| 基准含义 | 单点固定值 | — | 代码中 `CONDITIONAL_FACTORS["FACTOR-007"]["window_days"] = 60` |
| 适用阶段 | 数据拉取阶段 + 因子计算阶段 | — | 当前唯一使用的窗口值 |

### 1.2 基准值代码引用

```python
# wind_excel_automation.py (行58-61)
CONDITIONAL_FACTORS["FACTOR-007"] = {
    ...
    "window_days": 60,  # ← 基准值
    ...
}
```

### 1.3 基准值与 G7_FACTOR_ADJUDICATION_REPORT.md 的关系

```
裁决报告条件约束: "35~100日窗口稳定性验证"
         ↓
代码实现:        window_days = 60 (基准值)
         ↓
验证要求:        使用 60 日基准值计算合成因子
                  然后在 35/60/80/100 日窗口下验证稳定性
         ↓
结论:            60 日 = 验证基准锚点，非验证范围的唯一值
```

---

## 2. 可调边界定义

### 2.1 验证窗口范围

| 窗口值 | 单位 | 用途 | 状态 |
|---|---|---|---|
| 35 | 天 | 验证下界 — 短窗口稳定性检验 | 待验证 |
| 60 | 天 | **基准值** — 代码当前使用值 | 基准锚点 |
| 80 | 天 | 验证上界内侧 — 长窗口稳定性检验 | 待验证 |
| 100 | 天 | 验证上界 — 极长窗口稳定性检验 | 待验证 |

### 2.2 边界定义表

| 维度 | 下界 | 基准值 | 上界 | 不可变 |
|---|---|---|---|---|
| window_days | 35 | **60** | 100 | 否（验证阶段可调） |
| 合成公式 | SchemeD | SchemeD | SchemeD | 是 |
| 权重冻结 | frozen | frozen | frozen | 是 |
| decay_factor | frozen | frozen | frozen | 是 |

### 2.3 边界外的不可变参数

| 参数 | 值 | 可变性 | 理由 |
|---|---|---|---|
| f19_weight | frozen | 不可变 | DSHC 锁定，SchemeD 权重冻结 |
| f20_weight | frozen | 不可变 | DSHC 锁定，SchemeD 权重冻结 |
| cf003_weight | frozen | 不可变 | DSHC 锁定，SchemeD 权重冻结 |
| decay_factor | frozen | 不可变 | DSHC 锁定，时间衰减冻结 |
| window_days | **60** | 验证阶段可调 | 唯一可调窗口参数 |

---

## 3. 漂移预警阈值

### 3.1 窗口参数漂移定义

窗口参数漂移指合成因子在不同窗口下计算结果的一致性偏差。

| 漂移类型 | 定义 | 预警阈值 | 严重阈值 |
|---|---|---|---|
| 排名相关性漂移 | 窗口间合成因子排名 Spearman 相关系数 | < 0.80 (WARNING) | < 0.60 (CRITICAL) |
| 方向一致性漂移 | 窗口间合成因子正负方向不一致的观测比例 | > 20% (WARNING) | > 40% (CRITICAL) |
| 分布形态漂移 | 窗口间合成因子分布 KS 检验 p 值 | < 0.10 (WARNING) | < 0.05 (CRITICAL) |
| 权重贡献漂移 | 窗口间 F19/F20/CF003 各权重贡献变化率 | > 15% (WARNING) | > 30% (CRITICAL) |
| IC 波动漂移 | 窗口间因子 IC 值的标准差 | > 2×基准IC_std (WARNING) | > 3×基准IC_std (CRITICAL) |

### 3.2 漂移预警响应

| 预警级别 | 触发条件 | 响应动作 |
|---|---|---|
| WARNING | 任一维度达到预警阈值 | 标记异常，记录日志，继续计算 |
| CRITICAL | 任一维度达到严重阈值 | 停止窗口扩展，升级 DSHC 审核 |
| ESCALATION | 连续3个窗口 WARNING | 暂停 F007 条件验证，等待人工判断 |

### 3.3 漂移记录模板

```json
{
  "drift_record": {
    "factor_id": "FACTOR-007",
    "window_days": 35,
    "drift_type": "ranking_correlation",
    "value": 0.72,
    "threshold_warning": 0.80,
    "threshold_critical": 0.60,
    "level": "WARNING",
    "timestamp": "<ISO-8601>",
    "action": "log_and_continue"
  }
}
```

---

## 4. 多窗口验证执行规范

### 4.1 验证窗口序列

| 序列 | 窗口值 | 顺序 | 验证内容 |
|---|---|---|---|
| 1 | 60 | 基准锚点 | 合成因子基准计算 |
| 2 | 35 | 下界 | 短窗口 vs 基准 漂移检验 |
| 3 | 80 | 上界内侧 | 长窗口 vs 基准 漂移检验 |
| 4 | 100 | 上界 | 极长窗口 vs 基准 漂移检验 |

### 4.2 验证通过标准

| 指标 | 通过阈值 | 验证窗口数 |
|---|---|---|
| 排名相关性 | Spearman ρ ≥ 0.80 | ≥ 3/4 窗口通过 |
| 方向一致性 | 不一致比例 ≤ 20% | ≥ 3/4 窗口通过 |
| IC 波动 | std < 2×基准IC_std | ≥ 3/4 窗口通过 |

**整体通过**: 3 项指标全部满足 ≥ 3/4 窗口通过。

### 4.3 验证失败处理

| 失败类型 | 处理方式 |
|---|---|
| 单指标失败 | 记录失败原因，标记该指标 CONDITIONAL_PASS 不满足 |
| 多指标失败 | 升级 DSHC 审核，暂停 F007 灰度 |
| 全部通过 | WL-A007 条件满足，标记 READY_FOR_GRAY |

---

## 5. 参数版本记录

| 版本 | 时间 | 窗口值 | 来源 | 备注 |
|---|---|---|---|---|
| v1.0 | 2026-10-16 | 60 (代码常量) | wind_excel_automation.py | 初始代码定义 |
| v1.1 | 2026-10-16 | 35~100 (验证范围) | G7_FACTOR_ADJUDICATION_REPORT.md | 裁决报告条件约束 |
| v2.0 | 2026-10-16 | 60 (基准锚点) + 35/80/100 (验证) | 本文档 | 正式定义基准与验证关系 |

---

## 6. 与其他文档的对应关系

| 文档 | 引用 | 一致性 |
|---|---|---|
| G7_FACTOR_ADJUDICATION_REPORT.md | 35~100日窗口稳定性验证 | ✅ 本文档扩展定义 |
| wind_excel_automation.py | window_days: 60 | ✅ 本文档确认为基准值 |
| P49_factor_doc_supplement.md | window_days: 60 (基准) / 35~100日 (验证范围) | ✅ 本文档正式定义 |
| P49_factor_version_diff_report.md | ⚠️ 可接受差异 | ✅ 本文档消除歧义 |
| P49_pre_gray_check.md | 条件跟踪 WL-A007 | ✅ 本文档定义验证方法 |

---

## 7. 结论

1. **60日** 正式定义为 F007 合成因子的**基准窗口锚点**。
2. **35~100日** 正式定义为**多窗口验证范围**，包含4个验证窗口: 35/60/80/100日。
3. **5项漂移预警阈值** 已定义：排名相关性、方向一致性、分布形态、权重贡献、IC波动。
4. **3级预警响应机制** 已定义：WARNING / CRITICAL / ESCALATION。
5. **参数差异已消除**：S1的35~100日和S4的60日关系已正式定义。
6. **本文档不修改任何代码**——当前代码使用 window_days=60 继续有效。

> **DSHA-P54 声明**: 本文档为纯离线分析产物，未调用任何 Wind API。
> 所有治理不变量保持：wind_api_calls=0, backtest_started=false, gate=CLOSED/HOLD, release_permit=NOT_ISSUED。

---

_生成时间: 2026-10-16 GMT+8 | Agent: DSHA-P54 | Branch: feature/v88-g1_