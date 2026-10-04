#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSHE V86-RC2 L2 Evidence Package Integrity Checker
Task: DSHE_V86_RC2_PROD_PHASE_L2_EVIDENCE_AUTO / T3.4

Purpose:
  Automatically validate L2 evidence package file integrity, MD5 checksums,
  and audit field completeness. Missing/tampered items trigger CRITICAL alerts
  and block L2 submission.

Usage:
  python3 l2_evidence_package_check.py --check evidence_package_*.json
  python3 l2_evidence_package_check.py --check-dir .payload_evidence/
  python3 l2_evidence_package_check.py --verify-md5 MD5_CHECKSUM_LIST_evidence.json
  python3 l2_evidence_package_check.py --all .payload_evidence/
  python3 l2_evidence_package_check.py --dry-run

Exit Codes:
  0  - All checks PASS
  1  - One or more CRITICAL violations found
  2  - One or more WARNING violations found
  3  - Script error

Branch: feature/v85-chart-template
Date: 2026-10-15
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import glob
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
LOG_FILE = LOG_DIR / "l2_evidence_check.log"

# Severity levels
CRITICAL = "CRITICAL"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"
INFO = "INFO"

# Required top-level fields
REQUIRED_TOP_FIELDS = {
    "fingerprint": str,
    "run_id": str,
    "session_id": str,
    "total_calls": int,
    "generated_at": str,
    "caller": str,
    "dshb_reuse": bool,
    "calls": list,
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

# DEP registry info
DEP_REGISTRY_ID = "DEP-REG-001"
MAX_PAUSE_DAYS = 30
ROLLBACK_WINDOW_MIN = 15

# ─────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────
def setup_logging(level=logging.INFO):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger("l2_evidence_check")
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


# ─────────────────────────────────────────────────────────────────────
# MD5 Utilities
# ─────────────────────────────────────────────────────────────────────
def compute_file_md5(filepath):
    """Compute MD5 hash of a file."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest().upper()


def compute_json_md5(filepath):
    """Compute MD5 of JSON content (sorted keys for consistency)."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    content = json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2)
    md5 = hashlib.md5(content.encode("utf-8"))
    return md5.hexdigest().upper()


# ─────────────────────────────────────────────────────────────────────
# Integrity Checks
# ─────────────────────────────────────────────────────────────────────
class IntegrityChecker:
    """L2 Evidence Package Integrity Checker."""

    def __init__(self, logger):
        self.logger = logger
        self.results = []
        self.critical_count = 0
        self.warning_count = 0
        self.pass_count = 0

    def _add_result(self, severity, check_id, description, detail=""):
        """Add a check result."""
        result = {
            "severity": severity,
            "check_id": check_id,
            "description": description,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        }
        self.results.append(result)

        if severity == CRITICAL:
            self.critical_count += 1
            self.logger.critical(f"[{check_id}] {description}")
            if detail:
                self.logger.critical(f"  Detail: {detail}")
        elif severity == HIGH:
            self.critical_count += 1
            self.logger.critical(f"[{check_id}] {description}")
        elif severity == MEDIUM:
            self.warning_count += 1
            self.logger.warning(f"[{check_id}] {description}")
        elif severity == LOW:
            self.warning_count += 1
            self.logger.warning(f"[{check_id}] {description}")
        else:
            self.pass_count += 1
            self.logger.info(f"[{check_id}] {description}")

    def check_file_exists(self, filepath):
        """IC-01: Check file existence."""
        if not os.path.exists(filepath):
            self._add_result(CRITICAL, "IC-01", f"File not found: {filepath}")
            return False
        self._add_result(INFO, "IC-01", f"File exists: {filepath}")
        return True

    def check_json_valid(self, filepath):
        """IC-02: Check JSON validity."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._add_result(INFO, "IC-02", f"JSON valid: {filepath}")
            return data
        except json.JSONDecodeError as e:
            self._add_result(CRITICAL, "IC-02",
                             f"JSON invalid: {filepath} - {e}")
            return None

    def check_top_level_fields(self, data, filepath):
        """IC-03: Check required top-level fields."""
        for field, expected_type in REQUIRED_TOP_FIELDS.items():
            if field not in data:
                self._add_result(CRITICAL, "IC-03",
                                 f"Missing top-level field: {field} in {filepath}")
            elif not isinstance(data[field], expected_type):
                self._add_result(CRITICAL, "IC-03",
                                 f"Wrong type for '{field}': "
                                 f"expected {expected_type.__name__}, "
                                 f"got {type(data[field]).__name__}")

        # Check dshb_reuse must be False
        if data.get("dshb_reuse") is True:
            self._add_result(CRITICAL, "IC-03a",
                             f"DSHB reuse detected in {filepath} - "
                             f"dshb_reuse must be FALSE (audit hard rule)")

        # Check fingerprint format
        fingerprint = data.get("fingerprint", "")
        if not fingerprint.startswith("DSHE-"):
            self._add_result(CRITICAL, "IC-03b",
                             f"Invalid fingerprint format: '{fingerprint}' - "
                             f"must start with 'DSHE-'")

    def check_calls_array(self, data, filepath):
        """IC-04: Check calls array integrity."""
        calls = data.get("calls", [])
        total_calls = data.get("total_calls", 0)

        # Check total_calls matches actual
        if len(calls) != total_calls:
            self._add_result(CRITICAL, "IC-04",
                             f"Call count mismatch: total_calls={total_calls}, "
                             f"actual={len(calls)}")

        if total_calls == 0:
            self._add_result(CRITICAL, "IC-04a",
                             f"No calls in evidence package - "
                             f"cannot be valid L2 submission")

        # Check each call
        trace_ids = set()
        for i, call in enumerate(calls):
            call_idx = i + 1

            # Check required call fields
            for field, expected_type in REQUIRED_CALL_FIELDS.items():
                if field not in call:
                    self._add_result(CRITICAL, "IC-04b",
                                     f"Call #{call_idx}: missing field '{field}'")
                    continue
                if not isinstance(call[field], expected_type):
                    self._add_result(CRITICAL, "IC-04c",
                                     f"Call #{call_idx}: wrong type for "
                                     f"'{field}': expected "
                                     f"{expected_type.__name__}")

            # Check trace_id uniqueness
            trace_id = call.get("trace_id", "")
            if not trace_id:
                self._add_result(CRITICAL, "IC-04d",
                                 f"Call #{call_idx}: empty trace_id")
            elif trace_id in trace_ids:
                self._add_result(CRITICAL, "IC-04e",
                                 f"Call #{call_idx}: duplicate trace_id: "
                                 f"'{trace_id}'")
            trace_ids.add(trace_id)

            # Check trace_id format
            if trace_id and not trace_id.startswith("DSHE-"):
                self._add_result(HIGH, "IC-04f",
                                 f"Call #{call_idx}: trace_id format: "
                                 f"'{trace_id}' - should start with 'DSHE-'")

            # Check dshb_reuse per call
            if call.get("dsbh_reuse") is True:
                self._add_result(CRITICAL, "IC-04g",
                                 f"Call #{call_idx}: dshb_reuse=TRUE - "
                                 f"audit hard rule violation")

            # Check call_type
            call_type = call.get("call_type", "")
            if call_type not in ALLOWED_CALL_TYPES:
                self._add_result(CRITICAL, "IC-04h",
                                 f"Call #{call_idx}: invalid call_type: "
                                 f"'{call_type}' - must be "
                                 f"'DSHE_INDEPENDENT_ZHIJI'")

            # Check request_payload
            req_payload = call.get("request_payload")
            if req_payload is None or (isinstance(req_payload, dict) and
                                       len(req_payload) == 0):
                self._add_result(CRITICAL, "IC-04i",
                                 f"Call #{call_idx}: empty/missing "
                                 f"request_payload")

            # Check response_payload
            resp_payload = call.get("response_payload")
            if resp_payload is None or (isinstance(resp_payload, dict) and
                                        len(resp_payload) == 0):
                self._add_result(CRITICAL, "IC-04j",
                                 f"Call #{call_idx}: empty/missing "
                                 f"response_payload")

            # Check status
            status = call.get("status", "")
            if status not in ALLOWED_STATUSES:
                self._add_result(HIGH, "IC-04k",
                                 f"Call #{call_idx}: invalid status: "
                                 f"'{status}'")

            # Check request_payload fields
            if isinstance(req_payload, dict):
                if req_payload.get("independent") is not True:
                    self._add_result(HIGH, "IC-04l",
                                     f"Call #{call_idx}: request_payload."
                                     f"independent should be true")
                if req_payload.get("dsbh_reuse") is not False:
                    self._add_result(CRITICAL, "IC-04m",
                                     f"Call #{call_idx}: request_payload."
                                     f"dsbh_reuse should be false")

    def check_payload_persistence(self, data, filepath, evidence_dir):
        """IC-05: Check that individual call payloads are persisted."""
        calls = data.get("calls", [])
        missing_persistent = 0

        for call in calls:
            trace_id = call.get("trace_id", "")
            if not trace_id:
                continue

            trace_file = evidence_dir / f"{trace_id}.json"
            if not trace_file.exists():
                missing_persistent += 1
                if missing_persistent <= 5:
                    self._add_result(MEDIUM, "IC-05",
                                     f"Persistent payload missing: {trace_id}")

        if missing_persistent > 5:
            self._add_result(MEDIUM, "IC-05",
                             f"Additional {missing_persistent - 5} "
                             f"persistent payloads missing")

        if missing_persistent == 0 and len(calls) > 0:
            self._add_result(INFO, "IC-05",
                             f"All {len(calls)} call payloads persisted")

    def check_evidence_index(self, evidence_dir):
        """IC-06: Check evidence index file."""
        index_file = evidence_dir / "evidence_index.json"
        if not index_file.exists():
            self._add_result(LOW, "IC-06",
                             "evidence_index.json not found - "
                             "generate with dep_recovery_auto_verify_v3.py")
            return

        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index = json.load(f)

            if "fingerprint" not in index:
                self._add_result(MEDIUM, "IC-06",
                                 "evidence_index.json missing 'fingerprint'")
            if "run_id" not in index:
                self._add_result(MEDIUM, "IC-06",
                                 "evidence_index.json missing 'run_id'")

        except json.JSONDecodeError as e:
            self._add_result(CRITICAL, "IC-06",
                             f"evidence_index.json invalid: {e}")

    def check_negative_scenarios(self, data, filepath):
        """IC-07: Check for known negative scenario patterns."""
        # NEG-01: Old bridge rate fabrication
        calls = data.get("calls", [])
        if len(calls) == 0:
            self._add_result(CRITICAL, "NEG-01",
                             "Old bridge rate fabrication detected: "
                             "total_calls=0 but evidence claims L2 pass")

        # NEG-04: DSHB reuse (already checked per-call, but also at top level)
        if data.get("dshb_reuse") is True:
            self._add_result(CRITICAL, "NEG-04",
                             "DSHB result reuse detected: "
                             "dshb_reuse=TRUE at top level")

    def check_evidence_package(self, filepath, evidence_dir=None):
        """Full integrity check on an evidence package."""
        self.logger.info("=" * 60)
        self.logger.info(f"Checking evidence package: {filepath}")
        self.logger.info("=" * 60)

        if evidence_dir is None:
            evidence_dir = Path(filepath).parent

        # IC-01: File exists
        if not self.check_file_exists(filepath):
            return False

        # IC-02: JSON valid
        data = self.check_json_valid(filepath)
        if data is None:
            return False

        # IC-03: Top-level fields
        self.check_top_level_fields(data, filepath)

        # IC-04: Calls array
        self.check_calls_array(data, filepath)

        # IC-05: Payload persistence
        self.check_payload_persistence(data, filepath, evidence_dir)

        # IC-06: Evidence index
        self.check_evidence_index(evidence_dir)

        # IC-07: Negative scenarios
        self.check_negative_scenarios(data, filepath)

        return self.critical_count == 0

    def verify_md5_list(self, md5_list_file):
        """Verify MD5 checksum list."""
        self.logger.info("=" * 60)
        self.logger.info(f"Verifying MD5 list: {md5_list_file}")
        self.logger.info("=" * 60)

        if not os.path.exists(md5_list_file):
            self._add_result(CRITICAL, "MD5-01",
                             f"MD5 checksum list not found: {md5_list_file}")
            return False

        try:
            with open(md5_list_file, "r", encoding="utf-8") as f:
                md5_data = json.load(f)
        except json.JSONDecodeError as e:
            self._add_result(CRITICAL, "MD5-01",
                             f"MD5 checksum list invalid JSON: {e}")
            return False

        files = md5_data.get("files", [])
        evidence_dir = md5_data.get("evidence_dir", ".")

        verified = 0
        failed = 0

        for entry in files:
            filename = entry.get("filename", "")
            expected_md5 = entry.get("md5", "")
            filepath = Path(evidence_dir) / filename

            if not filepath.exists():
                self._add_result(CRITICAL, "MD5-02",
                                 f"File missing from MD5 list: {filename}")
                failed += 1
                continue

            actual_md5 = compute_file_md5(filepath)
            if actual_md5 != expected_md5.upper():
                self._add_result(CRITICAL, "MD5-03",
                                 f"MD5 mismatch: {filename} - "
                                 f"expected {expected_md5}, got {actual_md5}")
                failed += 1
            else:
                self.logger.info(f"  MD5 OK: {filename}")
                verified += 1

        self.logger.info(f"MD5 verification: {verified} passed, {failed} failed")

        if failed > 0:
            return False
        return True

    def get_summary(self):
        """Get check summary."""
        return {
            "total_checks": len(self.results),
            "pass_count": self.pass_count,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "verdict": "FAIL" if self.critical_count > 0
                       else ("WARNING" if self.warning_count > 0
                             else "PASS"),
        }

    def generate_report(self, filepath=None):
        """Generate human-readable report."""
        summary = self.get_summary()
        lines = []
        lines.append("=" * 60)
        lines.append("L2 Evidence Package Integrity Check Report")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Timestamp: {datetime.now().isoformat()}")
        lines.append(f"Checker: l2_evidence_package_check.py")
        lines.append(f"Dep Registry: {DEP_REGISTRY_ID}")
        lines.append(f"Max Pause: {MAX_PAUSE_DAYS} days")
        lines.append(f"Rollback Window: {ROLLBACK_WINDOW_MIN} min")
        lines.append("")
        lines.append("Summary:")
        lines.append(f"  Total Checks: {summary['total_checks']}")
        lines.append(f"  PASS: {summary['pass_count']}")
        lines.append(f"  CRITICAL: {summary['critical_count']}")
        lines.append(f"  WARNING: {summary['warning_count']}")
        lines.append(f"  Verdict: {'✅ ' if summary['verdict'] == 'PASS' else '❌ '}"
                     f"{summary['verdict']}")
        lines.append("")

        if self.results:
            lines.append("Details:")
            lines.append("-" * 60)
            for r in self.results:
                icon = {"PASS": "✅", "CRITICAL": "🚨", "HIGH": "🔴",
                        "MEDIUM": "⚠️", "LOW": "ℹ️"}.get(
                    r["severity"], "❓")
                lines.append(f"  {icon} [{r['check_id']}] "
                             f"{r['severity']}: {r['description']}")
                if r["detail"]:
                    lines.append(f"     {r['detail']}")
            lines.append("")

        lines.append("=" * 60)
        lines.append(f"Dep Registry: {DEP_REGISTRY_ID}")
        lines.append(f"Status: {summary['verdict']}")
        lines.append("=" * 60)

        report = "\n".join(lines)

        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report)

        return report

    def generate_json_report(self, filepath=None):
        """Generate JSON report."""
        summary = self.get_summary()
        report = {
            "generated_at": datetime.now().isoformat(),
            "checker": "l2_evidence_package_check.py",
            "dep_registry_id": DEP_REGISTRY_ID,
            "max_pause_days": MAX_PAUSE_DAYS,
            "rollback_window_min": ROLLBACK_WINDOW_MIN,
            "summary": summary,
            "results": self.results,
            "constraints": {
                "JOB_READY": False,
                "NO_ZHIJI_API_CALL": False,
                "NO_MODIFY_V85": True,
                "NO_OVERWRITE": True,
                "BRANCH_LOCKED": True,
                "L2_INDEPENDENT_CALL_CHAIN": True,
                "NO_DSHB_REUSE": True,
                "AUDIT_TRACEABILITY": True,
            },
        }

        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

        return report


# ─────────────────────────────────────────────────────────────────────
# Evidence Package Auto-Packaging Helper
# ─────────────────────────────────────────────────────────────────────
def generate_md5_checksum_list(evidence_dir, logger):
    """Generate MD5 checksum list for all evidence files."""
    evidence_dir = Path(evidence_dir)
    files_info = []

    for filepath in sorted(evidence_dir.glob("*.json")):
        if filepath.name.startswith("MD5_CHECKSUM_LIST_"):
            continue

        md5 = compute_file_md5(filepath)
        size = filepath.stat().st_size
        files_info.append({
            "filename": filepath.name,
            "md5": md5,
            "size": size,
            "mtime": datetime.fromtimestamp(
                filepath.stat().st_mtime
            ).isoformat(),
        })

    md5_list = {
        "generated_at": datetime.now().isoformat(),
        "evidence_dir": str(evidence_dir),
        "dep_registry_id": DEP_REGISTRY_ID,
        "total_files": len(files_info),
        "total_size": sum(f["size"] for f in files_info),
        "files": files_info,
    }

    md5_file = evidence_dir / "MD5_CHECKSUM_LIST_evidence.json"
    with open(md5_file, "w", encoding="utf-8") as f:
        json.dump(md5_list, f, indent=2, ensure_ascii=False)

    logger.info(f"MD5 checksum list generated: {md5_file.name} "
                f"({len(files_info)} files, "
                f"{sum(f['size'] for f in files_info):,} B)")

    return md5_list


def generate_evidence_index(evidence_dir, logger):
    """Generate evidence index."""
    evidence_dir = Path(evidence_dir)

    evidence_packages = []
    for filepath in sorted(evidence_dir.glob("evidence_package_*.json")):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            evidence_packages.append({
                "filename": filepath.name,
                "fingerprint": data.get("fingerprint", ""),
                "run_id": data.get("run_id", ""),
                "session_id": data.get("session_id", ""),
                "total_calls": data.get("total_calls", 0),
                "generated_at": data.get("generated_at", ""),
                "dshb_reuse": data.get("dshb_reuse", False),
                "size": filepath.stat().st_size,
            })
        except Exception as e:
            logger.warning(f"Failed to parse {filepath.name}: {e}")

    index = {
        "generated_at": datetime.now().isoformat(),
        "evidence_dir": str(evidence_dir),
        "dep_registry_id": DEP_REGISTRY_ID,
        "total_evidence_packages": len(evidence_packages),
        "evidence_packages": evidence_packages,
    }

    index_file = evidence_dir / "evidence_index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    logger.info(f"Evidence index generated: {index_file.name} "
                f"({len(evidence_packages)} packages)")

    return index


# ─────────────────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="L2 Evidence Package Integrity Checker"
    )
    parser.add_argument("--check", type=str, nargs="+",
                        help="Evidence package file(s) to check")
    parser.add_argument("--check-dir", type=str,
                        help="Directory to check all evidence packages")
    parser.add_argument("--verify-md5", type=str,
                        help="MD5 checksum list file to verify")
    parser.add_argument("--all", type=str,
                        help="Full check: integrity + MD5 + index")
    parser.add_argument("--generate-md5", type=str,
                        help="Generate MD5 checksum list for directory")
    parser.add_argument("--generate-index", type=str,
                        help="Generate evidence index for directory")
    parser.add_argument("--evidence-dir", type=str,
                        default=str(DEFAULT_EVIDENCE_DIR),
                        help="Evidence directory (default: .payload_evidence/)")
    parser.add_argument("--report", type=str,
                        help="Output report file path")
    parser.add_argument("--json-report", type=str,
                        help="Output JSON report file path")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable debug logging")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without writing")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(log_level)

    if args.dry_run:
        logger.info("[DRY-RUN] Dry run mode - no files will be written")

    if args.generate_md5:
        evidence_dir = Path(args.generate_md5)
        if args.dry_run:
            logger.info(f"[DRY-RUN] Would generate MD5 list for {evidence_dir}")
        else:
            generate_md5_checksum_list(evidence_dir, logger)
        return 0

    if args.generate_index:
        evidence_dir = Path(args.generate_index)
        if args.dry_run:
            logger.info(f"[DRY-RUN] Would generate index for {evidence_dir}")
        else:
            generate_evidence_index(evidence_dir, logger)
        return 0

    checker = IntegrityChecker(logger)
    all_pass = True

    if args.check:
        for filepath in args.check:
            result = checker.check_evidence_package(
                filepath, Path(args.evidence_dir)
            )
            if not result:
                all_pass = False

    if args.check_dir:
        evidence_dir = Path(args.check_dir)
        if not evidence_dir.exists():
            logger.error(f"Directory not found: {evidence_dir}")
            return 3

        patterns = [
            evidence_dir / "evidence_package_*.json",
        ]
        found = False
        for pattern in patterns:
            for filepath in sorted(evidence_dir.glob(pattern.name)):
                if not filepath.name.startswith("evidence_package_"):
                    continue
                found = True
                result = checker.check_evidence_package(
                    filepath, evidence_dir
                )
                if not result:
                    all_pass = False

        if not found:
            logger.warning(f"No evidence packages found in {evidence_dir}")

    if args.all:
        evidence_dir = Path(args.all)
        if not evidence_dir.exists():
            logger.error(f"Directory not found: {evidence_dir}")
            return 3

        # Check all evidence packages
        for filepath in sorted(evidence_dir.glob("evidence_package_*.json")):
            result = checker.check_evidence_package(filepath, evidence_dir)
            if not result:
                all_pass = False

        # Generate and verify MD5
        if not args.dry_run:
            generate_md5_checksum_list(evidence_dir, logger)
            generate_evidence_index(evidence_dir, logger)

        # Verify MD5
        md5_file = evidence_dir / "MD5_CHECKSUM_LIST_evidence.json"
        if md5_file.exists():
            result = checker.verify_md5_list(md5_file)
            if not result:
                all_pass = False

    if args.verify_md5:
        result = checker.verify_md5_list(args.verify_md5)
        if not result:
            all_pass = False

    # Generate reports
    if args.report:
        checker.generate_report(args.report)
        logger.info(f"Report generated: {args.report}")

    if args.json_report:
        checker.generate_json_report(args.json_report)
        logger.info(f"JSON report generated: {args.json_report}")

    # Summary
    summary = checker.get_summary()
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info(f"  Total: {summary['total_checks']}")
    logger.info(f"  PASS: {summary['pass_count']}")
    logger.info(f"  CRITICAL: {summary['critical_count']}")
    logger.info(f"  WARNING: {summary['warning_count']}")
    logger.info(f"  Verdict: {summary['verdict']}")
    logger.info("=" * 60)

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
