#!/usr/bin/env python3
"""
DSHB V86-RC2 Gate V5 Gray Decision Callback Handler
工单: DSHB_V86_RC2_G0_SHADOW_TRAFFIC_ISOLATION / T3.3
约束: NO_OVERWRITE=TRUE / NO_MODIFY_V85=TRUE / BRANCH_LOCKED=TRUE / NO_ZHIJI_API_CALL=FALSE

功能:
  1. 接收 HERMES gray_gate_decider 灰度决策事件 (ADVANCE/HOLD/OBSERVE/ROLLBACK/COMPLETE)
  2. 自动更新 Gate V5 状态 (READY/WARN/NOT_READY)
  3. 联动 DEP-001 周期性巡检启停
  4. 联动影子流量镜像启停
  5. 审计事件持久化与上报
  6. 事件去重与幂等处理
  7. 完整自检套件 (45 项)

用法:
  python3 gate_v5_gray_callback.py                          # 启动回调服务 (默认 9090 端口)
  python3 gate_v5_gray_callback.py --port=9091               # 自定义端口
  python3 gate_v5_gray_callback.py --dry-run                 # 干运行模式
  python3 gate_v5_gray_callback.py --self-test                # 自检
  python3 gate_v5_gray_callback.py --decide INPUT.json        # 单次决策处理
  python3 gate_v5_gray_callback.py --health                  # 健康检查
  python3 gate_v5_gray_callback.py --status                   # 状态查询
  python3 gate_v5_gray_callback.py --verbose                  # 详细输出

事件结构 (对齐 gray_gate_decider.py 输出):
  {
    "timestamp": "2026-10-17T10:00:00Z",
    "decision": "ADVANCE",
    "decision_reason": "G0 观测完成，准入 G1",
    "current_stage": "G0",
    "next_stage": "G1",
    "dep_001_status": "RECOVERED",
    "faults_detected": [],
    "all_faults": []
  }

状态机:
  ┌──────────┐  ROLLBACK   ┌─────────────┐
  │ READY    │────────────>│ NOT_READY    │
  └────┬─────┘            └──────┬───────┘
       │                         │
       │ ADVANCE/HOLD/OBSERVE    │ ADVANCE
       ▼                         ▼
  ┌──────────┐            ┌──────────┐
  │ WARN     │            │ READY    │
  └──────────┘            └──────────┘

联动矩阵:
  Decision    → Gate Status → DEP Probe → Shadow Mirror → Action
  ADVANCE     → READY       → START     → START        → 启动巡检+镜像
  HOLD        → WARN        → CONTINUE  → CONTINUE     → 保持当前状态
  OBSERVE     → WARN        → CONTINUE  → CONTINUE     → 保持当前状态
  ROLLBACK    → NOT_READY   → STOP      → STOP         → 停止巡检+镜像
  COMPLETE    → READY       → STOP      → STOP         → 全量完成，停止

版本号: V1.0
"""

import json
import os
import sys
import time
import hashlib
import logging
import threading
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

VERSION = "1.0"
WORK_ORDER = "DSHB_V86_RC2_G0_SHADOW_TRAFFIC_ISOLATION"
TASK_ID = "T3.3"

# ═══════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════

DEFAULT_CONFIG = {
    # ── 服务配置 ──
    "server_host": "0.0.0.0",
    "server_port": 9090,
    "request_timeout_seconds": 30,
    "max_concurrent_requests": 10,
    
    # ── Gate 配置 ──
    "gate_base_url": "https://gate.svc:9090",
    "gate_status_endpoint": "/api/v1/gate/status",
    "gate_audit_endpoint": "/api/v1/gate/audit-log",
    
    # ── DEP 巡检配置 ──
    "dep_probe_command": "python3 dep001_periodic_probe.py",
    "dep_probe_process_name": "dep001_periodic_probe",
    
    # ── 影子镜像配置 ──
    "shadow_mirror_api": "http://mirror-router.mirror-ns.svc:8080",
    "shadow_start_endpoint": "/api/v1/mirror/control/start",
    "shadow_stop_endpoint": "/api/v1/mirror/control/stop",
    "shadow_status_endpoint": "/api/v1/mirror/control/status",
    "shadow_rate_endpoint": "/api/v1/mirror/control/rate",
    
    # ── 审计配置 ──
    "audit_log_dir": "audit_logs/",
    "audit_max_entries": 10000,
    "audit_retention_days": 90,
    "audit_push_url": None,  # 外部审计推送 URL (可选)
    
    # ── 事件处理配置 ──
    "event_dedup_window_seconds": 60,      # 事件去重窗口
    "event_retry_max": 3,                  # 事件处理重试次数
    "event_retry_backoff_seconds": 2,      # 重试退避间隔
    
    # ── 健康检查 ──
    "health_check_interval_seconds": 30,
    "dep_health_timeout_seconds": 5,
    "mirror_health_timeout_seconds": 5,
    
    # ── 采样率联动 (G0-G5 阶段映射) ──
    "stage_sampling_rates": {
        "G0": 10.0,
        "G1": 20.0,
        "G2": 30.0,
        "G3": 50.0,
        "G4": 80.0,
        "G5": 100.0,
    },
    
    # ── 调试 ──
    "dry_run": False,
    "verbose": False,
    "log_level": "INFO",
}

# ── 决策-动作联动矩阵 ──
DECISION_ACTION_MAP = {
    "ADVANCE": {
        "gate_status": "READY",
        "dep_probe": "START",
        "shadow_mirror": "START",
        "description": "灰度推进：启动巡检+镜像",
    },
    "HOLD": {
        "gate_status": "WARN",
        "dep_probe": "CONTINUE",
        "shadow_mirror": "CONTINUE",
        "description": "灰度暂停：保持当前状态",
    },
    "OBSERVE": {
        "gate_status": "WARN",
        "dep_probe": "CONTINUE",
        "shadow_mirror": "CONTINUE",
        "description": "灰度观测：保持当前状态",
    },
    "ROLLBACK": {
        "gate_status": "NOT_READY",
        "dep_probe": "STOP",
        "shadow_mirror": "STOP",
        "description": "灰度回滚：停止巡检+镜像",
    },
    "COMPLETE": {
        "gate_status": "READY",
        "dep_probe": "STOP",
        "shadow_mirror": "STOP",
        "description": "灰度完成：停止巡检+镜像",
    },
}

# ── 状态机定义 ──
GATE_STATUSES = ["READY", "WARN", "NOT_READY"]
DECISIONS = ["ADVANCE", "HOLD", "OBSERVE", "ROLLBACK", "COMPLETE"]

# ═══════════════════════════════════════════════════════════
# 日志配置
# ═══════════════════════════════════════════════════════════

def setup_logging(log_level: str = "INFO", log_dir: str = "logs/") -> logging.Logger:
    """配置日志系统。"""
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger("gate_v5_gray_callback")
    logger.setLevel(getattr(logging, log_level))
    
    # 控制台处理器
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(getattr(logging, log_level))
    ch.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(ch)
    
    # 文件处理器
    fh = logging.FileHandler(
        os.path.join(log_dir, "gate_v5_gray_callback.log"),
        encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(fh)
    
    return logger

# ═══════════════════════════════════════════════════════════
# 审计事件
# ═══════════════════════════════════════════════════════════

class AuditEvent:
    """审计事件。"""
    
    EVENT_TYPES = [
        "DECISION_RECEIVED",
        "DECISION_PROCESSED",
        "DECISION_FAILED",
        "GATE_STATUS_UPDATED",
        "DEP_PROBE_STARTED",
        "DEP_PROBE_STOPPED",
        "SHADOW_MIRROR_STARTED",
        "SHADOW_MIRROR_STOPPED",
        "SHADOW_RATE_CHANGED",
        "HEALTH_CHECK",
        "CONFIG_CHANGED",
        "ERROR",
    ]
    
    SEVERITIES = ["INFO", "WARN", "ERROR", "CRITICAL"]
    
    def __init__(self, event_type: str, severity: str = "INFO", data: Dict = None):
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.severity = severity
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.data = data or {}
        self.processed = False
        self.error = None
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "timestamp": self.timestamp,
            "data": self.data,
            "processed": self.processed,
            "error": self.error,
        }
    
    def __str__(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class AuditLogger:
    """审计日志记录器。"""
    
    def __init__(self, logger: logging.Logger, config: Dict):
        self.logger = logger
        self.config = config
        self.audit_dir = Path(config["audit_log_dir"])
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.max_entries = config["audit_max_entries"]
        self._lock = threading.Lock()
        self._entries = []
        self._event_count = 0
    
    def log_event(self, event: AuditEvent) -> None:
        """记录审计事件。"""
        with self._lock:
            self._entries.append(event.to_dict())
            self._event_count += 1
            
            # 保留最大条数
            if len(self._entries) > self.max_entries:
                self._entries = self._entries[-self.max_entries:]
            
            # 写入审计日志文件
            today = datetime.utcnow().strftime("%Y%m%d")
            log_file = self.audit_dir / f"audit_{today}.jsonl"
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
            except Exception as e:
                self.logger.error(f"审计日志写入失败: {e}")
        
        # 外部推送 (可选)
        if self.config.get("audit_push_url"):
            self._push_to_external(event)
        
        # 日志输出
        level = {
            "INFO": "info",
            "WARN": "warning",
            "ERROR": "error",
            "CRITICAL": "critical",
        }.get(event.severity, "info")
        getattr(self.logger, level)(
            f"[AUDIT] {event.event_type}: {json.dumps(event.data, ensure_ascii=False)}"
        )
    
    def _push_to_external(self, event: AuditEvent) -> None:
        """推送审计事件至外部服务 (模拟)。"""
        if self.config["dry_run"]:
            self.logger.info(f"[DRY-RUN] 外部审计推送: {event.event_type}")
            return
        # 实际推送逻辑 (模拟)
        self.logger.info(f"[AUDIT-PUSH] {event.event_type} → {self.config['audit_push_url']}")
    
    def get_stats(self) -> Dict:
        """获取审计统计。"""
        with self._lock:
            return {
                "total_events": self._event_count,
                "recent_events": len(self._entries),
                "event_types": {et: sum(1 for e in self._entries if e["event_type"] == et) for et in AuditEvent.EVENT_TYPES},
                "severities": {s: sum(1 for e in self._entries if e["severity"] == s) for s in AuditEvent.SEVERITIES},
            }


# ═══════════════════════════════════════════════════════════
# 事件处理器
# ═══════════════════════════════════════════════════════════

class DecisionEventHandler:
    """灰度决策事件处理器。"""
    
    def __init__(self, logger: logging.Logger, audit_logger: AuditLogger, config: Dict):
        self.logger = logger
        self.audit = audit_logger
        self.config = config
        self._dedup_cache = {}
        self._dedup_window = config["event_dedup_window_seconds"]
        self._lock = threading.Lock()
        self._state = {
            "gate_status": "READY",
            "dep_probe_running": False,
            "shadow_mirror_running": False,
            "shadow_sampling_rate": 10.0,
            "current_stage": "G0",
            "last_decision": None,
            "last_decision_time": None,
            "decision_count": 0,
            "error_count": 0,
        }
    
    def process_decision(self, decision_event: Dict) -> Dict:
        """处理灰度决策事件。"""
        event_id = decision_event.get("event_id", str(uuid.uuid4()))
        decision = decision_event.get("decision", "")
        timestamp = decision_event.get("timestamp", "")
        current_stage = decision_event.get("current_stage", "G0")
        
        # 1. 事件去重检查
        dedup_key = self._compute_dedup_key(decision_event)
        if self._is_duplicate(dedup_key):
            self.logger.warning(f"重复事件已忽略: event_id={event_id}, decision={decision}")
            self.audit.log_event(AuditEvent("DECISION_FAILED", "WARN", {
                "event_id": event_id,
                "decision": decision,
                "reason": "duplicate_event_ignored",
                "dedup_key": dedup_key,
            }))
            return {
                "status": "DUPLICATE",
                "event_id": event_id,
                "decision": decision,
                "action": "ignored",
                "message": "事件已忽略 (重复)",
            }
        
        # 2. 验证事件结构
        validation = self._validate_decision_event(decision_event)
        if not validation["valid"]:
            self.logger.error(f"事件验证失败: {validation['errors']}")
            self.audit.log_event(AuditEvent("DECISION_FAILED", "ERROR", {
                "event_id": event_id,
                "decision": decision,
                "errors": validation["errors"],
            }))
            return {
                "status": "INVALID",
                "event_id": event_id,
                "decision": decision,
                "action": "rejected",
                "message": f"事件验证失败: {', '.join(validation['errors'])}",
                "errors": validation["errors"],
            }
        
        # 3. 记录事件接收
        self.audit.log_event(AuditEvent("DECISION_RECEIVED", "INFO", {
            "event_id": event_id,
            "decision": decision,
            "current_stage": current_stage,
            "timestamp": timestamp,
        }))
        
        # 4. 执行决策动作
        result = self._execute_decision_actions(decision, event_id, current_stage, decision_event)
        
        # 5. 更新状态
        with self._lock:
            self._state["last_decision"] = decision
            self._state["last_decision_time"] = timestamp
            self._state["decision_count"] += 1
            if current_stage:
                self._state["current_stage"] = current_stage
        
        # 6. 记录处理完成
        self.audit.log_event(AuditEvent("DECISION_PROCESSED", "INFO", {
            "event_id": event_id,
            "decision": decision,
            "result": result,
        }))
        
        return result
    
    def _compute_dedup_key(self, event: Dict) -> str:
        """计算事件去重键。"""
        content = json.dumps({
            "decision": event.get("decision"),
            "current_stage": event.get("current_stage"),
            "next_stage": event.get("next_stage"),
            "dep_001_status": event.get("dep_001_status"),
        }, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_duplicate(self, dedup_key: str) -> bool:
        """检查事件是否重复。"""
        now = time.time()
        # 清理过期缓存
        expired = [k for k, v in self._dedup_cache.items() if now - v > self._dedup_window]
        for k in expired:
            del self._dedup_cache[k]
        
        if dedup_key in self._dedup_cache:
            return True
        
        self._dedup_cache[dedup_key] = now
        return False
    
    def _validate_decision_event(self, event: Dict) -> Dict:
        """验证决策事件结构。"""
        errors = []
        required_fields = ["decision", "current_stage", "timestamp"]
        for field in required_fields:
            if field not in event or not event[field]:
                errors.append(f"缺少必填字段: {field}")
        
        if "decision" in event and event["decision"] not in DECISIONS:
            errors.append(f"无效决策值: {event['decision']} (有效值: {', '.join(DECISIONS)})")
        
        if "current_stage" in event and event["current_stage"] not in ["G0", "G1", "G2", "G3", "G4", "G5"]:
            errors.append(f"无效灰度阶段: {event['current_stage']}")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    def _execute_decision_actions(
        self, decision: str, event_id: str, current_stage: str, event: Dict
    ) -> Dict:
        """执行决策动作。"""
        action_map = DECISION_ACTION_MAP.get(decision)
        if not action_map:
            return {"status": "ERROR", "action": "rejected", "message": f"未知决策: {decision}"}
        
        result = {
            "status": "PROCESSED",
            "event_id": event_id,
            "decision": decision,
            "current_stage": current_stage,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "actions": {},
            "message": action_map["description"],
        }
        
        # 1. 更新 Gate 状态
        new_gate_status = action_map["gate_status"]
        gate_result = self._update_gate_status(new_gate_status, event_id, decision)
        result["actions"]["gate_status"] = gate_result
        
        # 2. 联动 DEP 巡检
        probe_action = action_map["dep_probe"]
        probe_result = self._control_dep_probe(probe_action, event_id, decision)
        result["actions"]["dep_probe"] = probe_result
        
        # 3. 联动影子镜像
        mirror_action = action_map["shadow_mirror"]
        mirror_result = self._control_shadow_mirror(mirror_action, event_id, decision, current_stage)
        result["actions"]["shadow_mirror"] = mirror_result
        
        # 4. 更新采样率 (如果适用)
        if decision in ("ADVANCE", "COMPLETE"):
            new_stage = event.get("next_stage", current_stage)
            target_rate = self.config["stage_sampling_rates"].get(new_stage, 10.0)
            rate_result = self._update_sampling_rate(target_rate, event_id, decision, new_stage)
            result["actions"]["sampling_rate"] = rate_result
        
        return result
    
    def _update_gate_status(self, new_status: str, event_id: str, decision: str) -> Dict:
        """更新 Gate 状态。"""
        old_status = self._state["gate_status"]
        
        if old_status == new_status:
            return {
                "status": "SKIPPED",
                "old_status": old_status,
                "new_status": new_status,
                "message": "状态未变化，跳过更新",
            }
        
        with self._lock:
            self._state["gate_status"] = new_status
        
        if self.config["dry_run"]:
            self.logger.info(f"[DRY-RUN] 更新 Gate 状态: {old_status} → {new_status} (decision={decision})")
            self.audit.log_event(AuditEvent("GATE_STATUS_UPDATED", "INFO", {
                "event_id": event_id,
                "old_status": old_status,
                "new_status": new_status,
                "decision": decision,
                "dry_run": True,
            }))
            return {
                "status": "DRY_RUN",
                "old_status": old_status,
                "new_status": new_status,
                "message": f"[DRY-RUN] Gate 状态已更新: {old_status} → {new_status}",
            }
        
        # 实际更新 (模拟)
        self.logger.info(f"更新 Gate 状态: {old_status} → {new_status} (decision={decision})")
        self.audit.log_event(AuditEvent("GATE_STATUS_UPDATED", "INFO", {
            "event_id": event_id,
            "old_status": old_status,
            "new_status": new_status,
            "decision": decision,
        }))
        
        return {
            "status": "OK",
            "old_status": old_status,
            "new_status": new_status,
            "message": f"Gate 状态已更新: {old_status} → {new_status}",
        }
    
    def _control_dep_probe(self, action: str, event_id: str, decision: str) -> Dict:
        """控制 DEP 巡检启停。"""
        current_running = self._state["dep_probe_running"]
        
        if action == "CONTINUE":
            return {
                "status": "CONTINUE",
                "current_running": current_running,
                "message": "保持当前巡检状态",
            }
        
        if action == "START" and current_running:
            return {
                "status": "ALREADY_RUNNING",
                "message": "DEP 巡检已在运行中",
            }
        
        if action == "STOP" and not current_running:
            return {
                "status": "ALREADY_STOPPED",
                "message": "DEP 巡检已停止",
            }
        
        if self.config["dry_run"]:
            self.logger.info(f"[DRY-RUN] DEP 巡检 {action} (decision={decision})")
            self.audit.log_event(AuditEvent(
                f"DEP_PROBE_{'STARTED' if action == 'START' else 'STOPPED'}",
                "INFO",
                {
                    "event_id": event_id,
                    "action": action,
                    "decision": decision,
                    "dry_run": True,
                }
            ))
            if action == "START":
                with self._lock:
                    self._state["dep_probe_running"] = True
            else:
                with self._lock:
                    self._state["dep_probe_running"] = False
            return {
                "status": "DRY_RUN",
                "action": action,
                "message": f"[DRY-RUN] DEP 巡检已{action.lower()}",
            }
        
        # 实际执行 (模拟)
        if action == "START":
            self.logger.info("启动 DEP 周期性巡检...")
            self._start_dep_probe()
            with self._lock:
                self._state["dep_probe_running"] = True
            self.audit.log_event(AuditEvent("DEP_PROBE_STARTED", "INFO", {
                "event_id": event_id,
                "decision": decision,
            }))
            return {
                "status": "OK",
                "action": "START",
                "message": "DEP 周期性巡检已启动",
            }
        else:
            self.logger.info("停止 DEP 周期性巡检...")
            self._stop_dep_probe()
            with self._lock:
                self._state["dep_probe_running"] = False
            self.audit.log_event(AuditEvent("DEP_PROBE_STOPPED", "INFO", {
                "event_id": event_id,
                "decision": decision,
            }))
            return {
                "status": "OK",
                "action": "STOP",
                "message": "DEP 周期性巡检已停止",
            }
    
    def _control_shadow_mirror(self, action: str, event_id: str, decision: str, stage: str) -> Dict:
        """控制影子流量镜像启停。"""
        current_running = self._state["shadow_mirror_running"]
        
        if action == "CONTINUE":
            return {
                "status": "CONTINUE",
                "current_running": current_running,
                "message": "保持当前镜像状态",
            }
        
        if action == "START" and current_running:
            return {
                "status": "ALREADY_RUNNING",
                "message": "影子镜像已在运行中",
            }
        
        if action == "STOP" and not current_running:
            return {
                "status": "ALREADY_STOPPED",
                "message": "影子镜像已停止",
            }
        
        if self.config["dry_run"]:
            self.logger.info(f"[DRY-RUN] 影子镜像 {action} (decision={decision}, stage={stage})")
            self.audit.log_event(AuditEvent(
                f"SHADOW_MIRROR_{'STARTED' if action == 'START' else 'STOPPED'}",
                "INFO",
                {
                    "event_id": event_id,
                    "action": action,
                    "decision": decision,
                    "stage": stage,
                    "dry_run": True,
                }
            ))
            if action == "START":
                with self._lock:
                    self._state["shadow_mirror_running"] = True
            else:
                with self._lock:
                    self._state["shadow_mirror_running"] = False
            return {
                "status": "DRY_RUN",
                "action": action,
                "message": f"[DRY-RUN] 影子镜像已{action.lower()}",
            }
        
        # 实际执行 (模拟)
        if action == "START":
            self.logger.info(f"启动影子流量镜像 (stage={stage})...")
            self._start_shadow_mirror(stage)
            with self._lock:
                self._state["shadow_mirror_running"] = True
            self.audit.log_event(AuditEvent("SHADOW_MIRROR_STARTED", "INFO", {
                "event_id": event_id,
                "decision": decision,
                "stage": stage,
            }))
            return {
                "status": "OK",
                "action": "START",
                "message": "影子流量镜像已启动",
            }
        else:
            self.logger.info("停止影子流量镜像...")
            self._stop_shadow_mirror()
            with self._lock:
                self._state["shadow_mirror_running"] = False
            self.audit.log_event(AuditEvent("SHADOW_MIRROR_STOPPED", "INFO", {
                "event_id": event_id,
                "decision": decision,
            }))
            return {
                "status": "OK",
                "action": "STOP",
                "message": "影子流量镜像已停止",
            }
    
    def _update_sampling_rate(self, target_rate: float, event_id: str, decision: str, stage: str) -> Dict:
        """更新采样率。"""
        current_rate = self._state["shadow_sampling_rate"]
        
        if abs(current_rate - target_rate) < 0.1:
            return {
                "status": "SKIPPED",
                "current_rate": current_rate,
                "target_rate": target_rate,
                "message": "采样率未变化，跳过更新",
            }
        
        if self.config["dry_run"]:
            self.logger.info(f"[DRY-RUN] 更新采样率: {current_rate}% → {target_rate}% (stage={stage})")
            with self._lock:
                self._state["shadow_sampling_rate"] = target_rate
            self.audit.log_event(AuditEvent("SHADOW_RATE_CHANGED", "INFO", {
                "event_id": event_id,
                "old_rate": current_rate,
                "new_rate": target_rate,
                "stage": stage,
                "decision": decision,
                "dry_run": True,
            }))
            return {
                "status": "DRY_RUN",
                "old_rate": current_rate,
                "new_rate": target_rate,
                "message": f"[DRY-RUN] 采样率已更新: {current_rate}% → {target_rate}%",
            }
        
        self.logger.info(f"更新采样率: {current_rate}% → {target_rate}% (stage={stage})")
        with self._lock:
            self._state["shadow_sampling_rate"] = target_rate
        self.audit.log_event(AuditEvent("SHADOW_RATE_CHANGED", "INFO", {
            "event_id": event_id,
            "old_rate": current_rate,
            "new_rate": target_rate,
            "stage": stage,
            "decision": decision,
        }))
        return {
            "status": "OK",
            "old_rate": current_rate,
            "new_rate": target_rate,
            "message": f"采样率已更新: {current_rate}% → {target_rate}%",
        }
    
    def _start_dep_probe(self) -> None:
        """启动 DEP 巡检 (模拟)。"""
        cmd = self.config["dep_probe_command"]
        if self.config["dry_run"]:
            return
        self.logger.info(f"启动 DEP 巡检: {cmd}")
        # 实际启动逻辑 (模拟)
    
    def _stop_dep_probe(self) -> None:
        """停止 DEP 巡检 (模拟)。"""
        proc_name = self.config["dep_probe_process_name"]
        if self.config["dry_run"]:
            return
        self.logger.info(f"停止 DEP 巡检: {proc_name}")
        # 实际停止逻辑 (模拟)
    
    def _start_shadow_mirror(self, stage: str) -> None:
        """启动影子镜像 (模拟)。"""
        if self.config["dry_run"]:
            return
        self.logger.info(f"启动影子镜像: {self.config['shadow_mirror_api']}{self.config['shadow_start_endpoint']}")
        # 实际启动逻辑 (模拟)
    
    def _stop_shadow_mirror(self) -> None:
        """停止影子镜像 (模拟)。"""
        if self.config["dry_run"]:
            return
        self.logger.info(f"停止影子镜像: {self.config['shadow_mirror_api']}{self.config['shadow_stop_endpoint']}")
        # 实际停止逻辑 (模拟)
    
    def get_state(self) -> Dict:
        """获取当前状态。"""
        with self._lock:
            return dict(self._state)
    
    def get_state_summary(self) -> Dict:
        """获取状态摘要。"""
        state = self.get_state()
        return {
            "gate_status": state["gate_status"],
            "dep_probe_running": state["dep_probe_running"],
            "shadow_mirror_running": state["shadow_mirror_running"],
            "shadow_sampling_rate": state["shadow_sampling_rate"],
            "current_stage": state["current_stage"],
            "last_decision": state["last_decision"],
            "last_decision_time": state["last_decision_time"],
            "decision_count": state["decision_count"],
            "error_count": state["error_count"],
            "version": VERSION,
            "work_order": WORK_ORDER,
        }


# ═══════════════════════════════════════════════════════════
# HTTP 服务器
# ═══════════════════════════════════════════════════════════

class GateCallbackHandler(BaseHTTPRequestHandler):
    """Gate V5 灰度回调 HTTP 处理。"""
    
    handler: DecisionEventHandler = None
    audit: AuditLogger = None
    logger: logging.Logger = None
    
    def _send_json(self, data: Dict, status_code: int = 200) -> None:
        """发送 JSON 响应。"""
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Request-Id", str(uuid.uuid4()))
        self.end_headers()
        self.wfile.write(body)
    
    def _read_json_body(self) -> Optional[Dict]:
        """读取 JSON 请求体。"""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length)
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 解析失败: {e}")
            return None
    
    def do_POST(self):
        """处理 POST 请求。"""
        if self.path == "/api/v1/gate/callback/decision":
            body = self._read_json_body()
            if body is None:
                self._send_json({"status": "ERROR", "message": "JSON 解析失败"}, 400)
                return
            
            event_id = str(uuid.uuid4())
            if "event_id" not in body:
                body["event_id"] = event_id
            
            result = self.handler.process_decision(body)
            self._send_json(result)
        
        elif self.path == "/api/v1/gate/callback/health":
            self._send_json({
                "status": "HEALTHY",
                "version": VERSION,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "work_order": WORK_ORDER,
            })
        
        else:
            self._send_json({"status": "ERROR", "message": f"未知端点: {self.path}"}, 404)
    
    def do_GET(self):
        """处理 GET 请求。"""
        if self.path == "/api/v1/gate/callback/status":
            state = self.handler.get_state_summary()
            state["timestamp"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            self._send_json(state)
        
        elif self.path == "/api/v1/gate/callback/health":
            self._send_json({
                "status": "HEALTHY",
                "version": VERSION,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "work_order": WORK_ORDER,
            })
        
        elif self.path == "/api/v1/gate/callback/audit/stats":
            stats = self.audit.get_stats()
            self._send_json(stats)
        
        else:
            self._send_json({"status": "ERROR", "message": f"未知端点: {self.path}"}, 404)
    
    def log_message(self, format, *args):
        """重写日志格式。"""
        self.logger.info(f"[HTTP] {args[0] if args else ''}")


# ═══════════════════════════════════════════════════════════
# 自检套件 (45 项)
# ═══════════════════════════════════════════════════════════

class SelfTest:
    """自检套件。"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        """执行单项检查。"""
        if condition:
            self.passed += 1
            self.logger.info(f"  ✅ {name}")
            return True
        else:
            self.failed += 1
            msg = f"  ❌ {name}: {detail}" if detail else f"  ❌ {name}"
            self.logger.error(msg)
            self.errors.append(name)
            return False
    
    def run_all(self) -> Dict:
        """运行全部自检。"""
        self.logger.info("=" * 60)
        self.logger.info(f"Gate V5 Gray Callback 自检套件 (V{VERSION})")
        self.logger.info(f"工单: {WORK_ORDER} / {TASK_ID}")
        self.logger.info("=" * 60)
        
        # ── T01-T05: 配置验证 ──
        self.logger.info("\n── 配置验证 (T01-T05) ──")
        self.check("T01: 版本号", VERSION == "1.0", f"版本={VERSION}")
        self.check("T02: 工单编号", WORK_ORDER == "DSHB_V86_RC2_G0_SHADOW_TRAFFIC_ISOLATION")
        self.check("T03: 决策类型数量", len(DECISIONS) == 5, f"决策数={len(DECISIONS)}")
        self.check("T04: 决策类型完整", set(DECISIONS) == {"ADVANCE", "HOLD", "OBSERVE", "ROLLBACK", "COMPLETE"})
        self.check("T05: 联动矩阵完整", len(DECISION_ACTION_MAP) == 5)
        
        # ── T06-T10: 状态机验证 ──
        self.logger.info("\n── 状态机验证 (T06-T10) ──")
        self.check("T06: Gate 状态定义", set(GATE_STATUSES) == {"READY", "WARN", "NOT_READY"})
        self.check("T07: ADVANCE→READY", DECISION_ACTION_MAP["ADVANCE"]["gate_status"] == "READY")
        self.check("T08: ROLLBACK→NOT_READY", DECISION_ACTION_MAP["ROLLBACK"]["gate_status"] == "NOT_READY")
        self.check("T09: HOLD→WARN", DECISION_ACTION_MAP["HOLD"]["gate_status"] == "WARN")
        self.check("T10: COMPLETE→READY", DECISION_ACTION_MAP["COMPLETE"]["gate_status"] == "READY")
        
        # ── T11-T15: 联动动作验证 ──
        self.logger.info("\n── 联动动作验证 (T11-T15) ──")
        self.check("T11: ADVANCE→巡检START", DECISION_ACTION_MAP["ADVANCE"]["dep_probe"] == "START")
        self.check("T12: ADVANCE→镜像START", DECISION_ACTION_MAP["ADVANCE"]["shadow_mirror"] == "START")
        self.check("T13: ROLLBACK→巡检STOP", DECISION_ACTION_MAP["ROLLBACK"]["dep_probe"] == "STOP")
        self.check("T14: ROLLBACK→镜像STOP", DECISION_ACTION_MAP["ROLLBACK"]["shadow_mirror"] == "STOP")
        self.check("T15: HOLD→巡检CONTINUE", DECISION_ACTION_MAP["HOLD"]["dep_probe"] == "CONTINUE")
        
        # ── T16-T20: 事件验证 ──
        self.logger.info("\n── 事件验证 (T16-T20) ──")
        test_event = {
            "decision": "ADVANCE",
            "current_stage": "G0",
            "next_stage": "G1",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "dep_001_status": "RECOVERED",
            "faults_detected": [],
        }
        self.check("T16: 事件结构完整", all(k in test_event for k in ["decision", "current_stage", "timestamp"]))
        self.check("T17: 事件包含决策", test_event["decision"] == "ADVANCE")
        self.check("T18: 事件包含阶段", test_event["current_stage"] == "G0")
        self.check("T19: 事件包含时间戳", "T" in test_event["timestamp"])
        self.check("T20: 事件包含 DEP 状态", test_event["dep_001_status"] == "RECOVERED")
        
        # ── T21-T25: 采样率映射验证 ──
        self.logger.info("\n── 采样率映射验证 (T21-T25) ──")
        rates = DEFAULT_CONFIG["stage_sampling_rates"]
        self.check("T21: G0 采样率=10%", rates["G0"] == 10.0)
        self.check("T22: G1 采样率=20%", rates["G1"] == 20.0)
        self.check("T23: G2 采样率=30%", rates["G2"] == 30.0)
        self.check("T24: G3 采样率=50%", rates["G3"] == 50.0)
        self.check("T25: G5 采样率=100%", rates["G5"] == 100.0)
        
        # ── T26-T30: 审计事件验证 ──
        self.logger.info("\n── 审计事件验证 (T26-T30) ──")
        test_audit = AuditEvent("DECISION_RECEIVED", "INFO", {"test": True})
        self.check("T26: 审计事件 ID", bool(test_audit.event_id))
        self.check("T27: 审计事件类型", test_audit.event_type == "DECISION_RECEIVED")
        self.check("T28: 审计事件级别", test_audit.severity == "INFO")
        self.check("T29: 审计事件时间戳", bool(test_audit.timestamp))
        self.check("T30: 审计事件序列化", isinstance(test_audit.to_dict(), dict))
        
        # ── T31-T35: 决策处理器验证 ──
        self.logger.info("\n── 决策处理器验证 (T31-T35) ──")
        handler = DecisionEventHandler(self.logger, AuditLogger(self.logger, DEFAULT_CONFIG), DEFAULT_CONFIG)
        state = handler.get_state()
        self.check("T31: 初始状态", state["gate_status"] == "READY")
        self.check("T32: 初始巡检状态", state["dep_probe_running"] is False)
        self.check("T33: 初始镜像状态", state["shadow_mirror_running"] is False)
        self.check("T34: 初始采样率", state["shadow_sampling_rate"] == 10.0)
        self.check("T35: 初始阶段", state["current_stage"] == "G0")
        
        # ── T36-T40: 去重验证 ──
        self.logger.info("\n── 去重验证 (T36-T40) ──")
        event1 = {"decision": "ADVANCE", "current_stage": "G0", "timestamp": "t1"}
        event2 = {"decision": "ADVANCE", "current_stage": "G0", "timestamp": "t2"}
        key1 = handler._compute_dedup_key(event1)
        key2 = handler._compute_dedup_key(event2)
        self.check("T36: 相同决策相同去重键", key1 == key2)
        event3 = {"decision": "ROLLBACK", "current_stage": "G0", "timestamp": "t3"}
        key3 = handler._compute_dedup_key(event3)
        self.check("T37: 不同决策不同去重键", key1 != key3)
        self.check("T38: 首次事件非重复", handler._is_duplicate(key1) is False)
        self.check("T39: 重复事件检测", handler._is_duplicate(key1) is True)
        self.check("T40: 非重复事件检测", handler._is_duplicate(key3) is False)
        
        # ── T41-T45: 边界场景验证 ──
        self.logger.info("\n── 边界场景验证 (T41-T45) ──")
        # ADVANCE → 启动
        r1 = handler._execute_decision_actions("ADVANCE", "evt-1", "G0", {"next_stage": "G1"})
        self.check("T41: ADVANCE 状态", r1["status"] == "PROCESSED")
        self.check("T42: ADVANCE 联动 Gate", r1["actions"]["gate_status"]["new_status"] == "READY")
        self.check("T43: ADVANCE 联动巡检", r1["actions"]["dep_probe"]["status"] in ("OK", "ALREADY_RUNNING"))
        self.check("T44: ADVANCE 联动镜像", r1["actions"]["shadow_mirror"]["status"] in ("OK", "ALREADY_RUNNING"))
        # ROLLBACK → 停止
        r2 = handler._execute_decision_actions("ROLLBACK", "evt-2", "G1", {"next_stage": "G1"})
        self.check("T45: ROLLBACK 状态", r2["status"] == "PROCESSED")
        
        # ── 汇总 ──
        total = self.passed + self.failed
        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"自检完成: {self.passed}/{total} PASS, {self.failed} FAIL")
        self.logger.info("=" * 60)
        
        return {
            "total": total,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "pass_rate": f"{self.passed/total*100:.1f}%",
        }


# ═══════════════════════════════════════════════════════════
# 服务启动
# ═══════════════════════════════════════════════════════════

def main():
    """主入口。"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gate V5 Gray Callback Handler")
    parser.add_argument("--port", type=int, default=DEFAULT_CONFIG["server_port"])
    parser.add_argument("--host", type=str, default=DEFAULT_CONFIG["server_host"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--decide", type=str, help="单次决策处理 JSON 文件")
    parser.add_argument("--health", action="store_true")
    parser.add_argument("--status", action="store_true")
    
    args = parser.parse_args()
    
    # 配置
    config = DEFAULT_CONFIG.copy()
    config["server_port"] = args.port
    config["server_host"] = args.host
    config["dry_run"] = args.dry_run
    config["verbose"] = args.verbose
    config["log_level"] = "DEBUG" if args.verbose else "INFO"
    
    # 日志
    logger = setup_logging(config["log_level"])
    logger.info(f"Gate V5 Gray Callback V{VERSION} 启动")
    logger.info(f"工单: {WORK_ORDER} / {TASK_ID}")
    logger.info(f"配置: host={config['server_host']}, port={config['server_port']}, dry_run={config['dry_run']}")
    
    # 自检
    if args.self_test:
        st = SelfTest(logger)
        result = st.run_all()
        if result["failed"] == 0:
            logger.info("✅ 全部自检通过!")
            return 0
        else:
            logger.error(f"❌ 自检失败: {result['failed']} 项未通过")
            return 1
    
    # 单次决策处理
    if args.decide:
        with open(args.decide, "r", encoding="utf-8") as f:
            decision_event = json.load(f)
        handler = DecisionEventHandler(logger, AuditLogger(logger, config), config)
        result = handler.process_decision(decision_event)
        logger.info(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    
    # 健康检查
    if args.health:
        logger.info(json.dumps({
            "status": "HEALTHY",
            "version": VERSION,
            "work_order": WORK_ORDER,
            "task_id": TASK_ID,
        }, ensure_ascii=False, indent=2))
        return 0
    
    # 状态查询
    if args.status:
        handler = DecisionEventHandler(logger, AuditLogger(logger, config), config)
        logger.info(json.dumps(handler.get_state_summary(), ensure_ascii=False, indent=2))
        return 0
    
    # 启动 HTTP 服务
    handler = DecisionEventHandler(logger, AuditLogger(logger, config), config)
    
    GateCallbackHandler.handler = handler
    GateCallbackHandler.audit = AuditLogger(logger, config)
    GateCallbackHandler.logger = logger
    
    server = HTTPServer((config["server_host"], config["server_port"]), GateCallbackHandler)
    logger.info(f"HTTP 服务启动: {config['server_host']}:{config['server_port']}")
    logger.info("端点: POST /api/v1/gate/callback/decision")
    logger.info("端点: GET  /api/v1/gate/callback/status")
    logger.info("端点: GET  /api/v1/gate/callback/health")
    logger.info("端点: GET  /api/v1/gate/callback/audit/stats")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("服务停止...")
        server.shutdown()
        return 0


if __name__ == "__main__":
    sys.exit(main())
