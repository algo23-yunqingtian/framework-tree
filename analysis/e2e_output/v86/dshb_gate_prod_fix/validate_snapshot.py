import json

path = r"D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v86\dshb_gate_prod_fix\full_reverify_v3_batch_logs\v86_rc2_dshb_bridge_snapshot_for_dshe.json"
with open(path, "r", encoding="utf-8") as f:
    d = json.load(f)

print("Valid JSON: YES")
print(f"Entries count: {len(d['entries'])}")
print(f"Metadata complete: {d['dual_dimension_stats']['metadata_completion']['complete']}/{d['dual_dimension_stats']['metadata_completion']['total']}")
print(f"Data fetchable: {d['dual_dimension_stats']['data_fetchable']['fetchable']}/{d['dual_dimension_stats']['data_fetchable']['total']}")
print(f"By category: {d['summary']['by_category']}")
print(f"By variety: {d['summary']['by_variety']}")
print(f"Has dshe_validation_info: {'dshe_validation_info' in d}")
print(f"Has metadata: {'metadata' in d}")
print(f"Has dual_dimension_stats: {'dual_dimension_stats' in d}")
print(f"Has entries: {'entries' in d}")
print(f"Has summary: {'summary' in d}")
print(f"Sampling strategy keys: {list(d['dshe_validation_info']['sampling_strategy'].keys())}")

# Verify first 8 are originals
originals = [e for e in d['entries'] if e['batch'] == 0]
print(f"\nOriginal entries (batch=0): {len(originals)}")
for e in originals:
    print(f"  {e['indicator_id']}: {e['name_cn']} | short={e['zhiji_short_id']} long={e['zhiji_long_id']} cat={e['category']} meta={e['metadata_complete']} fetch={e['data_fetchable']}")

# Verify category counts match
cats = {}
for e in d['entries']:
    cats[e['category']] = cats.get(e['category'], 0) + 1
print(f"\nCategory counts verification: {cats}")
print(f"Expected: derived=47, fabricated_short_id=123, real_short_id=8")

# Check all entries have required fields
required = ['indicator_id','semantic_id','name_cn','unit','type','zhiji_short_id','zhiji_long_id',
            'api_series_id_from_search','metadata_complete','data_fetchable','dependency_block',
            'fetch_error_msg','category','batch','priority']
missing = []
for e in d['entries']:
    for f in required:
        if f not in e:
            missing.append((e['indicator_id'], f))
print(f"\nMissing fields: {len(missing)}")
if missing:
    for m in missing[:10]:
        print(f"  {m}")
else:
    print("  ALL entries have required fields [OK]")

# Check data_fetchable is all False
fetch_true = [e['indicator_id'] for e in d['entries'] if e['data_fetchable']]
print(f"\nEntries with data_fetchable=true: {len(fetch_true)} (should be 0)")

# Check dependency_block is all True
block_false = [e['indicator_id'] for e in d['entries'] if not e['dependency_block']]
print(f"Entries with dependency_block=false: {len(block_false)} (should be 0)")

# Check derived entries have no IDs
derived_no_ids = sum(1 for e in d['entries'] if e['category']=='derived' and e['zhiji_short_id']=='DERIVED')
print(f"Derived entries with DERIVED IDs: {derived_no_ids} (should be 47)")

# Check metadata_complete matches
meta_true = sum(1 for e in d['entries'] if e['metadata_complete'])
meta_false = sum(1 for e in d['entries'] if not e['metadata_complete'])
print(f"Metadata complete=true: {meta_true} (should be 131)")
print(f"Metadata complete=false: {meta_false} (should be 47)")

print(f"\nFile size: {len(open(path,'rb').read())} bytes")
ok = (len(fetch_true)==0 and len(block_false)==0 and derived_no_ids==47 and meta_true==131)
print("ALL VALIDATIONS PASSED [OK]" if ok else "SOME CHECKS FAILED")
