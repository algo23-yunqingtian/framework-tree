#!/usr/bin/env python
import io, hashlib, os

manifest_path = r'D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03\p0\MD5_MANIFEST.md'
f = io.open(manifest_path, 'r', encoding='utf-8')
content = f.read()
f.close()

# Update node_binding_engine.py MD5
old = 'node_binding_engine.py  MD5=00523AADA6C98FCCE36573294C669A4A'
new = 'node_binding_engine.py  MD5=cd73deaeec54a7f1f8bde92c1300a9dc'
if old in content:
    content = content.replace(old, new)
    print('Updated node_binding_engine.py MD5')
else:
    print('WARNING: old engine MD5 not found in manifest')

# Update risk list MD5
old_risk = 'v88_phase03_visual_risk_list.md  MD5=2DDB8205E52B40526C041EBB704EE35D'
new_risk = 'v88_phase03_visual_risk_list.md  MD5=d394ddee9e749ffde6e2606502e9f7f1'
if old_risk in content:
    content = content.replace(old_risk, new_risk)
    print('Updated risk list MD5')

# Add new entries if not present
new_section = """
### V88_PHASE03_P0_R1_ENGINE_ADAPT_FIX (DSHE)
| 文件 | MD5 | 大小(B) |
|------|:---:|:------:|
| scripts/node_binding_engine.py | `cd73deaeec54a7f1f8bde92c1300a9dc` | 45,411 |
| analysis/e2e_output/v88/phase03/p0/v88_phase03_p0_engine_adapt_fix_report.md | `480b486c872c7cef09c11eb937d7ab20` | 11,748 |
| analysis/e2e_output/v88/phase03/p0/v88_phase03_visual_risk_list.md | `d394ddee9e749ffde6e2606502e9f7f1` | 14,507 |
| STATUS.md | `ed6f4c71bf7b26ef49655673693d5b37` | 1,047,997 |
| analysis/e2e_output/v88/JOB_READY.flag | `762adde951011c7a56714e402ea0d4d9` | 52,467 |
"""

if 'V88_PHASE03_P0_R1_ENGINE_ADAPT_FIX' not in content:
    content += '\n' + new_section
    print('Added new section')
else:
    print('Section already exists, skipping')

f = io.open(manifest_path, 'w', encoding='utf-8')
f.write(content)
f.close()
print('MD5_MANIFEST.md updated successfully')