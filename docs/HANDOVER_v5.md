# 交接文档 v5 · 2026-08-31 07:00 · framework-tree 主脑会话收尾

> 上一轮主脑会话（v4 交接）已完成：口径串台修复 + 总览页补齐 + 协作机制加固。
> 所有数字经 `framework-tree/` checkout 实测，非推断。HEAD 已推送。

---

## 0. 一句话现状

**HEAD = origin/main = `1cb547e`（已推送）。工作区干净（git status 空）。94 页 / 指标 196（v3.42）/ 门禁 75/75 + reclaim 12/0 / 死链 0。知几 API 配额已耗尽（10000 次），数据类任务全阻塞。**

---

## 1. 已核实事实（全部实测）

| 项 | 值 |
|---|---|
| HEAD / origin/main | `1cb547e`（已同步推送） |
| 工作区 | 干净（无未提交改动） |
| 页面 | 94 页：pb 37 / cu 25 / al 31 / index 等 |
| 指标 | 196 条 / version 3.42 |
| 门禁 | check_html 75/75 + verify_render 75/75 ALL PASS + reclaim 12/0 |
| 死链 | 0（含 17 个总览页） |
| 知几 API | ⚠️ 配额耗尽（HTTP 429「总配额已用尽: 10000 次」），search/series 全返 429 |

---

## 2. 本轮主脑做了什么（v4 → v5 之间）

1. **口径串台修复**（`68b938e`）：cu_4_3/cu_5_1 图注与定义段误写铝口径 → 改回铜口径 + 口径妥协说明；cu_6_2 新增「辅助指标口径声明」（al_62_import 实为铝土矿港口库存周频，非精炼铜进出口）；build_overview_cu_al.py docstring 更新。
2. **协作机制加固**（`fa51f4c` + `1cb547e`）：
   - `scripts/hooks/pre-commit`：改产物文件（`*.html/*.py/*.js`/`data/*.json`）但不写 STATUS.md → 拦截提交。已实测拦截 + 逃生通道 `--no-verify` + 回滚干净。
   - `scripts/bootstrap_agent.sh`：上线自检 6 项（git基线/hook安装/指标数/check_html/死链/知几配额），全绿才准开工。已实测。
   - 安装命令：`git config core.hooksPath scripts/hooks`（本机已启用，新 clone 需手动执行一次）。
   - AGENTS.md §4 补 hook + 自检说明；§8 快照更新至 2026-08-31。
   - STATUS.md 补记并行 agent 两笔未记录提交（d7b8235/93494de）。
3. **Memory 清理**：2190→2044 字符（92%），删除过时任务进度，保留知几配额耗尽等关键阻塞信息。

---

## 3. 已完成（无需再动）

- 铜铝缺口第二批 4 页（cu_4_2 仓单 / cu_4_3 社库 / cu_5_1 初级消费 / al_3_1_1 铝土矿）✅
- cu_4/cu_5 总览页补齐，全库死链 0 ✅
- 口径串台修复 + 跨金属辅助声明 ✅
- 协作机制：pre-commit hook + 上线自检脚本 ✅

---

## 4. 待办（按优先级，⚠️ 知几配额耗尽是最大卡点）

| # | 任务 | 归属 | 依赖 |
|---|---|---|---|
| 1 | ⚠️ **知几配额恢复**（充值/换源/等重置） | 用户 | — |
| 2 | 五金属 Step3 指标注册（138 节点，产物已落盘 `analysis/iwencai/step3_final_5m.json`） | 主脑 | 配额（注册本身不依赖，但建页需数据） |
| 3 | 五金属 Step4 建页（注册后 138 节点） | 五金属 agent | 主脑注册 + 配额 |
| 4 | 三表灌库（indicator_meta/series，spec 已定 `analysis/spec/db_design.md`） | 主脑 | 五金属注册后一次性灌（现在做会返工：ID 体系 CUS 前缀 vs IND 三段式冲突） |
| 5 | 铅库存骨架 8 张（C03/C04/C06/C10/C14b/C15b/C17b/C19） | 主脑 | 外部源/问财发散 |
| 6 | 铜铝剩余节点（4.4/4.5/5.2/5.3/6.3/7.x 等） | 铜铝 | 外部源 + 配额 |

---

## 5. 协作机制（2026-08-31 加固后，保证长期有效的三层保障）

**原理：把「靠 agent 自觉」改成「靠脚本强制」，每层都机器可验证。**

| 层 | 机制 | 怎么保证一直有效 |
|---|---|---|
| 1. 提交层 | pre-commit hook：改产物必须同步 STATUS.md | 拦截 = 提交失败，逃不过（除非 `--no-verify`，主脑可审计） |
| 2. 开工层 | bootstrap_agent.sh：上线自检 6 项 | 未提交改动/基线旧/门禁 FAIL → 红色 ❌ 禁止开工 |
| 3. 并行层 | git worktree 目录隔离（framework-tree-cu/-5m/-pb），共享缓存 DB 用 symlink，永不 checkout | 多 agent 各写各的目录，互不覆盖；协议见 `framework-tree-cu/docs/AGENT_PARALLEL_PROTOCOL.md` |

**切换交接协议（每次主脑 ↔ 并行 agent 交接必走）**：
1. 主脑确认：`git status -s` 空 + HEAD=origin + 无进行中 agent 进程
2. 并行 agent 开工前：`bash scripts/bootstrap_agent.sh` 全绿
3. 并行 agent 每次提交：带 STATUS.md 变更记录（hook 强制）
4. 并行 agent 必须走 worktree/分支，**禁止直接写 main checkout**
5. 完成回传：STATUS.md 记录 + `git push`，主脑跑 reclaim 门禁后 merge

---

## 6. 关键命令速查

```bash
cd /home/ubuntu/framework-tree
# 上线自检（必跑）
bash scripts/bootstrap_agent.sh
# 安装协作 hook（新 clone 一次）
git config core.hooksPath scripts/hooks
# 门禁三道
python3 scripts/check_html.py && node scripts/verify_render.js && python3 scripts/reclaim.py
# 指标数
python3 -c "import json;print(len(json.load(open('data/indicators_v1.json'))['indicators']))"
# 死链
python3 -c "
import re,glob,os
t=[x for f in glob.glob('*.html') for x in re.findall(r'href=\"([^\"]+\.html)\"',open(f,encoding='utf-8').read()) if not os.path.exists(x.split('#')[0])]
print(len(t))"
# 推
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
```

---

## 7. 交接终点

- 新会话接手 → 先 `bash scripts/bootstrap_agent.sh` 自检 → 读 STATUS.md §8 快照 → 按 §4 待办推进
- ⚠️ 知几配额耗尽：数据任务（五金属建页/铜铝补节点/铅骨架）全部等待，勿浪费时间重试拉数据
- 主脑可做不依赖数据的事：五金属 Step3 指标注册、三表灌库设计定稿
