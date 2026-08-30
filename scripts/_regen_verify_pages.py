#!/usr/bin/env python3
"""重写 verify_render.js 的 PAGES 数组：铅 30 页保持原样，铜铝 34 页按 jsdom 实测注册。"""
import re
import subprocess
import json

ROOT = '/home/ubuntu/framework-tree/'
P = ROOT + 'scripts/verify_render.js'
s = open(P, encoding='utf-8').read()

head = s.split('const PAGES = [\n')[0]
rest = s[s.rfind('\n];') + 3:]
# pb 块从 git HEAD 恢复原文（避免正则抽取丢行尾逗号）
pb_orig = subprocess.run(['git', 'show', 'HEAD:scripts/verify_render.js'],
                         cwd=ROOT, capture_output=True, text=True).stdout
pb_block = re.search(r'const PAGES = \[\n(.*?)\n\];', pb_orig, re.S).group(1)
pb_only = '\n'.join(l for l in pb_block.split('\n') if l.strip())

# jsdom 实测：哪些 cid 有 toggle 按钮且 se.series>=3
r = subprocess.run(['node', 'scripts/_probe2.js'], cwd=ROOT,
                   capture_output=True, text=True)
data = json.loads(r.stdout.strip().split('\n')[-1])
files = sorted(set(x['f'] for x in data))
seasonal = {f: [x['cid'] for x in data if x['f'] == f and x['okToggle']] for f in files}
charts = {f: open(ROOT + f, encoding='utf-8').read().count('<div class="chart">') for f in files}


def keyn(f):
    """al_3_2_3.html -> al_323 ; cu_2_1.html -> cu_21"""
    m = re.match(r'^(cu|al)_(\d)(?:_(\d+))?(?:_(\d+))?\.html$', f)
    return m.group(1) + '_' + m.group(2) + (m.group(3) or '') + (m.group(4) or '')


assert keyn('al_3_2_3.html') == 'al_323'
assert keyn('cu_3_1_1.html') == 'cu_311'
assert keyn('al_2_1.html') == 'al_21'
assert keyn('cu_6_1.html') == 'cu_61'

out = ['const PAGES = [',
       '  // ── 铅(PB) 30 页 ──',
       pb_only,
       '  // ── 铜(CU)/铝(AL) 34 页：主脑 2026-08-31 jsdom 实测注册 ──',
       '  // 铜铝页部分图无 season toggle 按钮（纯时序渲染），seasonal 留空；',
       '  // 不要按「__opts.se 存在」就注册——那些图初始即渲染历史年份线但无切换按钮 ──']

for f in files:
    n = charts[f]
    slist = ','.join("'" + x + "'" for x in seasonal[f])
    line = "  { key: '%s', file: '%s'" % (keyn(f), f)
    if n != 3:
        line += ", charts: %d" % n
    line += ", seasonal: [%s] }," % slist
    out.append(line)

out.append('];')
open(P, 'w', encoding='utf-8').write(head + '\n'.join(out) + rest)

new = open(P, encoding='utf-8').read()
print('PAGES 条目:', new.count("{ key: '"))
print('seasonal 图:', sum(len(v) for v in seasonal.values()))
print('seasonal=[] 页:', [f for f in files if not seasonal[f]])
print('\n样本行:')
for l in out:
    if "al_21" in l or "cu_311" in l:
        print(' ', l)
