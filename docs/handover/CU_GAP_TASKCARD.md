# 铜(CU)缺口节点建页 · 任务卡（零基础可做）· 2026-09-01 修订版

> **重要**：本卡已于 2026-09-01 修订，节点清单已更新。旧版本声称的 4.4/7.1 已存在，勿做。
> 你是新来的 agent，**不需要懂期货**。按本文档一步步做，产出与既有页面同一标准。
> 完成时间目标：5 个节点，每个 1-2 小时。
> 有不懂的名词看本文档「名词速查」（第 10 节），不要自己猜。

---

## 0. 你要做什么（一句话）

给**铜(CU)**这个品种做 **5 张看板子页面**，每页展示几个和铜有关的**数字指标**（交易所库存、终端消费、进出口）的**折线图**。

⚠️ **这 5 个节点在 indicators_v1.json 中注册指标数 = 0**，需要先做同花顺发散→知几验证→注册，再建页。

5 张页面和它们的主题：

| 节点号 | 页面主题 | 看什么 | tree_config 定义 |
|---|---|---|---|
| **cu_4_1** | 交易所库存 | LME/SHFE 仓库库存（日频） | 4.1 交易所库存 · 日 同步 |
| **cu_5_2** | 终端细分消费 | 电缆、空调、汽车等下游消费（月频） | 5.2 终端细分消费 · 滞后 |
| **cu_5_3** | 需求先行指标 | 订单、开工率领先指标（月/周） | 5.3 需求先行指标 · 先行1-2月 |
| **cu_6_3** | 制品出口 | 铜材、铜管出口量（月频） | 6.3 制品出口 · 同步 |
| **cu_6_4** | 海外对华发运 | 海外铜矿发运量（周/月） | 6.4 海外对华发运 · 先行1月 |

---

## 1. 环境（10 分钟，一次性）

```bash
# ① 进项目
cd /home/ubuntu/framework-tree
git fetch origin && git rebase origin/main
# ② 核验基线：下面必须输出 ≥ 809
python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print('指标数:', len(d['indicators']))"
# ③ 装协作 hook（一次）
git config core.hooksPath scripts/hooks
# ④ 跑上线自检（全绿才开工）
bash scripts/bootstrap_agent.sh
```

⚠️ **如果 ② 输出 < 809**：先 `git fetch origin && git rebase origin/main` 再核验，还不行就停下来问主脑。**基线旧直接开工 = 会覆盖别人的工作**。

---

## 2. 每一步怎么做（照抄）

### Step 1：先做同花顺发散（**必须先做，这 5 个节点无注册指标**）

这 5 个节点在 indicators_v1.json 中**注册指标数 = 0**，需要先用同花顺(iwencai)发散拿候选指标清单。

**同花顺访问方式**：你**没有**同花顺账号，需要问用户要账号密码。在飞书聊天里直接问用户："请提供同花顺登录账号密码，我需要做铜 5 个节点的指标发散"。

**发散脚本位置**：
- 批量驱动：`scripts/iwencai_batch_driver.py`
- 品种 manifest：`analysis/iwencai/CU/CU_manifest.json`
- 单节点 prompt 模板：`analysis/iwencai/prompts/CU_<节点>.md`（如果不存在需从 `analysis/iwencai/prompts/_template.md` 复制改造）

**发散流程**（每个节点）：
1. 打开同花顺问财网站 `iwencai.com`（需用户登录态）
2. 输入节点 prompt（从 `prompts/CU_4_1.md` 等读取）
3. 人工审核返回的指标列表，剔除明显不相关
4. 存为 `analysis/iwencai/CU/divergence_4.1.md` 等

**详细流程见**：`docs/COLLABORATION_PLAYBOOK.md` 第 3 章同花顺发散步骤。

---

### Step 2：知几验证（每个节点 5 分钟）

对同花顺返回的每个指标名，用知几 API 搜索验证是否有真实 ID 和时序数据：

```bash
python3 ~/.hermes/scripts/zhiji_api.py search "铜 交易所库存"
```

记录：
- 有 zhiji_id 且有数据的 → 进入注册列表
- 有 zhiji_id 但无数据 → 标「待外部源」
- 无 zhiji_id → 标「知几无字段」

---

### Step 3：注册到 indicators_v1.json（主脑合并）

**注意**：你**不能直接修改** `data/indicators_v1.json`（主脑独占）。需要把注册清单整理成 JSON 片段，开 PR 提交给主脑合并。

格式示例：
```json
{
  "cu_41_lme_stock": {
    "name": "LME铜库存",
    "unit": "吨",
    "freq": "daily",
    "ids": {"CU": "FU00012345"},
    "_origin": "SMM",
    "_nodes": ["4.1"]
  }
}
```

---

### Step 4：建页面（用现成引擎，30 秒）

**前提**：指标已注册，数据已拉入库（api_cache.db）。

```bash
cd /home/ubuntu/framework-tree
python3 scripts/build_cu_al_batch.py 4.1 5.2 5.3 6.3 6.4
```

这个引擎会自动：读指标 → 画折线图（含季节视图切换）→ 生成 `cu_4_1.html` 等文件。

**如果某节点引擎没生成**（可能是指标缺失）：
```bash
python3 scripts/build_cu_al_batch.py 4.1 --dry   # 看它为什么跳过
```

---

### Step 5：跑门禁（必须全绿）

```bash
cd /home/ubuntu/framework-tree
python3 scripts/check_html.py          # 静态校验
node scripts/verify_render.js          # 渲染校验（需 node）
python3 scripts/reclaim.py             # 格式契约
```

- `check_html.py` 报 FAIL → 看输出，通常是要在脚本顶部 `PAGES` 列表里注册新页面（照已有 cu_ 页面抄）
- `verify_render.js` 报 FAIL → 同样在 `PAGES` 里加 `{key: 'cu_41', file: 'cu_4_1.html', seasonal: ['echart_cu_41_c1', ...]}`，cid 从生成的 HTML 里抄（搜 `echart_cu_41`）
- `reclaim.py` 的 FAIL 如果是 `[FIX-]` 前缀误判，忽略（已知 bug）

---

### Step 6：更新 STATUS.md + 提交

```bash
cd /home/ubuntu/framework-tree
git status -s          # 确认只有你的 cu_*.html / build 脚本 / STATUS.md 变化
```

然后在 `STATUS.md`「近期变更记录」表格**最上面插入一行**（照已有行抄格式）：
```
| 2026-09-01 | **[CU-GAP] 铜4.1/5.2/5.3/6.3/6.4 建页上线**（agent） | agent | 做了什么、几个图、门禁结果 | 线B |
```

提交（**只能加你这些文件**，不要 `git add data/indicators_v1.json` 或别人的文件）：
```bash
git add cu_4_1.html cu_5_2.html cu_5_3.html cu_6_3.html cu_6_4.html scripts/ STATUS.md
git commit -m "[CU-GAP] 铜4.1/5.2/5.3/6.3/6.4 建页"
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin main
```

> ⚠️ pre-commit hook：如果你改了 `*.html/*.py/data/*.json` 但没动 `STATUS.md`，会被拦。所以**先改 STATUS.md 再提交**。

---

## 3. 交付报告（做完发主脑）

把以下内容发给主脑：

```
铜 5 节点建页完成：
- 每个节点做了哪些步骤（发散/验证/注册/建页）
- 每个节点用了哪些指标（key + 名称）
- 各页几幅图
- 门禁结果（check_html X/X, verify_render X/X）
- 跳过节点及原因（如无数据）
- git commit hash
- 分支名称（如果开了分支）
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
| `data/tree_config.json` | 节点权威定义（4.1/5.2/5.3/6.3/6.4 的 name + q） |
| `data/indicators_v1.json` | 指标元数据（**809 条 v3.45**，含节点归属 `_nodes`） |
| `scripts/api_cache.db` | 已拉数据缓存 |
| `scripts/iwencai_batch_driver.py` | 同花顺批量发散驱动 |
| `analysis/iwencai/CU/` | 铜品种发散记录目录 |
| `scripts/build_cu_al_batch.py` | **建页主引擎**（用法看文件头部注释） |
| `scripts/chart_kits.py` | 图表公共库（只读，别改） |
| `scripts/check_html.py` / `verify_render.js` / `reclaim.py` | 三道门禁 |
| `cu_2_1.html` | 样板页（看它的结构，你的页面应长这样） |

---

## 7. 已知坑

| 坑 | 解法 |
|---|---|
| 同花顺需要登录态 | 问用户要账号密码，不要自己尝试登录 |
| check_html/verify_render 报新页面没注册 | 在脚本顶部 `PAGES` 列表加你的页面（照抄既有 cu_ 条目） |
| reclaim.py FAIL=1 且是 `[FIX-]` 前缀 | 已知误判（白名单漏 `[FIX-`），忽略，不是你的错 |
| `search` 返回杂项 | 关键词必须空格分隔："铜 交易所库存" ✓，"铜交易所库存" ✗ |
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
idx = next(i for i, l in enumerate(lines) if l.startswith('| 2026-09-01'))
new_row = "| 2026-09-01 | **[CU-GAP] 铜4.1/5.2/5.3/6.3/6.4 建页上线**（agent） | agent | 内容 | 线B |"
lines.insert(idx, new_row)
open(path, 'w').write('\n'.join(lines))
# 检查有没有字面 \n 污染
print([i+1 for i, l in enumerate(lines) if '\\n' in l] or "无")
PYEOF
```

---

## 9. 铝(AL)缺口节点

铝(AL)同样有 **5 个缺口节点**，流程与铜完全一致，只是节点号不同：

| 节点号 | 页面主题 | tree_config 定义 |
|---|---|---|
| **al_3_1_2** | 海外矿·分国别总量 | 3.1.2 海外矿·分国别总量 · 月/年 |
| **al_3_1_4** | 矿进口量与分国别 | 3.1.4 矿进口量与分国别 · 月 滞后15-20天 |
| **al_6_1** | 原料进口 | 6.1 原料进口 · 滞后 |
| **al_6_4** | 海外对华发运 | 6.4 海外对华发运 · 先行1月 |
| **al_7_3** | 能源/原料成本 | 7.3 能源/原料成本 · 先行 |

如果你愿意，可以顺手把铝的 5 个节点也做了，流程一样，只是：
- 发散记录目录改为 `analysis/iwencai/AL/`
- 建页命令改为 `python3 scripts/build_cu_al_batch.py 3.1.2 3.1.4 6.1 6.4 7.3`

---

## 10. 名词速查（不懂就查这里）

| 词 | 意思 |
|---|---|
| **指标** | 一个可量化的数字序列，如"铜社会库存（万吨）"，每天/周/月一个数 |
| **节点** | 看板的一个板块，如 4.1=交易所库存。每个节点一张页面 |
| **正主** | 该页面最核心的指标（每页 1 个），其他都是辅助 |
| **折线图** | 横轴时间、纵轴数值的曲线 |
| **季节视图** | 同一张图按"历年同期"叠加展示（看周期性） |
| **api_cache.db** | 本机已下载的数据缓存，页面从这读数据 |
| **门禁** | 三道自动检查，全绿才算合格（质量关卡） |
| **git rebase / push** | 把别人的最新改动合并进来 / 把你的改动上传 |
| **基线** | 你开工时仓库的最新状态。基线旧=没跟上最新，会覆盖别人 |
| **同花顺(iwencai)** | 股票/期货问答网站，用自然语言问它能返回指标列表 |
| **知几 API** | 数据供应商（SMM/Mysteel 等）的查询接口 |
| **SMM / Mysteel / LME / SHFE** | 数据机构名（SMM=上海有色网，Mysteel=钢联，LME=伦敦金属交易所，SHFE=上期所） |
| **发散** | 用同花顺问"铜有哪些库存指标"，得到候选列表的过程 |
| **注册** | 把候选指标写入 indicators_v1.json 的过程 |