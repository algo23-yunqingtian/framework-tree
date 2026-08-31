# 主看板 chip 跳转修复 · 任务卡（解析器已由主脑实测验证）

> 问题：GitHub 主看板，点左侧指标行右侧的「品种小标签(chip)」，只有铅(PB)最早那十几个能跳进子页面，其他品种点进去只显示占位「📡 看板开发中」。
> 目标：让所有已有子页面都能被 chip 点进去。
> ⏱️ 预计 30 分钟（主脑已定位根因并实测好解析器，你不用重查）。

---

## 0. 根因（主脑已定位，不用重查）

`index.html` 第 286-312 行的 `PAGE_MAP` 是**手写硬编码字典**，只有 **16 个铅(PB)条目**，铜/铝/五金属一条都没有。

```js
const PAGE_MAP = { 'PB_p1':'pb_21_price_structure.html', ... };   // ← 只有 16 条，全 PB
const key = cm.code+'_'+leaf.id;        // 例: 'CU'+'_p1' → 'CU_p1'
if(PAGE_MAP[key]){ window.location.href = PAGE_MAP[key]; return; }
// 其余 → 占位
document.getElementById('ph-note').textContent =
  '📡 '+cm.code+' '+leaf.name+' 看板开发中 · 参考铅(PB)库存看板模板';   // ← 其他品种全走这行
```

根因：**建页流程没同步 PAGE_MAP**。铜铝 agent 用 `build_cu_al_batch.py` 批量建了 56 页，没人回头挂跳转，字典还是 8 月初手写版。

**key 格式**：`<品种CODE>_<leaf.id>`，如 `CU_p1` / `AL_i3` / `PB_s8` / `LC_p1`。

> ⚠️ **坑1：碳酸锂的 code 是 `LC`，不是 `LI`**（实测 `tree_config.json`：`{'li':'LC'}`）。别手写成 LI。
> 全部 code：`CU AL PB ZN NI SN LC SI`

---

## 1. 文件名命名不统一（本任务最大坑，⚠️ 主脑已实测）

| 品种 | 命名规则 | 真实例子 |
|---|---|---|
| cu / al | `<var>_<节点号点转下划线>.html` | `cu_2_1.html`(2.1) / `cu_3_1_1.html`(3.1.1) / `al_4_3.html`(4.3) |
| pb 多数 | `<var><节点号去掉点>_<名称>.html` | `pb_21_price_structure.html`(2.1) / `pb_41_exchange_stock.html`(4.1) |
| pb 少数 | `<var><前两段>_<末段>_<名称>.html` | `pb_32_3_regen_supply.html`(3.2.3) |
| pb 少数 | `<var><节点号去掉点>_<名称>.html`（三级） | `pb_311_overseas_mine.html`(3.1.1) |

**结论：不要写死文件名，用解析器 + glob 兜底。** pb 内部两种风格并存（`pb_311` 无下划线 vs `pb_32_3` 有下划线），硬编码必错。

### 解析器（主脑实测：CU 20 / AL 25 / PB 30 = 75 条命中，与现有 76 页对齐）

```python
import json, glob, os

tree = json.load(open('data/tree_config.json'))
code_by_leaf = {(c['id'], ch['id']): ch['code']
                for c in tree['categories'] for ch in c['children']}
vars_ = {c['id']: c['code'] for c in tree['commodities']}

def resolve(var, code):
    """var='cu'/'al'/'pb'; code='3.2.3' → HTML 文件名或 None"""
    nocomma = code.replace('.', ''); us = code.replace('.', '_')
    for c in (f'{var}_{us}.html', f'{var}_{nocomma}.html'):
        if os.path.exists(c): return c
    for pat in (f'{var}_{nocomma}_*.html', f'{var}_{us}_*.html'):
        h = [x for x in sorted(glob.glob(pat)) if not x.endswith('_overview.html')]
        if len(h) == 1: return h[0]
    if code.count('.') == 2:          # 3.2.3 → pb_32_3_* 风格
        a, b, c = code.split('.')
        for pat in (f'{var}_{a}{b}_{c}_*.html', f'{var}_{a}{b}_{c}*.html'):
            h = [x for x in sorted(glob.glob(pat)) if not x.endswith('_overview.html')]
            if len(h) == 1: return h[0]
    return None
```

**主脑实测结果（你跑出来应该完全一致，不一致说明环境有问题，先停下报我）：**
```
CU: 命中 20
AL: 命中 25
PB: 命中 30
ZN/NI/SN/LC/SI: 各 0（五金属还没建页，属正常）
总计 75 条
```

---

## 2. 执行步骤

### Step 1：环境（2 分钟）
```bash
cd /home/ubuntu/framework-tree
git fetch origin && git rebase origin/main
python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print('指标数:', len(d['indicators']))"   # 必须 ≥ 786
bash scripts/bootstrap_agent.sh
```

### Step 2：生成映射（跑一遍，确认输出 = CU20/AL25/PB30）
```bash
python3 << 'PYEOF'
import json, glob, os
tree = json.load(open('data/tree_config.json'))
code_by_leaf = {(c['id'], ch['id']): ch['code'] for c in tree['categories'] for ch in c['children']}
vars_ = {c['id']: c['code'] for c in tree['commodities']}

def resolve(var, code):
    nocomma = code.replace('.',''); us = code.replace('.','_')
    for c in (f'{var}_{us}.html', f'{var}_{nocomma}.html'):
        if os.path.exists(c): return c
    for pat in (f'{var}_{nocomma}_*.html', f'{var}_{us}_*.html'):
        h = [x for x in sorted(glob.glob(pat)) if not x.endswith('_overview.html')]
        if len(h) == 1: return h[0]
    if code.count('.') == 2:
        a,b,c = code.split('.')
        for pat in (f'{var}_{a}{b}_{c}_*.html', f'{var}_{a}{b}_{c}*.html'):
            h = [x for x in sorted(glob.glob(pat)) if not x.endswith('_overview.html')]
            if len(h) == 1: return h[0]
    return None

from collections import Counter
lines, ok, miss = [], 0, []
for vid, vcode in sorted(vars_.items()):
    for (catid, leafid), code in sorted(code_by_leaf.items()):
        if catid == 'balance': continue          # 8.x 平衡板块不做图
        key = f'{vcode}_{leafid}'
        f = resolve(vid, code)
        if f: lines.append(f"         '{key}':'{f}',  // {code} {leafid}"); ok += 1
        else: miss.append((key, code, vid))
print('\n'.join(lines))
print(f"\n可挂 {ok} 条")
print("未命中品种分布:", dict(Counter(m[2] for m in miss)))
PYEOF
```

### Step 3：写入 index.html
- 用 Step 2 输出**整体替换** `index.html` 第 287-304 行的 `PAGE_MAP` 字典
- 保留原有 16 条 PB 的注释风格
- **只改 PAGE_MAP，别动 `selectChip` 任何其他逻辑**

### Step 4：验收（三道，全绿才算完成）
```bash
cd /home/ubuntu/framework-tree

# ① 死链检查：每个目标文件必须真实存在
python3 << 'PYEOF'
import re, os
html = open('index.html', encoding='utf-8').read()
m = re.search(r'const PAGE_MAP = \{(.*?)\};', html, re.S)
targets = re.findall(r":\s*'([^']+\.html)'", m.group(1))
bad = [t for t in targets if not os.path.exists(t)]
print(f"PAGE_MAP {len(targets)} 条, 死链 {len(bad)} 条")
for b in bad: print("  X", b)
PYEOF

# ② 覆盖率：现有非总览子页应 100% 被挂
python3 << 'PYEOF'
import re, glob
html = open('index.html', encoding='utf-8').read()
m = re.search(r'const PAGE_MAP = \{(.*?)\};', html, re.S)
targets = set(re.findall(r"'([^']+\.html)'", m.group(1)))
have = set(f for f in glob.glob('*.html')
           if not f.endswith('_overview.html')
           and not f.startswith('pb_stock') and f != 'index.html')
print(f"现有子页 {len(have)}, 已挂 {len(have & targets)}, 未挂 {len(have - targets)}")
for f in sorted(have - targets): print("  ! 未挂:", f)
PYEOF

# ③ 门禁
python3 scripts/check_html.py
node scripts/verify_render.js
python3 scripts/reclaim.py
```

**验收标准**：死链 = 0；未挂 = 0（若仍有未挂，应是 pb_stock_v2 归档页，在回传里说明）；门禁全绿。

### Step 5：STATUS.md + 提交
```bash
python3 << 'PYEOF'
path = "STATUS.md"
lines = open(path).read().split('\n')
for i, l in enumerate(lines):
    if l.startswith('| 2026-08-31'):
        lines.insert(i, '| 2026-08-31 | **[A-INDEX] 主看板chip跳转修复：PAGE_MAP 16→75 条，覆盖 cu/al/pb 全部子页（agent） | agent | 根因=PAGE_MAP 手写硬编码只挂铅(PB)；改为 glob 解析器覆盖三种命名风格（cu/al 下划线式、pb 无下划线式、pb 3.x.y 混合式）；死链 0 / 未挂 0 / 门禁全绿 | 线A |')
        break
open(path, 'w').write('\n'.join(lines))
PYEOF

git add index.html STATUS.md
git commit -m "[A-INDEX] 主看板chip跳转修复: PAGE_MAP 16→75 条覆盖cu/al/pb全部子页(glob解析器)"
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
```

---

## 3. 红线

1. ❌ **不碰 `data/indicators_v1.json`**（主脑独占，你改会覆盖五金属 590 条注册）
2. ❌ **不碰 `scripts/chart_kits.py` / `scripts/reclaim.py`**（公共模块，主脑独占）
3. ❌ **不碰 `scripts/api_cache.db`**，不 `git add -f` 提交 `*.db`
4. ❌ **不 `git checkout -f` / `git reset --hard`**
5. ❌ **只改 PAGE_MAP 字典**，不重写 `selectChip` 跳转机制
6. ❌ **不要给不存在的页面造占位链接**（点不开就点不开；8.x 平衡板块、pb_stock_v2 归档页本来就不该挂）
7. ❌ **不用 `git add .`**，只 `git add index.html STATUS.md`

---

## 4. 回传（照抄填）

```
主看板 chip 跳转修复完成：
- PAGE_MAP 从 16 条 → ? 条（预期 75）
- 覆盖：cu ? 页 / al ? 页 / pb ? 页（预期 20/25/30）
- 死链检查：? 条（必须 0）
- 未挂页面：? 条（及原因）
- 门禁：check_html ?/? / verify_render ?/? / reclaim ?/?
- commit hash：
- 若发现第三种命名风格（解析器漏掉的），列出来给我
```
