#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update factor audit with current SHA snapshots and concurrent change analysis.
"""
import json, hashlib, os, datetime

BASE = r'D:\DSH_WORK\github工作\回测'
P49 = os.path.join(BASE, 'artifacts', 'p49_v3_backtest')
G7 = os.path.join(BASE, 'G7_ADJUDICATION_LEDGER')
AUDIT_JSON = os.path.join(BASE, 'artifacts', 'dshd_p81_factor_stability_audit.json')
VERSION_HISTORY = os.path.join(G7, 'p81_version_history.json')
HISTORY_AUDIT = os.path.join(BASE, 'artifacts', 'dshd_p81_factor_stability_audit.json')

# Re-compute current SHAs
current_sha = {}
for fname in os.listdir(P49):
    if fname.endswith(('.json', '.csv', '.md', '.py')) and not fname.startswith('.'):
        fpath = os.path.join(P49, fname)
        if os.path.isfile(fpath):
            with open(fpath, 'rb') as f:
                sha = hashlib.sha256(f.read()).hexdigest()
            current_sha[fname] = {'sha256': sha, 'size_bytes': os.path.getsize(fpath)}

# Detect concurrent changes (DSHA-P49-V3-WEIGHT-FIX)
concurrent_changes = []
for fname in ['factor_weight.json', 'factor_enable_config.json', 'weighted_backtest_metrics.json', 'factor_stability_report.md']:
    fpath = os.path.join(P49, fname)
    if os.path.exists(fpath):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = json.load(f)
            token = content.get('token', '')
            if 'WEIGHT-FIX' in token or 'WEIGHT_FIX' in str(content):
                concurrent_changes.append({
                    'file': fname,
                    'token': token,
                    'config_id': content.get('config_id', ''),
                    'prev_task': content.get('prev_task', ''),
                    'description': 'File modified by DSHA-P49-V3-WEIGHT-FIX during audit window',
                })
        except (json.JSONDecodeError, Exception):
            pass

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()

# Update audit JSON with current SHAs and concurrent change findings
if os.path.exists(AUDIT_JSON):
    with open(AUDIT_JSON, 'r', encoding='utf-8') as f:
        audit = json.load(f)
    
    # Add current SHA snapshots
    audit['p1_3_current_sha_snapshots'] = current_sha
    
    # Add concurrent change analysis
    audit['p1_3_concurrent_changes'] = {
        'detected': len(concurrent_changes) > 0,
        'changes': concurrent_changes,
        'analysis': {
            'summary': 'DSHA-P49-V3-WEIGHT-FIX task modified factor config files during audit window',
            'changes_applied': [
                'factor_enable_config.json: spread_cs moved from standard_factors to temporarily_disabled',
                'factor_weight.json: method changed to positive_IC_mean_weighted_with_shrinkage (4 positive IC factors only)',
                'weighted_backtest_metrics.json: backtest results regenerated with new config',
                'factor_stability_report.md: stability report regenerated',
            ],
            'ic_method_finding_status': 'PARTIALLY_MITIGATED',
            'detail': 'The WEIGHT-FIX task excluded spread_cs (negative IC dominant factor) and filtered to positive IC factors only. '
                      'This addresses the symptom but not the root cause: IC values still use TS_IC method, not CSV_IC. '
                      'The factor_stability_report.md should still show the same OI sign instability.',
        }
    }
    
    audit['updated_at'] = now
    
    with open(AUDIT_JSON, 'w', encoding='utf-8') as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)
    print(f'Updated: {AUDIT_JSON} ({os.path.getsize(AUDIT_JSON)} bytes)')
    print(f'  Concurrent changes detected: {len(concurrent_changes)}')
    for c in concurrent_changes:
        print(f'    - {c["file"]}: {c["config_id"]}')
else:
    print(f'ERROR: {AUDIT_JSON} not found')

# Update version history with current SHAs
if os.path.exists(VERSION_HISTORY):
    with open(VERSION_HISTORY, 'r', encoding='utf-8') as f:
        vh = json.load(f)
    
    # Add entries for current factor audit
    for fname, info in current_sha.items():
        # Check if this entry already exists
        exists = any(e.get('file') == fname and e.get('audit_context') == 'factor_stability_audit_current' 
                     for e in vh['entries'])
        if not exists:
            entry = {
                'snapshot_id': f'p81-audit-factor-current-{fname.replace(".", "-").replace("/", "-")}',
                'file': fname,
                'file_path': os.path.join(P49, fname),
                'action': 'AUDIT_SHA_SNAPSHOT_CURRENT',
                'agent': 'DSHD-P81-AUDIT-FACTOR',
                'reason': 'DSHD-P81-AUDIT-FACTOR-STABILITY: current SHA snapshot (post WEIGHT-FIX)',
                'timestamp': now,
                'task': 'DSHD-P81-AUDIT-FACTOR-STABILITY',
                'token': 'DSHD-P81-AUDIT-FACTOR-TOKEN',
                'pre_edit': {
                    'sha256': info['sha256'],
                    'size_bytes': info['size_bytes']
                },
                'snapshot_sha256': info['sha256'],
                'snapshot_size_bytes': info['size_bytes'],
                'toolchain_root': P49,
                'audit_context': 'factor_stability_audit_current'
            }
            vh['entries'].append(entry)
    
    vh['_meta']['last_factor_audit_update'] = now
    vh['_meta']['last_factor_audit_sha_count'] = len(current_sha)
    
    with open(VERSION_HISTORY, 'w', encoding='utf-8') as f:
        json.dump(vh, f, indent=2, ensure_ascii=False)
    print(f'\nUpdated: {VERSION_HISTORY} (entries: {len(vh["entries"])})')
else:
    print(f'ERROR: {VERSION_HISTORY} not found')
