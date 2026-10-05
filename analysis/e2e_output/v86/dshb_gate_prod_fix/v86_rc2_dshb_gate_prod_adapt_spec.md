# DSHB V86-RC2 Gate Prod Adaptation Specification V5

> **工单编号**: DSHB_V86_RC2_RDEP07_GATE_PROD_PREP / T3.2  
> **脚本版本**: V5.0 (`gate_pre_check_auto_v5.py`)  
> **基线版本**: V4.0 (`gate_pre_check_auto_v4.py`)  
> **报告文件**: `v86_rc2_dshb_gate_auto_check_report_v5.md`  
> **约束**: NO_OVERWRITE=TRUE / NO_MODIFY_V85=TRUE / BRANCH_LOCKED=TRUE  
> **文档版本**: V1.0  
> **编制日期**: 2026-08-31  

---

## 目录

1. [概述](#1-概述)
2. [版本演进 V4→V5](#2-版本演进-v4v5)
3. [环境分支设计](#3-环境分支设计)
4. [生产配置规范](#4-生产配置规范)
5. [沙箱配置隔离](#5-沙箱配置隔离)
6. [服务发现集成](#6-服务发现集成)
7. [Token 鉴权设计](#7-token-鉴权设计)
8. [超时与重试策略](#8-超时与重试策略)
9. [生产审计日志](#9-生产审计日志)
10. [CLI 参数说明](#10-cli-参数说明)
11. [配置示例](#11-配置示例)
12. [兼容性分析](#12-兼容性分析)
13. [迁移指南](#13-迁移指南)
14. [风险与缓解](#14-风险与缓解)
15. [附录](#15-附录)

---

## 1. 概述

### 1.1 背景

DSHB V86-RC2 Gate 常态化预检查脚本在 V4 版本中集成了 HERMES evidence_auditor_v2_plus 审计器、REG-06 修复、紧急旁路开关、PERF-GUARD 性能守护、DS-06 DEP 状态抖动检测及 ROB-01 损坏证据容错等关键能力。V4 已在沙箱环境中充分验证，全部 13 项检查项（G01~G10、G06A、PERF-GUARD、DS-06）运行稳定。

随着 DSHB V86-RC2 进入生产部署阶段，Gate 预检查脚本需要适配生产环境的特殊要求：

- **更严格的超时控制**: 生产环境要求更快的故障发现（30s vs 沙箱 60s）
- **独立的生产审计日志**: 生产环境需要独立于沙箱的审计日志路径
- **服务发现集成**: 生产环境需要动态服务发现能力
- **Token 鉴权**: 生产环境需要基于 Token 的认证机制
- **重试策略**: 生产环境需要指数退避重试（max_retries=3, backoff_factor=2）

### 1.2 目标

V5 版本（`gate_pre_check_auto_v5.py`）在完整保留 V4 全部功能的基础上，增加生产环境适配能力：

1. ✅ **环境分支**: 通过 `--env=prod/sandbox` 切换沙箱/生产配置
2. ✅ **配置隔离**: 沙箱与生产使用完全独立的配置集，互不影响
3. ✅ **生产超时控制**: 生产环境 30s 超时（沙箱保持 60s）
4. ✅ **生产审计日志**: 独立日志目录 `prod_audit_logs/`
5. ✅ **服务发现集成**: 生产环境支持服务发现（Mock 实现）
6. ✅ **Token 鉴权**: 生产环境支持 Token 认证
7. ✅ **重试策略**: 生产环境指数退避重试（max=3, backoff=2, initial=1s）
8. ✅ **自检函数**: `_run_self_test()` 验证环境分支、配置隔离、13 项检查

### 1.3 设计原则

| 原则 | 说明 |
|------|------|
| **零回归** | 沙箱模式必须产生与 V4 完全相同的结果 |
| **增量扩展** | 生产模式为新增能力，不修改任何 V4 现有逻辑 |
| **配置隔离** | 沙箱与生产使用完全独立的配置字典，互不干扰 |
| **向后兼容** | V4 的所有 CLI 参数在 V5 中完全兼容 |
| **自包含** | V5 脚本为完全独立的文件，不依赖 V4 运行时导入 |

---

## 2. 版本演进 V4→V5

### 2.1 版本对比

| 维度 | V4 (`gate_pre_check_auto_v4.py`) | V5 (`gate_pre_check_auto_v5.py`) |
|------|-----------------------------------|-----------------------------------|
| **行数** | 2025 | ~2674 |
| **报告文件** | `v86_rc2_dshb_gate_auto_check_report_v4.md` | `v86_rc2_dshb_gate_auto_check_report_v5.md` |
| **环境分支** | 无（仅沙箱） | `--env=prod/sandbox` |
| **超时设置** | 固定 60s | 沙箱 60s / 生产 30s |
| **审计超时** | 固定 60s | 沙箱 60s / 生产 30s |
| **日志级别** | 无 | 沙箱 DEBUG / 生产 INFO |
| **重试策略** | 无 | 沙箱 0 / 生产 max=3, backoff=2 |
| **服务发现** | 无 | 生产 Mock（URL 可配置） |
| **Token 鉴权** | 无 | 生产（Token 文件路径） |
| **生产审计日志** | 无 | `prod_audit_logs/` |
| **自检函数** | 无 | `_run_self_test()`（10 组 24 项） |

### 2.2 V4 功能保留清单

V5 完整保留了 V4 的全部功能，无删减、无修改：

| # | V4 功能 | V5 保留状态 |
|---|---------|-------------|
| 1 | REG-06 修复（审计器 ERROR → FAIL → NOT_READY） | ✅ 完整保留 |
| 2 | 紧急旁路开关（`--audit-bypass`） | ✅ 完整保留 |
| 3 | 紧急旁路双审批指纹 | ✅ 完整保留 |
| 4 | 紧急旁路变更审计日志 | ✅ 完整保留 |
| 5 | 紧急旁路 24h 自动过期 | ✅ 完整保留 |
| 6 | PERF-GUARD（审计处理时长 >60s FAIL, >45s WARN） | ✅ 完整保留 |
| 7 | ROB-01（损坏 JSON → 优雅 ERROR → FAIL） | ✅ 完整保留 |
| 8 | DS-06（DEP 状态抖动检测, 15min 窗口） | ✅ 完整保留 |
| 9 | Gate 判定矩阵（ERROR → FAIL） | ✅ 完整保留 |
| 10 | 全部 13 项检查（G01~G10, G06A, PERF-GUARD, DS-06） | ✅ 完整保留 |
| 11 | L1 证据包构建（`_build_l1_evidence`） | ✅ 完整保留 |
| 12 | V3 证据契约（EVIDENCE_CONTRACT_V1） | ✅ 完整保留 |
| 13 | DEP-REG-001 映射 | ✅ 完整保留 |
| 14 | V2 审计器集成（`--audit-validate`） | ✅ 完整保留 |
| 15 | V2 CLI 参数（`--work-dir`, `--strict`, `--output`） | ✅ 完整保留 |

### 2.3 V5 新增功能清单

| # | V5 功能 | 说明 |
|---|---------|------|
| 1 | `--env=prod/sandbox` CLI 参数 | 环境分支切换（支持 `--env prod` 和 `--env=prod` 两种格式） |
| 2 | `PRODUCTION_CONFIG` 字典 | 生产环境专用配置集合 |
| 3 | `SANDBOX_CONFIG` 字典 | 沙箱环境专用配置集合（V4 兼容） |
| 4 | `_apply_env_config()` | 环境配置合并函数 |
| 5 | `_setup_production_auth()` | 生产 Token 鉴权初始化 |
| 6 | `_setup_service_discovery()` | 生产服务发现初始化 |
| 7 | `_create_retry_delay()` | 指数退避延迟计算 |
| 8 | `ProductionAuditLogger` 类 | 生产审计日志独立记录器 |
| 9 | `AuditValidator` 环境感知超时 | 审计器超时随环境切换（30s/60s） |
| 10 | `_run_self_test()` | 24 项自检验证 |
| 11 | 环境报告章节 | 报告中新增环境配置章节 |

---

## 3. 环境分支设计

### 3.1 设计概述

V5 通过 `--env` CLI 参数实现环境分支，支持两个环境：

- **sandbox**（默认）: 沙箱环境，与 V4 完全兼容
- **prod**: 生产环境，启用生产专用配置

### 3.2 环境切换流程

```
CLI 参数 --env=prod/sandbox
    │
    ▼
parse_args() 解析 --env 参数
    │
    ▼
_apply_env_config(config, env) 合并环境配置
    │
    ├── sandbox → 应用 SANDBOX_CONFIG（V4 兼容默认值）
    │
    └── prod → 应用 PRODUCTION_CONFIG（生产专用配置）
    │
    ▼
GatePreCheck.__init__() 初始化环境组件
    │
    ├── sandbox → 不初始化生产组件
    │
    └── prod → 初始化 ProductionAuditLogger、服务发现、Token 鉴权
    │
    ▼
run_all_checks() 执行全部 13 项检查
    │
    ▼
generate_report() 生成包含环境章节的报告
```

### 3.3 环境分支代码位置

| 组件 | 文件位置 | 行号范围 |
|------|----------|----------|
| `PRODUCTION_CONFIG` | V5 脚本 | 46-58 |
| `SANDBOX_CONFIG` | V5 脚本 | 61-72 |
| `DEFAULT_CONFIG["env"]` | V5 脚本 | 97 |
| `DEFAULT_CONFIG["production"]` | V5 脚本 | 98-108 |
| `_apply_env_config()` | V5 脚本 | 121-171 |
| `_setup_production_auth()` | V5 脚本 | 174-244 |
| `_setup_service_discovery()` | V5 脚本 | 247-297 |
| `GatePreCheck._setup_production_components()` | V5 脚本 | 461-480 |
| `parse_args() --env` | V5 脚本 | 1861-1874 |
| `main() 环境配置` | V5 脚本 | 1902-1903 |

### 3.4 环境分支验证矩阵

| 场景 | sandbox | prod | 期望结果 |
|------|---------|------|----------|
| 超时设置 | 60s | 30s | 沙箱超时 > 生产超时 |
| 审计超时 | 60s | 30s | 随环境切换 |
| 日志级别 | DEBUG | INFO | 生产更简洁 |
| 重试次数 | 0 | 3 | 生产允许重试 |
| 退避因子 | 1 | 2 | 生产指数退避 |
| 初始延迟 | 0s | 1s | 生产有延迟 |
| 审计日志目录 | None | `prod_audit_logs/` | 生产独立路径 |
| 服务发现 | None | None (Mock) | 生产可配置 |
| Token 鉴权 | False | False (可启用) | 生产可配置 |
| 13 项检查 | ✅ 13 项 | ✅ 13 项 | 全部保留 |

---

## 4. 生产配置规范

### 4.1 PRODUCTION_CONFIG 定义

```python
PRODUCTION_CONFIG = {
    "timeout_seconds": 30,          # 生产超时 (30s vs 沙箱 60s)
    "audit_timeout_seconds": 30,    # 审计超时 (30s vs 沙箱 60s)
    "log_level": "INFO",            # 生产日志级别 (INFO vs 沙箱 DEBUG)
    "audit_log_dir": "prod_audit_logs/",  # 生产审计日志目录
    "service_discovery_url": None,  # 服务发现端点 (待配置)
    "token_auth_enabled": False,    # Token 鉴权 (默认关闭，需显式启用)
    "token_path": None,             # Token 文件路径 (待配置)
    "retry_max": 3,                 # 最大重试次数
    "retry_backoff_factor": 2,      # 指数退避因子
    "retry_initial_delay": 1.0,     # 初始重试延迟 (秒)
}
```

### 4.2 配置字段说明

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `timeout_seconds` | int | 30 | 操作超时（秒），生产环境比沙箱更严格 |
| `audit_timeout_seconds` | int | 30 | 审计器调用超时（秒），与 `timeout_seconds` 联动 |
| `log_level` | str | "INFO" | 日志级别，生产环境仅输出 INFO 及以上 |
| `audit_log_dir` | str | "prod_audit_logs/" | 生产审计日志独立目录 |
| `service_discovery_url` | str | None | 服务发现端点 URL（生产环境待配置） |
| `token_auth_enabled` | bool | False | 是否启用 Token 鉴权 |
| `token_path` | str | None | Token 文件路径 |
| `retry_max` | int | 3 | 最大重试次数 |
| `retry_backoff_factor` | int | 2 | 指数退避因子 |
| `retry_initial_delay` | float | 1.0 | 初始重试延迟（秒） |

### 4.3 生产配置激活条件

生产配置仅在以下条件下激活：

1. CLI 传入 `--env=prod` 或 `--env prod`
2. `_apply_env_config(config, "prod")` 被调用
3. `GatePreCheck._setup_production_components()` 初始化生产组件

### 4.4 生产组件初始化

当环境为 prod 时，`GatePreCheck._setup_production_components()` 执行以下初始化：

| 组件 | 类/函数 | 条件 |
|------|---------|------|
| 生产审计日志器 | `ProductionAuditLogger` | `env == "prod"` |
| 服务发现 | `_setup_service_discovery()` | `env == "prod"` |
| Token 鉴权 | `_setup_production_auth()` | `env == "prod"` |

---

## 5. 沙箱配置隔离

### 5.1 隔离原则

沙箱与生产配置**完全隔离**，满足以下要求：

1. **不同配置字典**: 沙箱使用 `SANDBOX_CONFIG`，生产使用 `PRODUCTION_CONFIG`
2. **互不干扰**: 修改一个环境的配置不影响另一个环境
3. **V4 兼容**: 沙箱配置保持 V4 默认值不变
4. **明确差异**: 7 个配置键在沙箱和生产之间不同

### 5.2 SANDBOX_CONFIG 定义

```python
SANDBOX_CONFIG = {
    "timeout_seconds": 60,          # 沙箱超时 (60s, 与 V4 相同)
    "audit_timeout_seconds": 60,    # 沙箱审计超时 (60s)
    "log_level": "DEBUG",           # 沙箱日志级别 (DEBUG)
    "audit_log_dir": None,          # 无独立审计日志目录
    "service_discovery_url": None,  # 无服务发现
    "token_auth_enabled": False,    # 无 Token 鉴权
    "token_path": None,             # 无 Token
    "retry_max": 0,                 # 无重试 (快速失败)
    "retry_backoff_factor": 1,      # N/A
    "retry_initial_delay": 0.0,     # N/A
}
```

### 5.3 沙箱与生产配置差异

| 配置键 | 沙箱值 | 生产值 | 差异 |
|--------|--------|--------|------|
| `timeout_seconds` | 60 | 30 | ✅ 不同 |
| `audit_timeout_seconds` | 60 | 30 | ✅ 不同 |
| `log_level` | "DEBUG" | "INFO" | ✅ 不同 |
| `retry_max` | 0 | 3 | ✅ 不同 |
| `retry_backoff_factor` | 1 | 2 | ✅ 不同 |
| `retry_initial_delay` | 0.0 | 1.0 | ✅ 不同 |
| `audit_log_dir` | None | "prod_audit_logs/" | ✅ 不同 |
| `service_discovery_url` | None | None | 相同 (生产可配置) |
| `token_auth_enabled` | False | False | 相同 (生产可配置) |
| `token_path` | None | None | 相同 (生产可配置) |

### 5.4 沙箱模式回归验证

沙箱模式必须产生与 V4 完全相同的结果：

| 验证项 | V4 值 | V5 沙箱值 | 一致性 |
|--------|-------|-----------|--------|
| 超时 | 60s | 60s | ✅ 一致 |
| 日志级别 | (无) | DEBUG | ✅ 沙箱默认 |
| 重试次数 | (无) | 0 | ✅ 无重试 |
| PERF-GUARD 阈值 | 60s | 60s | ✅ 一致 |
| PERF-GUARD 告警 | 45s | 45s | ✅ 一致 |
| DS-06 窗口 | 15min | 15min | ✅ 一致 |
| DS-06 切换阈值 | 2 | 2 | ✅ 一致 |
| ROB-01 重试 | 3 | 3 | ✅ 一致 |
| REG-06 矩阵 | ERROR→FAIL | ERROR→FAIL | ✅ 一致 |
| 13 项检查 | 13 | 13 | ✅ 一致 |

---

## 6. 服务发现集成

### 6.1 设计概述

生产环境需要服务发现能力来动态定位依赖服务。V5 提供服务发现的框架接口，当前为 Mock 实现，待生产环境配置真实端点后可启用。

### 6.2 服务发现流程

```
_apply_env_config(config, "prod")
    │
    ▼
_gate_pre_check._setup_production_components()
    │
    ▼
_setup_service_discovery(config)
    │
    ├── service_discovery_url == None
    │   └── 记录 "Service discovery URL not configured"
    │
    └── service_discovery_url != None
        ├── 设置 enabled=True
        ├── 记录 discovery_url
        └── Mock 发现服务列表:
            - evidence-auditor (http://hermes-auditor.svc:8080)
            - dep-registry (http://dep-registry.svc:9090)
            - dshb-api (http://dshb-api.svc:7070)
```

### 6.3 Mock 服务发现实现

当前 `_setup_service_discovery()` 返回 Mock 服务列表：

```python
mock_services = [
    {"name": "evidence-auditor", "url": "http://hermes-auditor.svc:8080", "status": "healthy"},
    {"name": "dep-registry", "url": "http://dep-registry.svc:9090", "status": "healthy"},
    {"name": "dshb-api", "url": "http://dshb-api.svc:7070", "status": "healthy"},
]
```

### 6.4 服务发现配置

在 `PRODUCTION_CONFIG` 中启用：

```python
# 在 DEFAULT_CONFIG 中修改
"production": {
    "service_discovery_url": "http://service-registry.internal:8500/discover",
    # ... 其他配置
}
```

### 6.5 服务发现状态输出

服务发现状态存储在 `config["_service_discovery"]` 中：

```json
{
    "enabled": true,
    "discovery_url": "http://service-registry.internal:8500/discover",
    "services_found": [
        {"name": "evidence-auditor", "url": "...", "status": "healthy"},
        {"name": "dep-registry", "url": "...", "status": "healthy"}
    ],
    "service_count": 2,
    "error": null
}
```

---

## 7. Token 鉴权设计

### 7.1 设计概述

生产环境可能需要基于 Token 的认证机制。V5 提供 Token 鉴权的框架接口，当前默认关闭，可通过配置启用。

### 7.2 Token 鉴权流程

```
_apply_env_config(config, "prod")
    │
    ▼
_gate_pre_check._setup_production_components()
    │
    ▼
_setup_production_auth(config)
    │
    ├── token_auth_enabled == False
    │   └── 记录 "Token authentication not enabled"
    │
    └── token_auth_enabled == True
        ├── token_path == None
        │   └── 记录 "token_path not configured"
        │
        └── token_path != None
            ├── 文件存在性检查
            ├── JSON 解析 (支持 JSON 和纯文本格式)
            ├── Token 提取 (token 或 access_token 字段)
            └── Token 存储在 config["_auth_token"]
```

### 7.3 Token 文件格式

支持两种格式：

**JSON 格式**（推荐）:
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_at": "2026-09-30T23:59:59"
}
```

**纯文本格式**:
```
eyJhbGciOiJIUzI1NiIs...
```

### 7.4 Token 鉴权启用配置

在 `DEFAULT_CONFIG` 中启用：

```python
"production": {
    "token_auth_enabled": True,
    "token_path": "/path/to/token.json",
    # ... 其他配置
}
```

### 7.5 Token 鉴权状态输出

Token 鉴权状态存储在 `config["_auth_status"]` 中：

```json
{
    "enabled": true,
    "token_loaded": true,
    "token_path": "/path/to/token.json",
    "token_preview": "eyJhbG...",
    "token_expires": "2026-09-30T23:59:59",
    "error": null
}
```

---

## 8. 超时与重试策略

### 8.1 超时控制

| 环境 | 超时设置 | 审计超时 | 说明 |
|------|----------|----------|------|
| 沙箱 | 60s | 60s | 与 V4 相同，宽松调试 |
| 生产 | 30s | 30s | 严格故障发现 |

超时应用于：
- `AuditValidator.validate()` 的 `subprocess.run(timeout=...)`
- `AuditValidator` 初始化时的 `timeout_seconds` 参数

### 8.2 重试策略

生产环境使用指数退避重试策略：

```
重试次数 N: 延迟 = initial_delay × (backoff_factor ^ N)

N=0: 1.0s × (2^0) = 1.0s
N=1: 1.0s × (2^1) = 2.0s
N=2: 1.0s × (2^2) = 4.0s
N=3: 1.0s × (2^3) = 8.0s (超出 max_retries=3，不执行)
```

### 8.3 重试函数

`_create_retry_delay(config, attempt)` 计算重试延迟：

```python
def _create_retry_delay(config, attempt):
    initial_delay = config.get("retry_initial_delay", 1.0)
    backoff_factor = config.get("retry_backoff_factor", 2)
    return initial_delay * (backoff_factor ** attempt)
```

### 8.4 重试适用场景

重试策略适用于以下生产操作（当前为框架预留，实际实现待后续版本）：

- 服务发现 HTTP 调用
- Token 刷新
- 审计器远程调用
- 外部 API 调用

### 8.5 沙箱重试行为

沙箱环境 `retry_max=0`，不执行重试，快速失败。

---

## 9. 生产审计日志

### 9.1 设计概述

生产环境使用独立的审计日志目录，与沙箱完全隔离。

### 9.2 ProductionAuditLogger 类

```python
class ProductionAuditLogger:
    def __init__(self, audit_log_dir, work_dir):
        # audit_log_dir: "prod_audit_logs/"
        # work_dir: 工作目录
        # 创建日志目录并生成日志文件
        # 文件名格式: prod_audit_YYYYMMDD_HHMMSS.jsonl

    def log(self, event_type, data, level="INFO"):
        # 追加 JSONL 格式日志条目

    def get_log_path(self):
        # 返回日志文件路径

    def get_log_size(self):
        # 返回日志文件大小 (字节)
```

### 9.3 日志文件结构

日志文件为 JSONL 格式（每行一个 JSON 对象）：

```json
{"timestamp": "2026-08-31T14:30:00.123456", "level": "INFO", "event_type": "GATE_CHECK_STARTED", "data": {"env": "prod", "work_dir": "..."}}
{"timestamp": "2026-08-31T14:30:05.789012", "level": "WARN", "event_type": "TIMEOUT_WARNING", "data": {"timeout": 30}}
```

### 9.4 日志目录

| 环境 | 日志目录 | 说明 |
|------|----------|------|
| 沙箱 | 无（V4 兼容） | 审计日志写入工作目录 |
| 生产 | `prod_audit_logs/` | 独立审计日志目录 |

### 9.5 日志初始化条件

`ProductionAuditLogger` 仅在 `env == "prod"` 时初始化：

```python
if self.env == "prod":
    audit_log_dir = self.config.get("production", {}).get("audit_log_dir", "prod_audit_logs/")
    self.prod_audit_logger = ProductionAuditLogger(audit_log_dir, self.work_dir)
else:
    self.prod_audit_logger = None
```

---

## 10. CLI 参数说明

### 10.1 参数列表

| 参数 | 格式 | 默认值 | 说明 |
|------|------|--------|------|
| `--work-dir` | `--work-dir <path>` | 脚本目录 | 工作目录路径 |
| `--strict` | `--strict` | False | 严格模式（FAIL 时返回非零退出码） |
| `--output` | `--output <path>` | 自动 | 报告输出路径 |
| `--audit-validate` | `--audit-validate` | False | 启用审计器联动 |
| `--audit-file` | `--audit-file <path>` | None | 审计证据包 JSON 路径 |
| `--audit-bypass` | `--audit-bypass` | False | 紧急旁路开关 |
| **`--env`** | **`--env <value>`** | **sandbox** | **环境分支: sandbox 或 prod** |
| **`--self-test`** | **`--self-test`** | **False** | **运行自检测试套件** |

### 10.2 --env 参数

**格式**:
- `--env sandbox` (两参数格式)
- `--env=sandbox` (等号格式)

**有效值**:
- `sandbox` — 沙箱环境（默认，V4 兼容）
- `prod` — 生产环境

**无效值**: 打印错误信息并退出

**示例**:
```bash
# 沙箱模式（默认）
python3 gate_pre_check_auto_v5.py

# 沙箱模式（显式）
python3 gate_pre_check_auto_v5.py --env sandbox
python3 gate_pre_check_auto_v5.py --env=sandbox

# 生产模式
python3 gate_pre_check_auto_v5.py --env prod
python3 gate_pre_check_auto_v5.py --env=prod

# 生产模式 + 严格 + 审计联动
python3 gate_pre_check_auto_v5.py --env=prod --strict --audit-validate
```

### 10.3 --self-test 参数

运行 V5 自检测试套件，验证：
- 沙箱模式 V4 兼容性
- 生产配置隔离
- 环境切换功能
- 全部 13 项检查可用性
- 重试延迟计算

```bash
python3 gate_pre_check_auto_v5.py --self-test
```

### 10.4 参数组合示例

```bash
# 示例 1: 沙箱标准检查
python3 gate_pre_check_auto_v5.py --env=sandbox

# 示例 2: 生产严格检查 + 审计联动
python3 gate_pre_check_auto_v5.py --env=prod --strict --audit-validate

# 示例 3: 生产检查 + 指定工作目录 + 紧急旁路
python3 gate_pre_check_auto_v5.py --env=prod --work-dir /path/to/workdir --audit-bypass

# 示例 4: 沙箱检查 + 自定义报告路径
python3 gate_pre_check_auto_v5.py --env=sandbox --output /path/to/report.md

# 示例 5: 自检
python3 gate_pre_check_auto_v5.py --self-test
```

---

## 11. 配置示例

### 11.1 默认配置（沙箱）

```python
DEFAULT_CONFIG = {
    "env": "sandbox",
    "production": {
        "timeout_seconds": 30,
        "audit_timeout_seconds": 30,
        "log_level": "INFO",
        "audit_log_dir": "prod_audit_logs/",
        "service_discovery_url": None,
        "token_auth_enabled": False,
        "token_path": None,
        "retry_max": 3,
        "retry_backoff_factor": 2,
        "retry_initial_delay": 1.0,
    },
    # ... V4 配置保留
}
```

### 11.2 生产环境配置（启用全部生产功能）

```python
config = {
    **DEFAULT_CONFIG,
    "env": "prod",
    "production": {
        "timeout_seconds": 30,
        "audit_timeout_seconds": 30,
        "log_level": "INFO",
        "audit_log_dir": "prod_audit_logs/",
        "service_discovery_url": "http://service-registry.internal:8500/discover",
        "token_auth_enabled": True,
        "token_path": "/etc/dshb/token.json",
        "retry_max": 3,
        "retry_backoff_factor": 2,
        "retry_initial_delay": 1.0,
    },
}
```

### 11.3 使用 apply_env_config 函数

```python
from gate_pre_check_auto_v5 import _apply_env_config, DEFAULT_CONFIG
from copy import deepcopy

# 沙箱配置
sandbox_config = deepcopy(DEFAULT_CONFIG)
_apply_env_config(sandbox_config, "sandbox")
print(f"Env: {sandbox_config['env']}, Timeout: {sandbox_config['timeout_seconds']}s")
# 输出: Env: sandbox, Timeout: 60s

# 生产配置
prod_config = deepcopy(DEFAULT_CONFIG)
_apply_env_config(prod_config, "prod")
print(f"Env: {prod_config['env']}, Timeout: {prod_config['timeout_seconds']}s")
# 输出: Env: prod, Timeout: 30s
```

### 11.4 Token 文件示例

```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": "2026-09-30T23:59:59",
    "issuer": "dshb-service-registry"
}
```

---

## 12. 兼容性分析

### 12.1 V4 兼容性矩阵

| 维度 | V4 行为 | V5 沙箱行为 | 兼容 |
|------|---------|-------------|------|
| CLI 参数 | 6 个参数 | 8 个参数（+2 新增） | ✅ 完全兼容 |
| 默认模式 | 无 env | 沙箱默认 | ✅ 行为相同 |
| 超时 | 60s | 60s | ✅ 一致 |
| 13 项检查 | 全部执行 | 全部执行 | ✅ 一致 |
| REG-06 修复 | ERROR→FAIL | ERROR→FAIL | ✅ 一致 |
| 紧急旁路 | 支持 | 支持 | ✅ 一致 |
| PERF-GUARD | 60s/45s | 60s/45s | ✅ 一致 |
| DS-06 | 15min/2次 | 15min/2次 | ✅ 一致 |
| ROB-01 | 优雅降级 | 优雅降级 | ✅ 一致 |
| 报告格式 | V4 格式 | V5 格式（+环境章节） | ✅ 向后兼容 |
| 报告文件名 | `..._v4.md` | `..._v5.md` | ✅ 不覆盖 |

### 12.2 代码兼容性

| 组件 | V4 | V5 | 兼容性 |
|------|----|----|--------|
| `DEFAULT_CONFIG` | 基础配置 | +env, +production | ✅ 增量 |
| `GATE_CHECKS` | 13 项 | 13 项 | ✅ 相同 |
| `AuditValidator` | 固定 60s | 可配置超时 | ✅ 增量 |
| `EmergencyBypassLogger` | V4 类 | 完整保留 | ✅ 相同 |
| `DepFlapDetector` | V4 类 | 完整保留 | ✅ 相同 |
| `GatePreCheck` | V4 引擎 | +环境分支 | ✅ 增量 |
| `parse_args()` | 6 参数 | 8 参数 | ✅ 增量 |
| `main()` | V4 主函数 | +环境配置 | ✅ 增量 |

### 12.3 文件兼容性

| 文件 | V4 行为 | V5 行为 | 兼容性 |
|------|---------|---------|--------|
| `gate_pre_check_auto_v4.py` | 存在 | **不修改** | ✅ 保留 |
| `gate_pre_check_auto_v5.py` | 不存在 | **新增** | ✅ 新增 |
| `..._v4.md` 报告 | 生成 | 不生成 | ✅ 保留 |
| `..._v5.md` 报告 | 不生成 | **生成** | ✅ 新增 |
| `audit_bypass_change_log.json` | 读写 | 读写（相同） | ✅ 兼容 |

### 12.4 零回归保证

V5 沙箱模式通过以下方式保证零回归：

1. **代码层面**: 所有 V4 检查方法、类、函数完整保留
2. **配置层面**: 沙箱配置保持 V4 默认值（timeout=60s, log=DEBUG）
3. **行为层面**: 沙箱模式不初始化任何生产组件
4. **测试层面**: `_run_self_test()` 验证沙箱模式 13 项检查全部可用
5. **报告层面**: V5 报告文件名不同（`_v5.md`），不覆盖 V4 报告

---

## 13. 迁移指南

### 13.1 从 V4 迁移到 V5

**沙箱用户**（大多数场景）:

```bash
# 之前 (V4)
python3 gate_pre_check_auto_v4.py

# 之后 (V5 沙箱模式 — 行为完全相同)
python3 gate_pre_check_auto_v5.py --env=sandbox
# 或省略 --env（默认 sandbox）
python3 gate_pre_check_auto_v5.py
```

**生产用户**（新增能力）:

```bash
# 之前 (V4 不支持生产模式)
# 无对应命令

# 之后 (V5 生产模式)
python3 gate_pre_check_auto_v5.py --env=prod

# 生产模式 + 严格 + 审计联动
python3 gate_pre_check_auto_v5.py --env=prod --strict --audit-validate
```

### 13.2 迁移步骤

1. **步骤 1**: 备份 V4 脚本（可选，V4 文件不会被修改）

2. **步骤 2**: 运行 V5 自检确认环境就绪
   ```bash
   python3 gate_pre_check_auto_v5.py --self-test
   ```

3. **步骤 3**: 沙箱模式验证（确认零回归）
   ```bash
   python3 gate_pre_check_auto_v5.py --env=sandbox
   # 对比 V4 报告与 V5 沙箱报告（检查项结果应一致）
   ```

4. **步骤 4**: 生产模式配置（如需）
   - 修改 `DEFAULT_CONFIG["production"]` 中的配置值
   - 设置 `service_discovery_url`（如需要服务发现）
   - 设置 `token_auth_enabled=True` + `token_path`（如需要 Token 鉴权）

5. **步骤 5**: 生产模式运行
   ```bash
   python3 gate_pre_check_auto_v5.py --env=prod --strict
   ```

### 13.3 回滚方案

如需回滚到 V4：

```bash
# 直接运行 V4 脚本（文件未被修改）
python3 gate_pre_check_auto_v4.py

# 或指定 V4 报告路径
python3 gate_pre_check_auto_v4.py --output v86_rc2_dshb_gate_auto_check_report_v4.md
```

V5 的 `--env=sandbox` 不会修改 V4 的任何文件或逻辑，因此回滚无风险。

### 13.4 配置迁移清单

| 配置项 | V4 值 | V5 沙箱值 | V5 生产值 | 迁移动作 |
|--------|-------|-----------|-----------|----------|
| `env` | (无) | sandbox | prod | 新增参数 |
| `timeout_seconds` | 60 (隐式) | 60 | 30 | 沙箱不变 |
| `audit_timeout_seconds` | 60 (隐式) | 60 | 30 | 沙箱不变 |
| `log_level` | (无) | DEBUG | INFO | 沙箱默认 |
| `retry_max` | (无) | 0 | 3 | 沙箱默认 |
| `production.audit_log_dir` | (无) | None | `prod_audit_logs/` | 生产新增 |
| `production.service_discovery_url` | (无) | None | None | 生产可配置 |
| `production.token_auth_enabled` | (无) | False | False | 生产可启用 |

---

## 14. 风险与缓解

### 14.1 风险矩阵

| # | 风险 | 影响 | 概率 | 缓解措施 |
|---|------|------|------|----------|
| R1 | 沙箱模式回归 | 检查失败 | 低 | `_run_self_test()` 验证 + 沙箱配置与 V4 完全一致 |
| R2 | 生产超时过短 | 误判超时 | 中 | 30s 基于生产 SLA 设定，可调大 |
| R3 | 配置混淆 | 环境串扰 | 低 | 完全独立的配置字典 + 自检验证 |
| R4 | 报告文件名冲突 | 覆盖 | 无 | V4/V5 使用不同文件名 |
| R5 | 服务发现不可用 | 功能缺失 | 中 | Mock 实现，生产端点待配置 |
| R6 | Token 鉴权未启用 | 安全缺口 | 中 | 框架预留，默认关闭需显式启用 |
| R7 | 重试策略未实现 | 功能缺失 | 高 | `_create_retry_delay()` 框架预留，实际重试逻辑待后续版本 |
| R8 | 生产审计日志权限 | 写入失败 | 低 | `ProductionAuditLogger` 静默降级 |

### 14.2 风险缓解策略

**R1: 沙箱模式回归**
- 缓解: `_run_self_test()` 中 TEST 1 和 TEST 4 专门验证沙箱模式
- 测试: 13 项检查全部可用 + V4 阈值全部保留
- 验证: 运行 `--self-test` 确认 24/24 通过

**R2: 生产超时过短**
- 缓解: 生产超时 30s 可在 `PRODUCTION_CONFIG` 中调整
- 建议: 初始部署使用 30s，根据实际审计耗时调整
- 监控: PERF-GUARD 提供审计耗时监控

**R3: 配置混淆**
- 缓解: `SANDBOX_CONFIG` 和 `PRODUCTION_CONFIG` 完全独立
- 测试: TEST 3 验证 7 个配置键差异
- 设计: `_apply_env_config()` 使用独立的配置字典

**R7: 重试策略未实现**
- 缓解: `_create_retry_delay()` 提供延迟计算函数
- 计划: 后续版本 (V6) 集成重试逻辑到审计器调用和服务发现

### 14.3 生产部署检查清单

- [ ] `gate_pre_check_auto_v5.py` 文件已部署
- [ ] `gate_pre_check_auto_v4.py` 文件保持不变（未修改）
- [ ] `--self-test` 运行通过（24/24）
- [ ] `--env=sandbox` 运行确认零回归
- [ ] `--env=prod` 运行确认生产配置生效
- [ ] `PRODUCTION_CONFIG` 中配置值符合生产环境要求
- [ ] `service_discovery_url` 已配置（如需要）
- [ ] `token_auth_enabled` 和 `token_path` 已配置（如需要）
- [ ] `prod_audit_logs/` 目录有写入权限
- [ ] 报告文件 `v86_rc2_dshb_gate_auto_check_report_v5.md` 生成正常

---

## 15. 附录

### 15.1 附录 A: 自检测试覆盖范围

| 测试编号 | 测试名称 | 覆盖项 |
|----------|----------|--------|
| TEST 1 | 沙箱模式 13 项检查 | 13 项检查、timeout=60s、log=DEBUG、retry=0 |
| TEST 2 | 生产配置隔离 | timeout=30s、log=INFO、retry=3、backoff=2、delay=1s |
| TEST 3 | 配置隔离验证 | sandbox≠prod、7 个键差异 |
| TEST 4 | V4 行为保留 | V4 阈值、REG-06 矩阵 |
| TEST 5 | 生产组件初始化 | env=prod、审计日志器、服务发现 |
| TEST 6 | 审计器环境超时 | sandbox=60s、prod=30s |
| TEST 7 | 13 项检查可用 | GATE_CHECKS 字典、13 个方法可调用 |
| TEST 8 | 环境切换 | sandbox→prod→sandbox |
| TEST 9 | 生产配置完整性 | 10 个配置键 |
| TEST 10 | 重试延迟计算 | 指数退避: 1s, 2s, 4s, 8s |

### 15.2 附录 B: 配置键完整列表

| 配置键 | 沙箱值 | 生产值 | 说明 |
|--------|--------|--------|------|
| `env` | "sandbox" | "prod" | 当前环境 |
| `timeout_seconds` | 60 | 30 | 操作超时 |
| `audit_timeout_seconds` | 60 | 30 | 审计超时 |
| `log_level` | "DEBUG" | "INFO" | 日志级别 |
| `audit_log_dir` | None | "prod_audit_logs/" | 审计日志目录 |
| `service_discovery_url` | None | None | 服务发现 URL |
| `token_auth_enabled` | False | False | Token 鉴权开关 |
| `token_path` | None | None | Token 文件路径 |
| `retry_max` | 0 | 3 | 最大重试 |
| `retry_backoff_factor` | 1 | 2 | 退避因子 |
| `retry_initial_delay` | 0.0 | 1.0 | 初始延迟 |
| `work_dir` | 脚本目录 | 脚本目录 | 工作目录 |
| `files` | V4 文件列表 | V4 文件列表 | 检查文件 |
| `thresholds` | V4 阈值 | V4 阈值 | 检查阈值 |
| `report_file` | `..._v5.md` | `..._v5.md` | 报告文件 |
| `auditor_path` | V4 路径 | V4 路径 | 审计器路径 |
| `audit_file` | None | None | 审计证据文件 |
| `audit_validate` | False | False | 审计联动开关 |
| `audit_service_emergency_bypass` | False | False | 紧急旁路开关 |
| `audit_bypass_approval` | None | None | 旁路审批者 |
| `audit_bypass_change_log` | [] | [] | 旁路变更日志 |
| `perf_guard_threshold_seconds` | 60 | 60 | PERF-GUARD 阈值 |
| `perf_guard_warn_seconds` | 45 | 45 | PERF-GUARD 告警 |
| `dep_flap_window_minutes` | 15 | 15 | DS-06 窗口 |
| `dep_flap_max_transitions` | 2 | 2 | DS-06 切换阈值 |
| `rob01_max_retries` | 3 | 3 | ROB-01 重试 |
| `gate_verdict_matrix` | V4 矩阵 | V4 矩阵 | Gate 判定矩阵 |
| `production` | (嵌套) | (嵌套) | 生产配置子字典 |

### 15.3 附录 C: 文件结构

```
dshb_gate_prod_fix/
├── gate_pre_check_auto_v4.py              # V4 脚本 (未修改)
├── gate_pre_check_auto_v5.py              # V5 脚本 (新增, ~2674 行)
├── v86_rc2_dshb_gate_auto_check_report_v4.md  # V4 报告
├── v86_rc2_dshb_gate_auto_check_report_v5.md  # V5 报告 (运行时生成)
├── audit_bypass_change_log.json            # 紧急旁路变更日志 (V4+V5 共用)
└── prod_audit_logs/                        # 生产审计日志目录 (运行时创建)
    └── prod_audit_YYYYMMDD_HHMMSS.jsonl   # 生产审计日志文件
```

### 15.4 附录 D: 版本标识

| 标识 | 值 |
|------|-----|
| 脚本版本 | V5.0 |
| 报告版本 | V5.0 |
| 工单编号 | DSHB_V86_RC2_RDEP07_GATE_PROD_PREP |
| 工单子项 | T3.2 |
| 约束 | NO_OVERWRITE=TRUE / NO_MODIFY_V85=TRUE / BRANCH_LOCKED=TRUE |
| 基线 | V4.0 (`gate_pre_check_auto_v4.py`) |
| 自检版本 | 24 项测试 |

### 15.5 附录 E: 变更日志

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| V5.0 | 2026-08-31 | 初版发布: 环境分支、生产配置、服务发现、Token 鉴权、重试策略、生产审计日志、自检函数 |

---

**文档结束**  
*编制: DSHB V86-RC2 Gate 团队*  
*工单: DSHB_V86_RC2_RDEP07_GATE_PROD_PREP / T3.2*
