# 协作任务卡 · 外部来源补充数据整合（2026-09-09 派发）

> 派发方：主脑 agent（服务器 A，Linux）
> 执行方：你（服务器 B，手上有一套主脑拿不到的**外部来源补充数据**）
> 目标：你把你那边的指标+图表产物整理好、提交到 GitHub 协作分支，主脑收到后做二次校验、灌库、重建看板上线。

---

## 0. 你手上有什么（一句话理解你的任务）

你本地有一套**主脑这边拿不到**的外部来源数据（第三方付费源 / 自有采集 / 调研整理等），里面包含已经整理好的**指标**（名称+代码+序列或元数据）和**图表**（可视化定义或成品页）。
你的任务是：把这些东西按本仓库的格式规范整理成结构化产物，提交到自己的协作分支。主脑不做"无中生有"——主脑负责**校验、合并、上线**，你的价值在于把外部源的数据送进来。

**分工边界（重要，避免重复劳动）**：
- 同花顺问财（iwencai.com）：**不需要你访问**，473 份发散回复主脑已全部做完，仓库 `analysis/iwencai/` 里都有。
- 知几数据库：**你用自己的搜索方式验证**（脚本/浏览器/你自己的 API 客户端都行），方法论通用。
- 外部源原始数据：**只有你有**，这是本任务的核心增量。

---

## 1. 关键网址与导航（对方 agent 必读，别假设你知道任何网址）

### 1.1 GitHub 仓库（你的工作区）
- 仓库地址：https://github.com/algo23-yunqingtian/framework-tree
- 仓库网页（看目录树 / 读文档 / 看 diff）：https://github.com/algo23-yunqingtian/framework-tree
- 克隆命令：
  `git clone git@github.com:algo23-yunqingtian/framework-tree.git`

### 1.2 GitHub Pages 线上看板（最终产出地址）
- 网址：https://algo23-yunqingtian.github.io/framework-tree/
- 这是 framework-tree 指标看板的线上地址。你做的指标/图表，最终由主脑 build 成 HTML 页面发布到这里。
- **建议你先打开这个网址看一遍现有页面**——判断你的数据是否已有对应页面、要落到哪个节点、有没有重复造轮子。

### 1.3 外部平台
- 同花顺问财 https://www.iwencai.com/chat —— **本任务不需要你访问**
- 知几数据库 —— 你的验证目标，API 客户端示例（主脑版，你有自己的就用自己的）：
  `python3 ~/.hermes/scripts/zhiji_api.py search "碳酸锂 产量 中国"`
  `python3 ~/.hermes/scripts/zhiji_api.py series FU00015030 2020-01-01 2026-09-09`

### 1.4 仓库内关键文档（clone 后在本地读，或直接在 GitHub 网页读）

| 文档 | 仓库内路径 | 说明 |
|---|---|---|
| **本任务卡** | `docs/COLLAB_TASK_EXTERNAL_DATA_20260909.md` | 你正在读的这份 |
| 新 agent 入职总入口 | `AGENTS.md` | 必读，含红线与协作协议 |
| 全局进度唯一真源 | `STATUS.md` | 必读，看清当前基线，防止覆盖别人成果 |
| 协作两条线隔离机制 | `COLLABORATION.md` | 线A=框架/前端，线B=指标/数据 |
| 完整流程 11 章 | `docs/COLLABORATION_PLAYBOOK.md` | 含格式契约与坑速查 |
| 页面规范 | `docs/PAGE_SPEC.md` | 你要提交 build 脚本/页面时必须遵守 |
| 目录树定义 | `data/tree_config.json` | 8 品种 × 6 板块 × 33 节点的完整结构 |
| 指标元数据真源 | `data/indicators_v1.json` | 1308 条已注册指标（v3.75），你的新指标最终合并到这里 |
| 同花顺逐节点发散 | `analysis/iwencai/<品种>/decision_<节点>.md` | 473 份回复（已完成的，不用你重做） |
| 已有知几匹配结果 | `analysis/zhiji_match/<品种>_zhiji_match.json` | 7 品种 2322 条已有匹配，避免你重复搜 |
| 锌库存知几搜索试点 | `docs/HANDOVER_20260904_zn_stock.md` | 可对照的样本结果 |
| 同花顺 P0-P4 方法论 | `docs/iwencai_methodology_20260903.md` | 取舍判断参考 |
| 数据缺口清单 | `STATUS.md` 待办区 | 哪些节点还没有数据，优先补这些 |

---

## 2. 前置准备（照顺序跑，不要跳）

```text
# 1. 配置 SSH（用主脑发给你的 Deploy Key 私钥）
mkdir -p ~/.ssh && chmod 700 ~/.ssh
#    把私钥内容存为 ~/.ssh/id_agent_deploy（内容主脑通过私密渠道给你）
chmod 600 ~/.ssh/id_agent_deploy

#    确认 SSH 能通（应该看到 "successfully authenticated"）
ssh -i ~/.ssh/id_agent_deploy -o StrictHostKeyChecking=accept-new -T git@github.com

# 2. 克隆
cd ~ && git clone git@github.com:algo23-yunqingtian/framework-tree.git
cd framework-tree

# 3. 强制指定用这个 key（否则会用你服务器上的默认 key）
GIT_SSH="ssh -i $HOME/.ssh/id_agent_deploy -o StrictHostKeyChecking=accept-new"

# 4. 同步到最新基线（必须！否则你会覆盖主脑已上线的成果）
git fetch origin
git checkout main && git pull --ff-only origin main

# 5. 开工自检（红线，不许跳过）
bash scripts/bootstrap_agent.sh
python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print('指标键数:', len(d), '| version:', d.get('version'))"
#    → 必须 ≥ 1308 键 / v3.75。少了 = 你基线旧，先 rebase，禁止开工。

# 6. 建你的工作分支
git checkout -b task/external_data_supply
```

---

## 3. 你的任务范围（按你的数据实际情况选做）

### A. 品种覆盖优先级（当前看板状态）

| 品种 | 现有页面 | 状态 | 优先级 |
|---|---|---|---|
| 铅 PB | ~37 页 | 老牌完整 | 低（除非你有独家数据） |
| 锌 ZN | 29 页 | 全板块完成 | 中 |
| 铜 CU | ~28 页 | 缺口已补，仍有细分节点缺口 | 中 |
| 铝 AL | ~28 页 | 同上 | 中 |
| 镍 NI | 28 页 | 已有页，知几匹配 C 级偏多（186 条） | 高 |
| 锡 SN | 28 页 | 同上（C 级 168 条） | 高 |
| 工业硅 SI | 28 页 | C 级 142 条 | 高 |
| 碳酸锂 LI | 部分页 | 发散只做到 4.4，5.x~7.3 全缺 | **最高** |

**建议**：优先补 **LI 缺口 + NI/SN/SI 的 C 级未命中项**（这些是知几查不到、但你的外部源可能有的）。
先打开 https://algo23-yunqingtian.github.io/framework-tree/ 确认哪些节点还没有真实数据图表。

### B. 板块范围硬约束
- 只做 **板块 2/3/4/5/6/7**（价格/供给/库存/需求/进出口/成本利润）。
- **板块 8（供需平衡 8.1/8.2/8.3）不做图表**，主脑另行做平衡表模式，你不要碰。

---

## 4. 产出格式（按你手头的东西选）

### 情况 1：你只有「指标定义 + 序列数据」
导出成 JSONL，每行一个指标的一条时序点。路径：`data/db_export/`

```json
{"key": "external_lc_output", "variety": "LC", "date": "2026-08-01", "value": 12345.0, "unit": "吨", "freq": "daily", "source": "你的来源标识"}
```

要求：
- 紧凑格式（`json.dumps(obj, ensure_ascii=False, separators=(',',':'))`），每行一条。
- 按品种分文件：`series_EXTERNAL_LI.jsonl`、`series_EXTERNAL_NI.jsonl`。
- 单个文件控制在 10MB 以内（实测 JSONL 约 0.5~0.7MB/品种可轻松走 git）。
- **绝不要提交 .db 文件**——`.gitignore` 第 1 行就是 `*.db`，你 push 不上去，等于白做。用 `git check-ignore -v <路径>` 自查。

### 情况 2：你有「指标 + 同花顺概念名 + 知几 ID」的匹配关系
走标准匹配格式，路径：`analysis/zhiji_match/<品种>_external.json`

```json
{
  "variety": "LI",
  "agent": "agent-B-20260909",
  "date": "2026-09-09",
  "matches": [
    {
      "node": "3.1.1",
      "node_name": "矿端产量",
      "external_indicator": "澳洲锂矿产量（你的来源）",
      "zhiji_id": "ID00188307",
      "zhiji_name": "锂矿：产量：中国（日）",
      "zhiji_freq": "日",
      "zhiji_unit": "吨",
      "match_level": "A",
      "verified": true,
      "source": "你的外部源名称",
      "notes": ""
    }
  ]
}
```

级别判定：A=知几真命中且口径一致；B=部分匹配但频率/单位/口径有差异（notes 必须写清差在哪）；C=知几无数据（notes 写你试过哪些关键词）。

### 情况 3：你已经做好「可视化图表定义」（ECharts option 等）
路径：`charts/external/<品种>_<节点>.json`，格式：

```json
{
  "variety": "LI",
  "node": "5.1",
  "title": "图表标题",
  "chart_note": "口径说明，必须写数据来源+频率+单位",
  "series": [
    {"key": "external_lc_output", "name": "你的指标名", "freq": "daily", "unit": "吨"}
  ],
  "chart_type": "line",
  "source": "你的外部源名称"
}
```

主脑会照 `docs/PAGE_SPEC.md` 规范统一 build 成 HTML，**你不需要用 f-string 写 JS 模板**（那是坑），也不用自己写 HTML 页面。

### 情况 4：你连 HTML 页面都做好了
那就直接放到你分支根目录，命名照既有规则（`li_3_1.html` 这样）。
但主脑**会全量重建**，所以你的页面只作为内容参考，最终以 `scripts/build_*.py` + `chart_kits.py` 为准。
如果你要提供 build 脚本，放到 `scripts/build_external_<品种>_<节点>.py`，**禁止改 `scripts/chart_kits.py`**（那是主脑独占的公共模块）。

---

## 5. 协作红线（违反直接打回，不看内容）

1. **禁止直接 push main**。只能 push `task/external_data_supply` 分支。
2. **禁止改** `data/indicators_v1.json` / `STATUS.md` 的既有内容 / `scripts/chart_kits.py`。
   新指标由主脑统一合并进 indicators_v1.json（主脑独占写入权）。
3. **禁止 `git add -f`**（会绕过 gitignore 把 `.db` 强提）。提交前先跑 `git status -s` 确认没有 .db/.env/.pyc。
4. **禁止 `git checkout -f` / `git reset --hard` 到非 main 的 commit**。
5. **禁止覆盖别人的成果**：只 `git add` 你自己新增的文件，绝不 `git add -A`。
6. **禁止在代码/commit 信息里出现任何 API key 或密钥**。
7. 用 f-string 写 JS 模板会 SyntaxError——用 `%` 格式化 + `%%` 转义（仅当你必须写 JS 时）。
8. **开工前必须跑第 2 节的基线自检**。基线旧就重跑会覆盖主脑已上线的成果，且 git merge 补不回来。

---

## 6. 提交与汇报

```text
# 每完成一批，立刻提交（30 秒内），别攒到最后
git status -s                          # 先看要提交什么，确认没有 .db/.env
git add data/db_export/ analysis/zhiji_match/ charts/external/   # 精确到目录，别用 -A
git commit -m "[B-EXT] <品种>外部源补充: <一句话说明>（新增 X 指标 / Y 图表）"
git push origin task/external_data_supply

# GitHub HTTPS 超时时的备用推送方式（腾讯云对 GitHub 连接常超时）
GIT_HTTP_VERSION=1.1 git -c http.version=HTTP/1.1 push origin task/external_data_supply
```

### 汇报格式（推完分支后，在消息里直接写给主脑，别只写在 commit 里）

```text
【外部源补充 · 完成汇报】
- 分支：task/external_data_supply
- 推送 SHA：<git rev-parse HEAD>
- 指标：新增 X 个（JSONL 共 Y 行 / 匹配 JSON 共 Z 条）
- 图表定义：N 个
- 覆盖节点：<品种>.<节点> 列表
- 外部源名称：<你的来源，便于主脑做口径标注>
- 需要你主脑确认的疑点：<比如口径不确定、单位存疑的指标>
```

---

## 7. 主脑这边会做什么（让你心里有数）

1. 跑 `python3 scripts/reclaim.py` 校验你的产物（格式契约 + 完整性）。
2. **不信任自报数字**——主脑会实查行数/键数，和你说的一致才继续。
3. 校验通过后：合并你的外部指标进 `indicators_v1.json`（版本号 +1，写 changelog）。
4. 照 `docs/PAGE_SPEC.md` 用 `chart_kits.py` 统一 build 页面。
5. 跑三道门禁：`check_html.py` → `verify_render.js` → `reclaim.py`，全绿才上线。
6. push main 后 GitHub Pages 自动发布到 https://algo23-yunqingtian.github.io/framework-tree/

**返工成本很低**：你的产物在分支上、没合 main 之前，看板零污染。主脑发现问题就让你在分支上改，你改完重推即可。

---

## 8. 卡点找谁

- 格式/口径/节点归属拿不准 → 先在分支上按 A/B/C 级别标注 + 写 notes，主脑 review 时一起讨论，**不要卡住不动工**。
- 知几搜不到 → 换至少 3 种关键词组合（同义词 / 中英混用 / 数字边界）再下结论，报"无数据"前必须尝试过。
- SSH / push 失败 → 先重试 3 次（网络抖动），还不行就用 `GIT_HTTP_VERSION=1.1` 备用方式。
