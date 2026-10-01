# -*- coding: utf-8 -*-
"""
alias_task_adapter.py
==========================================================================
V86 别名引擎任务适配层 — 对齐 V86 异步任务接口规范
==========================================================================

任务: DSHE_V86_ALIAS_ENGINE_PROTOTYPE_AND_CONFLICT_REGRESSION · T2.4
分支: feature/v85-chart-template
前置: analysis/e2e_output/v85/e_api_design/v86_task_api_design.md

适配目标:
  将 V86AliasEngine 原型封装为 V86 异步任务接口规范 (§2 dshe_alias_resolve),
  支持后端提交任务、返回判定结果、错误上报。

接口对齐:
  - task_type: "dshe_alias_resolve"
  - payload: {alias_names: [...], engine_variant: "f3+f4", version_tag: "v86.0-alpha"}
  - result: {total, resolved, canonical: [...], unresolved: [...]}
  - error: 统一格式 {error, code, message, detail, timestamp}

约束:
  - 只读加载 V85 引擎 (exec build_alias_library.py)
  - 不修改任何 V85 冻结数据
  - 不调用 zhiji API
  - 不覆盖 V85 交付物

用法:
  from alias_task_adapter import AliasTaskAdapter, TASK_TYPE

  adapter = AliasTaskAdapter(engine_variant="f3+f4")
  task = adapter.create_task(payload)
  result = adapter.execute_task(task)
  print(result)

  # CLI 冒烟
  python alias_task_adapter.py --smoke
"""

import os
import sys
import json
import time
import datetime
import hashlib
import uuid
from copy import deepcopy
from collections import Counter

# 添加原型目录到路径
CD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CD)

from v86_alias_engine_prototype import (
    V86AliasEngine,
    TASK_ID,
    BASE_COMMIT,
    E_COMMIT,
)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

TASK_TYPE = "dshe_alias_resolve"
SUPPORTED_VARIANTS = ("base", "f3", "f3+f4")
DEFAULT_VARIANT = "f3+f4"
DEFAULT_VERSION_TAG = "v86.0-alpha"
TASK_ID_PREFIX = "TASK-AH-"
TASK_ID_DATE_FMT = "%Y-%m-%d"

# 状态机 (对齐 v86_task_api_design.md §4)
STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_SUCCEEDED = "succeeded"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"
STATUS_TIMEOUT = "timeout"
TERMINAL_STATUSES = (STATUS_SUCCEEDED, STATUS_FAILED, STATUS_CANCELLED, STATUS_TIMEOUT)

# 错误码 (对齐 v86_task_api_design.md §10)
ERR_BAD_PAYLOAD = "BAD_PAYLOAD"
ERR_UNKNOWN_TASK_TYPE = "UNKNOWN_TASK_TYPE"
ERR_MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
ERR_TASK_NOT_FOUND = "TASK_NOT_FOUND"
ERR_TASK_NOT_READY = "TASK_NOT_READY"
ERR_TASK_ALREADY_TERMINAL = "TASK_ALREADY_TERMINAL"
ERR_PAYLOAD_UNACCEPTABLE = "PAYLOAD_UNACCEPTABLE"
ERR_ENGINE_INIT_FAILED = "ENGINE_INIT_FAILED"
ERR_ENGINE_DECIDE_FAILED = "ENGINE_DECIDE_FAILED"
ERR_RATE_LIMIT = "RATE_LIMIT"
ERR_INTERNAL_ERROR = "INTERNAL_ERROR"

# 速率限制 (对齐 v86_task_api_design.md §9)
MAX_PAYLOAD_BYTES = 4 * 1024 * 1024          # 4 MiB
MAX_TASK_TTL_SECONDS = 86400                # 24h
DEFAULT_TASK_TTL_SECONDS = 3600             # 1h
MAX_CONCURRENT_SUBTASKS = 16


# ---------------------------------------------------------------------------
# 错误处理
# ---------------------------------------------------------------------------

class TaskError(Exception):
    """任务执行错误, 携带统一错误码."""

    def __init__(self, code, message, detail=None, http_status=400):
        self.code = code
        self.message = message
        self.detail = detail
        self.http_status = http_status
        super().__init__(message)

    def to_dict(self):
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }


# ---------------------------------------------------------------------------
# 任务适配器
# ---------------------------------------------------------------------------

class AliasTaskAdapter:
    """V86 别名引擎任务适配层.

    封装 V86AliasEngine, 对齐 V86 异步任务接口规范 (§2 dshe_alias_resolve).
    支持任务创建、执行、结果查询、错误上报.

    参数:
      engine_variant: "base" | "f3" | "f3+f4" (默认 "f3+f4")
      version_tag: 版本标签 (默认 "v86.0-alpha")
      lazy_init: True 时首次执行才加载引擎 (节省初始化时间)
    """

    def __init__(self, engine_variant=DEFAULT_VARIANT, version_tag=DEFAULT_VERSION_TAG,
                 lazy_init=False):
        if engine_variant not in SUPPORTED_VARIANTS:
            raise TaskError(ERR_BAD_PAYLOAD,
                            "engine_variant must be one of %s" % (SUPPORTED_VARIANTS,),
                            http_status=400)

        self.engine_variant = engine_variant
        self.version_tag = version_tag
        self.lazy_init = lazy_init
        self._engine = None
        self._task_registry = {}      # task_id -> task dict
        self._task_seq = 0
        self._submit_history = []     # 幂等检查用

    # ----- 引擎生命周期 -----

    @property
    def engine(self):
        """懒加载引擎."""
        if self._engine is None:
            try:
                self._engine = V86AliasEngine(self.engine_variant)
            except Exception as e:
                raise TaskError(ERR_ENGINE_INIT_FAILED,
                                "Failed to initialize V86AliasEngine: %s" % str(e),
                                detail={"variant": self.engine_variant,
                                        "error": str(e)},
                                http_status=503)
        return self._engine

    # ----- 幂等键 -----

    def compute_idempotency_key(self, submitter, task_type, payload):
        """计算幂等键 (SHA256[:32], 对齐 v86_task_api_design.md §6.1)."""
        body = "%s|%s|%s" % (submitter, task_type,
                              json.dumps(payload, sort_keys=True, ensure_ascii=False))
        return hashlib.sha256(body.encode("utf-8")).hexdigest()[:32]

    def check_idempotency(self, idempotency_key, submitter):
        """检查幂等键是否已存在 (TTL 内). 返回既有 task_id 或 None."""
        for entry in self._submit_history:
            if (entry["idempotency_key"] == idempotency_key and
                    entry["submitter"] == submitter and
                    time.time() - entry["submitted_at"] < 24 * 3600):
                return entry["task_id"]
        return None

    # ----- 任务创建 -----

    def create_task(self, payload, submitter="anonymous", priority=5,
                    callback_url=None, ttl_seconds=DEFAULT_TASK_TTL_SECONDS,
                    idempotency_key=None):
        """创建任务 (对齐 POST /api/v1/tasks).

        payload 示例:
          {
            "alias_names": ["COMEX:铜:主力合约:收盘价(日", "沪铜主力收盘价"],
            "engine_variant": "f3+f4",
            "version_tag": "v86.0-alpha"
          }

        返回: task dict (包含 task_id, status, payload, ...).
        """
        # 校验 task_type
        task_type = TASK_TYPE

        # 校验 payload
        if not isinstance(payload, dict):
            raise TaskError(ERR_BAD_PAYLOAD, "payload must be a JSON object",
                            http_status=400)

        payload_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if len(payload_bytes) > MAX_PAYLOAD_BYTES:
            raise TaskError(ERR_PAYLOAD_UNACCEPTABLE,
                            "payload exceeds %d bytes" % MAX_PAYLOAD_BYTES,
                            http_status=422)

        # 提取必需字段
        alias_names = payload.get("alias_names", [])
        if not isinstance(alias_names, list) or len(alias_names) == 0:
            raise TaskError(ERR_MISSING_REQUIRED_FIELD,
                            "payload.alias_names is required and must be a non-empty list",
                            http_status=400)

        # 校验引擎变体
        req_variant = payload.get("engine_variant", self.engine_variant)
        if req_variant not in SUPPORTED_VARIANTS:
            raise TaskError(ERR_BAD_PAYLOAD,
                            "engine_variant must be one of %s" % (SUPPORTED_VARIANTS,),
                            http_status=400)

        req_version = payload.get("version_tag", self.version_tag)
        if not isinstance(req_version, str) or not req_version.strip():
            raise TaskError(ERR_MISSING_REQUIRED_FIELD,
                            "payload.version_tag is required",
                            http_status=400)

        # TTL 校验
        if ttl_seconds > MAX_TASK_TTL_SECONDS:
            ttl_seconds = MAX_TASK_TTL_SECONDS

        # 幂等检查
        if idempotency_key:
            existing_id = self.check_idempotency(idempotency_key, submitter)
            if existing_id:
                return deepcopy(self._task_registry[existing_id])

        # 生成 task_id
        self._task_seq += 1
        date_str = datetime.datetime.utcnow().strftime(TASK_ID_DATE_FMT)
        task_id = "%s%s-%05d" % (TASK_ID_PREFIX, date_str, self._task_seq)

        # 记录幂等
        if idempotency_key:
            self._submit_history.append({
                "idempotency_key": idempotency_key,
                "submitter": submitter,
                "task_id": task_id,
                "submitted_at": time.time(),
            })

        # 创建任务
        task = {
            "task_id": task_id,
            "task_type": task_type,
            "version_tag": req_version,
            "status": STATUS_QUEUED,
            "priority": priority,
            "progress": 0.0,
            "progress_msg": "queued",
            "submitter": submitter,
            "worker_id": None,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "enqueued_at": datetime.datetime.utcnow().isoformat() + "Z",
            "started_at": None,
            "finished_at": None,
            "poll_after_seconds": 30,
            "payload": payload,
            "result": None,
            "error": None,
            "retry_count": 0,
            "ttl_seconds": ttl_seconds,
            "callback_url": callback_url,
        }
        self._task_registry[task_id] = task
        return deepcopy(task)

    # ----- 任务执行 -----

    def execute_task(self, task_or_id, worker_id="worker-00"):
        """执行任务 (对齐 Worker 认领协议 §5.1).

        task_or_id: task dict 或 task_id 字符串.
        返回: task dict (更新后的状态 + 结果).
        """
        if isinstance(task_or_id, str):
            task_id = task_or_id
            if task_id not in self._task_registry:
                raise TaskError(ERR_TASK_NOT_FOUND,
                                "Task %s not found" % task_id,
                                http_status=404)
            task = deepcopy(self._task_registry[task_id])
        else:
            task = deepcopy(task_or_id)
            task_id = task["task_id"]

        # 状态检查
        if task["status"] in TERMINAL_STATUSES:
            raise TaskError(ERR_TASK_ALREADY_TERMINAL,
                            "Task %s already in terminal state %s" % (task_id, task["status"]),
                            http_status=409)

        # 标记为 running
        task["status"] = STATUS_RUNNING
        task["worker_id"] = worker_id
        task["started_at"] = datetime.datetime.utcnow().isoformat() + "Z"
        task["progress_msg"] = "claimed by %s" % worker_id
        self._task_registry[task_id] = deepcopy(task)

        # 执行别名解析
        payload = task["payload"]
        alias_names = payload.get("alias_names", [])
        engine_variant = payload.get("engine_variant", self.engine_variant)
        version_tag = payload.get("version_tag", self.version_tag)

        try:
            # 确保使用正确的引擎变体
            if self.engine_variant != engine_variant:
                eng = V86AliasEngine(engine_variant)
            else:
                eng = self.engine

            results = []
            unresolved = []
            total = len(alias_names)

            for i, alias_name in enumerate(alias_names):
                if not isinstance(alias_name, str) or not alias_name.strip():
                    unresolved.append({
                        "alias": alias_name,
                        "reason": "empty_or_invalid",
                    })
                    continue

                try:
                    resolve_result = eng.resolve(alias_name)
                    state = resolve_result["state"]
                    canonicals = resolve_result["canonicals"]

                    if state == "UNIQUE":
                        results.append({
                            "alias": alias_name,
                            "canonical_key": canonicals[0],
                            "confidence": 0.95,
                            "state": state,
                        })
                    elif state == "AMBIGUOUS":
                        results.append({
                            "alias": alias_name,
                            "canonical_key": canonicals[0],
                            "confidence": round(1.0 / len(canonicals), 4),
                            "state": state,
                            "all_canonicals": canonicals,
                            "ambiguity_ratio": resolve_result.get("ambiguity_ratio", 0.0),
                        })
                        unresolved.append({
                            "alias": alias_name,
                            "reason": "ambiguous_multi_canonical",
                            "canonicals": canonicals,
                        })
                    else:
                        # UNREGISTERED or NO_MATCH
                        unresolved.append({
                            "alias": alias_name,
                            "reason": state.lower(),
                        })

                except Exception as e:
                    unresolved.append({
                        "alias": alias_name,
                        "reason": "engine_error",
                        "error": str(e),
                    })

                # 更新进度
                progress = round(100.0 * (i + 1) / max(1, total), 2)
                task["progress"] = progress
                task["progress_msg"] = "resolved %d / %d aliases" % (i + 1, total)
                self._task_registry[task_id] = deepcopy(task)

            # 构建结果
            result = {
                "engine_variant": engine_variant,
                "version_tag": version_tag,
                "total": total,
                "resolved": len(results) - len(unresolved),
                "canonical": results,
                "unresolved": unresolved,
            }

            # 标记为 succeeded
            task["status"] = STATUS_SUCCEEDED
            task["progress"] = 100.0
            task["progress_msg"] = "done"
            task["finished_at"] = datetime.datetime.utcnow().isoformat() + "Z"
            task["result"] = result
            task["result_ref"] = "memory://alias_task_adapter/%s" % task_id

        except TaskError:
            raise
        except Exception as e:
            task["status"] = STATUS_FAILED
            task["progress_msg"] = "failed"
            task["finished_at"] = datetime.datetime.utcnow().isoformat() + "Z"
            task["error"] = {
                "error": True,
                "code": ERR_ENGINE_DECIDE_FAILED,
                "message": "Engine decision failed: %s" % str(e),
                "detail": {"error": str(e), "type": type(e).__name__},
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            }
            task["retryable"] = True

        self._task_registry[task_id] = deepcopy(task)
        return deepcopy(task)

    # ----- 任务查询 -----

    def get_task(self, task_id):
        """查询任务状态 (对齐 GET /api/v1/tasks/{task_id})."""
        if task_id not in self._task_registry:
            raise TaskError(ERR_TASK_NOT_FOUND,
                            "Task %s not found" % task_id,
                            http_status=404)
        return deepcopy(self._task_registry[task_id])

    def get_result(self, task_id):
        """获取任务结果 (对齐 GET /api/v1/tasks/{task_id}/result).

        前置: 任务必须为 succeeded.
        """
        task = self.get_task(task_id)
        if task["status"] != STATUS_SUCCEEDED:
            raise TaskError(ERR_TASK_NOT_READY,
                            "Task %s is in state %s, result not available"
                            % (task_id, task["status"]),
                            http_status=409)
        return deepcopy(task["result"])

    def list_tasks(self, status_filter=None, task_type_filter=None,
                   submitter_filter=None, limit=50, offset=0):
        """批量查询任务 (对齐 GET /api/v1/tasks)."""
        tasks = list(self._task_registry.values())

        if status_filter:
            tasks = [t for t in tasks if t["status"] == status_filter]
        if task_type_filter:
            tasks = [t for t in tasks if t["task_type"] == task_type_filter]
        if submitter_filter:
            tasks = [t for t in tasks if t["submitter"] == submitter_filter]

        tasks.sort(key=lambda t: t["created_at"])
        total = len(tasks)
        tasks = tasks[offset:offset + limit]

        return {
            "status_filter": status_filter,
            "task_type_filter": task_type_filter,
            "rows": [deepcopy(t) for t in tasks],
            "total": total,
            "returned": len(tasks),
            "limit": limit,
            "offset": offset,
        }

    def cancel_task(self, task_id):
        """取消任务 (对齐 POST /api/v1/tasks/{task_id}/cancel)."""
        task = self.get_task(task_id)
        if task["status"] in TERMINAL_STATUSES:
            raise TaskError(ERR_TASK_ALREADY_TERMINAL,
                            "Task %s already in terminal state %s" % (task_id, task["status"]),
                            http_status=409)
        task["status"] = STATUS_CANCELLED
        task["finished_at"] = datetime.datetime.utcnow().isoformat() + "Z"
        task["progress_msg"] = "cancelled"
        self._task_registry[task_id] = deepcopy(task)
        return deepcopy(task)

    # ----- 错误上报 -----

    def report_error(self, task_id, error_code, message, detail=None):
        """上报任务执行错误."""
        task = self.get_task(task_id)
        task["error"] = {
            "error": True,
            "code": error_code,
            "message": message,
            "detail": detail,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }
        task["status"] = STATUS_FAILED
        task["progress_msg"] = "failed"
        task["finished_at"] = datetime.datetime.utcnow().isoformat() + "Z"
        self._task_registry[task_id] = deepcopy(task)
        return deepcopy(task)

    def report_progress(self, task_id, progress_pct, msg):
        """回写任务进度 (对齐 Worker 进度回写 §5.2)."""
        task = self.get_task(task_id)
        task["progress"] = progress_pct
        task["progress_msg"] = msg
        self._task_registry[task_id] = deepcopy(task)
        return deepcopy(task)

    # ----- 队列统计 -----

    def queue_stats(self):
        """队列统计 (对齐 GET /api/v1/tasks/queue)."""
        tasks = list(self._task_registry.values())
        queued = sum(1 for t in tasks if t["status"] == STATUS_QUEUED)
        running = sum(1 for t in tasks if t["status"] == STATUS_RUNNING)
        succeeded = sum(1 for t in tasks if t["status"] == STATUS_SUCCEEDED)
        failed = sum(1 for t in tasks if t["status"] == STATUS_FAILED)
        cancelled = sum(1 for t in tasks if t["status"] == STATUS_CANCELLED)

        oldest_queued = None
        oldest_queued_ts = None
        for t in tasks:
            if t["status"] == STATUS_QUEUED:
                if oldest_queued_ts is None or t["enqueued_at"] < oldest_queued_ts:
                    oldest_queued_ts = t["enqueued_at"]
                    oldest_queued = t["task_id"]

        now = datetime.datetime.utcnow()
        oldest_queued_seconds = None
        if oldest_queued_ts:
            try:
                qdt = datetime.datetime.fromisoformat(oldest_queued_ts.rstrip("Z"))
                oldest_queued_seconds = round((now - qdt).total_seconds(), 1)
            except Exception:
                pass

        return {
            "queue_depth": len(tasks),
            "queued": queued,
            "running": running,
            "succeeded": succeeded,
            "failed": failed,
            "cancelled": cancelled,
            "workers_total": 0,      # 原型不管理 worker
            "workers_busy": running,
            "oldest_queued_seconds": oldest_queued_seconds,
            "oldest_queued_task_id": oldest_queued,
        }

    # ----- 版本信息 -----

    def version_info(self):
        """适配器版本信息."""
        return {
            "adapter": "AliasTaskAdapter",
            "task_type": TASK_TYPE,
            "engine_variant": self.engine_variant,
            "version_tag": self.version_tag,
            "supported_variants": list(SUPPORTED_VARIANTS),
            "max_payload_bytes": MAX_PAYLOAD_BYTES,
            "max_task_ttl_seconds": MAX_TASK_TTL_SECONDS,
            "engine": self.engine.version_info if self._engine else None,
        }

    def summary_stats(self):
        """适配器运行统计."""
        tasks = list(self._task_registry.values())
        return {
            "tasks_total": len(tasks),
            "tasks_by_status": dict(Counter(t["status"] for t in tasks)),
            "tasks_by_variant": dict(Counter(t["payload"].get(
                "engine_variant", self.engine_variant) for t in tasks)),
            "submit_history_size": len(self._submit_history),
            "engine_stats": self.engine.summary_stats() if self._engine else None,
        }


# ---------------------------------------------------------------------------
# 冒烟自测
# ---------------------------------------------------------------------------

def smoke_test():
    """冒烟自测: 验证任务适配层全部接口."""
    print("=" * 78)
    print("V86 别名引擎任务适配层 · 冒烟自测")
    print("=" * 78)

    checks = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        checks.append({"name": name, "status": status, "detail": detail})
        print("  [%s] %s" % (status, name))
        if detail:
            print("         %s" % detail)

    # --- 1. 适配器初始化 ---
    adapter = AliasTaskAdapter(engine_variant="f3+f4")
    info = adapter.version_info()
    check("适配器初始化", info["task_type"] == TASK_TYPE and
          info["supported_variants"] == list(SUPPORTED_VARIANTS),
          "task_type=%s, variants=%s" % (info["task_type"], info["supported_variants"]))

    # --- 2. 创建任务 ---
    payload = {
        "alias_names": [
            "碳酸锂工厂库存天数",
            "GFEX：工业硅：主力合约：单边交易：持仓量（日）",
            "产量",
            "LME：锌：库存（日）",
        ],
        "engine_variant": "f3+f4",
        "version_tag": "v86.0-alpha",
    }
    idem_key = adapter.compute_idempotency_key("smoke_test", TASK_TYPE, payload)
    task = adapter.create_task(payload, submitter="smoke_test", priority=5,
                               idempotency_key=idem_key)
    check("任务创建", task["task_id"].startswith(TASK_ID_PREFIX) and
          task["status"] == STATUS_QUEUED,
          "task_id=%s, status=%s" % (task["task_id"], task["status"]))

    # --- 3. 幂等键计算 ---
    check("幂等键计算", isinstance(idem_key, str) and len(idem_key) == 32,
          "key=%s" % idem_key[:16] + "...")

    # 幂等命中: 同一 key + submitter 返回同一 task_id
    task2 = adapter.create_task(payload, submitter="smoke_test",
                                idempotency_key=idem_key)
    check("幂等命中", task2["task_id"] == task["task_id"],
          "task2.id=%s == task.id=%s" % (task2["task_id"], task["task_id"]))

    # 幂等未命中: 不同 submitter
    task3 = adapter.create_task(payload, submitter="other_user",
                                idempotency_key=idem_key)
    check("幂等未命中 (不同submitter)", task3["task_id"] != task["task_id"],
          "task3.id=%s != task.id=%s" % (task3["task_id"], task["task_id"]))

    # --- 4. 执行任务 ---
    result_task = adapter.execute_task(task["task_id"], worker_id="smoke-worker")
    check("任务执行", result_task["status"] == STATUS_SUCCEEDED,
          "status=%s, progress=%s%%"
          % (result_task["status"], result_task["progress"]))

    result = result_task["result"]
    check("结果结构", result is not None and
          result.get("total", 0) == 4 and
          len(result.get("canonical", [])) >= 0 and
          len(result.get("unresolved", [])) >= 0,
          "total=%d, canonical=%d, unresolved=%d"
          % (result.get("total", 0), len(result.get("canonical", [])),
             len(result.get("unresolved", []))))

    # --- 5. 查询结果 ---
    result2 = adapter.get_result(task["task_id"])
    check("结果查询", result2["engine_variant"] == "f3+f4",
          "engine_variant=%s" % result2["engine_variant"])

    # --- 6. 批量查询 ---
    listing = adapter.list_tasks(status_filter=STATUS_SUCCEEDED, limit=10)
    check("批量查询", listing["total"] >= 1 and listing["returned"] >= 1,
          "total=%d, returned=%d" % (listing["total"], listing["returned"]))

    # --- 7. 取消任务 ---
    task_cancel = adapter.create_task(payload, submitter="smoke_test",
                                      priority=10)
    cancelled = adapter.cancel_task(task_cancel["task_id"])
    check("任务取消", cancelled["status"] == STATUS_CANCELLED,
          "status=%s" % cancelled["status"])

    # --- 8. 终态检查 ---
    try:
        adapter.execute_task(task["task_id"])
        check("终态检查", False, "should have raised")
    except TaskError as e:
        check("终态检查", e.code == ERR_TASK_ALREADY_TERMINAL,
              "code=%s, message=%s" % (e.code, e.message))

    # --- 9. 队列统计 ---
    stats = adapter.queue_stats()
    check("队列统计", stats["queue_depth"] >= 3,
          "depth=%d, queued=%d, running=%d, succeeded=%d"
          % (stats["queue_depth"], stats["queued"], stats["running"],
             stats["succeeded"]))

    # --- 10. 错误上报 ---
    task_err = adapter.create_task(payload, submitter="smoke_test")
    err_task = adapter.report_error(task_err["task_id"], ERR_ENGINE_DECIDE_FAILED,
                                    "test error", {"test": True})
    check("错误上报", err_task["status"] == STATUS_FAILED and
          err_task["error"]["code"] == ERR_ENGINE_DECIDE_FAILED,
          "status=%s, error_code=%s" % (err_task["status"], err_task["error"]["code"]))

    # --- 11. 无效 payload ---
    try:
        adapter.create_task({"alias_names": []})
        check("空alias_names拒绝", False, "should have raised")
    except TaskError as e:
        check("空alias_names拒绝", e.code == ERR_MISSING_REQUIRED_FIELD,
              "code=%s" % e.code)

    try:
        adapter.create_task({"alias_names": ["test"], "engine_variant": "invalid"})
        check("无效variant拒绝", False, "should have raised")
    except TaskError as e:
        check("无效variant拒绝", e.code == ERR_BAD_PAYLOAD,
              "code=%s" % e.code)

    # --- 12. 任务不存在 ---
    try:
        adapter.get_task("NONEXISTENT")
        check("不存在任务拒绝", False, "should have raised")
    except TaskError as e:
        check("不存在任务拒绝", e.code == ERR_TASK_NOT_FOUND,
              "code=%s" % e.code)

    # --- 13. 进度回写 ---
    task_prog = adapter.create_task(payload, submitter="smoke_test")
    prog_task = adapter.report_progress(task_prog["task_id"], 50.0, "halfway")
    check("进度回写", prog_task["progress"] == 50.0,
          "progress=%s%%, msg=%s" % (prog_task["progress"], prog_task["progress_msg"]))

    # --- 汇总 ---
    pass_count = sum(1 for c in checks if c["status"] == "PASS")
    fail_count = sum(1 for c in checks if c["status"] == "FAIL")

    print("-" * 78)
    print("冒烟结果: %d/%d PASS, %d FAIL" % (pass_count, len(checks), fail_count))
    print("=" * 78)

    return checks


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="V86 别名引擎任务适配层")
    parser.add_argument("--smoke", action="store_true", help="运行冒烟自测")
    parser.add_argument("--variant", type=str, default=DEFAULT_VARIANT,
                        choices=list(SUPPORTED_VARIANTS),
                        help="引擎变体 (默认 %s)" % DEFAULT_VARIANT)
    parser.add_argument("--test-resolve", type=str, nargs="+",
                        help="解析指定别名名 (调试用)")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    if args.smoke:
        checks = smoke_test()
        fail = sum(1 for c in checks if c["status"] == "FAIL")
        sys.exit(1 if fail > 0 else 0)

    if args.test_resolve:
        adapter = AliasTaskAdapter(engine_variant=args.variant)
        for name in args.test_resolve:
            eng = adapter.engine
            r = eng.resolve(name)
            print("%-60s state=%-12s canonicals=%d"
                  % (name[:60], r["state"], len(r["canonicals"])))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
