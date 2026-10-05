# DSHB V86-RC2 DEP-001 服务联调前置准备检查清单

> **文档类型**: 联调前置检查清单 (Integration Pre-condition Checklist)
> **文档版本**: V1.0
> **生成时间**: 2026-10-16
> **关联工单**: DSHB_V86_RC2_RDEP07_GATE_PROD_PREP / T3.3
> **关联阻塞项**: R-DEP-07 (DEP-001 短ID解析服务 HTTP 500 — P0阻断)
> **关联脚本**: `gate_pre_check_auto_v4.py` (当前V4), `gate_pre_check_auto_v5.py` (开发中 --env=prod/sandbox)
> **分支**: `dshb_gate_prod_fix` (BRANCH_LOCKED=TRUE)
> **约束**: NO_OVERWRITE=TRUE / NO_MODIFY_V85=TRUE / BRANCH_LOCKED=TRUE
> **跨团队协调**: DSHB (Gate) + DSHE (Alert Routing) + HERMES (Audit)

---

## 目录

1. [概述](#1-概述)
2. [DEP-001服务现状](#2-dep-001服务现状)
3. [网络白名单清单](#3-网络白名单清单)
4. [账号权限申请](#4-账号权限申请)
5. [证书与TLS配置](#5-证书与tls配置)
6. [端口与超时参数规范](#6-端口与超时参数规范)
7. [服务发现集成](#7-服务发现集成)
8. [生产审计日志独立落盘路径](#8-生产审计日志独立落盘路径)
9. [联调测试用例](#9-联调测试用例)
10. [健康探测接口规范](#10-健康探测接口规范)
11. [日志采集配置](#11-日志采集配置)
12. [联调前置条件检查清单](#12-联调前置条件检查清单)
13. [三方联调用例对齐](#13-三方联调用例对齐)
14. [风险与缓解措施](#14-风险与缓解措施)
15. [下一步行动](#15-下一步行动)
16. [附录A: 依赖链参考路径](#16-附录a-依赖链参考路径)
17. [附录B: 跨团队接口契约](#17-附录b-跨团队接口契约)
18. [附录C: 变更记录](#18-附录c-变更记录)

---

## 1. 概述

### 1.1 文档目的

本文档为 **DEP-001 短ID解析服务** 联调前置准备检查清单，用于系统化地确认 DEP-001 服务从 HTTP 500 故障状态恢复至生产可用状态的全部前置条件。

DEP-001 是当前 DSHB V86-RC2 生产发布（Production Launch）的 **唯一 P0 阻塞项**。在 DEP-001 服务恢复正常前，Gate 预检查始终返回 `NOT_READY`，data_fetchable_rate=0%，178 项指标全部无法获取真实数据。

### 1.2 工单引用

| 字段 | 值 |
|------|-----|
| **工单编号** | DSHB_V86_RC2_RDEP07_GATE_PROD_PREP / T3.3 |
| **阻塞项编号** | R-DEP-07 |
| **阻塞级别** | P0 (生产发布阻断) |
| **阻塞描述** | DEP-001 短ID解析服务返回 HTTP 500，全部178项指标取数率为0% |
| **关联DEP** | DEP-001 (zhiji 数据平台短ID前缀解析能力) |
| **关联台账** | `dshb_dep_registry_dep-reg-001.json` (DEP-REG-001) |
| **当前状态** | 🔴 BLOCKED — HTTP 500, Gate=NOT_READY |
| **目标状态** | 🟢 READY — HTTP 200, data_fetchable_rate≥80%, Gate=READY |

### 1.3 文档范围

本检查清单覆盖以下联调前置领域：

| 领域 | 范围 | 覆盖章节 |
|------|------|----------|
| **网络层** | 防火墙规则、DNS白名单、服务发现端点访问、内网路由、ACL、API网关路由 | §3 |
| **权限层** | 服务账号创建、API Token生成、服务间通信凭据、读写权限分级、Token轮换策略 | §4 |
| **安全层** | mTLS证书交换、CA配置、证书过期监控、TLS版本要求、加密套件白名单 | §5 |
| **协议层** | 端口参数、超时配置、重试策略、熔断器参数、DNS解析超时 | §6 |
| **发现层** | 服务注册、健康检查端点、发现协议、负载均衡、版本钉定 | §7 |
| **审计层** | 生产日志落盘路径、轮转策略、日志级别、JSON格式、保留策略、中心聚合 | §8 |
| **测试层** | 联调测试用例定义（8个核心用例） | §9 |
| **探测层** | 健康探测接口规范、响应格式、SLO、状态码 | §10 |
| **采集层** | 日志格式、采集Agent、采集间隔、级别、关键指标 | §11 |
| **前置层** | 联调前置条件检查清单（11项） | §12 |
| **对齐层** | 三方（DSHB/DSHE/HERMES）联调用例对齐 | §13 |
| **风险层** | 风险识别与缓解措施 | §14 |
| **行动层** | 分阶段下一步行动计划 | §15 |

### 1.4 跨团队协调

| 团队 | 职责 | 接口人 | 联调内容 |
|------|------|--------|----------|
| **DSHB** (Gate) | Gate预检查脚本 V4/V5、DEP-001探测逻辑、熔断机制 | DSHB Tech Lead | L1证据包构建、Gate预检查执行、data_fetchable_rate计算 |
| **DSHE** (Alert Routing) | 告警路由规则、告警分发策略、CRITICAL/MEDIUM告警 | DSHE Ops Lead | DEP-001状态变更告警、Gate NOT_READY告警、恢复通知 |
| **HERMES** (Audit) | 证据审计、审计日志归档、审计事件追踪 | HERMES Audit Lead | L1证据包审计、审计器ERROR处理、REG-06阻断验证 |

### 1.5 相关文档索引

| 文档 | 路径 | 用途 |
|------|------|------|
| DEP-001 主台账 | `dshb_dep_registry_dep-reg-001.json` | DEP-001全生命周期状态记录 |
| 外部依赖阻塞台账 | `v86_rc2_dshb_external_dependency_block_list.md` | 短ID解析能力缺失详情 |
| Gate V4 审计集成报告 | `v86_rc2_dshb_gate_audit_v2plus_integrate.md` | REG-06修复 + 紧急旁路 |
| 三方链E2E报告 | `v86_rc2_dshb_tripartite_dryrun_e2e_report.md` | L1→Gate→HERMES→DSHE全链路 |
| 数据平台工单记录 | `v86_rc2_dshb_data_platform_ticket_record.md` | DEP-01工单详情与AC验收标准 |
| 熔断演练报告 | `v86_rc2_dshb_dep_fuse_dryrun_report.md` | DEP-001 HTTP 500熔断机制验证 |
| DEP GAP同步日志 | `v86_rc2_dshb_dep_gap_sync_log.md` | 6项DEP SOP GAP识别与闭环 |

---

## 2. DEP-001服务现状

### 2.1 服务描述

DEP-001 是 **zhiji 数据平台的短ID前缀解析能力**，核心功能是提供 short_id → long_id 的映射解析服务。

| 字段 | 值 |
|------|-----|
| **DEP ID** | DEP-001 |
| **服务名称** | zhiji 数据平台短ID前缀解析能力 |
| **服务类型** | REST API (search/series) |
| **服务Owner** | zhiji 数据平台 (commodity_api) |
| **风险级别** | P0 |
| **接口端点** | `GET /commodity/api/series?id={short_id}` |
| **预期行为** | 输入 short_id → 服务端解析 → 返回对应数据系列 (HTTP 200) |
| **当前行为** | 所有 short_id 查询返回 HTTP 500 (`无法识别指标来源(id前缀)`) |
| **影响范围** | 8品种178项指标全量取数 |
| **当前状态** | 🔴 BLOCKED — HTTP 500 |

### 2.2 当前故障详情

**错误响应示例**:

```
HTTP 500: 无法识别指标来源(id前缀): j25_tc
```

| short_id | 指标名称 | 预期行为 | 当前行为 | HTTP状态 |
|----------|----------|----------|----------|----------|
| `j25_tc` | 沪铅期货收盘价 | HTTP 200 + 数据 | HTTP 500 无法识别 | 500 |
| `j26_tc` | 沪锌期货收盘价 | HTTP 200 + 数据 | HTTP 500 无法识别 | 500 |
| `j27_tc` | 沪铜期货收盘价 | HTTP 200 + 数据 | HTTP 500 无法识别 | 500 |
| `j28_tc` | 沪铝期货收盘价 | HTTP 200 + 数据 | HTTP 500 无法识别 | 500 |
| `i01` | 沪铜库存 | HTTP 200 + 数据 | permission_state=-4 | -4 |
| `i02` | 沪铝库存 | HTTP 200 + 数据 | permission_state=-4 | -4 |
| `s_001` | 新增条目代表 | HTTP 200 + 数据 | HTTP 500 无法识别 | 500 |
| `lme_cu_tc` | LME铜收盘价 | HTTP 200 + 数据 | HTTP 500 无法识别 | 500 |

### 2.3 影响分析

| 影响维度 | 数值 | 说明 |
|----------|------|------|
| 受影响指标总数 | **178** | 8品种全部指标 |
| 真实可取数率 | **0%** | data_fetchable_rate = 0/178 |
| 元数据完整率 | **73.6%** | 131/178项有元数据（无API取数能力） |
| Gate判定 | **NOT_READY** | data_fetchable_rate=0% < 80%阈值 |
| 熔断状态 | **TRIPPED** | 全部DEP-001探测ID被标记BLOCKED |
| 告警级别 | **CRITICAL** | P0阻断，需立即处理 |
| 阻塞时间 | **> 45天** | 自2026-06-29首次检测到当前 |

### 2.4 依赖链分析

DEP-001 是整条数据获取链路的 **L1 层入口**。依赖链断裂在第一个节点即导致全链路不可用：

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEP-001 依赖链完整视图                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │ L1   │───▶│  DEP-001  │───▶│ short_id │───▶│ long_id  │      │
│  │Probe │    │ REST API  │    │ (输入)   │    │ (解析结果) │      │
│  └──────┘    └──────────┘    └──────────┘    └──────────┘      │
│       │             │                                 │          │
│       │             ▼                                 ▼          │
│       │      ┌──────────┐                     ┌──────────┐      │
│       │      │ HTTP 500  │                     │ 数据系列  │      │
│       │      │ 🔴 BLOCKED│                     │ (取数)    │      │
│       │      └──────────┘                     └──────────┘      │
│       │                                  │                       │
│       ▼                                  ▼                       │
│  ┌──────────┐                     ┌──────────┐                  │
│  │3/3 BLOCKED│                     │ 178项指标 │                  │
│  │data_rate=0%│                    │ 真实取数  │                  │
│  └──────────┘                     └──────────┘                  │
│       │                                              │          │
│       ▼                                              ▼          │
│  ┌──────────┐                     ┌──────────┐                  │
│  │Gate NOT_ │                     │  Gate    │                  │
│  │  READY   │                     │  READY   │                  │
│  │🔴 阻断   │                     │🟢 放行   │                  │
│  └──────────┘                     └──────────┘                  │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│  当前状态: 🔴 链路在L1→DEP-001处断裂                              │
│  目标状态: 🟢 链路全通, data_fetchable_rate≥80%                   │
└─────────────────────────────────────────────────────────────────┘
```

**链路节点详解**:

| 层级 | 节点 | 职责 | 当前状态 | 依赖关系 |
|------|------|------|----------|----------|
| L0 | L1 Probe (探测) | 发送3个探测短ID请求 (j25_tc, i1, i3) | 🔴 3/3 BLOCKED | → DEP-001 |
| L1 | DEP-001 REST API | 解析 short_id → long_id | 🔴 HTTP 500 | ← L1 Probe |
| L2 | short_id 输入 | 用户/API传入的短ID | 🟢 正常格式 | → DEP-001 |
| L3 | long_id 解析结果 | DEP-001返回的完整数据系列ID | 🔴 无返回 | ← DEP-001 |
| L4 | 数据取数 | 使用 long_id 调用 series API 获取数据 | 🔴 无long_id输入 | ← long_id |
| L5 | data_fetchable_rate | 可取数指标数/总指标数 | 🔴 0% | ← 数据取数 |
| L6 | Gate 判定 | data_fetchable_rate ≥ 80% → READY | 🔴 NOT_READY | ← data_rate |

### 2.5 恢复后预期状态

| 指标 | 当前值 | 目标值 | 达成条件 |
|------|--------|--------|----------|
| HTTP状态码 | 500 | 200 | 服务端解析逻辑上线 |
| 真实可取数率 | 0% | ≥80% | ≥143/178项指标可取数 |
| Gate判定 | NOT_READY | READY | data_fetchable_rate≥80% |
| 熔断状态 | TRIPPED | CLOSED | 连续3次探测通过 |
| 告警级别 | CRITICAL | INFO | 状态恢复正常 |

---

## 3. 网络白名单清单

### 3.1 网络访问矩阵总览

DEP-001 服务在生产环境运行需要确保以下网络路径的连通性：

```
DSHB服务器 ───[内网VLAN]───▶ API网关 ───[mTLS]───▶ DEP-001服务集群
   │                                              │
   │    ┌─────────────────────────────────────────┘
   │    │
   ▼    ▼
DSHE告警系统 ◀───[内网VLAN]─── DEP-001服务集群
HERMES审计 ──[内网VLAN]─── DEP-001服务集群
```

### 3.2 防火墙规则清单

| 项目 | 描述 | Owner | 状态 | 截止日期 |
|------|------|-------|------|----------|
| **FW-01** | 入站: DSHB Gate服务器 → DEP-001 API端口 | 网络运维 | 🔴 待配置 | T+3 |
| **FW-02** | 入站: DSHE 告警服务器 → DEP-001 健康端点 | 网络运维 | 🔴 待配置 | T+3 |
| **FW-03** | 入站: HERMES 审计服务器 → DEP-001 审计日志端点 | 网络运维 | 🔴 待配置 | T+3 |
| **FW-04** | 出站: DEP-001 → 数据源数据库端口 | 网络运维 | 🟡 已有规则需验证 | T+1 |
| **FW-05** | 出站: DEP-001 → 日志中心 (ELK) | 网络运维 | 🔴 待配置 | T+3 |
| **FW-06** | 双向: DEP-001 ↔ Redis缓存集群 | 网络运维 | 🟡 已有规则需验证 | T+1 |
| **FW-07** | 出站: DEP-001 → 监控告警系统 (Prometheus) | 网络运维 | 🔴 待配置 | T+3 |
| **FW-08** | 双向: DEP-001 ↔ Consul/Etcd 服务发现 | 网络运维 | 🔴 待配置 | T+2 |

### 3.3 DNS解析白名单

| 项目 | 描述 | Owner | 状态 | 截止日期 |
|------|------|-------|------|----------|
| **DNS-01** | `dep001-api.internal` → 服务集群 VIP/IP | DNS运维 | 🔴 待解析 | T+1 |
| **DNS-02** | `dep001-health.internal` → 健康检查端点 | DNS运维 | 🔴 待解析 | T+1 |
| **DNS-03** | `dep001-audit.internal` → 审计日志端点 | DNS运维 | 🔴 待解析 | T+1 |
| **DNS-04** | SRV记录: `_dep001._tcp.internal` → 服务发现 | DNS运维 | 🔴 待配置 | T+2 |
| **DNS-05** | 反向DNS: `PTR(dep001-01.internal)` → `dep001-01` | DNS运维 | 🟡 待确认 | T+1 |
| **DNS-06** | 通配符证书DNS: `*.dep001.internal` | DNS运维 | 🔴 待配置 | T+2 |

### 3.4 服务发现端点访问

| 项目 | 描述 | Owner | 状态 | 截止日期 |
|------|------|-------|------|----------|
| **SD-01** | Consul服务目录 API 访问 (`/v1/catalog/services`) | 中间件运维 | 🔴 待开通 | T+2 |
| **SD-02** | DEP-001 服务注册 (`/v1/agent/service/register`) | 中间件运维 | 🔴 待注册 | T+2 |
| **SD-03** | 健康检查回调 (`/v1/agent/check/update`) | 中间件运维 | 🔴 待配置 | T+2 |
| **SD-04** | 服务状态查询 (`/v1/health/service/dep001`) | 中间件运维 | 🔴 待配置 | T+2 |
| **SD-05** | 事件通知 (`/v1/event/fire`) | 中间件运维 | 🔴 待配置 | T+2 |

### 3.5 内网路由规则

| 项目 | 描述 | Owner | 状态 | 截止日期 |
|------|------|-------|------|----------|
| **RT-01** | DSHB-VLAN → DEP001-VLAN 路由 | 网络运维 | 🔴 待配置 | T+3 |
| **RT-02** | DEP001-VLAN → DB-VLAN 路由 | 网络运维 | 🟡 已有规则需验证 | T+1 |
| **RT-03** | DEP001-VLAN → LOG-VLAN 路由 | 网络运维 | 🔴 待配置 | T+3 |
| **RT-04** | DEP001-VLAN → MON-VLAN 路由 | 网络运维 | 🔴 待配置 | T+3 |
| **RT-05** | DSHE-VLAN → DEP001-VLAN 路由 | 网络运维 | 🔴 待配置 | T+3 |

### 3.6 生产子网ACL

| 项目 | 描述 | Owner | 状态 | 截止日期 |
|------|------|-------|------|----------|
| **ACL-01** | DEP-001 子网段: `10.86.32.0/24` | 安全运维 | 🔴 待创建 | T+2 |
| **ACL-02** | 访问控制: 仅允许 DSHB/DSHE/HERMES 子网访问 | 安全运维 | 🔴 待配置 | T+3 |
| **ACL-03** | 入站过滤: 仅允许 443/8080 端口 | 安全运维 | 🔴 待配置 | T+3 |
| **ACL-04** | 出站过滤: 仅允许 DB端口/日志端口/监控端口 | 安全运维 | 🔴 待配置 | T+3 |
| **ACL-05** | 速率限制: DEP-001 API 调用频率上限 | 安全运维 | 🔴 待配置 | T+3 |

### 3.7 API网关路由规则

| 项目 | 描述 | Owner | 状态 | 截止日期 |
|------|------|-------|------|----------|
| **GW-01** | 路由规则: `/commodity/api/series` → DEP-001 upstream | API网关运维 | 🔴 待配置 | T+2 |
| **GW-02** | 超时配置: connect_timeout=30s, read_timeout=15s | API网关运维 | 🔴 待配置 | T+2 |
| **GW-03** | 重试策略: max_retries=3, backoff_factor=2 | API网关运维 | 🔴 待配置 | T+2 |
| **GW-04** | mTLS验证: 客户端证书强制校验 | API网关运维 | 🔴 待配置 | T+2 |
| **GW-05** | 限流: rate_limit=1000 req/min per client | API网关运维 | 🔴 待配置 | T+3 |
| **GW-06** | 路由: `/commodity/api/health` → DEP-001 health upstream | API网关运维 | 🔴 待配置 | T+2 |
| **GW-07** | CORS配置: 生产环境禁用跨域 (如需则白名单) | API网关运维 | 🔴 待配置 | T+3 |
| **GW-08** | 请求日志: 记录每条API请求的trace_id/status/latency | API网关运维 | 🔴 待配置 | T+2 |

---

## 4. 账号权限申请

### 4.1 服务账号与权限矩阵

| 权限项 | 描述 | 系统 | 状态 | 审批人 |
|--------|------|------|------|--------|
| **AUTH-01** | DEP-001 服务账号创建 (`svc-dep001-prod`) | 数据平台 IAM | 🔴 待申请 | 数据平台负责人 |
| **AUTH-02** | DSHB Gate 服务账号 (`svc-dshb-gate`) | 数据平台 IAM | 🟡 已有,需验证权限范围 | DSHB Tech Lead |
| **AUTH-03** | DSHE 告警系统账号 (`svc-dshe-alert`) | 数据平台 IAM | 🔴 待申请 | DSHE Ops Lead |
| **AUTH-04** | HERMES 审计系统账号 (`svc-hermes-audit`) | 数据平台 IAM | 🔴 待申请 | HERMES Audit Lead |
| **AUTH-05** | API Token: DSHB → DEP-001 (只读查询) | 数据平台 IAM | 🔴 待生成 | 数据平台负责人 |
| **AUTH-06** | API Token: DSHE → DEP-001 (健康探测) | 数据平台 IAM | 🔴 待生成 | DSHE Ops Lead |
| **AUTH-07** | API Token: HERMES → DEP-001 (审计日志读取) | 数据平台 IAM | 🔴 待生成 | HERMES Audit Lead |
| **AUTH-08** | 服务间通信: DEP-001 ↔ DSHB (mTLS + Token双因子) | API网关 | 🔴 待配置 | 安全运维 |
| **AUTH-09** | 服务间通信: DEP-001 ↔ DSHE (mTLS + Token双因子) | API网关 | 🔴 待配置 | 安全运维 |
| **AUTH-10** | 服务间通信: DEP-001 ↔ HERMES (mTLS + Token双因子) | API网关 | 🔴 待配置 | 安全运维 |

### 4.2 权限范围分级

| 权限范围 | 服务 | 权限级别 | 允许操作 | 禁止操作 |
|----------|------|----------|----------|----------|
| **只读-查询** | DSHB → DEP-001 | READ | `GET /series`, `GET /health`, `GET /ready` | 写操作, 管理操作 |
| **只读-健康** | DSHE → DEP-001 | READ_HEALTH | `GET /health`, `GET /ready`, `GET /live` | 数据查询, 写操作 |
| **只读-审计** | HERMES → DEP-001 | READ_AUDIT | `GET /audit/events`, `GET /audit/log` | 数据查询, 写操作 |
| **读写-管理** | 数据平台运维 | ADMIN | 全部操作 | — |

### 4.3 API Token 策略

| 项目 | 配置值 | 说明 |
|------|--------|------|
| Token格式 | JWT (JSON Web Token) | 标准JWT, RS256签名 |
| Token有效期 | 24小时 | 每日自动刷新 |
| Token刷新提前量 | 2小时前 | 自动刷新机制 |
| 最大并发Token数 | 每服务2个 (active + backup) | 支持无缝轮换 |
| Token签名密钥 | RS256 (2048-bit RSA) | 密钥由CA签发 |
| Token载荷 | `{sub, aud, exp, iat, scope, tid}` | tid=token_id用于审计追踪 |
| Token吊销 | 支持即时吊销 | 通过 `/token/revoke` 端点 |
| Token轮换告警 | Token过期前2小时告警 | DSHE路由至相关运维 |

### 4.4 Token轮换与过期策略

```
┌─────────────────────────────────────────────────────────┐
│                   Token 轮换生命周期                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  T0 (创建) ──┐                                          │
│  Token Active │                                          │
│       │        │   T0+22h (告警)                          │
│       │        ├──┐  ⚠️ Token将在2h后过期                  │
│  T0+23h       │  │  自动刷新                              │
│  Token Refresh │  │                                          │
│       │        │  │                                          │
│       ▼        ▼  ▼                                          │
│  T0+24h (过期) │  新Token创建                                │
│  ┌──────────┐ │  旧Token继续有效24h (Grace Period)          │
│  │旧Token   │ │  新Token立即生效                             │
│  │宽限期    │ │                                               │
│  └──────────┘ │                                               │
│       │        │                                               │
│  T0+48h       │                                               │
│  旧Token完全吊销                                              │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│  安全约束:                                                │
│  • 同一sub不允许同时有3个以上active Token                   │
│  • Token轮换失败自动重试, 最大3次                          │
│  • 连续轮换失败触发CRITICAL告警                            │
└─────────────────────────────────────────────────────────┘
```

### 4.5 审计日志权限

| 项目 | 配置值 | 说明 |
|------|--------|------|
| 审计日志读取权限 | HERMES + DSHB Ops | 仅审计团队和DSHB运维可读取 |
| 审计日志写入权限 | DEP-001 服务自身 | 服务写入审计日志到独立路径 |
| 审计日志删除权限 | 仅系统管理员 (需审批) | 保留90天后自动清理 |
| 审计事件追踪 | 全量追踪 | 所有API调用记录 trace_id |
| 审计日志加密 | AES-256-GCM | 传输中和存储时均加密 |

---

## 5. 证书与TLS配置

### 5.1 mTLS证书交换矩阵

```
┌─────────────────────────────────────────────────────────┐
│                   mTLS 证书拓扑                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐  client-cert  ┌──────────┐                │
│  │  DSHB    │ ─────────────▶ │  DEP-001  │                │
│  │  Gate    │ ◀───────────── │  Server   │                │
│  └──────────┘  server-cert  └──────────┘                │
│                                                         │
│  ┌──────────┐  client-cert  ┌──────────┐                │
│  │  DSHE    │ ─────────────▶ │  DEP-001  │                │
│  │  Alert   │ ◀───────────── │  Server   │                │
│  └──────────┘  server-cert  └──────────┘                │
│                                                         │
│  ┌──────────┐  client-cert  ┌──────────┐                │
│  │ HERMES   │ ─────────────▶ │  DEP-001  │                │
│  │  Audit   │ ◀───────────── │  Server   │                │
│  └──────────┘  server-cert  └──────────┘                │
│                                                         │
│  ┌──────────┐                                          │
│  │  CA (根)  │  签发所有证书                              │
│  └──────────┘                                          │
└─────────────────────────────────────────────────────────┘
```

### 5.2 证书清单

| 证书项 | 描述 | Owner | 状态 | 截止日期 |
|--------|------|-------|------|----------|
| **CERT-01** | DEP-001 服务端证书 (`dep001-api.internal`) | CA运维 | 🔴 待签发 | T+2 |
| **CERT-02** | DSHB Gate 客户端证书 (`svc-dshb-gate`) | CA运维 | 🔴 待签发 | T+2 |
| **CERT-03** | DSHE 客户端证书 (`svc-dshe-alert`) | CA运维 | 🔴 待签发 | T+2 |
| **CERT-04** | HERMES 客户端证书 (`svc-hermes-audit`) | CA运维 | 🔴 待签发 | T+2 |
| **CERT-05** | 通配符证书 (`*.dep001.internal`) | CA运维 | 🔴 待签发 | T+2 |
| **CERT-06** | 中间CA证书 (如有) | CA运维 | 🟡 已有 | — |
| **CERT-07** | 根CA证书 | CA运维 | 🟢 已有 | — |

### 5.3 证书配置参数

| 参数 | 配置值 | 说明 |
|------|--------|------|
| 证书有效期 | 365天 | 自动续期 |
| 续期提前量 | 30天前自动续期 | ACME协议 |
| 续期失败告警 | 提前15天告警 | DSHE路由 |
| 证书格式 | PEM (X.509 v3) | 标准格式 |
| 密钥类型 | RSA 2048-bit / ECDSA P-256 | 二选一, 优先ECDSA |
| 主题(CN) | `dep001-api.internal` | 服务端 |
| 主题备用名(SAN) | `dep001-01.internal`, `dep001-02.internal` | 所有实例 |
| 密钥保护 | AES-256-GCM加密存储 | 密钥管理系统(KMS) |

### 5.4 TLS版本要求

| TLS版本 | 生产环境 | 沙箱环境 | 说明 |
|---------|----------|----------|------|
| TLS 1.2 | ✅ 必须支持 | ✅ 必须支持 | 最低版本要求 |
| TLS 1.3 | ✅ 优先使用 | ✅ 优先使用 | 推荐版本 |
| TLS 1.1 | ❌ 禁用 | ❌ 禁用 | 不安全, 已禁用 |
| TLS 1.0 | ❌ 禁用 | ❌ 禁用 | 不安全, 已禁用 |
| SSL 3.0 | ❌ 禁用 | ❌ 禁用 | 不安全, 已禁用 |

### 5.5 加密套件白名单

**优先使用 (TLS 1.3)**:

```
TLS_AES_256_GCM_SHA384
TLS_CHACHA20_POLY1305_SHA256
TLS_AES_128_GCM_SHA256
```

**兼容使用 (TLS 1.2)**:

```
TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256
TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
```

**明确禁用**:

```
所有 RC4 套件
所有 CBC 模式套件
所有 DES/3DES 套件
所有 EXPORT 套件
TLS_RSA_* (静态RSA密钥交换)
```

### 5.6 证书过期监控

| 监控项 | 阈值 | 告警级别 | 告警路由 |
|--------|------|----------|----------|
| 服务端证书剩余有效期 < 30天 | 30天 | WARNING | DSHE → 运维群 |
| 服务端证书剩余有效期 < 15天 | 15天 | CRITICAL | DSHE → 值班人员 + 电话 |
| 客户端证书剩余有效期 < 30天 | 30天 | WARNING | DSHE → 相关服务负责人 |
| 证书已过期 | 0天 | CRITICAL | DSHE → 全体 + 电话 |
| 证书自动续期失败 | 连续2次失败 | CRITICAL | DSHE → CA运维 |
| 证书吊销列表(CRL)更新检查 | 每日1次 | INFO | 内部日志 |

---

## 6. 端口与超时参数规范

### 6.1 端口映射

| 参数 | 沙箱环境默认值 | 生产环境值 | 描述 |
|------|---------------|------------|------|
| **DEP-001 服务端口** | 8080 | **443** (mTLS) | DEP-001 REST API 主服务端口 |
| **DEP-001 管理端口** | 9090 | **9090** | Prometheus metrics 暴露端口 |
| **DEP-001 健康端口** | 8080 (复用) | **443** (复用) | `/health` `/ready` `/live` 端点 |
| **API网关端口** | 8080 | **443** (mTLS) | 统一入口, 反向代理至DEP-001 |
| **数据库端口** | 5432 (PostgreSQL) | **5432** | DEP-001 短ID→long_id 映射表存储 |
| **Redis缓存端口** | 6379 | **6379** | 短ID映射结果缓存 |
| **Consul/Etcd端口** | 8500 (HTTP) | **8500** (HTTP) | 服务发现注册 |
| **日志采集Agent端口** | 9200 (Elasticsearch) | **9200** | 日志中心接收端口 |

### 6.2 超时参数规范

| 参数 | 沙箱环境默认值 | 生产环境值 | 说明 |
|------|---------------|------------|------|
| **连接超时 (connect_timeout)** | 10s | **30s** | TCP连接建立超时, 生产环境考虑跨机房延迟 |
| **读取超时 (read_timeout)** | 10s | **15s** | 服务端响应等待超时 |
| **写入超时 (write_timeout)** | 5s | **10s** | 请求体写入超时 |
| **DNS解析超时 (dns_timeout)** | 3s | **5s** | DNS查询超时, 失败后回退到缓存IP |
| **总请求超时 (total_timeout)** | 25s | **55s** | 单次请求总耗时上限 (含重试) |
| **健康探测超时 (health_probe_timeout)** | 3s | **5s** | `/health` 端点响应超时 |
| **流式传输超时 (stream_timeout)** | — | **60s** | 大响应体流式传输空闲超时 |

### 6.3 重试策略

| 参数 | 配置值 | 说明 |
|------|--------|------|
| 最大重试次数 (max_retries) | **3** | 包括首次请求后的重试次数 |
| 退避因子 (backoff_factor) | **2** | 指数退避: delay = initial_delay × 2^attempt |
| 初始延迟 (initial_delay) | **1s** | 第一次重试前的等待时间 |
| 最大延迟 (max_delay) | **30s** | 退避延迟上限 |
| 重试条件 (retry_on_status) | `[502, 503, 504]` | 仅对网关/服务端错误重试 |
| 重试条件 (retry_on_exception) | `[ConnectionError, TimeoutError]` | 连接异常和超时重试 |
| 不可重试状态 | `[400, 401, 403, 404, 422]` | 客户端错误不重试 |
| 请求幂等性 (idempotency_key) | `X-Idempotency-Key` Header | 确保重试不会产生副作用 |

**重试时间线**:

```
首次请求 ─── delay=1s ─── 第1次重试 ─── delay=2s ─── 第2次重试 ─── delay=4s ─── 第3次重试
  │                │                │                │                │
  ▼                ▼                ▼                ▼                ▼
[T=0]          [T=1s]           [T=3s]           [T=7s]           [T=11s]
                                                                      
重试总耗时: ≤ 11s (3次重试) + 连接超时(30s×3次) = 最坏 101s
实际预算: total_timeout=55s (超限即中断)
```

### 6.4 熔断器参数

| 参数 | 配置值 | 说明 |
|------|--------|------|
| 失败阈值 (failure_threshold) | **5** | 滑动窗口内连续失败次数达到此值时熔断 |
| 窗口时长 (window_seconds) | **60** | 统计窗口滑动时间 |
| 最小请求数 (min_requests) | **20** | 窗口内最小请求数, 不足则不触发熔断 |
| 半开超时 (reset_timeout) | **60** | 熔断后等待此秒数进入半开状态 |
| 半开探测请求数 (half_open_requests) | **3** | 半开状态允许通过的探测请求数 |
| 半开恢复条件 | 3/3探测成功 | 全部探测成功则关闭熔断 |
| 熔断告警 | 触发CRITICAL告警 | DSHE路由至数据平台值班 |
| 熔断恢复告警 | 触发INFO告警 | DSHE路由通知恢复 |

### 6.5 健康探测参数

| 参数 | 配置值 | 说明 |
|------|--------|------|
| 探测间隔 (interval) | **30s** | 每30秒执行一次健康探测 |
| 探测超时 (timeout) | **5s** | 单次探测超时 |
| 连续失败阈值 (unhealthy_threshold) | **3** | 连续3次失败标记为DOWN |
| 连续成功阈值 (healthy_threshold) | **3** | 连续3次成功标记为UP |
| 首次探测延迟 (initial_delay) | **10s** | 服务启动后10秒开始首次探测 |
| 探测端点 | `/health` | 存活检查 |
| 就绪端点 | `/ready` | 就绪检查 (依赖外部资源) |
| 存活端点 | `/live` | 存活检查 (仅进程检查) |

---

## 7. 服务发现集成

### 7.1 服务注册端点

| 项目 | 描述 | 配置值 | 状态 |
|------|------|--------|------|
| **REG-01** | 服务注册API | `POST /v1/agent/service/register` | 🔴 待注册 |
| **REG-02** | 服务名称 | `dep001-api` | 🔴 待配置 |
| **REG-03** | 服务ID | `dep001-api-{instance_id}` | 🔴 待配置 |
| **REG-04** | 端口 | 443 (生产), 8080 (沙箱) | 🔴 待配置 |
| **REG-05** | 标签 | `env=prod`, `team=zhiji`, `tier=core` | 🔴 待配置 |
| **REG-06** | 元数据 | `version=1.0`, `endpoint=/commodity/api/series` | 🔴 待配置 |
| **REG-07** | 权重 | `weight=100` (默认), 支持动态调整 | 🔴 待配置 |
| **REG-08** | 健康检查 | HTTP GET `/health` every 30s, timeout 5s | 🔴 待配置 |

### 7.2 健康检查端点格式

DEP-001 服务需提供以下三个健康检查端点：

| 端点 | 路径 | 用途 | 检查内容 | 超时 |
|------|------|------|----------|------|
| **Liveness** | `GET /health` | 存活检查 | 进程是否存活 | 5s |
| **Readiness** | `GET /ready` | 就绪检查 | 依赖(DB/Redis)是否就绪 | 5s |
| **Live** | `GET /live` | 轻量存活检查 | 进程是否响应 | 3s |

### 7.3 健康检查响应格式

**正常状态 (UP)**:

```json
{
  "status": "UP",
  "version": "1.0.0",
  "timestamp": "2026-10-16T10:00:00+08:00",
  "uptime_seconds": 86400,
  "checks": {
    "database": "UP",
    "redis": "UP",
    "short_id_cache": "UP"
  },
  "instance_id": "dep001-api-01",
  "build_commit": "a1b2c3d4e5f6"
}
```

**异常状态 (DOWN)**:

```json
{
  "status": "DOWN",
  "version": "1.0.0",
  "timestamp": "2026-10-16T10:00:00+08:00",
  "uptime_seconds": 86400,
  "checks": {
    "database": "DOWN",
    "redis": "UP",
    "short_id_cache": "DEGRADED"
  },
  "error": "database_connection_timeout",
  "instance_id": "dep001-api-01"
}
```

### 7.4 服务发现协议

| 协议 | 配置 | 优先级 | 说明 |
|------|------|--------|------|
| **DNS/SRV** | `_dep001._tcp.internal` | P1 (首选) | 标准DNS SRV记录, 支持负载均衡 |
| **Consul** | `dep001-api` 服务名 | P2 (备选) | 自动注册/注销, 健康检查 |
| **Kubernetes Service** | `dep001-api-svc` | P2 (备选) | 如需容器化部署 |
| **Etcd** | `/dep001/api/v1/` 前缀 | P3 (回退) | 最终回退方案 |

### 7.5 负载均衡与实例权重

| 参数 | 配置值 | 说明 |
|------|--------|------|
| 负载均衡算法 | **轮询 (Round Robin)** | 默认, 支持权重 |
| 实例数 | **3** (初始), 可弹性伸缩至 10 | 生产环境至少3实例 |
| 健康实例权重 | 100 | 正常实例 |
| 降级实例权重 | 30 | 性能下降但未宕机的实例 |
| 维护实例权重 | 0 | 维护中的实例, 不接收流量 |
| 权重更新间隔 | 10s | 负载均衡器轮询间隔 |
| 会话保持 (sticky sessions) | ❌ 不启用 | DEP-001 无状态, 无需会话保持 |

### 7.6 服务版本钉定

| 项目 | 描述 | 值 | 说明 |
|------|------|-----|------|
| 服务版本 | `v1.0` | 当前部署版本 | API兼容, 向后兼容 |
| 版本钉定策略 | 标签选择 | `dep001-api:version=v1.0` | 仅路由至v1.0实例 |
| 灰度发布 | 金丝雀发布 (Canary) | 10%流量先行 | 新版本验证后逐步扩大 |
| 版本回滚 | 自动回滚 | 错误率>5%自动回滚 | 基于熔断器决策 |
| 多版本共存 | ✅ 支持 | v1.0 + v1.1 (金丝雀) | 最多2个版本共存 |

---

## 8. 生产审计日志独立落盘路径

### 8.1 日志目录结构

```
/opt/dshb/logs/
├── audit/                                    # 审计日志 (HERMES读取)
│   ├── dep001-api/
│   │   ├── 2026-10-16/
│   │   │   ├── dep001_audit_2026-10-16_00.jsonl
│   │   │   ├── dep001_audit_2026-10-16_01.jsonl
│   │   │   └── dep001_audit_2026-10-16_23.jsonl
│   │   └── archive/                         # 归档 (90天后压缩)
│   │       ├── 2026-10-16.zip
│   │       └── 2026-09-17.zip
│   └── .audit_manifest.json                 # 审计日志清单 (校验用)
├── app/                                      # 应用日志 (DSHB运维)
│   ├── dep001-api/
│   │   ├── dep001_app_2026-10-16.log
│   │   └── dep001_error_2026-10-16.log
│   └── .app_manifest.json
├── access/                                   # 访问日志 (API请求记录)
│   ├── dep001_api_access_2026-10-16.log
│   └── .access_manifest.json
├── metrics/                                  # 指标快照 (监控)
│   ├── dep001_metrics_2026-10-16.json
│   └── .metrics_manifest.json
└── gateway/                                  # 网关日志 (路由决策)
    ├── dep001_gateway_2026-10-16.log
    └── .gateway_manifest.json
```

### 8.2 文件轮转策略

| 参数 | 审计日志 | 应用日志 | 访问日志 | 说明 |
|------|----------|----------|----------|------|
| 轮转周期 | **每日轮转** | 每日轮转 | 每日轮转 | 按日期分割文件 |
| 文件大小限制 | 单文件 ≤ **100MB** | 单文件 ≤ **50MB** | 单文件 ≤ **80MB** | 超限触发额外轮转 |
| 归档格式 | `.jsonl.gz` (Gzip压缩) | `.log.gz` | `.log.gz` | 压缩存储 |
| 归档保留 | **90天** | **30天** | **90天** | 超出自动删除 |
| 归档压缩率 | 预计 5:1 | 预计 4:1 | 预计 5:1 | JSONL格式压缩率高 |
| 轮转触发时间 | UTC+8 00:00 | UTC+8 00:00 | UTC+8 00:00 | 每日零点 |
| 轮转触发条件 | 时间 OR 大小 | 时间 OR 大小 | 时间 OR 大小 | 先到先触发 |

### 8.3 日志级别配置

| 级别 | 生产环境 | 沙箱环境 | 说明 | 示例 |
|------|----------|----------|------|------|
| **ERROR** | ✅ 启用 | ✅ 启用 | 严重错误, 影响功能 | `HTTP 500: short_id解析失败` |
| **WARN** | ✅ 启用 | ✅ 启用 | 警告, 功能降级 | `重试次数已达上限` |
| **INFO** | ✅ 启用 | ✅ 启用 | 正常操作信息 | `short_id=j25_tc 解析成功` |
| **DEBUG** | ❌ 禁用 | ✅ 启用 | 调试信息 (高IO) | `缓存未命中, 查询DB` |
| **TRACE** | ❌ 禁用 | ❌ 禁用 | 追踪信息 (极高IO) | `HTTP请求头/体详情` |

### 8.4 日志格式 (JSON结构化)

**审计日志格式** (`dep001_audit_YYYY-MM-DD_HH.jsonl`):

```json
{
  "timestamp": "2026-10-16T10:00:00.123+08:00",
  "level": "INFO",
  "service": "dep001-api",
  "message": "short_id解析请求处理完成",
  "trace_id": "trace-abc123-def456-ghi789",
  "request_id": "req-20261016-00001",
  "event_type": "SHORT_ID_RESOLVE",
  "event_action": "RESOLVE_SUCCESS",
  "actor": {
    "service": "svc-dshb-gate",
    "client_ip": "10.86.10.50",
    "user_agent": "DSHB-Gate/4.0"
  },
  "target": {
    "short_id": "j25_tc",
    "resolved_long_id": "ID02226332",
    "data_series_name": "沪铅期货收盘价"
  },
  "result": {
    "http_status": 200,
    "latency_ms": 45,
    "data_points": 2520,
    "cache_hit": true
  },
  "metadata": {
    "server_instance": "dep001-api-01",
    "api_version": "v1",
    "client_id": "dshb-gate",
    "token_id": "tok-xyz789"
  }
}
```

**应用日志格式** (`dep001_app_YYYY-MM-DD.log`):

```json
{
  "timestamp": "2026-10-16T10:00:00.123+08:00",
  "level": "INFO",
  "service": "dep001-api",
  "message": "服务启动完成, 已注册至Consul",
  "component": "startup",
  "metadata": {
    "version": "1.0.0",
    "instance_id": "dep001-api-01",
    "uptime_seconds": 0
  }
}
```

**访问日志格式** (`dep001_api_access_YYYY-MM-DD.log`):

```json
{
  "timestamp": "2026-10-16T10:00:00.123+08:00",
  "method": "GET",
  "path": "/commodity/api/series?id=j25_tc",
  "status": 200,
  "latency_ms": 45,
  "request_size": 120,
  "response_size": 15234,
  "client_ip": "10.86.10.50",
  "user_agent": "DSHB-Gate/4.0",
  "trace_id": "trace-abc123",
  "token_id": "tok-xyz789"
}
```

### 8.5 日志保留策略

| 日志类型 | 热存储 (在线) | 温存储 (归档) | 总保留 | 合规依据 |
|----------|-------------|-------------|--------|----------|
| 审计日志 | 30天 | 90天 | **90天** | 审计合规要求 |
| 应用日志 | 7天 | 30天 | **30天** | 运维排障需求 |
| 访问日志 | 30天 | 90天 | **90天** | 安全审计需求 |
| 指标快照 | 1天 | 90天 | **90天** | 趋势分析需求 |
| 网关日志 | 7天 | 30天 | **30天** | 路由审计需求 |

### 8.6 日志中心化聚合

| 项目 | 配置值 | 说明 |
|------|--------|------|
| 目标系统 | **ELK Stack** (Elasticsearch + Logstash + Kibana) | 日志中心聚合 |
| 传输协议 | HTTPS (mTLS) | 加密传输 |
| 传输方式 | Filebeat → Logstash → Elasticsearch | 标准采集管道 |
| 索引命名 | `dep001-audit-YYYY.MM.dd` | 按天分索引 |
| 生命周期策略 (ILM) | 热(7天) → 温(30天) → 冷(90天) → 删除 | 自动管理 |
| 索引刷新间隔 | 10s | 近实时查询 |
| 查询保留 | 90天可查询 | 超过90天归档至冷存储 |

---

## 9. 联调测试用例

### 9.1 测试用例矩阵

| 用例ID | 描述 | 输入 | 预期输出 | 当前状态 |
|--------|------|------|----------|----------|
| **INT-01** | 正常短ID解析 (有效short_id) | `GET /series?id=j25_tc` (有效short_id) | HTTP 200 + `{long_id: "ID02226332", data_points: 2520}` | 🔴 待执行 |
| **INT-02** | 短ID未找到 (无效short_id) | `GET /series?id=non_existent_xyz` | HTTP 404 + `{error: "short_id_not_found", message: "短ID无法解析"}` | 🔴 待执行 |
| **INT-03** | 服务500错误 (模拟服务器错误) | `GET /series?id=j25_tc` (服务端故障注入) | HTTP 500 + `{error: "internal_error", message: "内部服务错误"}` + 触发熔断 | 🔴 待执行 |
| **INT-04** | 服务超时 (无响应) | `GET /series?id=j25_tc` (服务端无响应) | 超时错误 (15s read_timeout) + 重试3次 + 熔断触发 | 🔴 待执行 |
| **INT-05** | 高并发压力 (50+并发) | 50个并发请求, 不同short_id | 全部成功 + P99延迟 < 500ms + 无错误 | 🔴 待执行 |
| **INT-06** | 服务发现故障 (无实例) | Consul/Etcd宕机 | 优雅降级: DNS回退 + 本地缓存IP + 告警 | 🔴 待执行 |
| **INT-07** | TLS证书过期 | 使用过期证书连接 | 连接失败 + mTLS验证错误 + CRITICAL告警 | 🔴 待执行 |
| **INT-08** | Token过期 | 使用过期API Token请求 | HTTP 401 + `{error: "token_expired"}` + 触发重认证流程 | 🔴 待执行 |

### 9.2 INT-01: 正常短ID解析

```
┌─────────────────────────────────────────────────────────┐
│  INT-01: 正常短ID解析测试                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  测试目的: 验证DEP-001对有效short_id的正确解析能力          │
│                                                         │
│  前置条件:                                              │
│  □ DEP-001 服务已部署且运行                              │
│  □ 网络白名单已配置                                      │
│  □ 服务账号与API Token已生成                              │
│  □ mTLS证书已交换                                       │
│                                                         │
│  测试步骤:                                              │
│  1. 发送请求: GET /commodity/api/series?id=j25_tc       │
│  2. 附带有效API Token (Authorization: Bearer <token>)    │
│  3. 使用mTLS客户端证书连接                               │
│  4. 记录响应时间                                         │
│  5. 验证响应体                                           │
│                                                         │
│  预期结果:                                              │
│  • HTTP 状态码: 200 OK                                  │
│  • 响应体包含: long_id, data_points, series_name         │
│  • 响应时间: < 100ms (P99)                              │
│  • trace_id 已记录至审计日志                              │
│                                                         │
│  验证方法:                                              │
│  1. HTTP状态码 = 200                                    │
│  2. 响应体 JSON 字段校验                                 │
│  3. 审计日志中有对应记录                                  │
│  4. HERMES 审计器验证通过                                │
│                                                         │
│  通过标准: 全部4项验证通过                                │
│  失败标准: 任一项验证失败                                 │
└─────────────────────────────────────────────────────────┘
```

**请求示例**:

```http
GET /commodity/api/series?id=j25_tc HTTP/1.1
Host: dep001-api.internal
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
X-Idempotency-Key: int-01-test-001
X-Request-Id: req-int01-20261016-001
X-Trace-Id: trace-int01-20261016-001
```

**预期响应**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "short_id": "j25_tc",
    "long_id": "ID02226332",
    "series_name": "沪铅期货收盘价",
    "data_points": 2520,
    "start_date": "2015-01-01",
    "end_date": "2026-10-15"
  },
  "trace_id": "trace-int01-20261016-001",
  "timestamp": "2026-10-16T10:00:00+08:00"
}
```

### 9.3 INT-02: 短ID未找到

| 测试维度 | 值 |
|----------|-----|
| 测试目的 | 验证DEP-001对无效short_id的优雅错误处理 |
| 输入 | `GET /series?id=non_existent_xyz` |
| 预期HTTP状态 | 404 |
| 预期响应体 | `{code: 404, error: "short_id_not_found", message: "短ID无法解析"}` |
| 通过标准 | HTTP 404 + 错误信息明确 + 审计日志记录 |
| 失败标准 | HTTP 500 或 空响应 |

**关键验证点**:

- [ ] 返回HTTP 404（非500）
- [ ] 错误信息明确说明short_id不存在
- [ ] 不返回HTTP 500（不掩盖错误）
- [ ] 审计日志记录请求和响应
- [ ] 不触发熔断器（单次404不应熔断）

### 9.4 INT-03: 服务500错误

| 测试维度 | 值 |
|----------|-----|
| 测试目的 | 验证DEP-001服务端错误时的熔断机制 |
| 输入 | `GET /series?id=j25_tc` (服务端故障注入) |
| 故障注入方式 | 数据平台注入500错误响应 |
| 预期HTTP状态 | 500 |
| 预期响应体 | `{code: 500, error: "internal_error", message: "内部服务错误"}` |
| 熔断触发条件 | 连续5次失败 → 熔断器TRIPPED |
| 告警 | CRITICAL告警 → DSHE路由 |
| 通过标准 | 熔断器正确触发 + 告警正确路由 + 审计日志完整 |

**熔断触发验证**:

```
请求1 ──▶ 500 ──▶ 失败计数=1
请求2 ──▶ 500 ──▶ 失败计数=2
请求3 ──▶ 500 ──▶ 失败计数=3
请求4 ──▶ 500 ──▶ 失败计数=4
请求5 ──▶ 500 ──▶ 失败计数=5 → 🔴 熔断器TRIPPED!
请求6 ──▶ 🔴 直接拒绝(不发起真实请求)
...
T+60s ──▶ 半开(允许3个探测)
探测1 ──▶ 500 ──▶ 半开失败计数=1
探测2 ──▶ 500 ──▶ 半开失败计数=2
探测3 ──▶ 500 ──▶ 半开失败计数=3 → 🔴 重新TRIPPED
```

### 9.5 INT-04: 服务超时

| 测试维度 | 值 |
|----------|-----|
| 测试目的 | 验证超时处理和重试策略 |
| 故障注入方式 | 服务端无响应(不关闭连接) |
| 预期行为 | 15s读取超时 → 重试 → 最终失败 |
| 重试次数 | 3次 |
| 重试时间线 | T=0(失败) → T=1s(重试1) → T=3s(重试2) → T=7s(重试3) |
| 最终超时 | T=11s后标记失败 |
| 通过标准 | 重试3次 + 熔断器触发 + 告警正确 |

### 9.6 INT-05: 高并发压力

| 测试维度 | 值 |
|----------|-----|
| 测试目的 | 验证50+并发请求下的服务稳定性和SLO |
| 并发数 | 50 并发请求 |
| 请求类型 | 不同short_id (避免缓存干扰) |
| 持续时间 | 60秒 |
| SLO — 成功率 | ≥ 99.9% |
| SLO — P99延迟 | < 500ms |
| SLO — P95延迟 | < 300ms |
| SLO — P50延迟 | < 100ms |
| 通过标准 | 全部SLO达标 + 无熔断触发 + 无CRITICAL告警 |

**压力测试脚本配置**:

```python
# 伪代码 — 高并发压力测试
CONCURRENT_REQUESTS = 50
DURATION_SECONDS = 60
SHORT_IDS = ["j25_tc", "j26_tc", "j27_tc", "j28_tc", "j29_tc", 
             "j30_tc", "j31_tc", "j32_tc", "lme_cu_tc", "lme_al_tc",
             "s_001", "s_002", ...]  # 178个不同short_id

# 监控指标:
# - 成功率 (success_rate)
# - P50/P95/P99 延迟
# - 错误率 (error_rate)
# - 熔断器状态
# - 吞吐量 (requests_per_second)
```

### 9.7 INT-06: 服务发现故障

| 测试维度 | 值 |
|----------|-----|
| 测试目的 | 验证服务发现故障时的优雅降级 |
| 故障注入方式 | Consul/Etcd集群宕机 |
| 预期降级策略 | DNS回退 → 本地缓存IP → 告警 |
| 降级优先级 | 1. DNS SRV查询 2. 本地IP缓存 3. 硬编码IP |
| 通过标准 | 降级后仍可访问 + 降级告警正确 + 恢复后自动切换回服务发现 |

**降级流程**:

```
正常状态: 服务发现 → 获取实例列表 → 负载均衡
     │
     ▼ (Consul宕机)
降级1: DNS SRV查询 → 获取IP列表 → 负载均衡
     │
     ▼ (DNS也故障)
降级2: 本地IP缓存 → 使用上次缓存的IP → 负载均衡
     │
     ▼ (缓存过期)
降级3: 硬编码IP → 使用配置中的备用IP → 负载均衡
     │
     ▼ (所有降级失败)
熔断: 标记DEP-001不可用 → CRITICAL告警 → Gate NOT_READY
```

### 9.8 INT-07: TLS证书过期

| 测试维度 | 值 |
|----------|-----|
| 测试目的 | 验证TLS证书过期时的连接失败和告警 |
| 故障注入方式 | 客户端证书设置为已过期 |
| 预期行为 | mTLS验证失败 → 连接拒绝 → CRITICAL告警 |
| 告警级别 | CRITICAL |
| 告警内容 | `TLS证书过期: dep001-api.internal, 剩余有效期=-3天` |
| 通过标准 | 连接失败 + 告警正确 + 不回退为HTTP (安全优先) |

### 9.9 INT-08: Token过期

| 测试维度 | 值 |
|----------|-----|
| 测试目的 | 验证Token过期后的重认证流程 |
| 故障注入方式 | 使用已过期的API Token请求 |
| 预期HTTP状态 | 401 |
| 预期响应体 | `{code: 401, error: "token_expired", message: "Token已过期"}` |
| 重认证流程 | Token刷新 → 新Token获取 → 重试请求 |
| 重认证次数 | 最多1次 |
| 重认证失败 | 升级告警 → CRITICAL |
| 通过标准 | 401响应正确 + 重认证成功 + 重试成功 |

**重认证流程**:

```
请求1 ──▶ 401 (Token过期)
     │
     ▼
Token刷新 ──▶ 新Token获取成功
     │
     ▼
请求2 (使用新Token) ──▶ 200 OK ✅
     │
     ▼ (如果新Token获取失败)
CRITICAL告警 ──▶ DSHE路由 ──▶ 值班人员处理
```

### 9.10 测试用例执行顺序

```
阶段1: 基础连通性 (INT-01, INT-02)
  │
  ▼
阶段2: 异常处理 (INT-03, INT-04)
  │
  ▼
阶段3: 安全验证 (INT-07, INT-08)
  │
  ▼
阶段4: 压力测试 (INT-05)
  │
  ▼
阶段5: 降级测试 (INT-06)
  │
  ▼
全部通过 → Gate V5 --env=prod 验证
```

---

## 10. 健康探测接口规范

### 10.1 端点定义

| 端点 | 路径 | 方法 | 用途 | 超时 | 检查频率 |
|------|------|------|------|------|----------|
| **Liveness** | `/health` | GET | 存活检查 — 进程是否存活 | 5s | 每30s |
| **Readiness** | `/ready` | GET | 就绪检查 — 是否可接收流量 | 5s | 每30s |
| **Live** | `/live` | GET | 轻量存活 — 仅TCP层响应 | 3s | 每10s |

### 10.2 响应格式

**/health 端点响应**:

```json
{
  "status": "UP",
  "version": "1.0.0",
  "timestamp": "2026-10-16T10:00:00+08:00",
  "uptime_seconds": 86400,
  "instance_id": "dep001-api-01",
  "build_commit": "a1b2c3d4e5f6",
  "checks": {
    "database": "UP",
    "redis": "UP",
    "short_id_cache": "UP",
    "consul": "UP",
    "tls_certificate": "UP"
  },
  "dependencies": {
    "database_host": "dep001-db.internal:5432",
    "redis_host": "dep001-redis.internal:6379",
    "consul_agent": "consul-01.internal:8500"
  },
  "metrics": {
    "active_connections": 12,
    "requests_per_second": 45,
    "error_rate_percent": 0.02,
    "p99_latency_ms": 85,
    "circuit_breaker_state": "CLOSED"
  }
}
```

**/ready 端点响应**:

```json
{
  "status": "READY",
  "version": "1.0.0",
  "timestamp": "2026-10-16T10:00:00+08:00",
  "checks": {
    "database": "UP",
    "redis": "UP",
    "consul": "UP",
    "short_id_cache": "UP",
    "tls_certificate": "UP",
    "api_token_valid": "UP",
    "log_collection": "UP"
  },
  "ready_for_traffic": true
}
```

**/live 端点响应**:

```json
{
  "status": "ALIVE",
  "timestamp": "2026-10-16T10:00:00+08:00"
}
```

### 10.3 响应时间 SLO

| 端点 | P50 | P95 | P99 | 最大 | 说明 |
|------|-----|-----|-----|------|------|
| `/health` | < 20ms | < 50ms | < 100ms | 500ms | 完整健康检查 |
| `/ready` | < 20ms | < 50ms | < 100ms | 500ms | 依赖检查 |
| `/live` | < 5ms | < 10ms | < 30ms | 100ms | 仅TCP层响应 |

### 10.4 健康状态码

| HTTP状态码 | 状态 | 含义 | Gate行为 |
|-----------|------|------|----------|
| **200** | UP | 服务正常, 可接收流量 | 计入可用实例 |
| **503** | DOWN | 服务异常, 不可接收流量 | 标记实例不可用 |
| **503** | DEGRADED | 服务降级 (部分功能不可用) | 降低权重但保留 |
| **503** | MAINTENANCE | 维护中 | 权重设为0 |

### 10.5 健康探测决策逻辑

```
探测结果 → 决策 → 动作
─────────────────────────────────────
3次连续200 → UP   → 加入负载均衡池
3次连续503 → DOWN → 移出负载均衡池 + 告警
2次503    → WARN  → 告警(观察中)
混合200/503 → DEGRADED → 降低权重至30
```

### 10.6 健康探测与Gate联动

| 探测状态 | Gate行为 | 告警行为 | DEP-001状态 |
|----------|----------|----------|-------------|
| 全部实例UP | Gate READY | INFO | ACTIVE |
| 部分实例DOWN | Gate CONDITIONAL | WARNING | DEGRADED |
| 全部实例DOWN | Gate NOT_READY | CRITICAL | BLOCKED |
| 全部实例DOWN > 5min | Gate NOT_READY | CRITICAL + 电话 | BLOCKED (升级) |

---

## 11. 日志采集配置

### 11.1 日志格式规范

**统一日志格式 (JSON)**:

```json
{
  "timestamp": "2026-10-16T10:00:00.123+08:00",
  "level": "INFO",
  "service": "dep001-api",
  "message": "short_id解析请求处理完成",
  "trace_id": "trace-abc123-def456",
  "request_id": "req-20261016-00001",
  "span_id": "span-xyz789",
  "parent_span_id": null,
  "duration_ms": 45,
  "event_type": "SHORT_ID_RESOLVE",
  "event_action": "RESOLVE_SUCCESS",
  "actor_service": "svc-dshb-gate",
  "actor_ip": "10.86.10.50",
  "target_short_id": "j25_tc",
  "result_long_id": "ID02226332",
  "http_status": 200,
  "cache_hit": true,
  "latency_ms": 45,
  "error": null,
  "metadata": {
    "server_instance": "dep001-api-01",
    "version": "1.0.0",
    "env": "prod",
    "zone": "cn-north-1"
  }
}
```

### 11.2 采集Agent配置

| 项目 | 配置值 | 说明 |
|------|--------|------|
| 采集Agent | **Filebeat** (首选) / Fluentd (备选) | 轻量级日志采集 |
| 采集源 | `/opt/dshb/logs/audit/**/*.jsonl` | 审计日志 |
| 采集源 | `/opt/dshb/logs/app/**/*.log` | 应用日志 |
| 采集源 | `/opt/dshb/logs/access/**/*.log` | 访问日志 |
| 采集间隔 | **30s** | 每30秒轮询新日志 |
| 扫描深度 | 递归扫描全部子目录 | 覆盖所有实例 |
| 文件偏移记录 | 持久化到 `/var/lib/filebeat/registry` | 避免重复采集 |
| 最大文件大小 | 单文件 ≤ 100MB | 超限触发额外轮转 |
| 采集并发 | 最多10个文件同时采集 | 避免IO饱和 |

### 11.3 Filebeat 配置示例

```yaml
filebeat.inputs:
  - type: filestream
    id: dep001-audit-logs
    enabled: true
    paths:
      - /opt/dshb/logs/audit/**/*.jsonl
    parsers:
      - type: json
        json.keys_under_root: true
        json.add_error_key: true
    fields:
      log_type: audit
      service: dep001-api
    fields_under_root: true
    scan_frequency: 30s
    max_bytes: 10485760

  - type: filestream
    id: dep001-app-logs
    enabled: true
    paths:
      - /opt/dshb/logs/app/**/*.log
    parsers:
      - type: json
        json.keys_under_root: true
    fields:
      log_type: app
      service: dep001-api
    fields_under_root: true
    scan_frequency: 30s

output.logstash:
  hosts: ["logstash.internal:5044"]
  ssl:
    enabled: true
    certificate_authorities: ["/etc/pki/tls/certs/ca-cert.pem"]
    certificate: "/etc/pki/tls/certs/filebeat-cert.pem"
    key: "/etc/pki/tls/private/filebeat-key.pem"
```

### 11.4 日志级别配置

| 级别 | 生产环境 | 沙箱环境 | 采集至中心 | 保留天数 |
|------|----------|----------|-----------|----------|
| **ERROR** | ✅ 启用 | ✅ 启用 | ✅ 是 | 90 |
| **WARN** | ✅ 启用 | ✅ 启用 | ✅ 是 | 90 |
| **INFO** | ✅ 启用 | ✅ 启用 | ✅ 是 | 90 |
| **DEBUG** | ❌ 禁用 | ✅ 启用 | ❌ 否 (仅本地) | 7 |
| **TRACE** | ❌ 禁用 | ❌ 禁用 | ❌ 否 | — |

### 11.5 关键指标采集

| 指标名称 | 类型 | 采集频率 | 说明 | 告警阈值 |
|----------|------|----------|------|----------|
| **requests_per_second** | Counter | 10s | 每秒请求数 | > 1000 req/s (WARN), > 2000 req/s (CRITICAL) |
| **error_rate_percent** | Gauge | 10s | 错误率 (500/404/401) | > 1% (WARN), > 5% (CRITICAL) |
| **latency_p50_ms** | Gauge | 10s | P50延迟 | > 50ms (WARN), > 100ms (CRITICAL) |
| **latency_p95_ms** | Gauge | 10s | P95延迟 | > 200ms (WARN), > 300ms (CRITICAL) |
| **latency_p99_ms** | Gauge | 10s | P99延迟 | > 400ms (WARN), > 500ms (CRITICAL) |
| **active_connections** | Gauge | 10s | 活跃连接数 | > 100 (WARN), > 200 (CRITICAL) |
| **circuit_breaker_state** | Gauge | 30s | 熔断器状态 (0=关,1=半开,2=熔断) | = 2 (CRITICAL) |
| **cache_hit_ratio** | Gauge | 30s | 缓存命中率 | < 80% (WARN), < 50% (CRITICAL) |
| **short_id_resolve_success** | Counter | 10s | 短ID解析成功数 | — |
| **short_id_resolve_fail** | Counter | 10s | 短ID解析失败数 | > 10/min (WARN) |
| **upstream_latency_ms** | Gauge | 10s | 上游数据库延迟 | > 100ms (WARN), > 200ms (CRITICAL) |
| **tls_certificate_remaining_days** | Gauge | 1h | 证书剩余有效期(天) | < 30天 (WARN), < 15天 (CRITICAL) |
| **api_token_remaining_hours** | Gauge | 1h | Token剩余有效期(小时) | < 6h (WARN), < 2h (CRITICAL) |
| **memory_usage_percent** | Gauge | 30s | 内存使用率 | > 80% (WARN), > 90% (CRITICAL) |
| **disk_usage_percent** | Gauge | 5m | 磁盘使用率 | > 80% (WARN), > 90% (CRITICAL) |
| **cpu_usage_percent** | Gauge | 30s | CPU使用率 | > 80% (WARN), > 90% (CRITICAL) |

### 11.6 日志与告警联动

```
日志事件 ───▶ 日志分析 ───▶ 告警规则匹配 ───▶ 告警路由
   │              │              │               │
   ▼              ▼              ▼               ▼
JSON结构化     Logstash      Elasticsearch    DSHE Alert
写入ES         解析+过滤      聚合+异常检测     Routing
                                       │
                                       ▼
                               ┌──────────────────┐
                               │ 告警分级路由:       │
                               │                   │
                               │ ERROR > 10/min   │
                               │  → CRITICAL告警   │
                               │  → DSHE → 电话+IM│
                               │                   │
                               │ ERROR 1-10/min   │
                               │  → WARNING告警    │
                               │  → DSHE → IM群   │
                               │                   │
                               │ WARN > 100/min   │
                               │  → INFO告警       │
                               │  → DSHE → 日志    │
                               └──────────────────┘
```

---

## 12. 联调前置条件检查清单

### 12.1 核心前置条件 (全部必须通过)

- [ ] **CHECK-01**: DEP-001 服务已部署并运行 (所有实例健康状态UP)
- [ ] **CHECK-02**: 网络白名单已配置 (全部8条防火墙规则 + 6条DNS解析 + 5条路由规则)
- [ ] **CHECK-03**: 服务账号已创建且权限正确 (`svc-dep001-prod` + DSHB/DSHE/HERMES三个服务账号)
- [ ] **CHECK-04**: API Token 已生成 (3个服务各1个Token, JWT格式, 24h有效期)
- [ ] **CHECK-05**: mTLS证书已交换 (DEP-001服务端证书 + 3个客户端证书, 均在有效期内)
- [ ] **CHECK-06**: 服务发现已配置 (Consul/Etcd注册完成, 健康检查回调正常)
- [ ] **CHECK-07**: 健康探测端点已验证 (`/health` `/ready` `/live` 均返回200)
- [ ] **CHECK-08**: 日志采集已配置 (Filebeat部署完成, 日志正常采集至ELK)
- [ ] **CHECK-09**: 告警路由已配置 (DSHE V3路由规则, CRITICAL/WARNING/INFO分级路由)
- [ ] **CHECK-10**: Gate V5 `--env=prod` 模式已验证 (V5脚本dryrun通过, 生产参数正确)
- [ ] **CHECK-11**: 全部8个联调测试用例通过 (INT-01 ~ INT-08 全部PASS)

### 12.2 前置条件依赖关系

```
CHECK-01 (服务部署)
    │
    ├──▶ CHECK-02 (网络白名单)
    │        │
    │        ├──▶ CHECK-06 (服务发现)
    │        │        │
    │        │        └──▶ CHECK-07 (健康探测)
    │        │                 │
    │        │                 ▼
    │        │            CHECK-11 (联调测试)
    │        │                 │
    │        │                 ▼
    │        └──▶ CHECK-10 (Gate V5验证) ──▶ READY
    │
    ├──▶ CHECK-03 (服务账号)
    │        │
    │        └──▶ CHECK-04 (API Token)
    │                 │
    │                 └──▶ CHECK-11 (联调测试)
    │
    ├──▶ CHECK-05 (mTLS证书)
    │        │
    │        └──▶ CHECK-11 (联调测试)
    │
    └──▶ CHECK-08 (日志采集)
             │
             └──▶ CHECK-09 (告警路由)
                      │
                      └──▶ CHECK-11 (联调测试)
```

### 12.3 前置条件检查状态总表

| 检查项ID | 检查项描述 | Owner | 前置依赖 | 检查方法 | 当前状态 |
|----------|-----------|-------|----------|----------|----------|
| CHECK-01 | DEP-001服务部署 | 数据平台 | — | `/health` 返回200 | 🔴 待部署 |
| CHECK-02 | 网络白名单 | 网络运维 | CHECK-01 | `telnet`/`curl` 连通性 | 🔴 待配置 |
| CHECK-03 | 服务账号 | IAM运维 | CHECK-01 | 账号查询API | 🔴 待申请 |
| CHECK-04 | API Token | IAM运维 | CHECK-03 | Token验证端点 | 🔴 待生成 |
| CHECK-05 | mTLS证书 | CA运维 | CHECK-03 | `openssl s_client` | 🔴 待签发 |
| CHECK-06 | 服务发现 | 中间件运维 | CHECK-02 | Consul API查询 | 🔴 待注册 |
| CHECK-07 | 健康探测 | 数据平台 | CHECK-06 | 探测脚本执行 | 🔴 待配置 |
| CHECK-08 | 日志采集 | 运维 | CHECK-01 | Filebeat状态检查 | 🔴 待配置 |
| CHECK-09 | 告警路由 | DSHE | CHECK-08 | 告警测试触发 | 🔴 待配置 |
| CHECK-10 | Gate V5验证 | DSHB | CHECK-01~07 | V5 dryrun | 🟡 V4就绪 |
| CHECK-11 | 联调测试 | 三方 | CHECK-01~10 | INT-01~INT-08 | 🔴 待执行 |

### 12.4 检查执行命令参考

```bash
# CHECK-01: 服务部署验证
curl -sk https://dep001-api.internal/health | jq .

# CHECK-02: 网络连通性验证
telnet dep001-api.internal 443
openssl s_client -connect dep001-api.internal:443 -showcerts

# CHECK-03: 服务账号验证
curl -H "Authorization: Bearer <admin_token>" \
  https://iam.internal/api/v1/users?name=svc-dep001-prod

# CHECK-04: Token验证
curl -H "Authorization: Bearer <test_token>" \
  https://iam.internal/api/v1/tokens/validate

# CHECK-05: mTLS验证
openssl s_client -connect dep001-api.internal:443 \
  -cert /path/to/client-cert.pem \
  -key /path/to/client-key.pem \
  -CAfile /path/to/ca-cert.pem

# CHECK-06: 服务发现验证
curl http://consul.internal:8500/v1/health/service/dep001-api

# CHECK-07: 健康探测验证
python3 -c "
import requests
for endpoint in ['/health', '/ready', '/live']:
    r = requests.get(f'https://dep001-api.internal{endpoint}')
    print(f'{endpoint}: {r.status_code} — {r.json()}')
"

# CHECK-08: 日志采集验证
systemctl status filebeat
curl http://localhost:5066/api/status  # Filebeat monitor API

# CHECK-09: 告警路由验证
python3 dryrun_e2e_test_v5.py --test-alert-routing

# CHECK-10: Gate V5验证
python3 gate_pre_check_auto_v5.py --env=prod --audit-validate --strict

# CHECK-11: 联调测试
python3 integration_test_runner.py --test-id INT-01,INT-02,INT-03,INT-04,INT-05,INT-06,INT-07,INT-08
```

---

## 13. 三方联调用例对齐

### 13.1 三方职责矩阵

| 测试维度 | DSHB (Gate) | DSHE (Alert) | HERMES (Audit) | 跨团队 |
|----------|-------------|-------------|----------------|--------|
| **基础连通性** | 执行Gate预检查 | — | — | — |
| **短ID解析** | L1探测 + data_fetchable_rate计算 | DEP状态变更告警 | L1证据包审计 | E2E链验证 |
| **HTTP 500处理** | 熔断器触发 + Gate NOT_READY | CRITICAL告警路由 | 审计记录+REG-06验证 | 熔断链路E2E |
| **超时处理** | 重试策略 + 超时熔断 | WARNING告警 | 超时事件审计 | 超时链路E2E |
| **安全验证** | mTLS+Token验证 | — | 审计日志加密验证 | 安全链E2E |
| **降级处理** | 降级数据率计算 | 降级告警 | 降级事件审计 | 降级链E2E |
| **压力测试** | 并发请求执行 | 吞吐量告警监控 | — | — |
| **日志验证** | — | 日志告警触发 | 日志完整性审计 | 日志链E2E |

### 13.2 三方对齐测试用例映射

| 用例ID | DSHB测试内容 | DSHE测试内容 | HERMES测试内容 | 对齐验证点 |
|--------|-------------|-------------|----------------|-----------|
| **INT-01** | Gate预检查: data_fetchable_rate计算 | — | 审计L1证据包: short_id解析成功记录 | 三方均确认解析成功 |
| **INT-02** | Gate预检查: 无效short_id不阻塞 | — | 审计: 404错误记录 | 三方均确认优雅处理 |
| **INT-03** | Gate预检查: 熔断器触发 + NOT_READY | CRITICAL告警: DEP-001 HTTP 500 | 审计: 熔断事件记录 + REG-06验证 | 三方均确认熔断链路完整 |
| **INT-04** | Gate预检查: 重试3次 + 超时熔断 | WARNING告警: 请求超时 | 审计: 超时事件记录 | 三方均确认超时处理 |
| **INT-05** | Gate预检查: 压力测试结果收集 | — | — | DSHB独立执行 |
| **INT-06** | Gate预检查: 降级data_fetchable_rate | 降级告警: 服务发现故障 | 审计: 降级事件记录 | 三方均确认降级链路 |
| **INT-07** | Gate预检查: mTLS验证失败 | CRITICAL告警: 证书过期 | 审计: 证书过期事件 | 三方均确认安全失败处理 |
| **INT-08** | Gate预检查: Token刷新 + 重试 | — | 审计: Token过期 + 刷新记录 | 三方均确认重认证流程 |

### 13.3 三方E2E链路测试

```
┌──────────────────────────────────────────────────────────────┐
│                  三方E2E链路测试架构                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                 │
│  │  L1      │   │  DEP-001  │   │  Gate    │                 │
│  │  Probe   │──▶│  Service  │──▶│  V5      │                 │
│  │  (DSHB)  │   │  (zhiji)  │   │  (DSHB)  │                 │
│  └──────────┘   └──────────┘   └──────────┘                 │
│        │                │                │                   │
│        │                │                │                   │
│        ▼                ▼                ▼                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                 │
│  │  Alert   │   │  Audit   │   │  Log     │                 │
│  │  Route   │◀──│  (HERMES)│   │  Collect │                 │
│  │  (DSHE)  │   │          │   │  (ELK)   │                 │
│  └──────────┘   └──────────┘   └──────────┘                 │
│                                                              │
│  测试场景:                                                    │
│  • 全链Happy Path: L1→DEP-001→Gate→Alert→Audit→Log          │
│  • Gate断链: L1→DEP-001→Gate(故障)→Alert(CRITICAL)→Audit     │
│  • Alert断链: L1→DEP-001→Gate→Alert(故障)→Audit              │
│  • Audit断链: L1→DEP-001→Gate→Alert→Audit(故障)→Log          │
│  • DEP抖动全链: DEP-001 ACTIVE↔BLOCKED → Gate抖动检测        │
└──────────────────────────────────────────────────────────────┘
```

### 13.4 三方接口契约

| 接口 | 方向 | 数据格式 | 协议 | 频率 |
|------|------|----------|------|------|
| Gate → Alert | DSHB → DSHE | JSON (alert event) | HTTP POST | 事件触发 |
| Gate → Audit | DSHB → HERMES | JSON (evidence package) | 文件系统 + HTTP | 每次Gate执行 |
| Alert → Audit | DSHE → HERMES | JSON (alert log) | HTTP POST | 事件触发 |
| DEP-001 → Log | zhiji → ELK | JSONL (stream) | Filebeat | 实时 |
| Audit → Log | HERMES → ELK | JSON (audit event) | HTTP POST | 事件触发 |

### 13.5 三方联调时间线

```
时间轴:
T0      T1      T2      T3      T4      T5      T6
│       │       │       │       │       │       │
DSHB    ──────────────────────────────────────────────▶ Gate V5验证
DSHE    ────Alert配置──────Alert测试─────────────────────▶ 告警路由验证
HERMES  ────Audit配置────────────────Audit测试───────────▶ 审计验证
zhiji   ───DEP部署──DEP配置────────DEP测试────────────────▶ 服务就绪
三方    ───────────────联合E2E测试─────────────────────────▶ 全链验证
```

---

## 14. 风险与缓解措施

### 14.1 风险清单

| 风险ID | 风险描述 | 影响 | 概率 | 严重度 | 风险等级 |
|--------|----------|------|------|--------|----------|
| **R1** | DEP-001服务不稳定 (间歇性HTTP 500) | 熔断器频繁触发, Gate不稳定 | 中 | 高 | 🔴 高 |
| **R2** | Token轮换失败 (新旧Token重叠期异常) | 请求认证失败, 服务不可用 | 低 | 高 | 🟡 中 |
| **R3** | 网络延迟导致超时 (跨机房延迟) | 请求超时, 重试增加, 负载升高 | 中 | 中 | 🟡 中 |
| **R4** | 日志量爆炸 (INFO级别全量采集) | 磁盘空间耗尽, ELK索引膨胀 | 低 | 高 | 🟡 中 |
| **R5** | mTLS证书过期 (续期失败) | 全部连接失败, 服务不可用 | 低 | 严重 | 🔴 高 |
| **R6** | 服务发现故障 (Consul宕机) | 无法发现实例, 降级至DNS | 低 | 中 | 🟡 中 |
| **R7** | 并发压力超过SLO (INT-05不达标) | 高延迟, 错误率上升 | 中 | 中 | 🟡 中 |
| **R8** | 三方接口契约不一致 | 联调数据对不上, 审计链断裂 | 低 | 高 | 🟡 中 |
| **R9** | DEP-001恢复后状态不一致 (部分恢复) | data_fetchable_rate不稳定, Gate抖动 | 中 | 中 | 🟡 中 |
| **R10** | 审计日志丢失 (Filebeat采集失败) | 审计链不完整, 合规风险 | 低 | 高 | 🟡 中 |

### 14.2 缓解措施

#### R1: DEP-001服务不稳定

| 缓解措施 | 描述 | 优先级 |
|----------|------|--------|
| 熔断器 | failure_threshold=5, 避免雪崩 | P0 |
| 重试策略 | 指数退避, 避免立即重试 | P0 |
| 多实例 | 至少3实例, 单实例故障不中断 | P0 |
| 健康探测 | 30s间隔探测, 快速发现故障 | P0 |
| 告警 | CRITICAL告警立即通知 | P0 |

#### R2: Token轮换失败

| 缓解措施 | 描述 | 优先级 |
|----------|------|--------|
| 宽限期 | 旧Token过期后继续有效24h (Grace Period) | P0 |
| 双Token | 同时持有active+backup两个Token | P0 |
| 自动重试 | Token刷新失败自动重试3次 | P1 |
| 告警 | Token剩余<6h告警, <2h CRITICAL | P1 |

#### R3: 网络延迟导致超时

| 缓解措施 | 描述 | 优先级 |
|----------|------|--------|
| 超时调优 | connect_timeout=30s, read_timeout=15s | P1 |
| 重试 | 最多3次重试, 指数退避 | P1 |
| DNS缓存 | DNS解析结果缓存, 避免重复查询 | P2 |
| 连接池 | 长连接池, 减少TCP握手开销 | P2 |

#### R4: 日志量爆炸

| 缓解措施 | 描述 | 优先级 |
|----------|------|--------|
| 日志级别过滤 | 生产环境禁用DEBUG/TRACE | P0 |
| 采样 | INFO级别日志可采样(50%采样率) | P1 |
| 轮转 | 每日轮转 + 单文件100MB限制 | P0 |
| 清理 | 90天后自动删除 | P1 |
| 磁盘监控 | 磁盘>80%告警, >90% CRITICAL | P1 |

#### R5: mTLS证书过期

| 缓解措施 | 描述 | 优先级 |
|----------|------|--------|
| 自动续期 | ACME协议自动续期, 提前30天 | P0 |
| 监控告警 | 证书剩余<30天WARN, <15天CRITICAL | P0 |
| 证书检查 | 启动时检查证书有效期 | P0 |
| 手动备份 | 保留证书签发记录, 支持手动续期 | P2 |

#### R6: 服务发现故障

| 缓解措施 | 描述 | 优先级 |
|----------|------|--------|
| DNS回退 | 服务发现故障时回退至DNS SRV查询 | P0 |
| 本地缓存 | 缓存最后一次发现的实例列表 | P0 |
| 硬编码IP | 最终回退至配置中的备用IP | P1 |
| 告警 | 服务发现故障CRITICAL告警 | P0 |

#### R7: 并发压力超过SLO

| 缓解措施 | 描述 | 优先级 |
|----------|------|--------|
| 限流 | API网关限流1000 req/min per client | P1 |
| 弹性伸缩 | 自动扩缩容至10实例 | P1 |
| 缓存 | Redis缓存短ID映射结果 | P0 |
| 连接池 | 数据库连接池, 避免连接风暴 | P1 |

#### R8: 三方接口契约不一致

| 缓解措施 | 描述 | 优先级 |
|----------|------|--------|
| 契约文档 | 三方接口契约文档化 (附录B) | P0 |
| 契约测试 | 联调前执行契约兼容性测试 | P0 |
| 版本控制 | 接口版本钉定, 向后兼容 | P1 |
| 变更通知 | 接口变更提前72h通知三方 | P1 |

#### R9: DEP-001恢复后状态不一致

| 缓解措施 | 描述 | 优先级 |
|----------|------|--------|
| 抖动检测 | DS-06: 15min窗口内BLOCKED↔ACTIVE切换检测 | P1 |
| 逐步放量 | 恢复后先10%流量, 验证15min后全量 | P1 |
| Gate冷却 | 恢复后Gate执行3次连续READY才标记稳定 | P1 |
| 回滚SOP | 状态再次恶化时自动回滚至熔断状态 | P0 |

#### R10: 审计日志丢失

| 缓解措施 | 描述 | 优先级 |
|----------|------|--------|
| 本地持久化 | 日志先写本地磁盘, 再采集至中心 | P0 |
| Filebeat持久化 | 采集偏移持久化, 避免重复/丢失 | P0 |
| 备份 | 审计日志每日备份至异地存储 | P1 |
| 完整性校验 | `.audit_manifest.json` 记录每条日志的hash | P1 |

---

## 15. 下一步行动

### 15.1 行动阶段总览

| 阶段 | 名称 | 负责团队 | 预估工期 | 产出物 | 前置依赖 |
|------|------|----------|----------|--------|----------|
| **Phase 1** | 基础设施搭建 | 网络+IAM+CA | T+5天 | 网络白名单/账号/Token/证书 | — |
| **Phase 2** | 服务发现与健康探测 | 中间件+数据平台 | T+7天 | Consul注册/健康端点/降级策略 | Phase 1 |
| **Phase 3** | Gate V5 --env=prod验证 | DSHB | T+10天 | V5脚本dryrun通过 | Phase 1, 2 |
| **Phase 4** | 全量联调测试 | 三方 | T+14天 | INT-01~INT-08全部PASS | Phase 1, 2, 3 |
| **Phase 5** | 生产发布就绪评估 | 三方 | T+15天 | 发布就绪报告 + 放行决策 | Phase 4 |

### 15.2 Phase 1: 基础设施搭建 (T+5天)

**目标**: 完成网络、权限、TLS全部基础设施配置

| 行动ID | 行动项 | 负责人 | 截止日期 | 产出物 | 验证方法 |
|--------|--------|--------|----------|--------|----------|
| P1-01 | 防火墙规则配置 (8条) | 网络运维 | T+2 | FW规则清单 | `telnet` 连通性 |
| P1-02 | DNS解析配置 (6条) | DNS运维 | T+2 | DNS记录清单 | `dig` 查询 |
| P1-03 | 路由规则配置 (5条) | 网络运维 | T+3 | RT规则清单 | `traceroute` |
| P1-04 | API网关路由配置 (8条) | 网关运维 | T+3 | GW配置清单 | `curl` 请求 |
| P1-05 | 服务账号创建 (4个) | IAM运维 | T+2 | 账号清单 | IAM查询API |
| P1-06 | API Token生成 (3个) | IAM运维 | T+2 | Token清单 | Token验证API |
| P1-07 | mTLS证书签发 (5张) | CA运维 | T+3 | 证书清单 | `openssl verify` |
| P1-08 | 证书过期监控配置 | CA运维 | T+3 | 监控规则 | 告警测试 |

### 15.3 Phase 2: 服务发现与健康探测 (T+7天)

**目标**: 完成服务发现注册、健康检查端点、降级策略配置

| 行动ID | 行动项 | 负责人 | 截止日期 | 产出物 | 验证方法 |
|--------|--------|--------|----------|--------|----------|
| P2-01 | DEP-001服务注册至Consul | 中间件运维 | T+5 | 注册记录 | Consul API查询 |
| P2-02 | 健康检查端点实现 | 数据平台 | T+4 | 端点实现 | `/health` `/ready` `/live` |
| P2-03 | 健康探测配置 | 中间件运维 | T+5 | 探测配置 | 探测脚本执行 |
| P2-04 | 降级策略配置 | 中间件运维 | T+6 | 降级配置 | 故障注入测试 |
| P2-05 | 服务发现客户端集成 | DSHB | T+6 | 客户端代码 | 服务查询验证 |
| P2-06 | 负载均衡权重配置 | 中间件运维 | T+6 | 权重配置 | 流量分配验证 |
| P2-07 | 熔断器参数配置 | DSHB | T+7 | 熔断配置 | 熔断测试 |
| P2-08 | 服务版本钉定配置 | 中间件运维 | T+7 | 版本配置 | 版本路由验证 |

### 15.4 Phase 3: Gate V5 --env=prod 验证 (T+10天)

**目标**: Gate V5 脚本在 --env=prod 模式下完整验证通过

| 行动ID | 行动项 | 负责人 | 截止日期 | 产出物 | 验证方法 |
|--------|--------|--------|----------|--------|----------|
| P3-01 | V5脚本开发 (--env=prod/sandbox隔离) | DSHB | T+7 | `gate_pre_check_auto_v5.py` | dryrun通过 |
| P3-02 | 生产参数配置 | DSHB | T+8 | prod配置参数 | 配置校验 |
| P3-03 | L1证据包生产格式 | DSHB | T+8 | L1证据包构建器 | 证据包格式验证 |
| P3-04 | data_fetchable_rate生产计算 | DSHB | T+9 | 计算逻辑 | 178项指标全量验证 |
| P3-05 | Gate判定矩阵prod版本 | DSHB | T+9 | 判定矩阵 | 全部G01~G10验证 |
| P3-06 | V5 dryrun 执行 | DSHB | T+10 | dryrun报告 | `gate_pre_check_auto_v5.py --env=prod --audit-validate --strict` |
| P3-07 | V5 回归测试 | DSHB | T+10 | 回归测试报告 | V4→V5无回归 |

### 15.5 Phase 4: 全量联调测试 (T+14天)

**目标**: 全部8个联调测试用例通过

| 行动ID | 行动项 | 负责人 | 截止日期 | 产出物 | 验证方法 |
|--------|--------|--------|----------|--------|----------|
| P4-01 | INT-01: 正常短ID解析 | DSHB | T+11 | 测试报告 | 执行+审计 |
| P4-02 | INT-02: 短ID未找到 | DSHB | T+11 | 测试报告 | 执行+审计 |
| P4-03 | INT-03: 服务500错误+熔断 | DSHB+DSHE | T+12 | 测试报告 | 熔断验证 |
| P4-04 | INT-04: 服务超时 | DSHB+DSHE | T+12 | 测试报告 | 重试+熔断 |
| P4-05 | INT-05: 高并发压力 | DSHB | T+12 | 压力报告 | 50并发SLO验证 |
| P4-06 | INT-06: 服务发现降级 | DSHB+DSHE | T+13 | 测试报告 | 降级链路 |
| P4-07 | INT-07: TLS证书过期 | DSHB+DSHE | T+13 | 测试报告 | mTLS验证 |
| P4-08 | INT-08: Token过期 | DSHB+DSHE | T+13 | 测试报告 | 重认证流程 |
| P4-09 | 三方E2E联合测试 | 三方 | T+14 | E2E报告 | 全链验证 |

### 15.6 Phase 5: 生产发布就绪评估 (T+15天)

**目标**: 全部前置条件满足, 输出发布就绪报告

| 行动ID | 行动项 | 负责人 | 截止日期 | 产出物 | 验证方法 |
|--------|--------|--------|----------|--------|----------|
| P5-01 | 前置条件检查清单全过 | 三方 | T+14 | 检查清单全✅ | CHECK-01~11全通过 |
| P5-02 | 风险项全部关闭 | 三方 | T+14 | 风险台账更新 | R1~R10全部有缓解措施 |
| P5-03 | 发布就绪报告 | DSHB | T+15 | 发布就绪报告 | 三方评审 |
| P5-04 | 发布决策会 | 三方负责人 | T+15 | 决策记录 | 三方签字放行 |
| P5-05 | 灰度发布方案 | DSHB | T+15 | 灰度方案 | 10%→50%→100% |
| P5-06 | 回滚SOP | 三方 | T+15 | 回滚方案 | 回滚演练 |

### 15.7 行动依赖关系图

```
Phase 1 (基础设施)
  │
  ├── P1-01 FW规则 ──┐
  ├── P1-02 DNS解析 ──┤
  ├── P1-03 路由规则 ─┤──▶ Phase 2 (服务发现)
  ├── P1-04 GW路由 ──┤        │
  │                    │        ├── P2-01 Consul注册
  │                    │        ├── P2-02 健康端点
  │                    │        ├── P2-03 健康探测
  │                    │        └── P2-04 降级策略
  │                    │
  ├── P1-05 服务账号 ──┤──▶ Phase 3 (Gate V5)
  ├── P1-06 API Token ┤        │
  │                    │        ├── P3-01 V5开发
  │                    │        ├── P3-02 prod参数
  │                    │        └── P3-06 V5 dryrun
  │                    │
  ├── P1-07 mTLS证书 ──┤──▶ Phase 4 (联调测试)
  ├── P1-08 证书监控 ──┤        │
  │                    │        ├── P4-01~P4-08 INT用例
  │                    │        └── P4-09 三方E2E
  │                    │
  └── Phase 2 ─────────┘──▶ Phase 5 (就绪评估)
                                  │
                                  ├── P5-01 检查清单全过
                                  ├── P5-02 风险全部关闭
                                  ├── P5-03 发布就绪报告
                                  └── P5-04 三方决策会
```

### 15.8 关键里程碑

| 里程碑 | 日期 | 判定标准 |
|--------|------|----------|
| **M1: 基础设施就绪** | T+5 | Phase 1 全部8项完成 |
| **M2: 服务发现就绪** | T+7 | Phase 2 全部8项完成 |
| **M3: Gate V5 dryrun通过** | T+10 | Phase 3 全部7项完成 |
| **M4: 联调测试全过** | T+14 | Phase 4 全部9项完成, INT-01~INT-08 PASS |
| **M5: 发布就绪** | T+15 | Phase 5 全部6项完成, 三方签字放行 |

---

## 16. 附录A: 依赖链参考路径

### A.1 关键文件路径

| 文件 | 路径 | 用途 |
|------|------|------|
| DEP-001主台账 | `dshb_dep_registry_dep-reg-001.json` | DEP-001全生命周期状态 |
| Gate V4脚本 | `gate_pre_check_auto_v4.py` | 当前Gate预检查脚本 |
| Gate V5脚本 | `gate_pre_check_auto_v5.py` | 开发中, --env=prod/sandbox |
| 熔断演练报告 | `v86_rc2_dshb_dep_fuse_dryrun_report.md` | DEP-001熔断机制验证 |
| 三方E2E报告 | `v86_rc2_dshb_tripartite_dryrun_e2e_report.md` | L1→Gate→HERMES→DSHE链路 |
| 外部依赖台账 | `v86_rc2_dshb_external_dependency_block_list.md` | 短ID解析能力缺失详情 |
| 数据平台工单 | `v86_rc2_dshb_data_platform_ticket_record.md` | DEP-01工单详情与AC |
| DEP GAP日志 | `v86_rc2_dshb_dep_gap_sync_log.md` | 6项DEP SOP GAP |
| L1证据预检 | `l1_evidence_pre_check_v2.py` | L1层证据预检查 |
| 全量复测脚本 | `full_reverify_v3_batch_v2.py` | 178项指标全量复测 |
| 依赖触发器 | `dep_ready_trigger_v2.py` | DEP就绪检测触发 |
| 生产阶段1 | `dshb_gate_prod_stage1/` | 生产发布阶段1文件 |
| 生产阶段4 | `dshb_gate_prod_stage4/` | 灰度发布方案 |

### A.2 DEP-001 依赖链完整路径

```
依赖链层级:
L0: 探测层 (L1 Probe)
  └── 文件: l1_evidence_pre_check_v2.py
  └── 探测ID: j25_tc, i1, i3
  └── 探测端点: GET /commodity/api/series?id={short_id}

L1: 解析层 (DEP-001 REST API)
  └── 服务: zhiji commodity_api
  └── 端点: GET /commodity/api/series?id={short_id}
  └── 依赖: PostgreSQL (short_id→long_id映射表) + Redis (缓存)

L2: 数据层 (long_id数据取数)
  └── 端点: GET /commodity/api/series?id={long_id}
  └── 依赖: PostgreSQL (数据系列存储)

L3: Gate层 (gate_pre_check_auto_v5.py)
  └── 文件: gate_pre_check_auto_v5.py (开发中)
  └── 检查: G01~G10 + G06A + PERF-GUARD + ROB-01 + DS-06
  └── 阈值: data_fetchable_rate ≥ 80% → READY

L4: 审计层 (HERMES evidence_auditor)
  └── 文件: evidence_auditor.py (hermes_e2e_test/)
  └── 规则: REG-06, PERF-GUARD, ROB-01, DS-06
  └── 输出: PASS / CONDITIONAL_PASS / FAIL / ERROR

L5: 告警层 (DSHE Alert Routing)
  └── 路由: CRITICAL → 电话+IM, WARNING → IM群, INFO → 日志
  └── 事件: DEP状态变更, Gate NOT_READY, 熔断触发

L6: 日志层 (ELK Stack)
  └── 采集: Filebeat → Logstash → Elasticsearch → Kibana
  └── 日志: 审计日志 / 应用日志 / 访问日志
  └── 保留: 90天
```

---

## 17. 附录B: 跨团队接口契约

### B.1 Gate → Alert 事件格式 (DSHB → DSHE)

```json
{
  "event_id": "evt-20261016-00001",
  "timestamp": "2026-10-16T10:00:00+08:00",
  "source": "DSHB-Gate",
  "event_type": "GATE_NOT_READY",
  "severity": "CRITICAL",
  "dep_id": "DEP-001",
  "dep_status": "BLOCKED",
  "gate_status": "NOT_READY",
  "data_fetchable_rate": 0.0,
  "blocked_count": 178,
  "total_count": 178,
  "error_detail": "HTTP 500: 无法识别指标来源(id前缀)",
  "circuit_breaker_state": "TRIPPED",
  "circuit_breaker_tripped_at": "2026-10-16T09:55:00+08:00",
  "trace_id": "trace-gate-20261016-001",
  "metadata": {
    "gate_version": "5.0",
    "gate_script": "gate_pre_check_auto_v5.py",
    "env": "prod",
    "dep_registry_id": "DEP-REG-001"
  }
}
```

### B.2 Gate → Audit 证据包格式 (DSHB → HERMES)

```json
{
  "evidence_id": "evd-20261016-00001",
  "timestamp": "2026-10-16T10:00:00+08:00",
  "source": "DSHB-Gate",
  "contract_version": "EVIDENCE_CONTRACT_V1",
  "dep_registry_id": "DEP-REG-001",
  "dep_id": "DEP-001",
  "gate_result": "NOT_READY",
  "g06a_status": "FAIL",
  "data_fetchable_rate": 0.0,
  "total_indicators": 178,
  "fetchable_count": 0,
  "probe_results": [
    {
      "short_id": "j25_tc",
      "http_status": 500,
      "probe_ready": false,
      "latency_ms": 15000
    },
    {
      "short_id": "i1",
      "http_status": 500,
      "probe_ready": false,
      "latency_ms": 15000
    },
    {
      "short_id": "i3",
      "http_status": 500,
      "probe_ready": false,
      "latency_ms": 15000
    }
  ],
  "audit_bypass": false,
  "circuit_breaker_state": "TRIPPED",
  "dep_flap_detected": false,
  "perf_guard_triggered": false,
  "rob01_retry_triggered": false,
  "self_hash": "md5:abc123def456",
  "metadata": {
    "gate_version": "5.0",
    "env": "prod"
  }
}
```

### B.3 Alert → Audit 事件格式 (DSHE → HERMES)

```json
{
  "alert_id": "alert-20261016-00001",
  "timestamp": "2026-10-16T10:00:00+08:00",
  "source": "DSHE-Alert",
  "event_id": "evt-20261016-00001",
  "event_type": "GATE_NOT_READY",
  "severity": "CRITICAL",
  "routing_rule": "gate_not_ready_critical",
  "routing_target": "oncall_phone+im",
  "delivery_status": "DELIVERED",
  "delivery_attempts": 1,
  "trace_id": "trace-gate-20261016-001",
  "metadata": {
    "alert_version": "3.0",
    "routing_engine": "DSHE-Alert-Router"
  }
}
```

### B.4 接口契约版本控制

| 接口 | 当前版本 | 向后兼容 | 变更策略 |
|------|----------|----------|----------|
| Gate → Alert | v1.0 | ✅ 兼容 | 新增字段不破坏兼容 |
| Gate → Audit | v1.0 (EVIDENCE_CONTRACT_V1) | ✅ 兼容 | 新增字段+contract_version |
| Alert → Audit | v1.0 | ✅ 兼容 | 新增字段不破坏兼容 |

---

## 18. 附录C: 变更记录

### C.1 文档版本历史

| 版本 | 日期 | 变更内容 | 变更人 |
|------|------|----------|--------|
| V1.0 | 2026-10-16 | 初始版本 — 完整联调前置检查清单 | DSH Harness Agent |

### C.2 关联变更

| 变更ID | 变更内容 | 影响范围 | 关联工单 |
|--------|----------|----------|----------|
| CHG-001 | 创建DEP-001联调前置检查清单 | 三方联调流程 | DSHB_V86_RC2_RDEP07_GATE_PROD_PREP |
| CHG-002 | Gate V5开发 (--env=prod/sandbox) | Gate预检查 | DSHB_V86_RC2_RDEP07_GATE_PROD_PREP |
| CHG-003 | DEP-001服务恢复跟踪 | DEP状态 | DEP-REG-001 |

### C.3 相关工单引用

| 工单 | 状态 | 关联 |
|------|------|------|
| DSHB_V86_RC2_RDEP07_GATE_PROD_PREP / T3.3 | 🟢 进行中 | 本文档所属工单 |
| DSHB_V86_RC2_GATE_REG06_FIX_E2E / T3.3 | 🟢 已完成 | Gate V4 REG-06修复 |
| DSHB_V86_RC2_DEP_GAP_SYNC_T3.3 | 🟢 已完成 | DEP GAP同步 |
| DSHB_V86_RC2_GATE_FUSE_VERIFY / T3.3 | 🟢 已完成 | 熔断验证 |
| DSHB-DP-REQ-20261015-001 | 🟡 进行中 | 数据平台DEP-01工单 |

---

> **文档结束**
> 
> 本文档为 DEP-001 服务联调前置准备的完整检查清单，供三方（DSHB/DSHE/HERMES）联调前逐项确认。
> 
> **使用方法**: 按照 §12.1 核心前置条件检查清单逐项验证，全部通过后方可进入生产发布阶段。
> 
> **更新频率**: 每周更新一次，或状态变更时即时更新。
> 
> **下一次评审**: 2026-10-23 (或 Phase 1 完成后，以先到者为准)
