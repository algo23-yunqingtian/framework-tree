# AGENTS.md · framework-tree 新 Agent 入职总入口

> 你是新加入的 agent。**先读本文件**，然后严格按本文档顺序执行。
> 目标：不问我、不看旧会话，仅凭本文档 + 仓库内文档，产出与既有页面**同一标准**的成果。

---

## 0. 快速判断你该做什么（30 秒）

| 你想做的 | 归属 | 入口 |
|---|---|---|
| 做**新品种**看板（铜/铝/锌/镍/锡/锂/硅） | 指标录入线 | `docs/COLLABORATION_PLAYBOOK.md` 第3章 |
| 做**铅的下一板块**（供给/需求/成本利润/供需平衡） | 同上 | 同上 + `STATUS.md` 卡点区 |
| 改**前端页面**（样式/图表/跳转） | 架构线 | 同上第3章 + `scripts/chart_kits.py` |
| 只想知道**现状** | — | `STATUS.md`（唯一真源） |

---

## 1. 必读顺序（不许跳步，读完全部再动手）

```
1. 本文件 AGENTS.md
2. STATUS.md              ← 当前进度 + 谁负责什么（唯一真源）
3. docs/COLLABORATION.md  ← 两条线隔离机制（防止覆盖别人的工作）
4. docs/COLLABORATION_PLAYBOOK.md  ← 全流程 11 章（核心！含格式契约/坑速查）
5. README.md              ← 项目一句话
```

**严禁**：不读 STATUS.md 直接改代码 = 可能覆盖别人成果，会被文件锁拒写。

---

## 2. 目录写权限 + 并行安全

**同服务器**：文件锁强制隔离
- **线A（架构/前端）**：只能写 `framework-tree/`
- **线B（指标/数据）**：只能写 `analysis/` 下目录
- 写文件前必须拿锁，写完释放：
```bash
python3 ~/.hermes/scripts/file_write_lock.py acquire /home/ubuntu/framework-tree agent:<你的标识>
# ... 工作完成后 ...
python3 ~/.hermes/scripts/file_write_lock.py release /home/ubuntu/framework-tree
```
- 拿不到锁 = 有人在写，等待再试。

**跨服务器并行（重要）**：文件锁只在本机 `/tmp` 生效，**不同机器之间无效**。所以跨服务器协作必须走 **git 分支**：
- 每个任务单独建分支：`git checkout -b task/<品种>_<板块>`（如 `task/cu_price`）
- 在你的分支上开发、提交，**不要直接 push 到 main**
- 完成后开 PR：`gh pr create --fill`，由主脑 review 后 merge
- 分支前缀规范：`task/` 个人任务、`feature/` 功能开发

**冲突预防**：
- 改公共文件（`STATUS.md`/`chart_kits.py`/`indicators_v1.json`）前，先 `git pull` 看主脑最近改动
- 同时改同一文件 = 必然冲突，先问主脑或走 PR 合并
- `chart_kits.py` 公共模块只有主脑能改，其他人只能在分支上提 PR

**开工前基线同步（强制，犯过错的教训）**：
```bash
git fetch origin
git rebase origin/main          # 必须做！否则你的指标表/页面会缺 main 已有的东西
python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print('指标数:', len(d['indicators']))"
# 指标数必须 ≥ main 的 78（以 STATUS.md 最新记载为准）；少了 = 基线旧，先 rebase
```
- 分支基线必须是最新 main，禁止基于旧 commit 直接开工（实测教训：分支停在旧 main 会缺 5 个 j323_* 指标、diff 巨大、merge 冲突面扩大）
- 每一次新任务开始前重复上述步骤

---

## 3. 质量门禁（产出必须全绿才算完成）

```bash
# 1) 静态校验
python3 scripts/check_html.py
# 2) 渲染校验（需 node）
node scripts/verify_render.js
# 3) 格式契约 + 产物完整性（提交前最后一道）
python3 scripts/reclaim.py
```
三道全 PASS 才算完成。任何 FAIL 都要修复后重跑，不许带病提交。

### 3.5 指标取舍 5 规则（发散/验证/建页通用，做任何品种任何板块都适用）

同花顺发散返回常有重复指标、跨板块指标。按以下规则取舍，**不要静默丢弃**：

| # | 规则 | 动作 |
|---|---|---|
| 1 | **归属优先** | 指标必须落在本子节点边界内（以 tree_config.json 该节点 q 字段+板块定义为准）；跨类指标→剔除放备用库 |
| 2 | **去重** | 同一指标出现在多张图（时序/季节/占比）→ 保留信息量最大的图，其余作该图组成 |
| 3 | **数据可得性** | 同花顺推荐 ≠ 知几一定有序列。优先选知几能搜到、有连续序列的；搜不到的进备用库标「待外部源」 |
| 4 | **正主 vs 辅助** | 每子节点 1 个正主指标，其余作辅助/交叉验证，不喧宾夺主 |
| 5 | **产出可查** | 剔除项必须在发散记录 md 的「排除项」栏写明为何剔除，供后续回溯 |

**正主防串用（强制）**：做任何节点前，先查这个指标是否已经是**其他页面**的正主（grep 已有 build 脚本 / 已发布 HTML 的指标 ID）。已在别页做正主的指标（如 i18 铅锭社库=4.3 正主、j25_tc=2.5 正主）**禁止在本页重复当正主**，只能作辅助交叉或进备用库。正主必须贴合本节点 tree_config 的 q 字段定义（例：5.1 q=开工率·同步 → 正主应为铅酸电池开工率，不是表观消费）。

> 完整方法论见 `pb_prompt/batch/PB_库存_v19.md` 规则3（题材对象一致原则）+ 规则7（边界归属提示）；备用库生命周期规范见 `pb_prompt/Pb_看板指标定稿_v2.md`。

---

## 4. 回传协议（做完必须回传，主脑一键回收）

1. 更新 `STATUS.md`「近期变更记录」+ 对应待办区，**30 秒内** `git commit + push`
2. commit 前缀规范：代码 `[A]` / 任务 `[Txx]` / 数据 `[B]` / 文档 `[DOC]`
3. push 命令（Pages 有限频）：
```bash
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
```
4. 主脑跑 `python3 scripts/reclaim.py` 校验 → 全 PASS 后 merge 你的产出。

> **🚨 pre-commit 强制（2026-08-31 上线）**：改产物文件（`*.html/*.py/*.js`/`data/*.json`）但没动 `STATUS.md` 会被 hook 拦截。
> 安装（clone 后一次）：`git config core.hooksPath scripts/hooks`。
> 逃生通道：确属无需记录时 `git commit --no-verify`。别滥用——主脑会看到变更记录缺失。

**任务可见性**（主脑怎么知道新 agent 在做什么）：
1. `STATUS.md` 是唯一真源——他每完成一项必须写变更记录
2. `git log origin/main` 看提交历史 = 他改了什么、什么时间
3. 跑 `python3 scripts/reclaim.py` 自动输出任务语义标注（哪个品种/板块 + 前缀统计）
4. 若他在自己的 `task/*` 分支上开发，主脑看 PR 列表 + `git log <branch>` 即可

---

## 5. 常用命令速查

```bash
# 搜知几数据库（命中阈值 score≥12=A / 6-11=B / <6=C）
python3 ~/.hermes/scripts/zhiji_api.py search "新加坡 铅 仓单"
python3 ~/.hermes/scripts/zhiji_api.py series a10193708 2015-01-01 2026-08-29

# 拉数据入库（1秒限频，自动写 api_cache.db）
python3 scripts/refresh_cache.py

# 重建全部页面
for f in scripts/build_pb_*.py; do python3 "$f"; done

# 本地预览
python3 -m http.server 8786
```

---

## 6. 关键路径

| 文件 | 用途 | 谁能改 |
|---|---|---|
| `data/indicators_v1.json` | 指标元数据唯一真源 | 主脑合并 |
| `data/tree_config.json` | 目录树配置 | 线A |
| `scripts/chart_kits.py` | 图表公共模块 | **只有主脑能改** |
| `scripts/reclaim.py` | 一键回收校验 | 主脑 |
| `scripts/api_cache.db` | SQLite 缓存（不推 GitHub） | — |
| `STATUS.md` | 全局状态唯一真源 | 所有人（拿锁） |

---

## 7. 硬性红线

- ❌ 不推 `*.db` / `*.pyc` / `.env` 到 GitHub
- ❌ 不在公开页暴露知几 API key（key 在 `~/.hermes/scripts/zhiji_api.py`，不进仓库）
- ❌ 不经主脑允许改 `chart_kits.py` 公共模块
- ❌ 用 f-string 写 JS 模板（必须 `%` 格式化 + `%%` 转义）
- ❌ 看完 STATUS.md 前动手写代码

---

## 8. 当前进度快照（2026-08-31 06:30，详见 STATUS.md 近期变更记录）

**全库：94 页 / 指标 196（v3.42）/ 门禁 75/75 + reclaim 12/0 / 死链 0**

| 品种 | 上线板块 | 说明 |
|---|---|---|
| 铅(PB) 37页 | 价格2(6节点)/库存4.1/供给3.x/需求5.3/成本7.x + 进出口6.1-6.4 | 老牌完整，多为 3 图真数据页 |
| 铜(CU) 25页 | 3.x供给 + 4.2/4.3库存 + 5.1需求 + 6.1/6.2进出口 + 总览 | 缺口：4.1/4.4/4.5/5.2/5.3/6.3/7.x 待外部源 |
| 铝(AL) 31页 | 2.x价格 + 3.x供给 + 4.x库存全 + 5.x需求 + 6.3 + 7.x + 总览 | 缺口：6.1/6.2/6.4/7.3 待外部源 |

- ⚠️ **知几 API 配额已耗尽（10000 次/2026-08-31）**：`zhiji_api.py` search/series 全返 429，`refresh_cache.py` 失效。**数据类任务全部阻塞**，需充值或换源后再做。
- ⏳ 三表灌库（indicator_meta/series）设计已定（`analysis/spec/db_design.md`），待五金属注册后执行
- ⏳ 五金属（ZN/NI/SN/SI/LI）Step3 产物已落盘（`analysis/iwencai/step3_final_5m.json`，138节点），待注册指标 + Step4 建页
- 🚨 **协作机制（2026-08-31 加固）**：`git config core.hooksPath scripts/hooks` 后，改产物不写 STATUS.md 会被 pre-commit 拦截
