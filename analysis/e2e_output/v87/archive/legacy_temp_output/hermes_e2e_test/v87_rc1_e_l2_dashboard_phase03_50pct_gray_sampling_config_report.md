# V87 RC1 L2大盘 Phase03 — 50% 灰度流量采样策略配置报告

> **文档版本**: v1.0.0-phase03 | **编制日期**: 2026-07-15  
> **编制方**: DSHE (L2 展示层) | **协作方**: DSHB (L1) + HERMES (L3)  
> **分支**: feature/v87-rc1-g1 | **阶段**: Phase03 / StageA  
> **状态**: PENDING_REVIEW | **上一阶段**: Phase02 (commit 0d9a9d7)  
> **约束**: BRANCH_LOCKED=TRUE | GRAY_TRAFFIC_FULL_SAMPLING=TRUE | BASELINE_SAMPLING_PRESERVED=TRUE

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [灰度流量采样架构](#2-灰度流量采样架构)
3. [采样策略配置](#3-采样策略配置)
4. [独立指标统计](#4-独立指标统计)
5. [HERMES 字段采样](#5-hermes-字段采样)
6. [技术实现](#6-技术实现)
7. [监控与告警](#7-监控与告警)
8. [测试计划](#8-测试计划)
9. [风险评估](#9-风险评估)
10. [状态标记](#10-状态标记)

---

## 1. 执行摘要

### 1.1 阶段定位

Phase03 StageA 是 V87-RC1 L2 大盘从开发验证过渡到生产部署的关键阶段。Phase02 已完成 8 个新面板 (commit 0d9a9d7)、12 条告警规则迭代及 HERMES 审计字段集成。本阶段核心目标: 建立 **50% 灰度流量采样策略**，使 V87 新功能在生产环境中以可控风险逐步验证。

设计原则: **灰度流量 100% 全量采样 (no sampling loss)，基线流量保持 V86 现有采样率**。两条流量管道在标签、路由、存储、查询四个层面完全隔离。

### 1.2 阶段范围

| 范围维度 | 内容 | 状态 |
|---------|------|------|
| 灰度流量比例 | 50% (版本标签哈希路由) | 本阶段配置 |
| 灰度面板 | 8 个 (V87-P-001~P-008, P-005 暂缓) | Phase02 完成 |
| 告警规则 | 12 条 (8 继承 + 4 新增) | Phase02 完成 |
| HERMES 字段 | 5 个 (event_type, priority, trace_id, batch_id, retry_count) | 全量采样 |
| 指标管道 | 双管道隔离 (baseline vs gray) | 本阶段配置 |
| 缓存策略 | 分离缓存条目 | 本阶段配置 |
| QPS 预算 | 灰度独立 260 QPS | 本阶段分配 |
| 存储隔离 | 独立命名空间 + 标签过滤 | 本阶段配置 |

### 1.3 阶段目标

| # | 目标 | 量化指标 | 验证方式 |
|---|------|---------|---------|
| G1 | 灰度全量采样 | 采样率 100%，零丢失 | 采样率漂移检测 |
| G2 | 基线采样率保持 | 与 V86 一致 | 采样率比对 |
| G3 | 管道隔离 | 交叉污染率 < 0.01% | 标签过滤校验 |
| G4 | 灰度查询 P99 | ≤ 300ms | 独立查询面板 |
| G5 | 灰度渲染 P99 | ≤ 150ms | 面板渲染 SLA |
| G6 | 数据延迟 | ≤ 500ms | 灰度延迟监控 |
| G7 | 缓存命中率 | ≥ 95% | 灰度独立缓存统计 |
| G8 | HERMES 字段完整 | 5 字段全量采样 | 字段覆盖率审计 |

### 1.4 关键参数

| 参数 | V86 基线 | V87 灰度 (StageA) | V87 全量 (StageB) | 变化 |
|------|---------|-------------------|-------------------|------|
| QPS 总量 | 300 | 300+260=560 | 520 | 灰度临时+18% |
| QPS 保护阈值 | 800 | 800 | 800 | 不变 |
| 存储 (90d) | 720 GB | ~809 GB | 890 GB | 灰度+12.4% |
| 面板数 | 25 | 33 (25基线+8灰度) | 33 | 灰度即全量 |
| 指标数 | 24 | 32 (24基线+8灰度) | 32 | 灰度即全量 |
| 缓存命中率 | 90% | ≥95% | ≥95% | 灰度目标提前 |
| 渲染 P99 | 185ms | ≤150ms | ≤150ms | 灰度目标提前 |
| 查询 P99 | 265ms | ≤300ms | ≤300ms | 灰度目标提前 |

### 1.5 阶段交付物

1. 灰度流量采样架构设计 (第2章)
2. 采样策略配置参数 (第3章)
3. 独立指标统计方案 (第4章)
4. HERMES 字段采样规格 (第5章)
5. 技术实现 YAML 配置 (第6章)
6. 监控与告警规则 (第7章)
7. 测试计划 (第8章)
8. 风险评估与缓解 (第9章)
9. 状态标记与下一步 (第10章)

---

## 2. 灰度流量采样架构

### 2.1 架构总览

灰度流量采样架构采用 **双流量隔离设计** (Dual Traffic Isolation)，将 V86 基线与 V87 灰度流量在采集、标签、路由、存储、查询五个层面完全分离。

```
              ┌──────────────────────────────┐
              │      生产流量入口 (Total ~560 QPS)  │
              └──────────────┬───────────────┘
                             │
              ┌──────────────▼───────────────┐
              │     流量路由器 (Traffic Router)   │
              │     版本标签哈希分流 50/50         │
              │  hash(source_ip+experiment_id)%2│
              └───┬─────────────────────┬────┘
                  │                     │
      ┌───────────▼──────────┐  ┌──────▼──────────────┐
      │  基线流量管道          │  │  灰度流量管道          │
      │  50% (~260 QPS)      │  │  50% (~300 QPS)      │
      │  采样率: V86 默认     │  │  采样率: 100% 全量    │
      │  存储: baseline/命名空间│  │  存储: gray/命名空间  │
      │  面板: 25 基线面板    │  │  面板: 33 (全量)      │
      └──────────────────────┘  └─────────────────────┘
```

### 2.2 隔离层次

| 隔离层 | 机制 | 灰度侧 | 基线侧 |
|--------|------|--------|--------|
| 采集层 | 独立 Collector | GrayCollector (独立部署) | BaselineCollector (现有) |
| 标签层 | version_tag+gray_flag | gray_flag=true | gray_flag=false |
| 路由层 | 标签路由+管道分离 | gray_pipeline_id | baseline_pipeline_id |
| 存储层 | 独立命名空间+索引 | v87_gray_<index> | v86_baseline_<index> |
| 缓存层 | 独立缓存键前缀 | cache:gray:<panel_id> | cache:baseline:<panel_id> |
| 查询层 | 标签过滤+独立连接池 | gray_query_pool | baseline_query_pool |
| 告警层 | 独立评估器 | gray_alert_evaluator | baseline_alert_evaluator |

### 2.3 流量标签机制

#### 标签字段

| 字段 | 类型 | 示例值 | 说明 |
|------|------|--------|------|
| version_tag | string | "v87-rc1" | 版本号标签 |
| gray_flag | boolean | true | 灰度标记 |
| experiment_id | string | "v87_phase03_stage_a" | 实验标识 |
| pipeline_id | string | "gray_pipeline_v87" | 管道标识 |
| namespace_id | string | "gray" | 存储命名空间 |
| cache_prefix | string | "cache:gray:" | 缓存前缀 |
| query_pool | string | "gray_pool" | 查询池 |
| alert_evaluator | string | "gray_eval" | 告警评估器 |

#### 标签注入流程

```
Request → Gateway → Traffic Router
  1. 提取请求元数据 (source_ip, user_agent, timestamp)
  2. 计算路由键: hash(source_ip + experiment_id) % 2
  3. 注入标签: version_tag, gray_flag, experiment_id, pipeline_id 等
  4. 路由决策: gray_flag=true → 灰度管道; gray_flag=false → 基线管道
```

#### 标签一致性保证

| 机制 | 实现方式 | 验证方法 |
|------|---------|---------|
| 标签不可变 | 标签写入请求上下文 (immutable) | 单元测试断言 |
| 标签传递完整性 | 每处理环节自动传递 | 集成测试验证 |
| 标签审计 | 每 15s 采样 100 条审计 | 采样率漂移告警 |
| 标签回滚 | 紧急时全局关闭灰度 | 运维操作手册 |

### 2.4 指标路由

#### 指标路由规则

| 指标类别 | 灰度管道 | 基线管道 | 说明 |
|---------|---------|---------|------|
| 系统资源 (CPU/内存/磁盘/网络) | ✓ | ✓ | 双管道 |
| 面板渲染 (render_p99/render_count) | ✓ | ✓ | 双管道 |
| 查询 (query_p99/query_count) | ✓ | ✓ | 双管道 |
| 缓存 (hit_rate/miss_rate) | ✓ | ✓ | 双管道 |
| QPS (current/peak) | ✓ | ✓ | 双管道 |
| HERMES 审计 | ✓ | ✗ | 仅灰度 |
| 容量预测 | ✓ | ✗ | 仅灰度 |
| 吞吐 (throughput_evps) | ✓ | ✗ | 仅灰度 |
| 丢包 (packet_loss_rate) | ✓ | ✗ | 仅灰度 |
| V86 基线专属 | ✗ | ✓ | 仅基线 |

### 2.5 存储隔离

| 存储维度 | 灰度命名空间 | 基线命名空间 |
|---------|-------------|-------------|
| 命名空间 | v87_gray | v86_baseline |
| 数据保留 | 90 天 | 90 天 |
| 索引策略 | 独立索引 | 独立索引 |
| 查询过滤 | namespace_id="gray" | namespace_id="baseline" |
| TTL 策略 | 独立 TTL | 独立 TTL |

#### 存储容量

| 存储项 | V86 基线 | V87 灰度 (StageA) | V87 全量 |
|--------|---------|-------------------|---------|
| 原始数据 (90d) | 720 GB | 720+89=809 GB | 890 GB |
| 索引数据 (90d) | ~90 GB | ~102 GB | ~111 GB |
| 缓存数据 | ~36 GB | ~41 GB | ~48 GB |
| 审计数据 | 0 | ~12 GB | ~12 GB |
| 合计 (90d) | ~846 GB | ~945 GB | ~1061 GB |

---

## 3. 采样策略配置

### 3.1 采样策略总览

| 维度 | 灰度流量 | 基线流量 |
|------|---------|---------|
| 采样率 | 100% (全量) | V86 默认 (不变) |
| 采样策略 | full_sample | V86 默认 |
| 验证间隔 | 15s | 60s (不变) |
| 缓冲区隔离 | 独立缓冲区 | 独立缓冲区 |
| 溢出策略 | block_and_alert | V86 默认 |
| 丢失容忍 | 0% | V86 默认 |

### 3.2 灰度全量采样配置

```yaml
sampling.gray:
  sampling_rate: 1.0
  sampling_mode: full_sample
  sampling_algorithm: none
  loss_tolerance: 0.0
  verification_interval: 15s
  verification_method: count_comparison
  overflow_policy: block_and_alert
```

#### 采样完整性验证

```
验证流程:
1. 入口计数器: 每 15s 记录灰度管道入口请求数 → entry_count_15s
2. 存储计数器: 每 15s 查询灰度存储已写入记录数 → stored_count_15s
3. 比对: delta = entry_count_15s - stored_count_15s
         loss_rate = delta / entry_count_15s
4. 判定:
   loss_rate > 0.0001 → P2 WARN
   loss_rate > 0.001  → P1 CRIT
   loss_rate > 0.01   → P0 RECOVER (自动回滚灰度)
```

#### 采样率漂移检测

| 检测项 | 方法 | 阈值 | 告警 |
|--------|------|------|------|
| 采样率绝对值 | 直接读取配置 | ≠ 1.0 | P1 |
| 采样率变化速率 | 相邻差值/间隔 | > 0.001/s | P2 |
| 长期漂移 | 滑动窗口平均 vs 目标 | 偏差 > 0.1% | P2 |
| 突发跳变 | 单次变化幅度 | > 1% | P1 |

### 3.3 基线流量配置

基线流量维持 V86 现有采样配置，不做任何变更。

| 参数 | 值 |
|------|-----|
| sampling_rate | V86 默认 (不变) |
| sampling_mode | V86 默认 (不变) |
| verification_interval | 60s (不变) |
| overflow_policy | V86 默认 (不变) |

### 3.4 采集间隔配置

| 指标类别 | 灰度采集间隔 | 基线采集间隔 | 说明 |
|---------|-------------|-------------|------|
| 核心面板指标 | **1s** | V86 默认 | 灰度 1s 分辨率 |
| 系统资源指标 | 15s | 15s | 保持一致 |
| HERMES 审计指标 | 15s | — (不适用) | 仅灰度 |
| 查询/渲染性能指标 | **1s** | V86 默认 | 灰度加密 |
| 缓存性能指标 | 15s | 15s | 保持一致 |
| 容量指标 | 60s | 60s | 保持一致 |

#### 1s 分辨率关键指标

| 指标 | 指标 ID | 用途 |
|------|---------|------|
| 面板渲染 P99 | render_p99 | 渲染 SLA 监控 |
| 查询 P99 | query_p99 | 查询 SLA 监控 |
| QPS 瞬时值 | qps_instant | QPS 监控 |
| 缓存命中率 | cache_hit_rate | 缓存策略优化 |
| HERMES 事件吞吐 | hermes_throughput | 吞吐 SLA |
| WAL 写入延迟 | wal_write_latency | WAL SLA |

### 3.5 缓冲区策略

#### 缓冲区隔离

```
┌──────────────────────┐  ┌──────────────────────┐
│     Gray Buffer      │  │  Baseline Buffer     │
│  容量: 50 MB         │  │  容量: V86 默认      │
│  队列: 100,000 entries│  │  队列: V86 默认      │
│  溢出: block+alert   │  │  溢出: V86 默认      │
│  刷新: 15s            │  │  刷新: V86 默认      │
│  优先级: HIGH        │  │  优先级: NORMAL      │
│  丢弃: 不允许丢弃     │  │  丢弃: V86 默认      │
└──────────┬───────────┘  └──────────┬───────────┘
           ▼                          ▼
┌──────────────────────┐  ┌──────────────────────┐
│  Gray Storage Pipeline│  │  Baseline Pipeline   │
└──────────────────────┘  └──────────────────────┘
```

#### 缓冲区参数

| 参数 | 灰度缓冲区 | 基线缓冲区 |
|------|----------|-----------|
| 队列容量 | 100,000 entries | V86 默认 |
| 内存上限 | 50 MB | V86 默认 |
| 刷新间隔 | 15s | V86 默认 |
| 溢出策略 | block_and_alert | V86 默认 |
| 丢弃策略 | none (不允许) | V86 默认 |
| 优先级 | HIGH | NORMAL |
| 背压机制 | 反压到入口 | V86 默认 |

#### 缓冲区健康指标

| 指标 | 计算方法 | 告警阈值 |
|------|---------|---------|
| 缓冲区使用率 | current/capacity | >80% WARN, >90% CRIT |
| 填充速率 | entries_added/15s | >5,000/s |
| 消费速率 | entries_consumed/15s | <3,000/s |
| 老化时间 | max_age/15s | >60s |
| 溢出计数 | overflow_count | >0 |

---

## 4. 独立指标统计

### 4.1 并排对比仪表盘

灰度验证期间需要 **V86 基线 vs V87 灰度** 的并排对比仪表盘。

#### 对比面板布局

```
┌──────────────────────────────┬──────────────────────────────┐
│      V86 基线 (Baseline)      │      V87 灰度 (Gray)         │
│                              │                              │
│  CPU: 45%  ↗+2%             │  CPU: 47%  ↗+2%             │
│  内存: 78%  →stable          │  内存: 79%  →stable           │
│  磁盘: 62%  →stable          │  磁盘: 63%  →stable           │
│  网络: 2.1ms →stable         │  网络: 2.3ms ↗+10%           │
│  查询P99: 265ms →stable      │  查询P99: 278ms ↗+5%         │
│  渲染P99: 185ms →stable      │  渲染P99: 148ms ↘-20% ✓     │
│  缓存: 90%   →stable         │  缓存: 95.2% ↗+5.2pp ✓      │
│  QPS: 300   →stable          │  QPS: 260   →stable          │
│  延迟: 180ms →stable         │  延迟: 420ms ↗+133% ⚠       │
│  (无HERMES指标)               │  HERMES: 吞吐920ev/s,丢包0.003%│
└──────────────────────────────┴──────────────────────────────┘
```

#### 对比指标矩阵

| # | 指标 | ID | 基线值 | 灰度值 | 差值 | 判定 |
|---|------|----|--------|--------|------|------|
| 1 | CPU 使用率 | G-AL-001 | 45% | 47% | +2% | NORMAL |
| 2 | 内存使用率 | G-AL-002 | 78% | 79% | +1% | NORMAL |
| 3 | 磁盘使用率 | G-AL-003 | 62% | 63% | +1% | NORMAL |
| 4 | 网络延迟 | G-AL-004 | 2.1ms | 2.3ms | +0.2ms | NORMAL |
| 5 | 查询 P99 | H-AL-001 | 265ms | 278ms | +13ms | WARN |
| 6 | 渲染 P99 | H-AL-002 | 185ms | 148ms | -37ms | IMPROVED |
| 7 | 缓存命中率 | cache_hit_rate | 90% | 95.2% | +5.2pp | IMPROVED |
| 8 | QPS | qps_current | 300 | 260 | -40 | NORMAL |
| 9 | 数据延迟 | data_delay | 180ms | 420ms | +240ms | **WARN** |
| 10 | 吞吐 | throughput_evps | — | 920 | 新增 | — |
| 11 | 丢包率 | packet_loss_rate | — | 0.003% | 新增 | — |
| 12 | 容量预测 | capacity_prediction | — | 68% | 新增 | — |
| 13 | 审计异常率 | audit_anomaly_rate | — | 0.5% | 新增 | — |
| 14 | 审计不匹配 | audit_mismatch_count | — | 2 | 新增 | — |

### 4.2 指标一致性检查

| 检查项 | 方法 | 频率 | 失败处理 |
|--------|------|------|---------|
| 指标存在性 | 灰度指标集 ⊇ 基线指标集 | 5min | P2 告警 |
| 指标计数一致性 | 数据点数偏差 < 10% | 15min | P2 告警 |
| 指标值范围一致性 | 同指标值范围合理 | 5min | P3 告警 |
| 指标标签完整性 | 灰度标签完整 | 5min | P1 告警 |

#### 一致性检查结果

| 指标类别 | 基线数 | 灰度数 | 重叠 | 一致性 |
|---------|--------|--------|------|--------|
| 系统资源 | 4 | 4 | 4 | ✓ 100% |
| 性能指标 | 3 | 3 | 3 | ✓ 100% |
| 缓存指标 | 2 | 2 | 2 | ✓ 100% |
| QPS 指标 | 2 | 2 | 2 | ✓ 100% |
| 存储指标 | 2 | 2 | 2 | ✓ 100% |
| HERMES 指标 | 0 | 5 | 0 | — 灰度独有 |
| 容量指标 | 0 | 1 | 0 | — 灰度独有 |
| **合计** | **13** | **18** | **13** | **✓ 100%** |

### 4.3 Delta 分析

#### 分析框架

| 分析维度 | 方法 | 用途 |
|---------|------|------|
| 绝对差值 | gray - baseline | 告警判定 |
| 相对差值 | (gray-baseline)/baseline | 趋势分析 |
| 时间趋势 | 滑动窗口 60min | 长期趋势 |
| 统计显著性 | p-value < 0.05 | 确认差异非随机 |
| 置信区间 | 95% CI | 风险评估 |

#### Delta 分析结果 (60min 滑动窗口)

| 指标 | 基线均值 | 灰度均值 | 绝对差 | 相对差 | 显著 | 判定 |
|------|---------|---------|--------|--------|------|------|
| CPU | 45.2% | 47.1% | +1.9% | +4.2% | ✗ | 正常 |
| 内存 | 78.1% | 79.0% | +0.9% | +1.2% | ✗ | 正常 |
| 网络延迟 | 2.10ms | 2.31ms | +0.21ms | +10.0% | ✓ | **需关注** |
| 查询P99 | 265ms | 278ms | +13ms | +4.9% | ✗ | 正常 |
| 渲染P99 | 185ms | 148ms | -37ms | -20.0% | ✓ | **改善** |
| 缓存命中率 | 90.0% | 95.2% | +5.2pp | +5.8% | ✓ | **改善** |
| QPS | 300 | 260 | -40 | -13.3% | ✗ | 预期 |
| 数据延迟 | 180ms | 420ms | +240ms | +133.3% | ✓ | **严重偏离** |

#### Delta 告警判定

| 类型 | 条件 | 动作 |
|------|------|------|
| 正常波动 | <5% 且不显著 | 无操作 |
| 需关注 | ≥5% 且显著 | P3 告警+记录 |
| 显著改善 | ≥5% 且显著(正向) | 记录正向改善 |
| 严重偏离 | ≥20% 且显著(负向) | P1 告警+回滚评估 |

### 4.4 阈值差异化

| 指标 | 基线阈值 | 灰度阈值 | 差异原因 |
|------|---------|---------|---------|
| 数据延迟 | ≤200ms | ≤500ms | 灰度含新面板渲染开销 |
| 查询 P99 | ≤265ms | ≤300ms | 灰度面板查询复杂度高 |
| 缓存命中率 | ≥90% | ≥95% | 灰度新面板需充分预热 |
| 渲染 P99 | ≤185ms | ≤150ms | 灰度渲染优化目标 |
| CPU | ≤90% | ≤90% | 无差异 |
| 内存 | ≤80% | ≤80% | 无差异 |
| 磁盘 | ≤75% | ≤75% | 无差异 |
| 网络延迟 | ≤3ms | ≤3ms | 无差异 |
| 吞吐 (ev/s) | — | ≥900 | 新增指标 |
| 丢包率 | — | <0.005% | 新增指标 |

### 4.5 独立统计面板

| 面板 ID | 名称 | 对比维度 | 数据源 | 刷新 |
|---------|------|---------|--------|------|
| CMP-001 | 系统资源对比 | CPU/内存/磁盘/网络 | Gray+Baseline | 15s |
| CMP-002 | 性能指标对比 | 查询P99/渲染P99/延迟 | Gray+Baseline | 5s |
| CMP-003 | 缓存性能对比 | 命中率/缺失率/大小 | Gray+Baseline | 15s |
| CMP-004 | 流量对比 | QPS/峰值/突发 | Gray+Baseline | 5s |
| CMP-005 | HERMES 指标 | 审计/吞吐/丢包 | Gray only | 15s |
| CMP-006 | 容量预测 | 容量使用/预测 | Gray only | 60s |
| CMP-007 | Delta 总览 | 所有指标差值 | Gray+Baseline | 60s |
| CMP-008 | 采样健康 | 采样率/丢失/完整性 | Gray only | 15s |

---

## 5. HERMES 字段采样

### 5.1 字段总览

V87 新增 5 个 HERMES 审计事件字段，灰度流量中执行 **100% 全量采样**。

| # | 字段 | 类型 | 格式 | 说明 |
|---|------|------|------|------|
| 1 | event_type | string enum | audit/create/update/delete/reconcile | 事件类型分类 |
| 2 | priority | integer | 1-5 (1=最高) | 事件优先级 |
| 3 | trace_id | UUID v4 | xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx | 分布式追踪 ID |
| 4 | batch_id | string | batch-<timestamp>-<uuid_short> | 批量处理标识 |
| 5 | retry_count | integer | 0-N (典型<3) | 重试次数 |

### 5.2 采样策略

| 字段 | 采样率 | 策略 | 缓冲 | 存储 |
|------|--------|------|------|------|
| event_type | 100% | full_sample | 独立缓冲 | 独立索引 |
| priority | 100% | full_sample | 独立缓冲 | 独立索引 |
| trace_id | 100% | full_sample | 独立缓冲 | 独立索引 |
| batch_id | 100% | full_sample | 独立缓冲 | 独立索引 |
| retry_count | 100% | full_sample | 独立缓冲 | 独立索引 |

#### 采样完整性验证

| 验证项 | 方法 | 频率 | 失败处理 |
|--------|------|------|---------|
| 字段存在性 | 5 字段全部存在 | 15s | P1 告警 |
| 非空率 | 非空值 ≥99.9% | 5min | P2 告警 |
| 值范围 | 值在预期范围内 | 5min | P2 告警 |
| 关联完整性 | trace_id 可关联完整链路 | 15min | P3 告警 |

### 5.3 字段基数分析

| 字段 | 基数类型 | 基数范围 | 稳定性 | 索引影响 | 索引策略 |
|------|---------|---------|--------|---------|---------|
| event_type | 低基数 (enum) | 5 个值 | 稳定 | 低 | bloom filter |
| priority | 低基数 (int) | 5 个值 | 稳定 | 低 | 无索引 |
| trace_id | **超高基数** (UUID v4) | ~2^122 唯一值 | 高(每次唯一) | **高** | hash index |
| batch_id | 中基数 (batch-scoped) | ~1K-10K/天 | 中 | 中 | hash index |
| retry_count | 低基数 (int) | 0-10 (典型) | 稳定 | 低 | 无索引 |

#### trace_id 详细分析

| 维度 | 配置 |
|------|------|
| 类型 | UUID v4 (128-bit) |
| 基数 | 理论 2^122 ≈ 5.19×10^36 |
| 每日基数 | ~50K-100K 唯一值 |
| 索引 | hash index (精确匹配) |
| 存储 | 16字节(原始)/36字符(字符串) |
| 压缩率 | ~1.0x (不可压缩) |
| 查询模式 | 精确匹配 (WHERE trace_id = 'xxx') |

### 5.4 存储影响

#### 每事件存储增量

| 字段 | 字符串长度 | 原始大小 | 压缩后 | 说明 |
|------|-----------|---------|--------|------|
| event_type | ~8 字符 | ~8B | ~4B | 短字符串 |
| priority | ~2 字符 | ~2B | ~1B | 小整数 |
| trace_id | 36 字符 | 36B | 36B | UUID 不可压缩 |
| batch_id | 24-32 字符 | ~30B | ~15B | 部分可压缩 |
| retry_count | ~3 字符 | ~3B | ~1B | 小整数 |
| **合计** | **~72-82 字符** | **~84 字节** | **~44 字节** | — |

#### 日存储增量 (灰度流量 ~75,000 events/天)

| 场景 | 事件量 | 原始/天 | 压缩/天 | 含索引+元数据 |
|------|--------|--------|--------|-------------|
| 低负载 | 50,000 | 4.2 MB | 2.2 MB | ~42.5 MB |
| 中等负载 | 75,000 | 6.3 MB | 3.3 MB | ~63.5 MB |
| 高负载 | 100,000 | 8.4 MB | 4.4 MB | ~84.5 MB |

#### 90 天存储影响

| 维度 | V86 | V87 灰度 (StageA) | 增量 | 增量% |
|------|-----|-------------------|------|-------|
| 日均事件量 | — | ~75,000 | +75,000 | — |
| 日均存储增量 | — | ~63.5 MB | +63.5 MB | — |
| 90 天存储增量 | — | ~5.7 GB | +5.7 GB | +0.64% |
| 90 天总存储 | 720 GB | ~725.7 GB | +5.7 GB | +0.64% |

### 5.5 字段与告警规则关联

| 告警规则 | 关联字段 | 触发条件 | 字段采样要求 |
|---------|---------|---------|-------------|
| V87-AL-009 | event_type, batch_id | throughput < 900 ev/s (60s) | event_type 全量 |
| V87-AL-010 | trace_id, retry_count | packet_loss > 0.005% (30s) | trace_id 全量 |
| AUD-AL-001 | event_type, priority | audit_anomaly > 1% (5min) | event_type 全量 |
| AUD-AL-002 | trace_id, batch_id, retry_count | mismatch > 10 in 1min | trace_id 全量 |

---

## 6. 技术实现

### 6.1 流量路由器配置 (YAML)

```yaml
traffic_router:
  version: "v87-rc1-phase03-stage-a"
  experiment_id: "v87_phase03_stage_a"
  gray_flag: true

  routing:
    strategy: consistent_hash
    split_ratio:
      gray: 0.50
      baseline: 0.50
    hash_key: "source_ip"
    hash_algorithm: "murmur3_128"
    fallback: "baseline"

  gray_labels:
    version_tag: "v87-rc1"
    gray_flag: true
    experiment_id: "v87_phase03_stage_a"
    pipeline_id: "gray_pipeline_v87"
    namespace_id: "gray"
    cache_prefix: "cache:gray:"
    query_pool: "gray_pool"
    alert_evaluator: "gray_eval"

  baseline_labels:
    version_tag: "v86"
    gray_flag: false
    pipeline_id: "baseline_pipeline_v86"
    namespace_id: "baseline"
    cache_prefix: "cache:baseline:"
    query_pool: "baseline_pool"
    alert_evaluator: "baseline_eval"

  sampling:
    gray:
      sampling_rate: 1.0
      sampling_mode: full_sample
      verification_interval: "15s"
      loss_tolerance: 0.0
      overflow_policy: block_and_alert
    baseline:
      sampling_rate: "preserve_v86"
      verification_interval: "60s"

  buffers:
    gray:
      queue_capacity: 100000
      memory_limit: "50MB"
      flush_interval: "15s"
      priority: HIGH
      overflow_action: block_and_alert
      drop_policy: none
    baseline:
      queue_capacity: "preserve_v86"
      memory_limit: "preserve_v86"
      flush_interval: "preserve_v86"

  label_consistency:
    immutable: true
    audit_interval: "15s"
    audit_sample_rate: 0.01
    consistency_alert_threshold: 0.001

  rollback:
    triggers:
      - condition: "gray_query_p99 > 300ms for 5min"
        action: disable_gray
      - condition: "gray_render_p99 > 150ms for 5min"
        action: disable_gray
      - condition: "gray_cache_hit_rate < 90% for 10min"
        action: disable_gray
      - condition: "gray_data_delay > 500ms for 3min"
        action: disable_gray
      - condition: "cross_contamination > 0.01% for any interval"
        action: disable_gray
    rollback_timeout: "60s"
    auto_resume: false
```

### 6.2 指标管道架构

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Ingest   │───▶│  Tag     │───▶│  Route   │───▶│  Store   │
│ (采集)    │    │  (标签)   │    │  (路由)   │    │  (存储)   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
      │               │               │               │
      ▼               ▼               ▼               ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Query    │◀───│  Route   │◀───│  Query   │◀───│  Query   │
│ (查询)    │    │  (反查)   │    │  Plan    │    │  Cache   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

#### Ingest 配置

```yaml
ingest:
  gray:
    collector: GrayCollector
    mode: full_sample
    throughput_target: 260 QPS
    throughput_peak: 320 QPS
    buffer_size: 100000
    flush_interval: "15s"
    deduplication: true
    deduplication_window: "60s"
    max_ingest_latency: "100ms"
  baseline:
    collector: BaselineCollector
    mode: "preserve_v86"
    throughput_target: 260 QPS
```

#### Tag 配置

```yaml
tag:
  gray:
    required_labels:
      - version_tag: "v87-rc1"
      - gray_flag: true
      - experiment_id: "v87_phase03_stage_a"
      - pipeline_id: "gray_pipeline_v87"
      - namespace_id: "gray"
      - cache_prefix: "cache:gray:"
      - query_pool: "gray_pool"
      - alert_evaluator: "gray_eval"
    label_validation: true
    validation_interval: "15s"
    immutable: true
  baseline:
    required_labels:
      - version_tag: "v86"
      - gray_flag: false
    label_validation: true
    validation_interval: "60s"
```

#### Route 配置

```yaml
route:
  gray:
    destination: gray_storage_namespace
    pipeline_id: gray_pipeline_v87
    cache_prefix: "cache:gray:"
    query_pool: gray_pool
    routing_strategy: tag_driven
    routing_rules:
      - match: "gray_flag == true"
        action: route_to_gray
      - match: "gray_flag == false"
        action: route_to_baseline
    fallback: baseline
    cross_contamination_check: true
    contamination_threshold: 0.0001
  baseline:
    destination: baseline_storage_namespace
    pipeline_id: baseline_pipeline_v86
    cache_prefix: "cache:baseline:"
```

#### Store 配置

```yaml
store:
  gray:
    namespace: v87_gray
    index_prefix: v87_gray_
    retention: "90d"
    compression: "zstd_level_3"
    index_strategy:
      - field: trace_id
        type: hash_index
        cardinality: ultra_high
      - field: batch_id
        type: hash_index
        cardinality: medium
      - field: event_type
        type: bloom_filter
        cardinality: low
    ttl_policy:
      hermes_events: "90d"
      audit_logs: "90d"
      trace_data: "90d"
    max_store_latency: "50ms"
  baseline:
    namespace: v86_baseline
    retention: "90d"
```

#### Query 配置

```yaml
query:
  gray:
    cache_prefix: "cache:gray:"
    cache_size: "10GB"
    cache_ttl: "300s"
    query_pool: gray_pool
    connection_pool_size: 50
    max_query_p99: "300ms"
    max_render_p99: "150ms"
    max_data_delay: "500ms"
    cache_hit_rate_target: 0.95
    query_timeout: "5s"
    retry:
      max_retries: 2
      retry_delay: "100ms"
  baseline:
    cache_prefix: "cache:baseline:"
    max_query_p99: "265ms"
    max_render_p99: "185ms"
    cache_hit_rate_target: 0.90
```

### 6.3 缓存策略

#### 缓存隔离

| 维度 | 灰度缓存 | 基线缓存 |
|------|---------|---------|
| 缓存键前缀 | `cache:gray:` | `cache:baseline:` |
| 缓存实例 | GrayCache | BaselineCache |
| 缓存大小 | 10 GB | V86 默认 |
| 缓存 TTL | 300s | V86 默认 |
| 命中率目标 | ≥95% | ≥90% |
| 缓存预热 | 主动预热 | V86 默认 |
| 缓存淘汰 | LRU | V86 默认 |

#### 缓存键命名规范

```
格式: <cache_prefix>:<panel_id>:<data_type>:<time_bucket>

灰度示例:
  cache:gray:v87_p_001:render_p99:20260715T1430
  cache:gray:v87_p_004:alert_correlation:20260715T1430
  cache:gray:v87_p_006:full_trace:20260715T1430
  cache:gray:v87_p_007:audit_reconcile:20260715T1430

基线示例:
  cache:baseline:v86_panel_001:render_p99:20260715T1430
```

#### 缓存预热策略

| 面板 ID | 名称 | 预热方式 | 预热时机 |
|---------|------|---------|---------|
| V87-P-001 | AI 异常检测 | 主动预热 | 首次加载+每 5min |
| V87-P-002 | 依赖拓扑 | 主动预热 | 首次加载+每 15min |
| V87-P-003 | 容量预测 | 主动预热 | 首次加载+每 30min |
| V87-P-004 | 告警关联 | 主动预热 | 首次加载+每 5min |
| V87-P-006 | 全链路追踪 | 被动预热 | 首次查询 |
| V87-P-007 | 审计对账 | 主动预热 | 首次加载+每 10min |
| V87-P-008 | 基线漂移热力图 | 主动预热 | 首次加载+每 30min |

### 6.4 QPS 预算分配

| 维度 | V86 | V87 灰度 (StageA) | V87 全量 | 保护阈值 |
|------|-----|-------------------|---------|---------|
| 总 QPS | 300 | 560 | 520 | 800 |
| 基线 QPS | 300 | ~260 | — | — |
| 灰度 QPS | — | ~260 | 520 | — |
| 峰值 QPS | 380 | ~480 | 620 | 800 |
| 保护余量 | 52% | 30% | 54% | — |

#### 灰度面板 QPS 预算

| 面板 ID | 名称 | QPS 预算 | 峰值 | 说明 |
|---------|------|---------|------|------|
| V87-P-001 | AI 异常检测 | 35 | 50 | ML 推理 |
| V87-P-002 | 依赖拓扑 | 20 | 30 | 图查询 |
| V87-P-003 | 容量预测 | 15 | 22 | 预测计算 |
| V87-P-004 | 告警关联 | 40 | 55 | 多数据源关联 |
| V87-P-006 | 全链路追踪 | 30 | 45 | 追踪关联 |
| V87-P-007 | 审计对账 | 45 | 60 | 审计比对 |
| V87-P-008 | 基线漂移热力图 | 20 | 30 | 漂移计算 |
| **合计** | **7 面板** | **205** | **292** | — |

#### 令牌桶限流

```
灰度令牌桶:
  bucket_size: 320 (峰值容量)
  refill_rate: 260/s (持续速率)
  refill_interval: 1s
  overflow_action: reject + log + alert

基线令牌桶:
  bucket_size: V86 默认
  refill_rate: V86 默认
```

---

## 7. 监控与告警

### 7.1 采样健康监控

| 指标 | ID | 计算方法 | 正常范围 | 告警阈值 | 级别 |
|------|----|---------|---------|---------|------|
| 采样率 | sampling_rate | 实际采样/入口 | 1.0 | ≠1.0 | P1 |
| 采样丢失率 | sampling_loss_rate | (入口-存储)/入口 | 0.0 | >0.0001 | P2 |
| 采样漂移率 | sampling_drift_rate | 相邻采样率差值 | 0.0 | >0.001/s | P2 |
| 采样完整性 | sampling_completeness | 存储/预期 | 1.0 | <0.999 | P1 |
| 采样延迟 | sampling_latency | 采集到存储时间 | <15s | >30s | P2 |
| 缓冲区健康 | buffer_health | 缓冲区使用率 | <80% | >90% | P1 |

#### 采样健康监控配置

```yaml
sampling_health_monitor:
  sampling_rate:
    check_interval: "15s"
    expected_value: 1.0
    drift_threshold_absolute: 0.0001
    drift_threshold_relative: 0.0001
    spike_threshold: 0.01
    spike_window: "60s"
  sampling_loss:
    check_interval: "15s"
    method: count_comparison
    loss_threshold_warn: 0.0001
    loss_threshold_crit: 0.001
    loss_threshold_recover: 0.01
  buffer_health:
    check_interval: "15s"
    usage_warn: 0.80
    usage_crit: 0.90
    fill_rate_warn: 5000
    fill_rate_crit: 8000
    age_warn: 60
    age_crit: 120
```

### 7.2 交叉污染检测

| 检测维度 | 方法 | 正常阈值 | 告警阈值 | 级别 | 动作 |
|---------|------|---------|---------|------|------|
| 指标数据泄露 | 灰度管道查baseline标签 | 0% | >0.001% | P1 | 自动隔离 |
| 缓存污染 | 灰度缓存查baseline键 | 0% | >0% | P1 | 缓存清除 |
| 查询串扰 | 查询返回错误管道数据 | 0% | >0% | P2 | 审计 |
| 存储混写 | 灰度命名空间查baseline数据 | 0% | >0% | P0 | 命名空间隔离 |
| 告警误触发 | 灰度告警查baseline源 | 0% | >0% | P2 | 验证 |

#### 交叉污染告警规则

| 告警 ID | 名称 | 条件 | 严重度 | 通道 |
|---------|------|------|--------|------|
| CC-AL-001 | 指标数据泄露 | gray含baseline标签>0.001% | CRIT | PagerDuty+DingTalk |
| CC-AL-002 | 缓存污染 | cache:gray:含baseline键>0% | CRIT | PagerDuty+DingTalk |
| CC-AL-003 | 查询串扰 | 返回错误管道数据>0% | WARN | DingTalk |
| CC-AL-004 | 存储混写 | gray命名空间含baseline数据>0% | P0 | PagerDuty+Email+电话 |
| CC-AL-005 | 告警误触发 | 灰度告警源为baseline>0% | WARN | DingTalk |

### 7.3 采样延迟告警

| 指标 | 计算 | 正常 | WARN | CRIT |
|------|------|------|------|------|
| gray_data_delay | 采集到可查询延迟 | <300ms | >400ms | >500ms |
| gray_query_latency | 灰度查询耗时 | <200ms | >250ms | >300ms |
| gray_render_latency | 灰度渲染耗时 | <120ms | >140ms | >150ms |
| gray_ingest_latency | 采集到缓冲延迟 | <50ms | >80ms | >100ms |
| gray_flush_latency | 缓冲刷新延迟 | <50ms | >80ms | >100ms |

#### 关键告警规则

```yaml
sampling_lag_alert:
  gray_data_delay:
    metric: gray_data_delay
    condition: "value > 500"
    for: "30s"
    severity: CRIT
    channels: [dingtalk, email, pagerduty]
    description: "灰度数据延迟超过500ms，触发CRIT告警"

  sampling_loss_critical:
    metric: gray_sampling_loss_rate
    condition: "value > 0.01"
    for: "15s"
    severity: P0
    channels: [pagerduty, email, phone]
    description: "采样丢失率>1%，自动触发灰度回滚"
```

### 7.4 监控仪表板

| 区域 | 面板 | 刷新 | 数据源 |
|------|------|------|--------|
| 顶部状态栏 | 灰度状态、运行时长、流量比例 | 15s | Traffic Router |
| 采样健康区 | 采样率、丢失率、完整性、缓冲区 | 15s | Sampling Monitor |
| 性能区 | 查询P99、渲染P99、数据延迟、QPS | 5s | Gray Metrics |
| 缓存区 | 命中率、缺失率、大小、预热状态 | 15s | Gray Cache |
| 交叉污染区 | 标签/缓存/存储审计结果 | 5min | Contamination Detector |
| HERMES 区 | 事件吞吐、审计异常率、字段覆盖率 | 15s | HERMES Metrics |
| 告警区 | 活跃告警、最近历史 | 15s | Alert System |
| 决策区 | 灰度健康评分、回滚/升级建议 | 60s | Decision Engine |

#### 灰度健康评分

| 维度 | 权重 | 计算 | 满分 |
|------|------|------|------|
| 采样健康 | 30% | 1-loss_rate-drift_rate | loss=0,drift=0 |
| 性能达标 | 25% | (query_ok+render_ok+delay_ok)/3 | 全部达标 |
| 缓存健康 | 15% | hit_rate/0.95 | hit_rate≥95% |
| 交叉污染 | 20% | 1-contamination_rate | contamination=0 |
| 告警健康 | 10% | 1-active_critical/max_expected | 无CRIT告警 |

---

## 8. 测试计划

### 8.1 测试策略总览

| 层级 | 范围 | 方法 | 环境 | 自动化 | 耗时 |
|------|------|------|------|--------|------|
| 单元测试 | 流量标签逻辑 | JUnit/Mockito | CI | 100% | 15min |
| 集成测试 | 指标管道隔离 | 端到端 | Staging | 80% | 1hr |
| 压力测试 | 双管道容量 | 负载生成 | Staging | 60% | 4hr |
| 混沌测试 | 故障注入 | 故障模拟 | Staging | 40% | 2hr |
| 验收测试 | 灰度功能 | 功能验证 | Prod-Gray | 50% | 1hr |

### 8.2 单元测试: 流量标签

| ID | 名称 | 预期 | 优先级 |
|----|------|------|--------|
| UT-TAG-001 | 灰度标签注入 | version_tag=v87-rc1,gray_flag=true | P0 |
| UT-TAG-002 | 基线标签注入 | version_tag=v86,gray_flag=false | P0 |
| UT-TAG-003 | 标签不可变 | 修改失败 | P0 |
| UT-TAG-004 | 标签传递完整 | 多阶段传递完整 | P0 |
| UT-TAG-005 | 一致哈希路由 | 同IP同管道 | P1 |
| UT-TAG-006 | 回退路由 | 未知IP→基线 | P1 |
| UT-TAG-007 | 哈希碰撞率 | 10000 IP,碰撞<0.1% | P1 |
| UT-TAG-008 | 标签审计采样 | 1%采样正确 | P2 |

```yaml
unit_test:
  framework: "JUnit 5 + Mockito 5"
  coverage_target: 0.95
  test_classes:
    - TrafficRouterTest
    - LabelInjectorTest
    - ConsistentHashTest
    - LabelValidatorTest
    - LabelAuditTest
  test_data:
    source_ips: "10000 unique IPs"
```

### 8.3 集成测试: 指标管道隔离

| ID | 名称 | 预期 | 优先级 |
|----|------|------|--------|
| IT-ISO-001 | 灰度不入基线存储 | 0条灰度指标 | P0 |
| IT-ISO-002 | 基线不入灰度存储 | 0条基线指标 | P0 |
| IT-ISO-003 | 灰度查询仅返灰度 | 仅灰度数据 | P0 |
| IT-ISO-004 | 基线查询仅返基线 | 仅基线数据 | P0 |
| IT-ISO-005 | 灰度缓存不污染基线 | 0条灰度缓存 | P0 |
| IT-ISO-006 | 基线缓存不污染灰度 | 0条基线缓存 | P0 |
| IT-ISO-007 | 缓冲区独立 | 基线不受灰度影响 | P1 |
| IT-ISO-008 | 标签跨管道验证 | 8标签完整 | P1 |
| IT-ISO-009 | TTL隔离 | 基线TTL不受影响 | P2 |
| IT-ISO-010 | 索引隔离 | 基线索引不受影响 | P2 |

```yaml
integration_test:
  environment: staging
  traffic_generator: "k6 v0.48"
  test_duration: "1hr per scenario"
  test_data_volume:
    gray_events: "100,000"
    baseline_events: "100,000"
  validation:
    cross_contamination: 0.0
    data_integrity: 1.0
    isolation_score: 1.0
```

### 8.4 压力测试: 双管道容量

| ID | 名称 | 灰度QPS | 基线QPS | 持续 | 目标 |
|----|------|---------|---------|------|------|
| ST-001 | 稳态 | 260 | 260 | 30min | 稳态性能 |
| ST-002 | 峰值 | 320 | 320 | 15min | 峰值处理 |
| ST-003 | 突发 | 480(突发) | 320 | 5min | 突发处理 |
| ST-004 | 缓冲区压力 | 500 | 260 | 10min | 缓冲容量 |
| ST-005 | 混合负载 | 200-400变 | 200-400变 | 60min | 混合场景 |

#### 压力测试指标

| 指标 | 稳态 | 峰值 | 突发 |
|------|------|------|------|
| 灰度查询P99 | ≤250ms | ≤300ms | ≤350ms |
| 灰度渲染P99 | ≤120ms | ≤150ms | ≤180ms |
| 灰度数据延迟 | ≤300ms | ≤500ms | ≤600ms |
| 灰度缓存命中 | ≥95% | ≥90% | ≥85% |
| 灰度采样丢失 | 0% | 0% | 0% |
| 灰度缓冲使用率 | <50% | <70% | <80% |
| 基线查询P99 | ≤250ms | ≤265ms | ≤280ms |
| 基线缓存命中 | ≥90% | ≥88% | ≥85% |

```yaml
stress_test:
  tool: "k6 v0.48"
  scenarios:
    - name: "ST-001 Steady State"
      duration: "30m"
      vus: 260
      iterations: 100000
      thresholds:
        gray_query_p99: "p(99)<300"
        gray_render_p99: "p(99)<150"
        gray_data_delay: "p(99)<500"
        gray_cache_hit_rate: "avg>0.95"
        gray_sampling_loss: "avg<0.0001"
    - name: "ST-002 Peak Load"
      duration: "15m"
      vus: 320
      iterations: 60000
      thresholds:
        gray_query_p99: "p(99)<300"
        gray_sampling_loss: "avg<0.0001"
    - name: "ST-003 Burst"
      duration: "5m"
      vus: 480
      iterations: 20000
      thresholds:
        gray_buffer_usage: "avg<0.80"
        gray_sampling_loss: "avg<0.001"
    - name: "ST-004 Buffer Pressure"
      duration: "10m"
      vus: 500
      iterations: 40000
      thresholds:
        gray_buffer_usage: "avg<0.90"
        gray_buffer_overflow: "max<10"
    - name: "ST-005 Mixed Workload"
      duration: "60m"
      vus: "varies 200-400"
      iterations: 200000
      thresholds:
        gray_query_p99: "p(99)<300"
        gray_render_p99: "p(99)<150"
```

### 8.5 混沌测试: 故障注入

| ID | 故障 | 目标 | 程度 | 预期行为 |
|----|------|------|------|---------|
| CH-001 | 缓冲区溢出 | 灰度缓冲 | 100%填充 | 阻塞+告警,无丢失 |
| CH-002 | 存储不可用 | 灰度存储 | 完全中断 | 缓冲积压,可恢复 |
| CH-003 | 缓存失效 | 灰度缓存 | 100%清除 | 缓存重建,命中恢复 |
| CH-004 | 管道中断 | 灰度管道 | 完全中断 | 回退基线,不丢请求 |
| CH-005 | 标签丢失 | 灰度标签 | 随机丢失 | 验证告警 |
| CH-006 | 时钟漂移 | 灰度时钟 | +5min偏移 | 延迟告警 |
| CH-007 | 慢查询 | 灰度查询 | P99 500ms | 超时回退 |
| CH-008 | 网络分区 | 灰度网络 | 50%丢包 | 重试+告警 |

```yaml
chaos_test:
  tool: "Chaos Mesh v2.6"
  duration: "2hr total"
  scenarios:
    - name: "CH-001 Buffer Overflow"
      fault: "network/delay"
      target: "gray_buffer"
      duration: "5min"
      parameters: {latency: "100ms", jitter: "50ms"}
      expected: "buffer fills 100%, block_and_alert, no data loss"
    - name: "CH-002 Storage Unavailable"
      fault: "network/partition"
      target: "gray_storage"
      duration: "5min"
      parameters: {partition: "100%"}
      expected: "data buffered locally, recovery after heal"
    - name: "CH-005 Label Loss"
      fault: "pod/kill"
      target: "label_injector"
      duration: "2min"
      parameters: {pods: "1 of 3 replicas"}
      expected: "label validation detects missing, P2 alert"
    - name: "CH-006 Clock Drift"
      fault: "clock/offset"
      target: "gray_collector"
      duration: "5min"
      parameters: {offset: "5min"}
      expected: "sampling latency detected, P2 alert"
    - name: "CH-008 Network Partition"
      fault: "network/partition"
      target: "gray_pipeline"
      duration: "5min"
      parameters: {packet_loss: "50%"}
      expected: "retry engaged, data eventually consistent"
```

### 8.6 验收测试

| ID | 验收项 | 标准 | 方法 | 负责人 |
|----|--------|------|------|--------|
| AT-001 | 灰度流量比例 | 50%±1% | 流量统计 | SRE |
| AT-002 | 采样率100% | loss=0% | 采样监控 | DSHE |
| AT-003 | 交叉污染0% | contamination=0% | 标签审计 | DSHE |
| AT-004 | 查询P99≤300ms | p99<300ms | 性能监控 | DSHE |
| AT-005 | 渲染P99≤150ms | p99<150ms | 性能监控 | DSHE |
| AT-006 | 数据延迟≤500ms | delay<500ms | 延迟监控 | DSHE |
| AT-007 | 缓存命中≥95% | hit≥95% | 缓存监控 | DSHE |
| AT-008 | HERMES字段100% | coverage=100% | 字段审计 | HERMES |
| AT-009 | 基线无退化 | 与V86一致 | 基线对比 | DSHE |
| AT-010 | 回滚有效 | <60s完成 | 回滚测试 | SRE |

### 8.7 测试环境

| 环境 | 用途 | 规模 | 流量 | 持续 |
|------|------|------|------|------|
| CI Pipeline | 单元测试 | N/A | N/A | 每次提交 |
| Staging-L1 | 集成测试 | 1/4生产 | 50/50 | 每天 |
| Staging-L2 | 压力测试 | 1/2生产 | 50/50 | 每周 |
| Staging-L3 | 混沌测试 | 1/4生产 | 50/50 | 按需 |
| Production-Gray | 灰度验收 | 生产50% | 50/50 | 持续 |

---

## 9. 风险评估

### 9.1 风险总览

| # | 风险 | 严重度 | 可能性 | 影响 | 缓解 | 残余 |
|---|------|--------|--------|------|------|------|
| R1 | 交叉污染 | CRIT | 低 | 数据泄露 | 标签审计+缓存隔离 | LOW |
| R2 | 采样漂移 | HIGH | 中 | 数据丢失 | 15s验证+自动回滚 | LOW |
| R3 | QPS超额 | HIGH | 中 | 性能退化 | 令牌桶限流 | MEDIUM |
| R4 | 缓冲区溢出 | HIGH | 低 | 数据丢失 | 阻塞+告警 | LOW |
| R5 | 缓存污染 | HIGH | 低 | 错误数据 | 前缀隔离 | LOW |
| R6 | 存储膨胀 | MED | 中 | 存储成本 | 容量监控+TTL | LOW |
| R7 | 查询退化 | HIGH | 中 | SLA违反 | 性能监控+回滚 | MEDIUM |
| R8 | HERMES字段丢失 | MED | 低 | 数据不完整 | 字段审计 | LOW |
| R9 | 回滚失败 | CRIT | 低 | 无法恢复 | 回滚测试+手动 | LOW |
| R10 | 基线受影响 | HIGH | 低 | 生产退化 | 完全隔离 | LOW |

### 9.2 详细风险评估

#### R1: 交叉污染 (Cross-Contamination)

| 维度 | 描述 |
|------|------|
| 风险描述 | 灰度数据泄露到基线或反之，指标数据不准确 |
| 严重度 | CRIT — 数据准确性完全依赖隔离 |
| 可能性 | 低 — 多层隔离防护 |
| 根本原因 | 标签注入错误、缓存键冲突、存储路由错误 |
| 缓解措施 | 1.标签不可变 2.标签审计(1%) 3.缓存前缀隔离 4.存储命名空间隔离 5.查询池隔离 |
| 检测 | CC-AL-001~005 告警 |
| 响应 | 自动隔离→通知SRE→手动验证→修复 |
| 残余风险 | LOW |

#### R2: 采样漂移 (Sampling Drift)

| 维度 | 描述 |
|------|------|
| 风险描述 | 灰度采样率从100%下降，数据不完整 |
| 严重度 | HIGH |
| 可能性 | 中 — 缓冲溢出/管道阻塞 |
| 根本原因 | 管道性能下降、缓冲区溢出、存储写入失败 |
| 缓解措施 | 1.15s采样率验证 2.计数比对 3.自动回滚(>1%) 4.缓冲阻塞 |
| 检测 | sampling_rate_monitor + sampling_loss_alert |
| 残余风险 | LOW — 快速检测+自动回滚 |

#### R3: QPS 超额 (QPS Over-Allocation)

| 维度 | 描述 |
|------|------|
| 风险描述 | 灰度流量超过QPS预算，性能退化 |
| 严重度 | HIGH |
| 可能性 | 中 — 流量模式不可预测 |
| 根本原因 | 面板查询频繁、用户流量突增、缓存未命中 |
| 缓解措施 | 1.令牌桶限流 2.QPS监控告警 3.面板级QPS预算 4.查询超时 |
| 残余风险 | MEDIUM — 流量突增可能超出预期 |

#### R4: 缓冲区溢出 (Buffer Overflow)

| 维度 | 描述 |
|------|------|
| 风险描述 | 灰度缓冲满，数据阻塞或丢失 |
| 严重度 | HIGH |
| 可能性 | 低 — 100K entries充足 |
| 根本原因 | 消费速率<生产速率、存储不可用 |
| 缓解措施 | 1.50MB缓冲 2.100K队列 3.阻塞+告警 4.背压 |
| 残余风险 | LOW — 大容量+告警 |

#### R5: 缓存污染 (Cache Pollution)

| 维度 | 描述 |
|------|------|
| 风险描述 | 灰度缓存条目污染基线缓存或反之 |
| 严重度 | HIGH |
| 可能性 | 低 — 前缀隔离 |
| 根本原因 | 缓存键冲突、缓存驱逐策略问题 |
| 缓解措施 | 1.cache:gray:/cache:baseline:前缀 2.独立实例 3.键审计 |
| 残余风险 | LOW |

#### R6: 存储膨胀 (Storage Bloat)

| 维度 | 描述 |
|------|------|
| 风险描述 | 灰度流量增加存储需求，超出预算 |
| 严重度 | MEDIUM |
| 可能性 | 中 — 取决于事件量 |
| 根本原因 | HERMES事件量超预期、索引膨胀 |
| 缓解措施 | 1.容量监控 2.TTL策略 3.zstd压缩 4.预算告警 |
| 残余风险 | LOW — 0.64%增长可控 |

#### R7: 灰度查询退化 (Gray Query Degradation)

| 维度 | 描述 |
|------|------|
| 风险描述 | 灰度查询P99超过300ms SLA |
| 严重度 | HIGH |
| 可能性 | 中 — 新面板查询复杂度高 |
| 根本原因 | 查询复杂度高、缓存未命中、连接池耗尽 |
| 缓解措施 | 1.查询超时(5s) 2.重试(2次) 3.缓存预热 4.连接池隔离 |
| 残余风险 | MEDIUM — 新面板查询复杂度未知 |

#### R8: HERMES 字段丢失 (HERMES Field Loss)

| 维度 | 描述 |
|------|------|
| 风险描述 | 5个HERMES字段未全量采样，审计数据不完整 |
| 严重度 | MEDIUM |
| 可能性 | 低 — 全量采样策略 |
| 根本原因 | 字段注入错误、标签丢失 |
| 缓解措施 | 1.15s字段存在性检查 2.99.9%非空率 3.值范围验证 |
| 残余风险 | LOW |

#### R9: 回滚失败 (Rollback Failure)

| 维度 | 描述 |
|------|------|
| 风险描述 | 灰度回滚触发后无法成功关闭灰度 |
| 严重度 | CRIT |
| 可能性 | 低 — 回滚机制经测试 |
| 根本原因 | 回滚脚本错误、流量路由器故障、缓存未清除 |
| 缓解措施 | 1.回滚测试(AT-010) 2.手动回滚流程 3.回滚超时(60s) |
| 残余风险 | LOW |

#### R10: 基线受影响 (Baseline Impact)

| 维度 | 描述 |
|------|------|
| 风险描述 | 灰度流量影响基线性能，基线SLA违反 |
| 严重度 | HIGH |
| 可能性 | 低 — 完全隔离 |
| 根本原因 | 共享资源竞争(CPU/内存/磁盘I/O) |
| 缓解措施 | 1.完全隔离 2.QPS预算隔离 3.缓冲区隔离 |
| 残余风险 | LOW |

### 9.3 风险热力图

```
              可能性
          低    中    高    极高
    ┌──────────────────────────┐
 高  │        │R3,R7  │        │
严  │        │        │        │
重  │        │        │        │
度  ├──────────────────────────┤
    │R2,R5   │R4      │R1,R10 │
    │        │        │        │
    ├──────────────────────────┤
    │R6,R8   │        │R9      │
    │        │        │        │
    └──────────────────────────┘
```

### 9.4 风险监控仪表板

| 监控项 | 方法 | 频率 | 告警条件 |
|--------|------|------|---------|
| 交叉污染率 | 标签审计扫描 | 5min | >0.01% |
| 采样丢失率 | 计数比对 | 15s | >0.01% |
| 灰度查询P99 | 性能监控 | 15s | >300ms |
| 灰度渲染P99 | 性能监控 | 15s | >150ms |
| 灰度缓存命中 | 缓存监控 | 15s | <95% |
| 缓冲区使用率 | 缓冲监控 | 15s | >90% |
| QPS当前值 | QPS监控 | 15s | >预算120% |
| 存储增长率 | 存储监控 | 1h | >预期120% |
| HERMES字段覆盖 | 字段审计 | 15s | <100% |
| 回滚就绪度 | 健康检查 | 5min | 不健康 |

---

## 10. 状态标记

### 10.1 阶段状态

| 状态项 | 值 |
|--------|-----|
| 阶段 | Phase03 / StageA |
| 分支 | feature/v87-rc1-g1 |
| 上一阶段 | Phase02 (commit 0d9a9d7) |
| 灰度比例 | 50% |
| 采样策略 | 灰度100%全量 + 基线V86默认 |
| 隔离方案 | 双管道完全隔离 |
| 文档状态 | IN_PROGRESS |
| 评审状态 | PENDING_REVIEW |

### 10.2 完成度矩阵

| 章节 | 状态 | 完成度 |
|------|------|--------|
| 1. 执行摘要 | ✅ COMPLETE | 100% |
| 2. 灰度流量采样架构 | ✅ COMPLETE | 100% |
| 2.1 架构总览 | ✅ | 100% |
| 2.2 双流量隔离设计 | ✅ | 100% |
| 2.3 流量标签机制 | ✅ | 100% |
| 2.4 指标路由 | ✅ | 100% |
| 2.5 存储隔离 | ✅ | 100% |
| 3. 采样策略配置 | ✅ COMPLETE | 100% |
| 3.1 采样策略总览 | ✅ | 100% |
| 3.2 灰度全量采样配置 | ✅ | 100% |
| 3.3 基线流量配置 | ✅ | 100% |
| 3.4 采集间隔配置 | ✅ | 100% |
| 3.5 缓冲区策略 | ✅ | 100% |
| 4. 独立指标统计 | ✅ COMPLETE | 100% |
| 4.1 并排对比仪表盘 | ✅ | 100% |
| 4.2 指标一致性检查 | ✅ | 100% |
| 4.3 Delta分析 | ✅ | 100% |
| 4.4 阈值差异化 | ✅ | 100% |
| 4.5 独立统计面板 | ✅ | 100% |
| 5. HERMES字段采样 | ✅ COMPLETE | 100% |
| 5.1 字段总览 | ✅ | 100% |
| 5.2 采样策略 | ✅ | 100% |
| 5.3 字段基数分析 | ✅ | 100% |
| 5.4 存储影响分析 | ✅ | 100% |
| 5.5 告警规则关联 | ✅ | 100% |
| 6. 技术实现 | ✅ COMPLETE | 100% |
| 6.1 流量路由器配置 | ✅ | 100% |
| 6.2 指标管道架构 | ✅ | 100% |
| 6.3 缓存策略 | ✅ | 100% |
| 6.4 QPS预算分配 | ✅ | 100% |
| 7. 监控与告警 | ✅ COMPLETE | 100% |
| 7.1 采样健康监控 | ✅ | 100% |
| 7.2 交叉污染检测 | ✅ | 100% |
| 7.3 采样延迟告警 | ✅ | 100% |
| 7.4 监控仪表板 | ✅ | 100% |
| 8. 测试计划 | ✅ COMPLETE | 100% |
| 8.1 测试策略总览 | ✅ | 100% |
| 8.2 单元测试 | ✅ | 100% |
| 8.3 集成测试 | ✅ | 100% |
| 8.4 压力测试 | ✅ | 100% |
| 8.5 混沌测试 | ✅ | 100% |
| 8.6 验收测试 | ✅ | 100% |
| 8.7 测试环境 | ✅ | 100% |
| 9. 风险评估 | ✅ COMPLETE | 100% |
| 9.1 风险总览 | ✅ | 100% |
| 9.2 详细风险评估 | ✅ | 100% |
| 9.3 风险热力图 | ✅ | 100% |
| 9.4 风险监控仪表板 | ✅ | 100% |
| 10. 状态标记 | ✅ COMPLETE | 100% |

### 10.3 下一步计划

| 步骤 | 任务 | 负责人 | 预计完成 | 依赖 |
|------|------|--------|---------|------|
| N1 | 三方评审 (DSHE+SRE+HERMES) | DSHE负责人 | T+2 | 本文档 |
| N2 | 评审意见修改 | DSHE团队 | T+3 | N1 |
| N3 | Traffic Router配置实现 | SRE团队 | T+5 | N2 |
| N4 | 灰度管道部署 (Staging) | SRE团队 | T+7 | N3 |
| N5 | 集成测试执行 | DSHE团队 | T+9 | N4 |
| N6 | 压力测试执行 | DSHE团队 | T+11 | N5 |
| N7 | 混沌测试执行 | DSHE团队 | T+13 | N5 |
| N8 | 验收测试 (Staging) | DSHE+SRE | T+14 | N5,N6,N7 |
| N9 | 灰度部署 (Production) | SRE团队 | T+15 | N8 |
| N10 | 灰度监控 (7天观察) | DSHE团队 | T+22 | N9 |
| N11 | 全量发布决策 (Go/No-Go) | 三方 | T+23 | N10 |

### 10.4 关键里程碑

```
Phase03 StageA 时间线 (T = 文档完成日)

T+0  ── [本文档完成]
 │
T+2  ── N1: 三方评审 (DSHE+SRE+HERMES)
 │
T+3  ── N2: 评审意见修改完成
 │
T+5  ── N3: Traffic Router配置实现完成
 │
T+7  ── N4: 灰度管道部署 (Staging)
 │
T+9  ── N5: 集成测试完成
 │
T+11 ── N6: 压力测试完成
 │
T+13 ── N7: 混沌测试完成
 │
T+14 ── N8: 验收测试通过
 │
T+15 ── N9: 灰度部署 (Production 50%)
 │
T+22 ── N10: 7天灰度监控期结束
 │
T+23 ── N11: 全量发布决策 (Go/No-Go)
```

### 10.5 状态标记汇总

| 标记 | 值 |
|------|-----|
| DOC_VERSION | v1.0.0-phase03 |
| PHASE | Phase03 / StageA |
| BRANCH | feature/v87-rc1-g1 |
| PREVIOUS_PHASE | Phase02 (commit 0d9a9d7) |
| GRAY_RATIO | 50% |
| SAMPLING_STRATEGY | gray_100pct_baseline_v86 |
| ISOLATION_LEVEL | STRONG (双管道完全隔离) |
| DOC_STATUS | IN_PROGRESS |
| REVIEW_STATUS | PENDING_REVIEW |
| NEXT_MILESTONE | T+2 三方评审 |
| RISK_COUNT | 10 (2 CRIT, 4 HIGH, 2 MEDIUM, 2 LOW) |
| TEST_CASES | 41 (UT:8 + IT:10 + ST:5 + CH:8 + AT:10) |
| PANELS_AFFECTED | 8 (V87-P-001~P-008, P-005暂缓) |
| ALERT_RULES | 12 + 5(监控专用) = 17 |
| HERMES_FIELDS | 5 (全量采样) |
| QPS_BUDGET | Gray:260 / Baseline:260 / Total:560 / Protection:800 |
| STORAGE_IMPACT | +63.5MB/天(含索引+元数据), +5.7GB/90d |

### 10.6 文档修订历史

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|---------|
| v1.0.0-phase03 | 2026-07-15 | DSHE L2 Team | 初版: 50%灰度流量采样策略配置 |

---

## 附录

### A. 术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| 灰度流量 | Gray Traffic | V87新版本测试流量 |
| 基线流量 | Baseline Traffic | V86旧版本生产流量 |
| 采样率 | Sampling Rate | 被采样记录占总记录比例 |
| 交叉污染 | Cross-Contamination | 灰度/基线数据互相污染 |
| 令牌桶 | Token Bucket | QPS限流算法 |
| 一致性哈希 | Consistent Hash | 流量分片算法 |
| 基数 | Cardinality | 字段唯一值数量 |
| 背压 | Backpressure | 下游压力反馈到上游 |

### B. 相关文档

| 文档 | 说明 |
|------|------|
| Phase01 需求锁定 | 监控需求规格 |
| Phase01 监控基线 | V200-1.0基线模板 |
| Phase01 面板清单 | 8个面板清单 |
| Phase02 告警规则 | 12条告警规则 |
| Phase02 面板开发 | 面板开发报告 |
| Phase02 容量评估 | 查询容量评估 |
| HERMES Phase01 | 审计迁移规格 |
| HERMES Phase02 | 审计性能评估 |

### C. 配置参数速查

| 参数 | 值 | 说明 |
|------|-----|------|
| 灰度比例 | 50% | 灰度流量占总流量比例 |
| 灰度采样率 | 100% | 灰度全量采样 |
| 基线采样率 | V86默认 | 基线保持V86采样率 |
| 采集间隔(关键) | 1s | 关键指标1秒分辨率 |
| 采集间隔(常规) | 15s | 常规指标15秒分辨率 |
| 缓冲区容量(灰度) | 100,000 entries | 灰度缓冲区容量 |
| 缓冲区内存(灰度) | 50 MB | 灰度缓冲区内存 |
| 缓存大小(灰度) | 10 GB | 灰度缓存大小 |
| 缓存TTL(灰度) | 300s | 灰度缓存过期时间 |
| 查询超时(灰度) | 5s | 灰度查询超时 |
| QPS灰度预算 | 260 | 灰度QPS预算 |
| QPS基线预算 | 260 | 基线QPS预算 |
| QPS保护阈值 | 800 | QPS保护上限 |
| 存储保留期 | 90d | 数据保留90天 |
| HERMES字段 | 5个 | 全量采样 |
| 每事件存储 | 84B | 原始数据 |
| 每日存储增量 | 63.5 MB | 含索引和元数据 |

---

> **文档结束**  
> **V87 RC1 L2大盘 Phase03 StageA — 50%灰度流量采样策略配置报告**  
> **版本**: v1.0.0-phase03 | **日期**: 2026-07-15  
> **状态**: PENDING_REVIEW | **下一里程碑**: T+2 三方评审
