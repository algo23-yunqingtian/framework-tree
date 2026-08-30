# Step1 发散任务卡 · 5 金属批量（ZN/NI/SN/SI/LI）

> **一句话**：把仓库里有的 5 个金属品种做 Step1 同花顺发散，每品种 30 个节点，共 150 次问答。
> 这是纯机械活，适合长时间无人值守跑。

---

## 0. 你拿到的弹药（已就绪，直接读）

| 资产 | 路径 | 数量 |
|---|---|---|
| **驱动脚本** | `scripts/iwencai_batch_driver.py` | 已打补丁（支持 `--manifest` + 全品种映射 + 品种词库注入）|
| **校验器** | `scripts/check_divergence.py` | `--all` / `--variety` / `--strict` |
| **任务清单** | `analysis/iwencai/5metals_step1_manifest.json` | **150 tasks**（dim 已为英文值）|
| **单品种清单** | `analysis/iwencai/<CODE>_manifest.json` | 5 份（各 30 tasks）|
| **节点数** | — | **150 个**待发散节点 |
| **品种词库** | `prompt_lib/varieties/{ZN,NI,SN,SI,LI}.json` | 5 个（驱动脚本会读，自动注入正例词）|
| **维度词库** | `prompt_lib/dimensions/{价格,供应,库存,需求,进出口,成本利润}.json` | 6 个 |
| **Prompt 样本** | `analysis/iwencai/prompts/<CODE>_<节点>.md` | 150 份（仅供参考，驱动脚本会自渲染）|

**6 个维度 → 7 个板块的对应**（板块8 供需平衡不做图表，不发散）：

| 维度文件 | 覆盖板块节点 |
|---|---|
| 价格 | 2.1 盘面结构 · 2.2 现货与升贴水 · 2.3 海外价格 · 2.4 价差体系 · 2.5 估值与利润 · 2.6 持仓席位观察 |
| 供应 | 3.1.1 海外矿·财报产量 · 3.1.2 海外矿·分国别总量 · 3.1.3 国内矿产量 · 3.1.4 矿进口量与分国别 · 3.1.5 TC加工费 · 3.2.1 精炼产量 · 3.2.2 开工率与检修 · 3.2.3 再生·二次供应 · 3.2.4 冶炼利润→供应弹性 |
| 库存 | 4.1 交易所库存 · 4.2 仓单 · 4.3 社会库存 · 4.4 工厂库存 · 4.5 隐性·在途库存 |
| 需求 | 5.1 初级消费 · 5.2 终端细分消费 · 5.3 需求先行指标 |
| 进出口 | 6.1 原料进口 · 6.2 精炼金属进出口 · 6.3 制品出口 · 6.4 海外对华发运 |
| 成本利润 | 7.1 成本曲线与分位 · 7.2 日度利润测算 · 7.3 能源·原料成本 |

---

## 1. 开工前基线同步（强制）

```bash
git fetch origin
git checkout -b task/multi_metals_divergence origin/main
git rebase origin/main
# 确认弹药已拿到（3 项全绿才算基线对）
ls analysis/iwencai/prompts/NI_*.md | wc -l        # 应为 30
python3 -c "import json; m=json.load(open('analysis/iwencai/5metals_step1_manifest.json')); print('待发散 tasks:', len(m['tasks']))"  # 应为 150
python3 scripts/check_divergence.py --all          # 应显示 5 金属各 30 节点全缺（0/150）
```

### 1.1 前置依赖：`--ws`（唯一外部依赖，先搞定这个）

驱动脚本走 CDP 连本地 Chrome，**必须提供一个 page 级 websocket endpoint**。

```bash
# ① 确认本机有 Chrome 且已登录同花顺（iwencai.com）
# ② attach 后拿 page ws endpoint（示例：CDP 反查 /chat 页 target 的 webSocketDebuggerUrl）
python3 -c "
import json, urllib.request
tabs = json.load(urllib.request.urlopen('http://localhost:9222/json'))
for t in tabs:
    if 'iwencai' in t.get('url',''):
        print(t['url'][:60]); print('ws:', t['webSocketDebuggerUrl']); break
"
# 把打印出的 webSocketDebuggerUrl 填到下面命令的 --ws 参数
```

> 如果 Chrome 没开远程调试端口，需带 `--remote-debugging-port=9222` 重启。
> 同花顺页面必须先打开一个「新对话」页（脚本靠 `.ql-editor` 输入框定位，无此框会返回 `NO_EDITOR`）。

---

## 2. 执行步骤

### 2.1 批量驱动同花顺（Chrome CDP）

**入口**：左侧「新对话」/「最近7天」历史点进 → 底部聊天框 `[contenteditable].ql-editor` 粘贴 prompt 发。
**⚠️ 绝不用 `iwencai.com/search` AI搜索入口**（不输出文字）。

**批量驱动脚本（已纳入 repo，可直接用）**：
```bash
# 补丁版驱动脚本（支持 --manifest，全品种映射）
python3 scripts/iwencai_batch_driver.py \
    --manifest analysis/iwencai/5metals_step1_manifest.json \
    --ws <CDP_page_ws_url>

# 单品种（推荐：先跑一个品种验证）
python3 scripts/iwencai_batch_driver.py \
    --manifest analysis/iwencai/NI_manifest.json \
    --ws <CDP_page_ws_url>

# 单节点（冒烟测试）
python3 scripts/iwencai_batch_driver.py --node NI_2.1 --ws <CDP_page_ws_url>

# 区间续跑（断点续跑已内置，state 文件按 manifest 名隔离）
python3 scripts/iwencai_batch_driver.py \
    --manifest analysis/iwencai/NI_manifest.json \
    --ws <CDP_page_ws_url> --start 5 --end 15
```

**前置条件（重要）**：
- 驱动脚本走 CDP 连本地 Chrome，**必须先 attach 一个已登录同花顺的 Chrome**，拿到 `/chat` 页面的 page 级 websocket endpoint 填到 `--ws`
- 同花顺页面必须先打开一个「新对话」页
- 限流保护已内置：每节点间隔 50 秒（COOLDOWN=50），单节点最长等 420 秒
- **150 节点 ≈ 150 × 60s ≈ 2.5-3 小时**（含同花顺生成耗时），建议按品种分批跑

**汇报节奏（每完成一个品种报一次，共 5 次）**：
1. 每跑完一个品种（30 节点），先跑 `check_divergence.py --variety <CODE>` 自检
2. 退出码 0 就 commit + push，报「<CODE> 推了」（例：「NI 推了」）
3. 主脑验收通过后再开下一个品种
4. 单品种约 30-45 分钟，5 个品种共 2.5-3 小时

> 不建议一次性跑完 150 个再报——若第一个品种就发现格式/污染问题，早改能省 3 小时。

**产物**：`analysis/iwencai/<品种>/divergence_<节点>.md`
**状态**：`analysis/iwencai/_driver_state_5metals_step1.json`（断点续跑）

### 2.2 逐节点发散（方式 B，质量更高）

之前实测：一次发 4 节点 7 图 vs 逐节点 18 图——**逐节点方式主动排除跨类指标，带 HS 编码/真实月度数据/政策变量，质量明显更高**。

**推荐顺序**（从最有把握的开始）：
1. **NI 镍**（先做这个，词库最全：镍生铁NPI/高冰镍/印尼/不锈钢）
2. **ZN 锌**（Zn 词库已成熟）
3. **SI 工业硅**
4. **SN 锡**
5. **LI 碳酸锂**（词库已含 盐湖提锂/锂云母/三元前驱体/磷酸铁锂）

### 2.3 产出规范

每个节点产出：`analysis/iwencai/<CODE>/divergence_<节点号>.md`

**文件内容**（对齐已有的 CU/AL 格式）：
- 「独立基础指标枚举」表：序号 | 基础指标 | 直接含义 | 归属判断
- 「核心图表设计方案」表：序号 | 图名称 | 包含指标 | 题材归属度 | 数据源 | 形态 | 观测用途
- 「排除项」区：跨类指标写明「应归属X板块」
- 「主脑验收记录」区（若主脑有反馈）

### 2.4 Manifest 收尾

全部完成后写：`analysis/iwencai/<CODE>_manifest.json`
```json
{
  "variety": "NI",
  "generated": "2026-08-31",
  "nodes": [{"code": "2.1", "file": "divergence_2.1.md", "status": "ok"}, ...],
  "success": 30,
  "fail": 0
}
```

---

## 3. 五条铁律（AGENTS.md 3.5 + 实测教训）

1. **数量硬约束**：每子类 6-8 个指标，最多 10 个。**少比多好，宁缺勿滥**。
2. **独立基础指标原则**：只枚举原始可量化指标。**环比/同比/增速/分位/日增减/去化速度/高点低点** 这些**一律不单列**——它们是同一指标的呈现方式。
3. **题材对象一致**：判定标准唯一——该指标是否直接描述本子类题材对象。跨类指标**不删**，表末标注「与其他子类更相关 + 应归属环节」。
4. **正例关键词**：按 prompt 里的 `positive_keywords` 列表走，不自己发散到词库外。
5. **产出可查**：剔除项**必须**写「为何剔除」，供后续回溯。**禁止静默丢弃**。

---

## 4. 已知坑（踩过的，别重复）

| 坑 | 描述 | 对策 |
|---|---|---|
| **泛化词污染** | 搜"库存"命中大量无关节点 | 精确关键词 + 语义判定 |
| **同花顺发散入口错** | 用 `/search` AI搜索 → 无文字输出 | 只用「新对话」或「最近7天历史」 |
| **一次发多节点** | 一次发 4 节点，指标被串到错节点 | **逐节点单独发**（推荐）|
| **基线旧** | 分支基于旧 commit，缺 main 已有东西 | 开工前必 `git rebase origin/main` |
| **知几无数据** | 发散推荐 ≠ 知几一定有序列 | 后续 Step3 会暴露，先发散全量 |

---

## 5. 门禁 + 回传

```bash
# Step1 阶段无 HTML 产出，用专用校验器检查发散文件完整性
python3 scripts/check_divergence.py --all              # 5 金属全查，输出缺口清单
python3 scripts/check_divergence.py --variety NI       # 单品种
python3 scripts/check_divergence.py --variety NI --strict   # 严格模式（缺排除项也算 FAIL）

# 退出码: 0 = 全部齐全合格；1 = 有缺口（便于 cron/CI 判定）
```

**校验内容**：① 文件齐全（对照 tree_config 30 节点）② 含「指标枚举」+「图表方案」两表 ③ 表格行 ≥4 ④ 严格模式检查排除项/归属判断

**注意**：Step1 完成后**无需**跑 check_html.py / verify_render.js（那两个查 HTML 页面，本阶段无 HTML）。三道门禁在 Step4 建页后才需要跑。

**更新 STATUS.md 近期变更记录**（照现有表格格式，标 `[B]` 前缀）

**commit 前缀**：`[B-Step1]`

**push**：
```bash
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin task/multi_metals_divergence
```

**回传**：「NI 推了」/「ZN 推了」等，按品种报告进度。

---

## 6. 主脑这边会做的（并行）

我这边同时做**铜铝 Step4 建页**（CU 2.1 样板页 → 验收 → 批量 60 页），
你的发散和我不冲突。等你 150 节点发散完后，我接手做 **Step2 取舍决策**（脚本批量），
你再做 **Step3 知几验证**，主脑我做 **Step4 建页**。

---

## 7. 快速开始（照抄这一行）

```bash
# 1. 基线同步
git fetch origin && git checkout -b task/multi_metals_divergence origin/main && git rebase origin/main

# 2. 确认弹药
ls pb_prompt/batch/*_v19.md | wc -l   # 应 ≥30

# 3. 从 NI 开始逐节点发散（读 prompt，写 divergence_*.md）
cat pb_prompt/batch/NI_价格_v19.md
# ... 逐节点驱动同花顺 ...
```

**遇到问题**：不猜、不糊弄，回报阻塞状态。同花顺发散 150 次预计耗时较长，可按品种分批提交。