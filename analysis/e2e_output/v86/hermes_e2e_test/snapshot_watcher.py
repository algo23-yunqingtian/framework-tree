#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DSHE V86-RC2 Bridge Snapshot Watcher
Task: DSHE_V86_RC2_PROD_PHASE_DEP_WATCHER / T3.1

Function:
  - Polls remote repository for DSHB bridge snapshot file updates
  - Auto MD5 verification on file change detection
  - Local version caching with historical snapshot diffing
  - Alert on MD5 mismatch (integrity failure)
  - Auto-trigger dep_recovery_auto_verify.py when data_fetchable=TRUE detected

Usage:
  python3 snapshot_watcher.py                    # Interactive mode (auto-reload config)
  python3 snapshot_watcher.py --config watcher_config.yaml  # Custom config
  python3 snapshot_watcher.py --once             # Single poll cycle then exit
  python3 snapshot_watcher.py --check            # Quick health check

Author: DSHE V86-RC2 PROD PHASE DEP WATCHER
Branch: feature/v85-chart-template
Date: 2026-10-15
"""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "watcher_config.yaml"
LOCAL_CACHE_DIR = SCRIPT_DIR / ".snapshot_cache"
CACHE_META_FILE = LOCAL_CACHE_DIR / "snapshot_cache_meta.json"

# Default snapshot file paths (repo-relative)
DEFAULT_SNAPSHOT_PATHS = [
    "analysis/e2e_output/v86/hermes_e2e_test/v86_rc2_dshb_bridge_snapshot_for_dshe.json",
    "analysis/e2e_output/v86/dshb_gate_prod_fix/v86_rc2_dshb_bridge_snapshot_for_dshe.json",
]

DEFAULT_REPO_ROOT = "D:/DSH_WORK/framework-tree"
DEFAULT_POLL_INTERVAL = 300  # 5 minutes
DEFAULT_INITIAL_MD5 = "41856E22398A8DE70F561F62A33D3DA4"

# ─────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────
def setup_logging(level=logging.INFO):
    """Configure logging to both console and log file."""
    LOG_DIR = SCRIPT_DIR / ".logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "snapshot_watcher.log"

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    logger = logging.getLogger("snapshot_watcher")
    logger.setLevel(level)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

# ─────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────
def load_config(config_path=None):
    """Load watcher configuration from YAML file."""
    config_path = config_path or CONFIG_PATH

    defaults = {
        "snapshot_paths": DEFAULT_SNAPSHOT_PATHS,
        "repo_root": DEFAULT_REPO_ROOT,
        "poll_interval_seconds": DEFAULT_POLL_INTERVAL,
        "initial_md5": DEFAULT_INITIAL_MD5,
        "enable_recovery_verify": True,
        "recovery_verify_script": "dep_recovery_auto_verify.py",
        "notify_channels": ["console", "log"],
        "max_cache_versions": 50,
        "md5_mismatch_alert": True,
        "auto_fetch_remote": True,
        "git_remote": "origin",
    }

    if not config_path.exists():
        logging.info(f"[CONFIG] Config file not found: {config_path}")
        logging.info(f"[CONFIG] Using defaults")
        # Create default config
        if HAS_YAML:
            save_default_config(config_path, defaults)
        return defaults

    if HAS_YAML:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if loaded:
                    defaults.update(loaded)
                    logging.info(f"[CONFIG] Loaded config from: {config_path}")
        except Exception as e:
            logging.warning(f"[CONFIG] Failed to load config: {e}")
            logging.info(f"[CONFIG] Using defaults")
    else:
        logging.warning("[CONFIG] PyYAML not available, using defaults")

    return defaults


def save_default_config(config_path, defaults):
    """Save default configuration to YAML file."""
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("# DSHE V86-RC2 Snapshot Watcher Configuration\n")
            f.write("# Task: DSHE_V86_RC2_PROD_PHASE_DEP_WATCHER / T3.1\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            for key, value in defaults.items():
                if isinstance(value, list):
                    f.write(f"{key}:\n")
                    for item in value:
                        f.write(f"  - {item}\n")
                elif isinstance(value, bool):
                    f.write(f"{key}: {str(value).lower()}\n")
                elif isinstance(value, int):
                    f.write(f"{key}: {value}\n")
                else:
                    f.write(f'{key}: "{value}"\n')
        logging.info(f"[CONFIG] Default config saved to: {config_path}")
    except Exception as e:
        logging.warning(f"[CONFIG] Failed to save config: {e}")

# ─────────────────────────────────────────────────────────────────────
# Core Functions
# ─────────────────────────────────────────────────────────────────────
def compute_file_md5(file_path):
    """Compute MD5 hash of a file."""
    md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                md5.update(chunk)
        return md5.hexdigest().upper()
    except Exception as e:
        logging.error(f"[MD5] Failed to compute MD5 for {file_path}: {e}")
        return None


def find_snapshot_file(config):
    """Find the latest bridge snapshot file from configured paths."""
    repo_root = Path(config.get("repo_root", DEFAULT_REPO_ROOT))
    snapshot_paths = config.get("snapshot_paths", DEFAULT_SNAPSHOT_PATHS)

    found = []
    for rel_path in snapshot_paths:
        abs_path = repo_root / rel_path
        if abs_path.exists():
            md5 = compute_file_md5(abs_path)
            size = abs_path.stat().st_size
            mtime = datetime.fromtimestamp(
                abs_path.stat().st_mtime, tz=timezone.utc
            ).isoformat()
            found.append({
                "path": str(abs_path),
                "rel_path": rel_path,
                "md5": md5,
                "size": size,
                "mtime": mtime,
            })

    if not found:
        logging.warning("[FIND] No snapshot file found at any configured path")
        return None

    # Return the most recent one
    found.sort(key=lambda x: x["mtime"], reverse=True)
    logging.info(f"[FIND] Found {len(found)} snapshot file(s), using most recent")
    return found[0]


def git_fetch(config):
    """Fetch latest from remote repository."""
    if not config.get("auto_fetch_remote", True):
        logging.info("[GIT] Auto-fetch disabled, skipping")
        return True

    repo_root = config.get("repo_root", DEFAULT_REPO_ROOT)
    remote = config.get("git_remote", "origin")
    branch = "feature/v85-chart-template"

    try:
        result = subprocess.run(
            ["git", "fetch", remote, branch],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            logging.info(f"[GIT] Fetch successful: {remote}/{branch}")
            return True
        else:
            logging.warning(f"[GIT] Fetch failed: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        logging.warning("[GIT] git command not found")
        return False
    except subprocess.TimeoutExpired:
        logging.warning("[GIT] Fetch timed out")
        return False
    except Exception as e:
        logging.warning(f"[GIT] Fetch error: {e}")
        return False


def git_pull(config):
    """Pull latest changes from remote."""
    repo_root = config.get("repo_root", DEFAULT_REPO_ROOT)
    remote = config.get("git_remote", "origin")
    branch = "feature/v85-chart-template"

    try:
        result = subprocess.run(
            ["git", "pull", "--rebase", remote, branch],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            logging.info(f"[GIT] Pull successful: {remote}/{branch}")
            return True
        else:
            logging.warning(f"[GIT] Pull failed: {result.stderr.strip()}")
            # Try fetch first
            git_fetch(config)
            result2 = subprocess.run(
                ["git", "pull", "--rebase", remote, branch],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return result2.returncode == 0
    except Exception as e:
        logging.warning(f"[GIT] Pull error: {e}")
        return False


def load_snapshot_data(snapshot_info):
    """Load and parse the bridge snapshot JSON data."""
    path = snapshot_info["path"]
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate structure
        if "_meta" not in data or "snapshot_data" not in data:
            logging.error(f"[LOAD] Invalid snapshot structure in {path}")
            return None

        meta = data["_meta"]
        entries = data["snapshot_data"]

        logging.info(
            f"[LOAD] Snapshot loaded: {meta.get('snapshot_id', 'N/A')}, "
            f"{len(entries)} entries, "
            f"ALL_FALSE={meta.get('data_fetchable_ALL_FALSE', 'N/A')}"
        )

        return {
            "meta": meta,
            "entries": entries,
            "total": len(entries),
            "true_count": sum(1 for e in entries if e.get("data_fetchable") is True),
            "false_count": sum(1 for e in entries if e.get("data_fetchable") is False),
        }
    except json.JSONDecodeError as e:
        logging.error(f"[LOAD] JSON parse error: {e}")
        return None
    except Exception as e:
        logging.error(f"[LOAD] Load error: {e}")
        return None


def check_for_recovery(snapshot_data):
    """Check if any data_fetchable=TRUE entries exist (dependency recovery)."""
    if snapshot_data is None:
        logging.warning("[RECOVERY] No snapshot data to check")
        return None

    true_count = snapshot_data["true_count"]
    total = snapshot_data["total"]

    if true_count > 0:
        logging.warning(
            f"[RECOVERY] *** DEPENDENCY RECOVERY DETECTED *** "
            f"{true_count}/{total} entries now data_fetchable=TRUE"
        )
        recovered = [
            e for e in snapshot_data["entries"]
            if e.get("data_fetchable") is True
        ]
        # Sample first 10 for logging
        sample = recovered[:10]
        for entry in sample:
            logging.info(
                f"[RECOVERY]   {entry.get('indicator_id', '?')}: "
                f"{entry.get('display_name', '?')} "
                f"(product={entry.get('product', '?')})"
            )
        if len(recovered) > 10:
            logging.info(f"[RECOVERY]   ... and {len(recovered) - 10} more")

        return {
            "recovered": True,
            "true_count": true_count,
            "total": total,
            "entries": recovered,
        }
    else:
        logging.info(
            f"[RECOVERY] No recovery detected: "
            f"{true_count}/{total} entries data_fetchable=TRUE"
        )
        return {
            "recovered": False,
            "true_count": true_count,
            "total": total,
        }


def cache_snapshot(snapshot_info, snapshot_data):
    """Cache the current snapshot locally for historical comparison."""
    LOCAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Create versioned cache file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cache_file = LOCAL_CACHE_DIR / f"snapshot_{timestamp}.json"

    try:
        with open(snapshot_info["path"], "rb") as src, \
             open(cache_file, "wb") as dst:
            shutil.copyfileobj(src, dst)
        logging.info(f"[CACHE] Snapshot cached: {cache_file.name}")
    except Exception as e:
        logging.error(f"[CACHE] Failed to cache snapshot: {e}")
        return None

    # Update cache metadata
    meta = {
        "cached_at": timestamp,
        "source_path": snapshot_info["path"],
        "md5": snapshot_info["md5"],
        "size": snapshot_info["size"],
        "mtime": snapshot_info["mtime"],
        "total_entries": snapshot_data["total"] if snapshot_data else None,
        "true_count": snapshot_data["true_count"] if snapshot_data else None,
    }

    cache_meta = {}
    if CACHE_META_FILE.exists():
        try:
            with open(CACHE_META_FILE, "r", encoding="utf-8") as f:
                cache_meta = json.load(f)
        except Exception:
            cache_meta = {}

    cache_meta[timestamp] = meta

    # Prune old versions beyond max_cache_versions
    max_versions = config.get("max_cache_versions", 50)
    if len(cache_meta) > max_versions:
        sorted_keys = sorted(cache_meta.keys())
        excess = len(cache_meta) - max_versions
        for k in sorted_keys[:excess]:
            del cache_meta[k]
            old_file = LOCAL_CACHE_DIR / f"snapshot_{k}.json"
            if old_file.exists():
                old_file.unlink()
            logging.info(f"[CACHE] Pruned old version: {k}")

    with open(CACHE_META_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_meta, f, indent=2, ensure_ascii=False)

    logging.info(f"[CACHE] Cache metadata updated: {len(cache_meta)} versions")
    return cache_file


def diff_snapshots(current, previous):
    """Compare current snapshot with previous cached version."""
    if previous is None:
        logging.info("[DIFF] No previous snapshot for comparison")
        return {"changed": False, "reason": "no_previous"}

    changes = {
        "md5_changed": current["md5"] != previous["md5"],
        "size_changed": current["size"] != previous["size"],
        "entries_changed": False,
        "fields_changed": [],
        "new_true_entries": [],
        "false_to_true": [],
    }

    if not changes["md5_changed"]:
        logging.info("[DIFF] No changes detected (MD5 match)")
        return {"changed": False}

    logging.info(
        f"[DIFF] Changes detected: "
        f"MD5 {previous['md5'][:8]}... -> {current['md5'][:8]}..., "
        f"Size {previous['size']} -> {current['size']}"
    )

    return {"changed": True, **changes}


def run_recovery_verify(config, recovery_info):
    """Auto-trigger dependency recovery verification script."""
    if not config.get("enable_recovery_verify", True):
        logging.info("[VERIFY] Auto-verify disabled, skipping")
        return False

    script_path = SCRIPT_DIR / config.get(
        "recovery_verify_script", "dep_recovery_auto_verify.py"
    )

    if not script_path.exists():
        logging.warning(f"[VERIFY] Recovery verify script not found: {script_path}")
        return False

    logging.info(
        f"[VERIFY] Auto-triggering recovery verification: "
        f"{script_path.name}"
    )

    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "--auto",
             "--true-count", str(recovery_info["true_count"]),
             "--total", str(recovery_info["total"])],
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            logging.info(f"[VERIFY] Recovery verify completed successfully")
            if result.stdout:
                logging.info(f"[VERIFY] Output: {result.stdout[:500]}")
            return True
        else:
            logging.error(f"[VERIFY] Recovery verify failed: {result.stderr[:500]}")
            return False
    except subprocess.TimeoutExpired:
        logging.error("[VERIFY] Recovery verify timed out (300s)")
        return False
    except Exception as e:
        logging.error(f"[VERIFY] Recovery verify error: {e}")
        return False


def send_alert(config, level, message):
    """Send alert notification via configured channels."""
    alert_text = f"[{level.upper()}] {message}"

    if level == "CRITICAL":
        logging.critical(alert_text)
    elif level == "WARNING":
        logging.warning(alert_text)
    else:
        logging.info(alert_text)

    # Notify channels
    channels = config.get("notify_channels", ["console", "log"])

    # Console alert
    if "console" in channels and level in ("WARNING", "CRITICAL"):
        print(f"\n{'='*60}")
        print(f"  {alert_text}")
        print(f"{'='*60}\n")

    # Log alert
    if "log" in channels:
        LOG_DIR = SCRIPT_DIR / ".logs"
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        alert_file = LOG_DIR / "alerts.log"
        with open(alert_file, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | {level} | {message}\n")


def quick_health_check(config):
    """Perform a quick health check without waiting for poll cycle."""
    logging.info("=" * 60)
    logging.info("DSHE V86-RC2 Snapshot Watcher - HEALTH CHECK")
    logging.info("=" * 60)

    # 1. Check config
    logging.info(f"[CHECK 1/6] Configuration loaded from: {config_path}")
    config_source = "defaults" if not CONFIG_PATH.exists() else "file"
    logging.info(f"           Config source: {config_source}")
    logging.info(f"           Poll interval: {config['poll_interval_seconds']}s")
    logging.info(f"           Recovery verify: {config['enable_recovery_verify']}")
    logging.info(f"           Snapshot paths: {len(config['snapshot_paths'])}")

    # 2. Check repo access
    repo_root = Path(config["repo_root"])
    if repo_root.exists():
        logging.info(f"[CHECK 2/6] Repository accessible: {repo_root}")
    else:
        logging.warning(f"[CHECK 2/6] Repository NOT accessible: {repo_root}")

    # 3. Check snapshot files
    snapshot = find_snapshot_file(config)
    if snapshot:
        logging.info(f"[CHECK 3/6] Snapshot file found: {snapshot['rel_path']}")
        logging.info(f"           MD5: {snapshot['md5']}")
        logging.info(f"           Size: {snapshot['size']:,} B")
        logging.info(f"           Modified: {snapshot['mtime']}")
    else:
        logging.warning(f"[CHECK 3/6] No snapshot file found")

    # 4. Check snapshot data
    if snapshot:
        data = load_snapshot_data(snapshot)
        if data:
            logging.info(f"[CHECK 4/6] Snapshot data valid")
            logging.info(f"           Total entries: {data['total']}")
            logging.info(f"           data_fetchable=TRUE: {data['true_count']}")
            logging.info(f"           data_fetchable=FALSE: {data['false_count']}")

            recovery = check_for_recovery(data)
            if recovery and recovery.get("recovered"):
                logging.warning(
                    f"[CHECK 4/6] *** DEPENDENCY RECOVERY DETECTED ***"
                )
            else:
                logging.info(
                    f"[CHECK 4/6] Dependency recovery status: NOT RECOVERED"
                )
        else:
            logging.error(f"[CHECK 4/6] Snapshot data INVALID")

    # 5. Check cache
    if LOCAL_CACHE_DIR.exists():
        cache_files = list(LOCAL_CACHE_DIR.glob("snapshot_*.json"))
        logging.info(f"[CHECK 5/6] Local cache: {len(cache_files)} versions")
        if CACHE_META_FILE.exists():
            logging.info(f"           Cache metadata: {CACHE_META_FILE}")
    else:
        logging.info(f"[CHECK 5/6] Local cache: empty")

    # 6. Check recovery verify script
    verify_script = SCRIPT_DIR / config.get(
        "recovery_verify_script", "dep_recovery_auto_verify.py"
    )
    if verify_script.exists():
        logging.info(f"[CHECK 6/6] Recovery verify script: AVAILABLE")
    else:
        logging.warning(f"[CHECK 6/6] Recovery verify script: NOT FOUND")

    logging.info("=" * 60)
    logging.info("HEALTH CHECK COMPLETE")
    logging.info("=" * 60)


# ─────────────────────────────────────────────────────────────────────
# Main Polling Loop
# ─────────────────────────────────────────────────────────────────────
def poll_cycle(config, initial_md5=None):
    """Execute one polling cycle: fetch, find, verify, cache, diff."""
    cycle_start = time.time()
    logging.info("-" * 50)
    logging.info("[CYCLE] Starting poll cycle")

    # Step 1: Git fetch/pull
    if config.get("auto_fetch_remote", True):
        git_pull(config)

    # Step 2: Find snapshot file
    snapshot_info = find_snapshot_file(config)
    if not snapshot_info:
        logging.warning("[CYCLE] No snapshot found, skipping")
        return {"found": False}

    current_md5 = snapshot_info["md5"]
    logging.info(f"[CYCLE] Snapshot MD5: {current_md5}")
    logging.info(f"[CYCLE] Snapshot path: {snapshot_info['rel_path']}")

    # Step 3: MD5 integrity check
    initial_md5 = initial_md5 or config.get("initial_md5", DEFAULT_INITIAL_MD5)
    if current_md5 != initial_md5 and initial_md5:
        logging.info(
            f"[CYCLE] MD5 changed since baseline: "
            f"baseline={initial_md5[:8]}... current={current_md5[:8]}..."
        )

    # Check for MD5 mismatch alerts (config-driven)
    if config.get("md5_mismatch_alert", True) and current_md5 != initial_md5:
        send_alert(
            config, "WARNING",
            f"Snapshot MD5 changed from baseline. "
            f"Baseline: {initial_md5}, Current: {current_md5}"
        )

    # Step 4: Load snapshot data
    snapshot_data = load_snapshot_data(snapshot_info)
    if not snapshot_data:
        logging.error("[CYCLE] Failed to load snapshot data")
        return {"found": True, "data_valid": False}

    # Step 5: Check for dependency recovery
    recovery_info = check_for_recovery(snapshot_data)
    recovery_detected = recovery_info.get("recovered", False) if recovery_info else False

    # Step 6: Cache snapshot
    cache_file = cache_snapshot(snapshot_info, snapshot_data)

    # Step 7: Diff with previous version
    previous_info = get_latest_cached_version()
    diff_result = diff_snapshots(snapshot_info, previous_info)

    # Step 8: Auto-trigger recovery verification
    if recovery_detected and recovery_info:
        logging.warning(
            f"[CYCLE] *** DEPENDENCY RECOVERY DETECTED *** "
            f"({recovery_info['true_count']}/{recovery_info['total']})"
        )
        send_alert(
            config, "WARNING",
            f"DEPENDENCY RECOVERY: {recovery_info['true_count']}/{recovery_info['total']} "
            f"entries now data_fetchable=TRUE"
        )
        run_recovery_verify(config, recovery_info)

    cycle_duration = time.time() - cycle_start
    logging.info(
        f"[CYCLE] Poll cycle complete in {cycle_duration:.1f}s "
        f"(recovery={'YES' if recovery_detected else 'no'}, "
        f"changes={'YES' if diff_result.get('changed') else 'no'})"
    )

    return {
        "found": True,
        "data_valid": True,
        "md5": current_md5,
        "recovery_detected": recovery_detected,
        "changes_detected": diff_result.get("changed", False),
    }


def get_latest_cached_version():
    """Get the most recent cached snapshot version."""
    if not CACHE_META_FILE.exists():
        return None

    try:
        with open(CACHE_META_FILE, "r", encoding="utf-8") as f:
            meta = json.load(f)
        if not meta:
            return None

        latest_key = max(meta.keys())
        return meta[latest_key]
    except Exception:
        return None


def main():
    """Main entry point for snapshot watcher."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DSHE V86-RC2 Bridge Snapshot Watcher"
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to watcher_config.yaml"
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Run a single poll cycle and exit"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Run quick health check and exit"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(log_level)

    # Load config
    config = load_config(args.config)

    # Health check mode
    if args.check:
        quick_health_check(config)
        return

    # Banner
    logger.info("=" * 60)
    logger.info("DSHE V86-RC2 Bridge Snapshot Watcher")
    logger.info(f"Task: DSHE_V86_RC2_PROD_PHASE_DEP_WATCHER / T3.1")
    logger.info(f"Branch: feature/v85-chart-template")
    logger.info(f"Started: {datetime.now().isoformat()}")
    logger.info(f"Config: poll={config['poll_interval_seconds']}s, "
                f"recovery_verify={config['enable_recovery_verify']}")
    logger.info("=" * 60)

    # Run
    if args.once:
        result = poll_cycle(config)
        logger.info(f"Single cycle result: {result}")
        return

    # Continuous polling loop
    logger.info("[MAIN] Entering continuous polling loop (Ctrl+C to stop)")

    try:
        cycle_count = 0
        while True:
            cycle_count += 1
            logger.info(f"\n[MAIN] === Poll Cycle #{cycle_count} ===")
            try:
                poll_cycle(config)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error(f"[MAIN] Cycle error: {e}")

            # Wait for next cycle
            logger.info(
                f"[MAIN] Next cycle in {config['poll_interval_seconds']}s"
            )
            time.sleep(config["poll_interval_seconds"])

    except KeyboardInterrupt:
        logger.info("\n[MAIN] Interrupted by user")
        logger.info(f"[MAIN] Total cycles completed: {cycle_count}")
        logger.info("[MAIN] Snapshot Watcher stopped")


if __name__ == "__main__":
    main()
