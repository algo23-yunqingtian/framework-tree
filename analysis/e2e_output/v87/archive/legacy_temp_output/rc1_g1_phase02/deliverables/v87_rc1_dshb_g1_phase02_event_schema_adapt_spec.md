# V87 RC1 G1 Phase02 — DSHB 事件Schema适配规范

> **DSHB (Data Storage Hub Benchmark) 事件架构适配规范文档**
> 文档版本: v1.0 | 文档状态: 🟡 待三方会签

---

## 目录

1. [文档元数据](#1-文档元数据)
2. [背景与需求分析](#2-背景与需求分析)
3. [完整事件Schema定义](#3-完整事件schema定义)
4. [五项新增字段详细规格](#4-五项新增字段详细规格)
5. [三方命名对齐矩阵](#5-三方命名对齐矩阵)
6. [数据完整性规则](#6-数据完整性规则)
7. [Schema版本管理策略](#7-schema版本管理策略)
8. [事件管道流转架构](#8-事件管道流转架构)
9. [三方验证机制](#9-三方验证机制)
10. [迁移实施计划](#10-迁移实施计划)
11. [验收标准与检查清单](#11-验收标准与检查清单)
12. [签署与审批](#12-签署与审批)

---

## 1. 文档元数据

| 字段 | 内容 |
|------|------|
| **文档编号** | DSHB-ES-V87-RC1-G1-P02 |
| **文档标题** | V87 RC1 G1 Phase02 — DSHB 事件Schema适配规范 |
| **版本** | v1.0 |
| **所属分支** | `feature/v87-rc1-g1` |
| **所属版本** | V87 RC1 (Release Candidate 1) |
| **所属阶段** | Phase02 |
| **阶段时间窗口** | 2027-03-05 ~ 2027-03-19 (共 15 个工作日) |
| **前序版本** | V86 (event_schema_version = "86") |
| **编制日期** | 2027-03-19 |
| **编制部门** | DSHB 架构设计组 (ADG) |
| **编制人** | 架构师 王华 |
| **审核人** | DSHB/DSHE/HERMES 三方架构评审委员会 — 待审核 |
| **批准人** | 技术副总裁 陈涛 — 待批准 |
| **密级** | 内部公开 (Internal Public) |
| **文档状态** | 🟡 待三方会签 |
| **引用标准** | DSHB 事件架构规范 V2.4、DSHE 可观测性标准 V1.8、HERMES 审计规范 V3.1、ISO 8601 日期时间标准、RFC 4122 UUID 标准 |
| **关联文档** | DSHB-ES-V86 (V86 Schema 基线文档)、DSHB-VR-V87-RC1-G1-P02 (Phase02 风险登记册) |

### 1.1 适用范围

本规范适用于 V87 RC1 G1 组 Phase02 期间 DSHB 事件架构的适配工作，覆盖以下三方系统:

- **DSHB (Data Storage Hub Benchmark)** — 事件产生方，负责事件的生成、校验、持久化
- **DSHE (Data Storage Hub Engine)** — 事件消费方，负责事件的处理、转换、再分发
- **HERMES (High Efficiency Real-time Monitoring & Event System)** — 审计与监控方，负责事件的全链路审计追踪与合规校验

### 1.2 修订历史

| 版本 | 日期 | 修订人 | 修订说明 |
|------|------|--------|----------|
| v0.1 | 2027-03-06 | 王华 | 初稿，完成背景与需求分析章节 |
| v0.2 | 2027-03-09 | 王华 | 完成完整 Schema 定义与新增字段规格 |
| v0.3 | 2027-03-12 | 王华 | 完成命名对齐矩阵与完整性规则 |
| v0.4 | 2027-03-15 | 王华 | 完成版本管理策略与事件管道架构 |
| v0.5 | 2027-03-17 | 王华 | 完成三方验证、迁移计划、验收标准 |
| v1.0 | 2027-03-19 | 王华 | 🟡 提交三方会签，定稿版 |

---

## 2. 背景与需求分析

### 2.1 版本迭代概览

V87 RC1 是 DSHB 平台自 V86 以来的重大版本迭代，核心聚焦于**事件架构的可观测性增强**与**审计合规能力补齐**。本次 G1 组 Phase02 阶段专门针对事件 Schema 进行适配升级，以满足 HERMES 审计系统与 DSHE 监控系统的新增需求。

#### 2.1.1 V86 基线回顾

V86 事件 Schema 共定义 **15 个字段**，划分为两个层次:

| 层次 | 字段数 | 包含字段 |
|------|:------:|----------|
| 公共层 (Common) | 10 | event_id, event_timestamp, event_source, event_payload, status_code, processing_time, processing_duration, error_message, version_tag, event_schema_version |
| 扩展层 (Extension) | 5 | sequence_number, parent_event_id, tags, correlation_id, sha256_checksum |
| **合计** | **15** | — |

#### 2.1.2 V87 目标状态

V87 事件 Schema 扩展至 **20 个字段**，新增 5 个关键字段，字段层次重新划分为:

| 层次 | 字段数 | 包含字段 |
|------|:------:|----------|
| 公共层 (Common) | 12 | event_id, event_timestamp, event_source, event_payload, **event_type**🆕, status_code, processing_time, processing_duration, error_message, version_tag, event_schema_version, **batch_id**🆕 |
| 扩展层 (Extension) | 8 | **batch_id**, sequence_number, **priority**🆕, **retry_count**🆕, parent_event_id, tags, correlation_id, sha256_checksum |
| 全局追踪层 | 1 | **trace_id**🆕 |
| **合计** | **20** | — |

### 2.2 五项新增字段的需求来源

#### 2.2.1 HERMES 审计需求 (4 项)

HERMES (High Efficiency Real-time Monitoring & Event System) 审计系统在 2027 年 2 月提交审计报告 **HERMES-AUD-2027-003**，明确要求 DSHB 事件 Schema 新增以下能力:

##### 2.2.1.1 全链路追踪能力缺失 → trace_id

**需求编号**: HERMES-REQ-001
**严重级别**: 🔴 Critical

> **审计发现**: 当前 V86 Schema 缺乏统一的全链路追踪标识符。在事件流经 DSHB → DSHE → HERMES 三方系统时，无法建立端到端的关联关系。审计人员在排查跨系统数据异常时，需要手动比对多个系统的日志文件，平均排查耗时 4.2 小时/事件。

**解决方案**: 引入 `trace_id` 字段，采用 UUID v4 格式，在事件产生时生成并贯穿全链路传播。

**量化目标**:
- ✅ 实现 100% 事件全链路可追踪
- ✅ 跨系统异常排查耗时从 4.2 小时降至 **≤ 15 分钟**
- ✅ 支持分布式事务追踪与根因分析

##### 2.2.1.2 事件分类能力缺失 → event_type

**需求编号**: HERMES-REQ-002
**严重级别**: 🔴 Critical

> **审计发现**: 所有事件在 HERMES 审计视图中呈现为同质的 "EVENT" 类型，无法按业务语义分类。审计人员需要解析 `event_payload` 中的嵌套 JSON 字段才能判断事件性质，审计报告生成效率降低约 60%。

**解决方案**: 引入 `event_type` 枚举字段，预定义 25 种事件类型，支持分类统计、按类型审计和合规检查。

**量化目标**:
- ✅ 审计事件分类准确率 ≥ 99.5%
- ✅ 审计报告生成效率提升 **≥ 120%**
- ✅ 支持按事件类型的自动合规规则匹配

##### 2.2.1.3 批量操作关联能力缺失 → batch_id

**需求编号**: HERMES-REQ-003
**严重级别**: 🟡 High

> **审计发现**: 当 DSHB 执行批量写入、批量归档、批量导入等操作时，产生的大量事件在 HERMES 中表现为独立的零散记录。审计人员无法高效地将同一批次的操作结果聚合分析，批量操作的事后审计完全依赖人工筛选。

**解决方案**: 引入 `batch_id` 字段，采用 `{source}_{timestamp}_{seq}` 结构化格式，实现批量操作的原子化追踪。

**量化目标**:
- ✅ 批量操作关联准确率 ≥ 99.9%
- ✅ 批量审计分析效率提升 **≥ 200%**
- ✅ 支持批量操作的原子性验证与一致性检查

##### 2.2.1.4 失败重试分析能力缺失 → retry_count

**需求编号**: HERMES-REQ-004
**严重级别**: 🟡 High

> **审计发现**: 当前 Schema 无法记录事件的重试次数。在故障恢复场景中，HERMES 无法区分首次投递成功与多次重试后成功的事件，无法分析重试风暴对系统稳定性的影响，无法统计最终进入死信队列 (DLQ) 的事件比例。

**解决方案**: 引入 `retry_count` 整数字段，记录事件从产生到最终处理完成期间的重试次数，支持重试分析与死信管理。

**量化目标**:
- ✅ 重试事件识别准确率 100%
- ✅ DLQ 事件统计自动化率 100%
- ✅ 重试风暴检测响应时间 ≤ **5 秒**

#### 2.2.2 DSHE 监控需求 (1 项)

DSHE (Data Storage Hub Engine) 监控团队在 2027 年 2 月提交性能监控需求 **DSHE-MON-2027-001**，要求 DSHB 事件 Schema 新增优先级标识:

##### 2.2.2.1 事件优先级标识缺失 → priority

**需求编号**: DSHE-REQ-001
**严重级别**: 🟡 High

> **监控发现**: 当前所有事件在 DSHE 事件队列中按 FIFO 顺序处理，缺乏优先级机制。关键业务事件 (如存储告警、紧急恢复指令) 与低优先级事件 (如心跳、统计报表) 排队时间相同，导致关键事件平均处理延迟超标 30%~80%。

**解决方案**: 引入 `priority` 整数字段 (1-10)，支持事件优先级的显式标识与调度优化。

**量化目标**:
- ✅ 关键事件 (priority ≥ 8) 处理延迟 ≤ **500ms**
- ✅ 高优先级事件吞吐量提升 **≥ 40%**
- ✅ 支持基于优先级的差异化 SLA 监控

### 2.3 需求汇总矩阵

| 需求编号 | 需求方 | 字段 | 类型 | 严重级别 | 交付阶段 |
|----------|--------|------|------|:--------:|:--------:|
| HERMES-REQ-001 | HERMES 审计 | trace_id | UUID v4 | 🔴 Critical | Phase02 |
| HERMES-REQ-002 | HERMES 审计 | event_type | 枚举 (25值) | 🔴 Critical | Phase02 |
| HERMES-REQ-003 | HERMES 审计 | batch_id | 结构化字符串 | 🟡 High | Phase02 |
| HERMES-REQ-004 | HERMES 审计 | retry_count | 整数 (0-5) | 🟡 High | Phase02 |
| DSHE-REQ-001 | DSHE 监控 | priority | 整数 (1-10) | 🟡 High | Phase02 |
| **合计** | — | **5 个新字段** | — | 2 Critical / 3 High | — |

### 2.4 风险影响分析

#### 2.4.1 若不升级的风险

| 风险项 | 影响范围 | 影响程度 | 发生概率 |
|--------|----------|:--------:|:--------:|
| ❌ 审计合规风险 | HERMES 审计无法通过合规检查，可能导致数据保护等级评定降级 | 🔴 严重 | 95% |
| ❌ 事件追踪盲区 | 跨系统故障排查效率极低，MTTR (平均修复时间) 无法达标 | 🔴 严重 | 85% |
| ❌ 关键事件延迟 | DSHE 关键事件处理延迟超标，影响告警响应 SLA | 🟡 高 | 70% |
| ❌ 批量操作审计缺失 | 批量导入/归档操作无法实现事后审计闭环 | 🟡 高 | 60% |
| ❌ 重试管理失控 | 重试风暴不可检测，可能导致系统资源耗尽 | 🟡 高 | 50% |

#### 2.4.2 升级后的收益

| 收益项 | 量化指标 | 业务价值 |
|--------|----------|----------|
| ✅ 审计合规达标 | HERMES 审计评分 ≥ 95/100 | 满足行业合规要求 |
| ✅ 排查效率提升 | 跨系统排查耗时降低 **96.4%** (4.2h → 15min) | 运维效率显著提升 |
| ✅ 事件调度优化 | 关键事件延迟降低 **≥ 80%** | SLA 达标率提升 |
| ✅ 批量审计闭环 | 批量操作审计覆盖率 **100%** | 数据治理能力提升 |
| ✅ 重试智能管理 | 重试风暴检测时间 ≤ 5 秒 | 系统稳定性增强 |

---

## 3. 完整事件Schema定义

### 3.1 Schema 层次结构

V87 事件 Schema 采用**三层结构**设计:

```
┌─────────────────────────────────────────────────────────────┐
│  全局追踪层 (Global Trace Layer)                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  trace_id                                           │    │
│  │  (全链路贯穿，跨越所有公共层与扩展层字段)               │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  公共层 (Common Layer) — 12 字段                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  event_id | event_timestamp | event_source           │    │
│  │  event_payload | event_type🆕 | status_code          │    │
│  │  processing_time | processing_duration               │    │
│  │  error_message | version_tag | event_schema_version  │    │
│  │  batch_id🆕                                           │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  扩展层 (Extension Layer) — 8 字段                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  batch_id | sequence_number                          │    │
│  │  priority🆕 | retry_count🆕 | parent_event_id        │    │
│  │  tags | correlation_id | sha256_checksum             │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

> **说明**: `batch_id` 同时出现在公共层与扩展层。公共层中的 `batch_id` 是**必填**的基础批量标识，扩展层中的 `batch_id` 允许携带批次上下文扩展信息 (如批次的父批次引用、子批次列表等)。

### 3.2 完整字段定义表 (20 字段)

#### 3.2.1 全局追踪层字段

| 序号 | 字段名 | 数据类型 | 必填 | 示例值 | 引入版本 |
|:----:|--------|----------|:----:|--------|:--------:|
| 1 | `trace_id` 🆕 | string (UUID v4) | ✅ 是 | `"550e8400-e29b-41d4-a716-446655440000"` | V87 |

#### 3.2.2 公共层字段

| 序号 | 字段名 | 数据类型 | 必填 | 示例值 | 引入版本 |
|:----:|--------|----------|:----:|--------|:--------:|
| 2 | `event_id` | string (UUID v4) | ✅ 是 | `"a1b2c3d4-e5f6-7890-abcd-ef1234567890"` | V86 |
| 3 | `event_timestamp` | string (ISO 8601) | ✅ 是 | `"2027-03-19T14:30:00.123Z"` | V86 |
| 4 | `event_source` | string (枚举) | ✅ 是 | `"DSHB_STORAGE_ENGINE"` | V86 |
| 5 | `event_payload` | object (JSON) | ✅ 是 | `{"storage_id": "stg-001", "size_mb": 256}` | V86 |
| 6 | `event_type` 🆕 | string (枚举, 25值) | ✅ 是 | `"STORAGE_CREATE"` | V87 |
| 7 | `status_code` | string (枚举) | ✅ 是 | `"SUCCESS"` | V86 |
| 8 | `processing_time` | string (ISO 8601) | ⚠️ 条件 | `"2027-03-19T14:30:00.456Z"` | V86 |
| 9 | `processing_duration` | integer (ms) | ⚠️ 条件 | `333` | V86 |
| 10 | `error_message` | string | ⚠️ 条件 | `"Storage quota exceeded: 5120 MB / 5120 MB"` | V86 |
| 11 | `version_tag` | string | ✅ 是 | `"v87-rc1-g1"` | V86 |
| 12 | `event_schema_version` | string | ✅ 是 | `"87"` | V87 |
| 13 | `batch_id` 🆕 | string | ⚠️ 条件 | `"DSHB_20270319143000_0001"` | V87 |

#### 3.2.3 扩展层字段

| 序号 | 字段名 | 数据类型 | 必填 | 示例值 | 引入版本 |
|:----:|--------|----------|:----:|--------|:--------:|
| 14 | `batch_id` | string (结构化) | ⚠️ 条件 | `"DSHB_20270319143000_0001"` | V87 |
| 15 | `sequence_number` | integer | ⚠️ 条件 | `42` | V86 |
| 16 | `priority` 🆕 | integer (1-10) | ✅ 是 | `8` | V87 |
| 17 | `retry_count` 🆕 | integer (0-5) | ✅ 是 | `0` | V87 |
| 18 | `parent_event_id` | string (UUID v4) | ❌ 否 | `"9f8e7d6c-5b4a-3210-fedc-ba0987654321"` | V86 |
| 19 | `tags` | array[string] | ❌ 否 | `["urgent", "production", "storage"]` | V86 |
| 20 | `correlation_id` | string | ⚠️ 条件 | `"corr-a1b2c3d4"` | V86 |
| 21 | `sha256_checksum` | string (64 hex) | ❌ 否 | `"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"` | V86 |

> **字段计数说明**: 表格中列出 21 行是因为 `batch_id` 在公共层与扩展层各出现一次 (第 13 与第 14 行)。去重后实际字段数为 **20 个**。`trace_id` 为全局追踪层独立字段，不计入公共层或扩展层的字段编号。

### 3.3 字段必填性矩阵

| 字段 | 事件产生时 | DSHE 消费时 | HERMES 审计时 | 校验阶段 |
|------|:----------:|:-----------:|:-------------:|----------|
| `trace_id` | ✅ 必填 | ✅ 必填 | ✅ 必填 | 产生时 / 消费时 / 审计时 |
| `event_id` | ✅ 必填 | ✅ 必填 | ✅ 必填 | 产生时 |
| `event_timestamp` | ✅ 必填 | ✅ 必填 | ✅ 必填 | 产生时 |
| `event_source` | ✅ 必填 | ✅ 必填 | ✅ 必填 | 产生时 |
| `event_payload` | ✅ 必填 | ✅ 必填 | ✅ 必填 | 产生时 / 消费时 |
| `event_type` 🆕 | ✅ 必填 | ✅ 必填 | ✅ 必填 | 产生时 |
| `status_code` | ✅ 必填 | ✅ 必填 | ✅ 必填 | 消费时 / 审计时 |
| `processing_time` | ⚠️ 条件 | ⚠️ 条件 | ⚠️ 条件 | 消费时 |
| `processing_duration` | ⚠️ 条件 | ⚠️ 条件 | ⚠️ 条件 | 消费时 |
| `error_message` | ⚠️ 条件 | ⚠️ 条件 | ⚠️ 条件 | 消费时 / 审计时 |
| `version_tag` | ✅ 必填 | ✅ 必填 | ✅ 必填 | 产生时 |
| `event_schema_version` | ✅ 必填 | ✅ 必填 | ✅ 必填 | 产生时 / 消费时 |
| `batch_id` (公共层) | ⚠️ 条件 | ⚠️ 条件 | ⚠️ 条件 | 产生时 |
| `batch_id` (扩展层) | ⚠️ 条件 | ⚠️ 条件 | ⚠️ 条件 | 产生时 / 审计时 |
| `sequence_number` | ⚠️ 条件 | ⚠️ 条件 | ⚠️ 条件 | 产生时 |
| `priority` 🆕 | ✅ 必填 | ✅ 必填 | ✅ 必填 | 产生时 |
| `retry_count` 🆕 | ✅ 必填 | ✅ 必填 | ✅ 必填 | 产生时 / 消费时 |
| `parent_event_id` | ❌ 可选 | ❌ 可选 | ❌ 可选 | 产生时 |
| `tags` | ❌ 可选 | ❌ 可选 | ❌ 可选 | 产生时 |
| `correlation_id` | ⚠️ 条件 | ⚠️ 条件 | ⚠️ 条件 | 产生时 |
| `sha256_checksum` | ❌ 可选 | ❌ 可选 | ⚠️ 条件 | 产生时 / 审计时 |

> **⚠️ 条件必填说明**:
> - `processing_time` 与 `processing_duration`: 当事件状态为 `SUCCESS` 或 `PARTIAL` 时必填
> - `error_message`: 当事件状态为 `FAILED` 或 `TIMEOUT` 时必填
> - `batch_id`: 当事件属于批量操作时必填，单事件操作时可选
> - `sequence_number`: 当事件属于有序批次时必填
> - `correlation_id`: 当事件参与分布式事务关联时必填
> - `sha256_checksum`: 在 HERMES 审计场景下必填 (用于数据完整性校验)

---

## 4. 五项新增字段详细规格

### 4.1 event_type — 事件类型枚举

#### 4.1.1 字段定义

| 属性 | 值 |
|------|-----|
| **字段名** | `event_type` |
| **数据类型** | string (枚举) |
| **取值数量** | 25 个预定义值 |
| **是否必填** | ✅ 是 |
| **大小写敏感** | ✅ 是 (全大写) |
| **校验规则** | 必须为预定义枚举值之一，拒绝空值与未定义值 |

#### 4.1.2 枚举值完整定义

| 序号 | 枚举值 | 中文名称 | 分类 | 说明 | 典型场景 |
|:----:|--------|----------|------|------|----------|
| 1 | `STORAGE_CREATE` | 存储创建 | 🟢 存储操作 | 创建新的存储单元 | 新建存储桶/卷/分区 |
| 2 | `STORAGE_UPDATE` | 存储更新 | 🟢 存储操作 | 更新存储单元属性 | 修改存储配额/标签/元数据 |
| 3 | `STORAGE_DELETE` | 存储删除 | 🟢 存储操作 | 删除存储单元 | 删除存储桶/卷/分区 |
| 4 | `STORAGE_READ` | 存储读取 | 🟢 存储操作 | 读取存储数据 | 数据查询/读取操作 |
| 5 | `STORAGE_ARCHIVE` | 存储归档 | 🟢 存储操作 | 归档存储数据 | 冷数据存储归档 |
| 6 | `STORAGE_RESTORE` | 存储恢复 | 🟢 存储操作 | 从归档恢复数据 | 冷数据恢复到热存储 |
| 7 | `STORAGE_COMPRESS` | 存储压缩 | 🟢 存储操作 | 压缩存储数据 | 启用透明压缩 |
| 8 | `STORAGE_DECOMPRESS` | 存储解压缩 | 🟢 存储操作 | 解压存储数据 | 压缩数据恢复 |
| 9 | `DATA_IMPORT` | 数据导入 | 🔵 数据流转 | 从外部导入数据 | CSV/Parquet 批量导入 |
| 10 | `DATA_EXPORT` | 数据导出 | 🔵 数据流转 | 导出数据到外部 | CSV/Parquet 批量导出 |
| 11 | `DATA_MIGRATE` | 数据迁移 | 🔵 数据流转 | 存储数据迁移 | 跨节点/集群迁移 |
| 12 | `DATA_SYNC` | 数据同步 | 🔵 数据流转 | 数据同步操作 | 主从同步/跨区域同步 |
| 13 | `DATA_REPLICATE` | 数据复制 | 🔵 数据流转 | 数据复制操作 | 异地灾备复制 |
| 14 | `BATCH_SUBMIT` | 批次提交 | 🟠 批处理 | 批量操作提交 | 提交批量写入任务 |
| 15 | `BATCH_EXECUTE` | 批次执行 | 🟠 批处理 | 批量操作执行中 | 批量任务执行过程 |
| 16 | `BATCH_COMPLETE` | 批次完成 | 🟠 批处理 | 批量操作完成 | 批量任务完成通知 |
| 17 | `SYSTEM_HEARTBEAT` | 系统心跳 | 🟣 系统运维 | 系统心跳信号 | 服务存活探测 |
| 18 | `SYSTEM_ALERT` | 系统告警 | 🟣 系统运维 | 系统告警事件 | 磁盘空间/性能/容量告警 |
| 19 | `SYSTEM_FAILOVER` | 系统故障转移 | 🟣 系统运维 | 系统故障切换 | 主备切换 |
| 20 | `SYSTEM_CONFIG_CHANGE` | 配置变更 | 🟣 系统运维 | 系统配置变更 | 配置参数更新 |
| 21 | `SYSTEM_UPGRADE` | 系统升级 | 🟣 系统运维 | 系统版本升级 | 服务版本升级 |
| 22 | `ACCESS_AUDIT` | 访问审计 | 🔴 安全审计 | 访问审计日志 | 登录/权限变更/敏感操作 |
| 23 | `ACCESS_PERMISSION_CHANGE` | 权限变更 | 🔴 安全审计 | 权限变更操作 | 用户权限提升/降级 |
| 24 | `DATA_QUALITY_CHECK` | 数据质量检查 | 🟡 质量监控 | 数据质量检查结果 | 完整性/一致性校验 |
| 25 | `ERROR_UNHANDLED` | 未处理错误 | 🟡 质量监控 | 未分类的错误事件 | 未知/未预期的错误 |

#### 4.1.3 枚举分类统计

| 分类 | 颜色标识 | 枚举数量 | 枚举值 |
|------|:--------:|:--------:|--------|
| 存储操作 | 🟢 | 8 | STORAGE_CREATE, STORAGE_UPDATE, STORAGE_DELETE, STORAGE_READ, STORAGE_ARCHIVE, STORAGE_RESTORE, STORAGE_COMPRESS, STORAGE_DECOMPRESS |
| 数据流转 | 🔵 | 5 | DATA_IMPORT, DATA_EXPORT, DATA_MIGRATE, DATA_SYNC, DATA_REPLICATE |
| 批处理 | 🟠 | 3 | BATCH_SUBMIT, BATCH_EXECUTE, BATCH_COMPLETE |
| 系统运维 | 🟣 | 5 | SYSTEM_HEARTBEAT, SYSTEM_ALERT, SYSTEM_FAILOVER, SYSTEM_CONFIG_CHANGE, SYSTEM_UPGRADE |
| 安全审计 | 🔴 | 2 | ACCESS_AUDIT, ACCESS_PERMISSION_CHANGE |
| 质量监控 | 🟡 | 2 | DATA_QUALITY_CHECK, ERROR_UNHANDLED |
| **合计** | — | **25** | — |

#### 4.1.4 枚举值扩展规范

- **向后兼容**: 新增枚举值不影响现有系统的运行 (未知枚举值由 `ERROR_UNHANDLED` 兜底)
- **版本管理**: 枚举值变更需在 `event_schema_version` 中记录
- **命名规则**: 全大写字母 + 下划线分隔，长度不超过 32 字符
- **废弃策略**: 废弃的枚举值标记为 `@deprecated` 注释，保留至少 2 个大版本周期

---

### 4.2 priority — 事件优先级

#### 4.2.1 字段定义

| 属性 | 值 |
|------|-----|
| **字段名** | `priority` |
| **数据类型** | integer |
| **取值范围** | 1 ~ 10 (含边界) |
| **是否必填** | ✅ 是 |
| **默认值** | `5` (中等优先级) |
| **校验规则** | 必须为 1-10 之间的整数，拒绝浮点数、字符串与超范围值 |

#### 4.2.2 优先级等级定义

| 优先级 | 等级名称 | 颜色标识 | SLA 延迟目标 | 说明 | 典型事件类型 |
|:------:|----------|:--------:|:------------:|------|-------------|
| **10** | P10 — 紧急 | 🔴 Critical | ≤ 100ms | 最高优先级，立即处理，中断正常队列 | SYSTEM_FAILOVER, SYSTEM_ALERT (Critical) |
| **9** | P9 — 高紧急 | 🔴 Critical | ≤ 200ms | 高紧急级别，优先调度 | ACCESS_PERMISSION_CHANGE, STORAGE_DELETE (批量) |
| **8** | P8 — 高 | 🟠 High | ≤ 500ms | 高优先级，快速响应 | STORAGE_CREATE (关键), DATA_IMPORT (批量) |
| **7** | P7 — 中高 | 🟠 High | ≤ 1s | 中高优先级，优先处理 | BATCH_SUBMIT, DATA_MIGRATE |
| **6** | P6 — 中偏高 | 🟡 Medium | ≤ 2s | 中偏高优先级 | STORAGE_UPDATE (重要), DATA_EXPORT |
| **5** | P5 — 中 | 🟡 Medium | ≤ 3s | 中等优先级，默认值 | STORAGE_READ, DATA_QUALITY_CHECK |
| **4** | P4 — 中偏低 | 🟢 Low | ≤ 5s | 中偏低优先级 | SYSTEM_CONFIG_CHANGE |
| **3** | P3 — 低 | 🟢 Low | ≤ 10s | 低优先级，空闲时处理 | STORAGE_COMPRESS, STORAGE_ARCHIVE |
| **2** | P2 — 极低 | ⚪ Very Low | ≤ 30s | 极低优先级，尽力而为 | STORAGE_DECOMPRESS |
| **1** | P1 — 最低 | ⚪ Very Low | ≤ 60s | 最低优先级，仅空闲处理 | SYSTEM_HEARTBEAT |

#### 4.2.3 优先级与 event_type 推荐映射

| event_type | 推荐 priority | 理由 |
|------------|:-------------:|------|
| `SYSTEM_FAILOVER` | 10 | 故障切换需立即处理，影响系统可用性 |
| `SYSTEM_ALERT` | 9 | 告警需快速响应，避免事态扩大 |
| `ACCESS_PERMISSION_CHANGE` | 9 | 权限变更需立即审计 |
| `STORAGE_DELETE` | 8 | 删除操作需快速确认，避免数据丢失 |
| `DATA_IMPORT` | 7 | 批量导入需优先处理，避免队列堵塞 |
| `BATCH_SUBMIT` | 7 | 批处理任务提交需快速确认 |
| `STORAGE_CREATE` | 8 | 存储创建是业务关键操作 |
| `DATA_MIGRATE` | 7 | 数据迁移需优先调度 |
| `STORAGE_UPDATE` | 6 | 常规更新操作 |
| `DATA_EXPORT` | 6 | 导出数据操作 |
| `STORAGE_READ` | 5 | 常规读取操作，中等优先级 |
| `DATA_QUALITY_CHECK` | 5 | 质量检查中等优先级 |
| `SYSTEM_CONFIG_CHANGE` | 4 | 配置变更可稍后处理 |
| `STORAGE_COMPRESS` | 3 | 压缩操作可在空闲时执行 |
| `STORAGE_ARCHIVE` | 3 | 归档操作可在空闲时执行 |
| `STORAGE_DECOMPRESS` | 2 | 解压操作可在空闲时执行 |
| `SYSTEM_HEARTBEAT` | 1 | 心跳信号，最低优先级 |
| 其他 (ACCESS_AUDIT, ERROR_UNHANDLED 等) | 5 | 默认中等优先级 |

#### 4.2.4 优先级调度算法

```
┌─────────────────────────────────────────────────────┐
│          DSHE 事件队列优先级调度算法                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  事件到达 ──→ 提取 priority ──→ 路由到优先级队列       │
│                                       │             │
│                    ┌──────────────────┼──────────┐   │
│                    │                  │          │   │
│              ┌─────▼─────┐    ┌──────▼───┐  ┌──▼──┐ │
│              │ P10-P8   │    │ P7-P5    │  │P4-P1│ │
│              │ 快速通道  │    │ 标准通道  │  │慢速 │ │
│              │ ≤500ms   │    │ ≤3s      │  │≤60s │ │
│              └──────────┘    └──────────┘  └─────┘ │
│                                                     │
│  调度策略:                                          │
│  1. P10-P8: 中断当前低优先级处理，立即调度            │
│  2. P7-P5:  FIFO 顺序处理                          │
│  3. P4-P1:  空闲时轮询处理                          │
│                                                     │
│  饥饿防护:                                          │
│  - P1-P4 事件等待超过 SLA 后自动提升 priority        │
│  - 优先级提升上限: 当前 priority + 2 (不超过 10)     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### 4.2.5 优先级校验规则

- ✅ `priority` 必须为整数类型 (int32)
- ✅ `priority` 值必须在 [1, 10] 闭区间内
- ❌ 拒绝浮点数 (如 `5.5`)
- ❌ 拒绝字符串 (如 `"high"`)
- ❌ 拒绝超范围值 (如 `0` 或 `11`)
- ⚠️ `priority` 为 `null` 时自动设为默认值 `5`
- ⚠️ `priority` 为负数时拒绝事件产生 (抛异常)

---

### 4.3 trace_id — 全链路追踪标识

#### 4.3.1 字段定义

| 属性 | 值 |
|------|-----|
| **字段名** | `trace_id` |
| **数据类型** | string (UUID v4) |
| **格式规范** | RFC 4122 UUID v4 (36 字符, 含 4 个连字符) |
| **是否必填** | ✅ 是 (全局追踪层，始终必填) |
| **唯一性范围** | 全局唯一 (跨所有系统、跨所有时间) |
| **生命周期** | 事件产生时生成，贯穿事件全生命周期 |
| **传播方式** | 事件流转过程中不变，跨系统保持一致 |

#### 4.3.2 UUID v4 生成规范

```python
# trace_id 生成伪代码 (Python 参考实现)
import uuid
import secrets

def generate_trace_id():
    """
    生成 UUID v4 格式的 trace_id
    
    UUID v4 结构:
    ┌─────┬─────┬─────┬─────┬─────┐
    │ 8位 │ 4位 │ 4位 │ 4位 │ 12位 │
    └─────┴─────┴─────┴─────┴─────┘
     时间  时间  版本  变体   随机
    
    版本位: 第 13 位固定为 '4' (UUID v4)
    变体位: 第 17 位固定为 '8','9','a','b' 之一
    """
    # 方法1: 使用标准库 (推荐)
    return str(uuid.uuid4())
    
    # 方法2: 手动生成 (高并发场景，避免 GIL 竞争)
    # 随机生成 16 字节
    raw_bytes = secrets.token_bytes(16)
    
    # 设置版本位 (UUID v4)
    raw_bytes[6] = (raw_bytes[6] & 0x0F) | 0x40
    # 设置变体位 (RFC 4122)
    raw_bytes[8] = (raw_bytes[8] & 0x3F) | 0x80
    
    # 格式化为标准 UUID 字符串
    hex_bytes = raw_bytes.hex()
    return f"{hex_bytes[0:8]}-{hex_bytes[8:12]}-{hex_bytes[12:16]}-{hex_bytes[16:20]}-{hex_bytes[20:32]}"
```

#### 4.3.3 传播规则

| 场景 | 行为 | 说明 |
|------|------|------|
| DSHB 产生新事件 | 生成新 trace_id | 每个独立事件产生一个唯一的 trace_id |
| DSHB → DSHE 事件传递 | trace_id 保持不变 | DSHE 消费时读取 trace_id，用于关联追踪 |
| DSHE → HERMES 事件传递 | trace_id 保持不变 | HERMES 审计时通过 trace_id 关联全链路 |
| 事件重试 | trace_id 保持不变 | 重试后的事件仍使用原始 trace_id |
| 事件关联 (parent_event_id) | trace_id 继承父事件 | 子事件的 trace_id 与父事件相同 |
| 批次操作 (batch_id) | 同一批次内所有事件共享 trace_id | 批次操作视为一个逻辑事务 |
| 跨系统调用 | trace_id 通过 event_payload 传递 | 下游系统从 payload 中读取 trace_id |

#### 4.3.4 校验规则

- ✅ 必须符合 UUID v4 格式: 正则 `[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}`
- ✅ 长度必须为 36 字符 (含 4 个连字符)
- ❌ 拒绝 UUID v1/v2/v3/v5/v6/v7/v8 格式 (仅支持 v4)
- ❌ 拒绝空字符串与 `null` 值
- ❌ 拒绝大写 (必须全小写)

#### 4.3.5 与 event_id 的关系

| 维度 | trace_id | event_id |
|------|----------|----------|
| **语义** | 全链路追踪标识 | 事件唯一标识 |
| **粒度** | 追踪级别 (跨事件关联) | 事件级别 (单事件唯一) |
| **数量** | 1 个 trace_id 对应 N 个 event_id | 1 个 event_id 对应 1 个 trace_id |
| **生成时机** | 事件链首次产生时 | 每个事件独立产生时 |
| **是否变更** | 跨系统不变 | 每个事件独立生成 |
| **用途** | 跨系统追踪、关联分析 | 事件唯一识别、去重 |
| **索引** | 二级索引 (查询频率较低) | 主键索引 (查询频率极高) |

---

### 4.4 batch_id — 批量操作标识

#### 4.4.1 字段定义

| 属性 | 值 |
|------|-----|
| **字段名** | `batch_id` |
| **数据类型** | string (结构化) |
| **格式规范** | `{source}_{timestamp}_{seq}` |
| **是否必填** | ⚠️ 条件必填 (批量操作时必填) |
| **唯一性范围** | 全局唯一 (跨所有系统、跨所有时间) |
| **最大长度** | 64 字符 |

#### 4.4.2 格式规范

```
batch_id 格式: {source}_{timestamp}_{seq}

┌──────────┬───────────────────────────┬─────────┐
│  source  │  timestamp                │  seq    │
│  (来源)   │  (时间戳)                 │  (序号)  │
└──────────┴───────────────────────────┴─────────┘

字段说明:
┌──────────┬────────────┬────────────────────────────────────────┐
│  source  │  来源标识    │  DSHB/DSHE/HERMES/EXT (不超过 8 字符)  │
│          │            │  DSHB = DSHB 系统产生                    │
│          │            │  DSHE = DSHE 系统产生                    │
│          │            │  HERMES = HERMES 系统产生                │
│          │            │  EXT  = 外部系统产生                     │
├──────────┼────────────┼────────────────────────────────────────┤
│timestamp │  时间戳     │  YYYYMMDDHHmmss (14 位数字)             │
│          │            │  24 小时制，UTC+8 时区                   │
├──────────┼────────────┼────────────────────────────────────────┤
│  seq    │  批次序号    │  4 位数字，从 0001 开始递增              │
│          │            │  同一秒内最多 9999 个批次               │
└──────────┴────────────┴────────────────────────────────────────┘

示例:
  DSHB_20270319143000_0001    # DSHB 系统, 2027-03-19 14:30:00, 第 1 批次
  DSHB_20270319143000_0002    # 同一秒第 2 批次
  DSHE_20270319143001_0001    # DSHE 系统, 下一秒第 1 批次
  HERMES_20270319143002_0001  # HERMES 系统
  EXT_20270319143003_0001     # 外部系统
```

#### 4.4.3 校验正则

```
正则表达式: ^(DSHB|DSHE|HERMES|EXT)_\d{14}_\d{4}$

分解:
  ^                 # 字符串起始
  (DSHB|DSHE|HERMES|EXT)  # 来源标识 (4选1)
  _                 # 分隔符
  \d{14}            # 14 位数字时间戳 (YYYYMMDDHHmmss)
  _                 # 分隔符
  \d{4}             # 4 位数字序号 (0001-9999)
  $                 # 字符串结束

合法示例:
  ✅ DSHB_20270319143000_0001
  ✅ DSHE_20270319143001_0042
  ✅ HERMES_20270319143002_0001
  ✅ EXT_20270319143003_9999

非法示例:
  ❌ DSHB_20270319_0001        (时间戳不足 14 位)
  ❌ dshb_20270319143000_0001  (source 小写)
  ❌ DSHB_202703191430000_0001 (时间戳 15 位)
  ❌ DSHB_20270319143000_1     (seq 不足 4 位)
  ❌ BATCH_20270319143000_0001 (source 不在枚举中)
```

#### 4.4.4 批次上下文 (扩展层 batch_id)

扩展层的 `batch_id` 允许携带额外的批次上下文信息，通过 `event_payload` 中的嵌套 JSON 对象实现:

```json
{
  "batch_id": "DSHB_20270319143000_0001",
  "event_payload": {
    "batch_context": {
      "batch_name": "每日增量导入-华东集群",
      "batch_total_events": 50000,
      "batch_current_event": 2345,
      "parent_batch_id": "DSHB_20270318143000_0001",
      "sub_batch_ids": [
        "DSHB_20270319143001_0001",
        "DSHB_20270319143001_0002"
      ],
      "batch_status": "IN_PROGRESS",
      "batch_start_time": "2027-03-19T14:30:00Z",
      "batch_expected_end_time": "2027-03-19T16:00:00Z",
      "batch_owner": "data-ingestion-team",
      "batch_priority": 7
    }
  }
}
```

#### 4.4.5 批次生命周期

```
┌─────────────────────────────────────────────────────────┐
│                  批次生命周期状态机                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ┌────────┐    提交     ┌──────────┐    执行     ┌─────┐│
│   │ CREATED │ ─────────→ │ PENDING  │ ─────────→ │ EXEC ││
│   └────────┘            └──────────┘            └─────┘│
│        │                  │                  │           │
│        │ 取消              │ 取消              │ 失败      │
│        ▼                  ▼                  ▼           │
│   ┌────────┐        ┌────────┐         ┌─────────┐      │
│   │CANCELLED│       │CANCELLED│         │ FAILED  │      │
│   └────────┘        └────────┘         └─────────┘      │
│                                        │                 │
│                                        │ 重试成功          │
│                                        ▼                 │
│                                   ┌──────────┐           │
│                                   │COMPLETED │           │
│                                   └──────────┘           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

| 状态 | 值 | 说明 |
|------|-----|------|
| CREATED | `CREATED` | 批次已创建，尚未提交 |
| PENDING | `PENDING` | 批次已提交，等待调度 |
| EXECUTING | `EXECUTING` | 批次正在执行 |
| COMPLETED | `COMPLETED` | 批次执行完成 |
| FAILED | `FAILED` | 批次执行失败 |
| CANCELLED | `CANCELLED` | 批次已取消 |

---

### 4.5 retry_count — 重试计数

#### 4.5.1 字段定义

| 属性 | 值 |
|------|-----|
| **字段名** | `retry_count` |
| **数据类型** | integer (int32) |
| **取值范围** | 0 ~ 5 (含边界) |
| **是否必填** | ✅ 是 |
| **默认值** | `0` (首次投递，无重试) |
| **最大重试次数** | 5 |
| **超限行为** | 进入死信队列 (DLQ) |

#### 4.5.2 重试策略定义

| retry_count 值 | 含义 | 说明 | 系统行为 |
|:--------------:|------|------|----------|
| **0** | 首次投递 | 事件首次产生并投递，尚未重试 | ✅ 正常处理 |
| **1** | 第 1 次重试 | 首次投递失败后第 1 次重试 | ✅ 正常处理 |
| **2** | 第 2 次重试 | 第 2 次重试 | ✅ 正常处理 |
| **3** | 第 3 次重试 | 第 3 次重试 | ⚠️ 预警通知 |
| **4** | 第 4 次重试 | 第 4 次重试 | ⚠️ 预警通知 + 人工关注 |
| **5** | 第 5 次重试 (最大) | 最后一次重试 | 🔴 标记为即将进入 DLQ |

#### 4.5.3 重试时间窗口 (Exponential Backoff)

```
重试策略: 指数退避 + 抖动 (Jitter)

┌──────────┬────────────────┬──────────────────────────────────┐
│ 重试次数  │  等待时间      │  计算公式                          │
├──────────┼────────────────┼──────────────────────────────────┤
│ 1 → 2    │  2s ± 500ms   │  2^1 × 1s + random(-500ms, 500ms) │
│ 2 → 3    │  4s ± 1s      │  2^2 × 1s + random(-1s, 1s)       │
│ 3 → 4    │  8s ± 2s      │  2^3 × 1s + random(-2s, 2s)       │
│ 4 → 5    │  16s ± 4s     │  2^4 × 1s + random(-4s, 4s)       │
│ 5 → DLQ  │  —            │  超限，进入死信队列                 │
└──────────┴────────────────┴──────────────────────────────────┘

总最大等待时间: 2 + 4 + 8 + 16 = 30 秒 (不含抖动)
含抖动最大等待: 2.5 + 5 + 10 + 20 = 37.5 秒
```

#### 4.5.4 死信队列 (DLQ) 管理

当事件 `retry_count` 达到最大值 5 且重试仍失败时，事件进入死信队列 (DLQ):

```
┌─────────────────────────────────────────────────────────────┐
│                    死信队列 (DLQ) 管理                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  事件 ──→ 失败 ──→ retry_count++ ──→ retry_count ≥ 5?      │
│                                        │                    │
│                                   ┌────┴────┐               │
│                                   │ 是 (≥5)  │ 否 (<5)      │
│                                   ▼         ▼               │
│                              ┌────────┐ ┌────────┐          │
│                              │  DLQ   │ │ 重试   │          │
│                              └────────┘ └────────┘          │
│                                   │                         │
│                          ┌────────┴────────┐                │
│                          │                 │                │
│                    ┌─────▼──────┐   ┌─────▼─────┐          │
│                    │ DLQ 存储   │   │ DLQ 告警  │          │
│                    │ (持久化)   │   │ (通知人工) │          │
│                    └─────┬──────┘   └───────────┘          │
│                          │                                  │
│                    ┌─────▼──────┐                           │
│                    │ 人工处理   │                           │
│                    │ 1. 分析原因│                           │
│                    │ 2. 修复    │                           │
│                    │ 3. 手动重放│                           │
│                    │ 4. 确认结果│                           │
│                    └─────┬──────┘                           │
│                          │                                  │
│              ┌───────────┴───────────┐                      │
│              │                       │                      │
│         ┌────▼────┐           ┌─────▼─────┐                 │
│         │ 重放成功 │           │ 废弃归档  │                 │
│         │ 回到正常 │           │ (审计保留) │                 │
│         └─────────┘           └───────────┘                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 4.5.5 DLQ 存储规范

| 属性 | 规范 |
|------|------|
| **存储介质** | 持久化存储 (不丢失) |
| **保留周期** | 90 天 (可配置) |
| **保留内容** | 完整事件数据 + DLQ 元数据 (进入时间、失败原因、重试历史) |
| **访问权限** | 仅运维人员与审计人员可访问 |
| **重放能力** | 支持按事件/按批次/按时间范围批量重放 |
| **告警阈值** | DLQ 事件数 > 100 / 小时 触发告警 |

#### 4.5.6 校验规则

- ✅ `retry_count` 必须为整数类型 (int32)
- ✅ `retry_count` 值必须在 [0, 5] 闭区间内
- ✅ `retry_count = 0` 表示首次投递 (默认值)
- ❌ 拒绝浮点数 (如 `1.5`)
- ❌ 拒绝负数 (如 `-1`)
- ❌ 拒绝超范围值 (如 `6`)
- ⚠️ `retry_count = null` 时自动设为 `0`
- ⚠️ `retry_count = 5` 且再次失败时，拒绝新的事件投递 (强制进入 DLQ)

---

## 5. 三方命名对齐矩阵

### 5.1 命名原则

为确保 DSHB、DSHE、HERMES 三方系统在事件 Schema 适配过程中保持一致性，定义以下命名原则:

1. **蛇形命名法 (snake_case)**: 所有字段名统一使用蛇形命名法
2. **语义一致性**: 三方系统对同一字段的语义理解必须一致
3. **类型一致性**: 三方系统对同一字段的类型定义必须一致
4. **枚举对齐**: 枚举字段的取值范围在三方系统中必须完全一致
5. **版本同步**: 字段新增/修改必须同步通知所有三方系统

### 5.2 完整命名对齐矩阵 (20 字段)

| 序号 | DSHB 字段名 | DSHE 字段名 | HERMES 字段名 | 对齐状态 | 字段说明 |
|:----:|------------|-------------|--------------|:--------:|----------|
| 1 | `trace_id` | `trace_id` | `trace_id` | ✅ 完全一致 | 全链路追踪标识 |
| 2 | `event_id` | `event_id` | `event_id` | ✅ 完全一致 | 事件唯一标识 |
| 3 | `event_timestamp` | `event_time` | `event_timestamp` | ⚠️ DSHE 别名 | 事件产生时间 (DSHE 使用 `event_time` 别名) |
| 4 | `event_source` | `event_source` | `event_source` | ✅ 完全一致 | 事件来源系统 |
| 5 | `event_payload` | `event_data` | `event_payload` | ⚠️ DSHE 别名 | 事件负载数据 (DSHE 使用 `event_data` 别名) |
| 6 | `event_type` 🆕 | `event_type` | `event_type` | ✅ 完全一致 | 事件类型枚举 |
| 7 | `status_code` | `status` | `status_code` | ⚠️ DSHE 别名 | 事件处理状态 (DSHE 使用 `status` 别名) |
| 8 | `processing_time` | `processing_time` | `processing_time` | ✅ 完全一致 | 处理完成时间 |
| 9 | `processing_duration` | `processing_duration_ms` | `processing_duration` | ⚠️ DSHE 别名 | 处理耗时 (DSHE 使用 `processing_duration_ms` 别名，明确单位为毫秒) |
| 10 | `error_message` | `error_msg` | `error_message` | ⚠️ DSHE 别名 | 错误消息 (DSHE 使用 `error_msg` 缩写) |
| 11 | `version_tag` | `version_tag` | `version_tag` | ✅ 完全一致 | 版本标签 |
| 12 | `event_schema_version` | `schema_version` | `schema_version` | ⚠️ DSHE/HERMES 别名 | Schema 版本 (DSHE/HERMES 使用 `schema_version` 缩写) |
| 13 | `batch_id` (公共层) | `batch_id` | `batch_id` | ✅ 完全一致 | 批量操作标识 |
| 14 | `batch_id` (扩展层) | `batch_context` | `batch_context` | ⚠️ DSHE/HERMES 别名 | 批次上下文扩展 (DSHE/HERMES 使用 `batch_context` 表示扩展层信息) |
| 15 | `sequence_number` | `sequence` | `sequence_number` | ⚠️ DSHE 别名 | 序列号 (DSHE 使用 `sequence` 缩写) |
| 16 | `priority` 🆕 | `priority` | `priority` | ✅ 完全一致 | 事件优先级 |
| 17 | `retry_count` 🆕 | `retry_count` | `retry_count` | ✅ 完全一致 | 重试计数 |
| 18 | `parent_event_id` | `parent_event_id` | `parent_event_id` | ✅ 完全一致 | 父事件标识 |
| 19 | `tags` | `tags` | `tags` | ✅ 完全一致 | 标签列表 |
| 20 | `correlation_id` | `correlation_id` | `correlation_id` | ✅ 完全一致 | 关联标识 |
| 21 | `sha256_checksum` | `checksum` | `sha256_checksum` | ⚠️ DSHE 别名 | 数据校验和 (DSHE 使用 `checksum` 缩写) |

### 5.3 命名别名映射表

以下列出所有存在命名差异的字段，并提供双向映射关系:

| 字段语义 | DSHB 标准名 | DSHE 别名 | HERMES 别名 | 适配层处理 |
|----------|-------------|-----------|-------------|------------|
| 事件时间 | `event_timestamp` | `event_time` | — | DSHE 消费时将 `event_timestamp` 映射为 `event_time`，发送回 HERMES 时还原 |
| 事件负载 | `event_payload` | `event_data` | — | DSHE 消费时将 `event_payload` 映射为 `event_data`，发送回 HERMES 时还原 |
| 状态码 | `status_code` | `status` | — | DSHE 消费时将 `status_code` 映射为 `status`，发送回 HERMES 时还原 |
| 处理耗时 | `processing_duration` | `processing_duration_ms` | — | DSHE 消费时将 `processing_duration` 映射为 `processing_duration_ms` |
| 错误消息 | `error_message` | `error_msg` | — | DSHE 消费时将 `error_message` 映射为 `error_msg`，发送回时还原 |
| Schema 版本 | `event_schema_version` | `schema_version` | `schema_version` | DSHE/HERMES 消费时映射为 `schema_version` |
| 批次上下文 | `batch_id` (扩展层) | `batch_context` | `batch_context` | DSHE/HERMES 消费扩展层批次信息时使用 `batch_context` |
| 序列号 | `sequence_number` | `sequence` | — | DSHE 消费时将 `sequence_number` 映射为 `sequence` |
| 校验和 | `sha256_checksum` | `checksum` | — | DSHE 消费时将 `sha256_checksum` 映射为 `checksum` |

### 5.4 命名适配层设计

```
┌──────────────────────────────────────────────────────────────────┐
│                    事件 Schema 命名适配层                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐        ┌──────────────┐        ┌──────────┐       │
│  │  DSHB    │        │  适配层      │        │  DSHE    │       │
│  │ (标准名)  │───────→│  (双向映射)  │───────→│ (别名)   │       │
│  └──────────┘        └──────────────┘        └──────────┘       │
│                                                                  │
│  ┌──────────┐        ┌──────────────┐        ┌──────────┐       │
│  │  HERMES  │───────→│  (双向映射)  │───────→│  DSHB    │       │
│  │ (标准名)  │        │              │        │ (标准名)  │       │
│  └──────────┘        └──────────────┘        └──────────┘       │
│                                                                  │
│  适配层功能:                                                       │
│  1. DSHB → DSHE: 标准名 → 别名                                    │
│  2. DSHE → HERMES: 别名 → 标准名                                  │
│  3. 未知字段透传 (不丢弃，保留原始值)                                │
│  4. 字段缺失时填充默认值                                            │
│  5. 类型转换 (如 processing_duration: int → string)                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 5.5 命名对齐校验规则

- ✅ DSHB 系统必须使用标准名 (DSHB 是 Schema 标准定义方)
- ⚠️ DSHE 系统可使用别名，但必须在适配层完成双向映射
- ✅ HERMES 系统必须使用标准名
- ✅ 所有别名映射必须在三方系统部署前验证通过
- ❌ 禁止在适配层丢弃任何字段 (即使字段在目标系统中不使用，也必须透传保留)
- ⚠️ 未知字段 (Schema 中未定义的字段) 透传至 `extensions` 对象中

---

## 6. 数据完整性规则

### 6.1 规则概述

数据完整性规则 (Integrity Rules) 定义了事件从产生到消费的全生命周期中必须满足的校验条件。每条规则具有唯一编号、优先级和校验阶段，确保事件数据的质量与一致性。

### 6.2 规则定义 (INTEGRITY-01 ~ INTEGRITY-12)

#### INTEGRITY-01: event_id 唯一性校验

| 属性 | 值 |
|------|-----|
| **规则编号** | INTEGRITY-01 |
| **规则名称** | event_id 全局唯一性 |
| **优先级** | 🔴 Critical |
| **校验阶段** | 产生时 |
| **规则描述** | `event_id` 必须在系统全局范围内唯一，不得重复 |
| **校验逻辑** | 生成 event_id 后，查询存储系统确认无重复 |
| **违规处理** | 拒绝事件产生，抛出 `DuplicateEventIdError` |
| **违规示例** | ❌ 两个不同事件使用相同的 event_id |

```
校验伪代码:
IF EXISTS (SELECT 1 FROM events WHERE event_id = :event_id)
THEN
  RAISE DuplicateEventIdError("event_id '" + event_id + "' already exists")
ELSE
  INSERT INTO events (event_id, ...)
```

---

#### INTEGRITY-02: trace_id 格式校验

| 属性 | 值 |
|------|-----|
| **规则编号** | INTEGRITY-02 |
| **规则名称** | trace_id UUID v4 格式 |
| **优先级** | 🔴 Critical |
| **校验阶段** | 产生时 |
| **规则描述** | `trace_id` 必须符合 UUID v4 标准格式 |
| **校验逻辑** | 正则匹配: `^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` |
| **违规处理** | 拒绝事件产生，抛出 `InvalidTraceIdError` |
| **违规示例** | ❌ `12345` (不是 UUID 格式) ❌ `123e4567-e89b-12d3-a456-426614174000` (UUID v1，非 v4) |

---

#### INTEGRITY-03: event_timestamp 格式与合理性校验

| 属性 | 值 |
|------|-----|
| **规则编号** | INTEGRITY-03 |
| **规则名称** | event_timestamp ISO 8601 格式与合理性 |
| **优先级** | 🔴 Critical |
| **校验阶段** | 产生时 |
| **规则描述** | `event_timestamp` 必须符合 ISO 8601 格式且时间值合理 (不早于 2000-01-01，不晚于当前时间 + 5 分钟) |
| **校验逻辑** | 1) 格式校验: ISO 8601 正则 2) 范围校验: 2000-01-01T00:00:00Z ≤ timestamp ≤ NOW() + 5min |
| **违规处理** | 拒绝事件产生，抛出 `InvalidTimestampError` |
| **违规示例** | ❌ `2027-13-45T99:99:99Z` (无效日期) ❌ `2027-03-19T14:30:00.123` (缺少时区标识 Z) ❌ `1999-12-31T23:59:59Z` (早于 2000 年) |

---

#### INTEGRITY-04: event_type 枚举值校验

| 属性 | 值 |
|------|-----|
| **规则编号** | INTEGRITY-04 |
| **规则名称** | event_type 枚举值有效性 |
| **优先级** | 🔴 Critical |
| **校验阶段** | 产生时 |
| **规则描述** | `event_type` 必须是预定义的 25 个枚举值之一 |
| **校验逻辑** | `event_type` 必须在 EVENT_TYPE_ENUM 集合中 |
| **违规处理** | 拒绝事件产生，抛出 `InvalidEventTypeError` |
| **违规示例** | ❌ `UNKNOWN_TYPE` (不在枚举中) ❌ `storage_create` (小写，枚举要求全大写) ❌ `""` (空字符串) |

---

#### INTEGRITY-05: batch_id 格式校验

| 属性 | 值 |
|------|-----|
| **规则编号** | INTEGRITY-05 |
| **规则名称** | batch_id 结构化格式 |
| **优先级** | 🟡 High |
| **校验阶段** | 产生时 (批量操作时) |
| **规则描述** | `batch_id` 必须符合 `{source}_{timestamp}_{seq}` 格式 |
| **校验逻辑** | 正则匹配: `^(DSHB\|DSHE\|HERMES\|EXT)_\d{14}_\d{4}$` |
| **违规处理** | 拒绝事件产生，抛出 `InvalidBatchIdError` |
| **违规示例** | ❌ `BATCH_001` (格式不匹配) ❌ `DSHB_20270319_0001` (时间戳不足 14 位) |

---

#### INTEGRITY-06: priority 范围校验

| 属性 | 值 |
|------|-----|
| **规则编号** | INTEGRITY-06 |
| **规则名称** | priority 取值范围 |
| **优先级** | 🔴 Critical |
| **校验阶段** | 产生时 |
| **规则描述** | `priority` 必须为 [1, 10] 范围内的整数 |
| **校验逻辑** | `1 ≤ priority ≤ 10` 且 `priority` 为整数 |
| **违规处理** | 拒绝事件产生，抛出 `InvalidPriorityError` |
| **违规示例** | ❌ `0` (低于最小值) ❌ `11` (超过最大值) ❌ `5.5` (浮点数) ❌ `"high"` (字符串) |

---

#### INTEGRITY-07: retry_count 范围校验

| 属性 | 值 |
|------|-----|
| **规则编号** | INTEGRITY-07 |
| **规则名称** | retry_count 取值范围 |
| **优先级** | 🔴 Critical |
| **校验阶段** | 产生时 / 消费时 |
| **规则描述** | `retry_count` 必须为 [0, 5] 范围内的整数 |
| **校验逻辑** | `0 ≤ retry_count ≤ 5` 且 `retry_count` 为整数 |
| **违规处理** | 拒绝事件处理，抛出 `InvalidRetryCountError` |
| **违规示例** | ❌ `-1` (负数) ❌ `6` (超过最大值) ❌ `2.5` (浮点数) |

---

#### INTEGRITY-08: event_payload 非空与有效性校验

| 属性 | 值 |
|------|-----|
| **规则编号** | INTEGRITY-08 |
| **规则名称** | event_payload 非空与 JSON 有效性 |
| **优先级** | 🔴 Critical |
| **校验阶段** | 产生时 |
| **规则描述** | `event_payload` 必须为非空 JSON 对象，且 JSON 格式有效 |
| **校验逻辑** | 1) `event_payload` 不为 null/空 2) JSON 解析成功 3) 为 JSON 对象 (非数组/标量) |
| **违规处理** | 拒绝事件产生，抛出 `InvalidPayloadError` |
| **违规示例** | ❌ `null` (空值) ❌ `{invalid json}` (格式错误) ❌ `[]` (数组，应为对象) |

---

#### INTEGRITY-09: 条件字段必填校验

| 属性 | 值 |
|------|-----|
| **规则编号** | INTEGRITY-09 |
| **规则名称** | 条件必填字段完整性 |
| **优先级** | 🟡 High |
| **校验阶段** | 产生时 |
| **规则描述** | 根据事件状态和类型，校验条件必填字段是否完整 |
| **校验逻辑** | 见下表 |
| **违规处理** | 拒绝事件产生，抛出 `MissingRequiredFieldError` |

**条件必填矩阵**:

| 条件 | 必填字段 | 违规示例 |
|------|----------|----------|
| `status_code = "SUCCESS"` | `processing_time`, `processing_duration` | ❌ SUCCESS 状态缺少 processing_duration |
| `status_code = "FAILED"` | `error_message` | ❌ FAILED 状态缺少 error_message |
| `status_code = "TIMEOUT"` | `error_message`, `processing_duration` | ❌ TIMEOUT 状态缺少 error_message |
| 批量操作 (`batch_id` 非空) | `batch_id`, `sequence_number` | ❌ 有 batch_id 但缺少 sequence_number |
| 分布式事务 (`correlation_id` 非空) | `correlation_id`, `parent_event_id` | ❌ 有 correlation_id 但缺少 parent_event_id |
| 安全审计场景 | `sha256_checksum` | ❌ 安全审计事件缺少 sha256_checksum |

---

#### INTEGRITY-10: 命名对齐一致性校验

| 属性 | 值 |
|------|-----|
| **规则编号** | INTEGRITY-10 |
| **规则名称** | 三方命名映射一致性 |
| **优先级** | 🟡 High |
| **校验阶段** | 消费时 (DSHE) / 审计时 (HERMES) |
| **规则描述** | 事件字段名必须与目标系统的预期命名一致，或已通过适配层完成映射 |
| **校验逻辑** | 1) 检查字段名是否在目标系统的 Schema 中定义 2) 若使用别名，检查映射表是否包含该映射 3) 未定义的字段不得被丢弃 |
| **违规处理** | 警告日志 + 字段透传至 extensions，不拒绝事件 |
| **违规示例** | ⚠️ DSHE 收到 `event_timestamp` 但期望 `event_time` (适配层未正确映射) |

---

#### INTEGRITY-11: 版本兼容性校验

| 属性 | 值 |
|------|-----|
| **规则编号** | INTEGRITY-11 |
| **规则名称** | Schema 版本兼容性 |
| **优先级** | 🔴 Critical |
| **校验阶段** | 消费时 (DSHE) / 审计时 (HERMES) |
| **规则描述** | `event_schema_version` 必须与消费者支持的版本兼容 |
| **校验逻辑** | 1) 检查 `event_schema_version` 是否为消费者支持的版本 2) 若不兼容，检查是否存在向前兼容映射 3) 若无兼容映射，拒绝处理 |
| **违规处理** | 拒绝事件处理，抛出 `SchemaVersionIncompatibleError` |
| **违规示例** | ❌ DSHE 仅支持 Schema v86，收到 v87 事件且无兼容映射 |

---

#### INTEGRITY-12: sha256_checksum 完整性校验

| 属性 | 值 |
|------|-----|
| **规则编号** | INTEGRITY-12 |
| **规则名称** | SHA-256 校验和完整性 |
| **优先级** | 🟡 High |
| **校验阶段** | 审计时 (HERMES) |
| **规则描述** | 当 `sha256_checksum` 存在时，必须验证其与实际 event_payload 数据一致 |
| **校验逻辑** | 1) 提取 `sha256_checksum` 2) 对 `event_payload` 的 JSON 序列化结果计算 SHA-256 3) 比较计算值与声明值 4) 不一致则标记为完整性告警 |
| **违规处理** | 完整性告警 + 标记事件为 `INTEGRITY_WARNING`，不拒绝事件 (审计场景需保留原始数据) |
| **违规示例** | ⚠️ `sha256_checksum = "e3b0..."` 但实际 payload 计算结果为 `"a1b2..."` (数据被篡改) |

### 6.3 规则执行矩阵

| 规则编号 | 规则名称 | DSHB 产生时 | DSHE 消费时 | HERMES 审计时 | 优先级 |
|----------|----------|:----------:|:----------:|:------------:|:------:|
| INTEGRITY-01 | event_id 唯一性 | ✅ 执行 | — | — | 🔴 Critical |
| INTEGRITY-02 | trace_id 格式 | ✅ 执行 | ✅ 验证 | ✅ 验证 | 🔴 Critical |
| INTEGRITY-03 | event_timestamp 格式 | ✅ 执行 | ✅ 验证 | ✅ 验证 | 🔴 Critical |
| INTEGRITY-04 | event_type 枚举值 | ✅ 执行 | ✅ 验证 | ✅ 验证 | 🔴 Critical |
| INTEGRITY-05 | batch_id 格式 | ✅ 执行 | ✅ 验证 | ✅ 验证 | 🟡 High |
| INTEGRITY-06 | priority 范围 | ✅ 执行 | ✅ 验证 | ✅ 验证 | 🔴 Critical |
| INTEGRITY-07 | retry_count 范围 | ✅ 执行 | ✅ 执行 | ✅ 验证 | 🔴 Critical |
| INTEGRITY-08 | event_payload 有效性 | ✅ 执行 | ✅ 验证 | ✅ 验证 | 🔴 Critical |
| INTEGRITY-09 | 条件必填校验 | ✅ 执行 | ✅ 验证 | ✅ 验证 | 🟡 High |
| INTEGRITY-10 | 命名对齐一致性 | — | ✅ 执行 | ✅ 执行 | 🟡 High |
| INTEGRITY-11 | 版本兼容性 | — | ✅ 执行 | ✅ 执行 | 🔴 Critical |
| INTEGRITY-12 | sha256_checksum 完整性 | — | — | ✅ 执行 | 🟡 High |

### 6.4 规则执行统计

| 优先级 | 规则数量 | 规则编号 |
|:------:|:--------:|----------|
| 🔴 Critical | 8 | INTEGRITY-01, 02, 03, 04, 06, 07, 08, 11 |
| 🟡 High | 4 | INTEGRITY-05, 09, 10, 12 |
| **合计** | **12** | — |

---

## 7. Schema 版本管理策略

### 7.1 版本命名规范

| 属性 | 规范 |
|------|------|
| **版本标识字段** | `event_schema_version` (整数字符串，如 `"87"`) |
| **版本格式** | 主版本号 (如 `"87"`，非 `"V87"` 或 `"87.0"`) |
| **版本递增** | 仅在 Schema 结构变更时递增，不随功能版本递增 |
| **当前版本** | `"87"` (V87 RC1) |
| **前序版本** | `"86"` (V86) |

### 7.2 V86 → V87 版本变更摘要

| 变更类型 | 字段 | 变更内容 | 兼容性 |
|----------|------|----------|:------:|
| 🆕 新增字段 | `trace_id` | 新增全局追踪层字段 | ✅ 向后兼容 (新字段可缺省) |
| 🆕 新增字段 | `event_type` | 新增公共层枚举字段 | ⚠️ 需适配 (V86 事件无此字段) |
| 🆕 新增字段 | `priority` | 新增扩展层整数字段 | ⚠️ 需适配 (V86 事件无此字段) |
| 🆕 新增字段 | `batch_id` | 新增公共层+扩展层字段 | ⚠️ 需适配 (V86 事件无此字段) |
| 🆕 新增字段 | `retry_count` | 新增扩展层整数字段 | ⚠️ 需适配 (V86 事件无此字段) |
| 无变更 | 其他 15 个字段 | 保持不变 | ✅ 完全兼容 |

### 7.3 向后兼容性设计

#### 7.3.1 新增字段的默认值策略

为确保 V87 消费者能够处理 V86 遗留事件 (无新字段)，定义以下默认值:

| 字段 | V86 事件默认值 | V87 事件默认值 | 说明 |
|------|:-------------:|:-------------:|------|
| `trace_id` | 消费时生成 (兼容模式) | 产生时生成 | V86 事件在 DSHE 消费时由 DSHE 生成 trace_id 并标记为 `TRACE_COMPAT_MODE` |
| `event_type` | `"UNKNOWN_TYPE"` | 必须显式指定 | V86 事件使用兜底枚举值，触发兼容告警 |
| `priority` | `5` (中等优先级) | 必须显式指定 (1-10) | V86 事件使用默认中等优先级 |
| `batch_id` | `null` (不指定) | 批量操作时必须指定 | V86 事件无批次概念 |
| `retry_count` | `0` (首次投递) | 必须显式指定 (0-5) | V86 事件视为首次投递 |

#### 7.3.2 版本协商机制

```
┌─────────────────────────────────────────────────────────────┐
│                  Schema 版本协商流程                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  DSHB ──→ 事件 (event_schema_version="87") ──→ DSHE         │
│                                                             │
│  DSHE 检查:                                                  │
│    IF event_schema_version > 当前支持版本:                     │
│      IF 存在版本映射规则:                                     │
│        → 应用映射，降级处理                                    │
│      ELSE:                                                   │
│        → 拒绝事件，抛出 SchemaVersionIncompatibleError       │
│                                                             │
│    IF event_schema_version < 当前支持版本:                     │
│      → 兼容处理 (使用默认值填充新增字段)                       │
│                                                             │
│    IF event_schema_version == 当前支持版本:                    │
│      → 正常处理                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 7.3.3 版本映射表

| 从版本 | 到版本 | 映射规则 | 优先级 |
|:------:|:------:|----------|:------:|
| 86 | 87 | 新增字段填充默认值，旧字段保持不变 | ✅ 自动映射 |
| 87 | 86 | 删除新增字段，保留旧字段 | ⚠️ 需手动确认 (数据可能丢失) |
| 87 | 86 | 仅删除新增字段，不修改旧字段值 | ✅ 安全降级 |

### 7.4 版本管理规则

| 规则编号 | 规则 | 说明 |
|----------|------|------|
| VERSION-01 | 版本号不可逆 | 一旦发布，版本号不可回退或重用 |
| VERSION-02 | 字段只增不减 | 已定义的字段不得删除 (只能标记为 @deprecated) |
| VERSION-03 | 废弃保留 2 版本 | 废弃字段至少保留 2 个大版本周期后才可删除 |
| VERSION-04 | 向后兼容优先 | 新版本必须向后兼容旧版本 (新增字段可缺省) |
| VERSION-05 | 文档同步更新 | 版本变更必须同步更新本规范文档 |
| VERSION-06 | 三方通知 | 版本变更必须通知 DSHB/DSHE/HERMES 三方系统 |

---

## 8. 事件管道流转架构

### 8.1 全链路架构图

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           V87 事件全链路流转架构                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                        事件产生层 (Event Production)                            │   │
│  │                                                                              │   │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐               │   │
│  │  │存储引擎   │    │数据导入   │    │批处理引擎  │    │系统监控   │               │   │
│  │  │          │    │服务       │    │          │    │          │               │   │
│  │  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘               │   │
│  │       │               │               │               │                      │   │
│  │       └───────────────┴───────┬───────┴───────────────┘                      │   │
│  │                               │                                                │   │
│  │                    ┌──────────▼──────────┐                                    │   │
│  │                    │  事件生成器          │                                    │   │
│  │                    │  (Event Generator)   │                                    │   │
│  │                    │                      │                                    │   │
│  │                    │  生成 20 字段完整事件  │                                    │   │
│  │                    │  执行 INTEGRITY-01~09│                                    │   │
│  │                    │  设置 event_schema_  │                                    │   │
│  │                    │  version = "87"      │                                    │   │
│  │                    └──────────┬──────────┘                                    │   │
│  └───────────────────────────────┬───────────────────────────────────────────────┘   │
│                                  │                                                  │
│  ┌───────────────────────────────▼───────────────────────────────────────────────┐   │
│  │                      事件队列层 (Event Queue)                                    │   │
│  │                                                                                │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │   │
│  │  │ P10-P8   │  │  P7-P5   │  │  P4-P1   │  │  DLQ      │                     │   │
│  │  │ 快速通道  │  │ 标准通道  │  │ 慢速通道  │  │ 死信队列  │                     │   │
│  │  │ ≤500ms   │  │ ≤3s      │  │ ≤60s     │  │ (retry≥5)│                     │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘                     │   │
│  │       │              │              │              │                           │   │
│  │       └──────────────┴──────┬───────┴──────────────┘                           │   │
│  │                             │                                                   │   │
│  └─────────────────────────────┬───────────────────────────────────────────────────┘   │
│                                │                                                     │
│  ┌─────────────────────────────▼───────────────────────────────────────────────────┐   │
│  │                      事件消费层 (Event Consumption)                               │   │
│  │                                                                                  │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐ │   │
│  │  │                        DSHE 事件处理引擎                                       │ │   │
│  │  │                                                                              │ │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │ │   │
│  │  │  │ 版本协商     │→ │ 命名映射     │→ │ 数据处理     │→ │ 结果回传     │       │ │   │
│  │  │  │ (Integrity-  │  │ (Integrity- │  │ (业务逻辑)   │  │             │       │ │   │
│  │  │  │  11)         │  │  10)         │  │             │  │             │       │ │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │ │   │
│  │  │        │                │                │                │                  │ │   │
│  │  │        ▼                ▼                ▼                ▼                  │ │   │
│  │  │  执行 INTEGRITY-  校验字段映射     执行业务逻辑     记录处理结果              │ │   │
│  │  │  10, INTEGRITY-11                                                    │ │   │
│  │  │                                                                              │ │   │
│  │  └─────────────────────────────────────────────────────────────────────────────┘ │   │
│  │                              │                                                    │   │
│  └──────────────────────────────┬──────────────────────────────────────────────────┘   │
│                                 │                                                     │
│  ┌──────────────────────────────▼──────────────────────────────────────────────────┐   │
│  │                      事件审计层 (Event Audit)                                      │   │
│  │                                                                                  │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐ │   │
│  │  │                        HERMES 审计引擎                                        │ │   │
│  │  │                                                                              │ │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │ │   │
│  │  │  │ 完整性校验   │→ │ 合规检查     │→ │ 追踪分析     │→ │ 报告生成     │       │ │   │
│  │  │  │ (Integrity-  │  │ (枚举/规则)  │  │ (trace_id   │  │             │       │ │   │
│  │  │  │  12)         │  │             │  │ 关联分析)    │  │             │       │ │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │ │   │
│  │  │        │                │                │                │                  │ │   │
│  │  │        ▼                ▼                ▼                ▼                  │ │   │
│  │  │  验证 SHA-256     检查合规规则      全链路追踪关联     生成审计报告          │ │   │
│  │  │  校验和完整性                                                              │ │   │
│  │  │                                                                              │ │   │
│  │  └─────────────────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                                  │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 事件流转步骤详解

| 步骤 | 阶段 | 系统 | 操作 | 关键字段 | 校验规则 |
|:----:|------|------|------|----------|----------|
| 1 | 事件产生 | DSHB | 生成事件，设置 20 个字段 | 全部 20 字段 | INTEGRITY-01~09 |
| 2 | 版本标记 | DSHB | 设置 `event_schema_version = "87"` | `event_schema_version` | INTEGRITY-03 |
| 3 | 优先级路由 | DSHB | 根据 `priority` 路由到对应队列 | `priority` | INTEGRITY-06 |
| 4 | 事件入队 | DSHB | 事件写入对应优先级队列 | 全部 20 字段 | — |
| 5 | 事件出队 | DSHE | 从队列中取出事件 | 全部 20 字段 | — |
| 6 | 版本协商 | DSHE | 检查 `event_schema_version` 兼容性 | `event_schema_version` | INTEGRITY-11 |
| 7 | 命名映射 | DSHE | 执行字段名映射 (DSHB → DSHE) | 全部 20 字段 | INTEGRITY-10 |
| 8 | 完整性校验 | DSHE | 执行 INTEGRITY-02~08 验证 | trace_id, event_type, priority, etc. | INTEGRITY-02~08 |
| 9 | 重试判断 | DSHE | 检查 `retry_count`，决定是否重试 | `retry_count` | INTEGRITY-07 |
| 10 | 业务处理 | DSHE | 执行业务逻辑 | `event_payload` | — |
| 11 | 结果记录 | DSHE | 记录 `status_code`, `processing_time`, `processing_duration` | status_code, processing_time, processing_duration | INTEGRITY-09 |
| 12 | 事件回传 | DSHE | 将处理结果回传至 HERMES | 全部 20 字段 | — |
| 13 | 命名还原 | DSHE→HERMES | 执行字段名还原 (DSHE → 标准名) | 全部 20 字段 | INTEGRITY-10 |
| 14 | 完整性验证 | HERMES | 验证 SHA-256 校验和 | `sha256_checksum`, `event_payload` | INTEGRITY-12 |
| 15 | 合规检查 | HERMES | 检查事件合规性 | 全部字段 | INTEGRITY-04, 06, 07 |
| 16 | 追踪分析 | HERMES | 通过 `trace_id` 关联全链路事件 | `trace_id` | — |
| 17 | 报告生成 | HERMES | 生成审计报告 | 全部字段 | — |

### 8.3 重试流程详解

```
事件到达 DSHE
    │
    ▼
┌──────────────┐    是    ┌──────────────┐
│ retry_count  │────────→│  执行业务处理  │──────→ 成功 ──→ 完成
│   < 5        │         └──────────────┘
└──────┬───────┘
       │ 否 (retry_count ≥ 5)
       ▼
┌──────────────┐
│  进入 DLQ     │──────→ 告警通知运维人员
└──────────────┘         └──────→ 运维人员手动处理 (分析原因/修复/重放)

重试流程:
┌──────────┐    失败    ┌──────────────┐    成功    ┌──────────────┐
│ 处理事件  │─────────→ │ retry_count++ │─────────→ │ 更新状态      │
│          │           │ 检查 retry     │           │ status=      │
└──────────┘           │ _count < 5?    │           │ SUCCESS      │
                       └──────┬───────┘           └──────────────┘
                              │
                         ┌────▼─────┐
                         │ 是 (<5)   │──────→ 等待退避时间 ──→ 重新入队
                         │ 否 (≥5)   │──────→ 进入 DLQ
                         └──────────┘
```

### 8.4 关键路径与 SLA

| 路径 | 关键事件类型 | SLA 延迟 | 重试策略 | 超时时间 |
|------|-------------|:--------:|----------|:--------:|
| 🔴 P10 关键路径 | SYSTEM_FAILOVER, SYSTEM_ALERT | ≤ 100ms | 不重试 (立即人工介入) | 5s |
| 🟠 P8-P9 高优先级 | STORAGE_DELETE, DATA_IMPORT | ≤ 500ms | 最多 3 次重试 | 30s |
| 🟡 P5-P7 中优先级 | STORAGE_READ, DATA_MIGRATE | ≤ 3s | 最多 5 次重试 | 60s |
| 🟢 P1-P4 低优先级 | SYSTEM_HEARTBEAT, STORAGE_COMPRESS | ≤ 60s | 最多 5 次重试 | 120s |

---

## 9. 三方验证机制

### 9.1 验证机制概述

三方验证机制确保 DSHB、DSHE、HERMES 三个系统在事件 Schema 适配过程中的一致性、完整性和正确性。验证分为三个阶段进行:

### 9.2 验证阶段划分

```
┌──────────────────────────────────────────────────────────────────┐
│                      三方验证时间线                                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase02 开始            阶段1           阶段2          阶段3      │
│  2027-03-05              │                │              │        │
│                          ▼                ▼              ▼        │
│                    ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│                    │ 单元测试   │→ │ 集成测试   │→ │ 端到端测试 │  │
│                    │ (TDD)     │  │ (UAT)     │  │ (E2E)     │  │
│                    └───────────┘  └───────────┘  └───────────┘  │
│                         │              │              │          │
│                    DSHB 独立      DSHB+DSHE      三方全部       │
│                    验证           联调验证       联合验证        │
│                                                                  │
│  目标: 每个阶段全绿方可进入下一阶段                                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 9.3 阶段一: DSHB 单元测试验证

| 验证项 | 验证内容 | 验证方法 | 通过标准 | 状态 |
|--------|----------|----------|:--------:|:----:|
| U01 | event_id UUID v4 格式生成 | 单元测试 | 100% 通过 | ✅ |
| U02 | trace_id UUID v4 格式生成 | 单元测试 | 100% 通过 | ✅ |
| U03 | event_timestamp ISO 8601 格式 | 单元测试 | 100% 通过 | ✅ |
| U04 | event_type 枚举值有效性 (25 值) | 单元测试 | 100% 通过 | ✅ |
| U05 | batch_id 格式校验 | 单元测试 | 100% 通过 | ✅ |
| U06 | priority 范围校验 (1-10) | 单元测试 | 100% 通过 | ✅ |
| U07 | retry_count 范围校验 (0-5) | 单元测试 | 100% 通过 | ✅ |
| U08 | event_payload JSON 有效性 | 单元测试 | 100% 通过 | ✅ |
| U09 | INTEGRITY-01~09 规则执行 | 单元测试 | 100% 通过 | ✅ |
| U10 | event_schema_version = "87" | 单元测试 | 100% 通过 | ✅ |
| U11 | 条件必填字段校验 | 单元测试 | 100% 通过 | ✅ |
| U12 | 向后兼容 (V86 事件默认值填充) | 单元测试 | 100% 通过 | ✅ |
| **合计** | — | — | — | **12/12 ✅** |

### 9.4 阶段二: DSHB-DSHE 集成测试验证

| 验证项 | 验证内容 | 验证方法 | 通过标准 | 状态 |
|--------|----------|----------|:--------:|:----:|
| I01 | 事件产生→消费全链路 | 集成测试 | 100% 通过 | ✅ |
| I02 | 字段命名映射正确性 | 集成测试 | 100% 通过 | ✅ |
| I03 | 版本协商机制 | 集成测试 | 100% 通过 | ✅ |
| I04 | 优先级队列路由 | 集成测试 | 100% 通过 | ✅ |
| I05 | 重试机制正确性 | 集成测试 | 100% 通过 | ✅ |
| I06 | DLQ 管理功能 | 集成测试 | 100% 通过 | ✅ |
| I07 | 20 字段完整性校验 | 集成测试 | 100% 通过 | ✅ |
| I08 | 命名适配层双向映射 | 集成测试 | 100% 通过 | ✅ |
| **合计** | — | — | — | **8/8 ✅** |

### 9.5 阶段三: DSHB-DSHE-HERMES 端到端验证

| 验证项 | 验证内容 | 验证方法 | 通过标准 | 状态 |
|--------|----------|----------|:--------:|:----:|
| E01 | 全链路事件追踪 (trace_id 关联) | E2E 测试 | 100% 通过 | ✅ |
| E02 | SHA-256 完整性校验 (INTEGRITY-12) | E2E 测试 | 100% 通过 | ✅ |
| E03 | 审计合规检查 | E2E 测试 | 100% 通过 | ✅ |
| E04 | 批量操作审计关联 (batch_id) | E2E 测试 | 100% 通过 | ✅ |
| E05 | 重试历史审计追踪 | E2E 测试 | 100% 通过 | ✅ |
| E06 | 三方命名一致性最终验证 | E2E 测试 | 100% 通过 | ✅ |
| E07 | 20 字段端到端完整性 | E2E 测试 | 100% 通过 | ✅ |
| E08 | 审计报告显示 | E2E 测试 | 100% 通过 | ✅ |
| **合计** | — | — | — | **8/8 ✅** |

### 9.6 三方会签记录

| 验证阶段 | DSHB 代表 | DSHE 代表 | HERMES 代表 | 会签结论 |
|----------|-----------|-----------|-------------|:--------:|
| 阶段一: 单元测试 | 王华 (架构师) | — | — | ✅ 全绿通过 |
| 阶段二: 集成测试 | 王华 (架构师) | 刘芳 (DSHE 负责人) | — | ✅ 全绿通过 |
| 阶段三: 端到端测试 | 王华 (架构师) | 刘芳 (DSHE 负责人) | 赵磊 (HERMES 负责人) | ✅ 全绿通过 |

---

## 10. 迁移实施计划

### 10.1 迁移时间线

```
Phase02 (2027-03-05 ~ 2027-03-19)
│
├─ Week 1 (03-05 ~ 03-08): 开发阶段
│  ├─ D-1 (03-05): Schema 定义与文档定稿
│  ├─ D-2 (03-06): DSHB 事件生成器适配开发
│  ├─ D-3 (03-07): DSHE 命名适配层开发
│  └─ D-4 (03-08): HERMES 审计引擎适配开发
│
├─ Week 2 (03-09 ~ 03-12): 测试阶段
│  ├─ D-5 (03-09): 单元测试 (阶段一)
│  ├─ D-6 (03-10): 集成测试 (阶段二)
│  ├─ D-7 (03-11): 端到端测试 (阶段三)
│  └─ D-8 (03-12): 测试报告与问题修复
│
├─ Week 3 (03-13 ~ 03-19): 发布阶段
│  ├─ D-9 (03-13): 灰度发布 (DSHB 10% 流量)
│  ├─ D-10 (03-14): 灰度验证
│  ├─ D-11 (03-15): 全量发布 (DSHB 100%)
│  ├─ D-12 (03-16): DSHE 适配部署
│  ├─ D-13 (03-17): HERMES 适配部署
│  ├─ D-14 (03-18): 全链路验证
│  └─ D-15 (03-19): 🟢 最终验收与签署
│
```

### 10.2 迁移步骤

| 步骤 | 日期 | 系统 | 操作 | 负责人 | 状态 |
|:----:|------|------|------|--------|:----:|
| M01 | 03-05 | 三方 | Schema 定义评审与定稿 | 王华 | ✅ 完成 |
| M02 | 03-06 | DSHB | 事件生成器适配开发 | 王华 | ✅ 完成 |
| M03 | 03-07 | DSHE | 命名适配层开发 | 刘芳 | ✅ 完成 |
| M04 | 03-08 | HERMES | 审计引擎适配开发 | 赵磊 | ✅ 完成 |
| M05 | 03-09 | DSHB | 单元测试执行与修复 | 王华 | ✅ 完成 |
| M06 | 03-10 | DSHB+DSHE | 集成测试执行与修复 | 王华+刘芳 | ✅ 完成 |
| M07 | 03-11 | 三方 | 端到端测试执行与修复 | 王华+刘芳+赵磊 | ✅ 完成 |
| M08 | 03-12 | 三方 | 测试报告评审与问题修复 | 王华+刘芳+赵磊 | ✅ 完成 |
| M09 | 03-13 | DSHB | 灰度发布 (10% 流量) | 王华 | ✅ 完成 |
| M10 | 03-14 | DSHB | 灰度验证与监控 | 王华 | ✅ 完成 |
| M11 | 03-15 | DSHB | 全量发布 (100%) | 王华 | ✅ 完成 |
| M12 | 03-16 | DSHE | DSHE 适配部署 | 刘芳 | ✅ 完成 |
| M13 | 03-17 | HERMES | HERMES 适配部署 | 赵磊 | ✅ 完成 |
| M14 | 03-18 | 三方 | 全链路验证 | 王华+刘芳+赵磊 | ✅ 完成 |
| M15 | 03-19 | 三方 | 🟢 最终验收与签署 | 王华+刘芳+赵磊+陈涛 | 🟡 待执行 |

### 10.3 回退方案

| 回退场景 | 触发条件 | 回退操作 | 影响范围 | 预计耗时 |
|----------|----------|----------|----------|:--------:|
| R01: DSHB 回退 | 事件产生失败率 > 5% | 回退 DSHB 至 V86 Schema，使用 V86 事件格式 | 仅影响新产生的事件 | ≤ 30 分钟 |
| R02: DSHE 回退 | 事件消费失败率 > 10% | 关闭命名适配层，使用 V86 模式消费 | 影响 DSHE 新消费的事件 | ≤ 15 分钟 |
| R03: HERMES 回退 | 审计完整性校验失败率 > 1% | 关闭 INTEGRITY-12 校验，保留其他审计功能 | 仅影响完整性校验 | ≤ 10 分钟 |
| R04: 三方全量回退 | 任意一方严重故障导致级联影响 | 三方同时回退至 V86 模式 | 全部事件 | ≤ 1 小时 |

#### 回退决策树

```
事件产生失败率 > 5%?
    │
    ├── 是 → R01: DSHB 回退
    │        │
    │        └─ 失败率降至 < 1%? ── 是 ──→ ✅ 回退完成
    │                        │
    │                        否 → R04: 三方全量回退
    │
    └── 否 → 继续监控 ──→ 事件消费失败率 > 10%?
                                  │
                                  ├── 是 → R02: DSHE 回退
                                  │        │
                                  │        └─ 失败率降至 < 5%? ── 是 ──→ ✅ 回退完成
                                  │                        │
                                  │                        否 → R04: 三方全量回退
                                  │
                                  └── 否 → 继续监控 ──→ 完整性校验失败率 > 1%?
                                                          │
                                                          ├── 是 → R03: HERMES 回退
                                                          │        │
                                                          │        └─ 失败率降至 < 0.5%? ── 是 ──→ ✅ 回退完成
                                                          │                        │
                                                          │                        否 → R04: 三方全量回退
                                                          │
                                                          └── 否 → ✅ 系统稳定
```

### 10.4 数据兼容性保障

| 保障措施 | 说明 | 验证方式 |
|----------|------|----------|
| 🛡️ 向后兼容 | V87 消费者可处理 V86 事件 (新增字段使用默认值) | 使用 V86 测试数据集验证 |
| 🛡️ 向前兼容 | V86 消费者忽略 V87 新增字段 (不报错) | 使用 V87 测试数据集在 V86 环境验证 |
| 🛡️ 灰度验证 | 10% → 50% → 100% 逐步扩大流量 | 每步观察 4 小时，确认无异常 |
| 🛡️ 双写验证 | 灰度期间 DSHB 同时写入 V86 和 V87 格式 (影子模式) | 对比两路写入的数据一致性 |
| 🛡️ 快速回退 | 任意步骤可立即回退，无需数据修复 | 执行回退脚本验证 (≤ 30 分钟) |

---

## 11. 验收标准与检查清单

### 11.1 验收标准总览

| 类别 | 验收项 | 通过标准 | 验证方法 | 状态 |
|------|--------|----------|----------|:----:|
| **Schema 完整性** | | | | |
| AC01 | 20 个字段全部定义 | 20/20 字段定义完整 | Schema 文档审查 | ✅ |
| AC02 | 5 个新字段规格完整 | 5/5 字段有完整规格 | 字段规格审查 | ✅ |
| AC03 | 枚举值完整 | 25/25 event_type 枚举值 | 枚举列表审查 | ✅ |
| **完整性规则** | | | | |
| AC04 | INTEGRITY-01~12 全部定义 | 12/12 规则定义完整 | 规则文档审查 | ✅ |
| AC05 | 规则执行矩阵完整 | 12/12 规则有执行矩阵 | 执行矩阵审查 | ✅ |
| AC06 | 规则校验逻辑可执行 | 12/12 规则可编写为代码 | 代码审查 | ✅ |
| **命名对齐** | | | | |
| AC07 | 三方命名映射表完整 | 20/20 字段有映射 | 映射表审查 | ✅ |
| AC08 | 别名映射双向正确 | 映射表可双向转换 | 映射测试 | ✅ |
| AC09 | 未知字段透传 | 未定义字段不丢弃 | 异常测试 | ✅ |
| **版本管理** | | | | |
| AC10 | V86→V87 兼容映射 | V86 事件可被 V87 消费 | 兼容测试 | ✅ |
| AC11 | 默认值策略定义 | 5/5 新字段有默认值 | 默认值审查 | ✅ |
| AC12 | 版本不可逆保证 | 版本号不回退 | 版本历史审查 | ✅ |
| **管道流转** | | | | |
| AC13 | 事件全链路流转 | DSHB→DSHE→HERMES 全链路通 | E2E 测试 | ✅ |
| AC14 | 优先级队列路由 | 4 级队列路由正确 | 路由测试 | ✅ |
| AC15 | 重试机制正确 | 最多 5 次重试 | 重试测试 | ✅ |
| AC16 | DLQ 管理功能 | 超限事件进入 DLQ | DLQ 测试 | ✅ |
| **验证机制** | | | | |
| AC17 | 单元测试全绿 | 12/12 测试通过 | 测试报告 | ✅ |
| AC18 | 集成测试全绿 | 8/8 测试通过 | 测试报告 | ✅ |
| AC19 | 端到端测试全绿 | 8/8 测试通过 | 测试报告 | ✅ |
| **迁移计划** | | | | |
| AC20 | 迁移步骤完整 | 15/15 步骤定义完整 | 计划审查 | ✅ |
| AC21 | 回退方案完整 | 4 个回退场景有方案 | 回退方案审查 | ✅ |
| AC22 | 灰度发布计划 | 3 步灰度 (10%→50%→100%) | 灰度计划审查 | ✅ |

### 11.2 量化验收指标

| 指标编号 | 指标名称 | 目标值 | 实际值 | 达标 |
|----------|----------|:------:|:------:|:----:|
| QM01 | event_id 唯一性校验通过率 | 100% | 100% | ✅ |
| QM02 | trace_id UUID v4 格式校验通过率 | 100% | 100% | ✅ |
| QM03 | event_type 枚举值校验通过率 | 100% | 100% | ✅ |
| QM04 | priority 范围校验通过率 | 100% | 100% | ✅ |
| QM05 | retry_count 范围校验通过率 | 100% | 100% | ✅ |
| QM06 | batch_id 格式校验通过率 | 100% | 100% | ✅ |
| QM07 | 全链路追踪关联成功率 | ≥ 99.9% | 99.95% | ✅ |
| QM08 | 审计完整性校验准确率 | ≥ 99.5% | 99.8% | ✅ |
| QM09 | 重试事件识别准确率 | 100% | 100% | ✅ |
| QM10 | DLQ 事件统计自动化率 | 100% | 100% | ✅ |
| QM11 | 关键事件 (P8+) 处理延迟 | ≤ 500ms | 380ms | ✅ |
| QM12 | V86 事件向后兼容成功率 | 100% | 100% | ✅ |

### 11.3 检查清单

#### 11.3.1 Schema 定义检查清单

- [x] ✅ `trace_id` — UUID v4 格式，全局追踪层字段
- [x] ✅ `event_type` — 25 个枚举值，全大写命名
- [x] ✅ `priority` — 整数 1-10，10 为最高优先级
- [x] ✅ `batch_id` — `{source}_{timestamp}_{seq}` 格式
- [x] ✅ `retry_count` — 整数 0-5，超过 5 进入 DLQ
- [x] ✅ 完整 20 字段 Schema 定义
- [x] ✅ 字段必填性矩阵
- [x] ✅ 字段示例值
- [x] ✅ 字段类型定义

#### 11.3.2 完整性规则检查清单

- [x] ✅ INTEGRITY-01: event_id 唯一性校验
- [x] ✅ INTEGRITY-02: trace_id UUID v4 格式校验
- [x] ✅ INTEGRITY-03: event_timestamp ISO 8601 格式与合理性校验
- [x] ✅ INTEGRITY-04: event_type 枚举值校验
- [x] ✅ INTEGRITY-05: batch_id 结构化格式校验
- [x] ✅ INTEGRITY-06: priority 取值范围校验
- [x] ✅ INTEGRITY-07: retry_count 取值范围校验
- [x] ✅ INTEGRITY-08: event_payload 非空与 JSON 有效性校验
- [x] ✅ INTEGRITY-09: 条件必填字段完整性校验
- [x] ✅ INTEGRITY-10: 三方命名映射一致性校验
- [x] ✅ INTEGRITY-11: Schema 版本兼容性校验
- [x] ✅ INTEGRITY-12: SHA-256 校验和完整性校验

#### 11.3.3 命名对齐检查清单

- [x] ✅ DSHB → DSHE 字段映射表
- [x] ✅ DSHE → HERMES 字段映射表
- [x] ✅ 命名适配层双向映射
- [x] ✅ 未知字段透传机制
- [x] ✅ 字段缺失默认值填充

#### 11.3.4 验证检查清单

- [x] ✅ 单元测试 (12/12 通过)
- [x] ✅ 集成测试 (8/8 通过)
- [x] ✅ 端到端测试 (8/8 通过)
- [x] ✅ 三方会签完成

#### 11.3.5 迁移检查清单

- [x] ✅ 迁移步骤 15 步全部定义
- [x] ✅ 回退方案 4 个场景
- [x] ✅ 灰度发布 3 步计划
- [x] ✅ 数据兼容性保障措施

### 11.4 剩余风险

| 风险编号 | 风险描述 | 影响 | 缓解措施 | 残余风险等级 |
|----------|----------|------|----------|:------------:|
| RR01 | 三方系统时钟不同步可能导致 event_timestamp 异常 | 中 | 使用 NTP 同步，允许 ±5 分钟偏差 | 🟡 可接受 |
| RR02 | UUID v4 极端情况下的碰撞风险 | 低 | 使用加密安全的随机数生成器 | 🟢 可忽略 |
| RR03 | 灰度期间 V86/V87 双写的数据一致性风险 | 中 | 双写对比验证，不一致时以 V87 为准 | 🟡 可接受 |

---

## 12. 签署与审批

### 12.1 签署信息

| 角色 | 姓名 | 部门 | 职位 | 签署日期 | 签署状态 |
|------|------|------|------|:--------:|:--------:|
| 编制人 | 王华 | DSHB 架构设计组 | 架构师 | 2027-03-19 | ✅ 已签署 |
| DSHE 审核 | 刘芳 | DSHE 监控团队 | 团队负责人 | 2027-03-19 | ✅ 已签署 |
| HERMES 审核 | 赵磊 | HERMES 审计团队 | 团队负责人 | 2027-03-19 | ✅ 已签署 |
| 技术审批 | 陈涛 | 技术管理委员会 | 技术副总裁 | 待签署 | 🟡 待签署 |

### 12.2 签署声明

> 本人确认已详细审阅本规范文档的全部 12 个章节，确认以下内容:
>
> 1. ✅ **Schema 完整性**: 20 个字段定义完整，5 个新增字段规格清晰
> 2. ✅ **完整性规则**: INTEGRITY-01~12 共 12 条规则定义完整且可执行
> 3. ✅ **命名对齐**: 三方系统命名映射表完整，适配层设计合理
> 4. ✅ **版本管理**: V86→V87 向后兼容策略完善
> 5. ✅ **管道流转**: 事件全链路流转架构清晰，SLA 定义合理
> 6. ✅ **验证机制**: 三阶段验证全部通过
> 7. ✅ **迁移计划**: 迁移步骤完整，回退方案可靠
> 8. ✅ **验收标准**: 22 项验收标准全部达标
>
> 本签署代表本人同意按本规范执行 V87 RC1 G1 Phase02 事件 Schema 适配工作。

### 12.3 签署栏

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  编制人签署:                                                     │
│  ─────────────────────────────                                  │
│  王华  (DSHB 架构设计组 — 架构师)                                │
│  日期: 2027-03-19                                               │
│                                                                 │
│  ─────────────────────────────                                  │
│                                                                 │
│                                                                 │
│  DSHE 审核签署:                                                  │
│  ─────────────────────────────                                  │
│  刘芳  (DSHE 监控团队 — 团队负责人)                              │
│  日期: 2027-03-19                                               │
│  日期: _____________                                           │
│                                                                 │
│  ─────────────────────────────                                  │
│                                                                 │
│                                                                 │
│  HERMES 审核签署:                                               │
│  ─────────────────────────────                                  │
│  赵磊  (HERMES 审计团队 — 团队负责人)                            │
│  日期: 2027-03-19                                               │
│                                                                 │
│  ─────────────────────────────                                  │
│                                                                 │
│                                                                 │
│  技术审批签署:                                                   │
│  ─────────────────────────────                                  │
│  陈涛  (技术管理委员会 — 技术副总裁)                              │
│  日期: _____________                                           │
│                                                                 │
│  ─────────────────────────────                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 12.4 附录

#### 附录 A: 文档缩略语

| 缩略语 | 全称 | 中文 |
|--------|------|------|
| DSHB | Data Storage Hub Benchmark | 数据存储中心基准 |
| DSHE | Data Storage Hub Engine | 数据存储中心引擎 |
| HERMES | High Efficiency Real-time Monitoring & Event System | 高效实时监控与事件系统 |
| UUID | Universally Unique Identifier | 通用唯一标识符 |
| DLQ | Dead Letter Queue | 死信队列 |
| SLA | Service Level Agreement | 服务等级协议 |
| MTTR | Mean Time To Repair | 平均修复时间 |
| E2E | End-to-End | 端到端 |
| UAT | User Acceptance Test | 用户验收测试 |
| TDD | Test-Driven Development | 测试驱动开发 |
| NTP | Network Time Protocol | 网络时间协议 |

#### 附录 B: 参考文档

| 文档编号 | 文档名称 | 版本 | 说明 |
|----------|----------|:----:|------|
| DSHB-ES-V86 | DSHB 事件 Schema 基线文档 | V86 | 前序 Schema 定义 |
| DSHB-VR-V87-RC1-G1-P02 | Phase02 风险登记册 | v1.0 | 风险管理报告 |
| HERMES-AUD-2027-003 | HERMES 审计报告 | 2027-02 | 审计需求来源 |
| DSHE-MON-2027-001 | DSHE 监控需求 | 2027-02 | 监控需求来源 |
| ISO 8601 | 日期和时间格式标准 | — | event_timestamp 格式参考 |
| RFC 4122 | UUID 标准 | — | trace_id/event_id 格式参考 |
| DSHB 事件架构规范 V2.4 | — | V2.4 | 事件架构总体规范 |
| DSHE 可观测性标准 V1.8 | — | V1.8 | 可观测性标准 |
| HERMES 审计规范 V3.1 | — | V3.1 | 审计规范 |

#### 附录 C: 变更记录汇总

| 日期 | 版本 | 变更人 | 变更内容 | 影响范围 |
|------|:----:|--------|----------|----------|
| 2027-03-06 | v0.1 | 王华 | 创建文档，完成背景与需求分析 | — |
| 2027-03-09 | v0.2 | 王华 | 完成完整 Schema 定义与 5 个新字段规格 | 第 3-4 章 |
| 2027-03-12 | v0.3 | 王华 | 完成命名对齐矩阵与完整性规则 | 第 5-6 章 |
| 2027-03-15 | v0.4 | 王华 | 完成版本管理策略与事件管道架构 | 第 7-8 章 |
| 2027-03-17 | v0.5 | 王华 | 完成三方验证、迁移计划、验收标准 | 第 9-11 章 |
| 2027-03-19 | v1.0 | 王华 | 定稿，提交三方会签 | 全部 |

---

**文档结束**

> 📄 本文档版本: v1.0 | 状态: 🟡 待技术审批签署 | 编制: DSHB 架构设计组 (ADG)
>
> 如有疑问，请联系编制人 王华 (wang.hua@dshb.internal)
