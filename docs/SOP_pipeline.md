# framework-tree SOP — 指标树节点从 0 到上线全流程

> **用途**：让任意 agent（或新 agent）读本文档后，能独立完成「一个指标树节点」从同花顺发散 → 知几命中 → 入库 → 画图 → 上线的全过程。
> **模板节点**：铅(PB) 4.1~4.5 库存子页已跑通，是**范例**。其余 33 个节点照此流程复刻。
> **前置条件**：
> - 本机已有 `~/.hermes/scripts/zhiji_api.py`（知几 API 客户端）
> - `framework-tree/` 仓库已克隆，Git 远程走 SSH（HTTPS 被拦截）
> - 浏览器工具可访问同花顺问财(浏览器Q&A)，prompt 需粘贴到问财提问框
> - 文件锁白名单已配置（`~/.hermes/scripts/file_write_lock.py`），**只写 analysis/iwencai/ 或 framework-tree/ 的 scripts/data/docs/ 目录**，不写品种 HTML（HTML 由 build 脚本统一产出）

---

## 一、数据结构全景（三库一图）

```
framework-tree/
├── data/indicators_v1.json          ← 单一真源：指标 ID 主映射（i1~i36）
├── scripts/api_cache.db             ← 时序缓存（SQLite, 不推 GitHub）
├── scripts/indicator_correction.db  ← 同花顺→知几纠错库（A/B/C 分级记录）
├── prompt_lib/                      ← Prompt 词库（模板零领域词）
├── pb_prompt/                       ← 投喂记录 + 定稿
├── analysis/iwencai/PB/             ← 中间产物（命中结果 JSON 等）
└── *.html                           ← 最终看板（GitHub Pages 上线）
```

### 1.1 `data/indicators_v1.json`（唯一真源，版本号 v1.3）

**结构**：
```json
{
  "_meta": { "version": "1.3", "updated": "2026-08-28", "status": "部分验证", ... },
  "version_changelog": [ {"v": "1.0", "date": "2026-08-26", "change": "..."} ],
  "indicators": {
    "主连": { "name": "期货主连结算价", "unit": "元/吨", "freq": "daily",
              "verified": false, "ids": {"CU":"FU00014941", "AL":"...", "PB":"FU00014946", ...} },
    "i1": { "name": "LME铅库存", "unit": "吨", "freq": "daily",
            "verified": true, "category": "inventory", "ids": {"PB":"a10193709"} },
    ...
    "i36": {...}
  }
}
```

**关键规则**：
- 通用指标（主连/LME库存/SHFE库存/社库/TC/精炼产量/表观消费/开工率）：跨品种共享 key，`ids` 内含所有品种代码
- 品种专属指标（`i1`~`i36`）：`ids` 仅含一个品种代码（如 `PB`），未来同指标在其他品种可用时追加即可
- **凡修改必 bump version + 追加 changelog 一条**，再 `git commit + push`
- **绝不出现两个语义不同的指标共享同一 metric key**（i19-i36 之前踩过坑）

### 1.2 `scripts/api_cache.db`（SQLite，36 条 = 36 个已缓存指标）

**表结构**：
```sql
CREATE TABLE indicator_cache (
    code       TEXT NOT NULL,          -- 品种代码 PB/CU/AL...
    metric     TEXT NOT NULL,          -- 指标键 i1~i36
    zhiji_id   TEXT,                   -- 知几 ID（FU/a/ID/CUS 开头）
    data_json  TEXT,                   -- 完整 payload：{id, source, name, unit, freq, points[]}
    fetched_at TEXT,                   -- 拉取时间
    error_msg  TEXT,
    name       TEXT, unit TEXT, freq TEXT,
    PRIMARY KEY(code, metric)
);
```

**`data_json` 内容样例**（i1 LME铅库存）：
```json
{"id":"a10193709","source":"smm","name":"LME: 铅: 库存: 日度",
 "unit":"吨","freq":"日","points":[{"date":"2026-08-27","value":72300},...]}
```
> ⚠ **points 是倒序**（最新在前）。ECharts time 轴需要正序，build 时**必须反转**。

### 1.3 `scripts/indicator_correction.db`（纠错库）

**表结构**：
```sql
CREATE TABLE correction (
    id INTEGER PRIMARY KEY, indicator TEXT, subcat_from TEXT, subcat_to TEXT,
    error_type TEXT,         -- misattribute/dupe/out_of_dimension/price_signal
    reason TEXT, suggested_action TEXT, -- promote / drop / hold
    revive_condition TEXT, source_ver TEXT,
    created_at TEXT, status TEXT -- pending/promoted/dropped/archived
);
```
> 记录同花顺发散阶段发现的归属错误（如「铅精矿工厂库存」本属 4.4 却被错归 4.4→实际应归 4.6 原料库→最终并入 4.4），后续品种复用。

### 1.4 `prompt_lib/`（词库，模板永不改）

- `template_v19.md`：零领域词模板，**永远不改**
- `dimensions/库存.json`、`供应.json`、`需求.json`：维度词库（positive_keywords / compound_themes / usage_examples / boundary_tips）
- `varieties/PB.json`（未来加 CU/AL/ZN/NI/SN/LC/SI）：业内术语
- **新增维度/品种 = 新增 JSON 文件，不动模板**

---

## 二、7 步标准流程（每步有命令/输入/输出）

### STEP 1: 同花顺提问（发散指标）

**命令**：
```bash
cd framework-tree
python3 prompt_lib/render_prompt.py \
    --dim 库存 \
    --variety PB \
    --subdirs "4.1交易所库存|4.2仓单|4.3社会库存|4.4工厂库存|4.5隐性·在途" \
    -o pb_prompt/prompt_v19_PB_库存.md
```

**维度映射**（未来做其他目录时换 --dim）：

| 目录 | --dim |
|---|---|
| 价格 | （待建 dimensions/价格.json） |
| 供应 | `供应` |
| 库存 | `库存` |
| 需求 | `需求` |
| 进出口 / 成本利润 / 平衡 | （待建对应 JSON） |

**输出**：`pb_prompt/prompt_v19_PB_<维度>.md`

**下一步**（人工/agent 手工操作浏览器）：
1. 打开同花顺问财(浏览器Q&A)，**开新对话**（避免上下文污染）
2. 将 prompt 全文粘贴到提问框，**Enter 发送**
3. 立即把原始回答 `write_file` 落盘到 `analysis/iwencai/PB/<节点>_vXX_<日期>.md`（同花顺回答很长，分段取，防丢失）

**⚠ 注意**：
- 本用户偏好「只要结果，不要经济学逻辑/不要相关性」→ 用 v8 模板风格（prompt_v19 已内置）
- `browser_type` 直接打字粘贴，**别用 `browser_console` 表达式注入长文本**（有长度上限）

### STEP 2: 指标筛选（vN 定稿）

**输入**：同花顺原始回答 `analysis/iwencai/PB/<节点>_vXX_<日期>.md`

**人工审核规则**：
- 删除跨维度的指标（如库存页出现的「价格」「利润」「价差」→ 移到价格维度，进纠错库）
- 合并重复子类（如 4.6→4.4）
- 标注「无公开数据」的项（不进知几验证，节省配额）
- 每张图保留：图名 / 指标名 / 单位 / 频率 / 建议图表形态

**输出**：`pb_prompt/Pb_看板指标定稿_vN.md`（v 号递增，覆盖旧版）

### STEP 3: 知几命中（A/B/C 分级）

**准备指标清单**（每行一个，复制 STEP 2 定稿）：
```json
[
  {
    "code": "4.1_分地区",
    "name": "LME铅库存分地区(新加坡)",
    "kw": ["LME铅库存新加坡", "LME新加坡铅仓库", "新加坡 铅 仓单"],
    "priority": "low",
    "skip": false
  },
  {
    "code": "4.3_持有者",
    "name": "铅社库分持有者",
    "kw": ["铅社库持有者", "铅库存贸易商"],
    "priority": "low",
    "skip": true,
    "reason": "SMM/Mysteel 均无拆分数据"
  }
]
```
存为 `analysis/iwencai/PB/<节点>_verify_list.json`

**关键词三档策略（实测定稿）**：
| 档位 | 写法 | 用途 |
|---|---|---|
| kw[0] 主搜词 | 连写 | 保特异性 |
| kw[1] 辅搜词 | 2-token 空格（如「LME 铅 注销」） | 躲中文分词盲区 |
| kw[2] 兜底 | 短空格（如「新加坡 铅 仓单」） | 专攻「分地区/分仓库」 |

> ⚠ **4+ token 空格分词会 OR 退化**（混入无关品种），**禁止使用**

**运行**：
```bash
cd analysis/iwencai/PB
python3 zhiji_batch_verify.py \
    --input 4_1_verify_list.json \
    --out 4_1_zhiji_match_20260828.json \
    --variety PB
```

**输出**：`4_1_zhiji_match_*.json`，含 A_hit / B_weak / C_miss / SKIP 分级和每命中项的 `zhiji_id`

> ⚠ **zhiji_batch_verify.py 已内置 smm + mysteel 双源搜索**（v1.3 修复，原先 `all` 必漏）；如命中仍弱，需手工调 `zhiji_api.py search 关键词 smm 5` / `mysteel 5` 各一次补搜
> ⚠ **search 端点必须显式传 source**（`smm`/`mysteel`），不传或传 `all` 几乎一律返回 0
> ⚠ **本地限频**：zhiji_api.py 每次调系列需 `sleep 1s`（脚本已内建）

### STEP 4: 入库（indicators_v1.json 更新）

**规则**：
| 分级 | 处理 |
|---|---|
| A_hit（score ≥ 12） | `verified: true`，入库 indicators_v1.json |
| B_weak（score 6~11） | `verified: false`，占位待人工复核 |
| C_miss | 不入库，**入纠错库**（`error_type: out_of_dimension` 或记「无数据」） |
| SKIP | 不入库 |

**分配 metric key**：
```sql
-- 先查当前已占用 key（避免冲突！）
python3 -c "
import sqlite3
cur = sqlite3.connect('scripts/api_cache.db').execute('SELECT metric FROM indicator_cache ORDER BY CAST(substr(metric,2) AS INT)')
print([r[0] for r in cur.fetchall()])
"
```
> ⚠ **冲突防御**：`SELECT metric FROM indicator_cache` 排冲突；永远不让两个语义不同的指标共享同一 key（i19-i20 历史事故根因）

**分配原则**：
- `i1`~`i36`：已占用，新指标从此之后继续（`i37` 起）
- 通用指标（跨品种）：用中文 key（如「社库」），`ids` 内含多个品种
- 新品种（如镍）：建议用 `i_<品种>_<序号>` 前缀避免与铅 key 冲突

**操作**：
```python
# 编辑 data/indicators_v1.json
data['indicators']['i37'] = {
    "name": "<指标名>", "unit": "<单位>", "freq": "daily|weekly|monthly|annual",
    "verified": True, "category": "<目录分类>", "ids": {"PB": "a100xxxxx"}
}
data['_meta']['version'] = '1.4'
data['_meta']['updated'] = '2026-08-28'
data['version_changelog'].append({"v": "1.4", "date": "2026-08-28", "change": "新增 i37 <指标名>"})
```

**提交**：
```bash
cd framework-tree
git add data/indicators_v1.json
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_github -o StrictHostKeyChecking=accept-new" \
    git commit -m "[DATA] indicators_v1.json v1.4: +i37 <指标名>"
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_github -o StrictHostKeyChecking=accept-new" \
    git push origin main
```

### STEP 5: 拉数据（刷新 api_cache.db）

**使用统一脚本**（v1.3 合并版，单一真源 = indicators_v1.json）：
```bash
cd framework-tree/scripts

# 刷新刚入库的 i37
python3 refresh_cache.py --metrics i37

# 或刷新多个指标
python3 refresh_cache.py --metrics i37,i38,i39

# 或全部 verified=true 的 PB 指标（默认）
python3 refresh_cache.py

# 其他参数
python3 refresh_cache.py --code ZN --since 2018-01-01 --until 2026-09-01
```

**⚠ 前置校验**（build 前必做，防「图还是昨天的」）：
```bash
python3 -c "
import sqlite3, json
conn = sqlite3.connect('scripts/api_cache.db')
cur = conn.cursor()
db_ids = {r[0]: r[1] for r in cur.execute(\"SELECT metric, zhiji_id FROM indicator_cache WHERE code='PB'\").fetchall()}
conn.close()
json_ids = {k: v['ids'].get('PB') for k,v in json.load(open('data/indicators_v1.json', encoding='utf-8'))['indicators'].items() if k.startswith('i') and v.get('verified')}
# diff
added = set(json_ids) - set(db_ids)
removed = set(db_ids) - set(json_ids)
changed = {k for k in set(json_ids)&set(db_ids) if json_ids[k]!=db_ids[k]}
if added or removed or changed:
    print('DIFF:', '新增', added, '移除', removed, '变动', changed)
else:
    print('缓存与JSON一致')
"
```

### STEP 6: 画图（build → HTML）

**参考**：`scripts/build_pb_v2.py`（34KB，模板脚本，可复用图表函数）

**核心函数速查**：
| 函数 | 用途 |
|---|---|
| `chart_line_t(metric, color, unit, cid, name, ...)` | 单变量时序/季节双模式图 |
| `chart_dual(...)` | 双 Y 轴图 |
| `chart_multiline(...)` | 多线对比 |

**`chart_line_t` 高频参数**：
```python
# 默认季节图（库存类推荐）
chart_line_t("i3", "#5b7a8c", "万吨", "echart_p43_c7", "C07",
             "SMM · 周 · 万吨", default_seasonal=True)

# 计算指标（如 LME 注销占比 = i7/(i6+i7)）
rpairs = [[dt, round(m7[dt]/(m6[dt]+m7[dt])*100, 2)] for dt in common]
chart_line_t("i7", "#7a8a9c", "%", "echart_p42_c5b", "C05b",
             "SMM · 日 · %", default_seasonal=True, data=rpairs)
```

**关键约束**：
- **ECharts 必须离线化**（`assets/echarts.min.js` 进仓库），**绝不用 CDN**（CDP/受限网络下 timeout）
- 数据固化进 HTML（内联成 ECharts data 数组），不能请求 API
- 必须带**反拷贝保护**（禁右键/Ctrl+C/S/P/F12/选中/拖拽/打印）
- 对 zhiji 倒序数据**反转成正序**
- **ECharts JS 代码转义**：用 `esc()` 辅助函数处理 `{}`，不要用 f-string 直接拼 JS

**`esc()` 辅助函数（必须用）**：
```python
def esc(s):
    return s.replace("{", "{{").replace("}", "}}")
MAIN = f"""<script>{esc(js_code)}</script>"""
```

**新建子页 HTML 模板**：复制 `pb_41_stock.html` 或 `pb_stock_v2.html`，改 PAGE_MAP/chart 列表/data 映射，跑 build 脚本生成。

**⚠ 本地预览**：用 `python3 -m http.server <port>`，不要 Flask dev server（Werkzeug 缺失会崩）。

### STEP 7: 推送 GitHub Pages + STATUS.md 更新

**推送到仓库**：
```bash
cd framework-tree
git add -A
git commit -m "[REFRESH] 铅4.1子页 v5: 新增N图, 总M图"
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_github -o StrictHostKeyChecking=accept-new" \
    git push origin main
```

**Commit 前缀规范**：
| 前缀 | 场景 |
|---|---|
| `[DATA]` | indicators_v1.json 更新 |
| `[REFRESH]` | 缓存/HTML 更新 |
| `[CLEANUP]` | 脚本瘦身/归档 |
| `[DOC]` | 文档/SOP 更新 |

**更新 STATUS.md**（追加一行）：
```markdown
| 2026-08-28 | 铅 4.1 子页 v5 上线：新增 N 图，全真数据；指标库 v1.4 (+i37) | 线B |
```

**线上验证**（**必须做，不能只看 git log**）：
```bash
# 1. 看 CDN last-modified
curl -sI https://algo23-yunqingtian.github.io/framework-tree/pb_stock_v2.html

# 2. 绕过 CDN 强刷
curl -s "https://algo23-yunqingtian.github.io/framework-tree/pb_stock_v2.html?nocache=$(date +%s)" | grep "版本\|v5\|N图"

# 3. grep 关键特征字（版本号/快照日期/图数）确认内容
```

> ⚠ CDN 缓存 TTL 600s，push 后 1-2 分钟内可能还是旧版，用户问「还是旧版」时告知「F5 + 再等 1 分钟」

---

## 三、目录树全节点索引（33 个节点）

| 大类 | 节点 | 当前状态 |
|---|---|---|
| 2 价格信号 | 2.1盘面/2.2现货/2.3海外/2.4价差/2.5估值/2.6持仓 | ❌ 待做 |
| 3 供给 | 3.1.1-3.1.5矿端 / 3.2.1-3.2.4冶炼端 | ❌ 待做 |
| **4 库存** | **4.1-4.5** | **✅ 已跑通（范例）** |
| 5 需求 | 5.1初级消费/5.2终端细分/5.3先行指标 | ❌ 待做 |
| 6 进出口 | 6.1原料/6.2精炼/6.3制品/6.4海外发运 | ❌ 待做 |
| 7 成本·利润 | 7.1成本曲线/7.2日度利润/7.3能源成本 | ❌ 待做 |
| 8 供需平衡 | 8.1年度锚/8.2自建平衡/8.3表观拟合 | ❌ 待做 |

> 已移走的库存期 C15/C12/C17/C18（沪伦比值/再生产量/精矿进口/精矿产量）数据已在缓存，供给目录建页时直接接入。

---

## 四、坑速查表

| 坑 | 症状 | 解法 |
|---|---|---|
| search 不传 source | 全部返回 0，误判没数据 | `zhiji_api.py search 关键词 smm 5` 显式传 |
| 单关键词搜索漏指标 | 大量"骨架/找不到" | 多关键词发散（品种+长名+分项），实测 8 张骨架一次解锁 3 张 |
| zhiji_id 缓存在版本间漂移 | indicators_v1.json 更新了 ID，缓存还是旧 ID，图值域对但日期老 | 每次 bump JSON 后**必须**跑 refresh_cache.py |
| 缓存 metric key 冲突 | 旧映射占用了 i19/i20，v4 又想用另一组 → 图意不符 | 分配前 `SELECT metric FROM indicator_cache` 排冲突 |
| series 输出含控制字符 | `json.loads` 炸 | 用 `json.loads(stdout, strict=False)` |
| 指标名≠数值语义 | 画出来误导（如「进口盈亏」实为价格水平） | 画图前 `series` 拉值域：真盈亏应围绕 0 震荡 |
| 进口总量序列查不到 | 只有美/新/泰海关分国别 | 中国进出口总量需换海关总署外部源 |
| points 倒序 | 截图/最新值显示成旧数据 | build 时反转成正序 |
| 季节性图当前年越界 | `KeyError: 2026` | 只把「前 N-1 个完整年」纳入分位，当前年单独作线 |
| Werkzeug dev server 崩 | `PackageNotFoundError: werkzeug` | 用 `python3 -m http.server` 或 gunicorn |
| ECharts CDN 加载失败 | 页白 | 离线化 echarts.min.js 进仓库 |
| gh push 超时 | `Command timed out` | 走 SSH remote |
| Pages build failed | 连续 errored，新页 404 | **加 `.nojekyll` 禁用 Jekyll**（SOP/doc 内 `{占位符}` 被 Liquid 当模板变量解析崩溃。根目录放空文件 `.nojekyll` 即可） |
| ECharts 图白屏 | ECharts 5 加载成功但图内无数据 | **查 `__d` 等 JS 变量赋值顺序**：`data:__d` 引用必须**晚于** `window['__data_*']=[]` 赋值行（6.2 示范踩坑：数据赋在 `__d` 引用后面，`__d` 为 undefined 致 `echarts.init` 静默失败，`window['__inst_*']` 为空） |
| ECharts 图白屏 | 代码里 `{{ }}` 双重花括号 | **避免 `esc()` 与 f-string `.replace()` 混用**：esc() 把 `{` 变 `{{`，再 replace 就变 `{{{{`；改用 `%s` 格式化 + 逐段 `+` 拼接 JS 字符串 |
| 浏览器禁本地地址 | 127.0.0.1 拒 | 走本机外网 IP 或线上 Pages |
| 长 prompt 注入被截 | `browser_console` 表达式超长度 | 用 base64 分段注入或手工粘贴 |
| `cmd_series`/`cmd_search` 直接调用 | 返回 None | 必须 `subprocess.run` 调 CLI |

---

## 五、文件索引（速查）

| 文件 | 用途 |
|---|---|
| `scripts/refresh_cache.py` | **统一缓存刷新**（v1.3 合并版，替代旧两脚本） |
| `scripts/refresh_cache_i6_i18.py` | ⚠ DEPRECATED（历史存档） |
| `scripts/refresh_v4_new_ids.py` | ⚠ DEPRECATED（历史存档） |
| `scripts/build_pb_v2.py` | 看板构建脚本（模板） |
| `scripts/data_layer.py` | 实时 API 数据层（待清理双维护） |
| `scripts/api_server.py` | 本地查询服务（8786） |
| `scripts/api_cache.db` | 时序缓存（不推 GH） |
| `scripts/indicator_correction.db` | 纠错库 |
| `data/indicators_v1.json` | **指标 ID 主映射（唯一真源）** |
| `prompt_lib/render_prompt.py` | Prompt 渲染器 |
| `prompt_lib/batch_render.py` | 批量渲染 |
| `prompt_lib/template_v19.md` | 零领域词模板（永不改） |
| `prompt_lib/dimensions/{库存,供应,需求}.json` | 维度词库 |
| `prompt_lib/varieties/PB.json` | 铅业内术语 |
| `analysis/iwencai/PB/zhiji_batch_verify.py` | 知几批量验证（可 `--input` 读外部清单） |
| `pb_prompt/Pb_看板指标定稿_v4.md` | 铅库存定稿 v4（最新版） |
| `pb_stock_v2.html` | 铅库存 v4 主看板（22 图） |
| `pb_41_stock.html` | 铅 4.1 子页 |
| `STATUS.md` | 项目全局状态（唯一真源） |
| `COLLABORATION.md` | 两线隔离机制 |

---

> **维护者**：本文档应与 `handover_next_20260827.md`（任务交接）+ `STATUS.md`（状态）+ `COLLABORATION.md`（协作）配合使用。
> **更新规则**：SOP 变更后 `git commit [DOC]` + 更新 STATUS.md 记录。