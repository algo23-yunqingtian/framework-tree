#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
p81_safe_edit.py - P81 Toolchain Pre-modification Backup Hook
================================================================

Purpose
-------
Prevents silent loss of P81 generator / PS1 / patch / test / verify versions
when they are edited in place. Before any modification of a P81 toolchain file,
run this script to snapshot the current version with SHA256 metadata.

Token  : DSHD-P81-GIT-SAVE-TOKEN
Task   : DSHD-P81-GIT-SAVE
Version: v1.0.0

Subcommands
-----------
  snapshot <file>... [--agent LABEL] [--reason TEXT] [--ledger]
      Copy each file to _p81_snapshots/<name>.<YYYYMMDD_HHMMSS>.<agent>.bak
      and record SHA256/size/mtime to p81_version_history.json.

  restore  <file> --from SNAPSHOT_ID [--agent LABEL] [--reason TEXT] [--ledger]
      Restore <file> from a previous snapshot.  A pre-restore snapshot is
      taken first, so a failed restore is always recoverable.

  list     [<file>]
      List snapshot entries in p81_version_history.json (optionally filtered).

  check    <file>...
      Verify each file is in the P81_PROTECTED set and exists on disk.

  history  [<file>]
      Dump the full version history JSON.

  --version
      Print version string.

Design principles
-----------------
  1. Never modifies a file outside the P81_PROTECTED set.  Attempts to
     snapshot or restore an unlisted file are refused with exit code 2.
  2. Every snapshot/restore is recorded in p81_version_history.json with
     SHA256, size, mtime, agent label, reason, timestamp.
  3. Snapshot files live in _p81_snapshots/ (a gitignored sibling directory)
     and are named <name>.<YYYYMMDD_HHMMSS>.<agent>.bak so they are easy
     to discover and cannot pollute git status.
  4. --restore takes a defensive pre-restore snapshot before overwriting
     the target, so a failed restore is always recoverable.
  5. --ledger appends one event per subcommand to the shared audit ledger
     D:\\DSH_WORK\\github工作\\回测\\tracking_monitor_audit.jsonl.
  6. Fully offline.  wind_api_calls == 0.  No network, no wind, no Excel,
     no business CSV, no factor data, no backtest result access.

Red lines (P0)
--------------
  audit_only=YES  (read-only for the P81 monitoring loop)
  gate stays CLOSED/HOLD
  wind_api_calls = 0
  no kill of any non-P81 process
  no modification of business CSV, factor data, backtest results, or
  MANIFEST/skill artifacts
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCRIPT_VERSION = "v1.0.0"
TASK = "DSHD-P81-GIT-SAVE"
TOKEN = "DSHD-P81-GIT-SAVE-TOKEN"

# Root of the P81 toolchain (directory containing this file).
TOOLCHAIN_ROOT = Path(__file__).resolve().parent
HISTORY_PATH = TOOLCHAIN_ROOT / "p81_version_history.json"
SNAPSHOT_DIR = TOOLCHAIN_ROOT / "_p81_snapshots"
LEDGER_PATH = Path(r"D:\DSH_WORK\github工作\回测\tracking_monitor_audit.jsonl")

# Files guarded by this hook.  Paths are RELATIVE to TOOLCHAIN_ROOT.
# This is the authoritative list - the hook refuses to snapshot anything
# outside of it.
P81_PROTECTED = {
    # generator
    "recreate_p81.py",
    "recreate_p81.tweak_snapshot.py",
    # PS1 (active + snapshot)
    "dshd_p81_watch.ps1",
    "dshd_p81_watch.v1.2.0-TWEAK.ps1",
    # patch scripts
    "patch_p81_ext.py",
    "patch_p81_tweak.py",
    "patch_p81_brief.py",
    "patch_p81_fast_excel.py",
    # test scripts
    "test_p81_ext.ps1",
    "test_p81_tweak.ps1",
    # verify scripts
    "verify_p81_ext.ps1",
    "verify_p81_tweak_syntax.ps1",
    # the hook itself
    "p81_safe_edit.py",
    "p81_safe_edit.ps1",
    # version history ledger
    "p81_version_history.json",
}


def _tz():
    return timezone(timedelta(hours=8))


def _now_iso():
    return datetime.now(_tz()).strftime("%Y-%m-%dT%H:%M:%S%z")


def _now_stamp():
    return datetime.now(_tz()).strftime("%Y%m%d_%H%M%S")


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _mtime_iso(path):
    return datetime.fromtimestamp(path.stat().st_mtime, tz=_tz()).strftime(
        "%Y-%m-%dT%H:%M:%S%z"
    )


def resolve_target(file_arg):
    """Resolve a user-supplied file argument to an absolute Path.

    Returns (abs_path, relative_name_in_history).
    Raises ValueError if the file is not in the P81_PROTECTED list.
    """
    p = Path(file_arg)
    if not p.is_absolute():
        p = (TOOLCHAIN_ROOT / file_arg).resolve()
    else:
        p = p.resolve()
    if not p.exists() and p.parent == TOOLCHAIN_ROOT.resolve():
        # Allow snapshotting by name even if the file is being created.
        if p.name in P81_PROTECTED:
            return p, p.name
        raise ValueError(
            "file '%s' is not in the P81_PROTECTED list. Refusing. "
            "Protected names: %s" % (p.name, sorted(P81_PROTECTED))
        )
    if p.parent != TOOLCHAIN_ROOT.resolve():
        raise ValueError(
            "file is not under the P81 toolchain root %s: %s"
            % (TOOLCHAIN_ROOT, p)
        )
    if p.name not in P81_PROTECTED:
        raise ValueError(
            "file '%s' is not in the P81_PROTECTED list. Refusing. "
            "Protected names: %s" % (p.name, sorted(P81_PROTECTED))
        )
    return p, p.name


def read_history():
    if not HISTORY_PATH.exists():
        return {
            "_meta": {
                "created_at": _now_iso(),
                "script_version": SCRIPT_VERSION,
                "task": TASK,
                "token": TOKEN,
                "protected_files": sorted(P81_PROTECTED),
                "snapshot_dir": str(SNAPSHOT_DIR),
            },
            "entries": [],
        }
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def write_history(h):
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = HISTORY_PATH.with_suffix(HISTORY_PATH.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=2)
    os.replace(tmp, HISTORY_PATH)


def append_ledger(event_obj):
    if not LEDGER_PATH.parent.exists():
        LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event_obj, ensure_ascii=False) + "\n")


def _make_snapshot(abs_path, rel_name, action, agent, reason):
    """Create a .bak copy under _p81_snapshots/ and return the entry dict."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = _now_stamp()
    agent_tag = re.sub(r"[^A-Za-z0-9_\-]", "_", agent) if agent else "UNKNOWN"
    snap_id = "%s.%s.%s" % (abs_path.stem, stamp, agent_tag)
    snap_path = SNAPSHOT_DIR / (snap_id + ".bak")
    if snap_path.exists():
        snap_id = "%s.%d" % (snap_id, os.getpid())
        snap_path = SNAPSHOT_DIR / (snap_id + ".bak")
    shutil.copy2(abs_path, snap_path)
    return {
        "snapshot_id": snap_id,
        "file": rel_name,
        "action": action,
        "agent": agent,
        "reason": reason or "",
        "timestamp": _now_iso(),
        "script_version": SCRIPT_VERSION,
        "task": TASK,
        "token": TOKEN,
        "pre_edit": {
            "sha256": _sha256_file(abs_path),
            "size_bytes": abs_path.stat().st_size,
            "mtime": _mtime_iso(abs_path),
        },
        "snapshot_file": str(snap_path),
        "snapshot_sha256": _sha256_file(snap_path),
        "snapshot_size_bytes": snap_path.stat().st_size,
        "toolchain_root": str(TOOLCHAIN_ROOT),
    }


def cmd_snapshot(args):
    history = read_history()
    results = []
    failures = []
    for file_arg in args.files:
        try:
            abs_path, rel_name = resolve_target(file_arg)
        except ValueError as e:
            failures.append({"file": file_arg, "error": str(e)})
            continue
        if not abs_path.exists():
            failures.append({"file": rel_name, "error": "file not found",
                             "abs_path": str(abs_path)})
            continue
        entry = _make_snapshot(
            abs_path, rel_name, "PRE_EDIT_SNAPSHOT", args.agent, args.reason
        )
        history["entries"].append(entry)
        results.append({
            "snapshot_id": entry["snapshot_id"],
            "snapshot_file": entry["snapshot_file"],
            "pre_sha256": entry["pre_edit"]["sha256"],
            "snapshot_sha256": entry["snapshot_sha256"],
            "size_bytes": entry["pre_edit"]["size_bytes"],
        })
        if args.ledger:
            append_ledger({
                "timestamp": entry["timestamp"],
                "event": "P81-PRE-EDIT-SNAPSHOT",
                "agent": args.agent,
                "task": TASK,
                "token": TOKEN,
                "file": rel_name,
                "snapshot_id": entry["snapshot_id"],
                "snapshot_file": entry["snapshot_file"],
                "pre_sha256": entry["pre_edit"]["sha256"],
                "pre_size_bytes": entry["pre_edit"]["size_bytes"],
                "snapshot_sha256": entry["snapshot_sha256"],
                "intervention": "NONE",
                "note": args.reason or "",
            })
    write_history(history)
    payload = {
        "ok": True,
        "count": len(results),
        "failures": failures,
        "results": results,
        "history_path": str(HISTORY_PATH),
        "task": TASK,
        "token": TOKEN,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


def cmd_restore(args):
    history = read_history()
    try:
        abs_path, rel_name = resolve_target(args.file)
    except ValueError as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False, indent=2))
        return 2
    matches = [
        e for e in history["entries"]
        if e.get("snapshot_id") == args.from_snapshot and e.get("file") == rel_name
    ]
    if not matches:
        print(json.dumps({
            "ok": False,
            "error": "snapshot_id '%s' not found for file '%s'"
                     % (args.from_snapshot, rel_name),
        }, ensure_ascii=False, indent=2))
        return 2
    entry = matches[-1]
    snap_path = Path(entry["snapshot_file"])
    if not snap_path.exists():
        print(json.dumps({
            "ok": False,
            "error": "snapshot file missing on disk: %s" % snap_path,
        }, ensure_ascii=False, indent=2))
        return 2

    # Defensive pre-restore snapshot.
    pre_restore_id = None
    if abs_path.exists():
        try:
            pre_entry = _make_snapshot(
                abs_path,
                rel_name,
                "PRE_RESTORE_SNAPSHOT",
                args.agent,
                "auto-snapshot before restore from %s; %s"
                % (args.from_snapshot, args.reason or ""),
            )
            history["entries"].append(pre_entry)
            pre_restore_id = pre_entry["snapshot_id"]
        except Exception as e:
            print(json.dumps({
                "ok": False,
                "error": "failed to take pre-restore snapshot: %s" % e,
            }, ensure_ascii=False, indent=2))
            return 2

    shutil.copy2(snap_path, abs_path)
    new_sha = _sha256_file(abs_path)
    restore_entry = {
        "snapshot_id": "restore.%s.%s" % (_now_stamp(),
                                          re.sub(r"[^A-Za-z0-9_\-]", "_", args.agent)),
        "file": rel_name,
        "action": "RESTORE",
        "agent": args.agent,
        "reason": args.reason or "",
        "timestamp": _now_iso(),
        "script_version": SCRIPT_VERSION,
        "task": TASK,
        "token": TOKEN,
        "restored_from_snapshot": args.from_snapshot,
        "restored_from_snapshot_file": str(snap_path),
        "expected_sha256": _sha256_file(snap_path),
        "actual_sha256_after_restore": new_sha,
        "size_bytes": abs_path.stat().st_size,
        "matched": _sha256_file(snap_path) == new_sha,
        "pre_restore_snapshot_id": pre_restore_id,
    }
    history["entries"].append(restore_entry)
    write_history(history)
    if args.ledger:
        append_ledger({
            "timestamp": restore_entry["timestamp"],
            "event": "P81-RESTORE",
            "agent": args.agent,
            "task": TASK,
            "token": TOKEN,
            "file": rel_name,
            "restored_from": args.from_snapshot,
            "expected_sha256": restore_entry["expected_sha256"],
            "actual_sha256": new_sha,
            "matched": restore_entry["matched"],
            "intervention": "NONE",
            "note": args.reason or "",
        })
    print(json.dumps({
        "ok": True,
        "restored": rel_name,
        "from_snapshot": args.from_snapshot,
        "expected_sha256": restore_entry["expected_sha256"],
        "actual_sha256": new_sha,
        "matched": restore_entry["matched"],
        "pre_restore_snapshot": pre_restore_id,
        "history_path": str(HISTORY_PATH),
    }, ensure_ascii=False, indent=2))
    return 0 if restore_entry["matched"] else 3


def cmd_list(args):
    history = read_history()
    entries = history["entries"]
    if args.file:
        _, rel_name = resolve_target(args.file)
        entries = [e for e in entries if e.get("file") == rel_name]
    print(json.dumps({
        "ok": True,
        "count": len(entries),
        "entries": entries,
        "history_path": str(HISTORY_PATH),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_check(args):
    rc = 0
    for f in args.files:
        try:
            abs_path, rel_name = resolve_target(f)
        except ValueError as e:
            print(json.dumps({"file": f, "ok": False, "error": str(e)},
                             ensure_ascii=False))
            rc = 2
            continue
        exists = abs_path.exists()
        rec = {"file": rel_name, "ok": True, "exists": exists,
               "abs_path": str(abs_path),
               "protected": True}
        if exists:
            rec["sha256"] = _sha256_file(abs_path)
            rec["size_bytes"] = abs_path.stat().st_size
            rec["mtime"] = _mtime_iso(abs_path)
        print(json.dumps(rec, ensure_ascii=False))
    return rc


def cmd_history(args):
    history = read_history()
    entries = history["entries"]
    if args.file:
        _, rel_name = resolve_target(args.file)
        entries = [e for e in entries if e.get("file") == rel_name]
    print(json.dumps({
        "ok": True,
        "count": len(entries),
        "meta": history.get("_meta"),
        "entries": entries,
    }, ensure_ascii=False, indent=2))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="P81 toolchain pre-modification backup hook",
        epilog="version %s; task %s; token %s" % (SCRIPT_VERSION, TASK, TOKEN),
    )
    parser.add_argument("--version", action="version",
                        version="%s (%s)" % (SCRIPT_VERSION, TASK))
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("snapshot",
                       help="snapshot one or more protected P81 files before editing")
    p.add_argument("files", nargs="+")
    p.add_argument("--agent", default="DSHD-P81", help="agent label")
    p.add_argument("--reason", default="", help="free-form reason")
    p.add_argument("--ledger", action="store_true",
                   help="also append to tracking_monitor_audit.jsonl")
    p.set_defaults(func=cmd_snapshot)

    p = sub.add_parser("restore",
                       help="restore a protected P81 file from a previous snapshot")
    p.add_argument("file")
    p.add_argument("--from", dest="from_snapshot", required=True,
                   help="snapshot_id to restore from")
    p.add_argument("--agent", default="DSHD-P81")
    p.add_argument("--reason", default="")
    p.add_argument("--ledger", action="store_true")
    p.set_defaults(func=cmd_restore)

    p = sub.add_parser("list",
                       help="list snapshot entries (optionally filtered by file)")
    p.add_argument("file", nargs="?", default=None)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("check",
                       help="verify one or more files are in the protected set")
    p.add_argument("files", nargs="+")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("history",
                       help="dump the full version history")
    p.add_argument("file", nargs="?", default=None)
    p.set_defaults(func=cmd_history)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
