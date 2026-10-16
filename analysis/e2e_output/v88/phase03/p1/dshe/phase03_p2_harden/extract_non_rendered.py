import json
from collections import Counter

with open(r'D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03\p1\dshe\render_p012_prep\new_derived_metric_full_render_result.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

non_rendered = [r for r in data['individual_results'] if r['render_status'] != 'RENDERED']
print(f"Total non-RENDERED: {len(non_rendered)}")
print()
for r in non_rendered:
    iid = r['indicator_id']
    status = r['render_status']
    commodity = r['commodity']
    has_data = r['data_quality'].get('has_data', False)
    has_mapping = r['has_mapping']
    quality_issues = r['data_quality'].get('quality_issues', [])
    anomaly_type = r.get('anomaly_type', [])
    print(f"{iid:35s} | {status:18s} | commodity={commodity:5s} | hasData={has_data} | anomaly={anomaly_type}")

print()
statuses = Counter(r['render_status'] for r in non_rendered)
print(f"Status distribution: {dict(statuses)}")

# Write to evidence JSON
evidence = {
    "task_id": "V88_PHASE03_P2_DSHE_GATE_HARDEN_AND_PHASE04_PREP_PARTIAL_CHECK_JOB",
    "task": "T2",
    "task_description": "Partial render precheck for non-RENDERED indicators",
    "generated": "2026-10-16T22:45:00+08:00",
    "source": "new_derived_metric_full_render_result.json",
    "total_indicators": len(data['individual_results']),
    "non_rendered_count": len(non_rendered),
    "status_distribution": dict(statuses),
    "non_rendered_indicators": [
        {
            "indicator_id": r['indicator_id'],
            "mapped_target": r['mapped_target'],
            "commodity": r['commodity'],
            "render_status": r['render_status'],
            "has_mapping": r['has_mapping'],
            "has_data": r['data_quality'].get('has_data', False),
            "quality_issues": r['data_quality'].get('quality_issues', []),
            "anomaly_type": r.get('anomaly_type', []),
            "db_row_count": r['db_check'].get('row_count', 0)
        }
        for r in non_rendered
    ],
    "disclaimer": "This is a PRECHECK only. No indicator status changes have been made. No matched/partial classification has been altered.",
    "caliber_note": "caliber_inventory_snapshot not yet available from HERMES; this precheck uses existing render results from Phase03 P1."
}

with open(r'D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03\p1\dshe\phase03_p2_harden\partial_render_evidence\non_rendered_indicators_evidence.json', 'w', encoding='utf-8') as f:
    json.dump(evidence, f, indent=2, ensure_ascii=False)

print(f"\nEvidence written to partial_render_evidence/non_rendered_indicators_evidence.json")