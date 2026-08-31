# 三表灌库 · 框架设计决策文档

> 本文档记录三表灌库的**框架设计决策与背景**，供主脑与后续 agent 追溯"为什么这么做"。
> 任务执行细节见配套的任务卡 `HANDOVER_DB_LOAD_TASKCARD.md`。
> 主脑定稿时间：2026-08-31

---

## 0. 一句话结论

**指标元数据（786 条）与灌库脚本（`analysis/spec/db_load.py`）已由主脑完成并验收；时序数据拉取（614 个指标待拉）已委派给另一台服务器的 agent。**

DB 现状：`indicator_meta` 836 行 / `indicator_series` 196,985 行 / 有数据指标 172 个（20.6%）/ 外键孤立 0。

---

## 1. 历史背景与"三表"表述误差

- **2026-08-26** 定稿 `analysis/spec/db_design.md`：只定义**两表**（`indicator_meta` + `indicator_series`）
- **交接文档（v5）反复称"三表灌库"**：这是**表述误差**，spec 正文只有两表，无第三表定义
- **决策**：按 spec 的**两表**实现。交接文档中的"三表"一词统一理解为"元数据层 + 时序层"的整体灌库工作，不额外造第三表

> 若后续确实需要第三表（如 `indicator_relation` 指标关联表，用于跨指标交叉验证关系），需主脑单独评审后新增，当前不做。

---

## 2. ID 体系决策（最关键，解决了交接文档的核心阻塞）

### 2.1 交接文档标注的阻塞

交接 v5 §4 待办 #4 原文：

> 三表灌库（indicator_meta/series，spec 已定 `analysis/spec/db_design.md`） | 主脑 | **五金属注册后一次性灌（现在做会返工：ID 体系 CUS 前缀 vs IND 三段式冲突）**

即：spec 用 `IND-ZN-stock-01` 三段式，而现有数据是 `i1`/`j21_close`/`cu_21_import`/`CUS-08-1-1-xxxx` 等混杂前缀，直接照 spec 灌会造成大规模映射返工。

### 2.2 决策：**采用 `indicators_v1.json` 的 key 作为 `indicator_id`**，不造 IND 三段式

| 方案 | 评价 |
|---|---|
| ❌ 照 spec 用 `IND-ZN-stock-01` | 需为 786 条指标建映射表，且 spec 每子目录限 9 个（序号 01-09），实际单节点常有 10+ 指标，**必然返工** |
| ❌ 沿用 data-harbor 的 `CUS-08-{1-6}-{0-12}` | 那是 LME 月价 78 指标的专属编码（memory 记录），与看板指标体系不同源 |
| ✅ **用 indicators_v1.json 的 key** | `MIGRATION_FOR_LINE_B.md` 已钦定"统一到一个文件 `indicators_v1.json`"；key 已全局唯一、已含品种前缀语义（`cu_21_`/`zn_311_`）、已被 75 页 build 脚本引用 |

**多品种展开规则**（解决 1 个 key 对应多个品种的问题）：

```
indicator_id = f"{key}:{variety}"    例: j21_close:PB / zn_311_output:ZN / 主连:CU
```

- `主连` 的 ids 含 8 个品种 → 展开成 8 行（`主连:CU` / `主连:AL` / ...），每行一个独立 zhiji_id
- `zn_311_output` 只对应 ZN → 1 行
- 展开后 meta 共 **836 行**（786 key → 836 行，因部分 key 多品种）
- `variety_points` 取数时按 `code in ids` 过滤，避免跨品种数据串台

### 2.3 为什么不建映射表

`indicators_v1.json` 的 key 已在以下位置成为事实标准：

| 位置 | 引用方式 |
|---|---|
| `scripts/chart_kits.py` `load_metric(mid)` | 直接传 key（如 `load_metric("j21_close")`） |
| `scripts/api_cache.db` `metric` 字段 | 存 key（i1/j21_close/cu_21_import） |
| `indicators_v1.json` `_nodes` 字段 | 节点归属 |
| 75 个 build 脚本 | 硬编码 key |

**建映射表 = 在已统一的体系上再叠一层间接**，属过度设计。直接复用 key 是零成本方案。

---

## 3. category 字段推导规则

spec 要求 `category` 为 `price/supply/stock/demand/trade/cost/balance` 七值，数据源用 `data/tree_config.json` 的 `categories[].code`（板块号）+ 指标 `_nodes` 字段：

| 节点前缀 | category | spec 原值 | 说明 |
|---|---|---|---|
| 2.x | `price` | price | 价格信号 |
| 3.x | `supply` | supply | 供给 |
| 4.x | `inventory` | stock | **改用 inventory**（更准确，spec 的 stock 偏仓单） |
| 5.x | `demand` | demand | 需求 |
| 6.x | `trade` | trade | 进出口 |
| 7.x | `cost` | cost | 成本利润 |
| 8.x | `balance` | balance | 供需平衡（板块 8 不做图表，仅备用） |

**回退规则**（265 条指标无 `_nodes`，如 `主连`/`LME库存`/`社库`/`TC` 等早期通用指标）：

```
key 前缀 i* → inventory
key 前缀 j* → price
key 前缀 t* → price
其他        → price (默认)
```

> 回退准确率较低（如 `社库` 应归 inventory，但其 key 无 i 前缀）。如需精确，主脑后续可补 `_nodes` 字段到 indicators_v1.json。

**实测分布**：price 315 / supply 233 / inventory 129 / trade 73 / cost 50 / demand 36。

---

## 4. 表结构与 spec 的差异

| 项 | spec 定义 | 实际实现 | 原因 |
|---|---|---|---|
| `indicator_meta` 字段数 | 11 | **15** | 增加 `key`（便于 JOIN）、`node`（节点号）、`tier`（A/B 分层）、`origin`（Step3 溯源）、`has_series`（快速判断有无数据） |
| `indicator_series` 字段 | 3（含 `id` 自增） | **3** | 去掉自增 id（`indicator_id+date` 已足够唯一，节省空间） |
| 索引 | 5 个 | **6 个** | 增加 `idx_category`、`idx_key`（spec 第四节查询模式高频用到） |
| `status` 字段 | active/deprecated | 保留 | 全部初始化为 active |
| `chart_type` / `threshold` 字段 | spec 有 | **未建** | 看板实际未使用（chart_kits 硬编码图表类型），待 Step4 建页时需要再加 |

---

## 5. 数据流架构

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│ indicators_v1   │     │  api_cache.db     │     │  indicator_tree.db   │
│ .json (786 key) │     │  (172→836 目标)   │     │  (交付物, 线B)       │
│                 │     │                  │     │                      │
│ 元数据唯一真源   │     │  拉数缓存(不推GH) │     │  meta 836 / series   │
└────────┬────────┘     └────────┬─────────┘     └──────────▲───────────┘
         │                       │                          │
         │        ┌──────────────┴───────────┐              │
         └───────>│  analysis/spec/db_load.py │─────────────┘
                  │  (灌库脚本, 主脑已验收)    │
                  └──────────────────────────┘

外部: zhiji_api.py (search/series/kline) → 写入 api_cache.db
```

**分工**：
- `indicators_v1.json`：元数据唯一真源（主脑独占）
- `api_cache.db`：zhiji 原始响应缓存（不推 GitHub，本地重建）
- `indicator_tree.db`：交付物，供看板/API 读取（线B 目录，不推 GitHub）

---

## 6. 已完成的验证（主脑，2026-08-31）

| 项 | 结果 |
|---|---|
| JSON 合法性 | ✓ |
| meta 行数 | 836（786 key × 品种展开） |
| series 行数 | 196,985 |
| 有数据指标 | 172 / 836（20.6%） |
| 外键孤立 series | **0**（series 中每个 indicator_id 都在 meta 中） |
| spec 4 种查询模式 | 全部跑通（按品种+子目录 / 单指标时序 / 全品种横向对比 / 有数据过滤） |
| api_cache 172 条 key 是否都在 indicators_v1.json | ✓ 全部匹配（0 缺失） |
| code 是否都在该指标 ids 中 | ✓ 全部匹配（0 缺失） |
| value 类型 | 全 float（无字符串混入） |

---

## 7. 已知缺口（委派任务范围）

| 缺口 | 规模 | 处理方 |
|---|---|---|
| 五金属 (ZN/NI/SN/SI/LI) 时序数据 | **621 条待拉**（五金属 meta 621 行） | 委派 agent |
| 铜铝缺口节点（4.4/4.5/5.2/5.3/6.3/7.x） | 需先建页定指标，非本次范围 | 主脑/铜铝 agent |
| `chart_type` / `threshold` 字段 | meta 表未建，Step4 建页时需补 | 主脑评审 |
| 265 条无 `_nodes` 指标的 category 精确化 | 回退规则准确率有限 | 主脑后续补字段 |
| 铅库存 8 骨架补 5 张 | 需问财发散/外部源，非灌库范畴 | 线B |

---

## 8. 2026-08-31 数据覆盖事故（记录在案）

**事件**：主脑推 `adc3c41`（196→786，五金属 590 条注册）后，另一并行 agent 基于旧基线 196 重跑注册，连推 `56a3a69`→`9801dee`，**覆盖丢弃 590 条**（786→362）。

**关键事实**：
- 对方 166 条的 zhiji_id **100% 重叠**于主脑 590 条 → 对方是真子集，仅完成 29%
- 对方声称"253 拉数成功"**未落地**（api_cache.db 仍 172 行，五金属 0 条）
- 主脑从 git 历史 `adc3c41` 完整恢复，提交 `4d012a6`

**教训 → 已写入任务卡第 2 节护栏**：
1. 并行注册/建页必须走 `docs/AGENT_PARALLEL_PROTOCOL.md` 的 git worktree 隔离
2. 开工前必跑 `bash scripts/bootstrap_agent.sh` 校验基线指标数（对方若自检会报红色阻断）
3. `indicators_v1.json` 只主脑改，委派 agent 只做拉数写 `api_cache.db`

---

## 9. 文件清单

| 文件 | 状态 | 归属 |
|---|---|---|
| `analysis/spec/db_design.md` | 原始设计（2 表定义） | 线B |
| `analysis/spec/db_load.py` | 灌库脚本（已验收，勿改） | 主脑 |
| `analysis/spec/HANDOVER_DB_LOAD_TASKCARD.md` | 委派任务卡（执行细节） | 主脑 → agent |
| `analysis/spec/HANDOVER_DB_LOAD_SPEC.md` | 本文档（设计决策） | 主脑 |
| `analysis/db/indicator_tree.db` | 交付物（不推 GitHub） | 线B |
| `analysis/db_backups/` | 旧库备份 | 线B |
| `framework-tree/data/indicators_v1.json` | 元数据真源 786 条 v3.43 | 主脑独占 |
| `framework-tree/scripts/api_cache.db` | 拉数缓存（不推 GitHub） | 委派 agent 写入 |
| `framework-tree/STATUS.md` | 状态真源 | 主脑独占 |
