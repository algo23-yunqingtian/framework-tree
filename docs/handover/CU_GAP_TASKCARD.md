# 铜(CU)剩余节点建页 · 任务卡（零基础可做）

> 你是新来的 agent，**不需要懂期货**。按本文档一步步做，产出与既有页面同一标准。
> 完成时间目标：5 个节点，每个 1-2 小时。
> 有不懂的名词看本文档「名词速查」（第 9 节），不要自己猜。

---

## 0. 你要做什么（一句话）

给**铜(CU)**这个品种做 **5 张看板子页面**，每页展示几个和铜有关的**数字指标**（库存、成本、利润）的**折线图**。

5 张页面和它们的主题：

| 节点号 | 页面主题 | 看什么 |
|---|---|---|
| **cu_4_4** | 工厂库存 | 铜加工企业的库存水平（月/周） |
| **cu_4_5** | 隐性/在途库存 | 看不见的库存（在途、贸易商）（周/月） |
| **cu_7_1** | 成本曲线与分位 | 全行业成本分布，铜价在成本线什么位置 |
| **cu_7_2** | 日度利润测算 | 每天测算的冶炼利润 |
| **cu_7_3** | 能源/原料成本 | 电力、原料成本（先行指标） |

---

## 1. 环境（10 分钟，一次性）

```bash
# ① 进项目
cd /home/ubuntu/framework-tree
git fetch origin && git rebase origin/main
# ② 核验基线：下面必须输出 ≥ 786
python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print('指标数:', len(d['indicators']))"
# ③ 装协作 hook（一次）
git config core.hooksPath scripts/hooks
# ④ 跑上线自检（全绿才开工）
bash scripts/bootstrap_agent.sh
```

⚠️ **如果 ② 输出 < 786**：先 `git fetch origin && git rebase origin/main` 再核验，还不行就停下来问主脑。**基线旧直接开工 = 会覆盖别人的工作**（2026-08-31 刚出过事故，丢 590 条）。

---

## 2. 每一步怎么做（照抄）

### Step 1：找到这 5 个节点有哪些指标（约 30 分钟）

这 5 个节点的指标清单**已经在你拉下来的数据里**，不用自己发明。先查：

```bash
python3 << 'PYEOF'
import json
d = json.load(open('data/indicators_v1.json'))['indicators']
# 找 cu_ 开头、且 _nodes 含 4.4 / 4.5 / 7.1 / 7.2 / 7.3 的指标
want = ['4.4', '4.5', '7.1', '7.2', '7.3']
for key, meta in sorted(d.items()):
    if not key.startswith('cu_'):
        continue
    nodes = meta.get('_nodes') or []
    hit = [n for n in nodes if n in want]
    if hit:
        print(f"{key}\t{meta.get('name')}\t{meta.get('ids', {}).get('CU')}\t单位={meta.get('unit')}")
PYEOF
```

**得到每个节点的候选指标列表后**，每个节点按「1 个正主 + 0~2 个辅助」挑，规则：

| 规则 | 做法 |
|---|---|
| **正主贴合节点** | 4.4 正主 = 工厂/厂内库存；4.5 = 在途/隐性库存；7.1 = 成本曲线；7.2 = 冶炼利润；7.3 = 电力/原料价。用指标名里的词对照节点主题 |
| **优先有数据** | 同一节点多个候选，优先选 `api_cache.db` 里有数据的（下一节会验证） |
| **不要用其他页面的正主** | 查一下：`grep -rl "load_metric(\"<该指标key>\"" scripts/*.py`，如果已经在别的 build 脚本里用了，就别当正主，只做辅助 |

### Step 2：验证数据真的存在（每个节点 2 分钟）

```bash
python3 << 'PYEOF'
import sqlite3
c = sqlite3.connect('scripts/api_cache.db').cursor()
# 把上面查到的 cu_ 指标 key 填进这里，逐个验证
for key in ['cu_44_xxx', 'cu_45_yyy', 'cu_71_zzz']:   # ← 替换成你 Step1 找到的真实 key
    r = c.execute('SELECT metric, zhiji_id FROM indicator_cache WHERE metric=? AND code=?', (key, 'CU')).fetchone()
    print(key, '->', '有数据 ✓' if r else '无数据，换一个指标')
PYEOF
```

> **原则**：优先选有数据的指标。某个节点候选全部无数据 → 该节点先跳过，在交付报告里写「无数据，待外部源」，**不要硬造数据**。

### Step 3：建页面（用现成引擎，30 秒）

```bash
cd /home/ubuntu/framework-tree
python3 scripts/build_cu_al_batch.py 4.4 4.5 7.1 7.2 7.3
```

这个引擎会自动：读指标 → 画折线图（含季节视图切换）→ 生成 `cu_4_4.html` / `cu_4_5.html` / `cu_7_1.html` / `cu_7_2.html` / `cu_7_3.html` 到仓库根目录。

**如果某节点引擎没生成**（可能是指标缺失）：
```bash
python3 scripts/build_cu_al_batch.py 4.4 --dry   # 看它为什么跳过
```

### Step 4：跑门禁（必须全绿）

```bash
cd /home/ubuntu/framework-tree
python3 scripts/check_html.py          # 静态校验
node scripts/verify_render.js          # 渲染校验（需 node）
python3 scripts/reclaim.py             # 格式契约
```

- `check_html.py` 报 FAIL → 看输出，通常是要在脚本顶部 `PAGES` 列表里注册新页面（照已有 cu_ 页面抄）
- `verify_render.js` 报 FAIL → 同样在 `PAGES` 里加 `{key: 'cu_44', file: 'cu_4_4.html', seasonal: ['echart_cu_44_c1', ...]}`，cid 从生成的 HTML 里抄（搜 `echart_cu_44`）
- `reclaim.py` 的 FAIL 如果是 `[FIX-]` 前缀误判，忽略（已知 bug，见第 7 节）

### Step 5：更新 STATUS.md + 提交

```bash
cd /home/ubuntu/framework-tree
git status -s          # 确认只有你的 cu_*.html / build 脚本 / STATUS.md 变化
```

然后在 `STATUS.md`「近期变更记录」表格**最上面插入一行**（照已有行抄格式）：
```
| 2026-08-31 | **[CU-GAP] 铜4.4/4.5/7.1/7.2/7.3 建页上线**（agent） | agent | 做了什么、几个图、门禁结果 | 线B |
```

提交（**只能加你这些文件**，不要 `git add data/indicators_v1.json` 或别人的文件）：
```bash
git add cu_4_4.html cu_4_5.html cu_7_1.html cu_7_2.html cu_7_3.html scripts/ STATUS.md
git commit -m "[CU-GAP] 铜4.4/4.5/7.1/7.2/7.3 建页"
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
```

> ⚠️ pre-commit hook：如果你改了 `*.html/*.py/data/*.json` 但没动 `STATUS.md`，会被拦。所以**先改 STATUS.md 再提交**。改 STATUS.md 用 `python3` 拆行（见第 8 节），别用普通编辑器。

---

## 3. 交付报告（做完发主脑）

把以下内容发给主脑：

```
铜 5 节点建页完成：
- 每个节点用了哪些指标（key + 名称）
- 各页几幅图
- 门禁结果（check_html X/X, verify_render X/X）
- 跳过节点及原因（如无数据）
- git commit hash
```

---

## 4. 红线（违反 = 丢数据）

1. ❌ **不碰 `data/indicators_v1.json`**（指标元数据，主脑独占）
2. ❌ **不碰 `data/tree_config.json` / `scripts/chart_kits.py` / `scripts/reclaim.py`**（公共模块，主脑独占）
3. ❌ **不 `git add -f` 提交 `*.db`**（gitignore 已拦，别用强推）
4. ❌ **不造数据**：知几无序列的指标，宁可不上图也不编数值
5. ❌ **不 `git checkout -f` / `git reset --hard`**：会把别人未提交的改动抹掉
6. ❌ **不用 f-string 写 JS**：脚本里写 JS 模板用 `%` 格式化 + `%%` 转义

---

## 5. 通用命令速查

```bash
python3 ~/.hermes/scripts/zhiji_api.py search "铜 社会库存"   # 搜指标（关键词空格分隔）
python3 ~/.hermes/scripts/zhiji_api.py series <id> 2015-01-01 2026-08-31   # 取时序
python3 scripts/refresh_cache.py --metrics <key>   # 拉数入库
```

---

## 6. 参考文件

| 文件 | 用途 |
|---|---|
| `data/tree_config.json` | 节点权威定义（4.4/4.5/7.x 的 name + q） |
| `data/indicators_v1.json` | 指标元数据（786 条，含节点归属 `_nodes`） |
| `scripts/api_cache.db` | 已拉数据缓存 |
| `scripts/build_cu_al_batch.py` | **建页主引擎**（用法看文件头部注释） |
| `scripts/chart_kits.py` | 图表公共库（只读，别改） |
| `scripts/check_html.py` / `verify_render.js` / `reclaim.py` | 三道门禁 |
| `cu_2_1.html` | 样板页（看它的结构，你的页面应长这样） |

---

## 7. 已知坑

| 坑 | 解法 |
|---|---|
| check_html/verify_render 报新页面没注册 | 在脚本顶部 `PAGES` 列表加你的页面（照抄既有 cu_ 条目） |
| reclaim.py FAIL=1 且是 `[FIX-]` 前缀 | 已知误判（白名单漏 `[FIX-`），忽略，不是你的错 |
| `search` 返回杂项 | 关键词必须空格分隔："铜 社会库存" ✓，"铜社会库存" ✗ |
| HTTP 429「总配额已用尽」 | 停手报主脑，别反复重试 |
| 页面字节数异常小 | 数据可能没拉全，重跑 `refresh_cache.py --metrics <key>` |

---

## 8. 改 STATUS.md 的正确姿势

```python
# 在项目根目录跑
python3 << 'PYEOF'
path = "STATUS.md"
lines = open(path).read().split('\n')
# 找到「近期变更记录」标题行
idx = next(i for i, l in enumerate(lines) if l.startswith('| 2026-08-31'))
new_row = "| 2026-08-31 | **[CU-GAP] 铜4.4/4.5/7.1/7.2/7.3 建页上线**（agent） | agent | 内容 | 线B |"
lines.insert(idx, new_row)
open(path, 'w').write('\n'.join(lines))
# 检查有没有字面 \n 污染
print([i+1 for i, l in enumerate(lines) if '\\n' in l] or "无")
PYEOF
```

---

## 9. 名词速查（不懂就查这里）

| 词 | 意思 |
|---|---|
| **指标** | 一个可量化的数字序列，如"铜社会库存（万吨）"，每天/周/月一个数 |
| **节点** | 看板的一个板块，如 4.4=工厂库存。每个节点一张页面 |
| **正主** | 该页面最核心的指标（每页 1 个），其他都是辅助 |
| **折线图** | 横轴时间、纵轴数值的曲线 |
| **季节视图** | 同一张图按"历年同期"叠加展示（看周期性） |
| **api_cache.db** | 本机已下载的数据缓存，页面从这读数据 |
| **门禁** | 三道自动检查，全绿才算合格（质量关卡） |
| **git rebase / push** | 把别人的最新改动合并进来 / 把你的改动上传 |
| **基线** | 你开工时仓库的最新状态。基线旧=没跟上最新，会覆盖别人 |
| **知几 API** | 数据供应商（SMM/Mysteel 等）的查询接口 |
| **SMM / Mysteel / LME / SHFE** | 数据机构名（SMM=上海有色网，Mysteel=钢联，LME=伦敦金属交易所，SHFE=上期所） |
