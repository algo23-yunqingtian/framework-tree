# V86 异步任务调度接口方案

> 任务：`E_V85_READONLY_API_AND_V86_BACKEND_DESIGN` · T2.3
> 分支：`feature/v85-chart-template`
> 前置：`v86_backend_schema_design.md`（同目录，`task_run` 表）
> 未就绪依赖：`v86_init_backlog_total.md`（HERMES 产出，`DEPENDENCY_NOT_READY=TRUE`）
> 约束：设计仅涉及接口契约，不执行任何实际任务，不修改 V85 数据。

---

## 1. 设计目标

1. **提交**：客户端提交 DSHB 规则计算 / DSHE 别名解析 / Gate 全量回归等任务
2. **调度**：Worker 从队列认领、执行、回写状态
3. **查询**：客户端轮询任务状态与结果
4. **幂等**：同一 submit 请求（相同 payload + submitter）返回同一个 `task_id`
5. **可追溯**：每个任务绑定版本、payload、审计日志

---

## 2. 任务类型

| task_type | 说明 | 典型 payload |
|---|---|---|
| `dshb_rule_eval` | DSHB 规则计算：跑黑名单对一批模板/指标的组合判定 | `{template_ids: [...], blacklist_version: "v85-bl-final", output_format: "csv"}` |
| `dshe_alias_resolve` | DSHE 别名解析：把原始名解析为规范键 | `{alias_names: [...], engine_variant: "f3+f4", version_tag: "v86.0-alpha"}` |
| `dshe_canonical_resolve` | DSHE 规范键反查：给出规范键找所有关联别名 | `{canonical_keys: [...], include_rejected: false}` |
| `gate_full_run` | 全量 14 项 Gate 回归 | `{version_tag, engine_variant, case_set: "alias_test_case_set_v1"}` |
| `migration_verify` | V85→V86 迁移校验 | `{baseline_version: "f313570", target_version, thresholds: {...}}` |
| `risk_db_replay` | 重放 488 模板场景 A/B | `{template_count: 488, scenario: "A\|B\|both"}` |

---

## 3. 端点契约

### 3.1 `POST /api/v1/tasks`
- **角色**：`task_submit`（V86 专属，不复用 V85 portal_read）
- **幂等键**：`X-Idempotency-Key` header；同一 submitter + 相同 payload + 相同幂等键 → 返回原 `task_id`
- **请求**：
```json
{
  "task_type": "dshe_alias_resolve",
  "version_tag": "v86.0-alpha",
  "priority": 5,
  "payload": {
    "alias_names": ["COMEX:铜:主力合约:收盘价(日", "沪铜主力收盘价"],
    "engine_variant": "f3+f4"
  },
  "callback_url": "https://portal.internal/callbacks/task",
  "ttl_seconds": 3600
}
```
- **响应**（202 Accepted）：
```json
{
  "task_id": "TASK-DH-2026-10-01-00001",
  "task_type": "dshe_alias_resolve",
  "status": "queued",
  "priority": 5,
  "enqueued_at": "2026-10-01T16:20:00+08:00",
  "poll_after_seconds": 30,
  "poll_endpoint": "/api/v1/tasks/TASK-DH-2026-10-01-00001"
}
```

### 3.2 `GET /api/v1/tasks/{task_id}`
- **角色**：`task_read`
- **响应**：
```json
{
  "task_id": "TASK-DH-2026-10-01-00001",
  "task_type": "dshe_alias_resolve",
  "version_tag": "v86.0-alpha",
  "status": "running",
  "priority": 5,
  "progress": 42.50,
  "progress_msg": "resolved 425 / 1000 aliases",
  "submitter": "portal_service",
  "worker_id": "worker-03",
  "created_at": "2026-10-01T16:20:00+08:00",
  "enqueued_at": "2026-10-01T16:20:01+08:00",
  "started_at": "2026-10-01T16:20:15+08:00",
  "finished_at": null,
  "poll_after_seconds": 30
}
```

### 3.3 `GET /api/v1/tasks?status=&task_type=&submitter=&limit=&offset=`
- **角色**：`task_read`
- **用途**：批量查询
- **响应**：
```json
{
  "status_filter": "running",
  "task_type_filter": null,
  "rows": [...],
  "total": 12,
  "returned": 12,
  "limit": 50,
  "offset": 0
}
```

### 3.4 `GET /api/v1/tasks/{task_id}/result`
- **角色**：`task_read`
- **前置**：任务必须为 `succeeded`；否则 `409 TASK_NOT_READY`
- **响应**：
```json
{
  "task_id": "TASK-DH-2026-10-01-00001",
  "result_format": "json",
  "result": {
    "engine_variant": "f3+f4",
    "total": 2,
    "resolved": 2,
    "canonical": [
      {"alias": "COMEX:铜:主力合约:收盘价(日", "canonical_key": "cu_23_comex_close", "confidence": 0.92},
      {"alias": "沪铜主力收盘价", "canonical_key": "cu_23_comex_close", "confidence": 0.95}
    ],
    "unresolved": []
  },
  "result_ref": "s3://v86-results/2026/10/01/TASK-DH-2026-10-01-00001.json",
  "fetched_at": "2026-10-01T16:22:00+08:00"
}
```

### 3.5 `POST /api/v1/tasks/{task_id}/cancel`
- **角色**：`task_admin`
- **前置**：任务处于 `queued` / `running`；`succeeded`/`failed`/`cancelled` 状态返回 409
- **响应**：`{task_id, status: "cancelled", cancelled_at}`

### 3.6 `GET /api/v1/tasks/queue`
- **角色**：`task_admin`
- **用途**：查看队列深度、Worker 忙碌度、任务等待时间
- **响应**：
```json
{
  "queue_depth": 12,
  "queued": 8,
  "running": 4,
  "workers_total": 6,
  "workers_busy": 4,
  "oldest_queued_seconds": 45,
  "oldest_queued_task_id": "TASK-DH-2026-10-01-00012",
  "avg_wait_seconds_last_1h": 22.5
}
```

---

## 4. 状态机

```
                       +---------+
                       | queued  | <------------+
                       +---------+              |
                            |                   |
                            v                   |
                       +---------+              |
              +-------| running |-------+      |
              |       +---------+       |      |
              |           |             |      |
              v           v             v      |
       +-----------+  +---------+  +----------+|
       | succeeded |  | failed  |  | cancelled|--+
       +-----------+  +---------+  +----------+  |
                                |  +---------+   |
                                |  | timeout |   |
                                |  +---------+   |
                                |       |        |
                                |       +--------+  retry
                                +-----------------+
```

- `queued → running`：Worker 认领
- `running → succeeded/failed/cancelled/timeout`：终态
- `failed/timeout` 可 retry（`retry_count` 递增，最大 3 次；否则进入人工介入队列）
- `succeeded` 状态不可变；重试走新 `task_id`

---

## 5. Worker 认领协议

### 5.1 拉取任务（Long Polling 简化版）
```python
def claim_task(worker_id, task_types=None, timeout_seconds=30):
    """Worker 从队列认领一个任务。timeout_seconds 内无任务返回 None。"""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        task = db.execute("""
            UPDATE task_run SET status='running', worker_id=?, started_at=NOW(),
                               progress_msg='claimed by ' || ?
            WHERE id = (
                SELECT id FROM task_run
                WHERE status='queued'
                  AND (task_type IS NULL OR task_type = ANY(?))
                ORDER BY priority ASC, enqueued_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            RETURNING id, task_type, payload, version_tag, priority
        """, [worker_id, worker_id, task_types])
        if task:
            return task
        time.sleep(min(1, deadline - time.time()))
    return None
```

### 5.2 进度回写
```python
def report_progress(task_id, progress_pct, msg):
    db.execute("""
        UPDATE task_run SET progress=?, progress_msg=? WHERE task_id=?
    """, [progress_pct, msg, task_id])
```

### 5.3 完成回写
```python
def complete_task(task_id, result, result_ref=None):
    db.execute("""
        UPDATE task_run SET status='succeeded', progress=100, finished_at=NOW(),
                            result_ref=?, progress_msg='done'
        WHERE task_id=? AND status='running' AND worker_id=?
    """, [result_ref, task_id, current_worker_id()])
    # 写入结果对象存储（S3 / 本地文件）
    # 写审计日志
```

### 5.4 失败回写
```python
def fail_task(task_id, error_msg, retryable=True):
    task = db.query("SELECT * FROM task_run WHERE task_id=?", [task_id])
    if retryable and task["retry_count"] < 3:
        db.execute("""
            UPDATE task_run SET status='queued', retry_count=retry_count+1,
                                error=?, worker_id=NULL, started_at=NULL,
                                enqueued_at=NOW()
            WHERE task_id=?
        """, [error_msg, task_id])
    else:
        db.execute("""
            UPDATE task_run SET status='failed', error=?, finished_at=NOW()
            WHERE task_id=?
        """, [error_msg, task_id])
```

---

## 6. 幂等设计

### 6.1 幂等键计算
```python
def compute_idempotency_key(submitter, task_type, payload):
    body = f"{submitter}|{task_type}|{json.dumps(payload, sort_keys=True, ensure_ascii=False)}"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:32]
```

### 6.2 幂等检查
- 客户端提交任务时，服务器根据 `submitter + task_type + payload` 计算幂等键
- 若 `X-Idempotency-Key` 与之一致，且存在同键的近期任务（TTL 内），直接返回既有 `task_id`
- 若 key 不同但 payload 相同，视为新任务（可能客户端 bug），仍创建

### 6.3 TTL
- 幂等记录默认 TTL = 24 小时
- 超时后同一 payload 会创建新任务

---

## 7. 与只读接口的集成

### 7.1 结果通过只读接口暴露

`migration_verify` 与 `risk_db_replay` 任务产出 CSV/JSON 后，写入 V86 输出目录（例如 `analysis/e2e_output/v86/migration_verify/<task_id>/result.csv`），并注册到 V86 制品白名单，客户端可通过 `ArtifactAPI.get_file("migration_verify_result", version="v86.0-alpha")` 拉取。

**好处**：
- 结果与执行解耦，重跑不影响原结果
- 客户端可以本地缓存，减少 API 调用
- 审计链：`task_run` → `result_ref` → 只读接口 → 审计日志

### 7.2 任务 payload 引用只读制品

任务 payload 里可以引用 V85 只读制品，例如：
```json
{
  "task_type": "migration_verify",
  "payload": {
    "baseline_artifact": {"kind": "risk_db", "version": "f313570", "md5": "819cb85a..."},
    "target_artifact": {"kind": "risk_db_v86", "version": "v86.0-alpha"}
  }
}
```

Worker 执行时通过 `ArtifactAPI.verify_artifact_md5()` 校验基线一致性，MD5 不匹配直接 `failed`（不重试，属于配置错误）。

---

## 8. 回调与通知

### 8.1 主动回调
- 客户端在提交时提供 `callback_url`
- 任务进入终态（`succeeded`/`failed`/`cancelled`/`timeout`）时，服务端 POST 回调
- 回调 body：`{task_id, status, result_ref, finished_at}`
- 失败重试：3 次指数退避（1s/5s/30s）；仍失败则记入审计日志

### 8.2 长轮询替代
- 客户端不提供 `callback_url` 时，服务端要求客户端按 `poll_after_seconds` 主动拉
- `poll_after_seconds` 默认 30，任务即将完成时缩短到 5

---

## 9. 速率限制与配额

| 维度 | 限制 |
|---|---|
| 单 submitter 每分钟提交 | 30 次 |
| 全局每分钟提交 | 200 次 |
| 单任务 payload 大小 | ≤ 4 MiB |
| 单任务并发子任务数 | ≤ 16 |
| 优先级抢占 | priority 1 的任务可打断 priority ≥ 7 的任务（可选，默认关闭） |
| 任务 TTL | 默认 3600 秒（可配置，最大 86400） |

---

## 10. 错误响应

统一错误格式与 V85 只读接口一致（`error: true / code / message / detail / timestamp`）。

| 状态码 | code | 场景 |
|---|---|---|
| 400 | `BAD_PAYLOAD` / `UNKNOWN_TASK_TYPE` / `MISSING_REQUIRED_FIELD` | 参数错误 |
| 401 | `NO_TOKEN` / `BAD_TOKEN` | 认证失败 |
| 403 | `ROLE_FORBIDDEN` / `SUBMITTER_NOT_ALLOWED` | 权限不足 |
| 404 | `TASK_NOT_FOUND` | 任务不存在 |
| 409 | `TASK_NOT_READY` / `TASK_ALREADY_TERMINAL` / `VERSION_NOT_FOUND` | 状态冲突 |
| 412 | `PRECONDITION_FAILED` | 基线制品 MD5 不匹配 |
| 422 | `PAYLOAD_UNACCEPTABLE` | payload 过大 / 缺字段 |
| 429 | `RATE_LIMIT` | 提交过快 |
| 503 | `QUEUE_FULL` / `NO_WORKER_AVAILABLE` | 系统不可用 |

---

## 11. 与 V85 只读接口的边界

| 维度 | V85 只读接口 | V86 任务接口 |
|---|---|---|
| 方法 | GET only | GET + POST |
| 版本 | V85 冻结（`f313570`） | V86 演进（`v86.0-alpha`...） |
| 数据 | 只读冻结产物 | 写入 task_run / 结果对象 |
| 认证角色 | `portal_read` / `audit_read` / `ops_read` | `task_submit` / `task_read` / `task_admin` |
| 网络 | 进程内 | 进程内 + Worker 通信 |
| 是否调用 zhiji API | ❌ | ❌ |
| 是否修改业务结果 | ❌ | ✅（写入 task_run 表 + 结果对象） |

**关键分离**：
- V85 接口永远只读，是"数据源"
- V86 任务接口读 V85、写 V86，是"计算层"
- V86 结果通过只读接口对外暴露，是"输出层"

---

## 12. 部署拓扑（示意）

```
┌─────────────┐   POST /tasks    ┌──────────────┐
│  Client     │ ───────────────> │ API Server   │
│ (portal)    │ <─────────────── │ (FastAPI)    │
└─────────────┘   GET /tasks/{id}└──────┬───────┘
                                        │
                                        │ SELECT ... SKIP LOCKED
                                        │
                                        v
                                 ┌──────────────┐
                                 │ PostgreSQL   │
                                 │ task_run 表  │
                                 └──────┬───────┘
                                        │
                                        │ claim_task()
                                        v
                                 ┌──────────────┐      ┌────────────┐
                                 │ Worker 01-06 │ ───> │ Result Store│
                                 └──────┬───────┘      │ (S3/local) │
                                        │              └────────────┘
                                        │ write progress
                                        v
                                 ┌──────────────┐
                                 │ audit_log    │
                                 └──────────────┘
```

---

## 13. 与 `v86_backend_schema_design.md` 的关系

- 本方案**依赖** `task_run` 表（`v86_backend_schema_design.md` §3.3）
- 本方案**写入** `audit_log` 表（§3.4）
- 本方案**引用** `config_snapshot` 表（§3.5）校验基线一致性
- 本方案**产出**结果对象，注册到 V86 只读制品白名单

---

## 14. 未覆盖事项（明确非目标）

1. **无消息队列（Kafka/RabbitMQ）**：任务量预计 ≤ 1000/天，用数据库 SKIP LOCKED 足够
2. **无分布式 tracing**：V86 面向内部，`task_id` 作为关联键
3. **无任务优先级抢占**：默认关闭，如需启用走配置项
4. **无跨集群调度**：单集群部署
5. **无实时流**：任务都是批处理，非流式
6. **无自动重试策略可配置**：固定 3 次重试，`retryable` 由 Worker 上报决定

---

## 15. 依赖声明

| 依赖 | 状态 | 影响 |
|---|---|---|
| `v86_init_backlog_total.md` | **未就绪**（HERMES 产出） | 若 backlog 引入新的 task_type，走 `ADD rule_kind` 增量扩展；不改本方案 |
| `v86_backend_schema_design.md` | 已交付（同目录） | `task_run` 表结构已定义 |
| V85 只读接口 | 已交付（同目录） | 任务 payload 引用只读制品 |

---

## 16. 约束合规

- ✅ 不修改 V85 冻结数据
- ✅ 不调用 zhiji API
- ✅ 本方案仅定义接口契约，不落地任何执行代码
- ✅ 分支锁定 `feature/v85-chart-template`
- ✅ 只新增设计文档
