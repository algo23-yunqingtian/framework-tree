#!/usr/bin/env python
import io, os

manifest_path = r'D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\hermes_e2e_test\MD5_MANIFEST_cross_review.md'

# Try reading with different encodings
for enc in ['utf-8', 'gbk', 'latin-1']:
    try:
        f = io.open(manifest_path, 'r', encoding=enc)
        content = f.read()
        f.close()
        print(f'Read with encoding: {enc}')
        break
    except:
        continue

new_section = """
### V88_PHASE03_P0_R1_ENGINE_ADAPT_FIX (DSHE)
| File | MD5 | Size(B) |
|------|:---:|:------:|
| scripts/node_binding_engine.py | `cd73deaeec54a7f1f8bde92c1300a9dc` | 45,411 |
| analysis/e2e_output/v88/phase03/p0/v88_phase03_p0_engine_adapt_fix_report.md | `480b486c872c7cef09c11eb937d7ab20` | 11,748 |
| analysis/e2e_output/v88/phase03/p0/v88_phase03_visual_risk_list.md | `d394ddee9e749ffde6e2606502e9f7f1` | 14,507 |
"""

if 'V88_PHASE03_P0_R1_ENGINE_ADAPT_FIX' not in content:
    content += '\n' + new_section
    f = io.open(manifest_path, 'w', encoding=enc)
    f.write(content)
    f.close()
    print('Cross-review MD5 manifest updated')
else:
    print('Already exists')