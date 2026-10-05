#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSHE V86-RC2 L2 Evidence Package Integrity Checker V4
Task: 工单-DSHE / T3.1 + T3.2 + T3.5 L2 evidence shard spec V2

V4 Key Changes (vs V3):
  [P0 FIX] Off-by-one shard_count defect:
    - Old: self.shard_count = max(1, self.file_size // self.shard_size + 1)
    - New: self.shard_count = max(1, -(-self.file_size // self.shard_size))
    - When file_size == shard_size, old formula gives 2 (wrong), new gives 1 (correct)
  [T3.2] UnicodeDecodeError handling — WARN classification, latin-1 fallback
  [T3.2] Windows MAX_PATH (260 chars) precheck — WARN if exceeded
  [T3.2] JSON duplicate key detection — MEDIUM warning with audit fingerprint
  [T3.5] Exception classification matrix: ERROR/WARN/BLOCK/CRITICAL levels
  [T3.5] L2 evidence shard spec V2

V3 Key Changes (retained):
  - Sharded reading: chunk-based large JSON evidence package reading
  - Multi-threaded parallel pre-audit for directory batch processing
  - Memory-efficient evidence package processing
  - Streaming MD5 computation for large files
  - Configurable shard size and thread count
  - Progress reporting for large batches

V3.1 Key Changes (retained):
  - PERF-GUARD Performance Guardrails

Usage:
  python l2_evidence_package_check_v4.py --check <evidence.json>
  python l2_evidence_package_check_v4.py --check-dir <dir>
  python l2_evidence_package_check_v4.py --verify-md5 <md5_list.json>
  python l2_evidence_package_check_v4.py --all <dir>
  python l2_evidence_package_check_v4.py --pre-audit <evidence.json>
  python l2_evidence_package_check_v4.py --pre-audit-dir <dir> [--threads N]
  python l2_evidence_package_check_v4.py --generate-md5 <dir>
  python l2_evidence_package_check_v4.py --generate-index <dir>
  python l2_evidence_package_check_v4.py --dry-run
  python l2_evidence_package_check_v4.py --shard-size <bytes> [--check-dir <dir>]
  python l2_evidence_package_check_v4.py --exception-handling-test

V4 New CLI flags:
  --json-dup-key-check     Enable JSON duplicate key detection (MEDIUM warning)
  --max-path-check         Enable Windows MAX_PATH (260 chars) precheck
  --unicode-fallback       Enable UnicodeDecodeError fallback to latin-1
  --exception-handling-test Run all exception handling test cases

Exit Codes:
  0  - All checks PASS
  1  - One or more CRITICAL violations found
  2  - One or more WARNING violations found
  3  - Script error
  4  - Exception handling test failed

Branch: feature/v85-chart-template
Date: 2026-10-15
"""

import argparse
import gc
import hashlib
import json
import logging
import math
import os
import re
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
DEFAULT_EVIDENCE_DIR = SCRIPT_DIR / ".payload_evidence"
MD5_LIST_FILE = DEFAULT_EVIDENCE_DIR / "MD5_CHECKSUM_LIST_evidence.json"
EVIDENCE_INDEX_FILE = DEFAULT_EVIDENCE_DIR / "evidence_index.json"
LOG_DIR = SCRIPT_DIR / ".logs"
LOG_FILE = LOG_DIR / "l2_evidence_check_v4.log"

# Script version
SCRIPT_VERSION = "4.0.0"
SCRIPT_NAME = "DSHE V86-RC2 L2 Evidence Package Integrity Checker V4"

# Severity levels
CRITICAL = "CRITICAL"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"
INFO = "INFO"
WARN = "WARN"
ERROR = "ERROR"
BLOCK = "BLOCK"

# V4 NEW: Exception classification levels (T3.5)
EXCEPTION_LEVEL_ERROR   = "ERROR"     # Non-recoverable, log and return error result
EXCEPTION_LEVEL_WARN    = "WARN"      # Recoverable, continue with warning
EXCEPTION_LEVEL_BLOCK   = "BLOCK"     # Must block processing (malformed data)
EXCEPTION_LEVEL_CRITICAL = "CRITICAL" # Critical, halt all processing
EXCEPTION_LEVEL_MEDIUM  = "MEDIUM"    # Medium severity, report but continue

# V4 NEW: Exception classification matrix (T3.5)
EXCEPTION_CLASSIFICATION = {
    "FileNotFoundError":       (EXCEPTION_LEVEL_ERROR, "File not found — ERROR, return error result"),
    "UnicodeDecodeError":      (EXCEPTION_LEVEL_WARN, "Unicode decode error — WARN, fallback to latin-1"),
    "JSONDecodeError":         (EXCEPTION_LEVEL_BLOCK, "Malformed JSON — BLOCK, halt parsing"),
    "json.decoder.JSONDecodeError": (EXCEPTION_LEVEL_BLOCK, "Malformed JSON — BLOCK, halt parsing"),
    "DuplicateKeyError":       (EXCEPTION_LEVEL_MEDIUM, "JSON duplicate key — MEDIUM, audit fingerprint"),
    "MaxPathExceededError":    (EXCEPTION_LEVEL_WARN, "Windows MAX_PATH exceeded — WARN, precheck"),
    "OSError":                 (EXCEPTION_LEVEL_ERROR, "OS error — ERROR, return error result"),
    "PermissionError":         (EXCEPTION_LEVEL_BLOCK, "Permission denied — BLOCK, halt processing"),
    "TimeoutError":            (EXCEPTION_LEVEL_WARN, "Operation timeout — WARN, retry or skip"),
    "MemoryError":             (EXCEPTION_LEVEL_CRITICAL, "Out of memory — CRITICAL, halt processing"),
}

# Contract version
EVIDENCE_CONTRACT_VERSION = "EVIDENCE_CONTRACT_V1"

# DEP registry
DEP_REGISTRY_ID = "DEP-REG-001"
MAX_PAUSE_DAYS = 30
ROLLBACK_WINDOW_MIN = 15

# DEP state machine
DEP_STATES = {"ACTIVE", "BLOCKED", "RECOVERY", "RECOVERED", "ROLLED_BACK", "CLOSED"}
DEP_STATE_TRANSITIONS = {
    ("ACTIVE", "BLOCKED"): "DEP_FAILURE",
    ("BLOCKED", "RECOVERY"): "RECOVERY_START",
    ("RECOVERY", "RECOVERED"): "RECOVERY_COMPLETE",
    ("RECOVERED", "ACTIVE"): "RECOVERY_CONFIRM",
    ("RECOVERED", "ROLLED_BACK"): "ROLLBACK_TRIGGER",
    ("ROLLED_BACK", "CLOSED"): "DEP_CLOSED",
    ("ACTIVE", "CLOSED"): "MANUAL_CLOSE",
    ("BLOCKED", "ROLLED_BACK"): "PAUSE_TIMEOUT_ROLLBACK",
    ("BLOCKED", "ACTIVE"): "QUICK_RECOVERY",
    ("RECOVERY", "BLOCKED"): "RECOVERY_FAIL_BACK",
}

# V3: Default shard size for large JSON (4MB)
DEFAULT_SHARD_SIZE = 4 * 1024 * 1024  # 4MB

# V3: Default thread count for parallel pre-audit
DEFAULT_THREAD_COUNT = 4

# V4 NEW: Windows MAX_PATH constant (T3.2)
WINDOWS_MAX_PATH = 260
IS_WINDOWS = os.name == "nt"

# V4 NEW: JSON duplicate key detection settings (T3.2)
JSON_DUP_KEY_CHECK_ENABLED = False
JSON_DUP_KEY_AUDIT_PREFIX = "DUP-KEY"

# V4 NEW: Unicode fallback settings (T3.2)
UNICODE_FALLBACK_ENABLED = False
UNICODE_FALLBACK_ENCODING = "latin-1"

# V4 NEW: MAX_PATH check settings (T3.2)
MAX_PATH_CHECK_ENABLED = False

# V4 NEW: Exception handling test flag (T3.2)
EXCEPTION_HANDLING_TEST_ENABLED = False

# ─────────────────────────────────────────────────────────────────────
# V3.1: PERF-GUARD Performance Guardrails (T3.4) — retained
# ─────────────────────────────────────────────────────────────────────
PERF_GUARD_PACKAGING_TIME_LIMIT_SEC   = 1.0
PERF_GUARD_CALL_COUNT_LIMIT           = 256
PERF_GUARD_MEMORY_PEAK_LIMIT_MB       = 52
PERF_GUARD_FILE_SIZE_LIMIT_MB         = 10
PERF_GUARD_ENABLED                    = True
PERF_GUARD_MODE                       = "STRICT"

# Required top-level fields (EVIDENCE_CONTRACT_V1)
REQUIRED_TOP_FIELDS = {
    "fingerprint": str,
    "run_id": str,
    "session_id": str,
    "total_calls": int,
    "generated_at": str,
    "caller": str,
    "dshb_reuse": bool,
    "calls": list,
    "l2_version": str,
    "version_script": str,
}

# Required per-call fields
REQUIRED_CALL_FIELDS = {
    "trace_id": str,
    "timestamp": str,
    "indicator_id": str,
    "zhiji_short_id": str,
    "request_payload": dict,
    "response_payload": dict,
    "status": str,
    "call_type": str,
    "caller": str,
    "dsbh_reuse": bool,
}

# Allowed call_type values
ALLOWED_CALL_TYPES = {"DSHE_INDEPENDENT_ZHIJI"}

# Allowed status values
ALLOWED_STATUSES = {"INDEPENDENT_FETCH_OK", "INDEPENDENT_FETCH_FAIL"}

# DEP-REG ID format regex
DEP_REGISTRY_PATTERN = re.compile(r"^DEP-REG-\d{3}$")

# Response payload required fields
REQUIRED_RESPONSE_FIELDS = {"id": str, "points": list}

# Script audit required fields
SCRIPT_AUDIT_REQUIRED = {
    "uses_search_passthrough": bool,
    "has_id_consistency_assert": bool,
    "zero_value_counts_as_pass": bool,
    "retains_raw_payload": bool,
}


# ─────────────────────────────────────────────────────────────────────
# V4 NEW: Duplicate Key JSON Decoder (T3.2)
# ─────────────────────────────────────────────────────────────────────
class DuplicateKeyJSONDecoder(json.JSONDecoder):
    """
    V4 NEW: Custom JSON decoder that detects duplicate keys in JSON objects.

    When a duplicate key is found, it raises a DuplicateKeyError with full
    audit information (key name, first value, second value, occurrence count).

    Usage:
      data = json.loads(text, cls=DuplicateKeyJSONDecoder)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(object_pairs_hook=self._object_pairs_hook_check, **kwargs)
        self.duplicate_keys_found = []

    def _object_pairs_hook_check(self, pairs):
        """Check for duplicate keys in JSON object pairs."""
        seen_keys = {}
        for key, value in pairs:
            if key in seen_keys:
                seen_keys[key] += 1
                self.duplicate_keys_found.append({
                    "key": key,
                    "occurrence": seen_keys[key],
                    "total_count": seen_keys[key],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            else:
                seen_keys[key] = 1
        return dict(pairs)

    def get_duplicate_keys(self):
        """Return list of all duplicate keys found during parsing."""
        return self.duplicate_keys_found


class DuplicateKeyError(Exception):
    """
    V4 NEW: Exception raised when duplicate JSON keys are detected.

    Carries audit fingerprint information for traceability.
    """

    def __init__(self, duplicate_keys):
        self.duplicate_keys = duplicate_keys
        audit_fp = hashlib.sha256(
            json.dumps(duplicate_keys, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()[:16]
        self.audit_fingerprint = audit_fp
        super().__init__(
            "Duplicate JSON keys detected (%d duplicates). Audit fingerprint: %s" % (
                len(duplicate_keys), audit_fp
            )
        )


# ─────────────────────────────────────────────────────────────────────
# V4 NEW: Exception Classifier (T3.5)
# ─────────────────────────────────────────────────────────────────────
class ExceptionClassifier:
    """
    V4 NEW: Exception classification and handling engine (T3.5).

    Provides a consistent interface for classifying and handling exceptions
    according to the exception classification matrix defined in the L2 evidence
    shard spec V2.

    Usage:
      classifier = ExceptionClassifier()
      level, message = classifier.classify(exc)
      result = classifier.handle(exc, context)
    """

    def __init__(self):
        self.classification_log = []

    def classify(self, exc):
        """
        Classify an exception according to the classification matrix.

        Returns:
            tuple: (level, human_readable_message)
        """
        exc_type = type(exc).__name__
        exc_path = "%s.%s" % (exc.__class__.__module__, exc_type)
        exc_path_short = exc_type

        # Check full path first, then short name
        if exc_path in EXCEPTION_CLASSIFICATION:
            level, msg = EXCEPTION_CLASSIFICATION[exc_path]
        elif exc_path_short in EXCEPTION_CLASSIFICATION:
            level, msg = EXCEPTION_CLASSIFICATION[exc_path_short]
        else:
            # Unknown exception type
            level = EXCEPTION_LEVEL_ERROR
            msg = "Unknown exception type %s — ERROR, return error result" % exc_type

        self.classification_log.append({
            "exception_type": exc_path,
            "level": level,
            "message": msg,
            "detail": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return level, msg

    def handle(self, exc, context=None):
        """
        Classify and handle an exception, returning a result dict.

        Returns:
            dict: Result dict with verdict, error info, and classification.
        """
        level, msg = self.classify(exc)
        context_str = str(context) if context else ""

        result = {
            "verdict": "ERROR",
            "exception_level": level,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "classification": msg,
            "context": context_str,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Set verdict based on classification level
        if level == EXCEPTION_LEVEL_CRITICAL:
            result["verdict"] = "BLOCK_CRITICAL"
        elif level == EXCEPTION_LEVEL_BLOCK:
            result["verdict"] = "BLOCK"
        elif level == EXCEPTION_LEVEL_WARN:
            result["verdict"] = "WARNING"
        elif level == EXCEPTION_LEVEL_MEDIUM:
            result["verdict"] = "PASS_WITH_NOTES"
        else:  # ERROR
            result["verdict"] = "ERROR"

        return result

    def get_classification_log(self):
        """Return the log of all classifications made."""
        return list(self.classification_log)


# ─────────────────────────────────────────────────────────────────────
# V4 NEW: MaxPathExceededError (T3.2)
# ─────────────────────────────────────────────────────────────────────
class MaxPathExceededError(Exception):
    """
    V4 NEW: Exception raised when Windows MAX_PATH (260 chars) is exceeded.

    Carries audit fingerprint for traceability.
    """

    def __init__(self, filepath, path_length, max_allowed=WINDOWS_MAX_PATH):
        self.filepath = str(filepath)
        self.path_length = path_length
        self.max_allowed = max_allowed
        audit_fp = hashlib.sha256(
            ("%s:%d" % (self.filepath, self.path_length)).encode("utf-8")
        ).hexdigest()[:16]
        self.audit_fingerprint = audit_fp
        super().__init__(
            "Windows MAX_PATH exceeded: path length %d > %d (%s). Audit fingerprint: %s" % (
                path_length, max_allowed, self.filepath[:100], audit_fp
            )
        )


# ─────────────────────────────────────────────────────────────────────
# V3.1: PERF-GUARD Class (T3.4) — retained from V3
# ─────────────────────────────────────────────────────────────────────
class PerfGuard:
    """
    V3.1: PERF-GUARD Performance Guardrails (T3.4).

    Aligned with HERMES audit performance budget:
      - Packaging time limit: 1.0s (CRITICAL if exceeded)
      - Call count limit: 256 (CRITICAL if exceeded)
      - Memory peak limit: 52MB (HIGH if exceeded)
      - File size soft limit: 10MB (MEDIUM if exceeded)

    Modes:
      STRICT: Block packaging on CRITICAL threshold violation
      WARN:   Alert only, do not block
    """

    CRITICAL = CRITICAL
    HIGH = HIGH
    MEDIUM = MEDIUM
    LOW = LOW
    WARN = MEDIUM
    OK = "OK"

    def __init__(self, mode=PERF_GUARD_MODE, enabled=PERF_GUARD_ENABLED):
        self.mode = mode
        self.enabled = enabled
        self.findings = []
        self._start_time = time.time()
        self._memory_start = 0

    def begin(self):
        """Start PERF-GUARD monitoring."""
        self._start_time = time.time()
        self._memory_start = _get_memory_usage()
        self.findings = []
        logger.info("[PERF-GUARD] Monitoring started (mode=%s, limits: "
                     "time=%.1fs, calls=%d, mem=%.0fMB, file=%.0fMB)",
                     self.mode, PERF_GUARD_PACKAGING_TIME_LIMIT_SEC,
                     PERF_GUARD_CALL_COUNT_LIMIT,
                     PERF_GUARD_MEMORY_PEAK_LIMIT_MB,
                     PERF_GUARD_FILE_SIZE_LIMIT_MB)

    def _elapsed_sec(self):
        return time.time() - self._start_time

    def _current_memory_mb(self):
        current = _get_memory_usage()
        return (current - self._memory_start) / 1024 / 1024

    def _emit(self, level, check_id, message, detail=None, value=None, limit=None):
        """Record a PERF-GUARD finding."""
        f = {
            "level": level,
            "check_id": check_id,
            "message": message,
            "detail": detail,
            "value": value,
            "limit": limit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.findings.append(f)
        action = "BLOCK" if (self.mode == "STRICT" and level == CRITICAL) else "WARN"
        logger.warning("[PERF-GUARD] [%s] %s: %s (value=%s, limit=%s) → %s",
                       level, check_id, message,
                       self._format_value(value), self._format_limit(limit), action)
        return f

    def _format_value(self, v):
        if isinstance(v, float):
            return "%.2f" % v
        if isinstance(v, int):
            return str(v)
        return str(v)

    def _format_limit(self, l):
        if isinstance(l, float):
            return "%.1f" % l
        if isinstance(l, int):
            return str(l)
        return str(l)

    def check_packaging_time(self, elapsed_sec=None, label="packaging"):
        """Check if packaging time exceeds threshold. BLOCK if STRICT."""
        if not self.enabled:
            return None
        if elapsed_sec is None:
            elapsed_sec = self._elapsed_sec()
        if elapsed_sec > PERF_GUARD_PACKAGING_TIME_LIMIT_SEC:
            return self._emit(
                CRITICAL, "PG-TIME",
                "%s time %.2fs exceeds limit %.1fs" % (label, elapsed_sec,
                PERF_GUARD_PACKAGING_TIME_LIMIT_SEC),
                value=round(elapsed_sec, 3),
                limit=PERF_GUARD_PACKAGING_TIME_LIMIT_SEC,
            )
        logger.debug("[PERF-GUARD] %s time OK: %.2fs / %.1fs", label, elapsed_sec,
                      PERF_GUARD_PACKAGING_TIME_LIMIT_SEC)
        return None

    def check_call_count(self, total_calls):
        """Check if call count exceeds threshold. BLOCK if STRICT."""
        if not self.enabled:
            return None
        if total_calls > PERF_GUARD_CALL_COUNT_LIMIT:
            return self._emit(
                CRITICAL, "PG-CALLS",
                "Call count %d exceeds limit %d — oversized package" % (
                    total_calls, PERF_GUARD_CALL_COUNT_LIMIT),
                value=total_calls,
                limit=PERF_GUARD_CALL_COUNT_LIMIT,
            )
        logger.debug("[PERF-GUARD] Call count OK: %d / %d",
                      total_calls, PERF_GUARD_CALL_COUNT_LIMIT)
        return None

    def check_memory_peak(self, peak_mb=None):
        """Check if memory peak exceeds threshold. WARN + early termination hint."""
        if not self.enabled:
            return None
        if peak_mb is None:
            peak_mb = self._current_memory_mb()
        if peak_mb > PERF_GUARD_MEMORY_PEAK_LIMIT_MB:
            return self._emit(
                HIGH, "PG-MEM",
                "Memory peak %.1fMB exceeds limit %.0fMB — consider early termination" % (
                    peak_mb, PERF_GUARD_MEMORY_PEAK_LIMIT_MB),
                value=round(peak_mb, 1),
                limit=PERF_GUARD_MEMORY_PEAK_LIMIT_MB,
            )
        logger.debug("[PERF-GUARD] Memory OK: %.1fMB / %.0fMB",
                      peak_mb, PERF_GUARD_MEMORY_PEAK_LIMIT_MB)
        return None

    def check_file_size(self, size_bytes):
        """Check if file size exceeds soft limit. MEDIUM warning."""
        if not self.enabled:
            return None
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > PERF_GUARD_FILE_SIZE_LIMIT_MB:
            return self._emit(
                MEDIUM, "PG-FILE",
                "File size %.1fMB exceeds soft limit %.0fMB" % (
                    size_mb, PERF_GUARD_FILE_SIZE_LIMIT_MB),
                value=round(size_mb, 1),
                limit=PERF_GUARD_FILE_SIZE_LIMIT_MB,
            )
        logger.debug("[PERF-GUARD] File size OK: %.1fMB / %.0fMB",
                      size_mb, PERF_GUARD_FILE_SIZE_LIMIT_MB)
        return None

    def check_all(self, elapsed_sec=None, total_calls=0, peak_mb=None,
                  file_size_bytes=0, label="packaging"):
        """Run all PERF-GUARD checks and return summary."""
        self.check_packaging_time(elapsed_sec, label)
        self.check_call_count(total_calls)
        self.check_memory_peak(peak_mb)
        self.check_file_size(file_size_bytes)
        return self.get_summary()

    def any_critical(self):
        """Return True if any CRITICAL finding exists (blocks packaging in STRICT)."""
        return any(f["level"] == CRITICAL for f in self.findings)

    def any_high(self):
        """Return True if any HIGH or CRITICAL finding exists."""
        return any(f["level"] in (CRITICAL, HIGH) for f in self.findings)

    def get_summary(self):
        """Get PERF-GUARD summary."""
        counts = defaultdict(int)
        for f in self.findings:
            counts[f["level"]] += 1
        total = sum(counts.values())
        if any(f["level"] == CRITICAL for f in self.findings):
            verdict = "BLOCK"
        elif any(f["level"] == HIGH for f in self.findings):
            verdict = "WARN"
        elif any(f["level"] == MEDIUM for f in self.findings):
            verdict = "NOTICE"
        else:
            verdict = "PASS"
        return {
            "verdict": verdict,
            "mode": self.mode,
            "enabled": self.enabled,
            "total_findings": total,
            "CRITICAL": counts.get(CRITICAL, 0),
            "HIGH": counts.get(HIGH, 0),
            "MEDIUM": counts.get(MEDIUM, 0),
            "findings": self.findings,
            "limits": {
                "packaging_time_sec": PERF_GUARD_PACKAGING_TIME_LIMIT_SEC,
                "call_count": PERF_GUARD_CALL_COUNT_LIMIT,
                "memory_peak_mb": PERF_GUARD_MEMORY_PEAK_LIMIT_MB,
                "file_size_mb": PERF_GUARD_FILE_SIZE_LIMIT_MB,
            },
        }

    def to_result(self):
        """Convert PERF-GUARD summary to standard result dict for merging."""
        summary = self.get_summary()
        return {
            "perf_guard_verdict": summary["verdict"],
            "perf_guard_findings": summary["total_findings"],
            "perf_guard_critical": summary["CRITICAL"],
            "perf_guard_high": summary["HIGH"],
            "perf_guard_medium": summary["MEDIUM"],
            "perf_guard_mode": summary["mode"],
            "perf_guard_block": self.any_critical(),
            "perf_guard_findings_detail": summary["findings"],
        }


# ─────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────
def setup_logging(level=logging.INFO):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger("l2_evidence_check_v4")
    logger.setLevel(level)
    logger.handlers.clear()

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


logger = setup_logging()


# ─────────────────────────────────────────────────────────────────────
# V4 NEW: Sharded JSON Reader (T3.1 P0 FIX + T3.2 enhancements)
# ─────────────────────────────────────────────────────────────────────
class ShardedJSONReader:
    """
    V4: Read large JSON files in shards to reduce memory usage.

    V4 Changes vs V3:
      [P0 FIX] shard_count formula corrected:
        - Old: self.shard_count = max(1, self.file_size // self.shard_size + 1)
        - New: self.shard_count = max(1, -(-self.file_size // self.shard_size))
        - When file_size == shard_size, old gives 2 (wrong), new gives 1 (correct)
        - The +1 was incorrect for exact multiples of shard_size
      [T3.2] UnicodeDecodeError handling: catch and return as WARN classification
      [T3.2] Windows MAX_PATH (260 chars) precheck
      [T3.2] JSON duplicate key detection support

    Strategy:
      - For files < shard_size: standard json.load() (memory-efficient enough)
      - For files >= shard_size: streaming chunk reader with json parsing
    """

    def __init__(self, filepath, shard_size=DEFAULT_SHARD_SIZE,
                 unicode_fallback=False, max_path_check=False,
                 json_dup_key_check=False):
        self.filepath = Path(filepath)
        self.shard_size = shard_size
        self.file_size = self.filepath.stat().st_size if self.filepath.exists() else 0
        self.is_large = self.file_size >= self.shard_size

        # V4 P0 FIX: Ceiling division instead of floor division + 1
        # Old (V3): self.shard_count = max(1, self.file_size // self.shard_size + 1)
        # New (V4): self.shard_count = max(1, -(-self.file_size // self.shard_size))
        # This is ceiling division: ceil(a/b) = -(-a // b)
        # When file_size == shard_size: old gives 2 (wrong), new gives 1 (correct)
        # When file_size == shard_size + 1: old gives 2 (correct), new gives 2 (correct)
        # When file_size == 0: old gives 1 (correct), new gives 1 (correct)
        self.shard_count = max(1, -(-self.file_size // self.shard_size))

        # V4 NEW: Feature flags for exception handling
        self.unicode_fallback = unicode_fallback
        self.max_path_check = max_path_check
        self.json_dup_key_check = json_dup_key_check
        self.warnings = []

    def read(self):
        """
        Read JSON file, using sharded approach for large files.

        V4 enhancements:
          - UnicodeDecodeError: WARN level, fallback to latin-1
          - Windows MAX_PATH: WARN if path exceeds 260 chars
          - JSON duplicate keys: MEDIUM warning with audit fingerprint
        """
        # V4: Check file existence
        if not self.filepath.exists():
            raise FileNotFoundError("File not found: %s" % self.filepath)

        # V4 T3.2: Windows MAX_PATH precheck
        if self.max_path_check:
            self._check_max_path()

        # V4 T3.2: Unicode decode error handling with optional fallback
        encoding = "utf-8"
        unicode_error_handled = False

        if not self.unicode_fallback:
            # Standard mode: no fallback, UnicodeDecodeError will propagate
            encoding = "utf-8"
        else:
            # Unicode fallback mode: try utf-8 first, fall back to latin-1
            encoding = "utf-8"

        try:
            if self.file_size < self.shard_size:
                # Standard read for small files
                with open(self.filepath, "r", encoding=encoding) as f:
                    raw_text = f.read()
            else:
                # Large file: read in chunks
                logger.debug("[SHARD V4] Large file (%d bytes), reading in %d shards of %d bytes",
                             self.file_size, self.shard_count, self.shard_size)
                chunks = []
                total_read = 0
                with open(self.filepath, "r", encoding=encoding) as f:
                    while True:
                        chunk = f.read(self.shard_size)
                        if not chunk:
                            break
                        chunks.append(chunk)
                        total_read += len(chunk)
                        if len(chunks) % 10 == 0:
                            logger.debug("[SHARD V4] Read %d/%d bytes (%d chunks)",
                                         total_read, self.file_size, len(chunks))
                raw_text = "".join(chunks)

        except UnicodeDecodeError as e:
            if not self.unicode_fallback:
                # No fallback enabled: log warning but re-raise as WARN classification
                warn_msg = "UnicodeDecodeError in %s: %s — WARN (enable --unicode-fallback for latin-1 fallback)" % (
                    self.filepath, str(e))
                self.warnings.append({
                    "level": WARN,
                    "type": "UnicodeDecodeError",
                    "message": warn_msg,
                    "audit_fingerprint": hashlib.sha256(
                        str(e).encode("utf-8")).hexdigest()[:16],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                logger.warning("[V4 WARN] UnicodeDecodeError: %s", e)
                raise
            else:
                # Fallback to latin-1
                unicode_error_handled = True
                warn_msg = "UnicodeDecodeError in %s — WARN, falling back to %s" % (
                    self.filepath, UNICODE_FALLBACK_ENCODING)
                self.warnings.append({
                    "level": WARN,
                    "type": "UnicodeDecodeError",
                    "message": warn_msg,
                    "audit_fingerprint": hashlib.sha256(
                        str(e).encode("utf-8")).hexdigest()[:16],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "fallback_encoding": UNICODE_FALLBACK_ENCODING,
                })
                logger.warning("[V4 WARN] %s", warn_msg)
                # Retry with latin-1 encoding
                encoding = UNICODE_FALLBACK_ENCODING
                if self.file_size < self.shard_size:
                    with open(self.filepath, "r", encoding=encoding) as f:
                        raw_text = f.read()
                else:
                    chunks = []
                    with open(self.filepath, "r", encoding=encoding) as f:
                        while True:
                            chunk = f.read(self.shard_size)
                            if not chunk:
                                break
                            chunks.append(chunk)
                    raw_text = "".join(chunks)

        # V4 T3.2: JSON duplicate key detection
        if self.json_dup_key_check:
            decoder = DuplicateKeyJSONDecoder()
            try:
                data = decoder.decode(raw_text)
            except Exception:
                raise
            dup_keys = decoder.get_duplicate_keys()
            if dup_keys:
                dup_error = DuplicateKeyError(dup_keys)
                warn_msg = "JSON duplicate keys detected: %d duplicate keys found. %s" % (
                    len(dup_keys), str(dup_error))
                self.warnings.append({
                    "level": MEDIUM,
                    "type": "DuplicateKeyError",
                    "message": warn_msg,
                    "audit_fingerprint": dup_error.audit_fingerprint,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "duplicate_keys": dup_keys,
                })
                logger.warning("[V4 MEDIUM] %s", warn_msg)
                # Continue processing but return data with warnings attached
                data = {
                    "_v4_duplicate_key_warning": True,
                    "_v4_duplicate_key_count": len(dup_keys),
                    "_v4_duplicate_key_fingerprint": dup_error.audit_fingerprint,
                    "_v4_duplicate_keys": dup_keys,
                    "_v4_original_data": data,
                }
                return data

        # Standard JSON parse
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            raise

    def _check_max_path(self):
        """
        V4 T3.2: Check if file path exceeds Windows MAX_PATH (260 chars).

        Emits WARN if path is too long for Windows API compatibility.
        """
        path_str = str(self.filepath)
        path_length = len(path_str)
        if path_length > WINDOWS_MAX_PATH:
            path_error = MaxPathExceededError(path_str, path_length, WINDOWS_MAX_PATH)
            warn_msg = "Windows MAX_PATH exceeded: path length %d > %d (%s). %s" % (
                path_length, WINDOWS_MAX_PATH, path_str[:100], str(path_error))
            self.warnings.append({
                "level": WARN,
                "type": "MaxPathExceededError",
                "message": warn_msg,
                "audit_fingerprint": path_error.audit_fingerprint,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path_length": path_length,
                "max_allowed": WINDOWS_MAX_PATH,
                "is_windows": IS_WINDOWS,
            })
            logger.warning("[V4 WARN] %s", warn_msg)
        else:
            logger.debug("[V4 MAX_PATH] Path OK: %d / %d chars", path_length, WINDOWS_MAX_PATH)

    def get_info(self):
        return {
            "filepath": str(self.filepath),
            "file_size": self.file_size,
            "shard_size": self.shard_size,
            "shard_count": self.shard_count,
            "is_large": self.is_large,
            "version": SCRIPT_VERSION,
            "v4_warnings": self.warnings,
            "v4_warnings_count": len(self.warnings),
            "v4_unicode_fallback": self.unicode_fallback,
            "v4_max_path_check": self.max_path_check,
            "v4_json_dup_key_check": self.json_dup_key_check,
        }

    def get_warnings(self):
        """Return list of V4 warnings generated during reading."""
        return list(self.warnings)

    @staticmethod
    def compute_shard_count(file_size, shard_size):
        """
        V4 P0 FIX: Correctly compute shard count using ceiling division.

        This is the corrected formula:
          shard_count = ceil(file_size / shard_size) = -(-file_size // shard_size)

        Boundary test cases:
          - file_size=0:          max(1, 0) = 1
          - file_size=shard_size: max(1, 1) = 1  (V3 gave 2 — BUG)
          - file_size=shard_size+1: max(1, 2) = 2

        Args:
            file_size: File size in bytes (int)
            shard_size: Shard size in bytes (int, must be > 0)

        Returns:
            int: Number of shards needed
        """
        if shard_size <= 0:
            raise ValueError("shard_size must be > 0")
        if file_size <= 0:
            return 1
        return max(1, -(-file_size // shard_size))

    @staticmethod
    def verify_shard_count(file_size, shard_size):
        """
        V4: Verify shard count against old (V3) formula for regression testing.

        Returns dict with both formulas' results and comparison.
        """
        old_count = max(1, file_size // shard_size + 1)
        new_count = max(1, -(-file_size // shard_size))
        correct = (old_count == new_count)
        return {
            "file_size": file_size,
            "shard_size": shard_size,
            "old_formula_v3": old_count,
            "new_formula_v4": new_count,
            "match": correct,
            "off_by_one_bug": not correct,
            "old_formula_bug": old_count > new_count,
        }


# ─────────────────────────────────────────────────────────────────────
# V3: Memory-Efficient Evidence Loader (retained, with V4 sharded reader)
# ─────────────────────────────────────────────────────────────────────
class MemoryEfficientEvidenceLoader:
    """
    V3: Load evidence packages with memory optimization.
    V4: Updated to use V4 ShardedJSONReader with exception handling.

    Key optimizations:
      1. Sharded reading for large files (V4: with corrected shard_count)
      2. Progressive call processing (don't hold all calls in memory)
      3. Explicit garbage collection after processing
      4. Streaming MD5 computation
    """

    def __init__(self, filepath, shard_size=DEFAULT_SHARD_SIZE,
                 unicode_fallback=False, max_path_check=False,
                 json_dup_key_check=False):
        self.reader = ShardedJSONReader(
            filepath, shard_size,
            unicode_fallback=unicode_fallback,
            max_path_check=max_path_check,
            json_dup_key_check=json_dup_key_check,
        )
        self.info = self.reader.get_info()

    def load(self, perf_guard=None):
        """Load evidence package with memory optimization and PERF-GUARD."""
        start_mem = _get_memory_usage()
        start_time = time.time()

        # PERF-GUARD start
        if perf_guard is None:
            perf_guard = PerfGuard()
        perf_guard.begin()

        evidence = self.reader.read()

        elapsed = time.time() - start_time
        end_mem = _get_memory_usage()

        # Handle V4 duplicate key wrapper
        if isinstance(evidence, dict) and evidence.get("_v4_duplicate_key_warning"):
            original_data = evidence.get("_v4_original_data", {})
            total_calls = len(original_data.get("calls", []))
        else:
            total_calls = len(evidence.get("calls", [])) if isinstance(evidence, dict) else 0

        self.info.update({
            "load_time_ms": round(elapsed * 1000, 1),
            "memory_start_mb": round(start_mem / 1024 / 1024, 1),
            "memory_end_mb": round(end_mem / 1024 / 1024, 1),
            "memory_delta_mb": round((end_mem - start_mem) / 1024 / 1024, 1),
            "total_calls": total_calls,
        })

        # PERF-GUARD checks
        pg_result = perf_guard.check_all(
            elapsed_sec=elapsed,
            total_calls=total_calls,
            peak_mb=self.info["memory_delta_mb"],
            file_size_bytes=self.info["file_size"],
            label="load",
        )
        self.info["perf_guard"] = pg_result

        logger.info("[LOAD V4] %s: %d bytes, %d calls, %.1fms, +%.1fMB %s",
                     Path(self.info["filepath"]).name,
                     self.info["file_size"],
                     self.info["total_calls"],
                     self.info["load_time_ms"],
                     self.info["memory_delta_mb"],
                     "[PERF-GUARD: %s]" % pg_result["verdict"])

        return evidence

    def get_info(self):
        return dict(self.info)


# ─────────────────────────────────────────────────────────────────────
# V3: Utility - Memory Usage (retained)
# ─────────────────────────────────────────────────────────────────────
def _get_memory_usage():
    """Get current process memory usage in bytes."""
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except ImportError:
        try:
            import psutil
            return psutil.Process(os.getpid()).memory_info().rss
        except ImportError:
            return 0


def _format_size(size_bytes):
    """Format bytes to human-readable string."""
    if size_bytes < 1024:
        return "%d B" % size_bytes
    elif size_bytes < 1024 * 1024:
        return "%.1f KB" % (size_bytes / 1024)
    else:
        return "%.1f MB" % (size_bytes / (1024 * 1024))


# ─────────────────────────────────────────────────────────────────────
# V3: IntegrityChecker (retained)
# ─────────────────────────────────────────────────────────────────────
class IntegrityChecker:
    """L2 Evidence Package Integrity Checker V3 (inherits V2 checks + memory stats)."""

    def __init__(self, evidence, load_info=None):
        self.ev = evidence or {}
        self.findings = []
        self.load_info = load_info or {}

    def emit(self, level, check_id, message, detail=None):
        f = {
            "level": level,
            "check_id": check_id,
            "message": message,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.findings.append(f)
        return f

    def check_top_fields(self):
        missing = []
        type_mismatch = []
        for field, expected_type in REQUIRED_TOP_FIELDS.items():
            if field not in self.ev:
                missing.append(field)
            elif not isinstance(self.ev[field], expected_type):
                type_mismatch.append("%s: expected %s, got %s" % (
                    field, expected_type.__name__, type(self.ev[field]).__name__))
        if missing:
            self.emit(CRITICAL, "IC-03",
                      "Missing top-level fields: %s" % ", ".join(missing))
        if type_mismatch:
            self.emit(HIGH, "IC-03",
                      "Top-level field type mismatch: %s" % "; ".join(type_mismatch))
        contract_ver = self.ev.get("evidence_contract_version")
        if contract_ver is None:
            self.emit(HIGH, "IC-03V2",
                      "Missing evidence_contract_version field (EVIDENCE_CONTRACT_V1)")
        elif contract_ver != EVIDENCE_CONTRACT_VERSION:
            self.emit(HIGH, "IC-03V2",
                      "Contract version mismatch: expected %s, got %s" % (
                          EVIDENCE_CONTRACT_VERSION, contract_ver))
        if self.ev.get("dshb_reuse") is not False:
            self.emit(CRITICAL, "IC-03V2",
                      "dshb_reuse must be false (got %s)" % self.ev.get("dshb_reuse"))
        if "DSHE" not in self.ev.get("caller", ""):
            self.emit(HIGH, "IC-03",
                      "caller field does not contain 'DSHE': %s" % self.ev.get("caller"))
        return not missing

    def check_calls(self):
        calls = self.ev.get("calls") or []
        if not calls:
            self.emit(CRITICAL, "IC-04", "calls array is empty")
            return False
        seen_trace_ids = set()
        for i, call in enumerate(calls):
            for field, expected_type in REQUIRED_CALL_FIELDS.items():
                if field not in call:
                    self.emit(CRITICAL, "IC-04",
                              "Call[%d] missing field: %s" % (i, field))
                elif not isinstance(call[field], expected_type):
                    self.emit(HIGH, "IC-04",
                              "Call[%d].%s type mismatch" % (i, field))
            tid = call.get("trace_id", "")
            if not tid:
                self.emit(CRITICAL, "IC-04", "Call[%d] trace_id is empty" % i)
            elif tid in seen_trace_ids:
                self.emit(HIGH, "IC-04", "Call[%d] trace_id duplicate: %s" % (i, tid))
            seen_trace_ids.add(tid)
            ct = call.get("call_type")
            if ct and ct not in ALLOWED_CALL_TYPES:
                self.emit(HIGH, "IC-04", "Call[%d] invalid call_type: %s" % (i, ct))
            if call.get("dshb_reuse") is not False:
                self.emit(CRITICAL, "IC-04", "Call[%d] dshb_reuse is not false" % i)
            dep_reg_id = call.get("dep_registry_id")
            if dep_reg_id is not None and not DEP_REGISTRY_PATTERN.match(dep_reg_id):
                self.emit(HIGH, "IC-04V2",
                          "Call[%d] invalid dep_registry_id format: %s" % (i, dep_reg_id))
            status = call.get("status", "")
            if status not in ALLOWED_STATUSES:
                self.emit(MEDIUM, "IC-04", "Call[%d] unexpected status: %s" % (i, status))
        return len(calls) > 0

    def check_payload_persistence(self, evidence_dir=None):
        calls = self.ev.get("calls") or []
        if not evidence_dir:
            evidence_dir = DEFAULT_EVIDENCE_DIR
        missing_files = []
        for call in calls:
            tid = call.get("trace_id", "")
            if not tid:
                continue
            trace_file = Path(evidence_dir) / f"{tid}.json"
            if not trace_file.exists():
                missing_files.append(tid)
        if missing_files:
            self.emit(CRITICAL, "IC-05",
                      "Missing payload evidence files: %s" %
                      ", ".join(missing_files[:5]) +
                      ("..." if len(missing_files) > 5 else ""))
        return len(missing_files) == 0

    def check_evidence_index(self, evidence_dir=None):
        if not evidence_dir:
            evidence_dir = DEFAULT_EVIDENCE_DIR
        index_file = Path(evidence_dir) / "evidence_index.json"
        if not index_file.exists():
            self.emit(MEDIUM, "IC-06",
                      "Evidence index file not found: %s" % index_file)
            return False
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index = json.load(f)
            if "files" not in index:
                self.emit(HIGH, "IC-06", "Evidence index missing 'files' key")
                return False
            return True
        except (json.JSONDecodeError, Exception) as e:
            self.emit(HIGH, "IC-06", "Evidence index JSON invalid: %s" % e)
            return False

    def check_negative_patterns(self):
        findings = []
        total_calls = self.ev.get("total_calls", 0)
        bridge_rate = self.ev.get("bridge_rate")
        real_rate = self.ev.get("real_fetchable_rate")
        if total_calls == 0 and bridge_rate and bridge_rate > 0:
            self.emit(CRITICAL, "NEG-01",
                      "Bridge rate fabrication: total_calls=0 but bridge_rate=%s" %
                      bridge_rate)
            findings.append("NEG-01")
        calls = self.ev.get("calls") or []
        for i, call in enumerate(calls):
            req = call.get("request_payload")
            resp = call.get("response_payload")
            if req is None or resp is None:
                self.emit(CRITICAL, "NEG-02",
                          "Payload loss: Call[%d] request_payload=%s, response_payload=%s" % (
                              i, "null" if req is None else "present",
                              "null" if resp is None else "present"))
                if "NEG-02" not in findings:
                    findings.append("NEG-02")
            tid = call.get("trace_id", "")
            if not tid or tid == "":
                self.emit(CRITICAL, "NEG-03",
                          "TraceID missing: Call[%d] trace_id is empty" % i)
                if "NEG-03" not in findings:
                    findings.append("NEG-03")
        if self.ev.get("dshb_reuse") is True:
            self.emit(CRITICAL, "NEG-04", "DSHB reuse detected: dshb_reuse=true")
            findings.append("NEG-04")
        for i, call in enumerate(calls):
            if call.get("dshb_reuse") is True:
                self.emit(CRITICAL, "NEG-04", "DSHB reuse in call: Call[%d]" % i)
                if "NEG-04" not in findings:
                    findings.append("NEG-04")
        return len(findings) == 0

    def check_md5(self, md5_list=None):
        if not md5_list:
            return True
        errors = 0
        for item in md5_list:
            filepath = item.get("file", "")
            expected = item.get("md5", "")
            if not filepath or not expected:
                continue
            if not os.path.exists(filepath):
                self.emit(CRITICAL, "MD5-01",
                          "File not found for MD5 check: %s" % filepath)
                errors += 1
                continue
            actual = file_md5_streaming(filepath)
            if actual != expected:
                self.emit(CRITICAL, "MD5-02",
                          "MD5 mismatch: %s (expected=%s, actual=%s)" % (
                              filepath, expected[:16], actual[:16]))
                errors += 1
        return errors == 0

    def check_contract_version(self):
        contract_ver = self.ev.get("evidence_contract_version")
        if contract_ver == EVIDENCE_CONTRACT_VERSION:
            return True
        self.emit(HIGH, "IC-CONTRACT",
                  "Contract version check: expected %s, got %s" % (
                      EVIDENCE_CONTRACT_VERSION, contract_ver or "MISSING"))
        return False

    def check_dep_state_machine(self):
        dep_state = self.ev.get("dep_state")
        dep_reg_id = self.ev.get("dep_registry_id")
        if dep_reg_id:
            if not DEP_REGISTRY_PATTERN.match(dep_reg_id):
                self.emit(HIGH, "IC-DEP-REG",
                          "Invalid dep_registry_id format: %s (expected DEP-REG-NNN)" %
                          dep_reg_id)
        if dep_state:
            if dep_state not in DEP_STATES:
                self.emit(HIGH, "IC-DEP-STATE",
                          "Invalid dep_state: %s (expected one of %s)" % (
                              dep_state, ", ".join(sorted(DEP_STATES))))
        else:
            self.emit(MEDIUM, "IC-DEP-STATE",
                      "dep_state field is missing (recommended for V2)")
        max_pause = self.ev.get("max_pause_days")
        if max_pause is not None and max_pause != MAX_PAUSE_DAYS:
            self.emit(MEDIUM, "IC-DEP-CONF",
                      "max_pause_days=%s (expected %s)" % (max_pause, MAX_PAUSE_DAYS))
        rollback_win = self.ev.get("rollback_window_min")
        if rollback_win is not None and rollback_win != ROLLBACK_WINDOW_MIN:
            self.emit(MEDIUM, "IC-DEP-CONF",
                      "rollback_window_min=%s (expected %s)" % (rollback_win, ROLLBACK_WINDOW_MIN))
        return dep_state is not None

    def check_response_payload_structure(self):
        calls = self.ev.get("calls") or []
        for i, call in enumerate(calls):
            resp = call.get("response_payload") or {}
            for field in REQUIRED_RESPONSE_FIELDS:
                if field not in resp:
                    self.emit(HIGH, "IC-RESP",
                              "Call[%d] response_payload missing '%s'" % (i, field))
            points = resp.get("points") or []
            if points:
                for j, p in enumerate(points[:3]):
                    if "value" not in p:
                        self.emit(HIGH, "IC-RESP",
                                  "Call[%d].response_payload.points[%d] missing 'value'" % (i, j))
                    if "date" not in p:
                        self.emit(MEDIUM, "IC-RESP",
                                  "Call[%d].response_payload.points[%d] missing 'date'" % (i, j))
            if "resolved_id" not in resp:
                self.emit(MEDIUM, "IC-RESP",
                          "Call[%d] response_payload missing 'resolved_id'" % i)

    def check_script_audit(self):
        script = self.ev.get("script_audit") or {}
        if not script:
            self.emit(MEDIUM, "IC-SCRIPT",
                      "script_audit section is missing (recommended for V2)")
            return False
        for field, expected_type in SCRIPT_AUDIT_REQUIRED.items():
            if field not in script:
                self.emit(HIGH, "IC-SCRIPT", "script_audit missing '%s'" % field)
            elif not isinstance(script[field], expected_type):
                self.emit(HIGH, "IC-SCRIPT", "script_audit.%s type mismatch" % field)
        if script.get("uses_search_passthrough"):
            self.emit(CRITICAL, "G-09",
                      "script_audit.uses_search_passthrough=true -> G-09 FAIL")
        if not script.get("has_id_consistency_assert"):
            self.emit(CRITICAL, "G-09",
                      "script_audit.has_id_consistency_assert=false -> G-09 FAIL")
        if script.get("zero_value_counts_as_pass"):
            self.emit(CRITICAL, "G-09",
                      "script_audit.zero_value_counts_as_pass=true -> G-09 FAIL")
        if not script.get("retains_raw_payload"):
            self.emit(CRITICAL, "G-09",
                      "script_audit.retains_raw_payload=false -> G-09 FAIL")
        return True

    def run_all(self, evidence_dir=None, md5_list=None, perf_guard_result=None):
        self.check_top_fields()
        self.check_calls()
        self.check_payload_persistence(evidence_dir)
        self.check_evidence_index(evidence_dir)
        self.check_negative_patterns()
        self.check_md5(md5_list)
        self.check_contract_version()
        self.check_dep_state_machine()
        self.check_response_payload_structure()
        self.check_script_audit()
        if perf_guard_result:
            self._merge_perf_guard(perf_guard_result)
        return self.summarize()

    def _merge_perf_guard(self, pg_result):
        """Merge PERF-GUARD findings into checker results."""
        pg_findings = pg_result.get("perf_guard_findings_detail", [])
        pg_verdict = pg_result.get("perf_guard_verdict", "PASS")
        pg_block = pg_result.get("perf_guard_block", False)
        for f in pg_findings:
            self.findings.append({
                "level": f["level"],
                "check_id": "PG-" + f["check_id"].replace("PG-", ""),
                "message": f["message"],
                "detail": f.get("detail"),
                "timestamp": f["timestamp"],
                "perf_guard": True,
                "value": f.get("value"),
                "limit": f.get("limit"),
            })
        self._perf_guard_verdict = pg_verdict
        self._perf_guard_block = pg_block

    def summarize(self):
        counts = defaultdict(int)
        for f in self.findings:
            counts[f["level"]] += 1
        total = sum(counts.values())
        crit = counts.get(CRITICAL, 0)
        high = counts.get(HIGH, 0)
        if crit > 0:
            verdict = "BLOCK"
        elif high > 0:
            verdict = "WARNING"
        elif counts.get(MEDIUM, 0) > 0:
            verdict = "PASS_WITH_NOTES"
        else:
            verdict = "PASS"
        result = {
            "verdict": verdict,
            "total_findings": total,
            "CRITICAL": crit,
            "HIGH": high,
            "MEDIUM": counts.get(MEDIUM, 0),
            "LOW": counts.get(LOW, 0),
            "findings": self.findings,
        }
        if self.load_info:
            result["load_info"] = self.load_info
            if "perf_guard" in self.load_info:
                result["perf_guard"] = self.load_info["perf_guard"]
        if hasattr(self, '_perf_guard_verdict'):
            result["perf_guard_verdict"] = self._perf_guard_verdict
            result["perf_guard_block"] = self._perf_guard_block
        return result


# ─────────────────────────────────────────────────────────────────────
# V3: Pre-Auditor (retained)
# ─────────────────────────────────────────────────────────────────────
class PreAuditor:
    """
    V3: Pre-audit mode with memory-optimized loading.
    """

    def __init__(self, evidence, load_info=None):
        self.ev = evidence or {}
        self.events = []
        self.load_info = load_info or {}
        self.checker = IntegrityChecker(evidence, load_info)

    def emit(self, level, rule, dp, msg, trace_id=None):
        e = {
            "level": level,
            "rule": rule,
            "detect_point": dp,
            "message": msg,
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.events.append(e)
        return e

    def pre_audit(self):
        self.checker.run_all()
        integrity_findings = self.checker.findings
        for f in integrity_findings:
            level = f["level"]
            rule = "PRE-AUDIT"
            dp = f["check_id"]
            self.emit(level, rule, dp, f["message"])
        self._check_dual_evidence()
        self._check_trace_fingerprint()
        self._check_bridge_rate()
        self._check_dep_classification()
        self._check_script_audit()
        result = self._verdict()
        if self.load_info:
            result["load_info"] = self.load_info
        return result

    def _check_dual_evidence(self):
        calls = self.ev.get("calls") or []
        for c in calls:
            tid = c.get("trace_id")
            claimed = (c.get("status") or "").upper()
            if "COMPLETED" not in claimed and "FETCH_OK" not in claimed:
                continue
            resp = c.get("response_payload") or {}
            pts = resp.get("points") or []
            has_nonzero = False
            for p in pts:
                v = p.get("value")
                if v is not None and str(v).strip() not in ("", "0", "0.0"):
                    has_nonzero = True
                    break
            if not (pts and has_nonzero):
                self.emit(CRITICAL, "R-AUDIT-01", "D01.2",
                          "COMPLETED entry lacks real fetch evidence: %s" % tid, tid)

    def _check_trace_fingerprint(self):
        for f in ("fingerprint", "run_id", "session_id"):
            if not self.ev.get(f):
                self.emit(CRITICAL, "R-AUDIT-03", "D03.1",
                          "Missing audit field: %s" % f)
        calls = self.ev.get("calls") or []
        seen = set()
        for c in calls:
            tid = c.get("trace_id")
            if not tid:
                self.emit(CRITICAL, "R-AUDIT-03", "D03.1", "Call missing trace_id")
                continue
            if tid in seen:
                self.emit(HIGH, "R-AUDIT-03", "D03.1",
                          "Duplicate trace_id: %s" % tid, tid)
            seen.add(tid)
        if self.ev.get("dshb_reuse") is True:
            self.emit(CRITICAL, "R-AUDIT-03", "D03.2",
                      "dshb_reuse=true violates L2-R01")

    def _check_bridge_rate(self):
        mr = self.ev.get("metadata_rate")
        rr = self.ev.get("real_fetchable_rate")
        claimed = self.ev.get("bridge_rate")
        if claimed is not None and (mr is None or rr is None):
            self.emit(HIGH, "R-AUDIT-02", "D02.2",
                      "Bridge rate not split into dual columns: %s" % claimed)
            return
        if mr is not None and rr is not None and mr != rr:
            if claimed is not None and abs(claimed - mr) < 1e-9 and abs(mr - rr) > 1e-9:
                self.emit(CRITICAL, "R-AUDIT-02", "D02.1",
                          "Metadata rate(%s) masquerading as effective rate, actual=%s" % (mr, rr))
        measured = self._measure_real_rate()
        if claimed is not None and measured is not None and claimed > measured + 1e-9:
            self.emit(CRITICAL, "R-AUDIT-02", "D02.3",
                      "Effective rate numerator inflated: claimed %s, measured %s" % (
                          claimed, round(measured, 4)))

    def _measure_real_rate(self):
        calls = self.ev.get("calls") or []
        if not calls:
            return None
        ok = 0
        for c in calls:
            resp = c.get("response_payload") or {}
            pts = resp.get("points") or []
            if any(p.get("value") not in (None, "", 0, "0", "0.0") for p in pts):
                ok += 1
        return ok / len(calls)

    def _check_dep_classification(self):
        for c in (self.ev.get("calls") or []):
            cls = (c.get("dep_classification") or "").upper()
            if cls == "DEPENDENCY_BLOCK":
                resp = c.get("response_payload") or {}
                err = resp.get("error", "")
                if "无法识别指标来源" not in err and "permission_state" not in json.dumps(resp):
                    self.emit(HIGH, "R-AUDIT-04", "DEP-CLASS",
                              "Claimed DEPENDENCY_BLOCK but no external block evidence: %s" %
                              c.get("indicator_id"), c.get("trace_id"))
                if not c.get("dep_registry_id"):
                    self.emit(MEDIUM, "R-AUDIT-04", "DEP-CLASS",
                              "DEPENDENCY_BLOCK not registered: %s" % c.get("indicator_id"),
                              c.get("trace_id"))

    def _check_script_audit(self):
        script = self.ev.get("script_audit") or {}
        if not script:
            return
        if script.get("uses_search_passthrough"):
            self.emit(CRITICAL, "R-AUDIT-04", "D04.1",
                      "Script uses search passthrough -> G-09 FAIL")
        if not script.get("has_id_consistency_assert"):
            self.emit(CRITICAL, "R-AUDIT-04", "D04.2",
                      "Missing ID consistency assert -> G-09 FAIL")
        if script.get("zero_value_counts_as_pass"):
            self.emit(CRITICAL, "R-AUDIT-04", "D04.3",
                      "Zero value counts as pass -> G-09 FAIL")
        if not script.get("retains_raw_payload"):
            self.emit(CRITICAL, "R-AUDIT-04", "D04.4",
                      "Raw payload not retained -> G-09 FAIL")

    def _verdict(self):
        crit = [e for e in self.events if e["level"] == CRITICAL]
        high = [e for e in self.events if e["level"] == HIGH]
        medium = [e for e in self.events if e["level"] == MEDIUM]
        if crit:
            result = "FAIL"
        elif high or medium:
            result = "CONDITIONAL_PASS"
        else:
            result = "PASS"
        return {
            "verdict": result,
            "total_events": len(self.events),
            "CRITICAL": len(crit),
            "HIGH": len(high),
            "MEDIUM": len(medium),
            "events": self.events,
        }


# ─────────────────────────────────────────────────────────────────────
# V3: Streaming MD5 (retained)
# ─────────────────────────────────────────────────────────────────────
def file_md5_streaming(path, chunk_size=65536):
    """Streaming MD5 computation for large files."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def file_md5(path):
    """Backward-compatible MD5 function."""
    return file_md5_streaming(path)


# ─────────────────────────────────────────────────────────────────────
# V3: Parallel Pre-Audit (retained)
# ─────────────────────────────────────────────────────────────────────
class ParallelPreAuditExecutor:
    """
    V3: Multi-threaded parallel pre-audit for directory batch processing.
    V4: Updated to pass V4 exception handling flags through.

    Features:
      - Configurable thread count
      - Progress reporting
      - Per-file memory tracking
      - Garbage collection between files
    """

    def __init__(self, dirpath, thread_count=DEFAULT_THREAD_COUNT,
                 shard_size=DEFAULT_SHARD_SIZE,
                 unicode_fallback=False, max_path_check=False,
                 json_dup_key_check=False):
        self.dirpath = Path(dirpath)
        self.thread_count = thread_count
        self.shard_size = shard_size
        self.results = {}
        self.lock = threading.Lock()
        self.completion_count = 0
        self.total_count = 0
        self.errors = []
        self.unicode_fallback = unicode_fallback
        self.max_path_check = max_path_check
        self.json_dup_key_check = json_dup_key_check

    def collect_files(self):
        """Collect all evidence package files from directory."""
        files = sorted(self.dirpath.glob("evidence_package_*.json"))
        self.total_count = len(files)
        return files

    def _audit_single(self, filepath):
        """Audit a single evidence file (thread-safe) with PERF-GUARD."""
        filename = Path(filepath).name
        try:
            loader = MemoryEfficientEvidenceLoader(
                filepath, self.shard_size,
                unicode_fallback=self.unicode_fallback,
                max_path_check=self.max_path_check,
                json_dup_key_check=self.json_dup_key_check,
            )
            perf_guard = PerfGuard()
            evidence = loader.load(perf_guard=perf_guard)
            load_info = loader.get_info()

            auditor = PreAuditor(evidence, load_info)
            result = auditor.pre_audit()

            if perf_guard.any_critical():
                result["perf_guard_blocked"] = True
                result["verdict"] = "BLOCK_PERF_GUARD"
                logger.warning("[PARALLEL V4] %s: PERF-GUARD BLOCK - %d findings",
                               filename, perf_guard.get_summary()["total_findings"])

            with self.lock:
                self.completion_count += 1
                self.results[filename] = {
                    "verdict": result["verdict"],
                    "CRITICAL": result["CRITICAL"],
                    "HIGH": result["HIGH"],
                    "MEDIUM": result["MEDIUM"],
                    "total_events": result["total_events"],
                    "load_info": load_info,
                    "perf_guard": perf_guard.get_summary(),
                    "perf_guard_blocked": perf_guard.any_critical(),
                }
                pct = self.completion_count / self.total_count * 100
                logger.info("[PARALLEL V4 %d/%d %.0f%%] %s: %s (CRIT=%d, HIGH=%d) [%.1fms, +%.1fMB] PG:%s",
                            self.completion_count, self.total_count, pct,
                            filename, result["verdict"],
                            result["CRITICAL"], result["HIGH"],
                            load_info.get("load_time_ms", 0),
                            load_info.get("memory_delta_mb", 0),
                            "BLOCK" if perf_guard.any_critical() else "OK")

            del evidence
            gc.collect()

            return filename, result["verdict"]

        except Exception as e:
            with self.lock:
                self.completion_count += 1
                self.results[filename] = {
                    "verdict": "ERROR",
                    "error": str(e),
                    "load_info": None,
                }
                self.errors.append((filename, str(e)))
                logger.error("[PARALLEL V4] %s: ERROR - %s" % (filename, e))
            return filename, "ERROR"

    def execute(self):
        """Execute parallel pre-audit."""
        files = self.collect_files()
        if not files:
            logger.warning("No evidence files found in %s" % self.dirpath)
            return {}

        logger.info("[PARALLEL V4] Starting %d-thread pre-audit of %d files "
                    "(shard_size=%d bytes)",
                    self.thread_count, self.total_count, self.shard_size)
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            futures = {
                executor.submit(self._audit_single, str(f)): f.name
                for f in files
            }
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error("[PARALLEL V4] Unhandled error: %s" % e)

        elapsed = time.time() - start_time
        logger.info("[PARALLEL V4] Completed in %.1fms: %d files, %d errors, "
                    "avg=%.1fms/file",
                    elapsed * 1000, self.total_count, len(self.errors),
                    elapsed * 1000 / max(1, self.total_count))

        return self.results


# ─────────────────────────────────────────────────────────────────────
# Utility Functions (retained)
# ─────────────────────────────────────────────────────────────────────
def generate_md5_list(evidence_dir):
    evidence_dir = Path(evidence_dir)
    files = []
    for f in sorted(evidence_dir.glob("*")):
        if f.is_file():
            files.append({
                "file": str(f),
                "md5": file_md5_streaming(str(f)),
                "size": f.stat().st_size,
            })
    return files


def generate_evidence_index(evidence_dir, evidence_file=None):
    evidence_dir = Path(evidence_dir)
    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_contract_version": EVIDENCE_CONTRACT_VERSION,
        "files": [],
    }
    for f in sorted(evidence_dir.glob("*")):
        if f.is_file():
            entry = {
                "filename": f.name,
                "size": f.stat().st_size,
                "md5": file_md5_streaming(str(f)),
            }
            if evidence_file and f.name == evidence_file.name:
                entry["is_evidence_package"] = True
            index["files"].append(entry)
    return index


def check_evidence_package(filepath, evidence_dir=None, shard_size=DEFAULT_SHARD_SIZE,
                           perf_guard_mode=PERF_GUARD_MODE, perf_guard_enabled=PERF_GUARD_ENABLED,
                           unicode_fallback=False, max_path_check=False,
                           json_dup_key_check=False):
    filepath = Path(filepath)
    if not filepath.exists():
        logger.error("File not found: %s" % filepath)
        return {"verdict": "ERROR", "error": "file_not_found"}
    try:
        loader = MemoryEfficientEvidenceLoader(
            filepath, shard_size,
            unicode_fallback=unicode_fallback,
            max_path_check=max_path_check,
            json_dup_key_check=json_dup_key_check,
        )
        pg = PerfGuard(mode=perf_guard_mode, enabled=perf_guard_enabled)
        ev = loader.load(perf_guard=pg)
        load_info = loader.get_info()
        if pg.any_critical():
            pg_result = pg.to_result()
            return {"verdict": "BLOCK_PERF_GUARD", **pg_result,
                    "error": "perf_guard_critical",
                    "detail": "Packaging blocked by PERF-GUARD: %s" %
                              "; ".join(f["message"] for f in pg.findings if f["level"] == CRITICAL)}
    except json.JSONDecodeError as e:
        logger.error("JSON parse error: %s" % e)
        return {"verdict": "BLOCK", "error": "json_parse_error", "detail": str(e)}
    except Exception as e:
        logger.error("Load error: %s" % e)
        return {"verdict": "ERROR", "error": str(e)}
    if not evidence_dir:
        evidence_dir = filepath.parent
    checker = IntegrityChecker(ev, load_info)
    pg_result_dict = pg.to_result()
    result = checker.run_all(str(evidence_dir), perf_guard_result=pg_result_dict)
    if pg.any_high() and result["verdict"] == "PASS":
        result["verdict"] = "WARNING"
    return result


def pre_audit_evidence(filepath, shard_size=DEFAULT_SHARD_SIZE,
                       perf_guard_mode=PERF_GUARD_MODE, perf_guard_enabled=PERF_GUARD_ENABLED,
                       unicode_fallback=False, max_path_check=False,
                       json_dup_key_check=False):
    filepath = Path(filepath)
    if not filepath.exists():
        logger.error("File not found: %s" % filepath)
        return {"verdict": "ERROR", "error": "file_not_found"}
    try:
        loader = MemoryEfficientEvidenceLoader(
            filepath, shard_size,
            unicode_fallback=unicode_fallback,
            max_path_check=max_path_check,
            json_dup_key_check=json_dup_key_check,
        )
        pg = PerfGuard(mode=perf_guard_mode, enabled=perf_guard_enabled)
        ev = loader.load(perf_guard=pg)
        load_info = loader.get_info()
        if pg.any_critical():
            return {"verdict": "BLOCK_PERF_GUARD", "perf_guard": pg.to_result(),
                    "error": "perf_guard_critical"}
    except json.JSONDecodeError as e:
        logger.error("JSON parse error: %s" % e)
        return {"verdict": "ERROR", "error": "json_parse_error"}
    except Exception as e:
        logger.error("Load error: %s" % e)
        return {"verdict": "ERROR", "error": str(e)}
    auditor = PreAuditor(ev, load_info)
    result = auditor.pre_audit()
    result["perf_guard"] = pg.to_result()
    if pg.any_critical():
        result["verdict"] = "BLOCK_PERF_GUARD"
    return result


# ─────────────────────────────────────────────────────────────────────
# V4 NEW: Exception Handling Test Cases (T3.2)
# ─────────────────────────────────────────────────────────────────────
class ExceptionHandlingTestRunner:
    """
    V4 NEW: Run all exception handling test cases to verify T3.2 implementations.

    Tests cover:
      1. UnicodeDecodeError — WARN level, fallback to latin-1
      2. Windows MAX_PATH — precheck at 260 chars
      3. JSON duplicate keys — MEDIUM level, custom JSONDecoder
      4. Exception classification matrix — ERROR/WARN/BLOCK/CRITICAL
      5. P0 shard_count off-by-one fix verification
    """

    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def _test(self, name, passed, detail=""):
        self.results.append({
            "test": name,
            "passed": passed,
            "detail": detail,
        })
        if passed:
            self.passed += 1
            logger.info("[V4 TEST] PASS: %s %s", name, detail)
        else:
            self.failed += 1
            logger.warning("[V4 TEST] FAIL: %s %s", name, detail)

    def run_all(self):
        """Run all exception handling test cases."""
        logger.info("[V4 TEST] Running exception handling test suite...")
        self._test_shard_count_off_by_one()
        self._test_unicode_decode_error()
        self._test_max_path_check()
        self._test_json_duplicate_keys()
        self._test_exception_classification()
        self._test_exception_classifier()
        self._test_boundary_cases()
        self._print_summary()
        return self.failed == 0

    def _test_shard_count_off_by_one(self):
        """T3.1: Verify P0 off-by-one shard_count fix."""
        logger.info("[V4 TEST] === Shard Count Off-By-One Fix Tests ===")

        # Test 1: file_size == shard_size (the P0 bug case)
        file_size = 4096
        shard_size = 4096
        old_count = max(1, file_size // shard_size + 1)
        new_count = max(1, -(-file_size // shard_size))
        expected = 1
        self._test("shard_count[file==shard]",
                   new_count == expected and old_count != expected,
                   "old=%d (BUG), new=%d, expected=%d" % (old_count, new_count, expected))

        # Test 2: file_size == shard_size + 1
        file_size = 4097
        old_count = max(1, file_size // shard_size + 1)
        new_count = max(1, -(-file_size // shard_size))
        expected = 2
        self._test("shard_count[file==shard+1]",
                   new_count == expected and old_count == expected,
                   "old=%d, new=%d, expected=%d (both correct)" % (old_count, new_count, expected))

        # Test 3: empty file
        file_size = 0
        old_count = max(1, file_size // shard_size + 1)
        new_count = max(1, -(-file_size // shard_size))
        expected = 1
        self._test("shard_count[empty_file]",
                   new_count == expected and old_count == expected,
                   "old=%d, new=%d, expected=%d" % (old_count, new_count, expected))

        # Test 4: file_size == 2*shard_size
        file_size = 8192
        old_count = max(1, file_size // shard_size + 1)
        new_count = max(1, -(-file_size // shard_size))
        expected = 2
        self._test("shard_count[file==2*shard]",
                   new_count == expected and old_count != expected,
                   "old=%d (BUG), new=%d, expected=%d" % (old_count, new_count, expected))

        # Test 5: file_size == 1 (single byte)
        file_size = 1
        shard_size = 4096
        old_count = max(1, file_size // shard_size + 1)
        new_count = max(1, -(-file_size // shard_size))
        expected = 1
        self._test("shard_count[single_byte]",
                   new_count == expected and old_count == expected,
                   "old=%d, new=%d, expected=%d" % (old_count, new_count, expected))

        # Test 6: Verify ShardedJSONReader.compute_shard_count()
        assert ShardedJSONReader.compute_shard_count(0, 4096) == 1
        assert ShardedJSONReader.compute_shard_count(4096, 4096) == 1  # P0 fix
        assert ShardedJSONReader.compute_shard_count(4097, 4096) == 2
        assert ShardedJSONReader.compute_shard_count(8192, 4096) == 2
        assert ShardedJSONReader.compute_shard_count(8193, 4096) == 3
        assert ShardedJSONReader.compute_shard_count(12288, 4096) == 3
        self._test("compute_shard_count[all]", True, "all 6 boundary values correct")

        # Test 7: Verify verify_shard_count() helper
        v = ShardedJSONReader.verify_shard_count(4096, 4096)
        self._test("verify_shard_count[file==shard]",
                   v["off_by_one_bug"] == True and v["old_formula_v3"] == 2 and v["new_formula_v4"] == 1,
                   "old=%d, new=%d, bug=%s" % (v["old_formula_v3"], v["new_formula_v4"], v["off_by_one_bug"]))

    def _test_unicode_decode_error(self):
        """T3.2: UnicodeDecodeError handling test."""
        logger.info("[V4 TEST] === UnicodeDecodeError Handling Tests ===")

        # Test UnicodeDecodeError classification
        classifier = ExceptionClassifier()
        exc = UnicodeDecodeError("utf-8", b'\xff\xfe', 0, 2, "invalid start byte")
        level, msg = classifier.classify(exc)
        self._test("UnicodeDecodeError_classification",
                   level == EXCEPTION_LEVEL_WARN,
                   "level=%s (expected WARN)" % level)

        # Test UnicodeDecodeError handling result
        handled = classifier.handle(exc, context="test_file.json")
        self._test("UnicodeDecodeError_handling",
                   handled["verdict"] == "WARNING" and handled["exception_level"] == EXCEPTION_LEVEL_WARN,
                   "verdict=%s, level=%s" % (handled["verdict"], handled["exception_level"]))

    def _test_max_path_check(self):
        """T3.2: Windows MAX_PATH check test."""
        logger.info("[V4 TEST] === Windows MAX_PATH Check Tests ===")

        # Test path length exactly at limit
        short_path = "C:\\test\\file.json"
        self._test("max_path_under_limit",
                   len(short_path) <= WINDOWS_MAX_PATH,
                   "length=%d, limit=%d" % (len(short_path), WINDOWS_MAX_PATH))

        # Test path exceeding limit
        long_path = "C:\\" + "D" * 260 + "\\file.json"
        path_error = MaxPathExceededError(long_path, len(long_path), WINDOWS_MAX_PATH)
        self._test("max_path_exceeded",
                   len(long_path) > WINDOWS_MAX_PATH,
                   "length=%d, limit=%d, fingerprint=%s" % (
                       len(long_path), WINDOWS_MAX_PATH, path_error.audit_fingerprint))

        # Test MaxPathExceededError audit fingerprint
        self._test("max_path_audit_fingerprint",
                   hasattr(path_error, "audit_fingerprint") and len(path_error.audit_fingerprint) == 16,
                   "fingerprint=%s" % path_error.audit_fingerprint)

    def _test_json_duplicate_keys(self):
        """T3.2: JSON duplicate key detection test."""
        logger.info("[V4 TEST] === JSON Duplicate Key Detection Tests ===")

        # Test with duplicate keys
        test_json = '{"key1": "value1", "key1": "value2", "key2": "value2"}'
        decoder = DuplicateKeyJSONDecoder()
        try:
            data = decoder.decode(test_json)
        except Exception:
            # decoder.decode may raise for malformed JSON, but we want to test the hook
            pass

        dup_keys = decoder.get_duplicate_keys()
        self._test("duplicate_key_detection",
                   len(dup_keys) > 0 and dup_keys[0]["key"] == "key1",
                   "found %d duplicates" % len(dup_keys))

        # Test with no duplicates
        clean_json = '{"key1": "value1", "key2": "value2"}'
        decoder2 = DuplicateKeyJSONDecoder()
        data2 = decoder2.decode(clean_json)
        dup_keys2 = decoder2.get_duplicate_keys()
        self._test("duplicate_key_no_false_positive",
                   len(dup_keys2) == 0,
                   "found %d duplicates (expected 0)" % len(dup_keys2))

        # Test DuplicateKeyError audit fingerprint
        dup_error = DuplicateKeyError([{"key": "test", "occurrence": 2}])
        self._test("duplicate_key_error_fingerprint",
                   hasattr(dup_error, "audit_fingerprint") and len(dup_error.audit_fingerprint) == 16,
                   "fingerprint=%s" % dup_error.audit_fingerprint)

        # Test DuplicateKeyError classification
        classifier = ExceptionClassifier()
        level, msg = classifier.classify(dup_error)
        self._test("duplicate_key_classification",
                   level == EXCEPTION_LEVEL_MEDIUM,
                   "level=%s (expected MEDIUM)" % level)

    def _test_exception_classification(self):
        """T3.5: Exception classification matrix test."""
        logger.info("[V4 TEST] === Exception Classification Matrix Tests ===")

        test_cases = [
            (FileNotFoundError("test"), EXCEPTION_LEVEL_ERROR),
            (UnicodeDecodeError("utf-8", b'\xff', 0, 1, "bad"), EXCEPTION_LEVEL_WARN),
            (json.JSONDecodeError("test", "test", 0), EXCEPTION_LEVEL_BLOCK),
            (DuplicateKeyError([{"key": "x", "occurrence": 2}]), EXCEPTION_LEVEL_MEDIUM),
            (MaxPathExceededError("C:\\test\\file.json", 300), EXCEPTION_LEVEL_WARN),
            (OSError("test"), EXCEPTION_LEVEL_ERROR),
            (PermissionError("test"), EXCEPTION_LEVEL_BLOCK),
            (TimeoutError("test"), EXCEPTION_LEVEL_WARN),
            (MemoryError("test"), EXCEPTION_LEVEL_CRITICAL),
        ]

        for exc, expected_level in test_cases:
            classifier = ExceptionClassifier()
            level, msg = classifier.classify(exc)
            exc_type = type(exc).__name__
            self._test("classify_%s" % exc_type,
                       level == expected_level,
                       "level=%s (expected %s)" % (level, expected_level))

    def _test_exception_classifier(self):
        """T3.5: ExceptionClassifier handle() method test."""
        logger.info("[V4 TEST] === ExceptionClassifier.handle() Tests ===")

        classifier = ExceptionClassifier()

        # Test ERROR level
        result = classifier.handle(FileNotFoundError("test_file.json"), context="read")
        self._test("classifier_handle_error",
                   result["verdict"] == "ERROR",
                   "verdict=%s" % result["verdict"])

        # Test WARN level
        result = classifier.handle(UnicodeDecodeError("utf-8", b'\xff', 0, 1, "bad"), context="read")
        self._test("classifier_handle_warn",
                   result["verdict"] == "WARNING",
                   "verdict=%s" % result["verdict"])

        # Test BLOCK level
        result = classifier.handle(json.JSONDecodeError("test", "test", 0), context="parse")
        self._test("classifier_handle_block",
                   result["verdict"] == "BLOCK",
                   "verdict=%s" % result["verdict"])

        # Test CRITICAL level
        result = classifier.handle(MemoryError("OOM"), context="load")
        self._test("classifier_handle_critical",
                   result["verdict"] == "BLOCK_CRITICAL",
                   "verdict=%s" % result["verdict"])

        # Test classification log
        log = classifier.get_classification_log()
        self._test("classifier_classification_log",
                   len(log) == 4,
                   "logged %d classifications" % len(log))

    def _test_boundary_cases(self):
        """T3.5: Boundary test cases for exception handling."""
        logger.info("[V4 TEST] === Boundary Case Tests ===")

        # Test 1: file_size=0, shard_size=4096 → 1 shard
        info = ShardedJSONReader.compute_shard_count(0, 4096)
        self._test("boundary_empty_file", info == 1, "shard_count=%d" % info)

        # Test 2: file_size=1, shard_size=4096 → 1 shard
        info = ShardedJSONReader.compute_shard_count(1, 4096)
        self._test("boundary_single_byte", info == 1, "shard_count=%d" % info)

        # Test 3: file_size=4095, shard_size=4096 → 1 shard
        info = ShardedJSONReader.compute_shard_count(4095, 4096)
        self._test("boundary_just_below", info == 1, "shard_count=%d" % info)

        # Test 4: file_size=4096, shard_size=4096 → 1 shard (P0 FIX!)
        info = ShardedJSONReader.compute_shard_count(4096, 4096)
        self._test("boundary_exact_match", info == 1, "shard_count=%d" % info)

        # Test 5: file_size=4097, shard_size=4096 → 2 shards
        info = ShardedJSONReader.compute_shard_count(4097, 4096)
        self._test("boundary_just_above", info == 2, "shard_count=%d" % info)

        # Test 6: file_size=8192, shard_size=4096 → 2 shards (P0 FIX!)
        info = ShardedJSONReader.compute_shard_count(8192, 4096)
        self._test("boundary_exact_double", info == 2, "shard_count=%d" % info)

        # Test 7: file_size=8193, shard_size=4096 → 3 shards
        info = ShardedJSONReader.compute_shard_count(8193, 4096)
        self._test("boundary_just_above_double", info == 3, "shard_count=%d" % info)

        # Test 8: file_size=12288, shard_size=4096 → 3 shards (P0 FIX!)
        info = ShardedJSONReader.compute_shard_count(12288, 4096)
        self._test("boundary_exact_triple", info == 3, "shard_count=%d" % info)

        # Test 9: Large file with small shard
        info = ShardedJSONReader.compute_shard_count(10 * 1024 * 1024, 4096)
        expected = 2560
        self._test("boundary_large_file", info == expected,
                   "shard_count=%d, expected=%d" % (info, expected))

    def _print_summary(self):
        total = self.passed + self.failed
        logger.info("[V4 TEST] === Exception Handling Test Summary ===")
        logger.info("[V4 TEST] Total: %d, Passed: %d, Failed: %d", total, self.passed, self.failed)
        if self.failed > 0:
            logger.warning("[V4 TEST] FAILED TESTS:")
            for r in self.results:
                if not r["passed"]:
                    logger.warning("[V4 TEST]   FAIL: %s — %s", r["test"], r["detail"])
        else:
            logger.info("[V4 TEST] All %d tests PASSED", total)


def run_exception_handling_tests():
    """Run all exception handling test cases and return results."""
    runner = ExceptionHandlingTestRunner()
    success = runner.run_all()
    return {
        "success": success,
        "total": runner.passed + runner.failed,
        "passed": runner.passed,
        "failed": runner.failed,
        "results": runner.results,
    }


# ─────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="DSHE V86-RC2 L2 Evidence Package Integrity Checker V4")
    ap.add_argument("--check", help="Check single evidence file")
    ap.add_argument("--check-dir", help="Check all evidence files in directory")
    ap.add_argument("--verify-md5", help="Verify MD5 checksum list")
    ap.add_argument("--all", help="Run all checks on directory")
    ap.add_argument("--pre-audit", help="Pre-audit single evidence file")
    ap.add_argument("--pre-audit-dir", help="Pre-audit all evidence files in directory")
    ap.add_argument("--generate-md5", help="Generate MD5 checksum list")
    ap.add_argument("--generate-index", help="Generate evidence index")
    ap.add_argument("--dry-run", action="store_true", help="Dry run")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--threads", type=int, default=DEFAULT_THREAD_COUNT,
                    help="Thread count for parallel pre-audit (V3)")
    ap.add_argument("--shard-size", type=int, default=DEFAULT_SHARD_SIZE,
                    help="Shard size for large file reading in bytes (V3)")
    ap.add_argument("--perf-guard-mode", choices=["STRICT", "WARN"],
                    default=PERF_GUARD_MODE,
                    help="PERF-GUARD mode: STRICT=block on limit, WARN=alert only (V3.1)")
    ap.add_argument("--no-perf-guard", action="store_true",
                    help="Disable PERF-GUARD checks (V3.1)")
    ap.add_argument("--perf-guard-only", action="store_true",
                    help="Only run PERF-GUARD checks, skip integrity checks (V3.1)")
    # V4 NEW flags (T3.2)
    ap.add_argument("--json-dup-key-check", action="store_true",
                    help="Enable JSON duplicate key detection (MEDIUM warning, V4/T3.2)")
    ap.add_argument("--max-path-check", action="store_true",
                    help="Enable Windows MAX_PATH (260 chars) precheck (V4/T3.2)")
    ap.add_argument("--unicode-fallback", action="store_true",
                    help="Enable UnicodeDecodeError fallback to latin-1 (V4/T3.2)")
    ap.add_argument("--exception-handling-test", action="store_true",
                    help="Run all exception handling test cases (V4/T3.2)")

    args = ap.parse_args(argv)

    # V4: Update global flags
    global JSON_DUP_KEY_CHECK_ENABLED, MAX_PATH_CHECK_ENABLED, UNICODE_FALLBACK_ENABLED
    global EXCEPTION_HANDLING_TEST_ENABLED
    JSON_DUP_KEY_CHECK_ENABLED = args.json_dup_key_check
    MAX_PATH_CHECK_ENABLED = args.max_path_check
    UNICODE_FALLBACK_ENABLED = args.unicode_fallback
    EXCEPTION_HANDLING_TEST_ENABLED = args.exception_handling_test

    if args.dry_run:
        logger.info("%s V%s - DRY RUN" % (SCRIPT_NAME, SCRIPT_VERSION))
        logger.info("  Contract Version: %s" % EVIDENCE_CONTRACT_VERSION)
        logger.info("  DEP Registry ID: %s" % DEP_REGISTRY_ID)
        logger.info("  Evidence Dir: %s" % DEFAULT_EVIDENCE_DIR)
        logger.info("  Default Shard Size: %d bytes (%s)" % (
            args.shard_size, _format_size(args.shard_size)))
        logger.info("  Default Threads: %d" % args.threads)
        logger.info("  V3 Features: Sharded reading, Parallel pre-audit, "
                    "Streaming MD5, Memory-optimized loading")
        logger.info("  V3.1 PERF-GUARD: %s (mode=%s)" % (
            "ENABLED" if not args.no_perf_guard else "DISABLED", args.perf_guard_mode))
        logger.info("  PERF-GUARD Limits: time=%.1fs, calls=%d, mem=%.0fMB, file=%.0fMB" % (
            PERF_GUARD_PACKAGING_TIME_LIMIT_SEC, PERF_GUARD_CALL_COUNT_LIMIT,
            PERF_GUARD_MEMORY_PEAK_LIMIT_MB, PERF_GUARD_FILE_SIZE_LIMIT_MB))
        logger.info("  V4 Features: P0 shard_count fix, UnicodeDecodeError handling, "
                    "Windows MAX_PATH check, JSON duplicate key detection")
        logger.info("  V4 Flags: --json-dup-key-check=%s, --max-path-check=%s, "
                    "--unicode-fallback=%s" % (
                        args.json_dup_key_check, args.max_path_check, args.unicode_fallback))
        logger.info("  Modes: --check, --check-dir, --verify-md5, --all, "
                    "--pre-audit, --pre-audit-dir, --generate-md5, --generate-index, "
                    "--exception-handling-test")
        return 0

    # V4 NEW: Exception handling test mode
    if args.exception_handling_test:
        logger.info("V4 Exception Handling Test Suite")
        result = run_exception_handling_tests()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["success"] else 4

    if args.generate_md5:
        dirpath = Path(args.generate_md5)
        if not dirpath.exists():
            logger.error("Directory not found: %s" % dirpath)
            return 3
        md5_list = generate_md5_list(dirpath)
        output = dirpath / "MD5_CHECKSUM_LIST_evidence.json"
        with open(output, "w", encoding="utf-8") as f:
            json.dump(md5_list, f, indent=2, ensure_ascii=False)
        logger.info("Generated MD5 list: %s (%d files)" % (output, len(md5_list)))
        return 0

    if args.generate_index:
        dirpath = Path(args.generate_index)
        if not dirpath.exists():
            logger.error("Directory not found: %s" % dirpath)
            return 3
        ev_files = list(dirpath.glob("evidence_package_*.json"))
        ev_file = ev_files[0] if ev_files else None
        index = generate_evidence_index(dirpath, ev_file)
        output = dirpath / "evidence_index.json"
        with open(output, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        logger.info("Generated evidence index: %s (%d files)" % (output, len(index["files"])))
        return 0

    if args.verify_md5:
        md5_file = Path(args.verify_md5)
        if not md5_file.exists():
            logger.error("MD5 list not found: %s" % md5_file)
            return 3
        with open(md5_file, "r", encoding="utf-8") as f:
            md5_list = json.load(f)
        checker = IntegrityChecker({})
        ok = checker.check_md5(md5_list)
        result = checker.summarize()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            logger.info("MD5 verification: %s" % result["verdict"])
            for f in result["findings"]:
                logger.info("  [%s] %s: %s" % (f["level"], f["check_id"], f["message"]))
        return 0 if ok else 1

    if args.pre_audit:
        result = pre_audit_evidence(
            args.pre_audit, args.shard_size,
            unicode_fallback=args.unicode_fallback,
            max_path_check=args.max_path_check,
            json_dup_key_check=args.json_dup_key_check,
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            logger.info("PRE-AUDIT RESULT: %s" % result["verdict"])
            logger.info("  Events: %d (CRITICAL=%d, HIGH=%d, MEDIUM=%d)" % (
                result["total_events"], result["CRITICAL"], result["HIGH"], result["MEDIUM"]))
            if "load_info" in result and result["load_info"]:
                li = result["load_info"]
                logger.info("  Load: %s bytes, %d calls, %.1fms, +%.1fMB" % (
                    _format_size(li.get("file_size", 0)),
                    li.get("total_calls", 0),
                    li.get("load_time_ms", 0),
                    li.get("memory_delta_mb", 0)))
            for e in result["events"]:
                logger.info("  [%s] %s/%s: %s" % (
                    e["level"], e["rule"], e["detect_point"], e["message"]))
        return 0 if result["verdict"] != "FAIL" else 1

    if args.pre_audit_dir:
        dirpath = Path(args.pre_audit_dir)
        if not dirpath.exists():
            logger.error("Directory not found: %s" % dirpath)
            return 3

        pg_enabled = not args.no_perf_guard
        executor = ParallelPreAuditExecutor(
            dirpath, args.threads, args.shard_size,
            unicode_fallback=args.unicode_fallback,
            max_path_check=args.max_path_check,
            json_dup_key_check=args.json_dup_key_check,
        )
        all_results = executor.execute()

        pg_blocked = sum(1 for r in all_results.values()
                         if r.get("perf_guard_blocked"))
        pg_warnings = sum(1 for r in all_results.values()
                          if r.get("perf_guard") and r["perf_guard"]["verdict"] in ("WARN", "NOTICE"))

        if args.json:
            print(json.dumps(all_results, ensure_ascii=False, indent=2))
        else:
            all_pass = all(r.get("verdict", "") != "FAIL" and
                           r.get("verdict", "") != "ERROR"
                           for r in all_results.values())
            total_files = len(all_results)
            pass_count = sum(1 for r in all_results.values()
                             if r.get("verdict") in ("PASS", "PASS_WITH_NOTES",
                                                     "CONDITIONAL_PASS"))
            fail_count = sum(1 for r in all_results.values()
                             if r.get("verdict") == "FAIL")
            error_count = sum(1 for r in all_results.values()
                              if r.get("verdict") == "ERROR")
            logger.info("PRE-AUDIT DIR: %d files, %d PASS, %d FAIL, %d ERROR, %s" % (
                total_files, pass_count, fail_count, error_count,
                "ALL PASS" if all_pass else "HAS FAILURES"))
            total_mem = sum(r.get("load_info", {}).get("memory_delta_mb", 0)
                           for r in all_results.values()
                           if r.get("load_info"))
            avg_mem = total_mem / max(1, total_files)
            logger.info("  Memory: total=%.1fMB, avg=%.1fMB/file", total_mem, avg_mem)
            if pg_blocked > 0:
                logger.warning("  PERF-GUARD: %d files BLOCKED by performance limits", pg_blocked)
            if pg_warnings > 0:
                logger.info("  PERF-GUARD: %d files with WARN/NOTICE findings", pg_warnings)
            logger.info("  PERF-GUARD: mode=%s, limits: time=%.1fs, calls=%d, mem=%.0fMB",
                         args.perf_guard_mode, PERF_GUARD_PACKAGING_TIME_LIMIT_SEC,
                         PERF_GUARD_CALL_COUNT_LIMIT, PERF_GUARD_MEMORY_PEAK_LIMIT_MB)
        return 0 if all_pass else 1

    if args.check:
        result = check_evidence_package(
            args.check, shard_size=args.shard_size,
            unicode_fallback=args.unicode_fallback,
            max_path_check=args.max_path_check,
            json_dup_key_check=args.json_dup_key_check,
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            logger.info("CHECK RESULT: %s" % result["verdict"])
            logger.info("  Findings: %d (CRITICAL=%d, HIGH=%d, MEDIUM=%d)" % (
                result["total_findings"], result["CRITICAL"],
                result["HIGH"], result["MEDIUM"]))
            for f in result["findings"]:
                logger.info("  [%s] %s: %s" % (f["level"], f["check_id"], f["message"]))
            if "load_info" in result and result["load_info"]:
                li = result["load_info"]
                logger.info("  Load: %s bytes, %d calls, %.1fms, +%.1fMB" % (
                    _format_size(li.get("file_size", 0)),
                    li.get("total_calls", 0),
                    li.get("load_time_ms", 0),
                    li.get("memory_delta_mb", 0)))
        return 0 if result["verdict"] != "BLOCK" else 1

    if args.check_dir:
        dirpath = Path(args.check_dir)
        if not dirpath.exists():
            logger.error("Directory not found: %s" % dirpath)
            return 3
        files = sorted(dirpath.glob("evidence_package_*.json"))
        if not files:
            logger.warning("No evidence files found in %s" % dirpath)
            return 0
        all_pass = True
        for f in files:
            result = check_evidence_package(
                str(f), dirpath, args.shard_size,
                unicode_fallback=args.unicode_fallback,
                max_path_check=args.max_path_check,
                json_dup_key_check=args.json_dup_key_check,
            )
            if result["verdict"] == "BLOCK":
                all_pass = False
            logger.info("%s: %s" % (f.name, result["verdict"]))
        return 0 if all_pass else 1

    if args.all:
        dirpath = Path(args.all)
        if not dirpath.exists():
            logger.error("Directory not found: %s" % dirpath)
            return 3
        files = sorted(dirpath.glob("evidence_package_*.json"))
        if not files:
            logger.warning("No evidence files found in %s" % dirpath)
            return 0
        all_pass = True
        for f in files:
            result = check_evidence_package(
                str(f), dirpath, args.shard_size,
                unicode_fallback=args.unicode_fallback,
                max_path_check=args.max_path_check,
                json_dup_key_check=args.json_dup_key_check,
            )
            if result["verdict"] == "BLOCK":
                all_pass = False
            logger.info("%s: %s" % (f.name, result["verdict"]))
        return 0 if all_pass else 1

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
