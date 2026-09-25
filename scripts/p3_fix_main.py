#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P3_FIX_20260924: Comprehensive indicator data fix
Phase 1: R2 baseline merge (verified/freq/unit from main)
Phase 2: N1 Chinese key cleanup
Phase 3: N4 64_group migration to _meta
Phase 4: N3 FLAGGED_FOR_REVIEW
Phase 5: R1 zhji_id duplicate resolution
Phase 6: R-PREFIX-1 illegal prefix cleanup
"""

import json
import re
import os
import sys
import copy
from collections import Counter, defaultdict
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ===================== LOAD DATA =====================
with open(os.path.join(BASE, 'data', '_win_old.json'), 'r', encoding='utf-8') as f:
    win_raw = json.load(f)
with open(os.path.join(BASE, 'data', 'indicators_v1.json'), 'r', encoding='utf-8') as f:
    main_raw = json.load(f)

# Separate metadata from indicators
win_meta = {k: v for k, v in win_raw.items() if k.startswith('_') or k in ('version', 'change', 'updated')}
win_indicators = {k: v for k, v in win_raw.items() if k not in win_meta and isinstance(v, dict)}

main_meta = {k: v for k, v in main_raw.items() if k.startswith('_') or k in ('version', 'changelog')}
main_indicators = {k: v for k, v in main_raw.items() if k not in main_meta and isinstance(v, dict)}

# Ensure _meta exists
if '_meta' not in win_meta:
    win_meta['_meta'] = {}

print(f"Loaded: win={len(win_indicators)} indicators, main={len(main_indicators)} indicators")

# ===================== TRACKING =====================
changes = {
    'r2_verified_from_main': 0,
    'r2_freq_from_main': 0,
    'r2_unit_from_main': 0,
    'r2_verified_by_from_main': 0,
    'r2_name_from_win': 0,
    'n1_cn_keys_moved_to_meta': 0,
    'n4_group_moved': 0,
    'n3_flagged': 0,
    'r1_series_slice_added': 0,
    'r1_dup_groups_resolved': 0,
    'prefix_keys_renamed': 0,
    'prefix_keys_moved_to_meta': 0,
}
change_log = []  # detailed log

def log_change(phase, key, detail):
    change_log.append(f"[{phase}] {key}: {detail}")

# ===================== PHASE 1: R2 BASELINE MERGE =====================
print("\n" + "=" * 60)
print("PHASE 1: R2 BASELINE MERGE")
print("=" * 60)

both_keys = set(win_indicators.keys()) & set(main_indicators.keys())
print(f"Keys in both win and main: {len(both_keys)}")

for k in sorted(both_keys):
    w_entry = win_indicators[k]
    m_entry = main_indicators[k]

    # verified: always from main
    if 'verified' in m_entry and w_entry.get('verified') != m_entry['verified']:
        old_val = w_entry.get('verified')
        w_entry['verified'] = m_entry['verified']
        changes['r2_verified_from_main'] += 1
        log_change('R2', k, f"verified: {old_val} -> {m_entry['verified']}")

    # freq: always from main
    if 'freq' in m_entry and w_entry.get('freq') != m_entry['freq']:
        old_val = w_entry.get('freq')
        w_entry['freq'] = m_entry['freq']
        changes['r2_freq_from_main'] += 1
        log_change('R2', k, f"freq: {old_val} -> {m_entry['freq']}")

    # unit: always from main
    if 'unit' in m_entry and w_entry.get('unit') != m_entry['unit']:
        old_val = w_entry.get('unit')
        w_entry['unit'] = m_entry['unit']
        changes['r2_unit_from_main'] += 1
        log_change('R2', k, f"unit: {old_val} -> {m_entry['unit']}")

    # _verified_by: always from main
    if '_verified_by' in m_entry:
        old_val = w_entry.get('_verified_by')
        if old_val != m_entry['_verified_by']:
            w_entry['_verified_by'] = m_entry['_verified_by']
            changes['r2_verified_by_from_main'] += 1
            log_change('R2', k, f"_verified_by: {old_val} -> {m_entry['_verified_by']}")

    # name: from win (keep win's name)
    if 'name' in w_entry and 'name' in m_entry and w_entry['name'] != m_entry['name']:
        changes['r2_name_from_win'] += 1

print(f"\nR2 merge results:")
print(f"  verified updated from main: {changes['r2_verified_from_main']}")
print(f"  freq updated from main: {changes['r2_freq_from_main']}")
print(f"  unit updated from main: {changes['r2_unit_from_main']}")
print(f"  _verified_by updated from main: {changes['r2_verified_by_from_main']}")
print(f"  name kept from win: {changes['r2_name_from_win']}")

# Verify: no verified downgrade (True->False)
verified_downgrades = 0
for k in both_keys:
    if main_indicators[k].get('verified') == True and win_indicators[k].get('verified') == False:
        verified_downgrades += 1
print(f"\n  verified downgrades (main=True, win=False): {verified_downgrades}")

# Verify: no freq reverse change (daily->quarterly etc.)
freq_reverse = 0
for k in both_keys:
    wf = win_indicators[k].get('freq', '')
    mf = main_indicators[k].get('freq', '')
    if wf != mf:
        freq_reverse += 1
print(f"  freq changes (win != main): {freq_reverse}")

# ===================== PHASE 2: N1 CHINESE KEY CLEANUP =====================
print("\n" + "=" * 60)
print("PHASE 2: N1 CHINESE KEY CLEANUP")
print("=" * 60)

# Full non-ASCII scan
non_ascii_keys = [k for k in list(win_indicators.keys()) if re.search(r'[^\x00-\x7f]', k)]
print(f"Non-ASCII keys found: {len(non_ascii_keys)}")

# Mapping for cross-product Chinese keys -> _meta
cn_meta_entries = {}
for k in non_ascii_keys:
    entry = win_indicators[k]
    meta_key = f"_cn_{k}"
    cn_meta_entries[meta_key] = {
        'original_key': k,
        'reason': 'cross-product indicator, no single product prefix',
        'entry': copy.deepcopy(entry)
    }
    del win_indicators[k]
    changes['n1_cn_keys_moved_to_meta'] += 1
    log_change('N1', k, f"moved to _meta as {meta_key}")
    print(f"  Moved to _meta: '{k}' -> '{meta_key}'")

# Add to _meta
for meta_key, meta_entry in cn_meta_entries.items():
    win_meta['_meta'][meta_key] = meta_entry

print(f"\nN1 results: {changes['n1_cn_keys_moved_to_meta']} Chinese keys moved to _meta")

# ===================== PHASE 3: N4 64_GROUP MIGRATION =====================
print("\n" + "=" * 60)
print("PHASE 3: N4 64_GROUP MIGRATION")
print("=" * 60)

if '64_group' in win_indicators:
    g64 = win_indicators['64_group']
    win_meta['_meta']['64_group'] = copy.deepcopy(g64)
    del win_indicators['64_group']
    changes['n4_group_moved'] += 1
    log_change('N4', '64_group', 'moved to _meta')
    print(f"  64_group moved to _meta (name: {g64.get('name','?')[:60]})")
else:
    print(f"  64_group not found")

business_count = len(win_indicators)
print(f"\nBusiness indicators after N4: {business_count}")

# ===================== PHASE 4: N3 FLAGGED FOR REVIEW =====================
print("\n" + "=" * 60)
print("PHASE 4: N3 FLAGGED FOR REVIEW")
print("=" * 60)

n3_keys = ['al_2_scrap_al_import_source', 'li_52_battery', 'li_52_ev_sales', 'ni_45_output_2']
for k in n3_keys:
    if k in win_indicators:
        win_indicators[k]['_flag'] = 'FLAGGED_FOR_REVIEW'
        changes['n3_flagged'] += 1
        log_change('N3', k, 'FLAGGED_FOR_REVIEW')
        print(f"  Flagged: {k} -> name={win_indicators[k].get('name','?')[:40]}")
    else:
        print(f"  NOT FOUND: {k}")

print(f"\nN3 results: {changes['n3_flagged']} items flagged")

# ===================== PHASE 5: R1 ZHJI_ID DUPLICATE RESOLUTION =====================
print("\n" + "=" * 60)
print("PHASE 5: R1 ZHJI_ID DUPLICATE RESOLUTION")
print("=" * 60)

# Collect all ID values from ids dict
all_id_values = defaultdict(list)  # id_value -> [(key, product)]
for k, entry in win_indicators.items():
    ids = entry.get('ids', {})
    if isinstance(ids, dict):
        for product, id_val in ids.items():
            if id_val:
                all_id_values[id_val].append((k, product))

# Find duplicates
dup_groups = {id_val: members for id_val, members in all_id_values.items() if len(members) > 1}
total_dup_indicators = sum(len(m) for m in dup_groups.values())

print(f"Total ID values: {sum(len(m) for m in all_id_values.values())}")
print(f"Unique IDs: {len(all_id_values)}")
print(f"Duplicate groups: {len(dup_groups)}")
print(f"Indicators in dupe groups: {total_dup_indicators}")

# For each duplicate group, add series_slice field
# Use the indicator key as the distinguishing factor
for id_val, members in sorted(dup_groups.items(), key=lambda x: -len(x[1])):
    for idx, (key, product) in enumerate(members):
        entry = win_indicators.get(key)
        if entry:
            # Determine series_slice from the key
            # Use the part after product prefix + node
            key_parts = key.split('_')
            if len(key_parts) > 1:
                # Extract meaningful suffix
                suffix = '_'.join(key_parts[2:]) if len(key_parts) > 2 else key_parts[1]
                if suffix:
                    entry['series_slice'] = suffix
                else:
                    entry['series_slice'] = f'_{idx+1}'
            else:
                entry['series_slice'] = f'_{idx+1}'
            changes['r1_series_slice_added'] += 1

    changes['r1_dup_groups_resolved'] += 1

print(f"\nR1 results:")
print(f"  Duplicate groups resolved: {changes['r1_dup_groups_resolved']}")
print(f"  series_slice fields added: {changes['r1_series_slice_added']}")

# ===================== PHASE 6: R-PREFIX-1 ILLEGAL PREFIX CLEANUP =====================
print("\n" + "=" * 60)
print("PHASE 6: R-PREFIX-1 ILLEGAL PREFIX CLEANUP")
print("=" * 60)

whitelist_prefixes = ['cu', 'al', 'zn', 'ni', 'sn', 'si', 'li', 'pb', 'ao', 'wr']

# Identify illegal prefix keys (the specific external source ones from the task)
target_prefixes = [
    'lme', 'zincconc', 'shfe', 'electrolytic', 'smm', 'usgs',
    'coated', 'sample', 'imea', 'mhp', 'laterite', 'h2so4',
    'alumina', 'bauxite', 'tin', 'refined', 'refinezinc',
    'mysteel', 'nbs', 'plant', 'water', 'by', 'china',
    'fluoroaluminum'
]

# Build product inference map based on key content
product_map = {
    'zn': ['zincconc', 'zn_'],
    'al': ['alumina', 'bauxite', 'al_', 'fluoroal'],
    'ni': ['mhp', 'laterite', 'refined', 'water'],
    'si': ['h2so4'],
    'cu': ['lme_cu'],
    'pb': ['lme_pb'],
}

# Cross-product indicators to move to _meta
cross_product_keys = ['lme_inventory', 'shfe_inventory', 'nbs_pmi_m', 'by_province_by_country',
                      'china_customs_brazil_import_ore_zn_ore_sand_conc_colombia_china']

illegal_prefix_keys = []
for k in list(win_indicators.keys()):
    for p in target_prefixes:
        if k.startswith(p):
            illegal_prefix_keys.append(k)
            break

print(f"Illegal prefix keys found: {len(illegal_prefix_keys)}")

for k in sorted(illegal_prefix_keys):
    entry = win_indicators[k]
    name = entry.get('name', '')

    # Determine if cross-product
    if k in cross_product_keys:
        win_meta['_meta'][f'_prefix_{k}'] = {
            'original_key': k,
            'reason': 'cross-product indicator, moved from illegal prefix cleanup',
            'entry': copy.deepcopy(entry)
        }
        del win_indicators[k]
        changes['prefix_keys_moved_to_meta'] += 1
        log_change('PREFIX', k, 'moved to _meta (cross-product)')
        print(f"  Moved to _meta: '{k}' (cross-product)")
        continue

    # Determine product
    product = None
    # Check key content for product hints
    lower_k = k.lower()
    for p, indicators in product_map.items():
        for ind in indicators:
            if ind in lower_k:
                product = p
                break
        if product:
            break

    # If no product found from content, try to infer from the rest of the key
    if not product:
        # Check if key contains product abbreviation
        for p in ['cu', 'al', 'zn', 'ni', 'sn', 'si', 'li', 'pb']:
            if f'{p}' in lower_k.split('_')[1:] or f'{p}' in lower_k:
                # More careful check: look for product as a separate token
                for token in lower_k.split('_'):
                    if token == p:
                        product = p
                        break
                if product:
                    break

    if product:
        new_key = f'{product}_{k}'
        if new_key != k and new_key not in win_indicators:
            del win_indicators[k]
            win_indicators[new_key] = entry
            entry['_renamed_from'] = k
            changes['prefix_keys_renamed'] += 1
            log_change('PREFIX', k, f"renamed to '{new_key}'")
            print(f"  Renamed: '{k}' -> '{new_key}'")
        else:
            # If new_key exists, just add a note
            entry['_prefix_conflict'] = new_key
            changes['prefix_keys_renamed'] += 1
            log_change('PREFIX', k, f"conflict with '{new_key}', marked")
            print(f"  Conflict: '{k}' -> '{new_key}' exists, marked")
    else:
        # Cannot determine product, move to _meta
        win_meta['_meta'][f'_prefix_{k}'] = {
            'original_key': k,
            'reason': 'illegal prefix, product unknown',
            'entry': copy.deepcopy(entry)
        }
        del win_indicators[k]
        changes['prefix_keys_moved_to_meta'] += 1
        log_change('PREFIX', k, 'moved to _meta (product unknown)')
        print(f"  Moved to _meta: '{k}' (product unknown)")

print(f"\nR-PREFIX-1 results:")
print(f"  Keys renamed: {changes['prefix_keys_renamed']}")
print(f"  Keys moved to _meta: {changes['prefix_keys_moved_to_meta']}")

# ===================== FINALIZE =====================
print("\n" + "=" * 60)
print("FINALIZE")
print("=" * 60)

# Add metadata
final_data = {}

# Version
final_data['version'] = 'v3.50-p3fix'
final_data['change'] = 'P3_FIX: N1/N4/N3/R1/R2/PREFIX fixes applied, rebased to origin/main'
final_data['updated'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')

# Metadata
final_data['_meta'] = win_meta.get('_meta', {})
final_data['_main_metric'] = win_raw.get('_main_metric', {})

# Add all indicators
for k, v in sorted(win_indicators.items()):
    final_data[k] = v

# Count
final_count = len(win_indicators)
print(f"\nFinal business indicator count: {final_count}")
print(f"Total data keys (incl meta): {len(final_data)}")
print(f"Total _meta entries: {len(final_data.get('_meta', {}))}")

# Verify no non-ASCII keys remain
remaining_cn = [k for k in win_indicators.keys() if re.search(r'[^\x00-\x7f]', k)]
print(f"\nRemaining non-ASCII keys: {len(remaining_cn)}")

# Verify whitelist compliance
remaining_illegal = []
for k in win_indicators.keys():
    if not any(k.startswith(w) for w in whitelist_prefixes):
        remaining_illegal.append(k)
print(f"Remaining illegal prefix keys: {len(remaining_illegal)}")
if remaining_illegal:
    print(f"  Keys: {remaining_illegal[:20]}")

# Verify R2: no verified downgrade
verified_downgrade = 0
for k in both_keys:
    if k in win_indicators:
        w_v = win_indicators[k].get('verified')
        m_v = main_indicators[k].get('verified')
        if m_v == True and w_v == False:
            verified_downgrade += 1
print(f"R2 verification - verified downgrades: {verified_downgrade}")

# Verify R2: no _verified_by loss
verified_by_loss = 0
for k in both_keys:
    if k in win_indicators:
        if '_verified_by' in main_indicators[k] and '_verified_by' not in win_indicators[k]:
            verified_by_loss += 1
print(f"R2 verification - _verified_by loss: {verified_by_loss}")

# ===================== WRITE OUTPUT =====================
output_path = os.path.join(BASE, 'data', 'indicators_v1.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print(f"\nWritten: {output_path} ({os.path.getsize(output_path)} bytes)")

# Write change log
log_path = os.path.join(BASE, 'scripts', 'p3_fix_changelog.txt')
with open(log_path, 'w', encoding='utf-8') as f:
    f.write(f"P3_FIX_20260924 Change Log\n")
    f.write(f"Generated: {datetime.now().isoformat()}\n")
    f.write(f"Total changes: {len(change_log)}\n\n")
    for line in change_log:
        f.write(line + '\n')
print(f"Change log: {log_path}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
for key, val in changes.items():
    print(f"  {key}: {val}")

# Save for later use by deliverable scripts
summary_path = os.path.join(BASE, 'scripts', 'p3_fix_summary.json')
with open(summary_path, 'w', encoding='utf-8') as f:
    json.dump({
        'changes': changes,
        'total_changes': len(change_log),
        'final_count': final_count,
        'meta_count': len(final_data.get('_meta', {})),
        'remaining_cn': len(remaining_cn),
        'remaining_illegal': len(remaining_illegal),
        'verified_downgrade': verified_downgrade,
        'verified_by_loss': verified_by_loss,
        'dup_groups': len(dup_groups),
        'dup_indicators': total_dup_indicators,
    }, f, ensure_ascii=False, indent=2)
print(f"Summary saved: {summary_path}")