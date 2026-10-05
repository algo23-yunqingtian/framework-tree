# V86-RC2 审计器 v3 生产环境参数剖面（T3.3）

> **工单**: 工单-HERMES / T3.3 审计器 v3 生产环境参数剖面
> **分支**: `feature/v85-chart-template` @ `1b3c6f2`
> **编制方**: HERMES (L3 审计方)
> **日期**: 2026-10-15
> **状态**: 📋 剖面定稿
>
> **载体**: `evidence_auditor_v3.py` (v3.0.0, 短路+增量优化版)
> **约束**: NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE

---

## 0. 概述

审计器 v3 基于 v2.1-plus（42 用例）新增两项优化：
- **短路判定**：P0 批 CRITICAL 立即终止，跳过后续批次，失败包加速 2x
- **增量校验**：指纹未变时复用缓存，命中加速 **71.7x**（0.197ms vs 14.128ms）

本剖面按三个阶段（G0 影子 / G1~G4 灰度 / G5 全量）定义独立配置，并说明**<50call 小包跳过短路**的调度策略。

---

## 1. 配置参数总览

### 1.1 v3 核心参数

| 参数 | 默认值 | 含义 | 可调范围 |
|------|--------|------|----------|
| `enable_short_circuit` | True | 短路判定开关 | True / False |
| `enable_incremental` | False | 增量缓存开关 | True / False |
| `perf_budget_seconds` | 1.0 | 单次审计超时（秒） | 0.5 ~ 5.0 |
| `perf_budget_calls` | 256 | 性能预算最大 call 数 | 128 ~ 1024 |
| `incremental_cache_size` | 1000 | 增量缓存条目上限 | 100 ~ 10000 |
| `incremental_cache_ttl` | 3600 | 缓存过期时间（秒） | 300 ~ 86400 |
| `incremental_sample_rate` | 0.05 | 增量抽样交叉校验比例 | 0.01 ~ 0.50 |
| `dep_flap_threshold` | 2 | DEP 抖动检测阈值（次） | 1 ~ 5 |
| `real_fetchable_threshold` | 1.0 | G-06 真实可取数率阈值 | 0.8 ~ 1.0 |
| `batch_schedule` | auto | 批次调度策略 | auto / force_p0 / force_full |

### 1.2 批次定义

```python
BATCH_P0 = ["robustness", "contract", "perf_budget"]           # 契约+容错+性能
BATCH_P1 = ["script_audit", "bridge_rate_g06"]                  # Gate 强制项
BATCH_P2 = ["dual_evidence", "trace_fingerprint", "bridge_rate",
            "l2_independent", "cv_caliber", "dep_g09"]          # 双证据+桥接+独立性
BATCH_P3 = ["legacy_caliber", "dep_classification", "retire_flag"]  # 观测项

SHORT_CIRCUIT_LEVELS = (CRITICAL,)  # P0 批出现 CRITICAL 即短路
```

---

## 2. G0 影子测试配置（0% 流量，仅观测）

### 2.1 配置剖面

```python
G0_PROFILE = {
    # 审计模式
    "enable_short_circuit": True,
    "enable_incremental": True,        # G0 允许增量，验证缓存行为
    "batch_schedule": "auto",          # 自动路由

    # 性能预算（宽松，影子阶段允许慢一点收集数据）
    "perf_budget_seconds": 2.0,        # 影子阶段 2 秒超时
    "perf_budget_calls": 512,          # 允许大包

    # 增量缓存（G0 重点验证缓存行为）
    "incremental_cache_size": 5000,    # 大缓存，收集足够指纹样本
    "incremental_cache_ttl": 86400,    # 24 小时，影子期长缓存
    "incremental_sample_rate": 0.10,   # 10% 抽样交叉校验（高于灰度）

    # 审计阈值（G0 宽松，观测而非阻断）
    "real_fetchable_threshold": 0.80,  # 影子阶段 80% 即可
    "dep_flap_threshold": 3,           # 影子阶段抖动阈值 3 次

    # 调度策略
    "small_pkg_skip_circuit": True,    # <50call 跳过短路
    "max_concurrent": 1,               # 影子阶段单线程
}
```

### 2.2 G0 设计理由

| 参数 | 理由 |
|------|------|
| `incremental=True` | G0 是验证增量缓存正确性的关键阶段 |
| `sample_rate=0.10` | 影子阶段需要更高抽样率确保缓存与全量一致 |
| `threshold=0.80` | 影子阶段不阻断，仅观测数据质量 |
| `concurrent=1` | 影子阶段数据量小，无需并发 |

### 2.3 G0 预期行为

```
G0 影子测试 (0%, 0 品种)
    │
    ├── 接收 DSHB/DSHE 上报包
    ├── 自动路由: >50call → v3 短路, <50call → v2_plus 全量
    ├── 增量缓存命中率统计
    ├── 抽样交叉校验 (10%)
    └── 产出: 审计延迟分布 + 缓存命中率 + 短路率 + 数据质量报告
```

---

## 3. G1~G4 灰度配置（1%~50% 流量）

### 3.1 配置剖面

```python
G1_G4_PROFILE = {
    # 审计模式
    "enable_short_circuit": True,      # 灰度阶段启用短路，保护性能
    "enable_incremental": True,        # 灰度阶段启用增量，处理重复上报
    "batch_schedule": "auto",          # 自动路由

    # 性能预算（中等严格）
    "perf_budget_seconds": 1.0,        # 标准 1 秒超时
    "perf_budget_calls": 256,          # 标准 256 call 预算

    # 增量缓存
    "incremental_cache_size": 2000,    # 中等缓存
    "incremental_cache_ttl": 1800,     # 30 分钟，灰度期短缓存
    "incremental_sample_rate": 0.05,   # 5% 抽样交叉校验

    # 审计阈值（逐步收紧）
    # G1: 0.90 → G2: 0.95 → G3: 0.98 → G4: 0.99
    "real_fetchable_threshold": 0.95,  # 默认 G2，按阶段调整
    "dep_flap_threshold": 2,           # 标准 2 次

    # 调度策略
    "small_pkg_skip_circuit": True,    # <50call 跳过短路
    "max_concurrent": 1,               # 单线程（GIL 优化）
}
```

### 3.2 灰度阶段阈值递进

| 阶段 | 品种数 | 流量 | `real_fetchable_threshold` | `perf_budget_seconds` | `sample_rate` |
|------|--------|------|---------------------------|----------------------|---------------|
| G1 单品种 | 1 (PB) | 1% | 0.90 | 1.0 | 0.05 |
| G2 小范围 | 7 | 5% | 0.95 | 1.0 | 0.05 |
| G3 中范围 | 28 | 20% | 0.98 | 0.8 | 0.03 |
| G4 大范围 | 42 | 50% | 0.99 | 0.8 | 0.03 |

### 3.3 灰度阶段设计理由

- **阈值逐步收紧**：G1 宽松（0.90）给 DSHB 修复窗口，G4 严格（0.99）确保质量
- **G3 开始降低超时**：G3 流量 20%，性能压力增大，超时降至 0.8s
- **抽样率递减**：G1/G2 5%（充分验证），G3/G4 3%（降低开销）

---

## 4. G5 全量配置（100% 流量）

### 4.1 配置剖面

```python
G5_PROFILE = {
    # 审计模式
    "enable_short_circuit": True,      # 全量必须启用短路
    "enable_incremental": True,        # 全量启用增量
    "batch_schedule": "auto",          # 自动路由

    # 性能预算（严格）
    "perf_budget_seconds": 0.8,        # 0.8 秒超时
    "perf_budget_calls": 256,          # 标准预算

    # 增量缓存
    "incremental_cache_size": 5000,    # 全量需要大缓存
    "incremental_cache_ttl": 900,      # 15 分钟，高频更新
    "incremental_sample_rate": 0.02,   # 2% 抽样（最低）

    # 审计阈值（最严格）
    "real_fetchable_threshold": 0.99,  # 99% 真实可取数率
    "dep_flap_threshold": 2,           # 标准 2 次

    # 调度策略
    "small_pkg_skip_circuit": True,    # <50call 跳过短路
    "max_concurrent": 1,               # 单线程（GIL 优化）
    "batch_size": 32,                  # 批量审计，每批 32 包
}
```

### 4.2 G5 设计理由

| 参数 | 理由 |
|------|------|
| `threshold=0.99` | 全量阶段必须保证 99% 真实可取数 |
| `timeout=0.8s` | 全量流量下性能最关键 |
| `cache_ttl=900s` | 高频数据更新，缓存不宜过长 |
| `sample_rate=0.02` | 2% 足够保证一致性，降低开销 |
| `batch_size=32` | 批量提交减少 fsync 次数 |

---

## 5. 小包跳过短路优化策略

### 5.1 问题背景

上一轮实测发现：**<0.1ms 的极小包短路无收益甚至略慢**。

| 场景 | v2_plus 全量 | v3 短路 | 加速 |
|------|-------------|---------|------|
| 损坏根对象 (list) | 0.0088ms | 0.0150ms | **0.6x（反而慢）** |
| 空 dict 契约缺失 | 0.0921ms | 0.0961ms | 1.0x（持平） |
| calls 类型错乱 | 0.0619ms | 0.0645ms | 1.0x（持平） |

**根因**：短路是"用调度开销换检测跳过"。当检测本身极便宜（<0.1ms）时，批次调度 + 跳过集合维护的固定开销超过节省的检测成本。

### 5.2 调度策略

```python
def route_auditor(evidence):
    """按包形态路由到合适的审计器。"""
    
    # 预判：成本 < 1μs
    is_dict = isinstance(evidence, dict)
    call_count = len(evidence.get("calls", [])) if is_dict else 0
    
    # <50 call: 用 v2_plus 全量（短路开销 > 收益）
    if is_dict and call_count < 50:
        return "v2_plus"
    
    # >=50 call: 用 v3 短路（2x 加速）
    if is_dict and call_count >= 50:
        return "v3"
    
    # 非 dict: 用 v3（损坏包短路虽慢但保护后续批次）
    return "v3"
```

### 5.3 路由决策矩阵

| 包形态 | call 数 | 路由 | 理由 |
|--------|---------|------|------|
| 正常包 | <50 | v2_plus | 短路开销 > 收益 |
| 正常包 | ≥50 | **v3 短路** | 2x 加速 |
| 失败包 | <50 | v2_plus | 失败包本身就快，无需短路 |
| 失败包 | ≥50 | **v3 短路** | 短路跳过半数检测，2x 加速 |
| 损坏包 | 任意 | v3 | 保护后续批次不被污染 |
| 重复上报 | 任意 | **v3 增量** | 缓存命中 71.7x |

### 5.4 小包阈值选择

| 阈值 | 理由 |
|------|------|
| < 32 call | 过于保守，浪费 32~50 call 范围的短路收益 |
| **< 50 call** | ✅ 实测拐点：32call 加速 1.99x，但仍接近 1x |
| < 100 call | 过于激进，100call 短路收益 2x，不应跳过 |

**推荐**: 默认 `< 50`，可根据实际负载调至 30~80 范围。

---

## 6. 增量缓存策略

### 6.1 缓存指纹算法

```python
# 8 字段指纹
fingerprint = MD5(
    contract_version + "|" +
    fingerprint + "|" +
    run_id + "|" +
    audit_fingerprint + "|" +
    dep_status_sequence + "|" +
    calls_count + "|" +
    calls_status_distribution + "|" +
    real_fetchable_rate_sum
)
```

### 6.2 缓存生命周期

```
新证据包到达
    │
    ├── 计算指纹
    │
    ├── 指纹命中缓存？
    │       ├── Yes → 返回缓存结果 (0.197ms, 71.7x 加速)
    │       │         └── 抽样交叉校验 (sample_rate)
    │       │               └── 不一致 → 标记漂移，重算
    │       │
    │       └── No → 全量审计 (7~14ms)
    │                 └── 写入缓存 (FIFO 淘汰)
    │
    └── 缓存已满？
            ├── Yes → FIFO 淘汰最旧条目
            └── No  → 直接写入
```

### 6.3 缓存漂移检测

**风险**: 审计规则升级后，旧缓存可能不再适用。

**防护**: 抽样交叉校验

```python
# 每次缓存命中时，以 sample_rate 概率执行全量审计并比对
if cache_hit and random.random() < sample_rate:
    full_result = full_audit(evidence)
    if cache_result != full_result:
        # 标记漂移
        drift_detected = True
        # 清除该条目的缓存
        cache.invalidate(fingerprint)
        # 告警
        log("CACHE_DRIFT: fingerprint=%s sample_rate=%.2f", fp, rate)
```

**自测验证**: 人为篡改缓存后，抽样校验成功发现漂移（`drift_found=1`）。

### 6.4 缓存大小与 TTL 选择

| 阶段 | 缓存大小 | TTL | 理由 |
|------|----------|-----|------|
| G0 影子 | 5000 | 24h | 收集样本，长 TTL |
| G1~G2 灰度 | 2000 | 30m | 中等，适中 |
| G3~G4 灰度 | 2000 | 30m | 同上 |
| G5 全量 | 5000 | 15m | 大缓存，短 TTL |

---

## 7. 并发与内存上限

### 7.1 并发策略

**实测结论**：审计是纯 CPU 密集型，**单线程吞吐最优**（16 线程反而慢 14.3%）。

| 阶段 | 并发数 | 理由 |
|------|--------|------|
| G0 影子 | 1 | 数据量小，无需并发 |
| G1~G4 灰度 | 1 | GIL 优化，单线程最优 |
| G5 全量 | 1 | 批量提交替代并发 |

**超大规模场景**（> 10000 包/分钟）：使用多进程（`multiprocessing`）替代多线程。

### 7.2 内存上限

| 参数 | 值 | 计算依据 |
|------|-----|----------|
| 单包内存（256 call） | ~200 KB | 实测 175 KB |
| 增量缓存 2000 条目 | ~8 MB | 2000 × 4 KB（缓存元数据） |
| 批量缓冲 32 包 | ~6 MB | 32 × 200 KB |
| **总内存** | **~15 MB** | 可接受 |

**生产环境建议**:
- 审计进程内存限制: **256 MB**（预留 16x 余量）
- 缓存大小上限: **10000 条目**（约 40 MB）
- 单批处理上限: **128 包**（约 25 MB）

---

## 8. 超时与降级策略

### 8.1 超时层级

```
审计超时 (perf_budget_seconds)
    │
    ├── 未超时 → 正常返回
    │
    └── 超时 → 标记超时事件
                │
                ├── PERF-GUARD 告警
                ├── 返回超时结果 (不阻断)
                └── 记录超时包特征
```

### 8.2 降级策略

| 触发条件 | 降级动作 | 恢复条件 |
|----------|----------|----------|
| 审计超时率 > 10% | 降低 sample_rate 至 0.01 | 超时率 < 5% |
| 审计超时率 > 30% | 关闭增量缓存（减少指纹计算） | 超时率 < 15% |
| 审计超时率 > 50% | 关闭短路（全量审计更稳定） | 超时率 < 25% |
| 内存使用 > 80% | 降低缓存大小至 500 | 内存 < 60% |

### 8.3 超时阈值选择

| 阶段 | `perf_budget_seconds` | 理由 |
|------|----------------------|------|
| G0 | 2.0 | 影子阶段宽松 |
| G1 | 1.0 | 标准 |
| G2~G4 | 1.0 → 0.8 | 逐步收紧 |
| G5 | 0.8 | 全量严格 |

---

## 9. 调度器集成示例

### 9.1 生产调度器代码骨架

```python
class AuditScheduler:
    def __init__(self, profile: dict):
        self.profile = profile
        self.v2 = PlusAuditor()  # v2_plus 全量
        self.v3 = V3Auditor()     # v3 短路
        self.incr = IncrementalAuditor(
            cache_size=profile["incremental_cache_size"],
            cache_ttl=profile["incremental_cache_ttl"],
            sample_rate=profile["incremental_sample_rate"],
        )
        self.store = WALStore("/data/events.db")

    def process(self, evidence: dict) -> AuditResult:
        # 1. 路由决策
        route = self._route(evidence)
        
        # 2. 增量缓存检查
        if self.profile["enable_incremental"]:
            cached = self.incr.get(evidence)
            if cached:
                return cached
        
        # 3. 执行审计
        if route == "v3":
            auditor = self.v3
        else:
            auditor = self.v2
        
        result = auditor.audit(evidence)
        
        # 4. 写入缓存
        if self.profile["enable_incremental"]:
            self.incr.put(evidence, result)
        
        # 5. 事件存储
        self.store.append_events(result.events)
        
        return result

    def _route(self, evidence):
        is_dict = isinstance(evidence, dict)
        calls = len(evidence.get("calls", [])) if is_dict else 0
        skip_circuit = self.profile.get("small_pkg_skip_circuit", True)
        
        if skip_circuit and is_dict and calls < 50:
            return "v2_plus"
        return "v3"
```

---

## 10. 配置版本管理

### 10.1 配置版本号

| 版本 | 阶段 | 日期 | 变更 |
|------|------|------|------|
| v3-profile-0.1 | G0 影子 | 2026-10-15 | 初始剖面 |
| v3-profile-0.2 | G1~G4 灰度 | 2026-10-15 | 灰度阶段配置 |
| v3-profile-0.3 | G5 全量 | 2026-10-15 | 全量配置 |

### 10.2 配置变更流程

```
修改配置剖面
    │
    ├── 1. 更新版本号 (v3-profile-0.X)
    ├── 2. 在 staging 环境验证 (--self-test + --perf-bench)
    ├── 3. 提交三方评审 (DSHB + DSHE + HERMES)
    ├── 4. 更新 STATUS.md 变更记录
    └── 5. 灰度切换 (G1 先切, G2 次之)
```

---

## 11. 配置对照速查表

| 参数 | G0 影子 | G1 灰度 | G2 灰度 | G3 灰度 | G4 灰度 | G5 全量 |
|------|---------|---------|---------|---------|---------|---------|
| `enable_short_circuit` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `enable_incremental` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `perf_budget_seconds` | 2.0 | 1.0 | 1.0 | 0.8 | 0.8 | 0.8 |
| `perf_budget_calls` | 512 | 256 | 256 | 256 | 256 | 256 |
| `cache_size` | 5000 | 2000 | 2000 | 2000 | 2000 | 5000 |
| `cache_ttl` | 86400 | 1800 | 1800 | 1800 | 1800 | 900 |
| `sample_rate` | 0.10 | 0.05 | 0.05 | 0.03 | 0.03 | 0.02 |
| `real_fetchable_threshold` | 0.80 | 0.90 | 0.95 | 0.98 | 0.99 | 0.99 |
| `dep_flap_threshold` | 3 | 2 | 2 | 2 | 2 | 2 |
| `small_pkg_skip_circuit` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `max_concurrent` | 1 | 1 | 1 | 1 | 1 | 1 |

---

*本剖面基于 `evidence_auditor_v3.py` (v3.0.0) 实测数据编制。所有阈值和参数均可根据生产环境实际负载调整，调整前应在 staging 环境验证。*
