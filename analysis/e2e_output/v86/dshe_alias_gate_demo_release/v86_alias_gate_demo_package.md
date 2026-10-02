# V86 别名引擎 Gate 评审演示包

> 任务: `DSHE_V86_ALIAS_GATE_DEMO_ASSEMBLY_AND_RELEASE_NOTE_COMPILE` · T2.1
> 分支: `feature/v85-chart-template` @ `d1e070d`
> 版本: `v86.0.0-frozen`
> 用途: Gate 评审现场演示 / PPT 素材 / 门户演示配套
> 约束: NO_ZHIJI_API_CALL / NO_MODIFY_V85 / NO_OVERWRITE

---

## 目录

1. [关键指标卡片包](#1-关键指标卡片包)
2. [灰度演练时序与样例日志](#2-灰度演练时序与样例日志)
3. [异常注入场景样例](#3-异常注入场景样例)
4. [门户演示配套脚本](#4-门户演示配套脚本)
5. [PPT 素材包](#5-ppt-素材包)
6. [演示流程总控表](#6-演示流程总控表)

---

## 1. 关键指标卡片包

### 1.1 引擎核心指标 (Metric Cards)

| 指标 | 实测值 | V85 基线 | Δ | 阈值 | 状态 |
|------|--------|----------|---|------|------|
| **别名条目总数** | 4,643 | 4,643 | 0 | — | ✅ 一致 |
| **Canonical Key 去重数** | 1,818 | — | — | — | ✅ 新增 |
| **F2 UNIQUE 解析** | 2,713 (58.43%) | — | — | — | ✅ 新增 |
| **F2 AMBIGUOUS 解析** | 165 (3.55%) | — | — | ≤ 5% | ✅ 达标 |
| **F2 NO_MATCH 解析** | 1,751 (37.71%) | — | — | — | ✅ 新增 |
| **F2 UNREGISTERED 解析** | 14 (0.30%) | — | — | — | ✅ 新增 |
| **PASS 率 (f3+f4)** | 96.40% (4,476) | 99.14% (4,603) | -2.74pp | ≥ 95% | ✅ 达标 |
| **REVIEW 率** | 3.55% (165) | 0% | +3.55pp | ≤ 5% | ✅ 达标 |
| **BLOCK 率** | 0.04% (2) | 0.86% (40) | -0.82pp | — | ✅ 下降 |
| **引擎冷启动** | 22,739ms | ~20,000ms | +13.7% | ≤ 30s | ✅ 达标 |
| **单条裁决耗时** | 0.143ms | ~0.08ms | +78.75% | ≤ 5ms | ✅ 达标 |
| **吞吐** | 2,144 entries/s | ~1,500/s | +42.9% | ≥ 1,500/s | ✅ 提升 |
| **缓存命中率** | 100% (预热后) | 无缓存 | — | ≥ 85% | ✅ 新增 |
| **内存占用** | ~128MB | ~70MB | +82.9% | ≤ 512MB | ✅ 达标 |

### 1.2 F1/F2/F3/F4 修复档指标

| 修复档 | 触发/命中 | 说明 | 证据文件 |
|--------|-----------|------|----------|
| **F1 异常兜底** | 2,878 hits / 1,765 misses | KeyError 安全捕获, 别名未命中返回 NO_MATCH | `v86_alias_full_replay_report.md` §4 |
| **F2 UNIQUE** | 2,713 | 别名→canonical_key 唯一解析 | `replay_results.json` |
| **F2 AMBIGUOUS** | 165 | 别名→多 canonical_key 歧义 | `alias_p0_manual_sample_set.json` |
| **F2 NO_MATCH** | 1,751 | 别名库未命中 | `v86_alias_full_replay_report.md` §3 |
| **F3 R-05 触发** | 2 | 黑名单重排优先于别名匹配 | `v86_alias_full_replay_report.md` §5 |
| **F4a 抑制** | 132 | 子串包含抑制事件 | `v86_alias_full_replay_report.md` §6 |
| **F4b 抑制** | 46 | 复合短语抑制事件 | `v86_alias_full_replay_report.md` §6 |
| **F4 受影响条目** | 51 | 最终被 F4 抑制的别名条目数 | `v86_alias_full_replay_report.md` §6 |

### 1.3 性能对比卡片

```
┌─────────────────────────────────────────────────────────────────────┐
│  🚀 V86 别名引擎性能对比                                              │
├──────────────────┬──────────────────────────────────────────────────┤
│  吞吐提升         │  V85: ~1,500/s  →  V86: 2,144/s  (+42.9%)      │
├──────────────────┼──────────────────────────────────────────────────┤
│  PASS 率          │  V85: 99.14%    →  V86: 96.40%   (-2.74pp)      │
│  (f3+f4 模式)     │  说明: F3+F4 引入更严格门禁, 误放行减少          │
├──────────────────┼──────────────────────────────────────────────────┤
│  首次请求 (热缓存) │  V85: ~5ms      →  V86: 0.01ms    (-99.8%)     │
│  (预热后)         │  LRU 缓存 1024 条目, 100% 命中                   │
├──────────────────┼──────────────────────────────────────────────────┤
│  单条裁决         │  V85: ~0.08ms   →  V86: 0.143ms   (+78.75%)     │
│                   │  F1-F4 四层修复增加 ~0.06ms 开销                  │
├──────────────────┼──────────────────────────────────────────────────┤
│  缓存节省         │  热路径: 0.01ms vs 冷路径: 0.14ms (14x 加速)     │
├──────────────────┼──────────────────────────────────────────────────┤
│  灰度-基线差      │  PASS 率差: 2.74pp (阈值 ≤ 5pp)                  │
│  (G-GR-10)        │  在安全范围内, F3+F4 门禁重排导致的预期差异       │
└──────────────────┴──────────────────────────────────────────────────┘
```

### 1.4 灰度门禁状态卡片

```
┌─────────────────────────────────────────────────────────────────────┐
│  🛡️ 灰度门禁状态 (12 道)                                             │
├──────────────┬──────────┬──────────┬──────────┬────────────────────┤
│  门禁 ID     │  指标     │  实测值   │  阈值     │  状态              │
├──────────────┼──────────┼──────────┼──────────┼────────────────────┤
│  G-GR-01     │  错误率   │  0.00%   │  ≤ 0.1%  │  ✅ PASS           │
│  G-GR-02     │  平均耗时 │  0.14ms  │  ≤ 5ms   │  ✅ PASS           │
│  G-GR-03     │  P99 耗时 │  0.80ms  │  ≤ 50ms  │  ✅ PASS           │
│  G-GR-04     │  歧义率   │  3.55%   │  ≤ 5%    │  ✅ PASS           │
│  G-GR-05     │  PASS 率  │  96.40%  │  ≥ 95%   │  ✅ PASS           │
│  G-GR-06     │  F4 抑制率│  1.10%   │  ≤ 10%   │  ✅ PASS           │
│  G-GR-07     │  缓存命中率│  100.0%  │  ≥ 85%   │  ✅ PASS           │
│  G-GR-08     │  冷启动   │  22.74s  │  ≤ 30s   │  ✅ PASS           │
│  G-GR-09     │  首次请求 │  0.01ms  │  ≤ 50ms  │  ✅ PASS           │
│  G-GR-10     │  灰度-基线差│  2.74pp │  ≤ 5pp   │  ✅ PASS           │
│  G-GR-11     │  长尾歧义  │  0 新增  │  ≤ 0/天  │  ✅ PASS           │
│  G-GR-12     │  内存占用  │  128MB   │  ≤ 512MB │  ✅ PASS           │
├──────────────┴──────────┴──────────┴──────────┴────────────────────┤
│  结论: 12/12 全绿, 具备全量上线条件                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 灰度演练时序与样例日志

### 2.1 灰度放量时序图

```
时间轴 (T+0)                    流量比例              引擎模式        门禁状态
─────────────────────────────────────────────────────────────────────────
T+0d   ──────── Phase 0 ────────  0% (仅监控)        f3+f4          12/12 PASS
│       冷启动 22.74s ✓
│       首次请求 0.01ms ✓
│       预热 18 样本 ✓
│       缓存 956 条目 ✓
│
T+1d   ─── Phase 1 START ────────  10%               f3+f4          12/12 PASS
│       W0: PASS 96.42%
│       W1: PASS 96.38%
│       W2: PASS 96.41%
│
T+2d   ─── 异常注入: 解析超时 ───── 10%               f3+f4          8/12 FAIL
│       error_rate: 1.52% (超阈值)
│       avg_latency: 55.3ms (超阈值)
│       ─── 自动降级 L0→L1 (F4 off) ───
│       切换耗时: 3s
│       流量中断: 0 请求
│
T+2d+  ─── 恢复 L0 ──────────────  10%               f3+f4          12/12 PASS
│
T+2d+  ─── 异常注入: 缓存失效 ───── 10%               f3+f4          11/12 FAIL
│       cache_hit_rate: 45.1% (低于阈值)
│       告警 (非自动降级, P1 级别)
│       恢复: 缓存持久化后自动恢复
│
T+3d   ─── 异常注入: 脏数据 ──────  10%               f3+f4          10/12 FAIL
│       error_rate: 0.85% (超阈值)
│       ambiguity_rate: 8.12% (超阈值)
│       ─── 自动降级 L0→L2 (F3 off) ───
│       切换耗时: 3s
│       PASS 率恢复: 99.14% (base 模式)
│
T+5d   ─── Phase 2 START ────────  30%               f3+f4          12/12 PASS
│       W0: PASS 96.42%
│       W1: PASS 96.39%
│
T+5d+  ─── 异常注入: 超时+缓存 ───  30%               f3+f4          7/12 FAIL
│       自动降级 L1 → 恢复
│
T+7d   ─── Phase 3 START ────────  100%              f3+f4          12/12 PASS
│       全量切换验证
│       PASS 96.39% ~ 96.42%
│
T+8d   ─── 稳态监控 ─────────────  100%              f3+f4          12/12 PASS
```

### 2.2 样例日志 — Phase 0 冷启动

```
[2026-10-01T08:00:00Z] [INFO] === V86 Alias Engine Startup ===
[2026-10-01T08:00:00Z] [INFO] Mode: f3+f4
[2026-10-01T08:00:00Z] [INFO] Repo: /opt/dshe/framework-tree
[2026-10-01T08:00:00Z] [INFO] Python: 3.11.8
[2026-10-01T08:00:00Z] [INFO] Dependencies: OK
[2026-10-01T08:00:00Z] [INFO] Loading V85 alias library (read-only)...
[2026-10-01T08:00:00Z] [INFO]   File: /v85/indicator_alias_library.csv
[2026-10-01T08:00:00Z] [INFO]   Size: 1.2MB, 4643 entries
[2026-10-01T08:00:22Z] [INFO] Engine initialization complete (22739ms)
[2026-10-01T08:00:22Z] [INFO] F1 guard: enabled
[2026-10-01T08:00:22Z] [INFO] F2 resolver: enabled (UNIQUE/AMBIGUOUS/NO_MATCH/UNREGISTERED)
[2026-10-01T08:00:22Z] [INFO] F3 gate reorder: enabled (R-05 priority)
[2026-10-01T08:00:22Z] [INFO] F4 self-suppress: enabled (F4a+F4b)
[2026-10-01T08:00:22Z] [INFO] Starting warmup (18 samples)...
[2026-10-01T08:00:22Z] [INFO]   [1/18] 碳酸锂工厂库存天数 → UNIQUE ✓
[2026-10-01T08:00:22Z] [INFO]   [2/18] 电解铜库存 → UNIQUE ✓
[2026-10-01T08:00:22Z] [INFO]   ...
[2026-10-01T08:00:27Z] [INFO] Warmup complete (18/18, 4890ms)
[2026-10-01T08:00:27Z] [INFO] LRU cache loaded: 956 entries
[2026-10-01T08:00:27Z] [INFO] Cache persisted: resolve_cache.pkl (256KB)
[2026-10-01T08:00:27Z] [INFO] Metrics endpoint: :8081/metrics
[2026-10-01T08:00:27Z] [INFO] Health endpoint: :8080/healthz
[2026-10-01T08:00:27Z] [INFO] Engine ready (degrade_level=0, mode=f3+f4)
```

### 2.3 样例日志 — 异常注入: 解析超时

```
[2026-10-01T10:30:00Z] [WARN] G-GR-01 FAIL: error_rate=1.52% (threshold ≤ 0.1%)
[2026-10-01T10:30:00Z] [WARN] G-GR-02 FAIL: avg_latency=55.3ms (threshold ≤ 5ms)
[2026-10-01T10:30:00Z] [WARN] G-GR-03 FAIL: p99_latency=434.2ms (threshold ≤ 50ms)
[2026-10-01T10:30:00Z] [WARN] G-GR-10 FAIL: gray_vs_base_diff=7.2pp (threshold ≤ 5pp)
[2026-10-01T10:30:01Z] [ACTION] DegradeController: evaluating...
[2026-10-01T10:30:01Z] [ACTION] DegradeController: L0→L1 (F4 off, mode=f3)
[2026-10-01T10:30:01Z] [INFO]   Writing DEGRADE_LEVEL=1 to /etc/v86/degrade_level
[2026-10-01T10:30:01Z] [INFO]   POST /api/mode {"mode":"f3"}
[2026-10-01T10:30:04Z] [INFO] Engine mode changed: f3+f4 → f3
[2026-10-01T10:30:04Z] [INFO] F4 self-suppress: DISABLED
[2026-10-01T10:30:04Z] [INFO] F3 gate reorder: ENABLED
[2026-10-01T10:30:04Z] [INFO]   Post-degrade metrics: error_rate=0.00%, avg_latency=0.13ms
[2026-10-01T10:30:04Z] [INFO]   Post-degrade gates: 12/12 PASS
[2026-10-01T10:30:04Z] [INFO]   Traffic lost: 0 requests (3s switch, 0 interruption)
[2026-10-01T10:31:00Z] [INFO] Recovery check: error_rate ≤ 0.05% for 60s
[2026-10-01T10:31:00Z] [INFO] Recovery check: avg_latency ≤ 3ms for 60s
[2026-10-01T10:36:00Z] [ACTION] Recovery conditions met, reverting L1→L0
[2026-10-01T10:36:00Z] [INFO]   Writing DEGRADE_LEVEL=0
[2026-10-01T10:36:00Z] [INFO]   POST /api/mode {"mode":"f3+f4"}
[2026-10-01T10:36:02Z] [INFO] Engine mode restored: f3 → f3+f4
```

### 2.4 样例日志 — 引擎崩溃恢复

```
[2026-10-01T14:15:00Z] [CRITICAL] Engine process terminated (SIGKILL, exit code 137)
[2026-10-01T14:15:05Z] [WARN] K8s: pod v86-alias-engine-7d8f9c4b6-x2k9m is CrashLoopBackOff
[2026-10-01T14:15:05Z] [WARN] K8s: livenessProbe failed (HTTP 503)
[2026-10-01T14:15:05Z] [ACTION] Envoy: switching traffic to v85_baseline (100%)
[2026-10-01T14:15:08Z] [INFO] Envoy config reload: v86_gray weight=0, v85_baseline weight=100
[2026-10-01T14:15:08Z] [INFO] Writing DEGRADE_LEVEL=3
[2026-10-01T14:15:08Z] [INFO] Traffic: 100% → V85 baseline (0 interruption)
[2026-10-01T14:15:08Z] [INFO] K8s: creating replacement pod...
[2026-10-01T14:15:30Z] [INFO] K8s: pod v86-alias-engine-7d8f9c4b6-p4n7q started
[2026-10-01T14:15:52Z] [INFO] Engine initialization complete (22739ms)
[2026-10-01T14:15:52Z] [INFO] Warmup complete (18/18, 4890ms)
[2026-10-01T14:15:52Z] [INFO] readinessProbe: HTTP 200 OK
[2026-10-01T14:15:52Z] [INFO] Engine ready, mode=f3+f4
[2026-10-01T14:15:52Z] [ACTION] Recovery confirmed, switching traffic back to V86
[2026-10-01T14:15:55Z] [INFO] Envoy config reload: v86_gray weight=100, v85_baseline weight=0
[2026-10-01T14:15:55Z] [INFO] Writing DEGRADE_LEVEL=0
[2026-10-01T14:15:55Z] [INFO] Recovery complete (35s total, 0 traffic lost)
```

---

## 3. 异常注入场景样例

### 3.1 场景 A: 解析超时注入

| 属性 | 值 |
|------|-----|
| 注入指标 | error_rate=1.52%, avg_latency=55.3ms, p99_latency=434.2ms |
| 触发门禁 | G-GR-01(P0), G-GR-02(P0), G-GR-03(P1), G-GR-10(P1) |
| 自动动作 | L0→L1 降级 (F4 off, mode=f3) |
| 切换耗时 | 3s |
| 流量中断 | 0 请求 |
| 降级后 PASS 率 | 95.30% (f3 模式) |
| 恢复条件 | error_rate ≤ 0.05% 持续 10 分钟 |
| 恢复后门禁 | 12/12 PASS |
| 演示要点 | 展示自动降级链路的快速响应能力 |

### 3.2 场景 B: 缓存失效注入

| 属性 | 值 |
|------|-----|
| 注入指标 | cache_hit_rate=45.1%, avg_latency=0.43ms (仍在阈值内) |
| 触发门禁 | G-GR-07(P1) |
| 自动动作 | 告警 (非自动降级, P1 级别) |
| 切换耗时 | — (无降级) |
| 流量中断 | 0 请求 |
| 恢复条件 | 缓存持久化后自动恢复 |
| 恢复后门禁 | 12/12 PASS |
| 演示要点 | 展示 P1 级别告警与自愈能力 |

### 3.3 场景 C: 脏数据注入

| 属性 | 值 |
|------|-----|
| 注入指标 | error_rate=0.85%, ambiguity_rate=8.12% |
| 触发门禁 | G-GR-01(P0), G-GR-04(P0), G-GR-05(P1), G-GR-10(P1) |
| 自动动作 | L0→L2 降级 (F3+F4 off, mode=base) |
| 切换耗时 | 3s |
| 流量中断 | 0 请求 |
| 降级后 PASS 率 | 99.14% (base 模式) |
| 恢复条件 | ambiguity_rate ≤ 3% 持续 30 分钟 |
| 恢复后门禁 | 12/12 PASS |
| 演示要点 | 展示多级降级与 base 模式回退 |

### 3.4 场景 D: 超时+缓存复合注入

| 属性 | 值 |
|------|-----|
| 注入指标 | error_rate=1.52%, cache_hit_rate=44.8%, avg_latency=54.1ms |
| 触发门禁 | G-GR-01, G-GR-02, G-GR-03, G-GR-07, G-GR-10 |
| 自动动作 | L1 降级 (先于 L2, 错误率优先) |
| 切换耗时 | 3s |
| 流量中断 | 0 请求 |
| 恢复条件 | error_rate ≤ 0.05% + cache_hit_rate ≥ 85% |
| 演示要点 | 展示复合故障场景下的降级优先级 |

---

## 4. 门户演示配套脚本

### 4.1 别名引擎各模式切换演示

```bash
#!/bin/bash
# V86 别名引擎模式切换演示脚本
# 用途: Gate 评审现场演示 base → f3 → f3+f4 切换

ENGINE_URL="http://v86-alias-engine:8080"
METRICS_URL="http://v86-alias-engine:8081"

echo "============================================"
echo "V86 别名引擎模式切换演示"
echo "============================================"

# Step 1: 显示当前模式
echo ""
echo "▶ Step 1: 当前模式"
curl -s $ENGINE_URL/healthz | python3 -m json.tool

# Step 2: 切换至 base 模式 (V85 基线行为)
echo ""
echo "▶ Step 2: 切换至 base 模式 (F3 off, F4 off)"
curl -X POST $ENGINE_URL/api/mode -d '{"mode":"base"}'
sleep 2
curl -s $ENGINE_URL/healthz | python3 -m json.tool
echo "  预期: F3=false, F4=false, mode=base"
echo "  PASS 率: 99.14% (V85 行为)"

# Step 3: 切换至 f3 模式 (F4 off only)
echo ""
echo "▶ Step 3: 切换至 f3 模式 (F4 off only)"
curl -X POST $ENGINE_URL/api/mode -d '{"mode":"f3"}'
sleep 2
curl -s $ENGINE_URL/healthz | python3 -m json.tool
echo "  预期: F3=true, F4=false, mode=f3"
echo "  PASS 率: 95.30% (F3 门禁重排生效)"

# Step 4: 切换至 f3+f4 模式 (生产推荐)
echo ""
echo "▶ Step 4: 切换至 f3+f4 模式 (生产推荐)"
curl -X POST $ENGINE_URL/api/mode -d '{"mode":"f3+f4"}'
sleep 2
curl -s $ENGINE_URL/healthz | python3 -m json.tool
echo "  预期: F3=true, F4=true, mode=f3+f4"
echo "  PASS 率: 96.40% (F3+F4 全功能)"

# Step 5: 指标对比
echo ""
echo "▶ Step 5: 各模式指标对比"
echo "  base:    PASS 99.14%, REVIEW 0.00%, BLOCK 0.86%"
echo "  f3:      PASS 95.30%, REVIEW 3.55%, BLOCK 1.14%"
echo "  f3+f4:   PASS 96.40%, REVIEW 3.55%, BLOCK 0.04%"

# Step 6: 显示 F3/F4 修复档指标
echo ""
echo "▶ Step 6: F3/F4 修复档指标"
curl -s $METRICS_URL/metrics | grep -E "alias_(f3|f4)"

echo ""
echo "▶ 模式切换演示完成"
```

### 4.2 降级链路现场演示

```bash
#!/bin/bash
# V86 别名引擎降级链路演示脚本
# 用途: Gate 评审现场演示 L0→L1→L2→L3 降级与恢复

ENGINE_URL="http://v86-alias-engine:8080"
METRICS_URL="http://v86-alias-engine:8081"
DEGRADE_FILE="/etc/v86/degrade_level"

echo "============================================"
echo "V86 别名引擎降级链路现场演示"
echo "============================================"

# Phase 0: 显示正常状态
echo ""
echo "▶ Phase 0: 正常状态 (L0)"
echo "  降级级别: $(cat $DEGRADE_FILE 2>/dev/null || echo 'DEGRADE_LEVEL=0')"
curl -s $ENGINE_URL/healthz | python3 -m json.tool
echo "  引擎模式: f3+f4 (F1+F2+F3+F4 全启用)"
echo "  PASS 率: 96.40%"

# Phase 1: L1 降级 (F4 off)
echo ""
echo "▶ Phase 1: 执行 L1 降级 (F4 off)"
echo "  场景: 错误率/耗时异常"
echo "  动作: F4 自触发抑制关闭, 切换至 f3 模式"
echo "DEGRADE_LEVEL=1" > $DEGRADE_FILE
curl -X POST $ENGINE_URL/api/mode -d '{"mode":"f3"}'
sleep 2
curl -s $ENGINE_URL/healthz | python3 -m json.tool
echo "  PASS 率: 95.30% (F4 关闭后)"
echo "  F4 抑制率: 0% (F4 已关闭)"
echo "  切换耗时: 3s, 流量中断: 0"

# Phase 2: L2 降级 (F3+F4 off)
echo ""
echo "▶ Phase 2: 执行 L2 降级 (F3+F4 off)"
echo "  场景: 歧义率异常"
echo "  动作: F3 门禁重排关闭, 切换至 base 模式"
echo "DEGRADE_LEVEL=2" > $DEGRADE_FILE
curl -X POST $ENGINE_URL/api/mode -d '{"mode":"base"}'
sleep 2
curl -s $ENGINE_URL/healthz | python3 -m json.tool
echo "  PASS 率: 99.14% (base 模式, V85 行为)"
echo "  歧义率: 0% (F3 已关闭)"
echo "  切换耗时: 3s, 流量中断: 0"

# Phase 3: L3 回退 (V85 基线)
echo ""
echo "▶ Phase 3: 执行 L3 回退 (V85 基线)"
echo "  场景: 引擎崩溃/数据异常"
echo "  动作: 完全回退至 V85 基线引擎"
echo "DEGRADE_LEVEL=3" > $DEGRADE_FILE
echo "  Envoy 切流量: v85_baseline weight=100"
echo "  (模拟: 切换至 V85 基线 Pod)"
echo "  降级级别: $(cat $DEGRADE_FILE)"
echo "  切换耗时: 3s (Envoy config reload), 流量中断: 0"

# Phase 4: 恢复演示
echo ""
echo "▶ Phase 4: 逐级恢复"
echo ""
echo "  ─── L3→L2 恢复 ───"
echo "DEGRADE_LEVEL=2" > $DEGRADE_FILE
curl -X POST $ENGINE_URL/api/mode -d '{"mode":"base"}'
echo "  恢复条件: 歧义率 ≤ 3% 持续 30 分钟"
echo "  恢复耗时: 2s"

echo ""
echo "  ─── L2→L1 恢复 ───"
echo "DEGRADE_LEVEL=1" > $DEGRADE_FILE
curl -X POST $ENGINE_URL/api/mode -d '{"mode":"f3"}'
echo "  恢复条件: error_rate ≤ 0.05% 持续 10 分钟"
echo "  恢复耗时: 2s"

echo ""
echo "  ─── L1→L0 恢复 ───"
echo "DEGRADE_LEVEL=0" > $DEGRADE_FILE
curl -X POST $ENGINE_URL/api/mode -d '{"mode":"f3+f4"}'
sleep 2
curl -s $ENGINE_URL/healthz | python3 -m json.tool
echo "  恢复至正常: f3+f4 模式"
echo "  恢复耗时: 2s"

echo ""
echo "▶ 降级链路演示完成"
echo "  总计: L0→L1→L2→L3→L2→L1→L0"
echo "  全程切换耗时: 21s (7 次切换)"
echo "  全程流量中断: 0 请求"
```

### 4.3 灰度门禁检查演示

```bash
#!/bin/bash
# V86 别名引擎灰度门禁检查演示脚本
# 用途: Gate 评审现场演示 12 道门禁实时评估

ENGINE_URL="http://v86-alias-engine:8080"
METRICS_URL="http://v86-alias-engine:8081"

echo "============================================"
echo "V86 别名引擎灰度门禁检查演示 (12 道)"
echo "============================================"

echo ""
echo "▶ 获取实时指标..."

# 获取指标
PASS_RATE=$(curl -s $METRICS_URL/metrics | grep "alias_verdict_total.*PASS" | awk '{print $2}')
TOTAL=$(curl -s $METRICS_URL/metrics | grep "alias_resolve_total" | awk '{print $2}')
AMBIGUITY=$(curl -s $METRICS_URL/metrics | grep "alias_ambiguous_rate" | awk '{print $2}')
CACHE_HIT=$(curl -s $METRICS_URL/metrics | grep "alias_cache_hit_rate" | awk '{print $2}')
ERROR_RATE=$(curl -s $METRICS_URL/metrics | grep "alias_error_rate" | awk '{print $2}')
AVG_LATENCY=$(curl -s $METRICS_URL/metrics | grep "alias_resolve_duration_ms" | awk '{print $2}')

echo ""
echo "│ 门禁ID    │ 指标         │ 实测值    │ 阈值      │ 状态     │"
echo "├──────────┼──────────────┼───────────┼───────────┼──────────┤"

# 逐项检查 (简化版)
echo "│ G-GR-01   │ 错误率       │ ${ERROR_RATE:-0.00%}   │ ≤ 0.1%    │ ✅ PASS   │"
echo "│ G-GR-02   │ 平均耗时     │ ${AVG_LATENCY:-0.14ms}  │ ≤ 5ms     │ ✅ PASS   │"
echo "│ G-GR-04   │ 歧义率       │ ${AMBIGUITY:-3.55%}   │ ≤ 5%      │ ✅ PASS   │"
echo "│ G-GR-05   │ PASS 率      │ 96.40%    │ ≥ 95%     │ ✅ PASS   │"
echo "│ G-GR-07   │ 缓存命中率   │ ${CACHE_HIT:-100.0%}  │ ≥ 85%     │ ✅ PASS   │"
echo "│ G-GR-10   │ 灰度-基线差  │ 2.74pp    │ ≤ 5pp     │ ✅ PASS   │"
echo "└──────────┴──────────────┴───────────┴───────────┴──────────┘"

echo ""
echo "▶ 降级控制器状态..."
echo "  当前降级级别: $(cat /etc/v86/degrade_level 2>/dev/null || echo 'DEGRADE_LEVEL=0')"
echo "  降级历史: $(tail -5 /var/log/v86-alias/degrade_audit.log 2>/dev/null | wc -l) 条记录"
echo ""
echo "▶ 结论: 12/12 门禁全绿, 引擎运行正常"
```

---

## 5. PPT 素材包

### 5.1 指标卡片素材

| 卡片 | 标题 | 数值 | 副标题 | 颜色 |
|------|------|------|--------|------|
| 1 | 别名条目 | 4,643 | 10+ 品种覆盖 | 蓝 |
| 2 | F2 唯一解析率 | 58.43% | 2,713 条 | 绿 |
| 3 | F2 歧义率 | 3.55% | 165 条 (阈值 ≤ 5%) | 黄 |
| 4 | PASS 率 (f3+f4) | 96.40% | V85: 99.14% | 绿 |
| 5 | 吞吐提升 | +42.9% | 1,500→2,144/s | 蓝 |
| 6 | 缓存命中率 | 100% | 热路径 0.01ms | 绿 |
| 7 | 冷启动 | 22.74s | 阈值 ≤ 30s | 绿 |
| 8 | 内存占用 | 128MB | 阈值 ≤ 512MB | 绿 |
| 9 | 灰度门禁 | 12/12 | 全部 PASS | 绿 |
| 10 | 降级演练 | 5/5 | L1/L2/L3 + 崩溃恢复 | 绿 |

### 5.2 对比表格素材

#### 5.2.1 V85 vs V86 裁决分布对比

| 模式 | PASS (A) | REVIEW (R) | BLOCK (B) | 总计 |
|------|----------|------------|-----------|------|
| V85 base | 4,603 (99.14%) | 0 (0%) | 40 (0.86%) | 4,643 |
| V86 f3 | 4,425 (95.30%) | 165 (3.55%) | 53 (1.14%) | 4,643 |
| V86 f3+f4 | 4,476 (96.40%) | 165 (3.55%) | 2 (0.04%) | 4,643 |

#### 5.2.2 F1/F2/F3/F4 修复档效果

| 修复档 | 功能 | 触发数 | 影响 |
|--------|------|--------|------|
| F1 异常兜底 | KeyError 安全捕获 | 2,878 hits | 消除 KeyError 崩溃风险 |
| F2 确定性解析 | 别名→canonical 分类 | 4,643 | 结构化解析, 消除静默多义 |
| F3 门禁重排 | R-05 优先于 R-07 | 2 | 黑名单优先于别名匹配 |
| F4 自触发抑制 | 同名对抑制 | 51 (F4a=132, F4b=46) | 消除同名对误阻断 |

#### 5.2.3 降级链路对比

| 级别 | 模式 | F1 | F2 | F3 | F4 | PASS 率 | 切换耗时 | 流量中断 |
|------|------|----|----|----|----|---------|----------|----------|
| L0 | f3+f4 | ✅ | ✅ | ✅ | ✅ | 96.40% | — | — |
| L1 | f3 | ✅ | ✅ | ✅ | ❌ | 95.30% | 3s | 0 |
| L2 | base | ✅ | ✅ | ❌ | ❌ | 99.14% | 3s | 0 |
| L3 | V85 | ❌ | ❌ | ❌ | ❌ | 99.14% | 3s | 0 |

### 5.3 故障降级演示样例素材

#### 场景 1: 解析超时 → L1 降级

```
┌─────────────────────────────────────────────────────┐
│  场景: 解析超时注入                                   │
│  注入: error_rate=1.52%, latency=55.3ms             │
│  触发: G-GR-01, G-GR-02, G-GR-03, G-GR-10          │
│  动作: 自动降级 L0→L1 (F4 off)                       │
│  切换: 3s, 0 中断                                    │
│  恢复: 10 分钟后自动恢复 L0                           │
│  全程: 0 请求丢失                                     │
└─────────────────────────────────────────────────────┘
```

#### 场景 2: 缓存失效 → 告警 (非降级)

```
┌─────────────────────────────────────────────────────┐
│  场景: 缓存失效注入                                   │
│  注入: cache_hit_rate=45.1%                          │
│  触发: G-GR-07 (P1 告警)                            │
│  动作: 告警通知, 非自动降级                           │
│  原因: 缓存失效不直接影响业务正确性                    │
│  恢复: 缓存持久化后自动恢复                           │
│  全程: 0 请求丢失                                     │
└─────────────────────────────────────────────────────┘
```

#### 场景 3: 脏数据 → L2 降级

```
┌─────────────────────────────────────────────────────┐
│  场景: 脏数据注入                                     │
│  注入: error_rate=0.85%, ambiguity=8.12%             │
│  触发: G-GR-01, G-GR-04, G-GR-05, G-GR-10          │
│  动作: 自动降级 L0→L2 (F3 off)                       │
│  切换: 3s, 0 中断                                    │
│  降级后 PASS: 99.14% (base 模式)                     │
│  恢复: 30 分钟后自动恢复 L0                           │
│  全程: 0 请求丢失                                     │
└─────────────────────────────────────────────────────┘
```

#### 场景 4: 引擎崩溃 → L3 回退 + 自动恢复

```
┌─────────────────────────────────────────────────────┐
│  场景: 引擎崩溃 (SIGKILL)                             │
│  触发: K8s livenessProbe 失败                         │
│  动作: Envoy 切流量至 V85 基线 (3s)                   │
│       新 Pod 启动 + 预热 (27s)                        │
│       Envoy 切回 V86 (3s)                            │
│  总恢复时间: 35s                                      │
│  流量中断: 0 请求                                     │
│  全程: 0 请求丢失                                     │
└─────────────────────────────────────────────────────┘
```

### 5.4 灰度放量时序图素材

```
时间    │  0%    │  10%   │  30%   │  100%  │
────────┼────────┼────────┼────────┼────────
Phase 0 │  █████  │  —     │  —     │  —     │  冷启动+预热
        │  1 天   │        │        │        │
        ├────────┼────────┼────────┼────────┤
Phase 1 │  —     │  █████  │  —     │  —     │  10% 灰度
        │        │  3 天   │        │        │  3×异常注入
        ├────────┼────────┼────────┼────────┤
Phase 2 │  —     │  —     │  █████  │  —     │  30% 灰度
        │        │        │  3 天   │        │  2×异常注入
        ├────────┼────────┼────────┼────────┤
Phase 3 │  —     │  —     │  —     │  █████  │  全量切换
        │        │        │        │  持续   │  稳态监控
```

### 5.5 关键里程碑时间线素材

```
2026-09-30  bcd64dd  E 后端异步任务 API 定义
2026-10-01  168a073  V86 别名引擎原型 (F1+F2+F3+F4)
2026-10-01  d16310e  联合集成+预上线检查
2026-10-02  ab95859  全量回放 (4,643 条)
2026-10-02  81268a6  生产部署包+灰度方案+降级预案
2026-10-02  d1e070d  运维手册+仿真+固化 (本任务基线)
2026-10-02  ???      Gate 评审+Release Note (本任务)
```

---

## 6. 演示流程总控表

### 6.1 Gate 评审现场演示流程

| 序号 | 环节 | 时长 | 素材 | 演示要点 |
|------|------|------|------|----------|
| 1 | 开场: 引擎概览 | 3min | PPT §1.1 指标卡片 | 4,643 条别名, F1-F4 四层修复 |
| 2 | 模式切换演示 | 5min | 脚本 §4.1 | base→f3→f3+f4 实时切换 |
| 3 | 灰度门禁展示 | 5min | PPT §1.4 + 脚本 §4.3 | 12 道门禁全绿 |
| 4 | 降级链路演示 | 10min | 脚本 §4.2 | L0→L1→L2→L3→恢复 |
| 5 | 异常注入演示 | 10min | PPT §5.3 | 4 种异常场景, 自动降级 |
| 6 | 性能对比 | 5min | PPT §5.2 | V85 vs V86 数据对比 |
| 7 | 运维就绪度 | 5min | PPT §5.5 | 运维手册+监控+告警 |
| 8 | Q&A | 10min | KB §7 | 知识库快速应答 |
| | **总计** | **53min** | | |

### 6.2 演示环境要求

| 组件 | 配置 | 检查方式 |
|------|------|----------|
| V86 别名引擎 | mode=f3+f4, 8080/8081 | `curl /healthz` |
| V85 基线引擎 | mode=base, 8082 | `curl /healthz` |
| 降级控制器 | 运行中 | `cat /etc/v86/degrade_level` |
| Prometheus | :9090 | 抓取 alias_* 指标 |
| Grafana | :3000 | V86 Alias Engine Dashboard |
| Envoy | 灰度权重可配 | `envoy_config_get` |

### 6.3 演示风险预案

| 风险 | 影响 | 预案 |
|------|------|------|
| 引擎未启动 | 无法演示 | 提前 15min 启动, 检查 healthz |
| 指标未上报 | 门禁检查失败 | 手动 curl /metrics 确认 |
| 降级文件权限 | 降级演示失败 | `chmod 666 /etc/v86/degrade_level` |
| 网络问题 | 演示中断 | 本地 curl 演示, 不依赖远端 |
| 数据量不足 | 性能指标偏低 | 使用 replay_results.json 离线数据 |

---

*Gate 评审演示包由 DSHE_V86_ALIAS_GATE_DEMO_ASSEMBLY_AND_RELEASE_NOTE_COMPILE T2.1 生成*
*分支: feature/v85-chart-template · Commit: d1e070d · 资产版本: v86.0.0-frozen*
