# 交接文档：B-LI-GAP 外科手术合并 + 后续收尾 · 2026-09-01

> **用途**：上下文过长换会话后，新 agent 直接按本文档续做，无需回忆旧会话。
> **项目**：`/home/ubuntu/framework-tree`（GitHub Pages 有色金属指标看板）
> **仓库**：`ssh://git@github.com/algo23-yunqingtian/framework-tree.git`
> **当前 main HEAD**：`a4a8bd0 [FIX-P1-P2-BATCH]`

---

## 一、背景（30 秒理解）

用户本地 Windows agent（B-LI-GAP）在分支 `task/li_gap_pages` 上做了**锂(LI) 缺口 14 节点建页**，push 了 2 commits 但**分支基线 stale**（停在 `c27d002`，比 main 早十几个 commit），不能直接 merge。

**我（主线 agent）已做的手术式合并**：从分支精确提取 14 页 HTML + 23 条指标，落到 main 工作区。

---

## 二、当前已完成（未 commit 未 push，git status 有 17 个改动）

```
M data/indicators_v1.json        # 786→809 (+23 LI 指标)
M scripts/check_html.py          # 已 +14 条 li_* 注册
M scripts/verify_render.js       # 已 +14 条 li_* 注册
?? li_2_3.html                   # 新增 14 页（已落地，未跟踪）
?? li_3_1_4.html ... li_7_2.html
```

**14 页内容**：li_2_3 / li_3_1_4 / li_3_1_5 / li_3_2_2 / li_4_5 / li_5_1 / li_5_2 / li_5_3 / li_6_1 / li_6_2 / li_6_3 / li_6_4 / li_7_1 / li_7_2

**23 条新增指标**：全为 Mysteel/知几 真实 zhiji_id（ID01551919 等），来源真实。

---

## 三、当前状态（**已全部完成并 push main**）

| 步骤 | 状态 |
|---|---|
| 14 页 HTML | ✅ 已落地，已 git tracked |
| `data/indicators_v1.json` | ✅ 809 指标（v3.45） |
| `scripts/check_html.py` | ✅ 已 +14 条注册 |
| `scripts/verify_render.js` | ✅ 已 +14 条注册 |
| `index.html` PAGE_MAP | ✅ 已 +14 条 LC_ 映射 |
| 页脚版本 | ✅ 14 页 `vv3.44` → `v3.45` |
| li_71/li_72 seasonal | ✅ 主图无季节按钮，seasonal 清空 |
| STATUS.md | ✅ 2 条记录 |
| commit + push | ✅ `6038233` + `a0e2f15` |

**三道门禁**：check_html 223/223 ✅ + verify_render 224/224 ✅ + reclaim 12/0 ✅

---

## 四、剩余工作

**主线收尾**（我本地，无需 agent）：
- [ ] 五金属 NI/SN/SI 剩余子页补建（~20 页，`build_5m_batch.py` 跑）
- [ ] 三表灌库（`db_import_jsonl.py + db_load.py`）

**待派 Windows agent**（需同花顺）：
- [ ] 铜 5 缺口节点（4.1/5.2/5.3/6.3/6.4）
- [ ] 铝 5 缺口节点（3.1.2/3.1.4/6.1/6.4/7.3）

### Step 1：补 index.html PAGE_MAP 14 条 LC_ 映射

`index.html` 目前**没有**任何 `LC_` 锂映射，主站点击锂板块叶子无法跳转。

**位置**：`index.html` 约第 338 行（`'CU_c3':'cu_7_3.html'` 附近，PAGE_MAP 字典内）。

**插入代码块**（14 行，直接加到 CU_c3 之后）：

```js
         'LC_p3':'li_2_3.html',   // 2.3 海外价格
         'LC_s4':'li_3_1_4.html', // 3.1.4 库存
         'LC_s5':'li_3_1_5.html', // 3.1.5 毛利
         'LC_s7':'li_3_2_2.html', // 3.2.2 产能利用
         'LC_i5':'li_4_5.html',   // 4.5 隐性在途
         'LC_d1':'li_5_1.html',   // 5.1 初级消费
         'LC_d2':'li_5_2.html',   // 5.2 终端消费
         'LC_d3':'li_5_3.html',   // 5.3 消费先行
         'LC_t1':'li_6_1.html',   // 6.1 原料进口
         'LC_t2':'li_6_2.html',   // 6.2 进出口
         'LC_t3':'li_6_3.html',   // 6.3 制品出口
         'LC_t4':'li_6_4.html',   // 6.4 全球出口
         'LC_c1':'li_7_1.html',   // 7.1 成本曲线
         'LC_c2':'li_7_2.html',   // 7.2 利润
```

**同时修 dynamic jump bug**：找到 `index.html` 里这句：
```js
if(!PAGE_MAP[key] && ['ZN','NI','SN','SI','LI'].indexOf(cm.code)>=0){
```
把 `'LI'` 加入数组（当前 main 可能缺 LI，需确认）；如果已经是 `cm.code` 就不用改。分支用了 `cm.id`，**确认哪个正确**——看 tree_config 的 LC leaf 定义：如果是 `id='li'` 就用 `cm.id`，如果 `code='LI'` 就用 `cm.code`。

### Step 2：更新 STATUS.md 近期变更记录

**位置**：`STATUS.md` 第 73 行「## 近期变更记录」表头下方第 2 行。

**插入 1 行**（前缀 `[B-LI-GAP]`）：

```
| 2026-09-01 | **[B-LI-GAP] 锂缺口14节点建页合并** | 主脑 | **来源**：Windows agent 分支 `task/li_gap_pages`（2 commits，分支基线 stale，外科手术合并）。**页面**：14 页 li_2_3/3_1_4/3_1_5/3_2_2/4_5/5_1/5_2/5_3/6_1/6_2/6_3/6_4/7_1/7_2 全真数据（1-2图/页，note+nav+footer齐全）。**指标**：indicators_v1.json 786→809（+23 LI 指标，全 Mysteel/知几 zhiji_id，v3.43→v3.45）。**门禁注册**：check_html + verify_render 各 +14 条。**待做**：index.html PAGE_MAP 14 条 LC_ 映射 + 主站 dynamic jump LI 加入白名单。|
```

### Step 3：git add + commit + push

```bash
cd /home/ubuntu/framework-tree
git add -A
git commit -m "[B-LI-GAP] 锂缺口14节点建页合并: 14页全真数据+23指标(v3.45)+check_html/verify_render注册+index.html PAGE_MAP"
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
```

### Step 4：三道门禁验证

```bash
python3 scripts/check_html.py 2>&1 | tail -4    # 期望 223/223 PASS（209+14）
node scripts/verify_render.js 2>&1 | tail -4     # 期望 224/224 ALL PASS（210+14）
python3 scripts/reclaim.py 2>&1 | tail -4        # 期望 PASS=12 FAIL=0
```

如果 FAIL，用 `--file` 参数定位：
```bash
python3 scripts/check_html.py --file li_2_3.html
```

### Step 5：重拉 LI 缓存验证时序真实（可选但推荐）

```bash
python3 scripts/refresh_cache.py --metrics 'li_' 2>&1 | tail -20
```

---

## 四、验收标准（新 agent 自检用）

| 项 | 标准 | 命令 |
|---|---|---|
| 14 页存在 | 全部 li_*.html 文件在 git tracked | `git ls-files li_2_3.html li_7_2.html` |
| 14 页质量 | 每页 1-2 图，有 chart-note，无跨品种串台 | 抽查 `head -50 li_5_1.html` |
| 指标数 | indicators_v1.json 共 809 条 | `python3 -c "import json; print(len(json.load(open('data/indicators_v1.json'))['indicators']))"` |
| check_html 注册 | 14 条 li_* 在 PAGES 里 | `grep -c '"li_23"\|"li_72"' scripts/check_html.py` 应=2 |
| verify_render 注册 | 同上 | `grep -c "key: 'li_23'\|key: 'li_72'" scripts/verify_render.js` 应=2 |
| PAGE_MAP | index.html 含 14 条 LC_ | `grep -c "'LC_" index.html` 应=14 |
| 门禁 | 三道全 PASS | 见 Step 4 |

---

## 五、已知坑（必读）

1. **分支基线 stale 教训**：任何分支开工前必须 `git fetch && git rebase origin/main`，否则直接 merge 会 10 万行删除
2. **pre-commit 钩子**：改产物不改 STATUS.md → commit 被拦；写 STATUS 后再 commit
3. **14 页图数偏少**（1-2 图）：同花顺发散数据量有限，属正常；后续同花顺 agent 可补
4. **li 页 cid 命名**：`echart_li_23_c1`（压缩式无下划线），与 check_html 其他条目一致
5. **API 缓存不入 git**：23 条 LI 时序在 api_cache.db，分支未推，本机的 `scripts/refresh_cache.py --metrics li_` 可重建

---

## 六、后续任务（P1 主线 + P2 子代理）

完成 LI 合并后，按原计划：

| # | 任务 | 量 | 谁做 |
|---|---|---|---|
| 1 | 五金属 NI/SN/SI 剩余子页补建 | ~20 页 | 我（本地 `build_5m_batch.py`） |
| 2 | 三表灌库（indicator_meta/series） | 一次性 | 我（本地 `db_import_jsonl.py + db_load.py`） |
| 3 | 铜 5 缺口节点（4.1/5.2/5.3/6.3/6.4） | 5 节点 | Windows agent（需同花顺） |
| 4 | 铝 5 缺口节点（3.1.2/3.1.4/6.1/6.4/7.3） | 5 节点 | Windows agent（需同花顺） |

**同花顺 agent 任务卡待写**：见 Step 7。