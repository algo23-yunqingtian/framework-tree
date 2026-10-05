# V86-RC2 灰度降级策略规范（更新版）

> **工单**: DSHE_V86_RC2_L2_PANEL_REAL_DEP_GRAY_DEP_READY / T3.5
> **分支**: `feature/v85-chart-template` @ `629ccb7`（前次提交）→ 本轮新增
> **编制方**: DSHE（L2 面板） | **协作方**: HERMES（L3 审计）+ DSHB（L1 证据）+ B-Team
> **日期**: 2026-10-15 | **文档状态**: FINAL (REVISION)
> **约束**: JOB_READY=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE / NO_ZHIJI_API_CALL=FALSE
> **上游基线**: `v86_rc2_e_l2_panel_gray_degrade_spec.md`（T3.3 FINAL）
> **对齐目标**: `gray_gate_decider.py` (12/12 自检 PASS) + HERMES T3.5 灰度门禁评审纪要

---

## 1. 更新摘要（相对 T3.3 原规范的 diff）

### 1.1 本次修订驱动

| # | 触发源 | 变更性质 |
|---|--------|---------|
| 1 | DEP-001 长期 BLOCKED（2026-10-05 ~ 本轮持续） | 新增场景规则 |
| 2 | `gray_gate_decider.py` 落地（12/12 自检 PASS） | 决策语义对齐 |
| 3 | HERMES 三方灰度门禁评审（8 项一致 + 2 项 P0 待办） | 阈值口径锁定 |
| 4 | CASE-A01 真实预发 5 PASS / 3 FAIL（3 FAIL 全部 DEP-001 预期行为） | 短路路径实测化 |
| 5 | DS-06 抖动检测已在 `evidence_auditor_v2_plus.py` 上线 | 抖动规则纳入灰度 |

### 1.2 变更清单（新增 / 修改 / 保留）

| 章节 | 变更类型 | 说明 |
|------|---------|------|
| §2 DEP 长时间不可用场景定义与降级规则 | 🆕 新增 | 引入 DEP_LONG_BLOCKED 状态与 P1/P2 双档降级 |
| §3 灰度阶段 × DEP 故障交互矩阵（24 组合） | 🆕 新增 | 6 阶段 × 4 状态全展开 |
| §4 gray_gate_decider 行为对齐 | 🆕 新增 | 5 决策 × 4 L2 面板动作 × 状态同步 |
| §5 DS-06 抖动规则在灰度中的应用 | 🆕 新增 | 与 G0~G5 判定融合 |
| §6 自动降级触发 / 恢复条件 | ✏️ 修改 | 加入 DEP 依赖项；保留流量/指标/告警原条件 |
| §7 更新后的灰度阶段配置矩阵 | ✏️ 修改 | 各阶段增加 DEP 故障注解列 |
| §8 降级策略更新（含 DEP 故障变体） | ✏️ 修改 | 增加 DEP_LONG_BLOCKED / FLAPPING 列 |
| §9 更新后的 DEP 故障自动回退流程 | ✏️ 修改 | 引入自动降级到历史快照 + 面板动作联动 |
| §10 更新后的切换控制逻辑 | ✏️ 修改 | 新增 `panel_action_mask` 位掩码 |
| §11 跨团队同步 | ✏️ 修改 | 增加 DEP_LONG_BLOCKED / DS-06 触发同步 |
| §5/§7/§8 原内容 | ✅ 保留 | Token Bucket / 采样 / 静默 / 阈值语义不变 |

### 1.3 保持不变项（明确列出）

- 6 阶段灰度骨架 G0→G5 不变；
- 流量 Token Bucket 三级（500/300/100 rps）不变；
- 指标 P0 强制 100% 不可降级不变；
- DEP grace=300s / poll=30s / recovery_polls=3 不变；
- Alert Adapter V3 环境守卫不变；
- 审计轨迹 `audit_fingerprint` 结构不变；
- `BRANCH_LOCKED=TRUE` / `NO_MODIFY_V85=TRUE` / `NO_OVERWRITE=TRUE` 不变。

---

## 2. DEP 长时间不可用场景定义与降级规则（🆕 新增）

### 2.1 场景定义

原规范 §6 仅覆盖「DEP 单次故障 → grace 300s → fallback → recovery」的短时链路。本次新增 **DEP_LONG_BLOCKED** 场景：DEP-001 长时间（≥1 个观测期 = ≥24h）持续 BLOCKED 或 RECOVERED→BLOCKED 反复（≥3 次/24h），触发跨阶段降级。

| 状态 | 语义 | 判定条件 | 灰度影响 |
|------|------|---------|---------|
| **DEP-READY** | 正常 | `dep_001_status=RECOVERED` 且 `dep_flap_count=0` 且 G-06/G-10 PASS | G0~G5 可推进 |
| **DEP_BLOCKED_SHORT** | 短时阻塞 | BLOCKED ≤ grace (300s) | 阶段 HOLD，等待 grace 到期 |
| **DEP_BLOCKED_LONG** | 长时间阻塞 🆕 | BLOCKED ≥ 24h 或 BLOCKED ≥ 3 次/24h 且未恢复 | G1~G5 强制 HOLD，G0 可继续观测但禁止晋级 |
| **DEP_FLAPPING** | 抖动 🆕 | RECOVERED→BLOCKED 循环 ≥ 3 次/24h（DS-06 触发） | 全阶段冻结，回滚到 mock |
| **DEP_PARTIAL** | 部分就绪 | 对照组 ID02226332/a10021355 正常，实验组短ID HTTP 500 | G1~G5 HOLD，允许用长ID 通路推进旁路验证 |

### 2.2 自动降级规则（DEP 长时间不可用）

| 触发条件 | 自动动作 | 目标状态 | 面板动作 | 通知 |
|---------|---------|---------|---------|------|
| BLOCKED ≥ 24h 且当前阶段 = G0 | 保持 G0 观测，禁止晋级 | G0-HOLD | 徽章 `🟡SHADOW_MODE+DEP_LONG_BLOCKED` | 每 6h 通知 HERMES |
| BLOCKED ≥ 24h 且当前阶段 ∈ G1~G4 | 降阶至 G0（影子） | G0-FALLBACK | A-1 + A-4（Alert→sandbox + 静默） | P1 通知 HERMES+DSHB |
| BLOCKED ≥ 24h 且当前阶段 = G5 | 降阶至 G4，暂停 push 到 prod | G4-DEGRADED | A-1 + A-4 + `push=FALSE` | P0 通知三方 |
| BLOCKED ≥ 72h | 强制切换历史快照（≤ 24h 内） | SNAPSHOT-FALLBACK | A-2 (DS→mock) + A-3 (采集暂停) | P0 通知三方+电话 |
| DEP_FLAPPING（DS-06 触发） | 冻结所有晋级 | G-current-FROZEN | A-4 静默 + 保留 mock | CRITICAL + 电话 |

### 2.3 降级与恢复的对称性

- **降级**：按上表逐档触发，每档动作叠加（前一档动作不撤销）；
- **恢复**：需满足「BLOCKED→RECOVERED 3 次成功轮询 + G-06/G-10 PASS + 连续 24h 稳定」三重条件后逐档撤销；
- **例外**：DEP_FLAPPING 恢复需 HERMES 人工确认（对应 F5，见 §4.3）。

---

## 3. 灰度阶段 × DEP 故障交互矩阵（🆕 24 组合）

6 阶段 × 4 DEP 状态（ACTIVE / BLOCKED / FALLBACK / FLAPPING）= **24 种组合**。图例：✅ 可推进 | ⏸ 停留 | ❌ 阻断 | ⚠️ 部分放行 | 🟡 降级运行

### 3.1 分阶段展开

| 阶段 | DEP 状态 | 决策 | L2 面板状态 | 告警 | 徽章 | 备注 |
|------|---------|-----|-----------|------|------|------|
| **G0** | ACTIVE | ADVANCE→G1 | 全功能 | P0-P2 观察 | 🟡SHADOW | 正常路径 |
| G0 | BLOCKED | OBSERVE | 全功能（不取数） | 全部静默 | 🟡SHADOW+DEP_BLOCKED | 影子不依赖取数 |
| G0 | FALLBACK | OBSERVE | 历史快照显示 | 全部静默 | 🟡SHADOW+SNAPSHOT | 允许继续观测 |
| G0 | FLAPPING | HOLD | 全功能但冻结 | CRITICAL | 🟡SHADOW+FLAPPING | DS-06 触发，观察稳定性 |
| **G1** | ACTIVE | ADVANCE→G2 | 全功能 | P0 | 🟢GRAY-G1 | 正常路径 |
| G1 | BLOCKED | HOLD | 只读+降级 | P0 静默 P1/P2 | 🟡GRAY-G1+HOLD | 需 DEP 就绪 |
| G1 | FALLBACK | HOLD | 快照模式 | 全部静默 | 🟡GRAY-G1+SNAPSHOT | 冻结 |
| G1 | FLAPPING | ROLLBACK (F5) | mock 回退 | CRITICAL+电话 | 🔴ROLLBACK | 降阶至 G0 |
| **G2~G4** | ACTIVE | ADVANCE | 全功能 | P0-P2 | 🟢GRAY-G{n} | 正常路径 |
| G2~G4 | BLOCKED | HOLD | 只读降级 | P1/P2 静默 | 🟡GRAY-G{n}+HOLD | A-4 触发 |
| G2~G4 | FALLBACK | HOLD + A-2 | 快照 + 采集暂停 | 全部静默 | 🟡GRAY+SNAPSHOT | A-2 + A-3 叠加 |
| G2~G4 | FLAPPING | ROLLBACK (F5) | 降阶至上一阶段 | CRITICAL | 🔴ROLLBACK | 人工确认 F5 |
| **G5** | ACTIVE | COMPLETE | 全功能+生产推送 | 全部生产 | 🟢FULLY_AVAILABLE | 灰度结束 |
| G5 | BLOCKED | ROLLBACK (F2) | 强制切 G4+mock | P0 全通道 | 🔴ROLLBACK-F2 | 自动回滚 30min 确认 |
| G5 | FALLBACK | ROLLBACK (F2) | G4+快照 | P0 | 🔴ROLLBACK-F2 | 生产通道关闭 |
| G5 | FLAPPING | ROLLBACK (F5) | G4+mock | CRITICAL | 🔴ROLLBACK-F5 | 人工介入 |

### 3.2 24 组合速查表

| 阶段 | ACTIVE | BLOCKED | FALLBACK | FLAPPING |
|------|--------|---------|---------|---------|
| G0 | ✅ ADVANCE | ⏸ OBSERVE | ⏸ OBSERVE | ⚠️ HOLD |
| G1 | ✅ ADVANCE | ⏸ HOLD | ⏸ HOLD | ❌ ROLLBACK(F5) |
| G2 | ✅ ADVANCE | ⏸ HOLD | ⏸ HOLD | ❌ ROLLBACK(F5) |
| G3 | ✅ ADVANCE | ⏸ HOLD | ⏸ HOLD | ❌ ROLLBACK(F5) |
| G4 | ✅ ADVANCE | ⏸ HOLD | ⏸ HOLD | ❌ ROLLBACK(F5) |
| G5 | ✅ COMPLETE | ❌ ROLLBACK(F2) | ❌ ROLLBACK(F2) | ❌ ROLLBACK(F5) |

---

## 4. gray_gate_decider 行为对齐（🆕 新增）

### 4.1 5 类决策动作定义

对齐 `gray_gate_decider.py` 的实际决策语义（12/12 自检 PASS）：

| 决策 | 触发条件（源码语义） | 语义 | L2 面板动作 |
|------|------------------|------|-----------|
| **ADVANCE** | 无故障 + 当前阶段准入 + 观测期完成 + 下一阶段准入 | 推进至下一阶段 | `panel_state=GRAY-G{n+1}` + 徽章升级 |
| **HOLD** | 准入未通过 或 下一阶段准入未通过 | 维持当前阶段 | `panel_state=HOLD` + 徽章 `+HOLD` 后缀 |
| **OBSERVE** | 观测期未满 | 继续当前观测 | `panel_state=OBSERVE` + 剩余时长展示 |
| **ROLLBACK** | F1/F2/F3/F4/F5 任一触发 | 按矩阵回滚 | 对应动作集（见 §4.3）+ 徽章 `🔴ROLLBACK` |
| **COMPLETE** | G5 观测完成 | 灰度结束 | `panel_state=FULLY_AVAILABLE` + 6 通道推送 |

> **备注**：任务描述中提到的 `PROCEED/PAUSE/ESCALATE` 是概念名，实际脚本内命名分别为 `ADVANCE/HOLD/OBSERVE`（无独立 ESCALATE，ESCALATE 语义由 ROLLBACK 的 F3/F4/F5「需人工确认」承载）。

### 4.2 决策输出与 L2 面板状态同步

`decide(state)` → L2 面板 `panel_state` 映射契约：

```
decision          → panel_state          → badge        → 告警行为
ADVANCE           → GRAY-G{n+1}          → 🟢           → 该阶段告警全开
HOLD              → HOLD                 → 🟡+HOLD      → P1/P2 静默，P0 保留
OBSERVE           → OBSERVE              → 🟡+OBSERVE   → 全部观察不推送
ROLLBACK(F1)      → MOCK-FALLBACK        → 🔴           → P0 全通道+电话
ROLLBACK(F2)      → G{n-1}+SNAPSHOT      → 🔴           → P0 全通道
ROLLBACK(F3)      → G{n}+FREEZE          → 🔴+FREEZE    → 保持但冻结推进
ROLLBACK(F4)      → G{n}+DEGRADED        → 🟡+DEGRADED  → 静默 30min 观察
ROLLBACK(F5)      → G{n-1}+MOCK          → 🔴           → CRITICAL+电话
COMPLETE          → FULLY_AVAILABLE      → 🟢           → 生产 6 通道
```

### 4.3 F1~F5 回滚矩阵与 L2 面板动作映射

| 故障 | 严重度 | decider 触发条件 | auto_rollback | need_confirm | 超时 | 对应面板动作（A-1~A-4） |
|-----|--------|-----------------|--------------|-------------|------|---------------------|
| **F1 链路级** | FATAL | HTTP 500 ×5 或 对照组失败 | ✅ | ❌ | 0 秒 | A-1 + A-2 + A-3 + A-4（全回退 mock） |
| **F2 审计级** | HIGH | CRITICAL > 0 | ✅ | ✅ | 30 min | A-1 + A-4（Alert→sandbox + 静默） |
| **F3 Gate 级** | HIGH | G-06 未通过 | ❌ | ✅ | 8 h | A-4（仅冻结，不改数据源） |
| **F4 性能级** | MEDIUM | 吞吐降 >50% 或 p95 > 200ms | ❌ | ✅ | 2 h | A-4（静默 30min 观察） |
| **F5 稳定性级** | MEDIUM | DEP 抖动 ≥3 或断连 > 5 | ❌ | ✅ | 1 h | A-2 + A-4（切快照+静默） |

> **F1 立即自动**：`flags_to_set=["GATE_REVIEW_PAUSED=TRUE","JOB_READY=FALSE"]`；
> **F2 自动+确认**：30 分钟内人工确认，超时后自动降级至 G0；
> **F3~F5 需确认**：DSHE 发起 + HERMES 审批，超时未确认则升级 ESCALATE。

### 4.4 决策输入契约（L2 → decider）

L2 面板每 5 min 采集一次状态并喂入 `decide(state)`：

```json
{"current_stage":"G3","dep_001_status":"BLOCKED","non_zero_rate":0.99,"p95_ms":15,
 "critical_alerts":0,"dep_flap_count":0,"observe_hours_elapsed":30,"http_500_count":0,
 "control_group_failed":false,"gate_g06_pass":true,"throughput_drop_pct":0,"disconnect_count":0}
```

**契约保证**：字段缺省值对齐 `gray_gate_decider.py` `check_faults`/`check_stage_admission` 的默认（`.get(..., default)`），保证输入缺字段的健壮性。

---

## 5. DS-06 抖动规则在灰度中的应用（🆕 新增）

### 5.1 DS-06 规则回顾

DS-06 已在 `evidence_auditor_v2_plus.py` 落地（v2.1.0-plus 3 项新能力之一）：
> "RECOVERED 后再次发生 BLOCKED ≥ 2 次判定为 DEP 抖动"

状态机扩展：

```
ACTIVE → BLOCKED(不计) → RECOVERY(不计) → RECOVERED(窗口打开)
        → DEP_FAILURE ×2 (窗口已开) → ⚠️ FLAPPING
        → RECOVERY→BLOCKED (未经过 RECOVERED) = 恢复验证失败（不计抖动）
```

### 5.2 灰度阶段应用矩阵

| 阶段 | DS-06 阈值（dep_flap_count） | 触发后决策 | 面板动作 | 告警 |
|------|--------------------------|-----------|---------|------|
| G0 | <2（观察期） | HOLD 但不回滚 | 徽章 `+FLAPPING-WATCH` | CRITICAL 观察 |
| G1 | <2 | ROLLBACK→G0 (F5) | A-2 + A-4 | CRITICAL |
| G2 | <2 | ROLLBACK→G1 (F5) | A-2 + A-4 | CRITICAL |
| G3 | <2 | ROLLBACK→G2 (F5) | A-2 + A-4 | CRITICAL |
| G4 | <2 | ROLLBACK→G3 (F5) | A-2 + A-4 | CRITICAL |
| G5 | <2 | ROLLBACK→G4 (F5) | A-1 + A-2 + A-4 | CRITICAL + 电话 |

### 5.3 抖动窗口管理

- **窗口起始**：进入 RECOVERED 状态即打开（不再重置计数）；
- **窗口关闭**：连续 24h 无 BLOCKED 事件；
- **计数保留**：窗口关闭后 `dep_flap_count` 保留 7 天作为审计证据（用于 F5 判定复盘）；
- **DS-06 与 F5 的边界**：DS-06 阈值 = 2 次抖动即判定；F5 阈值 = 抖动 ≥3 次或断连 >5 才回滚。因此抖动第 2 次触发 DS-06 CRITICAL 告警但仅 HOLD，第 3 次才升级为 F5 ROLLBACK。

### 5.4 抖动事件审计轨迹

每次 DS-06 触发写入事件存储：

```json
{"event_id":"DS06-<ts>-<dep_id>","event_type":"DEP_FLAP_DETECTED","dep_registry_id":"DEP-001",
 "phase":"G{n}","flap_count":2,"window_opened_at":"...","trigger_state_transition":"RECOVERED→BLOCKED×2",
 "audit_fingerprint":"<md5>","panel_action":"HOLD+F5-WATCH"}
```

---

## 6. 自动降级触发条件与恢复条件

### 6.1 触发条件矩阵（扩展 DEP 变体）

| 降级类别 | 触发条件 | 恢复条件 | 阶段范围 |
|---------|---------|---------|---------|
| 流量-软限流 | rps > 500s 且持续 >500s | <500s 持续 60s | G1-G5 |
| 流量-硬限流 | rps > 300s 且持续 >30s | <300s 持续 120s | G1-G5 |
| 流量-熔断 | rps > 100s 且持续 >60s | <100s 持续 300s + 人工 | G2-G5 |
| 采样-P1 降级 | CPU > 80% | CPU < 70% 持续 120s | G1-G5 |
| 采样-P2 降级 | CPU > 70% | CPU < 60% 持续 120s | G1-G5 |
| 告警-维护窗口 | 计划内 | 窗口结束 | 全阶段 |
| 告警-晋级过渡 | 晋级前 15min | 晋级确认 | G1-G5 |
| 告警-DEP 降级 | DEP BLOCKED ≥ grace | DEP RECOVERED ×3 | G1-G5 |
| 告警-风暴 | P2 速率 >3x 基线 | 速率回落 10min | 全阶段 |
| 阈值调整 | 7 日基线漂移 >20% | 连续 7 日稳定 | G1-G5 |
| **🆕 DEP 长时间阻塞** | BLOCKED ≥ 24h | RECOVERED + G-06 PASS + 24h 稳定 | G1-G5 |
| **🆕 DEP FLAPPING** | DS-06 计数 ≥ 2 | 24h 无 BLOCKED 事件 | 全阶段 |
| **🆕 G-06 未通过** | 有效桥接率 <阈值 | G-06 PASS | G1-G5 |

### 6.2 恢复条件对称性检查

对每种触发条件，恢复条件必须「严格弱于」触发条件（避免抖动式反复切换）：

| 触发 | 恢复 | 稳定性余量 |
|------|------|-----------|
| BLOCKED ≥ 24h | RECOVERED + G-06 PASS + **连续 24h** 稳定 | 24h 缓冲 |
| FLAPPING ≥ 2 次 | **24h 无 BLOCKED** 事件 | 24h 缓冲 |
| CRITICAL > 0 | CRITICAL = 0 且 HIGH ≤ 阶段阈值 | 立即 |
| F1 链路 | HTTP 500 = 0 且对照组 PASS + 3 次成功轮询 | 90s |
| F4 性能 | 吞吐恢复 + p95 < 阈值 持续 30min | 30min |

---

## 7. 更新后的灰度阶段配置矩阵（G0~G5 with DEP fault annotations）

**变更**：在原规范 §3 的表基础上增加 **DEP 故障注解列** + **决策来源列**。

| 参数 | G0 | G1 | G2 | G3 | G4 | G5 |
|------|----|----|----|----|----|----|
| 流量比例 | 100%旁路 | 1% | 10% | 30% | 60% | 100% |
| P0 采样 | 100% | 100% | 100% | 100% | 100% | 100% |
| P1 采样 | — | — | 70% | 85% | 100% | 100% |
| P2 采样 | 100% | 50% | 70% | 85% | 100% | 100% |
| 告警级别 | P0-P2 观察 | P0 | P0+P1 | P0-P2 | 全部 | 全部生产 |
| 面板禁用 | — | SP4-12,SP5-08,SP6-06 | SP4-12 | 无 | 无 | 无 |
| 晋级条件 | 0P0+0回滚+24h | 0P0+0回滚+24h | P0<2+P1<5 | P0<3+P1<8 | 完整性≥195/197 | 168h 稳定 |
| 回滚条件 | P0>3 或 DEP>5min | P0 触发 | P0≥2 或 P1≥5 | 超阈值 | 超阈值 | 任一 P0 |
| 检查频率 | 15min | 5min | 5min | 5min | 5min | 1min |
| **决策来源** 🆕 | decider | decider | decider | decider | decider | decider |
| **DEP 依赖** 🆕 | 不依赖 | 强制 | 强制 | 强制 | 强制 | 强制 |
| **DEP_BLOCKED 时** 🆕 | OBSERVE | HOLD | HOLD | HOLD | HOLD | ROLLBACK-F2 |
| **DEP_FALLBACK 时** 🆕 | OBSERVE | HOLD | HOLD | HOLD | HOLD | ROLLBACK-F2 |
| **DEP_FLAPPING 时** 🆕 | HOLD | ROLLBACK-F5 | ROLLBACK-F5 | ROLLBACK-F5 | ROLLBACK-F5 | ROLLBACK-F5 |
| **DS-06 阈值** 🆕 | <2 | <2 | <2 | <2 | <2 | <2 |

---

## 8. 降级策略更新（含 DEP 故障变体）

### 8.1 流量降级（Token Bucket）—— 保留 + DEP 变体

| 级别 | 阈值 | 原规范动作 | DEP 故障变体 🆕 |
|------|------|-----------|--------------|
| 软限流 500 rps | >500s 持续 >500s | 队列缓冲 | BLOCKED 时自动跳过硬限直接进熔断（防止堆积无效请求） |
| 硬限流 300 rps | >300s 持续 30s | 拒绝 429 | FALLBACK 时 P1/P2 全降为 0，仅 P0 保留 |
| 熔断 100 rps | >100s 持续 60s | 仅 P0 通过 | FLAPPING 时立即熔断（不等阈值） |

### 8.2 指标采样降级 —— 保留 + DEP 变体

| 变体 | 条件 | P0 | P1 | P2 | 说明 |
|------|------|----|----|----|----|
| 原规范 CPU 降级 | CPU>80/70% | 100% | 50% | 50% | 保留 |
| **🆕 DEP_BLOCKED_LONG** | BLOCKED ≥ 24h | 100% | 30% | 10% | 大幅收缩非必要指标 |
| **🆕 DEP_FALLBACK** | 切换到快照 | 100% | 0% | 0% | 快照只读 P0 |
| **🆕 DEP_FLAPPING** | DS-06 触发 | 100% | 20% | 0% | 最小化面板依赖 |

### 8.3 告警静默 —— 保留 + DEP 变体

| 变体 | 触发 | 静默范围 | 时长 | 恢复 |
|------|------|---------|------|------|
| 原规范 6 类 | 保留 | 保留 | 保留 | 保留 |
| **🆕 DEP 长时间阻塞** | BLOCKED ≥ 24h | P1+P2 | 阻塞持续期 | RECOVERED + 24h 稳定 |
| **🆕 FLAPPING 静默** | DS-06 触发 | P1+P2（保留 CRITICAL） | FLAPPING 持续期 | 24h 无事件 |
| **🆕 G5 强制静默** | ROLLBACK-F2 触发 | 除 P0 外全部 | 30min（F2 确认期） | F2 确认 |

### 8.4 阈值动态调整 —— 保留 + DEP 变体

| 变体 | 触发 | 调整范围 | 说明 |
|------|------|---------|------|
| 原规范 7 日滑动 | 保留 | ±50% | 保留 |
| **🆕 DEP 阻塞期基线冻结** | BLOCKED ≥ 24h | 冻结 7 日基线 | 防止 BLOCKED 期间数据扭曲基线 |
| **🆕 恢复期基线重训** | RECOVERED + 24h 稳定 | 从当日零点重训 | 避免旧基线误报 |

### 8.5 降级适用矩阵（更新版）

| 策略 | G0 | G1 | G2 | G3 | G4 | G5 |
|------|----|----|----|----|----|----|
| 流量-软限 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 流量-硬限 | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| 流量-熔断 | — | — | ✅ | ✅ | ✅ | ✅ |
| 采样降级 | — | ✅ | ✅ | ✅ | ✅ | — |
| 自动静默 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 阈值调整 | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| **🆕 DEP 长时间降级** | ⚠️ 观察 | ✅ | ✅ | ✅ | ✅ | ✅ |
| **🆕 FLAPPING 冻结** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 9. 更新后的 DEP 故障自动回退流程

### 9.1 时间线（扩展 DEP_LONG_BLOCKED）

| 时间 | 事件 | 状态转换 | 面板动作 | 决策 |
|------|------|---------|---------|------|
| T+0s | DEP 不可达 | ACTIVE → BLOCKED | 徽章 `+DEP_BLOCKED` | OBSERVE |
| T+300s | grace 到期 | BLOCKED → FALLBACK | A-4 静默 P1/P2 | HOLD |
| T+300s~T+24h | 阻塞持续 | FALLBACK 保持 | A-2 切快照 + A-3 采集暂停 | HOLD |
| T+24h | 阻塞累计 24h | FALLBACK → DEP_LONG_BLOCKED | 徽章 `+DEP_LONG_BLOCKED` | HOLD（若 G1+）/ OBSERVE（G0） |
| T+24h~T+72h | 长时间阻塞 | DEP_LONG_BLOCKED 保持 | 降阶至 G0（若原为 G1~G4） | HOLD |
| T+72h | 阻塞累计 72h | 强制降级 | A-1+A-2+A-3+A-4 全回退 mock | ROLLBACK (F2-like) |
| T+X | 3 次成功轮询 | FALLBACK → RECOVERY | 静默解除准备 | OBSERVE |
| T+X+90s | 恢复验证通过 | RECOVERY → RECOVERED | 恢复实时数据 | ADVANCE |
| T+X+90s+24h | 稳定 24h | RECOVERED 保持 | 徽章恢复 | ADVANCE |
| — | RECOVERED 后又 BLOCKED ×2 | 打开 FLAPPING 窗口 | A-4 + 徽章 `+FLAPPING-WATCH` | HOLD |
| — | 窗口内 BLOCKED ×3 | FLAPPING 触发 | A-2 + A-4 + 回退 mock | ROLLBACK (F5) |

### 9.2 状态机图（扩展，紧凑表示）

```
ACTIVE --DEP_FAILURE--> BLOCKED --grace 300s--> FALLBACK --3次成功--> RECOVERY --验证通过--> RECOVERED
  ↑                        │                                              │
  └────────────────────────┴──────── (grace 未到期 或 恢复失败) ─────────────┘
                                                                          │
                                                              ┌───────────┴───────────┐
                                                              │                       │
                                                        24h 稳定(关窗)         BLOCKED×2(开窗)
                                                                              │
                                                                              ▼
                                                                        FLAPPING ⚠️
                                                                              │ BLOCKED×3 (窗口内)
                                                                              ▼
                                                                        ROLLBACK (F5)
BLOCKED --≥24h--> DEP_LONG_BLOCKED (与 FLAPPING 平级，触发降级)
```

### 9.3 参数（新增项标 🆕）

| 参数 | 值 | 说明 |
|------|-----|------|
| grace | 300s | 保留 |
| poll_interval | 30s | 保留 |
| poll_timeout | 5s | 保留 |
| recovery_polls | 3 | 保留 |
| snapshot_retention | 30d | 保留 |
| snapshot_max_age | 24h | 保留 |
| **🆕 dep_long_block_threshold** | 24h | DEP_LONG_BLOCKED 阈值 |
| **🆕 dep_full_rollback_threshold** | 72h | 强制全回退阈值 |
| **🆕 flap_window_hours** | 24h | FLAPPING 窗口关闭时长 |
| **🆕 ds_06_flap_threshold** | 2 | DS-06 触发阈值 |
| **🆕 f5_flap_threshold** | 3 | F5 回滚阈值（> DS-06） |

---

## 10. 更新后的切换控制逻辑

### 10.1 配置驱动扩展

在原规范 JSON 配置基础上，新增 `panel_action_mask` 位掩码字段（4 bit，对齐 rollback_plan A-1~A-4）：

```json
{"phase":"G3","decider_decision":"HOLD",
 "dep_fault_annotation":{"dep_001_status":"BLOCKED","block_duration_hours":26.5,"flap_count":0,"flap_window_open":false},
 "panel_action_mask":{"a1_alert_sandbox":false,"a2_ds_mock":true,"a3_collector_pause":false,"a4_alert_silence":true},
 "hot_reload_interval_sec":5,
 "audit_trail_event_types":["phase_change","dep_state_change","ds06_flap","panel_action_apply","decider_decision"]}
```

### 10.2 `panel_action_mask` 位掩码语义

| bit | 名称 | 触发来源 | 幂等性 |
|-----|------|---------|-------|
| A-1 | `alert_sandbox` | ROLLBACK-F1/F2 或 DEP 长时间阻塞 | 幂等 |
| A-2 | `ds_mock` | ROLLBACK-F1/F5 或 FALLBACK | 幂等 |
| A-3 | `collector_pause` | ROLLBACK-F1 或 DEP_BLOCKED ≥ 72h | 幂等 |
| A-4 | `alert_silence` | 任何 ROLLBACK 或 FLAPPING | 幂等 |

### 10.3 热重载与安全

- 保留 5s 热重载间隔；
- **新增**：`panel_action_mask` 变化视为高优事件，走「先应用 → 后审计」路径，防止审计滞后于动作；
- **新增**：语法校验失败 → 回退至上一有效配置 + 触发 F2-like 静默；
- 环境守卫：Alert Adapter V3 环境隔离（PROD_AUTH_MISSING/PROD_CROSS_WRITE/SANDBOX_CROSS_WRITE）保留。

### 10.4 阶段配置对比（更新版）

| 字段 | G0 | G1 | G2 | G3 | G4 | G5 |
|------|----|----|----|----|----|----|
| deploy_env | sandbox | sandbox | sandbox | sandbox | sandbox | prod |
| push | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| P0/P1/P2 采样 | 1.0/-/- | 1.0/-/0.5 | 1.0/0.7/0.7 | 1.0/0.85/0.85 | 1.0/1.0/1.0 | 1.0/1.0/1.0 |
| badge | SHADOW | GRAY-G1 | GRAY-G2 | GRAY-G3 | GRAY-G4 | FULLY |
| rollback_target | mock | G0 | G1 | G2 | G3 | G4 |
| **🆕 decider_enabled** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **🆕 action_mask_default** | 0b0000 | 0b0000 | 0b0000 | 0b0000 | 0b0000 | 0b0000 |
| **🆕 flap_watch_enabled** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 11. 跨团队同步（DSHB / HERMES / B-Team 对齐）

### 11.1 同步节奏（扩展）

原规范：G0 进入 → 每日报告 → 晋级 → G5 → 回滚 → DEP 故障 → DS-06 抖动。

**本次新增**：

| 事件 | 同步对象 | 时效 | 通道 |
|------|---------|------|------|
| DEP_LONG_BLOCKED 触发（BLOCKED ≥ 24h） | HERMES + DSHB + B-Team | 立即 | 飞书+邮件 |
| 面板动作 mask 变更（A-1~A-4 任一翻转） | HERMES | 立即 | 事件存储 + 告警 |
| decider 决策切换（如 HOLD→ROLLBACK） | 三方 | 立即 | 事件存储 |
| DS-06 触发（第 2 次抖动） | HERMES | 立即 | CRITICAL |
| FLAPPING 触发（第 3 次抖动） | 三方 | 立即 | CRITICAL + 电话 |
| 恢复（连续 24h 稳定） | 三方 | 24h 后 | 报告 |
| 基线重训完成 | DSHB | 当日 | 报告 |

### 11.2 责任矩阵（更新）

| 事件 | DSHE | DSHB | HERMES | B-Team |
|------|------|------|--------|--------|
| G0 进入 | 通知（1日） | — | 审计 | — |
| 晋级 G0→G1 | 决策+执行 | 确认数据源 | 审批 | — |
| 晋级 G1~G5 | 决策+执行 | — | 审批 | 业务通知 |
| 回滚 F1 | 执行（≤5min） | 通知 | 事后审计 | 通知（≤4h） |
| 回滚 F2 | 执行+确认 | 通知 | 审批（30min 内） | 通知 |
| 回滚 F3/F4/F5 | 发起 | 通知 | 审批 | 通知 |
| **🆕 DEP_LONG_BLOCKED** | 发起 | 加速修复 | 审批降级 | 通知 |
| **🆕 FLAPPING** | 冻结+通知 | 稳定性分析 | CRITICAL 审批 | 通知 |
| **🆕 DS-06 第 2 次** | 观察 | 记录 | 分析 | — |
| **🆕 panel_action_mask 变化** | 执行 | — | 事件存储审计 | — |

### 11.3 与 HERMES 灰度门禁评审纪要对齐

引用 `v86_rc2_hermes_gray_gate_review_minutes.md` §1 8 项一致结论 + §10 5 项待办：

- ✅ 8 项评审结论已全部在本文档反映；
- ⏳ 待办 1（P0）：DEP-001 短ID 解析服务就绪 → DSHB 主导，阻塞 G1~G5；
- ⏳ 待办 4（P0）：CASE-A01 正向 E2E 真实环境 → 三方，本文档 §4.2 决策契约已就位；
- ✅ 待办 2/3/5（P1）：审计吞吐阈值/批量上报/灰度阶梯阈值已在 decider 中固化；
- **本次更新新增**：DEP_LONG_BLOCKED 与 FLAPPING 场景在评审 §6 阻断行为基础上向前延伸。

### 11.4 事件存储共享契约

所有跨团队事件写入 `audit_event_store`，字段包括 `event_id / event_type / phase / dep_registry_id / panel_action_mask / decider_decision / audit_fingerprint`。三方均可通过 `--query --dep DEP-REG-001` 或 `--team DSHB/DSHE/HERMES` 独立检索。

---

## 12. 约束合规声明

| 约束 | 值 | 状态 | 说明 |
|------|-----|------|------|
| JOB_READY | FALSE | ✅ | DEP-001 BLOCKED，与 flag 一致 |
| NO_ZHIJI_API_CALL | FALSE | ✅ | 允许真实取数调用 |
| NO_MODIFY_V85 | TRUE | ✅ | 本文档仅在 `analysis/e2e_output/v86/` 内新增 |
| NO_OVERWRITE | TRUE | ✅ | 新增文件 `v86_rc2_e_l2_panel_gray_degrade_spec_update.md`，未修改原 T3.3 spec |
| BRANCH_LOCKED | TRUE | ✅ | 分支 `feature/v85-chart-template` |
| L2_INDEPENDENT_CALL_CHAIN | TRUE | ✅ | L2 面板使用独立调用链 |
| AUDIT_TRACEABILITY | TRUE | ✅ | 事件存储契约覆盖 §11.4 |
| ENV_GUARD_ENFORCED | TRUE | ✅ | Alert Adapter V3 保留 |
| P0_FORCED_100 | TRUE | ✅ | P0 采样 100% 不可降级保留 |
| DS_06_ENFORCED | TRUE | ✅ | §5 已完整落地 |
| DEP_GRACE_PERIOD | 300s | ✅ | 保留 |
| **🆕 DEP_LONG_BLOCK_THRESHOLD** | 24h | ✅ | 新增 |
| **🆕 FLAPPING_F5_THRESHOLD** | 3 次 | ✅ | 新增（>DS-06 阈值 2） |
| **🆕 DECIDER_ALIGNED** | TRUE | ✅ | 与 `gray_gate_decider.py` 12/12 自检 PASS 对齐 |
| **🆕 PANEL_ACTION_MASK_4BIT** | TRUE | ✅ | 新增位掩码 |
| **🆕 CASE_A01_REAL_RUN_VERIFIED** | TRUE | ✅ | 5PASS/3FAIL 3 FAIL 为 DEP 预期行为 |
| HOT_RELOAD | TRUE | ✅ | 5s 保留 |
| ALERT_ADAPTER_V3 | TRUE | ✅ | 保留 |
| CROSS_TEAM_SYNC_CONFIGURED | TRUE | ✅ | §11 已扩展 |

---

## 13. 状态标记

```
DSHE_V86_RC2_L2_PANEL_GRAY_DEGRADE_SPEC_UPDATED=TRUE
T3.5_GRAY_DEGRADE_SPEC_UPDATE_COMPLETE=TRUE
DEP_LONG_BLOCKED_SCENARIO_DEFINED=TRUE
DECIDER_ALIGNMENT_COMPLETED=TRUE
DS_06_FLAP_INTEGRATION_COMPLETED=TRUE
GRAY_PHASES_DEP_INTERACTION_MATRIX=24_combinations
DECISION_ACTIONS=5(ADVANCE/HOLD/OBSERVE/ROLLBACK/COMPLETE)
L2_PANEL_ACTIONS=4(A-1_alert_sandbox/A-2_ds_mock/A-3_collector_pause/A-4_alert_silence)
DECIDER_TO_PANEL_MAPPING=5:4
FLAPPING_F5_THRESHOLD=3
DS_06_THRESHOLD=2
DEP_LONG_BLOCK_THRESHOLD=24h
DEP_FULL_ROLLBACK_THRESHOLD=72h
FLAP_WINDOW_HOURS=24
GRAY_PHASES=6(G0+G1+G2+G3+G4+G5)
DEP_STATES=4(ACTIVE/BLOCKED/FALLBACK/FLAPPING)
DEGRADED_VARIANTS=4(DEP_LONG_BLOCKED/FLAPPING/FALLBACK/CPU)
AUTO_DEGRADE_TRIGGERS=13(原10+新3)
CROSS_TEAM_SYNC_EXTENDED=TRUE
AUDIT_EVENT_STORE_INTEGRATED=TRUE
DEP_001_STATUS=BLOCKED
JOB_READY=FALSE
GATE_DECISION=NOT_READY
HERMES_GRAY_GATE_REVIEW_DONE=TRUE
```

---

## 附录 A. 与原规范的关键差异（Diff 摘要）

| 原规范（T3.3） | 更新版（T3.5） |
|--------------|--------------|
| DEP 只有 ACTIVE/BLOCKED/FALLBACK/RECOVERY/RECOVERED 5 状态 | 新增 DEP_LONG_BLOCKED + FLAPPING 2 状态 = **7 状态** |
| 无 dep_long_block_threshold 参数 | 新增 24h 阈值 + 72h 强制回退 |
| DS-06 只描述规则，未融入灰度决策 | 与 F5 阈值解耦（DS-06=2, F5=3），全阶段矩阵落地 |
| 无 gray_gate_decider 对齐 | 5 决策 × 4 面板动作 × 状态同步契约 |
| 无面板动作位掩码 | panel_action_mask 4-bit 位掩码 |
| 24 组合未展开 | 6 阶段 × 4 DEP 状态 = 24 组合全展开 |
| 无跨团队事件同步扩展 | 新增 7 类新事件同步 |
| 恢复条件未系统化 | 每种触发条件都有对称恢复条件 + 稳定性余量 |

## 附录 B. 引用文档

- `v86_rc2_e_l2_panel_gray_degrade_spec.md`（T3.3 原规范基线）
- `v86_rc2_hermes_gray_gate_review_minutes.md`（三方评审 8 项一致）
- `v86_rc2_hermes_session_handover_latest.md`（会话交接，含 §16 灰度判定）
- `v86_rc2_hermes_case_a01_real_run_report.md`（CASE-A01 真实预发 5/3）
- `gray_gate_decider.py`（12/12 自检 PASS，5 决策源）
- `v86_rc2_e_l2_panel_rollback_plan.md`（rollback_l2_panel.sh A-1~A-4 定义）
- `evidence_auditor_v2_plus.py`（DS-06 抖动检测载体）
- `EVIDENCE_CONTRACT_V1.md`（三方证据包契约）

---

*Generated: 2026-10-15 | Task: DSHE_V86_RC2_L2_PANEL_REAL_DEP_GRAY_DEP_READY / T3.5*
*Branch: feature/v85-chart-template @ 629ccb7 (L2_PANEL_REAL_DEP_GRAY_READY, 本轮 T3.5 前基线)*
*Status: T3.5 COMPLETE — 24 组合矩阵 / 5 决策映射 / DS-06 融合 / DEP_LONG_BLOCKED 场景全部定义*
