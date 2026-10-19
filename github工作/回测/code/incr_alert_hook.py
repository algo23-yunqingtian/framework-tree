#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DSHC-DATA-PIPELINE-SMOKE-LIVE · 管道告警钩子模块
────────────────────────────────────────────────────────────
工单: DSHC-DATA-PIPELINE-SMOKE-LIVE
令牌: DSHC-DATA-PIPELINE-SMOKE-LIVE-TOKEN

功能:
  1. 结构化告警 JSON 生成 — 管道异常事件统一输出格式
  2. 日志标准化 — 统一 run_id/阶段/状态/error_code/shard_path/行数/SHA/耗时
  3. 审计日志写入 — 追加至 tracking_monitor_audit.jsonl
  4. DSHD 监控适配 — 输出字段兼容 DSHD watcher 捕获格式
  5. CLI 工具 — 支持独立告警发射

用法:
  # 作为库导入
  from incr_alert_hook import AlertHook
  hook = AlertHook()
  hook.emit(event_type="PIPELINE_COLLECT_TIMEOUT", stage="collect", status="FAIL", ...)

  # 作为 CLI 工具
  python code/incr_alert_hook.py --emit --type PIPELINE_COLLECT_TIMEOUT --detail "simulated"

  # 列出所有告警类型
  python code/incr_alert_hook.py --list-types

治理红线:
  - 零 Wind 调用 (wind_api_calls=0)
  - Gate=CLOSED/HOLD, Release=NOT_ISSUED
  - V2 只读保护
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ════════════════════════════════════════════════════════════════
# 🔒 安全锁 (与 DAG 调度脚本一致)
# ════════════════════════════════════════════════════════════════
REAL_WIND_CALL = False
WIND_API_CALLS = 0
OFFLINE_ONLY = True
AUTO_BACKTEST = "DENIED"
RELEASE_PERMIT = "NOT_ISSUED"
GATE = "CLOSED/HOLD"
CSV_READONLY = True
V1_FROZEN = True
F01_A06_UNCHANGED = True

TZ_CN = timezone(timedelta(hours=8))
WORKORDER = "DSHC-DATA-PIPELINE-SMOKE-LIVE"
TOKEN = "DSHC-DATA-PIPELINE-SMOKE-LIVE-TOKEN"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIT_LOG = PROJECT_ROOT / "tracking_monitor_audit.jsonl"

# ════════════════════════════════════════════════════════════════
# 工具函数
# ════════════════════════════════════════════════════════════════
def now_iso() -> str:
    return datetime.now(TZ_CN).isoformat(timespec="seconds")


# ════════════════════════════════════════════════════════════════
# 告警钩子类
# ════════════════════════════════════════════════════════════════
class AlertHook:
    """
    管道告警钩子 — 结构化告警输出 + 审计日志写入 + DSHD 监控适配

    输出格式兼容 DSHD 监控 watcher (P68/P69) 的 JSONL 结构。
    所有告警自动追加至 tracking_monitor_audit.jsonl。

    标准化字段 (P1.4 日志标准化):
      - run_id:            唯一运行标识 (DSHC-ALERT-YYYYMMDDHHMMSS)
      - stage:             管道阶段 (collect/sha_snapshot/validate/merge/update_manifest/system)
      - status:            状态 (PASS/FAIL/WARN/ROLLBACK/REJECTED)
      - error_code:        错误码 (E13_SYMBOL_BLACKLISTED/COLLECT_TIMEOUT/...)
      - shard_path:        增量分片路径
      - row_count:         行数统计
      - sha256:            SHA-256 摘要
      - duration_seconds:  耗时 (秒)
    """

    # ── 告警事件类型常量 ──
    PIPELINE_COLLECT_TIMEOUT = "PIPELINE_COLLECT_TIMEOUT"
    PIPELINE_COLLECT_FAIL_ROLLBACK = "PIPELINE_COLLECT_FAIL_ROLLBACK"
    PIPELINE_VALIDATE_E13_BLOCK = "PIPELINE_VALIDATE_E13_BLOCK"
    PIPELINE_VALIDATE_E14_BLOCK = "PIPELINE_VALIDATE_E14_BLOCK"
    PIPELINE_VALIDATE_E15_BLOCK = "PIPELINE_VALIDATE_E15_BLOCK"
    PIPELINE_MERGE_FAIL = "PIPELINE_MERGE_FAIL"
    PIPELINE_SHA_TAMPER_DETECTED = "PIPELINE_SHA_TAMPER_DETECTED"
    PIPELINE_LOCK_CONFLICT = "PIPELINE_LOCK_CONFLICT"
    PIPELINE_LOCK_PRESSURE_TEST = "PIPELINE_LOCK_PRESSURE_TEST"
    PIPELINE_BACKFILL_DRYRUN = "PIPELINE_BACKFILL_DRYRUN"
    PIPELINE_DAG_DRYRUN_COMPLETE = "PIPELINE_DAG_DRYRUN_COMPLETE"
    PIPELINE_ROW_COUNT_MISMATCH = "PIPELINE_ROW_COUNT_MISMATCH"
    PIPELINE_SMOKE_LIVE_COMPLETE = "PIPELINE_SMOKE_LIVE_COMPLETE"
    PIPELINE_ALERT_HOOK_READY = "PIPELINE_ALERT_HOOK_READY"

    # ── 阶段常量 ──
    STAGE_COLLECT = "collect"
    STAGE_SHA_SNAPSHOT = "sha_snapshot"
    STAGE_VALIDATE = "validate"
    STAGE_MERGE = "merge"
    STAGE_UPDATE_MANIFEST = "update_manifest"
    STAGE_LOCK = "lock"
    STAGE_BACKFILL = "backfill"
    STAGE_SYSTEM = "system"
    STAGE_SMOKE = "smoke_test"

    # ── 状态常量 ──
    STATUS_PASS = "PASS"
    STATUS_FAIL = "FAIL"
    STATUS_WARN = "WARN"
    STATUS_ROLLBACK = "ROLLBACK"
    STATUS_REJECTED = "REJECTED"

    # ── 严重级别映射 ──
    _SEVERITY_MAP = {
        STATUS_PASS: "OK",
        STATUS_WARN: "WARNING",
        STATUS_ROLLBACK: "WARNING",
        STATUS_FAIL: "CRITICAL",
        STATUS_REJECTED: "WARNING",
    }

    def __init__(
        self,
        workorder: str = WORKORDER,
        token: str = TOKEN,
        audit_log_path: Optional[Path] = None,
        dry_run: bool = False,
    ):
        """
        初始化告警钩子。

        Args:
            workorder: 工单标识
            token: 令牌标识
            audit_log_path: 审计日志路径 (默认 tracking_monitor_audit.jsonl)
            dry_run: 如果 True, 仅生成告警不写入审计日志
        """
        self.workorder = workorder
        self.token = token
        self.audit_log_path = audit_log_path or AUDIT_LOG
        self.dry_run = dry_run
        self.alerts: List[Dict[str, Any]] = []
        self._alert_counter = 0

    # ── 核心方法: 发射告警 ──
    def emit(
        self,
        event_type: str,
        stage: str,
        status: str,
        error_code: Optional[str] = None,
        shard_path: Optional[str] = None,
        row_count: int = 0,
        sha256: Optional[str] = None,
        duration_seconds: float = 0.0,
        detail: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
        rollback_triggered: bool = False,
        v2_sha256: Optional[str] = None,
        mode: str = "DRY_RUN",
    ) -> Dict[str, Any]:
        """
        发射结构化告警。

        Args:
            event_type:        告警事件类型 (使用类常量)
            stage:             管道阶段
            status:            状态 (PASS/FAIL/WARN/ROLLBACK/REJECTED)
            error_code:        错误码
            shard_path:        增量分片路径
            row_count:         行数
            sha256:            SHA-256 摘要
            duration_seconds:  耗时 (秒)
            detail:            附加上下文
            retryable:         是否可重试
            rollback_triggered: 是否触发回滚
            v2_sha256:         V2 原始归档 SHA (只读保护验证)
            mode:              运行模式 (DRY_RUN/EXECUTE)

        Returns:
            完整的告警字典
        """
        self._alert_counter += 1
        run_id = f"DSHC-ALERT-{datetime.now(TZ_CN).strftime('%Y%m%d%H%M%S')}-{self._alert_counter:03d}"

        severity = self._SEVERITY_MAP.get(status, "WARNING")

        alert = {
            # ── 标准化核心字段 ──
            "run_id": run_id,
            "stage": stage,
            "status": status,
            "error_code": error_code,
            "shard_path": shard_path,
            "row_count": row_count,
            "sha256": sha256,
            "duration_seconds": round(duration_seconds, 3),

            # ── 治理状态 ──
            "timestamp": now_iso(),
            "event": event_type,
            "event_id": run_id,
            "agent": self.workorder,
            "token": self.token,
            "wind_api_calls": 0,
            "gate": GATE,
            "release_permit": RELEASE_PERMIT,
            "mode": mode,

            # ── DSHD 监控适配字段 ──
            "severity": severity,
            "alert_level": severity,
            "invariants": {
                "gate": GATE,
                "release_permit": RELEASE_PERMIT,
                "wind_api_calls": 0,
                "real_wind_call": False,
                "csv_readonly": True,
                "v1_frozen": True,
                "f01_a06_unchanged": True,
                "lc_shf_permanently_blacklisted": True,
            },

            # ── 上下文信息 ──
            "message": self._build_message(event_type, stage, status, error_code),
            "retryable": retryable,
            "rollback_triggered": rollback_triggered,
        }

        # 条件字段
        if v2_sha256:
            alert["v2_sha256"] = v2_sha256

        if detail:
            alert["detail"] = detail

        self.alerts.append(alert)

        if not self.dry_run:
            self._write_audit(alert)

        return alert

    # ── 私有方法 ──
    def _build_message(self, event_type: str, stage: str, status: str,
                       error_code: Optional[str]) -> str:
        """构建人类可读消息。"""
        parts = [event_type]
        if stage:
            parts.append(f"stage={stage}")
        if status:
            parts.append(f"status={status}")
        if error_code:
            parts.append(f"error={error_code}")
        return " | ".join(parts)

    def _write_audit(self, alert: Dict[str, Any]) -> None:
        """写入审计日志 JSONL。"""
        try:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(alert, ensure_ascii=False) + "\n")
        except OSError as e:
            sys.stderr.write(f"[ALERT_HOOK] Failed to write audit log: {e}\n")

    # ── 查询方法 ──
    def get_alerts(self) -> List[Dict[str, Any]]:
        """返回所有已发射的告警列表。"""
        return list(self.alerts)

    def get_summary(self) -> Dict[str, Any]:
        """返回告警摘要统计。"""
        total = len(self.alerts)
        by_status = {}
        by_stage = {}
        by_severity = {}

        for a in self.alerts:
            by_status[a["status"]] = by_status.get(a["status"], 0) + 1
            by_stage[a["stage"]] = by_stage.get(a["stage"], 0) + 1
            by_severity[a.get("severity", "WARNING")] = by_severity.get(a.get("severity", "WARNING"), 0) + 1

        return {
            "total_alerts": total,
            "by_status": by_status,
            "by_stage": by_stage,
            "by_severity": by_severity,
            "dry_run": self.dry_run,
            "workorder": self.workorder,
            "token": self.token,
            "gate": GATE,
            "release_permit": RELEASE_PERMIT,
            "wind_api_calls": 0,
        }

    def get_alerts_json(self, indent: int = 2) -> str:
        """返回所有告警的 JSON 字符串。"""
        return json.dumps(self.alerts, ensure_ascii=False, indent=indent)

    # ── 便捷方法 ──
    @staticmethod
    def validate_log_fields(alert: Dict[str, Any]) -> List[str]:
        """
        验证告警是否符合日志标准化要求 (P1.4)。

        必填字段: run_id, stage, status, error_code, shard_path,
                  row_count, sha256, duration_seconds
        """
        required = [
            "run_id", "stage", "status", "error_code",
            "shard_path", "row_count", "sha256", "duration_seconds",
        ]
        missing = [f for f in required if f not in alert]
        if missing:
            return [f"Missing required fields: {missing}"]

        errors = []
        if alert["status"] not in ("PASS", "FAIL", "WARN", "ROLLBACK", "REJECTED"):
            errors.append(f"Invalid status: {alert['status']}")
        if not alert["run_id"].startswith("DSHC-ALERT-"):
            errors.append(f"Invalid run_id format: {alert['run_id']}")
        return errors


# ════════════════════════════════════════════════════════════════
# CLI 入口
# ════════════════════════════════════════════════════════════════
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="incr_alert_hook.py",
        description=f"{WORKORDER} · 管道告警钩子模块",
    )

    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--emit", action="store_true",
                              help="发射一条告警")
    action_group.add_argument("--list-types", action="store_true",
                              help="列出所有告警事件类型")
    action_group.add_argument("--validate", action="store_true",
                              help="验证告警日志字段标准化")

    parser.add_argument("--type", type=str, default=None,
                        help="告警事件类型 (用于 --emit)")
    parser.add_argument("--stage", type=str, default=None,
                        help="管道阶段")
    parser.add_argument("--status", type=str, default=None,
                        help="状态")
    parser.add_argument("--error-code", type=str, default=None,
                        help="错误码")
    parser.add_argument("--shard-path", type=str, default=None,
                        help="分片路径")
    parser.add_argument("--row-count", type=int, default=0,
                        help="行数")
    parser.add_argument("--sha256", type=str, default=None,
                        help="SHA-256 摘要")
    parser.add_argument("--duration", type=float, default=0.0,
                        help="耗时 (秒)")
    parser.add_argument("--detail", type=str, default=None,
                        help="附加详情 (JSON)")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅生成告警不写入审计日志")
    parser.add_argument("--validate-alert", type=str, default=None,
                        help="验证指定 JSON 告警 (用于 --validate)")

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if args.list_types:
        print("告警事件类型:")
        print("-" * 50)
        for name in sorted(vars(AlertHook).keys()):
            if name.startswith("PIPELINE_") and not name.startswith("_"):
                print(f"  {name}")
        print("-" * 50)
        print(f"\n共 {sum(1 for n in vars(AlertHook).keys() if n.startswith('PIPELINE_'))} 种告警类型")
        print(f"\n治理状态:")
        print(f"  Gate:         {GATE}")
        print(f"  Release:      {RELEASE_PERMIT}")
        print(f"  Wind calls:   {WIND_API_CALLS}")
        print(f"  Offline:      {OFFLINE_ONLY}")
        return 0

    if args.emit:
        hook = AlertHook(dry_run=args.dry_run)
        detail = None
        if args.detail:
            try:
                detail = json.loads(args.detail)
            except json.JSONDecodeError:
                detail = {"raw": args.detail}

        alert = hook.emit(
            event_type=args.type or AlertHook.PIPELINE_ALERT_HOOK_READY,
            stage=args.stage or AlertHook.STAGE_SYSTEM,
            status=args.status or AlertHook.STATUS_PASS,
            error_code=args.error_code,
            shard_path=args.shard_path,
            row_count=args.row_count,
            sha256=args.sha256,
            duration_seconds=args.duration,
            detail=detail,
        )
        print(json.dumps(alert, ensure_ascii=False, indent=2))
        print(f"\n✅ Alert emitted: {alert['run_id']}")
        return 0

    if args.validate:
        if not args.validate_alert:
            print("Usage: --validate --validate-alert '<json_alert>'")
            return 1
        try:
            alert = json.loads(args.validate_alert)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            return 1

        errors = AlertHook.validate_log_fields(alert)
        if errors:
            print(f"❌ Validation FAILED: {errors}")
            return 1
        print("✅ Validation PASSED: all required fields present")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
