# 双 Agent 并行协作协议（2026-08-31 事故后制定）

> 本协议由一次真实事故触发。事故复盘见下方「§0」，所有条款都有对应教训。
> **任何在本仓库干活的 agent，开工第一件事是读 §2 的开工检查，30 秒。**

---

## §0 事故复盘：两个 agent 共用一个 checkout 目录

**时间线（2026-08-31）**

| 时刻 | 事件 |
|---|---|
| T+0 | 我在 `task/cu_price` 工作树里改了 `data/indicators_v1.json`（162→179 条）+ `scripts/build_cu_al_batch.py`，未提交 |
| T+10min | 另一个 agent 在同一 `/home/ubuntu/framework-tree` 目录 `git checkout main` + commit `c2d1595 [B-5M-Step1merge]`（五金属 Step1/2 合并） |
| T+10min | 我的**已跟踪文件改动被 main 版本覆盖，全部丢失**：指标注册、引擎的 MAIN_METRIC/comm_only/is_stale 三项改进 |
| T+10min | 幸免的是：`scripts/api_cache.db`（不被 git 跟踪，163 行数据全在）+ untracked 的 `al_2_*.html`（工作树清理没删） |
| T+15min | 我用 `git worktree add` 建了隔离工作树重放全部改动 |

**reflog 证据**
```
c2d1595 HEAD@{0}: checkout: moving from task/cu_price to main   ← 不是我切的
3a22c9e HEAD@{1}: checkout: moving from main to task/cu_price
c2d1595 HEAD@{2}: commit: [B-5M-Step1merge] 五金属Step1/Step2产物合并进main
```

**根因**：`AGENTS.md` §2 早就写了「跨服务器并行必须走 git 分支」，但**两个 agent 都在同一台机器上，共用同一个 working directory**。文件锁（`file_write_lock.py`）只管同服务器同目录的写权限，管不住 `git checkout` 把别人的未提交改动清掉。**分支隔离保护的是 commit 之间的合并冲突，不是 checkout 造成的文件覆盖。**

**丢失内容清单**（已全部重放恢复）

| 丢失项 | 恢复方式 |
|---|---|
| `indicators_v1.json` 17 条新增/重定向（162→179） | 重放脚本 |
| `build_cu_al_batch.py` 的 MAIN_METRIC / comm_only / is_stale / THEME_BY_COMM | 重放补丁 |
| `scripts/pull_al_2x_cache.py` 数据溯源脚本 | 重写（缓存数据本身在 db 里没丢） |
| `STATUS.md` 变更记录 | 重写 |

---

## §1 协议核心：目录隔离，不是分支隔离

**一句话**：每个 agent 一个 `git worktree` 目录，共享一个仓库、共享缓存 DB，**永不切换分支、永不 checkout**。

```
/home/ubuntu/framework-tree/          ← 主工作树（主脑专用，main）
/home/ubuntu/framework-tree-cu/       ← worktree（task/cu_price）
/home/ubuntu/framework-tree-5m/       ← worktree（task/multi_metals）
/home/ubuntu/framework-tree-pb/       ← worktree（task/pb_xxx）
```

- 所有 worktree 共享同一个 `.git`，提交互不干扰，`git log` 都能看到。
- 别人切分支不会动你的目录——**这是唯一真正管用的隔离**。
- 缓存 `scripts/api_cache.db` 不推 GitHub，用 symlink 共享一份，避免各目录数据不一致：
  ```bash
  git worktree add /home/ubuntu/framework-tree-<任务> <branch>
  ln -sf /home/ubuntu/framework-tree/scripts/api_cache.db \
         /home/ubuntu/framework-tree-<任务>/scripts/api_cache.db
  ```

**不要做的事**
- ❌ 在别人的工作树里 `git checkout` / `git pull` / `git reset`
- ❌ 在别人的工作树里 `git add` / `git commit`（会连带提交对方的未提交改动）
- ❌ 直接 `rm` 别人的 untracked 文件（本事故中 untracked 的 HTML 是唯一幸存资产）
- ❌ 改 `scripts/api_cache.db` 以外的共享文件而不走自己的 worktree

---

## §2 开工检查（30 秒，强制执行）

每次开工前跑这一段，能挡掉 90% 的冲突：

```bash
# 1) 我是不是在属于自己的工作树里？
pwd                                          # 必须是 /home/ubuntu/framework-tree-<我的任务>
git branch --show-current                   # 必须是 task/<我的分支>

# 2) 别人的分支有没有被我踩到？（worktree 列表）
git worktree list
#   输出里出现 /home/ubuntu/framework-tree 且不在我名下 → 停手，那是主脑的

# 3) 基线是不是最新的？（旧基线=merge 冲突面扩大）
git fetch origin
git log --oneline origin/main..HEAD | wc -l   # 我的领先数
git log --oneline HEAD..origin/main | wc -l   # main 领先数，>0 需考虑 rebase

# 4) 公共真源当前的指标数（少了=基线旧）
python3 -c "import json;d=json.load(open('data/indicators_v1.json'));print(len(d['indicators']),d['version'])"

# 5) 工作区是不是干净的？（有别人的未提交改动=不要动）
git status -s
#   出现不是我创建的 M/?? 文件 → 停手，问主脑
```

---

## §3 提交纪律：别让未提交文件活过 15 分钟

本事故中丢失的所有内容都是「改了没提交」的状态。**worktree 隔离能防别人的 checkout，但不能防你自己的工作被自己遗忘。**

规则：
1. **每 15 分钟或每完成一个可独立验证的子步骤就 commit**。commit message 前缀沿用 `[T14-*]` / `[B-*]` / `[A]` / `[DOC]`。
2. 单个 commit 只干一件事（一次指标注册、或一次建页、或一次引擎修复）。这样丢了能精确定位。
3. `git commit` 之后**立刻 `git push` 到自己的 `task/*` 分支**——远端是最终保险，本地 commit 也会因误操作丢失。
4. 长任务（>1 小时）先写 `output/HANDOVER_<任务>_<日期>.md` 交接文档，写完就 commit。

---

## §4 公共文件所有权

| 文件 | 谁能改 | 规则 |
|---|---|---|
| `data/indicators_v1.json` | 各 agent 可在自己分支改 | **必须只追加，不删不改既有条目**；版本号单调递增；冲突时以「追加条目数多 + version 新」为准 |
| `data/tree_config.json` | 主脑 | 节点定义唯一真源，其他 agent 只读 |
| `scripts/chart_kits.py` | 主脑 | 公共图表库，改动走 PR |
| `scripts/build_cu_al_batch.py` | 铜铝任务 agent | 品种专属引擎，可随分支演进 |
| `scripts/check_html.py` / `verify_render.js` | 谁加页谁注册 | **追加条目，不改既有**；key 必须带品种前缀（见 §5） |
| `STATUS.md` | 所有 agent | 只往「变更记录」表顶部追加一行，不编辑他人行 |
| `scripts/api_cache.db` | 所有 agent（symlink 共享） | INSERT OR REPLACE 各自 metric，不删他人行 |

**追加不覆盖原则**是本仓库最重要的协作约定——本事故的引擎里「按指标条数投票判主品种」曾把铜 `cu_2_3/cu_2_4/cu_2_5` 三个已验收页面覆盖成铝数据，就是因为把「判定」做成了会覆盖既有产物的行为。

---

## §5 门禁 key 命名（防撞名）

门禁注册文件里出现过裸 key（铜 2.2-2.6 用 `"2.2"` 这种），导致铝 2.2 页注册时撞名。

规则：
- `check_html.py` 的 PAGES key **必须带品种前缀**：`"cu_2_2"` / `"al_2_2"` / `"pb_2_2"`
- `verify_render.js` 的 key 同上：`'al_22'` / `'cu_22'`
- 铅的历史裸 key（`"21"`/`"22"`）保留不动（无冲突），新条目禁止再裸写
- 图表 cid 同理必须带品种：`echart_al_21_c1` 而非 `echart_21_c1`（否则与铅页 resize 串台）

---

## §6 发现别人踩了怎么办

按顺序处理，不要自作主张：

1. **先确认是自己的改动丢了还是别人的**：
   ```bash
   git reflog -10 | cat        # 看谁什么时候切的分支
   git fsck --no-reflogs --lost-found   # 未提交的已跟踪改动一般找不回
   ```
2. **判断能否重放**：untracked 文件 + 缓存 DB + 我的脚本/参数都在 → 重放（本事故就是这样恢复的）。
3. **无法恢复的**：立刻在 `STATUS.md` 变更记录写一行事故说明，告知主脑，不要静默补写假装无事。
4. **不要**去改别人的 commit、不要 `git reset --hard` 共享目录、不要替对方提交。

---

## §7 给主脑的建议（治理层面）

1. 给每个 agent 分配固定工作树目录名（`framework-tree-<品种或任务>`），写进各自的任务卡。
2. 任务卡里强制加「开工检查 5 条」（§2）作为第一行。
3. `reclaim.py` 的提交前缀白名单目前只有 `[A]/[B]/[DOC]`，但实际全在用 `[T14-*]`，建议补上 `[T14-*]` 前缀族，否则每次回收都带一个假 FAIL。
4. 共享缓存 DB 建议加一个 `meta` 表记录「谁在什么时候写了哪条 metric」，方便溯源。

---

## §8 本次事故后我实际采用的目录

```
/home/ubuntu/framework-tree-cu/     ← 铜铝 PR #1（task/cu_price），本文作者
```

其他 agent 请建自己的目录，别进这个。
