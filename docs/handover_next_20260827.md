# 📋 framework-tree 下一轮任务交接 — 2026-08-27

> **入口**：本文件是唯一真源。下一轮对话先读本文件，按「一、任务清单」顺序执行。
> **配合**：`STATUS.md`（全局状态）、`COLLABORATION.md`（两线隔离机制）、`prompt_lib/README.md`（词库用法）。
> **当前主线状态**：铅(PB)库存子页 v4 定稿已完成并上线（15 图全真数据），可作其余品种/目录的**模板范例**。

---

## 一、下一轮任务清单（按顺序执行）

### 🥇 T1. 向用户演示「数据存储结构」全景
已完成于 2026-08-27 对话（本轮已演示，见下方「三、数据库结构」）。若用户还要，可补做：
- 用 `sqlite3 .schema` 实际输出三个库的建表语句
- 用 `sqlite3 "SELECT * FROM indicator_cache LIMIT 3"` 展示真实行数据

### 🥇 T2. 脚本优化 / 代码压缩检查
对以下已跑通脚本做一轮瘦身审查（只读审查 + 必要的 patch，不要重写）：
1. `scripts/refresh_cache_i6_i18.py` + `scripts/refresh_v4_new_ids.py` — **两脚本结构重复** → 可合并成 `scripts/refresh_cache.py --target i6-i18|v4new|all`，减少维护面
2. `scripts/build_pb_v2.py`（34KB）— 五个 `build_4x()` 函数有大量重复的 `chart_dual/chart_line_t/chart_multiline` 调用，可考虑用「图表配置 dict + for 循环」压缩 30-40% 代码量（**不建议本轮做**，风险大；留待品种批量化时一起做）
3. `scripts/api_server.py` + `scripts/data_layer.py` — data_layer.py 的 INDICATORS dict 与 `data/indicators_v1.json` **两处维护**，应该只读 json 单一来源（待办，涉及 api_server 联动，需谨慎）

### 🥇 T3. 标准化流程固化（README 化）
将「同花顺提问 → 指标筛选 → 画图存档 → 推送 GitHub → 数据库管理」整套 SOP 写成
`framework-tree/docs/SOP_pipeline.md`（**核心交付**，让零基础 agent 阅读后能独立维护）。
SOP 内容框架见下方「四、标准化流程（已跑通的铅库存范例）」。

### 🥈 T4. 批量跑「铅(PB) 全部目录树节点」
用户期望：铅目录树共 **8 大类 / 33 个指标叶节点**（不 是9/10 个），每个节点走完整流程 → 产出指标 + 图 + 同步 GitHub。

| 大类 | 节点 | 当前状态 |
|---|---|---|
| 2 价格信号 | 2.1盘面/2.2现货/2.3海外/2.4价差/2.5估值/2.6持仓 | ❌ 未动（库存专注期） |
| 3 供给 | 3.1.1-3.1.5 矿端 / 3.2.1-3.2.4 冶炼端 | ❌ 未动（移走的 C15/C12/C17/C18 数据已在缓存，可复用） |
| **4 库存** | **4.1-4.5** | ✅ **已跑通（本轮）** |
| 5 需求 | 5.1初级消费/5.2终端细分/5.3先行指标 | ❌ 未动 |
| 6 进出口 | 6.1原料/6.2精炼/6.3制品/6.4海外发运 | ❌ 未动 |
| 7 成本·利润 | 7.1成本曲线/7.2日度利润/7.3能源成本 | ❌ 未动 |
| 8 供需平衡 | 8.1年度锚/8.2自建平衡/8.3表观拟合 | ❌ 未动 |

**执行方式**（逐个节点）：
```
1. 用 prompt_lib 渲染该节点的同花顺 prompt：python3 prompt_lib/render_prompt.py --dim <维度> --variety PB --subdirs "4.1...|4.2..." 
2. 粘贴同花顺 browser 提问 → 存档 analysis/iwencai/PB/<节点>_vXX_<日期>.md
3. 用 zhiji_batch_verify.py（复制模板改 kw）跑知几命中 → A/B/C 分级
4. 验证 ID 写入 data/indicators_v1.json（version bump）
5. 建子页 HTML（仿 pb_41_stock.html 或 build_pb_v2.py 的模块化函数）
6. git commit + push（[DATA] 前缀）
```
**注意**：一个节点一个 commit，别一把梭；每个节点完成后在 STATUS.md 加一行。

### 🥈 T5. 单品种全量数据向同花顺校准机制
用户背景：同花顺 v19 给的是「研报关注度」视角，可能漏细分仓库/分地区（本轮 LME 新加坡系列就是它漏的）。
机制设计（待执行）：
1. 把 PB 定稿 + 知几命中情况（A/B/C）整理成一份「校准包」
2. 发给同花顺：让它评审「哪些不可得有替代 / 哪些子类漏了 / 复合图组合是否专业」
3. 回传后人工审核 → 更新 v5 定稿 → 重跑命中 → 更新 indicators_v1.json
4. 产物存 `analysis/iwencai/PB/calibration_<日期>.md`

---

## 二、工具/脚本索引（已跑通）

| 文件 | 功能 | 用法 |
|---|---|---|
| `~/.hermes/scripts/zhiji_api.py` | 知几 API v2 客户端（search/series） | `python3 zhiji_api.py search 关键词 all 5` |
| `prompt_lib/render_prompt.py` | 渲染同花顺 prompt（模板零领域词） | `--dim 库存 --variety PB --subdirs "4.1...|4.2..." -o out.md` |
| `prompt_lib/batch_render.py` | 批量渲染（batch_config.json 驱动） | `--config prompt_lib/batch_config.json` |
| `analysis/iwencai/PB/zhiji_batch_verify.py` | 批量 search→命中判断（空格分词策略） | 改 NEW_INDICATORS 后运行 |
| `scripts/refresh_cache_i6_i18.py` | 按 indicators_v1.json 刷新 i6-i18 | 直接运行 |
| `scripts/refresh_v4_new_ids.py` | v4 新发现 ID（新加坡系列等）入缓存 | 直接运行 |
| `scripts/build_pb_v2.py` | 从 api_cache.db 构建 pb_stock_v2.html + pb_41_stock.html | 直接运行 |
| `scripts/data_layer.py` | 指标树实时 API 数据层（SQLite+增量） | `python data_layer.py status` |
| `scripts/api_server.py` | 本地查询 API（8786 端口） | `python3 api_server.py 8786` |

---

## 三、数据库结构（已实测）

### 3.1 `framework-tree/data/indicators_v1.json` — 指标 ID 主映射（唯一真源）
```
_meta: {version, updated, status, 说明, 验证规则}
version_changelog: [{v, date, change}]  ← 每次改动必须追加
indicators:
  通用指标(主连/LME库存/SHFE库存/社库/TC/精炼产量/表观消费/开工率): {name,unit,freq,verified,ids:{CU,AL,PB,...}}
  i1..i36 品种专属: {name,unit,freq,verified,category,ids:{PB:zhiji_id}}
```
**维度标注**：name / unit（单位）/ freq（频率）/ verified（是否搜索→series 实测过）/ category（inventory 等）/ ids（品种→ID）

### 3.2 `framework-tree/scripts/api_cache.db` — 时序缓存（SQLite）
```
表 indicator_cache:
  code(PB) | metric(i1..i36) | zhiji_id | data_json{id,source,name,unit,freq,points[]} | fetched_at | error_msg | name | unit | freq
```
- 36 条 = 36 个已缓存指标，points 存 [{date,value}]
- 反拷贝保护前提下本地全部时序，GitHub 不推 DB

### 3.3 `framework-tree/scripts/indicator_correction.db` — 纠错库（同花顺→知几映射纠偏）
```
表 correction: id | indicator | subcat_from | subcat_to | error_type(misattribute等) | reason | suggested_action | revive_condition | source_ver | created_at | status(merged_into_4.4等)
表 correction_log: id | correction_id | action | note | changed_at
```
- 8 条纠错记录（如「铅精矿工厂库存」从 4.4 纠正到 4.6→再并入 4.4）

### 3.4 `prompt_lib/` — Prompt 词库（模板 + 维度词库 + 品种词库）
```
template_v19.md（零领域词，永远不改）
dimensions/库存.json   ← positive_keywords/compound_themes/usage_examples/boundary_tips
dimensions/供应.json
dimensions/需求.json
varieties/PB.json      ← industry_terms（业内术语）
batch_config.json      ← 批量任务清单
```

---

## 四、标准化流程（铅库存已跑通范例 SOP）

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1  同花顺提问（发散指标）                                 │
│   prompt_lib/render_prompt.py --dim 库存 --variety PB        │
│   → pb_prompt/prompt_v19_PB_库存.md → 粘贴同花顺 browser      │
│   → 存档 analysis/iwencai/PB/stock_vXX_<日期>.md             │
├─────────────────────────────────────────────────────────────┤
│ STEP 2 指标筛选（vN 定稿）                                    │
│   人工审核：删价格类 / 合并子类(4.6→4.4) / 标注不可得          │
│   → pb_prompt/Pb_看板指标定稿_vN.md                          │
├─────────────────────────────────────────────────────────────┤
│ STEP 3 知几命中（A/B/C 分级）                                 │
│   zhiji_batch_verify.py（空格分词策略：主连写+辅空格）         │
│   → analysis/iwencai/PB/vN_zhiji_verified_<日期>.json        │
├─────────────────────────────────────────────────────────────┤
│ STEP 4 指标库入库（indicators_v1.json v-bump）               │
│   A=verified:true，B=占位，C=不入库 → git commit [DATA]      │
├─────────────────────────────────────────────────────────────┤
│ STEP 5 拉数据（refresh_cache_*.py → api_cache.db）           │
│   批量 search→series 落 SQLite，1 秒/次限频                    │
├─────────────────────────────────────────────────────────────┤
│ STEP 6 画图存档（build_pb_v2.py → *.html）                   │
│   Dark ECharts 一行两图；骨架置底；日期动态                   │
├─────────────────────────────────────────────────────────────┤
│ STEP 7 推送 GitHub Pages + STATUS.md 更新                    │
│   git add -A && commit [V4-DRAFT]/[REFRESH]/[CLEANUP] && push│
│   CDN 缓存 ~10 分钟，F5 刷新可见                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 五、关键卡点 / 已知问题

| # | 卡点 | 建议 |
|---|---|---|
| 1 | GitHub Pages CDN 缓存 600s，push 后用户看到旧版 | 告知用户「F5 + 等 1-2 分钟」 |
| 2 | data_layer.py 与 indicators_v1.json 双维护 | 长期改为 data_layer 只读 json |
| 3 | 4.3 社库分持有者/分品种 = 无公开数据（C 级） | 定稿里标注"不可得"，不硬画 |
| 4 | i29/i30 等 v4 新增 ID 已入缓存未在页面使用完 | T4 建图时接入 |
| 5 | build_pb_v2.py 34KB 有重复 | 批量品种化时重构 |

---

## 六、文件索引

```
framework-tree/
├── STATUS.md                        # 全局状态（唯一真源）
├── index.html                       # 主站目录树（PAGE_MAP 跳转 pb_stock_v2.html?tab=X）
├── pb_stock_v2.html                 # 铅库存 v4 定稿主看板（15 图全真）
├── pb_41_stock.html                 # 4.1 子类独立页
├── data/indicators_v1.json          # 指标 ID 主映射（v1.2）
├── prompt_lib/                      # Prompt 词库（模板+维度+品种）
├── pb_prompt/                       # 铅专项投喂记录+定稿
├── scripts/
│   ├── build_pb_v2.py               # 看板构建（最新版含 v4 布局）
│   ├── refresh_cache_i6_i18.py      # 缓存刷新（部分）
│   ├── refresh_v4_new_ids.py        # 缓存刷新（v4 新发现）
│   ├── data_layer.py                # 实时 API 数据层
│   ├── api_server.py                # 本地查询服务
│   ├── api_cache.db                 # 时序缓存（不推 GH）
│   └── indicator_correction.db      # 纠错库
├── legacy/20260826_pb_stock_v1/     # v1 旧版归档
└── docs/SOP_pipeline.md             # ← 本轮待建（T3）
```