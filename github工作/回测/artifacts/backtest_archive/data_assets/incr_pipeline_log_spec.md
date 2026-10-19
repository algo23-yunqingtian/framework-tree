# 管道运行日志标准化规范

**文档ID**: DSHC-PIPELINE-LOG-SPEC-V1
**工单**: DSHC-DATA-PIPELINE-SMOKE-LIVE
**令牌**: DSHC-DATA-PIPELINE-SMOKE-LIVE-TOKEN
**版本**: 1.0.0
**日期**: 2026-10-19T16:41:03+08:00

---

## 1. 概述

本文档定义了 DSHC 增量数据管道所有运行日志的标准化格式，确保日志输出的可追溯性、可审计性和可监控性。

所有管道运行日志必须包含以下**必填字段**。

---

## 2. 必填字段

| 字段 | 类型 | 示例 | 说明 |
|------|------|------|------|
| `run_id` | string | `DSHC-ALERT-20261020153000-001` | 唯一运行标识，格式: `DSHC-ALERT-YYYYMMDDHHMMSS-NNN` |
| `stage` | string | `collect` | 管道阶段: `collect` / `sha_snapshot` / `validate` / `merge` / `update_manifest` / `lock` / `backfill` / `system` / `smoke_test` |
| `status` | string | `PASS` | 状态: `PASS` / `FAIL` / `WARN` / `ROLLBACK` / `REJECTED` |
| `error_code` | string/null | `E14_FIELD_CASE_MISMATCH` | 错误码 (无错误时为 null) |
| `shard_path` | string/null | `artifacts/.../increment_bar_20261020.csv` | 增量分片路径 (无分片时为 null) |
| `row_count` | integer | `54` | 行数统计 |
| `sha256` | string/null | `14950B9464BAEFD8...` | SHA-256 摘要 (无摘要时为 null) |
| `duration_seconds` | number | `45.23` | 耗时 (秒) |

---

## 3. 治理状态字段 (自动附加)

| 字段 | 值 | 说明 |
|------|-----|------|
| `timestamp` | ISO 8601 | 事件时间戳 |
| `event` | string | 告警事件类型 |
| `agent` | `DSHC-DATA-PIPELINE-SMOKE-LIVE` | 工单标识 |
| `token` | `DSHC-DATA-PIPELINE-SMOKE-LIVE-TOKEN` | 令牌标识 |
| `wind_api_calls` | `0` | 始终为 0 (零 Wind 调用) |
| `gate` | `CLOSED/HOLD` | 固定值 |
| `release_permit` | `NOT_ISSUED` | 固定值 |
| `severity` | `OK` / `WARNING` / `CRITICAL` | DSHD 监控严重级别 |

---

## 4. 告警事件类型

| 事件类型 | 触发条件 | 严重级别 |
|----------|----------|----------|
| `PIPELINE_COLLECT_TIMEOUT` | 采集超时 | CRITICAL |
| `PIPELINE_COLLECT_FAIL_ROLLBACK` | 采集失败后回滚 | CRITICAL |
| `PIPELINE_VALIDATE_E13_BLOCK` | 黑名单品种命中 | CRITICAL |
| `PIPELINE_VALIDATE_E14_BLOCK` | 字段大小写错误 | CRITICAL |
| `PIPELINE_VALIDATE_E15_BLOCK` | 完整性校验失败 | CRITICAL |
| `PIPELINE_MERGE_FAIL` | 合并步骤失败 | CRITICAL |
| `PIPELINE_SHA_TAMPER_DETECTED` | SHA 篡改检测 | CRITICAL |
| `PIPELINE_LOCK_CONFLICT` | 文件锁冲突 | WARNING |
| `PIPELINE_BACKFILL_DRYRUN` | 回填 dry-run | INFO |
| `PIPELINE_DAG_DRYRUN_COMPLETE` | DAG dry-run 完成 | INFO |
| `PIPELINE_SMOKE_LIVE_COMPLETE` | 冒烟测试完成 | INFO |
| `PIPELINE_ALERT_HOOK_READY` | 告警钩子就绪 | INFO |

---

## 5. DSHD 监控适配

所有告警 JSON 自动包含以下 DSHD watcher 兼容字段:

```json
{
    "severity": "OK | WARNING | CRITICAL",
    "invariants": {
        "gate": "CLOSED/HOLD",
        "release_permit": "NOT_ISSUED",
        "wind_api_calls": 0,
        "real_wind_call": false,
        "csv_readonly": true,
        "v1_frozen": true,
        "f01_a06_unchanged": true,
        "lc_shf_permanently_blacklisted": true
    }
}
```

DSHD watcher (P68/P69) 可通过以下规则捕获告警:

```
grep "agent.*DSHC-DATA-PIPELINE-SMOKE-LIVE" tracking_monitor_audit.jsonl
```

---

## 6. 告警示例

### 6.1 采集超时 (CRITICAL)

```json
{
    "run_id": "DSHC-ALERT-20261020153000-001",
    "stage": "collect",
    "status": "ROLLBACK",
    "error_code": "COLLECT_TIMEOUT",
    "shard_path": "artifacts/.../increment_bar_20261020.csv",
    "row_count": 0,
    "sha256": null,
    "duration_seconds": 15.23,
    "timestamp": "2026-10-20T15:30:00+08:00",
    "event": "PIPELINE_COLLECT_TIMEOUT",
    "agent": "DSHC-DATA-PIPELINE-SMOKE-LIVE",
    "token": "DSHC-DATA-PIPELINE-SMOKE-LIVE-TOKEN",
    "wind_api_calls": 0,
    "gate": "CLOSED/HOLD",
    "release_permit": "NOT_ISSUED",
    "severity": "CRITICAL",
    "message": "PIPELINE_COLLECT_TIMEOUT | stage=collect | status=ROLLBACK | error=COLLECT_TIMEOUT",
    "retryable": true,
    "rollback_triggered": true,
    "detail": {
        "retry_attempts": 3,
        "expected_retries": 3,
        "v2_unchanged": true
    },
    "invariants": {
        "gate": "CLOSED/HOLD",
        "release_permit": "NOT_ISSUED",
        "wind_api_calls": 0,
        "real_wind_call": false,
        "csv_readonly": true,
        "v1_frozen": true,
        "f01_a06_unchanged": true,
        "lc_shf_permanently_blacklisted": true
    }
}
```

### 6.2 字段大小写错误 (CRITICAL)

```json
{
    "run_id": "DSHC-ALERT-20261020153100-002",
    "stage": "validate",
    "status": "FAIL",
    "error_code": "E14_FIELD_CASE_MISMATCH",
    "shard_path": "artifacts/.../increment_bar_20261020.csv",
    "row_count": 3,
    "sha256": null,
    "duration_seconds": 0.05,
    "timestamp": "2026-10-20T15:31:00+08:00",
    "event": "PIPELINE_VALIDATE_E14_BLOCK",
    "severity": "CRITICAL",
    "message": "PIPELINE_VALIDATE_E14_BLOCK | stage=validate | status=FAIL | error=E14_FIELD_CASE_MISMATCH",
    "detail": {
        "errors_found": 2,
        "error_messages": [
            "VOL 字段大小写错误: 'vol' (应为 'VOL')",
            "VOL 字段大小写错误: 'volume' (应为 'VOL')"
        ]
    },
    "invariants": { "gate": "CLOSED/HOLD", "release_permit": "NOT_ISSUED" }
}
```

### 6.3 锁冲突 (WARNING)

```json
{
    "run_id": "DSHC-ALERT-20261020153200-003",
    "stage": "lock",
    "status": "PASS",
    "error_code": "LOCK_CONFLICT",
    "shard_path": null,
    "row_count": 0,
    "sha256": "14950B9464BAEFD8...",
    "duration_seconds": 0.12,
    "timestamp": "2026-10-20T15:32:00+08:00",
    "event": "PIPELINE_LOCK_PRESSURE_TEST",
    "severity": "OK",
    "message": "PIPELINE_LOCK_PRESSURE_TEST | stage=lock | status=PASS | error=LOCK_CONFLICT",
    "detail": {
        "instance_1_lock_created": true,
        "instance_2_rejected": true,
        "instance_2_return_code": 1,
        "v2_unchanged": true,
        "lock_timeout_minutes": 30
    }
}
```

---

## 7. 日志写入位置

所有管道告警日志统一追加至:

```
tracking_monitor_audit.jsonl
```

每行一个 JSON 对象，使用 UTF-8 编码，确保无 BOM。

---

## 8. 验证

告警日志字段验证可通过告警钩子模块的 CLI 工具完成:

```bash
python code/incr_alert_hook.py --validate --validate-alert '<json_alert>'
```

---

## 9. 治理不变量

以下治理不变量在所有告警日志中保持不变:

- `wind_api_calls` = 0 (零 Wind 调用)
- `gate` = CLOSED/HOLD
- `release_permit` = NOT_ISSUED
- `csv_readonly` = true (V2 只读保护)
- `v1_frozen` = true (V1 冻结)
- `f01_a06_unchanged` = true
- `lc_shf_permanently_blacklisted` = true (LC.SHF 永久黑名单)

---

*文档结束*
