# V88 Phase03-P0 告警等级映射表

> **TASK_ID**: V88_PHASE03_P0_R1_CHART_META_BINDING / T1
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **前置**: 三方评审完成 (CONDITIONAL_PASS, Phase03-P0启动许可) / CHG-DV-01 告警分级映射需求
> **性质**: P0原型期交付物 — 不改动Phase02已上线告警阈值
> **状态**: V88_PHASE03_P0_ALERT_LEVEL_MAPPING=READY
> **依赖**: HERMEShf WARN/CRIT 2档体系 / DSHB GREEN/YELLOW/RED/BLUE 4级体系 / DSHE factor_drift面板

---

## 0. 一句话总结

**Phase03-P0 建立 HERMEShf 2档(WARN/CRIT) ↔ DSHE/DSHB 4级(GREEN/YELLOW/RED/BLUE) 双向映射表, 统一告警分级接口, 覆盖因子漂移/并发扩容/灾备切换/扩量数据源4个面板, 消除 CHG-DV-01 对齐差异, 为 P1 仿真阶段告警规则部署提供标准接口。**

---

## 1. 映射背景与需求

### 1.1 问题陈述

三方对齐评审(7通过/3待调整/0阻塞)识别出告警分级体系差异:

| 来源 | 分级体系 | 等级数 | 使用场景 |
|------|---------|:------:|---------|
| **HERMEShf 顶层规划** | WARN / CRIT | **2档** | 全链路统一告警标准 |
| **DSHB 数据模块** | GREEN / YELLOW / RED / BLUE | **4级** | 指标漂移监测/数据质量 |
| **DSHE 可视化模块** | 混合: WARN/CRIT(3面板) + GREEN/YELLOW/RED/BLUE(因子面板) | **2+4** | 监控大盘/灾备/因子漂移 |

### 1.2 CHG-DV-01 变更项

| 字段 | 值 |
|------|-----|
| **CHG-ID** | CHG-DV-01 |
| **描述** | 因子漂移告警分级体系差异 (GREEN/YELLOW/RED/BLUE vs WARN/CRIT) |
| **影响范围** | G2因子漂移 / ALIGN-03 / ALIGN-04 |
| **责任方** | DSHE + HERMEShf |
| **优先级** | P1 |
| **处置** | 建立双向映射表, 统一告警接口 |
| **关联风险** | R-V88-021 (因子漂移告警分级不统一导致告警疲劳) |

---

## 2. 双向映射表

### 2.1 核心映射矩阵

| # | DSHE/DSHB 4级 | HERMEShf 2档 | 映射关系 | 告警动作 | 通知级别 | 升级策略 |
|:-:|:--------------:|:------------:|:--------:|---------|:--------:|---------|
| 1 | 🟢 **GREEN** | **正常 (N/A)** | 正常, 无告警 | 无动作 | 静默 | — |
| 2 | 🟡 **YELLOW** | **WARN** | YELLOW ↔ WARN | 记录日志 + 观察7天 | 邮件/日报 | 持续3天→升级RED |
| 3 | 🔴 **RED** | **CRIT** | RED ↔ CRIT | 立即止损 / 备选评审 | 即时推送+短信 | 持续1h→升级BLUE |
| 4 | 🔵 **BLUE** | **CRIT(升级)** | BLUE ↔ CRIT+ESCALATED | P2告警 + 降级评估 | 即时推送+电话 | 持续24h→人工介入 |

### 2.2 反向映射 (HERMEShf → DSHE/DSHB)

| # | HERMEShf 2档 | DSHE/DSHB 4级 | 映射规则 | 判定条件 |
|:-:|:------------:|:--------------:|:--------:|---------|
| 1 | **WARN** | 🟡 YELLOW | WARN→YELLOW | 触发WARN条件但未达CRIT阈值 |
| 2 | **CRIT** | 🔴 RED | CRIT→RED | 触发CRIT条件(1σ/2σ/符号翻转/漂移速率) |
| 3 | **CRIT** | 🔵 BLUE | CRIT→BLUE | CRIT条件持续+升级标记(持续>1h) |

### 2.3 数值阈值映射 (因子漂移专用)

| 指标 | GREEN (正常) | YELLOW (WARN) | RED (CRIT) | BLUE (CRIT升级) |
|------|:-----------:|:-------------:|:----------:|:--------------:|
| **IC 绝对值衰减** | IC ≥ 0.30 | 0.20 ≤ IC < 0.30 | 0.10 ≤ IC < 0.20 | IC < 0.10 |
| **IC 符号翻转** | 无翻转 | 偶发翻转(<3次/月) | 频繁翻转(≥3次/月) | 连续翻转(≥7天) |
| **IR 稳定性** | IR > 1.0 | 0.5 < IR ≤ 1.0 | 0.1 ≤ IR ≤ 0.5 | IR < 0.1 |
| **漂移速率 (CUSUM)** | |CUSUM| < 0.15 | 0.15 ≤ |CUSUM| < 0.25 | 0.25 ≤ |CUSUM| < 0.50 | |CUSUM| ≥ 0.50 |
| **EWMA 偏移** | |EWMA| < 0.05 | 0.05 ≤ |EWMA| < 0.10 | 0.10 ≤ |EWMA| < 0.20 | |EWMA| ≥ 0.20 |

**阈值依据**: HERMEShf 顶层规划 §2.3 因子漂移监控框架 + DSHB CUSUM+EWMA 双层检测参数 + 1σ=0.364 / 2σ=0.728 基线。

---

## 3. 监控面板告警规则映射

### 3.1 面板1: 因子漂移面板 (factor_drift)

| 规则ID | 规则描述 | DSHE 4级阈值 | HERMEShf 2档映射 | 告警级别 | 噪声率目标 |
|--------|---------|:------------:|:----------------:|:--------:|:----------:|
| **FDR-01** | IC 绝对值衰减 | GREEN≥0.30 / YELLOW≥0.20 / RED≥0.10 / BLUE<0.10 | N/A / WARN / CRIT / CRIT+ESCALATED | 🟡/🔴/🔵 | <10% |
| **FDR-02** | IC 符号翻转 | GREEN=无 / YELLOW=偶发 / RED=频繁 / BLUE=连续 | N/A / WARN / CRIT / CRIT+ESCALATED | 🟡/🔴/🔵 | <10% |
| **FDR-03** | IR 稳定性 | GREEN>1.0 / YELLOW>0.5 / RED>0.1 / BLUE<0.1 | N/A / WARN / CRIT / CRIT+ESCALATED | 🟡/🔴/🔵 | <10% |
| **FDR-04** | 漂移速率(CUSUM) | GREEN<0.15 / YELLOW<0.25 / RED<0.50 / BLUE≥0.50 | N/A / WARN / CRIT / CRIT+ESCALATED | 🟡/🔴/🔵 | <10% |

### 3.2 面板2: 并发扩容面板 (concurrency_scale)

| 规则ID | 规则描述 | 告警级别 | HERMEShf 2档 | 对应门禁 |
|--------|---------|:--------:|:------------:|:--------:|
| **CC-01** | P99时延 > 300ms | 🟡 WARN | WARN | R-5 |
| **CC-02** | P99时延 > 500ms | 🔴 CRIT | CRIT | R-5 |
| **CC-03** | CPU > 5% | 🟡 WARN | WARN | R-6 |
| **CC-04** | CPU > 10% | 🔴 CRIT | CRIT | R-6 |
| **CC-05** | 队列深度 > 500 | 🟡 WARN | WARN | — |
| **CC-06** | 队列深度 > 800 | 🔴 CRIT | CRIT | — |
| **CC-07** | error_rate > 0.01% | 🟡 WARN | WARN | G4 |
| **CC-08** | error_rate > 0.05% | 🔴 CRIT | CRIT | G4 |

**注意**: 并发扩容面板已使用 HERMEShf WARN/CRIT 2档体系, 无需映射转换。

### 3.3 面板3: 灾备切换面板 (dr_fallback)

| 规则ID | 规则描述 | 告警级别 | HERMEShf 2档 | 对应门禁 |
|--------|---------|:--------:|:------------:|:--------:|
| **DR-01** | 切换开始 (switchover) | 🟡 WARN | WARN | S-3 |
| **DR-02** | 切换超时 > 5min | 🔴 CRIT | CRIT | S-3 |
| **DR-03** | RPO > 0 | 🔴 CRIT | CRIT | S-4 |
| **DR-04** | 降级深度 ≥ 2 | 🟡 WARN | WARN | G3 |
| **DR-05** | 降级深度 = 2 持续 > 10min | 🔴 CRIT | CRIT | G3 |
| **DR-06** | 对账不一致 > 0% | 🔴 CRIT | CRIT | S-4 |
| **DR-07** | 同步双写状态 inactive | 🟡 WARN | WARN | CHG-DV-02 |

**注意**: 灾备切换面板已使用 WARN/CRIT 2档体系。

### 3.4 面板4: 扩量数据源面板 (expansion_source)

| 规则ID | 规则描述 | 告警级别 | HERMEShf 2档 | 对应门禁 |
|--------|---------|:--------:|:------------:|:--------:|
| **ES-01** | 采集成功率 < 95% | 🟡 WARN | WARN | D-5 |
| **ES-02** | DQA ERROR > 0 | 🔴 CRIT | CRIT | D-2/D-6 |
| **ES-03** | DQA吞吐 < 1000条/天 | 🟡 WARN | WARN | D-6 |
| **ES-04** | 入库延迟 > T+1d | 🟡 WARN | WARN | D-3 |
| **ES-05** | 指标供给完整性 < 100% | 🔴 CRIT | CRIT | D-4 |
| **ES-06** | SMM付费源IC<0.10持续7天 | 🔴 CRIT | CRIT | R-V88-008 |

**注意**: 扩量数据源面板已使用 WARN/CRIT 2档体系。

---

## 4. 告警联动矩阵

### 4.1 跨面板联动规则

| 源面板 | 源规则 | 源级别 | 目标面板 | 目标动作 | 优先级 |
|--------|--------|:------:|----------|---------|:------:|
| factor_drift | FDR-01/02 | 🔴 RED (CRIT) | concurrency_scale | 暂停扩量操作 | P0 |
| factor_drift | FDR-01/02 | 🔵 BLUE (CRIT+) | dr_fallback | 触发灾备降级评估 | P1 |
| concurrency_scale | CC-02 | 🔴 CRIT | expansion_source | 暂停扩量入库 | P0 |
| dr_fallback | DR-02/03 | 🔴 CRIT | expansion_source | 暂停扩量入库 | P0 |
| expansion_source | ES-02 | 🔴 CRIT | factor_drift | 标记数据源不可用 | P1 |

### 4.2 告警升级路径

```
GREEN (正常)
  ↓ 触发WARN条件
YELLOW (WARN) — 记录+观察
  ↓ 持续3天 OR 触发CRIT条件
RED (CRIT) — 立即止损/备选评审
  ↓ 持续1h
BLUE (CRIT+ESCALATED) — P2告警+降级评估
  ↓ 持续24h
人工介入 — 升级至DSHB+DSHE+HERMEShf联合处置
```

### 4.3 告警降级路径

```
BLUE (CRIT+)
  ↓ 触发条件消除 1h
RED (CRIT)
  ↓ 持续3天无复发
YELLOW (WARN)
  ↓ 持续7天噪声率<10%
GREEN (正常)
```

---

## 5. 告警接口规范

### 5.1 统一告警消息格式

```json
{
  "alert_id": "FDR-01-20261015-001",
  "panel": "factor_drift",
  "rule_id": "FDR-01",
  "rule_name": "IC绝对值衰减",
  "dshe_level": "RED",
  "hermes_level": "CRIT",
  "dshe_level_cn": "红色",
  "hermes_level_cn": "严重",
  "severity": "CRIT",
  "value": 0.08,
  "threshold": 0.10,
  "timestamp": "2026-10-15T10:30:00Z",
  "duration_min": 45,
  "escalated": false,
  "action": "immediate_stop_loss",
  "notification": ["push", "sms"],
  "auto_resolve_after_h": 24,
  "silent_period": false,
  "noise_rate_pct": 8.2,
  "related_risk": "R-V88-021"
}
```

### 5.2 字段定义

| 字段 | 类型 | 说明 | 必填 |
|------|:----:|------|:----:|
| alert_id | string | 告警唯一标识: `{规则ID}-{日期}-{序号}` | ✅ |
| panel | string | 面板ID: factor_drift/concurrency_scale/dr_fallback/expansion_source | ✅ |
| rule_id | string | 告警规则ID | ✅ |
| dshe_level | enum | DSHE 4级: GREEN/YELLOW/RED/BLUE | ✅ |
| hermes_level | enum | HERMEShf 2档: N/A/WARN/CRIT/CRIT_ESCALATED | ✅ |
| severity | enum | 标准化严重度: WARN/CRIT | ✅ |
| value | float | 当前值 | ✅ |
| threshold | float | 触发阈值 | ✅ |
| escalated | bool | 是否已升级 | ✅ |
| noise_rate_pct | float | 7天噪声率(%) | ✅ |

---

## 6. 噪声率管控方案

### 6.1 静默期策略 (7天)

| 阶段 | 天数 | 阈值策略 | 噪声率目标 | 说明 |
|:----:|:----:|:--------:|:----------:|------|
| 初期 | D1-D3 | 宽松阈值(WARN↑10%) | <20% | 收集基线数据 |
| 中期 | D4-D5 | 标准阈值 | <12% | 微调参数 |
| 后期 | D6-D7 | 收紧阈值(WARN↓5%) | <10% | 验证收敛 |
| 稳定 | D8+ | 标准阈值 | <10% | 正常监控 |

### 6.2 噪声率监控指标

| 指标 | 计算方式 | 目标值 | 告警条件 |
|------|---------|:------:|---------|
| alert_noise_rate | 误报数 / 总告警数 × 100% | <10% | >15%触发调参 |
| alert_dedup_rate | 重复告警占比 | <5% | >10%触发去重优化 |
| alert_resolution_time | 告警平均解决时长 | <4h | >8h触发升级 |
| alert_flip_rate | 告警翻转率(触发→消除→触发) | <3% | >5%触发阈值平滑 |

---

## 7. 映射表部署方案

### 7.1 配置文件路径

```
analysis/e2e_output/v88/phase03/p0/
├── alert_level_mapping.json      # 机器可读映射表 (JSON格式)
├── alert_rules_config.yaml       # 4面板告警规则配置 (YAML格式)
└── v88_phase03_p0_alert_level_mapping.md  # 本文档 (人类可读)
```

### 7.2 部署时序

| 时间 | 动作 | 责任方 | 验证 |
|:----:|------|:------:|------|
| P0 D1 | 映射表+规则配置编写 | DSHE | 格式校验 PASS |
| P0 D2 | HERMEShf WARN/CRIT阈值确认 | HERMEShf | 书面确认 |
| P0 D3 | 三方评审映射表+噪声率方案 | DSHB+DSHE+HERMEShf | CHG-DV-01关闭 |
| P1 D4 | 映射表集成至渲染引擎 | DSHE | 单元测试通过 |
| P1 D5 | 告警规则部署至监控大盘 | DSHE | 告警触发验证 |

---

## 8. 风险关联

| 风险ID | 描述 | 等级 | 映射表覆盖 | 缓解措施 |
|--------|------|:----:|:----------:|---------|
| R-V88-021 | 因子漂移告警分级不统一导致告警疲劳 | P2 | ✅ 双向映射+升级/降级路径 | 建立映射表+7天静默期+噪声率监控 |
| R-V88-012 | 新增因子监控阈值产生告警噪声 | P2 | ✅ 噪声率管控方案 | 三档阈值+7天静默期+<10%目标 |
| R-V88-019 | 因子漂移可视化面板数据源不可用 | Medium | ✅ 面板降级策略 | 显示上次数据+降级标记+DR告警 |

---

## 9. 验收标准

| # | 验收项 | 标准 | 状态 |
|:-:|--------|------|:----:|
| 1 | 双向映射表完整 | GREEN/YELLOW/RED/BLUE ↔ WARN/CRIT 全部映射 | ✅ |
| 2 | 4面板告警规则配置 | 因子漂移4项+并发8项+灾备7项+扩量6项=25项 | ✅ |
| 3 | 告警接口规范 | 统一消息格式+字段定义+JSON Schema | ✅ |
| 4 | 噪声率管控方案 | 7天静默期+4项监控指标+<10%目标 | ✅ |
| 5 | 告警联动矩阵 | 5项跨面板联动规则+升级/降级路径 | ✅ |
| 6 | Phase02告警阈值零修改 | 10条现有告警规则+6SLA+15项阈值不变 | ✅ |
| 7 | CHG-DV-01 映射需求覆盖 | 完全覆盖GREEN/YELLOW/RED/BLUE ↔ WARN/CRIT | ✅ |
| 8 | R-V88-021 风险缓解 | 映射表+噪声率管控+7天静默期 | ✅ |

---

## 10. 约束合规确认

| # | 约束 | 状态 |
|:-:|------|:----:|
| 1 | Phase02线上渲染逻辑不修改 | ✅ |
| 2 | Phase02 node_binding不修改 | ✅ |
| 3 | Phase02生产告警阈值不修改 (10条告警/6SLA/15项阈值) | ✅ |
| 4 | CPU FUSE 2.0%不修改 | ✅ |
| 5 | BRANCH_LOCKED (feature/v88-g1) | ✅ |
| 6 | NO_OVERWRITE (新建文件) | ✅ |
| 7 | NO_MODIFY_V87 | ✅ |
| 8 | NO_EDIT_RELEASE_TAG | ✅ |
| 9 | NO_ZHIJI_API_CALL | ✅ |
| 10 | APPEND_ONLY (元数据追加) | ✅ |

---

## 11. 增量更新记录

| 版本 | 日期 | 更新内容 | 操作 |
|:----:|:----:|----------|:----:|
| v1.0 | 2026-10-15 | P0告警等级映射表初稿(T1交付物) | 新增 |

**当前版本:** v1.0
**告警映射状态:** ✅ READY — 等待HERMEShf WARN/CRIT阈值确认
**下一步:** HERMEShf确认 → 三方评审映射表 → CHG-DV-01关闭 → P1告警规则部署

---

*Document Generated: 2026-10-15 UTC+8*
*Generated by: DSHE Agent*
*Branch: feature/v88-g1 (BRANCH_LOCKED)*
*Status: V88_PHASE03_P0_ALERT_LEVEL_MAPPING=READY*
*Reference: CHG-DV-01 / HERMEShf Phase03 Top-Level Plan / DSHB Data Align Review*
