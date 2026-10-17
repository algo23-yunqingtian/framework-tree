#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
workspace_audit_hook.py — Read-only audit collection for factor workspace

TASK_ID: V88_PHASE03_P7_DSHB_P019_FACTOR_CALIB_ALIGNMENT
TASK: T1 — Audit hook deployment
AGENT: DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)

SAFETY: This script is READ-ONLY. It never modifies any file in the workspace.
        It only reads file content to compute hashes and writes audit logs to audit/.
        No git push, no API calls, no factor computation.
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_DIR = os.path.join(WORKSPACE, 'audit')
REPO_ROOT = os.path.abspath(os.path.join(WORKSPACE, '..', '..'))

TARGET_FILES = [
    'ic_ir_calc_skeleton.py',
    'ic_ir_calc_skeleton.py.md5',
    'input/',
    'output/',
    'audit/',
    'checksum/',
]

EXTERNAL_FILES = [
    ('opt_trigger/wind_online_watcher.py', os.path.join(REPO_ROOT, 'opt_trigger', 'wind_online_watcher.py')),
    ('opt_trigger/wind_online_watcher.py.md5', os.path.join(REPO_ROOT, 'opt_trigger', 'wind_online_watcher.py.md5')),
]


def compute_hashes(filepath):
    """Compute MD5, SHA256, and git blob SHA1 for a file."""
    with open(filepath, 'rb') as f:
        data = f.read()

    md5 = hashlib.md5(data).hexdigest().upper()
    sha256 = hashlib.sha256(data).hexdigest()

    # Git blob hash (SHA1 of "blob <size>\0<content>")
    blob_header = f'blob {len(data)}\0'.encode('utf-8')
    blob_sha1 = hashlib.sha1(blob_header + data).hexdigest()

    return md5, sha256, blob_sha1


def collect_file(filepath, relpath):
    """Collect metadata for a single file."""
    result = {
        'filename': relpath,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }

    if not os.path.exists(filepath):
        result['status'] = 'NOT_FOUND'
        return result

    try:
        stat = os.stat(filepath)
        size = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

        if size == 0:
            result['status'] = 'EMPTY'
            result['size_bytes'] = 0
            result['mtime'] = mtime
            return result

        md5, sha256, blob_sha1 = compute_hashes(filepath)

        result.update({
            'status': 'EXISTS',
            'size_bytes': size,
            'mtime': mtime,
            'md5': md5,
            'sha256': sha256,
            'git_blob_sha1': blob_sha1,
        })

    except Exception as e:
        result['status'] = 'ERROR'
        result['error'] = str(e)

    return result


def collect_directory(dirpath, relprefix):
    """Collect metadata for all files in a directory."""
    results = []
    if not os.path.isdir(dirpath):
        return results

    for entry in sorted(os.listdir(dirpath)):
        full = os.path.join(dirpath, entry)
        rel = os.path.join(relprefix, entry)
        if os.path.isfile(full):
            results.append(collect_file(full, rel))
        elif os.path.isdir(full):
            results.extend(collect_directory(full, rel))

    return results


def run_audit():
    """Run full workspace audit."""
    print(f'Audit Hook v1.0 — STARTING ({datetime.now(timezone.utc).isoformat()})')
    print(f'Workspace: {WORKSPACE}')
    print(f'Repo root: {REPO_ROOT}')
    print()

    entries = []

    for target in TARGET_FILES:
        if target.endswith('/'):
            dirpath = os.path.join(WORKSPACE, target)
            entries.extend(collect_directory(dirpath, target))
        else:
            filepath = os.path.join(WORKSPACE, target)
            entries.append(collect_file(filepath, target))

    for relpath, fullpath in EXTERNAL_FILES:
        entries.append(collect_file(fullpath, relpath))

    exists_count = sum(1 for e in entries if e['status'] == 'EXISTS')
    empty_count = sum(1 for e in entries if e['status'] == 'EMPTY')
    not_found_count = sum(1 for e in entries if e['status'] == 'NOT_FOUND')
    error_count = sum(1 for e in entries if e['status'] == 'ERROR')

    audit_result = {
        'schema': 'v88-workspace-audit-v1.0',
        'task_id': 'V88_PHASE03_P7_DSHB_P019_FACTOR_CALIB_ALIGNMENT',
        'task': 'T1_AUDIT_HOOK_DEPLOYMENT',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'branch': 'feature/v88-g1',
        'branch_locked': True,
        'read_only': True,
        'no_auto_git_push': True,
        'summary': {
            'total_entries': len(entries),
            'exists': exists_count,
            'empty': empty_count,
            'not_found': not_found_count,
            'error': error_count,
        },
        'entries': entries,
    }

    os.makedirs(AUDIT_DIR, exist_ok=True)
    log_path = os.path.join(AUDIT_DIR, 'workspace_audit_snapshot.json')
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(audit_result, f, indent=2, ensure_ascii=False)

    jsonl_path = os.path.join(AUDIT_DIR, 'workspace_audit_log.jsonl')
    with open(jsonl_path, 'a', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(f'Audit Hook v1.0 — COMPLETE')
    print(f'  Files collected: {len(entries)}')
    print(f'  EXISTS: {exists_count}')
    print(f'  EMPTY: {empty_count}')
    print(f'  NOT_FOUND: {not_found_count}')
    print(f'  ERROR: {error_count}')
    print(f'  Audit log: {log_path}')
    print(f'  JSONL log: {jsonl_path}')

    return audit_result


if __name__ == '__main__':
    run_audit()
