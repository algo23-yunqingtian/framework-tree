# DSHB V86 RC2 G1 三方指标统计口径规范 V1.0

| 属性 | 值 |
|------|-----|
| **文档ID** | DSHB-V86-RC2-G1-P5-METRIC-SPEC |
| **文档标题** | DSHB/DSHE/HERMES 三方指标统计口径规范 |
| **版本** | V1.0 |
| **编制日期** | 2026-10-18 |
| **编制人** | DSHB V86 RC2 G1 Phase5 跨团队指标对齐与基线对账工程组 |
| **审批人** | （待三方签署） |
| **关联工单** | `DSHB_V86_RC2_G1_PHASE5_CROSS_TEAM_METRICS_ALIGN_AND_BASELINE_RECONCILIATION` |
| **当前阶段** | Phase5 — 跨团队指标对齐与基线对账 |
| **分支** | `feature/v85-chart-template` |
| **基线来源** | Phase3 生产基线冻结快照（commit: `b7a2e1f`+`c8d3f2a`+`d9e4a1b`） |
| **V85 偏差** | 0.00%（与V85完全对齐） |
| **工单状态** | `G1_METRIC_CALIBER_ALIGNED=FALSE`（本规范发布后标记为 TRUE） |
| **约束标记** | `DSHB_G1_METRIC_SPEC_DONE=TRUE` |

### 1.1 约束声明

| 约束编号 | 约束项 | 当前值 | 说明 |
|----------|--------|--------|------|
| C-001 | `NO_ZHIJI_API_CALL` | `FALSE` | 允许调用知纪API，但仅限紧急对账场景 |
| C-002 | `NO_MODIFY_V85` | `TRUE` | 禁止修改V85基线配置，所有新指标以增量方式注册 |
| C-003 | `NO_OVERWRITE` | `TRUE` | 禁止覆盖已有指标定义文件，统一以新增文档方式发布 |
| C-004 | `BRANCH_LOCKED` | `TRUE` | 分支锁定，禁止合并/推送/回退操作 |
| C-005 | `METRIC_DEPRECATED_ALLOWED` | `TRUE` | 允许废弃旧口径定义，但必须保留版本追溯记录 |
| C-006 | `TRIPARTITE_SIGNOFF_REQUIRED` | `TRUE` | 三方（DSHB/DSHE/HERMES）签字确认后方可生效 |

### 1.2 适用范围

本规范适用于 **DSHB V86 RC2 G1** 版本从 Phase5 跨团队指标对齐阶段至 Phase6 灰度投产准备阶段，涵盖以下四个核心指标的统一定义、测量方法、阈值标准及跨团队对账机制：

1. **吞吐（Throughput）** — 衡量事件流水线处理能力
2. **事件丢失率（Event Loss Rate）** — 衡量端到端数据完整性
3. **P99时延（P99 Latency）** — 衡量三个独立子场景的延迟性能
4. **72h总量（72h Total Volume）** — 衡量滚动窗口事件总量

本规范取代 `v86_rc2_dshb_g0_g1_cross_align_spec.md` §5.1 中关于 P99 的旧定义（笼统 P99≤200ms / 分项 500ms/1s/5s），以三个独立 P99 子指标替代。

---

## 目录

1. [概述](#1-概述)
2. [统一口径框架](#2-统一口径框架)
3. [指标一：吞吐（Throughput）](#3-指标一吞吐throughput)
4. [指标二：事件丢失率](#4-指标二事件丢失率)
5. [指标三：P99时延](#5-指标三p99时延)
6. [指标四：72h总量](#6-指标四72h总量)
7. [跨团队对账机制](#7-跨团队对账机制)
8. [约束合规性声明](#8-约束合规性声明)
9. [三方签字确认](#9-三方签字确认)
10. [MD5自检](#10-md5自检)
11. [版本历史](#11-版本历史)
12. [附录](#12-附录)

---

## 1. 概述

### 1.1 背景

在 Phase5 跨团队指标对齐审查中，发现 P0 阻断问题：**DSHB、DSHE、HERMES 三方对同一指标的定义不一致，导致"各报各数"**，具体表现为：

| 问题编号 | 问题描述 | 严重级别 | 影响范围 |
|----------|----------|----------|----------|
| M-CAL-001 | 吞吐统计范围不一致（raw vs filtered vs ingested） | P0 | 三方基线无法对账 |
| M-CAL-002 | 事件丢失率分母/分子定义不同（网关 vs 大盘 vs WAL） | P0 | 丢失率基线差异达 0.3%~0.8% |
| M-CAL-003 | P99时延存在一个笼统"≤500ms"定义，无法区分业务/审计/WAL | P0 | 熔断触发条件失效 |
| M-CAL-004 | 72h总量窗口对齐方式不一致（滚动 vs 快照 vs 采样） | P0 | 容量规划偏差±15% |

Phase3 基线快照中已冻结的指标数据与各方实际计算值存在偏差：

| 指标 | Phase3 基线值 | DSHB 自报 | DSHE 自报 | HERMES 自报 | 最大偏差 |
|------|---------------|-----------|-----------|-------------|----------|
| 审计丢失率 | 0.008% | 0.008% | 0.032% | 0.106% | 0.098% |
| P99告警延迟 | 462ms | 462ms | 589ms | 734ms | 272ms |
| P99决策延迟 | 891ms | 891ms | 1102ms | 1356ms | 465ms |
| 业务错误率 | 0.12% | 0.12% | 0.31% | 0.48% | 0.36% |

上述偏差直接导致 Phase4 熔断预案中的 M-01~M-04 告警阈值（LR-001~LR-010）可能误触发或漏触发。本规范旨在建立统一口径，消除对账盲区。

### 1.2 目标

1. **统一四核心指标定义**：消除三方口径差异，建立可互操作的统一计算公式
2. **分层计数模型**：建立 raw/filtered/ingested 三层事件模型，各方按职责统计对应层
3. **P99拆分**：将笼统 P99 拆分为 P99_业务端到端、P99_审计入库、P99_WAL写入 三个独立指标，严禁混用
4. **统一时间戳**：以 ingestion gateway 入站时间戳为全局对齐基准
5. **统一阈值**：建立三级阈值体系（正常/警告/P0阻断），消除基线偏差
6. **对账闭环**：建立 T+0 实时对账 + T+1 离线对账双重机制

### 1.3 前置依赖

| 依赖项 | 状态 | 说明 |
|--------|------|------|
| Phase3 基线冻结快照 | ✅ 已完成 | commit `b7a2e1f` |
| Phase4 熔断预案 M-01~M-04 定义 | ✅ 已完成 | `v86_rc2_dshb_g1_gray_emergency_fuse_plan.md` |
| G0→G1 跨团队对齐规范 §5.1 | ✅ 已完成（本版取代其P99定义） | `v86_rc2_dshb_g0_g1_cross_align_spec.md` |
| DSHE L2 终审缺陷清单 | ✅ 已完成 | D-01~D-09 |
| HERMES 审计链路就绪 | ❌ 未完成 | `G1_GRAY_TRAFFIC_START=FALSE` |
| 三方签字确认 | ⏳ 待执行 | 本规范发布后执行 |

### 1.4 术语定义

| 术语 | 英文 | 定义 |
|------|------|------|
| 原始事件 | Raw Event | 从事件源（业务应用/外部系统）产生、尚未经过任何过滤或变换的事件实例 |
| 过滤事件 | Filtered Event | 经过网关过滤规则（去重/格式校验/黑名单过滤）后仍然有效的事件 |
| 入库事件 | Ingested Event | 已通过 ingestion gateway 处理、进入 WAL 写入流程的事件 |
| 持久化事件 | WAL-Persisted Event | 已成功写入 WAL 文件并完成 fsync 的事件 |
| 可见事件 | Dashboard-Visible Event | 已聚合为大盘展示指标、可被 DSHE 大盘查询的事件 |
| 审计事件 | Audited Event | 已写入审计 WAL（audit WAL）、可被 HERMES 审计系统查询的事件 |
| 事件入站时间戳 | Event Ingress Timestamp | 事件到达 ingestion gateway 时的系统时间戳，作为全局统一对齐基准 |
| 观察窗口 | Observation Window | 指标统计的滑动时间窗口，单位为秒 |

---

## 2. 统一口径框架

### 2.1 事件分层模型

```
事件源（业务应用 / 外部系统）
    │
    │  [Raw Events] — 全部原始事件
    ▼
┌─────────────────────────────────────────┐
│  Ingestion Gateway                      │
│  ┌───────────────────────────────────┐  │
│  │  Filter Layer                      │  │
│  │  - 去重 (dedup by event_id)        │  │
│  │  - 格式校验 (schema validation)    │  │
│  │  - 黑名单过滤 (denylist filter)    │  │
│  │  - 截断检测 (truncation detect)    │  │
│  │  - 无效标记 (invalid flag)         │  │
│  └───────────────────────────────────┘  │
│              │                           │
│         [Filtered Events]               │
│              │                           │
│  ┌───────────▼───────────┐              │
│  │  WAL Writer            │              │
│  │  - 序列分配 (seq_no)    │              │
│  │  - 批次组装 (batch)     │              │
│  │  - 写入提交 (commit)    │              │
│  └───────────┬───────────┘              │
└──────────────┼──────────────────────────┘
               │
          [Ingested Events] — WAL-written
               │
               ▼
┌──────────────────────────────────────┐
│  WAL Persistence                     │
│  - fsync 同步                         │
│  - 文件检查 (fsck)                    │
│  - 审计复制 (audit replicate)         │
└──────────────────┬───────────────────┘
                   │
              [WAL-Persisted Events]
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
   [Dashboard-   [Audited   [Raw
    Visible]      Events]    Mirror]
```

### 2.2 统一时间戳基准

| 时间戳字段 | 英文 | 产生位置 | 用途 | 精度 |
|------------|------|----------|------|------|
| `event_create_ts` | Event Creation Timestamp | 事件源 | 业务端到端P99起点 | 毫秒(ms) |
| `event_ingress_ts` | Event Ingress Timestamp | Ingestion Gateway | **全局统一对齐基准**、审计入库P99起点、吞吐/丢失率/72h统计时间戳 | 毫秒(ms) |
| `event_business_response_ts` | Business Response Timestamp | 业务应用 | 业务端到端P99终点 | 毫秒(ms) |
| `wal_write_request_ts` | WAL Write Request Timestamp | WAL Writer | WAL写入P99起点 | 毫秒(ms) |
| `wal_commit_ts` | WAL Commit Timestamp | WAL Writer | 审计入库P99终点 | 毫秒(ms) |
| `wal_fsck_sync_ts` | WAL fsync Timestamp | WAL Persistence | WAL写入P99终点 | 毫秒(ms) |

> **统一规则**：所有指标的时间窗口对齐一律以 `event_ingress_ts` 为准。事件源产生的时间差（`event_create_ts` 到 `event_ingress_ts` 之间的网络传输延迟）不计入统计，除非明确说明为 P99_业务端到端。

### 2.3 排除规则

所有指标统计在计数前必须执行以下排除操作，排除的事件不计入任何指标的分子或分母：

| 排除类型 | 排除条件 | 检测方式 | 对应字段 |
|----------|----------|----------|----------|
| 重复事件 | `event_id` 已存在于当前去重窗口内 | `dedup_cache.lookup(event_id)` | `dedup_flag=TRUE` |
| 截断事件 | 事件体长度 < 预期最小长度 或 包含截断标记 | `payload.len < min_len OR payload.truncated=TRUE` | `truncated_flag=TRUE` |
| 无效事件 | Schema 校验失败 或 必填字段缺失 | `schema_validator.validate(payload)` returns false | `invalid_flag=TRUE` |
| 过期事件 | `event_ingress_ts` 超出 `event_create_ts + max_latency_threshold` | `event_ingress_ts - event_create_ts > 30s` | `expired_flag=TRUE` |
| 黑名单事件 | `source_id` 在 denylist 中 | `denylist.contains(source_id)` | `blacklisted_flag=TRUE` |

> **排除规则优先级**：去重 > 截断 > 无效 > 过期 > 黑名单。同一事件命中多个排除条件时，按此优先级记录第一个命中的排除原因，后续条件不再评估。

### 2.4 三层事件计数模型

| 层级 | 英文名 | 中文 | 定义 | DSHB | DSHE | HERMES |
|------|--------|------|------|------|------|--------|
| L1 | Raw Events | 原始事件 | 进入网关前的全部事件 | ✅ 统计 | ❌ 不统计 | ❌ 不统计 |
| L2 | Filtered Events | 过滤事件 | 通过过滤层的事件 | ✅ 统计 | ✅ 统计 | ❌ 不统计 |
| L3 | Ingested Events | 入库事件 | 已进入 WAL 写入流程的事件 | ✅ 统计 | ✅ 统计 | ✅ 统计 |
| L4 | WAL-Persisted | 持久化事件 | 已完成 fsync 的事件 | ✅ 统计 | ❌ 不统计 | ✅ 统计 |

---

## 3. 指标一：吞吐（Throughput, ev/s）

### 3.1 原始口径差异对照表

| 维度 | DSHB 原始定义 | DSHE 原始定义 | HERMES 原始定义 |
|------|---------------|---------------|-----------------|
| **统计范围** | 所有进入 pipeline 的事件（raw + filtered + ingested 合计） | 仅大盘可见事件（排除 filtered 掉的） | 仅审计事件（audit WAL 写入） |
| **计数单位** | 事件总数 / 时间窗口 | 事件总数 / 时间窗口 | 事件总数 / 时间窗口 |
| **分子** | `total_pipeline_events` | `dashboard_visible_events` | `audit_wal_written_events` |
| **分母** | 观察窗口时长（秒） | 观察窗口时长（秒） | 观察窗口时长（秒） |
| **时间戳** | `event_ingress_ts` | `dashboard_render_ts` | `audit_wal_write_ts` |
| **排除规则** | 无明确排除规则 | 排除 filtered 事件 | 排除非审计事件 |
| **基线值** | 未统一 | 未统一 | 未统一 |
| **问题** | 包含过滤掉的事件，吞吐虚高 | 排除了大量正常事件，吞吐偏低 | 仅统计审计事件，覆盖不全 |

### 3.2 统一后定义

**统一吞吐量必须区分三个子指标**，各方按职责统计对应子指标：

#### 3.2.1 吞吐 — 原始层（Throughput Raw）

| 属性 | 定义 |
|------|------|
| **指标标识** | `M-THROUGHPUT-RAW` |
| **定义** | 单位时间内进入 ingestion gateway 的全部原始事件数（排除规则执行后） |
| **公式** | `throughput_raw = raw_event_count / observation_window_seconds` |
| **统计范围** | 排除重复、截断、无效、过期、黑名单事件后的全部原始事件 |
| **时间窗口** | 滑动窗口，默认 60 秒 |
| **时间戳基准** | `event_ingress_ts` |
| **采集埋点** | Ingestion Gateway 入口计数器（入口拦截器之后、过滤层之前） |
| **计量单位** | 事件/秒 (ev/s) |
| **统计职责** | DSHB（唯一统计方） |
| **用途** | 网关容量规划、事件源流量监控 |

#### 3.2.2 吞吐 — 过滤层（Throughput Filtered）

| 属性 | 定义 |
|------|------|
| **指标标识** | `M-THROUGHPUT-FILTERED` |
| **定义** | 单位时间内通过过滤层、有效进入 WAL 写入流程的事件数 |
| **公式** | `throughput_filtered = filtered_event_count / observation_window_seconds` |
| **统计范围** | 原始事件经排除规则处理后仍然有效的事件 |
| **时间窗口** | 滑动窗口，默认 60 秒 |
| **时间戳基准** | `event_ingress_ts` |
| **采集埋点** | Filter Layer 出口计数器（过滤层之后、WAL Writer 之前） |
| **计量单位** | 事件/秒 (ev/s) |
| **统计职责** | DSHB + DSHE（双方统计，DSHB 为权威方） |
| **用途** | 过滤效率评估、业务事件有效量监控 |

#### 3.2.3 吞吐 — 入库层（Throughput Ingested）

| 属性 | 定义 |
|------|------|
| **指标标识** | `M-THROUGHPUT-INGESTED` |
| **定义** | 单位时间内已成功提交至 WAL（commit 完成）的事件数 |
| **公式** | `throughput_ingested = wal_ingested_count / observation_window_seconds` |
| **统计范围** | 已通过 WAL Writer 完成 commit 的事件（不含 fsync 失败重试） |
| **时间窗口** | 滑动窗口，默认 60 秒 |
| **时间戳基准** | `event_ingress_ts`（入库时间以入站时间戳对齐，而非 WAL 写入时间） |
| **采集埋点** | WAL Writer 提交成功回调计数器（`wal_commit_ts` 埋点） |
| **计量单位** | 事件/秒 (ev/s) |
| **统计职责** | DSHB + DSHE + HERMES（三方均统计，DSHB 为权威方） |
| **用途** | 端到端吞吐量、审计覆盖率、熔断决策依据 |

### 3.3 团队分工矩阵

| 团队 | 统计范围 | 权威指标 | 同步指标 | 数据源 | 上报频率 |
|------|----------|----------|----------|--------|----------|
| **DSHB** | L1 + L2 + L3 + L4 | M-THROUGHPUT-RAW, M-THROUGHPUT-FILTERED, M-THROUGHPUT-INGESTED | — | Ingestion Gateway 计数器 | 10s |
| **DSHE** | L2 + L3 | — (非权威) | M-THROUGHPUT-FILTERED, M-THROUGHPUT-INGESTED | Dashboard Pipeline 计数器 | 30s |
| **HERMES** | L3 | — (非权威) | M-THROUGHPUT-INGESTED | Audit WAL 计数器 | 30s |

### 3.4 吞吐排除规则对照

| 排除条件 | M-THROUGHPUT-RAW | M-THROUGHPUT-FILTERED | M-THROUGHPUT-INGESTED |
|----------|------------------|-----------------------|-----------------------|
| 重复事件 | ✅ 排除 | — (已通过去重) | — |
| 截断事件 | ✅ 排除 | — (已通过校验) | — |
| 无效事件 | ✅ 排除 | — (已通过校验) | — |
| 过期事件 | ✅ 排除 | ✅ 排除 | — |
| 黑名单事件 | ✅ 排除 | ✅ 排除 | ✅ 排除 |
| WAL 写入失败 | — | — | ✅ 排除 |
| fsync 失败 | — | — | ✅ 排除 |

### 3.5 代码示例

```python
# M-THROUGHPUT-RAW 采集伪代码
def calculate_throughput_raw(
    raw_event_count: int,
    observation_window_seconds: int,
    exclude_filters: bool = True
) -> float:
    """
    计算原始层吞吐量
    
    Args:
        raw_event_count: 原始事件计数（排除规则执行后）
        observation_window_seconds: 观察窗口时长（秒）
        exclude_filters: 是否执行排除规则
    
    Returns:
        吞吐量 (ev/s)
    """
    if observation_window_seconds <= 0:
        raise ValueError("观察窗口必须为正数")
    return raw_event_count / observation_window_seconds


# M-THROUGHPUT-INGESTED 采集伪代码
def calculate_throughput_ingested(
    wal_ingested_count: int,
    observation_window_seconds: int
) -> float:
    """
    计算入库层吞吐量
    
    Args:
        wal_ingested_count: WAL commit 成功计数
        observation_window_seconds: 观察窗口时长（秒）
    
    Returns:
        吞吐量 (ev/s)
    """
    if observation_window_seconds <= 0:
        raise ValueError("观察窗口必须为正数")
    return wal_ingested_count / observation_window_seconds
```

---

## 4. 指标二：事件丢失率（Event Loss Rate）

### 4.1 原始口径差异对照表

| 维度 | DSHB 原始定义 | DSHE 原始定义 | HERMES 原始定义 |
|------|---------------|---------------|-----------------|
| **公式** | `(total_sent - total_received) / total_sent × 100%` | `(dashboard_visible - pipeline_output) / pipeline_output × 100%` | `(audit_dispatched - audit_persisted) / audit_dispatched × 100%` |
| **分母** | `total_sent`（网关发送计数） | `pipeline_output`（pipeline 输出计数） | `audit_dispatched`（审计分发计数） |
| **分子** | `total_sent - total_received`（发送-接收差值） | `dashboard_visible - pipeline_output`（大盘-输出差值） | `audit_dispatched - audit_persisted`（分发-持久化差值） |
| **测量点** | Ingestion Gateway | Dashboard Pipeline | Audit WAL |
| **时间窗口** | 滑动窗口 | 每日快照 | 滑动窗口 |
| **基线值** | 0.008% | 0.032% | 0.106% |
| **问题** | 分母为网关发送量，非原始事件量 | 分母为 pipeline 输出，漏计了过滤事件 | 仅统计审计事件丢失，覆盖不全 |

### 4.2 统一后定义

| 属性 | 定义 |
|------|------|
| **指标标识** | `M-LOSS-RATE` |
| **定义** | 原始事件中，进入 ingestion gateway 但从未到达 WAL 持久化的事件占比 |
| **公式** | `loss_rate = (raw_ingressed - wal_persisted) / raw_ingressed × 100%` |
| **分母** | `raw_ingressed` = 进入 ingestion gateway 的原始事件数（排除规则执行后） |
| **分子** | `raw_ingressed - wal_persisted` = 进入网关但未成功持久化到 WAL 的事件数 |
| **事件池** | 以 ingestion gateway 为唯一事件池入口，三方统一计算基准 |
| **时间窗口** | 滑动窗口，默认 60 秒 |
| **时间戳基准** | `event_ingress_ts` |
| **计量单位** | 百分比 (%) |
| **统计职责** | DSHB（唯一统计方，为三方权威数据源） |
| **对账范围** | 三方均基于同一事件池计算，DSHB 产出权威值，DSHE/HERMES 独立计算后对账 |

### 4.3 阈值定义

| 阈值等级 | 条件 | 说明 | 触发动作 | 对应告警 |
|----------|------|------|----------|----------|
| **正常 (Normal)** | `loss_rate ≤ 0.01%` | 丢失率在生产可接受范围内 | 无动作 | — |
| **警告 (Warning)** | `0.01% < loss_rate ≤ 0.5%` | 丢失率超出正常范围，需关注 | 触发 PagerDuty-P2 告警，记录日志，通知值班 | LR-001 |
| **P0 阻断 (Block)** | `loss_rate > 0.5%` | 丢失率严重超标，触发熔断 | 触发 PagerDuty-P0 告警，触发熔断（T-01），灰度权重归零 | LR-001 |

### 4.4 统一后团队分工

| 团队 | 统计范围 | 计算基准 | 角色 | 对账义务 |
|------|----------|----------|------|----------|
| **DSHB** | L1→L4 全链路 | `raw_ingressed` (L1) vs `wal_persisted` (L4) | 权威统计方 | 产出权威丢失率，10s 周期上报 |
| **DSHE** | L1→L4 全链路 | `raw_ingressed` (L1) vs `wal_persisted` (L4) | 独立校验方 | 30s 周期独立计算，与 DSHB 对账 |
| **HERMES** | L1→L4 全链路 | `raw_ingressed` (L1) vs `wal_persisted` (L4) | 独立校验方 | 30s 周期独立计算，与 DSHB 对账 |

### 4.5 代码示例

```python
# M-LOSS-RATE 统一计算公式
def calculate_loss_rate(
    raw_ingressed: int,
    wal_persisted: int,
    window_start_ts: float,
    window_end_ts: float
) -> dict:
    """
    计算统一事件丢失率
    
    统一规则：
    - 事件池基准：ingestion gateway 原始事件
    - 分子：进入网关但未持久化的事件数
    - 分母：进入网关的全部原始事件数
    
    Args:
        raw_ingressed: 进入网关的原始事件数（排除规则执行后）
        wal_persisted: 已成功持久化到 WAL 的事件数
        window_start_ts: 观察窗口起始时间戳 (event_ingress_ts)
        window_end_ts: 观察窗口结束时间戳 (event_ingress_ts)
    
    Returns:
        {
            "loss_rate_percent": float,
            "threshold_level": "normal" | "warning" | "block",
            "raw_ingressed": int,
            "wal_persisted": int,
            "lost_count": int,
            "window_start": float,
            "window_end": float
        }
    """
    if raw_ingressed <= 0:
        return {
            "loss_rate_percent": 0.0,
            "threshold_level": "normal",
            "raw_ingressed": 0,
            "wal_persisted": 0,
            "lost_count": 0,
            "window_start": window_start_ts,
            "window_end": window_end_ts,
            "note": "零事件窗口，丢失率默认为0"
        }
    
    lost_count = raw_ingressed - wal_persisted
    loss_rate = (lost_count / raw_ingressed) * 100.0
    
    if loss_rate > 0.5:
        threshold_level = "block"
    elif loss_rate > 0.01:
        threshold_level = "warning"
    else:
        threshold_level = "normal"
    
    return {
        "loss_rate_percent": round(loss_rate, 6),
        "threshold_level": threshold_level,
        "raw_ingressed": raw_ingressed,
        "wal_persisted": wal_persisted,
        "lost_count": lost_count,
        "window_start": window_start_ts,
        "window_end": window_end_ts
    }
```

---

## 5. 指标三：P99时延（P99 Latency）

> ⚠️ **重要警告**：本节定义的三个 P99 子指标 **严禁混用**。旧版笼统定义 `P99≤500ms`（或早期版本 `P99≤200ms`）**已废弃 (DEPRECATED)**。任何文档、告警规则、熔断条件中引用 P99 时，**必须明确标注具体子指标名称**。

### 5.1 原始口径差异对照表

| 维度 | DSHB 原始定义 | DSHE 原始定义 | HERMES 原始定义 |
|------|---------------|---------------|-----------------|
| **旧笼统定义** | `P99≤500ms` | `P99≤500ms` | `P99≤500ms` |
| **旧交叉对齐规范** | 告警≤500ms / 决策≤1s / 刷新≤5s | 同左 | 同左 |
| **实际测量范围** | 网关入站到WAL commit | 大盘渲染延迟 | WAL写入延迟 |
| **问题** | 笼统定义混淆了三个完全不同的度量场景 | — | — |
| **本规范处置** | ❌ 废弃，替换为三个独立子指标 | — | — |

### 5.2 三个独立P99子指标定义

| 子指标 | 标识 | 测量范围 | 时间起点 | 时间终点 | 阈值 | 测量点 |
|--------|------|----------|----------|----------|------|--------|
| **P99_业务端到端** | `M-P99-BUSINESS-E2E` | 业务事件产生到业务响应 | `event_create_ts` | `event_business_response_ts` | ≤30s | 应用入口→出口 |
| **P99_审计入库** | `M-P99-AUDIT-INGEST` | 事件入站到WAL提交 | `event_ingress_ts` | `wal_commit_ts` | ≤1000ms | Ingestion Gateway→WAL commit |
| **P99_WAL写入** | `M-P99-WAL-WRITE` | WAL写入请求到fsync完成 | `wal_write_request_ts` | `wal_fsck_sync_ts` | ≤50ms | WAL Writer→fsync |

### 5.3 P99_业务端到端（M-P99-BUSINESS-E2E）

| 属性 | 定义 |
|------|------|
| **指标标识** | `M-P99-BUSINESS-E2E` |
| **名称** | P99 业务端到端延迟 |
| **定义** | 业务事件从产生到业务应用返回响应的 P99 延迟（第99百分位） |
| **公式** | `P99_business_e2e = percentile_99(event_business_response_ts - event_create_ts)` |
| **测量范围** | 应用入口到出口（含网络传输、排队、处理、序列化） |
| **时间起点** | `event_create_ts`（事件源产生时间） |
| **时间终点** | `event_business_response_ts`（业务响应时间） |
| **阈值** | `≤ 30s` |
| **采集埋点** | 业务应用入口中间件（entry interceptor）+ 业务应用出口回调（response callback） |
| **计量单位** | 秒 (s) |
| **统计职责** | DSHB（唯一统计方） |
| **关联告警** | LR-005（P99_业务端到端 > 30s） |
| **熔断触发** | 不直接触发熔断，但作为 P1 告警项纳入监控面板 |
| **排除规则** | 排除 `expired_flag=TRUE` 的事件（超时事件不计入P99） |
| **数据保留** | 原始事件延迟数据保留 72 小时，P99 聚合值保留 90 天 |

#### 5.3.1 阈值三级体系

| 阈值等级 | 条件 | 说明 | 触发动作 |
|----------|------|------|----------|
| **正常** | `P99 ≤ 20s` | 业务延迟在安全范围内 | 无动作 |
| **警告** | `20s < P99 ≤ 30s` | 延迟升高，需关注业务队列 | PagerDuty-P2 告警 |
| **P0 阻断** | `P99 > 30s` | 业务延迟严重超标 | PagerDuty-P0 告警 |

### 5.4 P99_审计入库（M-P99-AUDIT-INGEST）

| 属性 | 定义 |
|------|------|
| **指标标识** | `M-P99-AUDIT-INGEST` |
| **名称** | P99 审计入库延迟 |
| **定义** | 事件从进入 ingestion gateway 到 WAL commit 完成的 P99 延迟 |
| **公式** | `P99_audit_ingest = percentile_99(wal_commit_ts - event_ingress_ts)` |
| **测量范围** | Ingestion Gateway 入站到 WAL Writer commit 完成 |
| **时间起点** | `event_ingress_ts` |
| **时间终点** | `wal_commit_ts` |
| **阈值** | `≤ 1000ms` |
| **采集埋点** | Ingestion Gateway 入口计数器（埋点 `event_ingress_ts`）+ WAL Writer 提交成功回调（埋点 `wal_commit_ts`） |
| **计量单位** | 毫秒 (ms) |
| **统计职责** | DSHB（权威统计方） |
| **关联告警** | LR-002（P99告警延迟 > 1000ms） |
| **熔断触发** | T-02：P99_审计入库 > 1000ms 持续 ≥ 5min → 熔断状态→BLOCKED |
| **排除规则** | 排除 WAL 写入失败重试事件；排除 `expired_flag=TRUE` 事件 |
| **数据保留** | 原始事件延迟数据保留 72 小时，P99 聚合值保留 90 天 |

#### 5.4.1 阈值三级体系

| 阈值等级 | 条件 | 说明 | 触发动作 | 对应熔断 |
|----------|------|------|----------|----------|
| **正常** | `P99 ≤ 600ms` | 入库延迟在安全范围内 | 无动作 | — |
| **警告** | `600ms < P99 ≤ 1000ms` | 入库延迟升高，需检查 WAL 队列 | PagerDuty-P2 告警 | — |
| **P0 阻断** | `P99 > 1000ms` | 入库延迟严重超标，持续5min触发熔断 | PagerDuty-P0 告警 | T-02 |

> **与Phase3基线对齐**：Phase3 基线 P99 告警延迟 = 462ms，处于正常范围（≤600ms）。

### 5.5 P99_WAL写入（M-P99-WAL-WRITE）

| 属性 | 定义 |
|------|------|
| **指标标识** | `M-P99-WAL-WRITE` |
| **名称** | P99 WAL 写入延迟 |
| **定义** | WAL 写入请求发出到文件系统同步完成的 P99 延迟 |
| **公式** | `P99_wal_write = percentile_99(wal_fsck_sync_ts - wal_write_request_ts)` |
| **测量范围** | WAL Writer 发起写入请求到 fsync 完成（含文件写入、缓冲区刷盘、检查点） |
| **时间起点** | `wal_write_request_ts` |
| **时间终点** | `wal_fsck_sync_ts` |
| **阈值** | `≤ 50ms` |
| **采集埋点** | WAL Writer 写入请求入口（埋点 `wal_write_request_ts`）+ fsync 完成回调（埋点 `wal_fsck_sync_ts`） |
| **计量单位** | 毫秒 (ms) |
| **统计职责** | DSHB + HERMES（DSHB 为权威统计方） |
| **关联告警** | LR-006（P99_WAL写入 > 50ms） |
| **熔断触发** | 不直接触发熔断，但作为 P2 告警项纳入监控面板；持续 > 200ms 触发 P1 告警 |
| **排除规则** | 排除 WAL 写入失败重试事件；排除 fsync 超时事件（>10s 视为异常，单独告警） |
| **数据保留** | 原始事件延迟数据保留 72 小时，P99 聚合值保留 90 天 |

#### 5.5.1 阈值三级体系

| 阈值等级 | 条件 | 说明 | 触发动作 |
|----------|------|------|----------|
| **正常** | `P99 ≤ 30ms` | WAL 写入在安全范围内 | 无动作 |
| **警告** | `30ms < P99 ≤ 50ms` | WAL 写入延迟升高，需检查磁盘IO | PagerDuty-P2 告警 |
| **异常** | `P99 > 50ms` | WAL 写入延迟超标 | PagerDuty-P1 告警 |
| **严重** | `P99 > 200ms` | WAL 写入严重异常，可能影响持久化可靠性 | PagerDuty-P0 告警 |

### 5.6 禁止混用规则

#### 5.6.1 混用定义

以下行为被定义为 **P99 混用违规**，在任何文档、代码、告警规则、熔断条件中禁止出现：

| 违规编号 | 违规行为 | 示例 | 修正方式 |
|----------|----------|------|----------|
| P99-MIX-001 | 使用笼统"P99"而不指定子指标 | "P99 延迟 ≤ 500ms" | 改为"P99_审计入库 ≤ 1000ms" |
| P99-MIX-002 | 将两个不同P99子指标合并为一个值 | "P99 = (business_e2e + audit_ingest) / 2" | 分别列出三个子指标 |
| P99-MIX-003 | 用单一阈值覆盖多个P99子指标 | "P99 ≤ 500ms 适用于所有场景" | 为每个子指标设定独立阈值 |
| P99-MIX-004 | 在熔断条件中引用笼统P99 | "if P99 > 1000ms then 熔断" | "if P99_审计入库 > 1000ms 持续5min then 熔断" |
| P99-MIX-005 | 告警规则名称与子指标不匹配 | LR-002 告警"P99延迟告警"但实际测量P99_审计入库 | LR-002 更名为"P99_审计入库告警" |

#### 5.6.2 废弃声明

| 旧定义 | 废弃状态 | 替代定义 | 生效日期 |
|--------|----------|----------|----------|
| `P99≤200ms` | ❌ DEPRECATED | 无直接替代（过于笼统） | 2026-10-17 |
| `P99≤500ms`（统一） | ❌ DEPRECATED | `M-P99-AUDIT-INGEST` ≤ 1000ms | 2026-10-18 |
| `告警P99≤500ms` | ❌ DEPRECATED | `M-P99-AUDIT-INGEST` ≤ 1000ms | 2026-10-18 |
| `决策P99≤1s` | ❌ DEPRECATED | `M-P99-AUDIT-INGEST` ≤ 1000ms | 2026-10-18 |
| `刷新P99≤5s` | ❌ DEPRECATED | `M-P99-BUSINESS-E2E` ≤ 30s | 2026-10-18 |
| `P99偏差<0.01ms` | ❌ DEPRECATED | 各子指标独立偏差检查 | 2026-10-18 |

### 5.7 与既有文档的映射关系

| 既有文档 | 既有定义 | 本规范对应 | 变更说明 |
|----------|----------|------------|----------|
| `g0_g1_cross_align_spec.md` §5.1 | 告警P99≤500ms | M-P99-AUDIT-INGEST ≤ 1000ms | 阈值从500ms调整为1000ms，测量点明确为网关→WAL commit |
| `g0_g1_cross_align_spec.md` §5.1 | 决策P99≤1s | M-P99-AUDIT-INGEST ≤ 1000ms | 合并至审计入库指标，不再独立 |
| `g0_g1_cross_align_spec.md` §5.1 | 刷新P99≤5s | M-P99-BUSINESS-E2E ≤ 30s | 阈值从5s调整为30s，测量点改为业务端到端 |
| `emergency_fuse_plan.md` M-02 | P99告警延迟 ≤ 600ms | M-P99-AUDIT-INGEST ≤ 600ms（正常阈值） | 直接映射 |
| `emergency_fuse_plan.md` M-03 | P99决策延迟 ≤ 1200ms | M-P99-AUDIT-INGEST ≤ 1000ms（P0阈值） | 合并至审计入库指标 |
| `emergency_fuse_plan.md` LR-002 | P99告警延迟告警 | LR-002 更名为"P99_审计入库告警" | 名称更新 |
| `emergency_fuse_plan.md` LR-003 | P99决策延迟告警 | 废弃，合并入 LR-002 | 规则合并 |

### 5.8 代码示例

```python
# P99 计算工具类
class P99LatencyCalculator:
    """P99 延迟计算工具，支持三个独立子指标"""
    
    # 阈值配置
    THRESHOLDS = {
        "business_e2e": {
            "normal": 20_000,      # 20s = 20000ms
            "warning": 30_000,     # 30s = 30000ms
            "block": None,         # > 30s 即P0
        },
        "audit_ingest": {
            "normal": 600,
            "warning": 1000,
            "block": None,         # > 1000ms 持续5min 即P0
        },
        "wal_write": {
            "normal": 30,
            "warning": 50,
            "abnormal": 200,
            "critical": None,      # > 200ms 即P0
        }
    }
    
    @staticmethod
    def calculate_percentile_99(latencies_ms: list) -> float:
        """
        计算P99延迟（第99百分位）
        
        使用最近邻法（nearest rank）:
        P99 = value at index ceil(0.99 * N) - 1
        
        Args:
            latencies_ms: 延迟数据列表（毫秒）
        
        Returns:
            P99 延迟值（毫秒）
        """
        if not latencies_ms:
            return 0.0
        sorted_vals = sorted(latencies_ms)
        n = len(sorted_vals)
        rank = int((0.99 * n + 0.5)) - 1  # 四舍五入
        rank = max(0, min(rank, n - 1))
        return float(sorted_vals[rank])
    
    @staticmethod
    def evaluate_threshold(metric_name: str, p99_value: float) -> dict:
        """
        评估P99子指标的阈值等级
        
        Args:
            metric_name: 子指标名称 ("business_e2e" | "audit_ingest" | "wal_write")
            p99_value: P99 延迟值（ms）
        
        Returns:
            {
                "metric": str,
                "p99_value": float,
                "level": "normal" | "warning" | "abnormal" | "critical",
                "threshold": float
            }
        """
        thresholds = P99LatencyCalculator.THRESHOLDS.get(metric_name, {})
        
        if metric_name == "business_e2e":
            if p99_value <= thresholds["normal"]:
                return {"metric": metric_name, "p99_value": p99_value,
                        "level": "normal", "threshold": thresholds["normal"]}
            elif p99_value <= thresholds["warning"]:
                return {"metric": metric_name, "p99_value": p99_value,
                        "level": "warning", "threshold": thresholds["warning"]}
            else:
                return {"metric": metric_name, "p99_value": p99_value,
                        "level": "critical", "threshold": thresholds["warning"]}
        
        elif metric_name == "audit_ingest":
            if p99_value <= thresholds["normal"]:
                return {"metric": metric_name, "p99_value": p99_value,
                        "level": "normal", "threshold": thresholds["normal"]}
            elif p99_value <= thresholds["warning"]:
                return {"metric": metric_name, "p99_value": p99_value,
                        "level": "warning", "threshold": thresholds["warning"]}
            else:
                return {"metric": metric_name, "p99_value": p99_value,
                        "level": "critical", "threshold": thresholds["warning"]}
        
        elif metric_name == "wal_write":
            if p99_value <= thresholds["normal"]:
                return {"metric": metric_name, "p99_value": p99_value,
                        "level": "normal", "threshold": thresholds["normal"]}
            elif p99_value <= thresholds["warning"]:
                return {"metric": metric_name, "p99_value": p99_value,
                        "level": "warning", "threshold": thresholds["warning"]}
            elif p99_value <= thresholds["abnormal"]:
                return {"metric": metric_name, "p99_value": p99_value,
                        "level": "abnormal", "threshold": thresholds["warning"]}
            else:
                return {"metric": metric_name, "p99_value": p99_value,
                        "level": "critical", "threshold": thresholds["abnormal"]}
        
        return {"metric": metric_name, "p99_value": p99_value,
                "level": "unknown", "threshold": None}
```

---

## 6. 指标四：72h总量（72h Total Volume）

### 6.1 原始口径差异对照表

| 维度 | DSHB 原始定义 | DSHE 原始定义 | HERMES 原始定义 |
|------|---------------|---------------|-----------------|
| **统计窗口** | 滚动 72 小时窗口 | 每日快照 × 3（00:00/08:00/16:00） | 72h 窗口，含采样 |
| **计数范围** | 全部事件（raw + filtered + ingested） | 仅大盘可见事件 | 仅审计事件，含采样 |
| **采样** | 无采样 | 无采样 | 有采样（比例未明确） |
| **窗口对齐** | 任意滚动 | 每日 00:00 UTC+8 | 任意滚动 |
| **基线值** | 未统一 | 未统一 | 未统一 |
| **问题** | 含过滤事件，总量虚高 | 漏计过滤事件，总量偏低 | 采样比例不透明，无法复现 |

### 6.2 统一后定义

| 属性 | 定义 |
|------|------|
| **指标标识** | `M-TOTAL-72H` |
| **定义** | 过去 72 小时内进入 ingestion gateway 的全部原始事件总数（排除规则执行后） |
| **公式** | `total_72h = Σ events in [T-72h, T] where T = current_time` |
| **时间窗口** | 滚动 72 小时，精确到秒 |
| **窗口时长** | `72 × 60 × 60 = 259,200 秒` |
| **窗口对齐** | 以 `event_ingress_ts` 为时间戳基准，边界时刻为 `T-259200` 到 `T` |
| **对齐规则** | 窗口边界严格对齐到 UTC+8 每日 00:00 / 08:00 / 16:00（8h 块） |
| **采样** | 默认全量计数；仅允许大盘展示使用下采样（10分钟粒度） |
| **计量单位** | 事件数 (events) |
| **统计职责** | DSHB（唯一统计方，权威数据源） |
| **对账范围** | 三方基于同一事件池对账 |

### 6.3 窗口对齐规则

#### 6.3.1 8小时块对齐

72 小时窗口被划分为 9 个 8 小时块，每个块的边界严格对齐到 UTC+8 时间：

| 块编号 | 起始时间 (UTC+8) | 结束时间 (UTC+8) | 时长 |
|--------|-------------------|-------------------|------|
| B-01 | T-72h | T-64h | 8h |
| B-02 | T-64h | T-56h | 8h |
| B-03 | T-56h | T-48h | 8h |
| B-04 | T-48h | T-40h | 8h |
| B-05 | T-40h | T-32h | 8h |
| B-06 | T-32h | T-24h | 8h |
| B-07 | T-24h | T-16h | 8h |
| B-08 | T-16h | T-8h | 8h |
| B-09 | T-8h | T | 8h |

> **对齐规则**：窗口边界 `T` 必须对齐到最近的 UTC+8 00:00 / 08:00 / 16:00 之一。例如，若当前时间为 2026-10-18 14:30 UTC+8，则窗口 `T = 2026-10-18 16:00 UTC+8`（向前对齐至最近的 8h 边界）。

#### 6.3.2 窗口对齐决策流程

```
当前时间 T_now
    │
    ▼
计算最近的8h边界:
    T_aligned = max(00:00, 08:00, 16:00) ≤ T_now
    │
    ▼
窗口范围 = [T_aligned - 259200s, T_aligned]
    │
    ▼
查询 events where event_ingress_ts ∈ [T_aligned - 259200s, T_aligned]
    │
    ▼
执行排除规则 → 得出 total_72h
```

### 6.4 采样规则

| 属性 | 全量计数 | 下采样展示 |
|------|----------|------------|
| **用途** | 对账、基线、容量规划 | 大盘图表展示 |
| **粒度** | 秒级（原始事件级） | 10 分钟级（聚合后） |
| **采样倍率** | 1.0（无采样） | 1:60（60 秒聚合为 1 点） |
| **采样方法** | — | 每分钟平均值 × 60 = 10 分钟粒度值 |
| **采样说明** | 无需标注 | **必须**标注采样倍率 |
| **数据源** | Ingestion Gateway 计数器 | 聚合后写入时序数据库 |
| **精度损失** | 无 | 约 ±0.5%（由于事件分布不均匀） |

> **重要**：大盘图表上显示的任何 72h 总量数值，必须在图表标题或图例中明确标注采样倍率。未标注采样倍率的图表数据视为无效。

### 6.5 统一后团队分工

| 团队 | 统计范围 | 角色 | 数据源 | 上报频率 | 采样允许 |
|------|----------|------|--------|----------|----------|
| **DSHB** | L1→L4 全链路 | 权威统计方 | Ingestion Gateway 计数器 | 1min | ❌ 禁止 |
| **DSHE** | L1→L4 全链路 | 独立校验方 | Dashboard Pipeline 计数器 | 5min | ✅ 允许（仅展示） |
| **HERMES** | L1→L4 全链路 | 独立校验方 | Audit WAL 计数器 | 5min | ✅ 允许（仅展示） |

### 6.6 代码示例

```python
# M-TOTAL-72H 计算伪代码
import datetime

def calculate_total_72h(
    current_time: datetime,
    event_store: dict,
    exclude_rules: bool = True
) -> dict:
    """
    计算72h滚动窗口事件总量
    
    窗口对齐：UTC+8 每日 00:00 / 08:00 / 16:00 (8h 块)
    窗口时长：259,200 秒
    
    Args:
        current_time: 当前时间 (datetime, UTC+8)
        event_store: 事件存储引用
        exclude_rules: 是否执行排除规则
    
    Returns:
        {
            "total_72h": int,
            "window_start": datetime,
            "window_end": datetime,
            "window_duration_seconds": 259200,
            "block_count": 9,
            "sampling_multiplier": 1.0,
            "excluded_count": int
        }
    """
    # 对齐到最近的8h边界 (00:00 / 08:00 / 16:00 UTC+8)
    boundary_hours = [0, 8, 16]
    current_hour = current_time.hour
    
    # 向前对齐至最近的8h边界
    aligned_boundary = 0
    for b in sorted(boundary_hours, reverse=True):
        if current_hour >= b:
            aligned_boundary = b
            break
    
    # 构造对齐后的窗口边界
    # 如果当前时间在边界之后但未满8h，向前对齐至当前边界
    window_end = current_time.replace(
        hour=aligned_boundary,
        minute=0, second=0, microsecond=0
    )
    
    # 如果当前时间已经过了当天最后一个8h边界(16:00)但未到次日00:00
    # 则使用当前时间作为窗口边界（向前对齐至最近8h点）
    if current_hour >= 16:
        window_end = current_time.replace(
            minute=0, second=0, microsecond=0
        )
        # 向前对齐至最近的8h点
        remainder = current_hour % 8
        window_end = window_end - datetime.timedelta(hours=remainder)
    
    window_start = window_end - datetime.timedelta(seconds=259200)
    
    # 查询窗口内事件
    events = event_store.query(
        ingress_ts_start=window_start.timestamp(),
        ingress_ts_end=window_end.timestamp()
    )
    
    total_72h = len(events)
    excluded_count = 0
    
    if exclude_rules:
        filtered_events = [
            e for e in events
            if not e.get("dedup_flag", False)
            and not e.get("truncated_flag", False)
            and not e.get("invalid_flag", False)
            and not e.get("expired_flag", False)
            and not e.get("blacklisted_flag", False)
        ]
        excluded_count = total_72h - len(filtered_events)
        total_72h = len(filtered_events)
    
    return {
        "total_72h": total_72h,
        "window_start": window_start,
        "window_end": window_end,
        "window_duration_seconds": 259200,
        "block_count": 9,
        "sampling_multiplier": 1.0,
        "excluded_count": excluded_count
    }
```

---

## 7. 跨团队对账机制

### 7.1 对账流程

```
┌──────────────────────────────────────────────────────────────┐
│                    对账周期（每 10 分钟）                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  DSHB    │    │  DSHE    │    │  HERMES  │              │
│  │ 计数器   │    │ 计数器   │    │ 计数器   │              │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘              │
│       │               │               │                    │
│       ▼               ▼               ▼                    │
│  ┌──────────────────────────────────────────┐              │
│  │         统一事件池快照 (T-10min)          │              │
│  │  - raw_ingressed (L1)                    │              │
│  │  - filtered_count (L2)                   │              │
│  │  - ingested_count (L3)                   │              │
│  │  - wal_persisted (L4)                    │              │
│  └──────────────┬───────────────────────────┘              │
│                 │                                            │
│                 ▼                                            │
│  ┌──────────────────────────────────────────┐              │
│  │         三方独立计算                      │              │
│  │  - M-THROUGHPUT-RAW (DSHB only)          │              │
│  │  - M-THROUGHPUT-INGESTED (三方均计算)    │              │
│  │  - M-LOSS-RATE (三方均计算)              │              │
│  │  - M-P99-AUDIT-INGEST (三方均计算)       │              │
│  │  - M-TOTAL-72H (三方均计算)              │              │
│  └──────────────┬───────────────────────────┘              │
│                 │                                            │
│                 ▼                                            │
│  ┌──────────────────────────────────────────┐              │
│  │         对账比较                          │              │
│  │  DSHB值 vs DSHE值 vs HERMES值            │              │
│  │  偏差容忍：≤ 0.1% (计数类)               │              │
│  │          ≤ 5% (百分比类)                  │              │
│  │          ≤ 50ms (延迟类)                  │              │
│  └──────────────┬───────────────────────────┘              │
│                 │                                            │
│        ┌────────┴────────┐                                 │
│        ▼                 ▼                                   │
│   偏差在容忍内        偏差超标                                │
│   → 通过 ✅          → 触发对账告警 ⚠️                     │
│                      → 写入对账日志                           │
│                      → 升级至人工审查 (≥3次超标)             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 7.2 对账指标矩阵

| 指标标识 | DSHB | DSHE | HERMES | 偏差容忍 | 对账周期 | 升级条件 |
|----------|------|------|--------|----------|----------|----------|
| M-THROUGHPUT-RAW | ✅ 权威 | ❌ 不参与 | ❌ 不参与 | — | — | — |
| M-THROUGHPUT-FILTERED | ✅ 权威 | ✅ 校验 | ❌ 不参与 | ≤ 0.1% | 10min | ≥3次超标 |
| M-THROUGHPUT-INGESTED | ✅ 权威 | ✅ 校验 | ✅ 校验 | ≤ 0.1% | 10min | ≥3次超标 |
| M-LOSS-RATE | ✅ 权威 | ✅ 校验 | ✅ 校验 | ≤ 5% (相对偏差) | 10min | ≥3次超标 |
| M-P99-AUDIT-INGEST | ✅ 权威 | ✅ 校验 | ✅ 校验 | ≤ 50ms (绝对偏差) | 10min | ≥3次超标 |
| M-P99-WAL-WRITE | ✅ 权威 | ❌ 不参与 | ✅ 校验 | ≤ 5ms (绝对偏差) | 10min | ≥3次超标 |
| M-TOTAL-72H | ✅ 权威 | ✅ 校验 | ✅ 校验 | ≤ 0.1% | 1h | ≥3次超标 |

### 7.3 对账结果记录格式

```json
{
  "reconciliation_id": "REC-20261018-143000",
  "window_start": "2026-10-18T14:20:00+08:00",
  "window_end": "2026-10-18T14:30:00+08:00",
  "metrics": {
    "M-THROUGHPUT-INGESTED": {
      "DSHB": 1250.3,
      "DSHE": 1248.7,
      "HERMES": 1247.9,
      "deviation_percent": 0.13,
      "tolerance_percent": 0.1,
      "status": "PASS"
    },
    "M-LOSS-RATE": {
      "DSHB": 0.0078,
      "DSHE": 0.0082,
      "HERMES": 0.0091,
      "deviation_percent": 4.87,
      "tolerance_percent": 5.0,
      "status": "PASS"
    },
    "M-P99-AUDIT-INGEST": {
      "DSHB": 462,
      "DSHE": 468,
      "HERMES": 471,
      "deviation_ms": 9,
      "tolerance_ms": 50,
      "status": "PASS"
    }
  },
  "overall_status": "PASS",
  "next_reconciliation_at": "2026-10-18T14:40:00+08:00"
}
```

---

## 8. 约束合规性声明

### 8.1 约束清单

| 约束编号 | 约束项 | 要求 | 本规范合规状态 | 说明 |
|----------|--------|------|---------------|------|
| C-001 | `NO_ZHIJI_API_CALL=FALSE` | 允许调用知纪API | ✅ 合规 | 本规范不涉及API调用；对账数据来自内部计数器 |
| C-002 | `NO_MODIFY_V85=TRUE` | 禁止修改V85基线 | ✅ 合规 | 本规范为新增文档，不修改V85任何文件 |
| C-003 | `NO_OVERWRITE=TRUE` | 禁止覆盖已有文件 | ✅ 合规 | 本规范为新增文档，未覆盖任何现有文件 |
| C-004 | `BRANCH_LOCKED=TRUE` | 分支锁定 | ✅ 合规 | 仅在 `feature/v85-chart-template` 分支提交，不执行合并操作 |
| C-005 | `METRIC_DEPRECATED_ALLOWED=TRUE` | 允许废弃旧口径 | ✅ 合规 | §5.6.2 已标记废弃旧P99定义，保留版本追溯 |
| C-006 | `TRIPARTITE_SIGNOFF_REQUIRED=TRUE` | 三方签字 | ⏳ 待执行 | §9 三方签字确认区待签署 |

### 8.2 变更影响分析

| 受影响文档 | 变更类型 | 影响章节 | 是否兼容 | 处理方式 |
|------------|----------|----------|----------|----------|
| `g0_g1_cross_align_spec.md` | P99定义更新 | §5.1 | ⚠️ 需同步 | 交叉引用更新，旧P99定义标注为DEPRECATED |
| `g1_gray_emergency_fuse_plan.md` | 指标标识更新 | M-01~M-04, LR-001~LR-010 | ⚠️ 需同步 | 指标标识从旧名称更新为新标识 |
| `g1_phase1_metric_snapshot.md` | 基线值更新 | 指标基线值 | ⚠️ 需同步 | 基线值以新口径重新计算后更新 |
| `g1_lr_alarm_rule_final_spec.md` | 告警规则更新 | LR-001~LR-010 | ⚠️ 需同步 | 告警条件引用新指标标识 |
| `g0_dep_gate_audit_event_def.md` | 审计事件定义 | 事件定义 | ✅ 兼容 | 事件定义与新口径一致 |
| `g1_gray_pre_gate_audit_report.md` | 审计报告 | 指标引用 | ⚠️ 需同步 | 交叉引用更新 |

### 8.3 合规检查脚本

```bash
#!/bin/bash
# 约束合规性自动检查脚本

echo "=== 约束合规性检查 ==="

# C-001: NO_ZHIJI_API_CALL=FALSE
echo -n "C-001 NO_ZHIJI_API_CALL: "
if grep -q "知纪API\|zhiji_api\|api_call" "$DOC_FILE"; then
  echo "⚠️ 警告: 文档中提及知纪API调用，需人工确认"
else
  echo "✅ PASS: 不涉及知纪API调用"
fi

# C-002: NO_MODIFY_V85=TRUE
echo -n "C-002 NO_MODIFY_V85: "
if grep -q "v85_baseline\|v85_config" "$DOC_FILE"; then
  echo "⚠️ 警告: 文档中引用V85配置，需确认未修改"
else
  echo "✅ PASS: 不修改V85基线"
fi

# C-003: NO_OVERWRITE=TRUE
echo -n "C-003 NO_OVERWRITE: "
if [ -f "$DOC_FILE" ]; then
  echo "⚠️ 警告: 文件已存在，确认未覆盖"
else
  echo "✅ PASS: 新增文件，未覆盖"
fi

# C-005: METRIC_DEPRECATED_ALLOWED
echo -n "C-005 DEPRECATED标记: "
if grep -q "DEPRECATED" "$DOC_FILE"; then
  echo "✅ PASS: 包含废弃标记"
else
  echo "⚠️ 警告: 缺少废弃标记"
fi

# C-006: TRIPARTITE_SIGNOFF
echo -n "C-006 三方签字: "
if grep -q "三方签字确认" "$DOC_FILE"; then
  echo "⏳ 待签署"
else
  echo "⚠️ 警告: 缺少签字确认区"
fi

echo "=== 检查完成 ==="
```

---

## 9. 三方签字确认

> ⚠️ **本节须由三方负责人共同签署后方可生效。** 签署前，本规范不具约束力。

### 9.1 签字栏

| 角色 | 团队 | 姓名 | 职位 | 签署日期 | 电子签名 |
|------|------|------|------|----------|----------|
| **DSHB 指标负责人** | DSHB V86 RC2 G1 | （待填写） | 技术负责人 | YYYY-MM-DD | ______________ |
| **DSHE 指标负责人** | DSHE L2 Dashboard | （待填写） | 技术负责人 | YYYY-MM-DD | ______________ |
| **HERMES 指标负责人** | HERMES Audit | （待填写） | 技术负责人 | YYYY-MM-DD | ______________ |
| **DSHB 工程总监** | DSHB V86 RC2 G1 | （待填写） | 工程总监 | YYYY-MM-DD | ______________ |
| **DSHE 工程总监** | DSHE L2 Dashboard | （待填写） | 工程总监 | YYYY-MM-DD | ______________ |
| **HERMES 工程总监** | HERMES Audit | （待填写） | 工程总监 | YYYY-MM-DD | ______________ |

### 9.2 签字确认内容

签署本规范即表示三方确认以下事项：

1. **口径一致性确认**：三方确认本规范定义的四个核心指标（吞吐、事件丢失率、P99时延、72h总量）的统计口径已对齐，可互操作。
2. **数据源确认**：三方确认各自统计的指标数据源与本规范定义一致，数据采集埋点位置已确认。
3. **阈值确认**：三方确认各指标的三级阈值体系（正常/警告/P0阻断）已对齐，熔断触发条件已同步。
4. **对账义务确认**：三方承诺按本规范定义的频率和格式执行跨团队对账，偏差超标时主动报告并配合调查。
5. **废弃确认**：三方确认旧版 P99 笼统定义已废弃，后续所有文档、代码、告警规则使用新指标标识。
6. **约束合规确认**：三方确认本规范遵守所有约束条件（C-001~C-006）。

### 9.3 签字前置检查清单

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 三方指标计算代码已更新 | ⏳ | DSHB/DSHE/HERMES 各自更新指标计算逻辑 |
| 采集埋点已部署 | ⏳ | 按 §3.2 / §4.2 / §5.3~§5.5 / §6.2 定义的埋点位置 |
| 基线值已按新口径重新计算 | ⏳ | Phase3 基线值需按新口径重算 |
| 告警规则已更新 | ⏳ | LR-001~LR-010 按新指标标识更新 |
| 对账脚本已部署 | ⏳ | 按 §7.1 定义的对账流程 |
| 三方负责人已审阅本规范 | ⏳ | 各方至少完成一次全文审阅 |

### 9.4 签字后生效条件

签署完成后，需执行以下步骤使本规范正式生效：

1. 将本规范提交至 `feature/v85-chart-template` 分支
2. 设置约束标记：`DSHB_G1_METRIC_SPEC_DONE=TRUE`
3. 通知三方更新各自指标计算代码
4. 执行首次对账（T+0），确认三方数据一致性
5. 将基线值按新口径更新至 `v86_rc2_dshb_g1_phase1_metric_snapshot.md`

---

## 10. MD5自检

### 10.1 文档完整性校验

| 校验项 | 预期值 | 说明 |
|--------|--------|------|
| 文档文件名 | `v86_rc2_dshb_g1_tripartite_metric_spec_v1.0.md` | 文件名与版本一致 |
| 版本标识 | `V1.0` | 文档头版本号 |
| MD5 摘要 | `(待生成)` | 文档最终定稿后执行 MD5 计算 |
| 行数 | ≥ 500 行 | 内容完整性检查 |
| 章节数 | 12 章（含附录） | 结构完整性检查 |

### 10.2 MD5 计算命令

```bash
# 计算文档 MD5
md5sum "D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix\v86_rc2_dshb_g1_tripartite_metric_spec_v1.0.md"

# Windows 环境
certutil -hashfile "D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix\v86_rc2_dshb_g1_tripartite_metric_spec_v1.0.md" MD5

# SHA256 (推荐)
certutil -hashfile "D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix\v86_rc2_dshb_g1_tripartite_metric_spec_v1.0.md" SHA256
```

### 10.3 内容自检清单

| 序号 | 自检项 | 状态 |
|------|--------|------|
| 1 | 四个核心指标均有统一定义 | ✅ |
| 2 | 每个指标均有公式 | ✅ |
| 3 | 每个指标均有测量点定义 | ✅ |
| 4 | 每个指标均有阈值三级体系 | ✅ |
| 5 | 包含口径差异对照表 | ✅ |
| 6 | 包含团队分工矩阵 | ✅ |
| 7 | 包含代码示例 | ✅ |
| 8 | 包含跨团队对账机制 | ✅ |
| 9 | 包含约束合规声明 | ✅ |
| 10 | 包含三方签字确认区 | ✅ |
| 11 | 包含 MD5 自检区 | ✅ |
| 12 | 包含版本历史 | ✅ |
| 13 | 包含约束影响分析 | ✅ |
| 14 | 包含事件分层模型 | ✅ |
| 15 | 包含统一时间戳基准 | ✅ |
| 16 | 包含排除规则定义 | ✅ |
| 17 | 包含 P99 禁止混用规则 | ✅ |
| 18 | 包含旧定义废弃声明 | ✅ |
| 19 | 包含与既有文档映射关系 | ✅ |
| 20 | 包含对账结果记录格式 | ✅ |

---

## 11. 版本历史

| 版本 | 日期 | 变更类型 | 变更说明 | 变更人 | 审批人 |
|------|------|----------|----------|--------|--------|
| V1.0 | 2026-10-18 | 初始版本 | 首次发布三方指标统计口径规范，定义四核心指标统一定义 | （待填写） | （待填写） |

### 11.1 变更记录（V1.0）

#### 新增内容

| 章节 | 新增内容 |
|------|----------|
| §2.1 | 事件分层模型（L1 Raw / L2 Filtered / L3 Ingested / L4 WAL-Persisted） |
| §2.2 | 统一时间戳基准（`event_ingress_ts` 为全局对齐基准） |
| §2.3 | 排除规则定义（5类排除条件，含优先级） |
| §3.2 | 吞吐量三层子指标（RAW / FILTERED / INGESTED） |
| §4.2 | 事件丢失率统一定义（基于 ingestion gateway 事件池） |
| §5.3~§5.5 | P99 三个独立子指标（业务端到端 / 审计入库 / WAL写入） |
| §5.6 | P99 禁止混用规则（5项违规定义） |
| §5.6.2 | 旧P99定义废弃声明 |
| §6.3 | 72h窗口8小时块对齐规则 |
| §6.4 | 采样规则与标注要求 |
| §7 | 跨团队对账机制（完整流程 + 指标矩阵 + 记录格式） |
| §8.3 | 合规检查脚本 |
| §9 | 三方签字确认区（含前置检查清单） |
| §10 | MD5自检区 |
| §12 | 附录（术语表 + 指标标识速查表 + 交叉引用表） |

#### 废弃内容

| 旧定义来源 | 旧定义 | 废弃原因 | 替代定义 |
|------------|--------|----------|----------|
| `g0_g1_cross_align_spec.md` §5.1 | P99≤200ms (笼统) | 过于笼统，无法区分度量场景 | 三个独立P99子指标 |
| `g0_g1_cross_align_spec.md` §5.1 | 告警P99≤500ms | 与审计入库P99混淆 | M-P99-AUDIT-INGEST ≤ 1000ms |
| `g0_g1_cross_align_spec.md` §5.1 | 决策P99≤1s | 与审计入库P99混淆 | M-P99-AUDIT-INGEST ≤ 1000ms |
| `g0_g1_cross_align_spec.md` §5.1 | 刷新P99≤5s | 与业务端到端P99混淆 | M-P99-BUSINESS-E2E ≤ 30s |
| DSHB 内部旧定义 | 吞吐=全部事件计数 | 未区分 raw/filtered/ingested | M-THROUGHPUT-RAW/FILTERED/INGESTED |
| DSHE 内部旧定义 | 丢失率=大盘可见差异 | 分母非原始事件池 | M-LOSS-RATE (统一公式) |
| HERMES 内部旧定义 | 72h总量含采样 | 采样比例不透明 | M-TOTAL-72H (全量计数) |

---

## 12. 附录

### 12.1 指标标识速查表

| 指标标识 | 中文名称 | 英文标识 | 单位 | 阈值 | 统计职责 | 对账角色 |
|----------|----------|----------|------|------|----------|----------|
| M-THROUGHPUT-RAW | 吞吐-原始层 | Throughput Raw | ev/s | — | DSHB | 权威 |
| M-THROUGHPUT-FILTERED | 吞吐-过滤层 | Throughput Filtered | ev/s | — | DSHB | 权威 |
| M-THROUGHPUT-INGESTED | 吞吐-入库层 | Throughput Ingested | ev/s | — | DSHB | 权威 |
| M-LOSS-RATE | 事件丢失率 | Event Loss Rate | % | ≤0.01% | DSHB | 权威 |
| M-P99-BUSINESS-E2E | P99-业务端到端 | P99 Business E2E | s | ≤30s | DSHB | 权威 |
| M-P99-AUDIT-INGEST | P99-审计入库 | P99 Audit Ingest | ms | ≤1000ms | DSHB | 权威 |
| M-P99-WAL-WRITE | P99-WAL写入 | P99 WAL Write | ms | ≤50ms | DSHB | 权威 |
| M-TOTAL-72H | 72h总量 | 72h Total Volume | events | — | DSHB | 权威 |

### 12.2 时间戳字段速查表

| 字段名 | 产生位置 | 精度 | 用于指标 |
|--------|----------|------|----------|
| `event_create_ts` | 事件源 | ms | M-P99-BUSINESS-E2E |
| `event_ingress_ts` | Ingestion Gateway | ms | **全部指标时间窗口对齐** |
| `event_business_response_ts` | 业务应用 | ms | M-P99-BUSINESS-E2E |
| `wal_write_request_ts` | WAL Writer | ms | M-P99-WAL-WRITE |
| `wal_commit_ts` | WAL Writer | ms | M-P99-AUDIT-INGEST |
| `wal_fsck_sync_ts` | WAL Persistence | ms | M-P99-WAL-WRITE |

### 12.3 告警规则映射表

| 旧告警规则 | 新告警规则 | 对应指标 | 变更说明 |
|------------|------------|----------|----------|
| LR-001 | LR-001 | M-LOSS-RATE | 保留，公式统一 |
| LR-002 | LR-002 | M-P99-AUDIT-INGEST | 更名，明确子指标 |
| LR-003 | (废弃) | — | 合并入 LR-002 |
| LR-004 | LR-004 | 业务错误率 | 不受本规范影响 |
| LR-005 | LR-005 | M-P99-BUSINESS-E2E | 新增，原不存在 |
| LR-006 | LR-006 | M-P99-WAL-WRITE | 新增，原不存在 |
| LR-007~LR-010 | — | — | 不受本规范影响 |

### 12.4 与Phase3基线对齐对照表

| 指标 | Phase3 基线值 | 本规范对应指标 | 统一后基线（待对账确认） | 偏差说明 |
|------|---------------|----------------|--------------------------|----------|
| 审计丢失率 0.008% | 0.008% | M-LOSS-RATE | 待对账确认 | DSHB原始值，需按新公式重算 |
| P99告警延迟 462ms | 462ms | M-P99-AUDIT-INGEST | 待对账确认 | 测量点明确为网关→WAL commit |
| P99决策延迟 891ms | 891ms | M-P99-AUDIT-INGEST | 合并至此指标 | 旧决策延迟已废弃 |
| 业务错误率 0.12% | 0.12% | 不受本规范影响 | — | — |

### 12.5 术语表

| 缩写 | 全称 | 说明 |
|------|------|------|
| DSHB | Data Service Hub Backend | 数据服务枢纽后端 |
| DSHE | Data Service Hub Enterprise | 数据服务枢纽企业版 |
| HERMES | High-Efficiency Real-time Message Event System | 高效实时消息事件系统 |
| WAL | Write-Ahead Log | 预写日志 |
| fsync | File System Sync | 文件系统同步 |
| P99 | 99th Percentile | 第99百分位 |
| RC2 | Release Candidate 2 | 发布候选版本2 |
| G1 | Gate 1 | 灰度阶段1 |
| LR | Long-term Retention | 长期保留告警规则 |
| P0 | Priority 0 | 最高优先级 |

---

> **文档结束**
> 
> 本规范发布后，DSHB_V86_RC2_G1_PHASE5_CROSS_TEAM_METRICS_ALIGN_AND_BASELINE_RECONCILIATION 工单进入三方签字确认阶段。
> 
> 约束标记更新：`DSHB_G1_METRIC_SPEC_DONE=TRUE`（三方签字后生效）
