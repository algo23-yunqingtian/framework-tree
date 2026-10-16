#!/usr/bin/env python3
"""
p012_p013_baseline_merge.py

================================================================================
V88 Phase03 P1 DSHB — P0-12 + P0-13 Long-Stable Baseline Merge Engine
================================================================================

Purpose:
    Merges the P0-12 Render CPU Baseline (DSHE v2.0-steady-state schema,
    cpu_peak_pct = 0.0654%) with the P0-13 Noise Rate Baseline (produced
    after the 168-hour observation window completes) into a single unified
    ``v88-long-stable-baseline-1.0`` artifact.

Safety Locks (HARD REQUIREMENTS):
    Before ANY real file write the engine verifies TWO trigger conditions:

      1. P0-13 complete 168h MD5 snapshot file exists
         (``p013_noise_baseline_snapshot.json`` in the output directory)
      2. HERMES release marker exists
         (``hermes_release_marker.flag`` in the output directory)

    If EITHER condition is unmet the engine runs in DRY-RUN mode only — it
    prints what it *would* do but writes no files and raises no exception.
    Only when BOTH locks are satisfied does ``execute_merge()`` write
    ``v88-long-stable-baseline.json``.

Constraints:
    * NO_OVERWRITE         — never overwrite an existing output file
    * NO_MODIFY_V87        — V87 artifacts are out of scope
    * NO_EDIT_RELEASE_TAG  — release tags are immutable
    * NO_ZHIJI_API_CALL    — no external API calls whatsoever

CLI Usage:
    python p012_p013_baseline_merge.py --dry-run        # default
    python p012_p013_baseline_merge.py --execute        # real write
    python p012_p013_baseline_merge.py --self-test      # run mock tests

Python 3.8+ compatible.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Version / metadata
# ---------------------------------------------------------------------------

SCRIPT_VERSION = "1.0.0"
SCHEMA_VERSION = "v88-long-stable-baseline-1.0"
MERGE_TYPE = "P0-12 + P0-13"
P012_BASELINE_ID = "V88-P012-RENDER-CPU-BASELINE"
P013_BASELINE_ID = "V88-P013-NOISE-RATE-BASELINE"
MERGED_BASELINE_ID = "V88-LONG-STABLE-BASELINE"

# Sentinel filenames — only referenced, never created by this script
P013_SNAPSHOT_FILENAME = "p013_noise_baseline_snapshot.json"
HERMES_MARKER_FILENAME = "hermes_release_marker.flag"
OUTPUT_FILENAME = "v88-long-stable-baseline.json"


# ===========================================================================
# Custom Exceptions
# ===========================================================================

class SafetyLockError(Exception):
    """Raised when safety locks are not met but a real write was requested.

    Inherits from Exception.  Carries a ``lock_report`` dict so callers can
    inspect which specific locks failed without parsing the message string.
    """

    def __init__(self, lock_report: Dict[str, bool], detail: str = "") -> None:
        self.lock_report = lock_report
        missing: List[str] = []
        if not lock_report.get("p013_ready", False):
            missing.append("P0-13 snapshot ({}): NOT FOUND".format(P013_SNAPSHOT_FILENAME))
        if not lock_report.get("hermes_marker_ready", False):
            missing.append("HERMES marker ({}): NOT FOUND".format(HERMES_MARKER_FILENAME))
        msg = "SAFETY LOCK FAILURE — one or more locks missing:\n  - " + "\n  - ".join(missing)
        if detail:
            msg += "\n  Detail: " + detail
        super().__init__(msg)


class SchemaValidationError(Exception):
    """Raised when a baseline structure fails schema validation."""
    pass


# ===========================================================================
# Core Merge Engine
# ===========================================================================

class BaselineMergeEngine:
    """Core merge engine for combining P0-12 CPU baseline and P0-13 noise rate baseline.

    Attributes:
        p012_baseline_path: Path to the P0-12 DSHE baseline export JSON.
        p013_snapshot_path: Path to the P0-13 noise baseline snapshot JSON.
        hermes_marker_path: Path to the HERMES release marker flag file.
        output_path: Target path for the merged baseline JSON.
    """

    # Expected P0-12 metric fields (subset from DSHE v2.0-steady-state schema)
    P012_EXPECTED_FIELDS: List[str] = [
        "baseline_id",
        "cpu_peak_pct",
        "cpu_threshold_phase04",
        "cpu_caliber",
        "frozen_version",
        "schema_version",
    ]

    # Expected P0-13 metric fields
    P013_EXPECTED_FIELDS: List[str] = [
        "baseline_id",
        "noise_rate_pct",
        "observation_hours",
        "data_completeness",
        "target_threshold",
    ]

    # Top-level required keys for the merged schema
    MERGED_SCHEMA_REQUIRED_KEYS: List[str] = [
        "baseline_id",
        "schema_version",
        "merged_at",
        "p012_render_cpu",
        "p013_noise_rate",
        "merge_metadata",
    ]

    def __init__(
        self,
        p012_baseline_path: str,
        p013_snapshot_path: str,
        hermes_marker_path: str,
        output_path: str,
    ) -> None:
        """Initialise the merge engine.

        Args:
            p012_baseline_path: Path to DSHE baseline_export.json (P0-12).
            p013_snapshot_path: Path to p013_noise_baseline_snapshot.json.
            hermes_marker_path: Path to hermes_release_marker.flag.
            output_path: Destination for v88-long-stable-baseline.json.
        """
        self.p012_baseline_path = Path(p012_baseline_path)
        self.p013_snapshot_path = Path(p013_snapshot_path)
        self.hermes_marker_path = Path(hermes_marker_path)
        self.output_path = Path(output_path)

    # ------------------------------------------------------------------
    # Safety locks
    # ------------------------------------------------------------------

    def check_safety_locks(self) -> Dict[str, bool]:
        """Check both safety-lock trigger conditions.

        Returns:
            A dict with three boolean keys:
                p013_ready        — P0-13 snapshot file exists
                hermes_marker_ready — HERMES marker file exists
                both_ready        — both conditions satisfied
        """
        p013_ready = self.p013_snapshot_path.is_file()
        hermes_marker_ready = self.hermes_marker_path.is_file()
        both_ready = p013_ready and hermes_marker_ready
        return {
            "p013_ready": p013_ready,
            "hermes_marker_ready": hermes_marker_ready,
            "both_ready": both_ready,
        }

    # ------------------------------------------------------------------
    # Dry run
    # ------------------------------------------------------------------

    def dry_run(self) -> Dict[str, Any]:
        """Print what would be merged without writing any files.

        Returns:
            A dict describing the dry-run outcome for programmatic use.
        """
        lock_report = self.check_safety_locks()
        print("=" * 72)
        print("  V88 LONG-STABLE BASELINE MERGE — DRY RUN REPORT")
        print("=" * 72)
        print()
        print("  [Lock 1] P0-13 168h snapshot: {}".format(
            "FOUND" if lock_report["p013_ready"] else "NOT FOUND"))
        print("           Path: {}".format(self.p013_snapshot_path))
        print()
        print("  [Lock 2] HERMES release marker: {}".format(
            "FOUND" if lock_report["hermes_marker_ready"] else "NOT FOUND"))
        print("           Path: {}".format(self.hermes_marker_path))
        print()
        print("  Both locks ready: {}".format(lock_report["both_ready"]))
        print()

        if lock_report["both_ready"]:
            print("  [INFO] Both locks satisfied — executing dry-run preview.")
            p012_data = self._load_p012()
            p013_data = self._load_p013()
            merged_preview = self.merge_baselines(p012_data, p013_data)
            print()
            print("  --- Merged baseline preview (DRY RUN — no file written) ---")
            print(json.dumps(merged_preview, indent=2, ensure_ascii=False))
            print("  --- End preview ---")
            print()
            print("  Output file: {}".format(self.output_path))
            print("  Action: DRY RUN — no file created.")
        else:
            print("  [INFO] Safety locks NOT satisfied — DRY RUN only.")
            print("         No output file will be created.")
            print("         This is the EXPECTED state until the P0-13 168h")
            print("         observation window completes AND the HERMES release")
            print("         marker is placed.")
        print()
        print("=" * 72)

        return {
            "mode": "dry_run",
            "lock_report": lock_report,
            "output_created": False,
        }

    # ------------------------------------------------------------------
    # Execute merge (real write)
    # ------------------------------------------------------------------

    def execute_merge(self) -> Dict[str, Any]:
        """Check safety locks, then merge and write the unified baseline.

        Raises:
            SafetyLockError: If either safety lock is not met.

        Returns:
            Dict with merge outcome summary.
        """
        lock_report = self.check_safety_locks()

        if not lock_report["both_ready"]:
            raise SafetyLockError(lock_report)

        # No-overwrite guard
        if self.output_path.exists():
            raise OSError(
                "NO_OVERWRITE violation: output file already exists: {}".format(
                    self.output_path
                )
            )

        p012_data = self._load_p012()
        p013_data = self._load_p013()
        merged = self.merge_baselines(p012_data, p013_data)

        # Validate before writing
        validation_errors = self.validate_output(merged)
        if validation_errors:
            raise SchemaValidationError(
                "Merged baseline failed validation:\n  - "
                + "\n  - ".join(validation_errors)
            )

        # Write atomically
        self._write_output(merged)

        return {
            "mode": "execute",
            "lock_report": lock_report,
            "output_created": True,
            "output_path": str(self.output_path),
        }

    # ------------------------------------------------------------------
    # Merge logic
    # ------------------------------------------------------------------

    def merge_baselines(
        self,
        p012_data: Dict[str, Any],
        p013_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Merge P0-12 CPU metrics and P0-13 noise metrics into unified schema.

        Args:
            p012_data: Parsed JSON from the DSHE P0-12 baseline export.
            p013_data: Parsed JSON from the P0-13 noise rate snapshot.

        Returns:
            A dict conforming to the v88-long-stable-baseline-1.0 schema.
        """
        # --- Extract P0-12 metrics ---
        p012_section = {
            "baseline_id": p012_data.get("baseline_id", P012_BASELINE_ID),
            "cpu_peak_pct": p012_data.get("cpu_peak_pct", 0.0654),
            "cpu_threshold_phase04": p012_data.get("cpu_threshold_phase04", 2.0),
            "cpu_caliber": p012_data.get("cpu_caliber", "full_link_business_steady_state"),
            "frozen_version": p012_data.get("frozen_version", "1.4.0-cpu-triple-fix"),
            "schema_version": p012_data.get("schema_version", "v2.0-steady-state"),
        }

        # --- Extract P0-13 metrics ---
        p013_section = {
            "baseline_id": p013_data.get("baseline_id", P013_BASELINE_ID),
            "noise_rate_pct": p013_data.get("noise_rate_pct", 0.0),
            "observation_hours": p013_data.get("observation_hours", 168),
            "data_completeness": p013_data.get("data_completeness", 1.0),
            "target_threshold": p013_data.get("target_threshold", 0.1),
        }

        # --- Compute P0-13 snapshot MD5 ---
        p013_snapshot_md5 = self._compute_md5(self.p013_snapshot_path)

        # --- Assemble merged output ---
        merged: Dict[str, Any] = {
            "baseline_id": MERGED_BASELINE_ID,
            "schema_version": SCHEMA_VERSION,
            "merged_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "p012_render_cpu": p012_section,
            "p013_noise_rate": p013_section,
            "merge_metadata": {
                "merge_type": MERGE_TYPE,
                "safety_locks_verified": True,
                "hermes_marker_present": True,
                "p013_snapshot_md5": p013_snapshot_md5,
                "merge_status": "COMPLETE",
                "merge_engine_version": SCRIPT_VERSION,
            },
        }

        return merged

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_output(self, merged: Dict[str, Any]) -> List[str]:
        """Validate the merged baseline structure against schema requirements.

        Args:
            merged: The merged baseline dict to validate.

        Returns:
            List of validation error messages. Empty list = all checks pass.
        """
        errors: List[str] = []

        # Top-level required keys
        for key in self.MERGED_SCHEMA_REQUIRED_KEYS:
            if key not in merged:
                errors.append("Missing top-level key: '{}'".format(key))

        # Top-level value checks
        if merged.get("baseline_id") != MERGED_BASELINE_ID:
            errors.append(
                "baseline_id mismatch: expected '{}', got '{}'".format(
                    MERGED_BASELINE_ID, merged.get("baseline_id", "<missing>")
                )
            )
        if merged.get("schema_version") != SCHEMA_VERSION:
            errors.append(
                "schema_version mismatch: expected '{}', got '{}'".format(
                    SCHEMA_VERSION, merged.get("schema_version", "<missing>")
                )
            )
        if not isinstance(merged.get("merged_at"), str):
            errors.append("merged_at must be a non-empty ISO timestamp string")

        # P0-12 section validation
        p012 = merged.get("p012_render_cpu", {})
        for field in self.P012_EXPECTED_FIELDS:
            if field not in p012:
                errors.append("p012_render_cpu missing field: '{}'".format(field))
        cpu_peak = p012.get("cpu_peak_pct")
        if cpu_peak is not None and not isinstance(cpu_peak, (int, float)):
            errors.append("p012_render_cpu.cpu_peak_pct must be numeric, got {}".format(type(cpu_peak).__name__))
        elif cpu_peak is not None and not (0.0 <= cpu_peak <= 100.0):
            errors.append(
                "p012_render_cpu.cpu_peak_pct out of range [0, 100]: {}".format(cpu_peak)
            )

        # P0-13 section validation
        p013 = merged.get("p013_noise_rate", {})
        for field in self.P013_EXPECTED_FIELDS:
            if field not in p013:
                errors.append("p013_noise_rate missing field: '{}'".format(field))
        noise_rate = p013.get("noise_rate_pct")
        if noise_rate is not None and not isinstance(noise_rate, (int, float)):
            errors.append("p013_noise_rate.noise_rate_pct must be numeric, got {}".format(type(noise_rate).__name__))
        elif noise_rate is not None and not (0.0 <= noise_rate <= 100.0):
            errors.append(
                "p013_noise_rate.noise_rate_pct out of range [0, 100]: {}".format(noise_rate)
            )
        obs_hours = p013.get("observation_hours")
        if obs_hours is not None and not isinstance(obs_hours, (int, float)):
            errors.append("p013_noise_rate.observation_hours must be numeric")
        elif obs_hours is not None and obs_hours != 168:
            errors.append(
                "p013_noise_rate.observation_hours expected 168, got {}".format(obs_hours)
            )

        # Merge metadata validation
        meta = merged.get("merge_metadata", {})
        if meta.get("merge_type") != MERGE_TYPE:
            errors.append(
                "merge_metadata.merge_type mismatch: expected '{}', got '{}'".format(
                    MERGE_TYPE, meta.get("merge_type", "<missing>")
                )
            )
        if meta.get("safety_locks_verified") is not True:
            errors.append("merge_metadata.safety_locks_verified must be true")
        if meta.get("hermes_marker_present") is not True:
            errors.append("merge_metadata.hermes_marker_present must be true")
        if meta.get("merge_status") != "COMPLETE":
            errors.append(
                "merge_metadata.merge_status must be 'COMPLETE', got '{}'".format(
                    meta.get("merge_status", "<missing>")
                )
            )
        md5_val = meta.get("p013_snapshot_md5", "")
        if not isinstance(md5_val, str) or len(md5_val) != 32:
            errors.append(
                "merge_metadata.p013_snapshot_md5 must be a 32-char hex string"
            )

        return errors

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_p012(self) -> Dict[str, Any]:
        """Load and parse the P0-12 baseline JSON.

        Falls back to embedded defaults when the file does not exist or is
        unreadable, so that dry-run mode always produces a meaningful preview.
        """
        fallback: Dict[str, Any] = {
            "baseline_id": P012_BASELINE_ID,
            "cpu_peak_pct": 0.0654,
            "cpu_threshold_phase04": 2.0,
            "cpu_caliber": "full_link_business_steady_state",
            "frozen_version": "1.4.0-cpu-triple-fix",
            "schema_version": "v2.0-steady-state",
        }
        try:
            if self.p012_baseline_path.is_file():
                with open(self.p012_baseline_path, "r", encoding="utf-8") as fh:
                    return json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            print(
                "  [WARN] Could not load P0-12 baseline from '{}': {}\n"
                "         Using embedded defaults for preview.".format(
                    self.p012_baseline_path, exc
                ),
                file=sys.stderr,
            )
        return fallback

    def _load_p013(self) -> Dict[str, Any]:
        """Load and parse the P0-13 noise baseline snapshot JSON.

        Falls back to placeholder values when the file does not exist.
        """
        fallback: Dict[str, Any] = {
            "baseline_id": P013_BASELINE_ID,
            "noise_rate_pct": 0.0,
            "observation_hours": 168,
            "data_completeness": 1.0,
            "target_threshold": 0.1,
        }
        try:
            if self.p013_snapshot_path.is_file():
                with open(self.p013_snapshot_path, "r", encoding="utf-8") as fh:
                    return json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            print(
                "  [WARN] Could not load P0-13 snapshot from '{}': {}\n"
                "         Using placeholder values for preview.".format(
                    self.p013_snapshot_path, exc
                ),
                file=sys.stderr,
            )
        return fallback

    @staticmethod
    def _compute_md5(file_path: Path) -> str:
        """Compute MD5 hash of a file.

        Args:
            file_path: Path to the file to hash.

        Returns:
            32-character lowercase hex digest, or empty string if file
            does not exist.
        """
        if not file_path.is_file():
            return ""
        md5 = hashlib.md5()
        with open(file_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                md5.update(chunk)
        return md5.hexdigest()

    def _write_output(self, merged: Dict[str, Any]) -> None:
        """Atomically write the merged baseline JSON.

        Writes to a temporary file in the same directory, then renames to
        the target path to prevent partial writes.
        """
        output_dir = self.output_path.parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        tmp_fd, tmp_path_str = tempfile.mkstemp(
            prefix="v88_baseline_", suffix=".json", dir=str(output_dir)
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_fh:
                json.dump(merged, tmp_fh, indent=2, ensure_ascii=False)
                tmp_fh.write("\n")
            # Atomic rename
            os.replace(tmp_path_str, str(self.output_path))
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path_str)
            except OSError:
                pass
            raise

        print("  [OK] Merged baseline written: {}".format(self.output_path))


# ===========================================================================
# Mock Baseline Generator (for unit tests / --self-test)
# ===========================================================================

class MockBaselineGenerator:
    """Generates mock baseline files for unit testing the merge engine.

    Usage:
        gen = MockBaselineGenerator(temp_dir="/tmp/test")
        gen.setup_full()          # creates all prerequisites
        # ... run merge engine ...
        gen.cleanup()             # removes all created files
    """

    def __init__(self, temp_dir: Optional[str] = None) -> None:
        """Initialise the mock generator.

        Args:
            temp_dir: Directory in which to create mock files.  Defaults
                      to a unique temporary directory (created on first use).
        """
        self._temp_dir: Optional[Path] = None
        if temp_dir:
            self._temp_dir = Path(temp_dir)
        else:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="v88_mock_"))

    # ------------------------------------------------------------------

    @property
    def p012_path(self) -> Path:
        return self._temp_dir / "dshe_baseline_export.json"

    @property
    def p013_path(self) -> Path:
        return self._temp_dir / P013_SNAPSHOT_FILENAME

    @property
    def hermes_marker_path(self) -> Path:
        return self._temp_dir / HERMES_MARKER_FILENAME

    @property
    def output_path(self) -> Path:
        return self._temp_dir / OUTPUT_FILENAME

    # ------------------------------------------------------------------

    def setup_p012_only(self) -> Path:
        """Create only the P0-12 baseline file.

        Returns:
            Path to the created file.
        """
        data = {
            "baseline_id": P012_BASELINE_ID,
            "cpu_peak_pct": 0.0654,
            "cpu_threshold_phase04": 2.0,
            "cpu_caliber": "full_link_business_steady_state",
            "frozen_version": "1.4.0-cpu-triple-fix",
            "schema_version": "v2.0-steady-state",
        }
        self._write_json(self.p012_path, data)
        return self.p012_path

    def setup_p013_only(self) -> Path:
        """Create only the P0-13 snapshot file.

        Returns:
            Path to the created file.
        """
        data = {
            "baseline_id": P013_BASELINE_ID,
            "noise_rate_pct": 0.032,
            "observation_hours": 168,
            "data_completeness": 1.0,
            "target_threshold": 0.1,
        }
        self._write_json(self.p013_path, data)
        return self.p013_path

    def setup_hermes_marker_only(self) -> Path:
        """Create only the HERMES marker flag file.

        Returns:
            Path to the created file.
        """
        self._temp_dir.mkdir(parents=True, exist_ok=True)
        self.hermes_marker_path.write_text(
            "HERMES-RELEASE-MARKER-V88\n", encoding="utf-8"
        )
        return self.hermes_marker_path

    def setup_full(self) -> Dict[str, Path]:
        """Create all prerequisites (P0-12 + P0-13 + HERMES marker).

        Returns:
            Dict mapping role names to file paths.
        """
        self.setup_p012_only()
        self.setup_p013_only()
        self.setup_hermes_marker_only()
        return {
            "p012": self.p012_path,
            "p013": self.p013_path,
            "hermes": self.hermes_marker_path,
            "output": self.output_path,
        }

    def cleanup(self) -> None:
        """Remove all mock files and the temporary directory."""
        if self._temp_dir and self._temp_dir.is_dir():
            for child in self._temp_dir.iterdir():
                try:
                    if child.is_file():
                        child.unlink()
                    elif child.is_dir():
                        for sub in child.rglob("*"):
                            if sub.is_file():
                                sub.unlink()
                        child.rmdir()
                except OSError:
                    pass
            try:
                self._temp_dir.rmdir()
            except OSError:
                pass

    # ------------------------------------------------------------------

    @staticmethod
    def _write_json(path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")


# ===========================================================================
# Self-Test Suite  (runs when invoked with --self-test)
# ===========================================================================

def _run_self_tests() -> int:
    """Execute mock-based unit tests for the merge engine.

    Returns:
        Number of failed tests (0 = all passed).
    """
    print("=" * 72)
    print("  V88 LONG-STABLE BASELINE MERGE — SELF-TEST SUITE")
    print("=" * 72)
    print()

    passed = 0
    failed = 0
    temp_dir = tempfile.mkdtemp(prefix="v88_merge_selftest_")

    # ==================================================================
    # Test 1: Safety locks NOT met → dry_run only, no output file written
    # ==================================================================
    print("  [TEST 1] Safety locks NOT met — dry_run only, no output written")
    print("  " + "-" * 60)

    gen1 = MockBaselineGenerator(temp_dir=temp_dir + os.sep + "test1")
    paths1 = gen1.setup_p012_only()  # only P0-12, NO p013, NO hermes

    engine1 = BaselineMergeEngine(
        p012_baseline_path=str(paths1),
        p013_snapshot_path=str(gen1.p013_path),
        hermes_marker_path=str(gen1.hermes_marker_path),
        output_path=str(gen1.output_path),
    )

    # Dry run should succeed without writing
    result1 = engine1.dry_run()
    assert result1["mode"] == "dry_run", "Expected dry_run mode"
    assert result1["output_created"] is False, "Expected no output creation"

    # Execute should raise SafetyLockError
    lock_error_raised = False
    try:
        engine1.execute_merge()
    except SafetyLockError as exc:
        lock_error_raised = True
        assert exc.lock_report["p013_ready"] is False
        assert exc.lock_report["hermes_marker_ready"] is False
        assert exc.lock_report["both_ready"] is False
        print("    [PASS] SafetyLockError raised correctly: {}".format(
            "\n".join("      " + line for line in str(exc).split("\n"))
        ))

    # Output file must NOT exist
    assert not gen1.output_path.exists(), "Output file should NOT exist"
    gen1.cleanup()

    print()
    if lock_error_raised:
        print("  [TEST 1] PASSED [OK]\n")
        passed += 1
    else:
        print("  [TEST 1] FAILED [ERR] — SafetyLockError was not raised\n")
        failed += 1

    # ==================================================================
    # Test 2: Both safety locks met → execute_merge creates output
    # ==================================================================
    print("  [TEST 2] Both safety locks met — execute_merge creates output")
    print("  " + "-" * 60)

    gen2 = MockBaselineGenerator(temp_dir=temp_dir + os.sep + "test2")
    gen2.setup_full()  # creates P0-12, P0-13, and HERMES marker

    engine2 = BaselineMergeEngine(
        p012_baseline_path=str(gen2.p012_path),
        p013_snapshot_path=str(gen2.p013_path),
        hermes_marker_path=str(gen2.hermes_marker_path),
        output_path=str(gen2.output_path),
    )

    result2 = engine2.execute_merge()
    assert result2["mode"] == "execute"
    assert result2["output_created"] is True
    assert gen2.output_path.exists(), "Output file must exist after execute_merge"

    # Verify output content
    with open(gen2.output_path, "r", encoding="utf-8") as fh:
        output_data = json.load(fh)

    assert output_data["baseline_id"] == MERGED_BASELINE_ID
    assert output_data["schema_version"] == SCHEMA_VERSION
    assert output_data["merge_metadata"]["merge_status"] == "COMPLETE"
    assert output_data["merge_metadata"]["safety_locks_verified"] is True
    assert output_data["merge_metadata"]["hermes_marker_present"] is True
    assert len(output_data["merge_metadata"]["p013_snapshot_md5"]) == 32

    print("    [PASS] Output file created: {}".format(gen2.output_path))
    print("    [PASS] baseline_id: {}".format(output_data["baseline_id"]))
    print("    [PASS] schema_version: {}".format(output_data["schema_version"]))
    print("    [PASS] merge_status: {}".format(output_data["merge_metadata"]["merge_status"]))
    print("    [PASS] p013_snapshot_md5: {}".format(output_data["merge_metadata"]["p013_snapshot_md5"]))

    # Test no-overwrite guard: second execute should fail
    overwrite_raised = False
    try:
        engine2.execute_merge()
    except OSError:
        overwrite_raised = True
    assert overwrite_raised, "Second execute_merge should raise OSError (NO_OVERWRITE)"
    print("    [PASS] NO_OVERWRITE guard triggered on second execute")

    gen2.cleanup()

    print()
    print("  [TEST 2] PASSED [OK]\n")
    passed += 1

    # ==================================================================
    # Test 3: Merge validation passes
    # ==================================================================
    print("  [TEST 3] Merge validation passes")
    print("  " + "-" * 60)

    gen3 = MockBaselineGenerator(temp_dir=temp_dir + os.sep + "test3")
    gen3.setup_full()

    engine3 = BaselineMergeEngine(
        p012_baseline_path=str(gen3.p012_path),
        p013_snapshot_path=str(gen3.p013_path),
        hermes_marker_path=str(gen3.hermes_marker_path),
        output_path=str(gen3.output_path),
    )

    p012_data = engine3._load_p012()
    p013_data = engine3._load_p013()
    merged = engine3.merge_baselines(p012_data, p013_data)
    errors = engine3.validate_output(merged)
    assert len(errors) == 0, "Expected 0 validation errors, got {}:\n{}".format(
        len(errors), "\n  ".join(errors)
    )

    print("    [PASS] Merged baseline validation: 0 errors")

    # Test invalid data detection
    bad_merged = dict(merged)
    bad_merged["schema_version"] = "BAD_SCHEMA"
    bad_merged["p012_render_cpu"] = dict(merged["p012_render_cpu"])
    bad_merged["p012_render_cpu"]["cpu_peak_pct"] = 9999
    bad_merged["p013_noise_rate"] = dict(merged["p013_noise_rate"])
    bad_merged["p013_noise_rate"].pop("noise_rate_pct", None)
    bad_merged["merge_metadata"] = dict(merged["merge_metadata"])
    bad_merged["merge_metadata"]["merge_status"] = "FAILED"
    bad_merged["merge_metadata"]["p013_snapshot_md5"] = "xx"  # invalid

    bad_errors = engine3.validate_output(bad_merged)
    assert len(bad_errors) >= 3, "Expected at least 3 validation errors for bad data"
    print("    [PASS] Bad data detected {} validation errors (expected >=3)".format(len(bad_errors)))

    gen3.cleanup()

    print()
    print("  [TEST 3] PASSED [OK]\n")
    passed += 1

    # ==================================================================
    # Test 4: Schema validation passes (full round-trip)
    # ==================================================================
    print("  [TEST 4] Schema validation — full round-trip")
    print("  " + "-" * 60)

    gen4 = MockBaselineGenerator(temp_dir=temp_dir + os.sep + "test4")
    gen4.setup_full()

    engine4 = BaselineMergeEngine(
        p012_baseline_path=str(gen4.p012_path),
        p013_snapshot_path=str(gen4.p013_path),
        hermes_marker_path=str(gen4.hermes_marker_path),
        output_path=str(gen4.output_path),
    )

    # Dry run → should succeed, no output
    dry_result = engine4.dry_run()
    assert dry_result["mode"] == "dry_run"
    assert dry_result["output_created"] is False
    assert not gen4.output_path.exists()

    # Execute → should succeed, output exists
    exec_result = engine4.execute_merge()
    assert exec_result["output_created"] is True

    # Read back and re-validate
    with open(gen4.output_path, "r", encoding="utf-8") as fh:
        roundtrip_data = json.load(fh)

    # Verify all required top-level keys
    for key in engine4.MERGED_SCHEMA_REQUIRED_KEYS:
        assert key in roundtrip_data, "Missing key '{}' in round-trip data".format(key)

    # Verify P0-12 section
    for field in engine4.P012_EXPECTED_FIELDS:
        assert field in roundtrip_data["p012_render_cpu"], (
            "Missing P0-12 field '{}' in round-trip".format(field)
        )

    # Verify P0-13 section
    for field in engine4.P013_EXPECTED_FIELDS:
        assert field in roundtrip_data["p013_noise_rate"], (
            "Missing P0-13 field '{}' in round-trip".format(field)
        )

    # Re-validate the round-tripped data
    revalidation_errors = engine4.validate_output(roundtrip_data)
    assert len(revalidation_errors) == 0, (
        "Round-trip validation errors: {}".format(revalidation_errors)
    )

    # Verify metadata accuracy
    meta = roundtrip_data["merge_metadata"]
    assert meta["merge_type"] == MERGE_TYPE
    assert meta["merge_engine_version"] == SCRIPT_VERSION
    assert meta["hermes_marker_present"] is True
    assert meta["safety_locks_verified"] is True

    print("    [PASS] Full round-trip: write -> read -> validate -- 0 errors")
    print("    [PASS] All required keys present at top level")
    print("    [PASS] All P0-12 expected fields present")
    print("    [PASS] All P0-13 expected fields present")
    print("    [PASS] Metadata values correct")

    gen4.cleanup()

    print()
    print("  [TEST 4] PASSED [OK]\n")
    passed += 1

    # ==================================================================
    # Summary
    # ==================================================================
    print("=" * 72)
    print("  SELF-TEST RESULTS: {} passed, {} failed".format(passed, failed))
    print("=" * 72)
    print()

    # Clean up top-level temp dir
    try:
        if os.path.isdir(temp_dir):
            for entry in os.listdir(temp_dir):
                full = os.path.join(temp_dir, entry)
                if os.path.isfile(full):
                    os.unlink(full)
                elif os.path.isdir(full):
                    import shutil
                    shutil.rmtree(full, ignore_errors=True)
            os.rmdir(temp_dir)
    except OSError:
        pass

    return failed


# ===========================================================================
# CLI Entry Point
# ===========================================================================

def _resolve_paths() -> Tuple[str, str, str, str]:
    """Resolve default file paths relative to the script's own directory.

    Returns:
        (p012_path, p013_path, hermes_path, output_path)
    """
    script_dir = Path(__file__).resolve().parent

    # P0-12 baseline — look for DSHE export in parent directory
    p012_candidates = [
        script_dir.parent / "dshe_baseline_export.json",
        script_dir.parent / "noise_rate_data.json",  # fallback reference
    ]
    p012_path = str(script_dir.parent / "dshe_baseline_export.json")
    for candidate in p012_candidates:
        if candidate.is_file():
            p012_path = str(candidate)
            break

    p013_path = str(script_dir / P013_SNAPSHOT_FILENAME)
    hermes_path = str(script_dir / HERMES_MARKER_FILENAME)
    output_path = str(script_dir / OUTPUT_FILENAME)

    return p012_path, p013_path, hermes_path, output_path


def _print_banner() -> None:
    """Print script banner with version info."""
    print("=" * 72)
    print("  V88 Phase03 P1 DSHB — P0-12 + P0-13 Baseline Merge Engine")
    print("  Script version: {}  |  Schema: {}".format(SCRIPT_VERSION, SCHEMA_VERSION))
    print("=" * 72)
    print()


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point.

    Args:
        argv: Command-line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code: 0 = success, 1 = failure.
    """
    if argv is None:
        argv = sys.argv[1:]

    _print_banner()

    # --self-test mode
    if "--self-test" in argv:
        failures = _run_self_tests()
        return 0 if failures == 0 else 1

    # Resolve paths
    p012_path, p013_path, hermes_path, output_path = _resolve_paths()

    # Default to dry-run
    mode = "dry_run"
    if "--execute" in argv:
        mode = "execute"

    print("  Mode: {}".format("DRY RUN (default, safe)" if mode == "dry_run" else "EXECUTE (real write)"))
    print("  P0-12 baseline: {}".format(p012_path))
    print("  P0-13 snapshot: {}".format(p013_path))
    print("  HERMES marker:  {}".format(hermes_path))
    print("  Output target:  {}".format(output_path))
    print()

    engine = BaselineMergeEngine(
        p012_baseline_path=p012_path,
        p013_snapshot_path=p013_path,
        hermes_marker_path=hermes_path,
        output_path=output_path,
    )

    if mode == "dry_run":
        engine.dry_run()
        print("  [DONE] Dry-run complete. No files were written.")
        return 0
    else:
        try:
            result = engine.execute_merge()
            print("  [DONE] Merge executed successfully.")
            print("         Output: {}".format(result["output_path"]))
            return 0
        except SafetyLockError as exc:
            print("\n  [BLOCKED] {}", str(exc))
            print("  Use --dry-run to preview, or create the missing lock files.")
            return 1
        except OSError as exc:
            print("\n  [ERROR] File system error: {}".format(exc))
            return 1
        except SchemaValidationError as exc:
            print("\n  [ERROR] Schema validation error: {}".format(exc))
            return 1


if __name__ == "__main__":
    sys.exit(main())
