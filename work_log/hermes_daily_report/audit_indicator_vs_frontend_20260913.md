# 审计报告：看板指标定义 vs GitHub Pages 前端图表一致性核验

> **审计日期**：2026-09-13  
> **审计分支**：`origin/indicator-correction-win`（HEAD = `38bf48c`）  
> **审计人**：主脑 Agent（GLM-5.2）  
> **审计模式**：只读，未修改任何源码  

---

## 〇、审计摘要

| 维度 | 数值 |
|---|---|
| 分支 HTML 页面总数 | 311 |
| 分支 ECharts 图表总数 | 1,394 |
| chart_registry.json 覆盖页 | 210 页 / 596 图（**覆盖率 69.5%**） |
| chart_registry.json 未覆盖页 | 50 页 / 798 图（**57.3% 的图表无注册**） |
| 指标串台（主图指标语义≠节点板块） | 327 条 |
| 自身重复 "vs" 标题 | 62 条 |
| GitHub Pages 部署版本 vs 分支 HEAD | **一致**（al_2_1.html md5 完全相同） |

**结论**：GitHub Pages 部署版本与 `indicator-correction-win` 分支 HEAD 同步。但前端与指标文档/注册表之间存在**大规模结构化偏差**，集中在五金属（非铅）品种和 LI（碳酸锂）品种的"板块聚合页"。

---

## 一、文档与配置真源定位

### 1.1 指标元数据真源

| 文件 | 路径 | 版本 | 指标数 |
|---|---|---|---|
| indicators_v1.json | `data/indicators_v1.json` | v3.48 (2026-09-02) | 930 条 |
| tree_config.json | `data/tree_config.json` | — | 8 品种 × 7 大类 × 33 节点 |
| chart_registry.json | `data/chart_registry.json` | v1.0 (2026-08-31) | 259 页 / 596 图 / 49 异常 |

- `indicators_v1.json` 为 dict 结构，含 `_meta`（版本+验证规则）、`indicators`（930 key）、`64_group`（6.4 海外发运组合定义）。
- `tree_config.json` 定义 8 品种（CU/AL/PB/ZN/NI/SN/SI/LI）× 7 大板块（价格2/供给3/库存4/需求5/进出口6/成本利润7/供需平衡8）× 33 子节点，每节点含 `q`（定义）、`comms`（适用品种）。
- `chart_registry.json` 由 `scripts/build_chart_registry.py` 正则+规则引擎自动生成，**仅覆盖 210 页**（下文详述）。

### 1.2 绘图规则文档

| 文档 | 路径 | 用途 |
|---|---|---|
| CHART_REGISTRY.md | `docs/CHART_REGISTRY.md` | 人类可读全表+异常报告 |
| PAGE_SPEC.md | `docs/PAGE_SPEC.md` | 页面规范 |
| METHODOLOGY_INDICATOR_CORRECTION.md | `docs/METHODOLOGY_INDICATOR_CORRECTION.md` | 指标修正方法论 |
| COLLABORATION_PLAYBOOK.md | `docs/COLLABORATION_PLAYBOOK.md` | 11 章全流程含格式契约 |
| chart_kits.py | `scripts/chart_kits.py` | 公共 Build 模块（CSS+JS+图表函数） |

### 1.3 绘图规则要点（从 chart_kits.py + tree_config.json 提取）

- **图表类型**：`chart_line_t`（单指标时序⇄季节双模式）、`chart_dual`（双轴复合）、`chart_triple`（三系列堆叠面积）
- **坐标轴**：左轴/右轴双轴制，`scale: true` 自适应
- **更新频率**：daily/weekly/monthly/quarterly，由 `indicators_v1.json` 的 `freq` 字段决定
- **指标口径备注**：每图 `.chart-note` 段落含"什么时候看/怎么看"说明
- **反拷贝**：`oncontextmenu/onkeydown/onselectstart` 全禁

---

## 二、前端硬编码指标提取

### 2.1 全量统计

| 品种 | HTML 页数 | ECharts 图表数 |
|---|---|---|
| 铅 PB | 37 | ~120 |
| 铜 CU | 34 | ~150 |
| 铝 AL | 35 | ~80 |
| 锌 ZN | 42 | ~210 |
| 镍 NI | 43 | ~330 |
| 锡 SN | 41 | ~190 |
| 硅 SI | 39 | ~170 |
| 锂 LI | 38 | ~140 |
| **合计** | **311** | **1,394** |

### 2.2 前端图表结构

每个数据页 `*.html` 的图表块结构：
```html
<div class="chart">
  <div class="chart-title">{指标名}（主图·{节点}）</div>
  <div class="chart-sub">{indicator_id} · {freq} · {unit} · {data_points}点</div>
  <div id="echart_{品种}_{节点}_c{序号}" style="height:320px"></div>
  <div class="chart-note">📌 什么时候看：...怎么看：...</div>
</div>
```

- 指标 ID 格式：`{品种}_{序号}_{语义名}`（如 `al_00_openinterest_front`）
- 节点标记：标题尾部 `（主图·2.1）` 或 `（补充·2.1）`
- ECharts 初始化：`echarts.init` + `setOption`，数据内嵌 JSON

---

## 三、差异审计清单

### 3.1 缺陷类型 A：chart_registry 未覆盖页（文档有定义，注册表无记录）

**严重度**：🔴 高  

`chart_registry.json` 仅覆盖 210/311 页（69.5%），50 页共 798 图未进入注册表。

**根因**：`build_chart_registry.py` 的正则 `parse_node_code` 对以下页面格式不识别：
- **板块聚合页**（`zn_3.html` / `ni_2.html` / `li_3.html` 等）：文件名只有 1 位板块号，无子节点号
- **品种首页**（`zn_0.html` / `cu_0.html` 等）：node=0 不在 2-8 范围
- **碳酸锂子节点**（`li_2_3.html` / `li_3_1_4.html` 等）：格式未被正则匹配

**未覆盖页按品种分布**：

| 品种 | 未覆盖页数 | 未覆盖图表数 |
|---|---|---|
| 锌 ZN | 7 | 157 |
| 镍 NI | 6 | 217 |
| 硅 SI | 6 | 127 |
| 锡 SN | 6 | 124 |
| 锂 LI | 17 | 94 |
| 铝 AL | 4 | 26 |
| 铜 CU | 3 | 30 |
| 铅 PB | 1 | 0（仅 pb_stock_v2 归档页） |

**Top 10 未覆盖页（按图表数）**：

| 页面 | 图表数 | 说明 |
|---|---|---|
| ni_3.html | 70 | 镍供给板块聚合页 |
| ni_2.html | 65 | 镍价格板块聚合页 |
| zn_3.html | 57 | 锌供给板块聚合页 |
| ni_4.html | 53 | 镍库存板块聚合页 |
| li_3.html | 40 | 锂供给板块聚合页 |
| si_3.html | 40 | 硅供给板块聚合页 |
| sn_3.html | 40 | 锡供给板块聚合页 |
| zn_0.html | 39 | 锌品种首页 |
| sn_2.html | 28 | 锡价格板块聚合页 |
| li_2.html | 26 | 锂价格板块聚合页 |

### 3.2 缺陷类型 B：指标串台（前端渲染了不属于该节点的指标）

**严重度**：🔴 高  

**判定方法**：提取每页 `hcrumbs` 的节点号（如"2 价格信号"），与 `chart-title` 中主图指标名做关键词规则匹配（与 `build_chart_registry.py` 的 `KEYWORD_RULES` 一致）。

**总计 327 条串台**（排除 `vs` 复合图和散文式标题后）：

| 品种 | 串台数 | 典型问题 |
|---|---|---|
| 锌 ZN | 93 | zn_3.html 供给页含大量库存/进出口指标；zn_7.html 成本页含升贴水/产量 |
| 镍 NI | 82 | ni_2.html 价格页含冶炼利润/仓单/进口盈亏；ni_4.html 库存页含升贴水 |
| 硅 SI | 35 | si_2.html 价格页含库存/利润；si_4.html 库存页含多晶硅指标 |
| 锡 SN | 32 | sn_2.html 价格页含库存/利润；sn_3.html 供给页含进口量 |
| 锂 LI | 31 | li_2.html 价格页含全部板块指标；li_3.html 供给页含进口/库存/利润 |
| 铜 CU | 20 | cu_0.html 含家电/汽车产量；cu_2_1 含进口盈亏 |
| 铝 AL | 20 | al_3_2_3 供给页含废铝进口；al_5_1 需求页含电解铝开工率 |
| 铅 PB | 14 | pb_314 供给页含海关进口量；pb_324 含再生铅利润 |

**高频串台模式**（按应属板块）：

| 串台方向 | 次数 | 典型案例 |
|---|---|---|
| 供给指标→库存页 | 37 | "SMM: 国内电解铝厂内库存" 出现在 al_4_3（库存页）但指标名含"电解铝"触发供给规则 |
| 进出口指标→供给页 | 64 | "锌矿砂及其精矿：进口数量" 出现在 zn_3（供给页）但"进口"触发进出口规则 |
| 精炼产量→需求页 | 77 | "电解铝：消费量" 出现在 al_5_2（需求页）但"电解铝"触发供给规则 |
| 成本利润→价格页 | 28 | "冶炼利润" 出现在 li_2/sn_2（价格页） |
| 库存→价格页 | 37 | "仓单" 出现在 ni_2/sn_2（价格页） |

> **注**：部分串台为**设计意图**（如板块聚合页 li_2/ni_2/sn_2 是五金属"全板块一览"页，刻意收录跨板块指标做总览）。但 node 页（如 `al_3_2_3` 供给·再生）出现非本节点指标属于真实缺陷。

### 3.3 缺陷类型 C：自身重复 "vs" 标题

**严重度**：🟡 中  

62 条图表标题为 `A vs A` 格式（两侧指标名完全相同），如：
- `LME：铝：注销仓单（日） vs LME：铝：注销仓单（日）`（al_4_1.html）
- `SHFE：电解铜：主力合约：收盘价（日） vs SHFE：电解铜：主力合约：收盘价（日）`（cu_2_4.html）
- `碳酸锂：碳化法：生产利润（日） vs 碳酸锂：碳化法：生产利润（日）`（li_2_5.html）

**根因**：`chart_dual` 函数在拼装 `A vs B` 标题时，两个指标的 `name` 字段相同（近月/远月、均值/标准差等未消歧），`_mid_suffix` 消歧函数未覆盖所有情况。

### 3.4 缺陷类型 D：chart_registry 异常条目

**严重度**：🟡 中  

`chart_registry.json` 自身标注 49 条 🔴 异常 + 127 条 🟢 无关键词命中：

| 异常类型 | 数量 | 说明 |
|---|---|---|
| 🔴 主图指标归属错误 | 49 | 如"精炼产量"放在价格页 |
| 🟢 无关键词命中 | 127 | 规则引擎未匹配到任何关键词 |

按品种分布：NI 31 / SI 31 / SN 31 / ZN 24 / AL 17 / PB 15 / CU 14 / LI 13。

### 3.5 缺陷类型 E：孤岛页面（无入站链接）

**严重度**：🟡 中  

52 个含图表页面无任何其他页面的 `href` 指向（不含 index/overview/特殊页）：

| 品种 | 孤岛页数 | 典型页面 |
|---|---|---|
| 锂 LI | 17 | li_2/li_3/li_4/li_5_*/li_6_*/li_7_* |
| 镍 NI | 6 | ni_0/ni_2/ni_3/ni_4/ni_5/ni_7 |
| 硅 SI | 6 | si_2/si_3/si_4/si_5/si_6/si_7 |
| 锡 SN | 6 | sn_2/sn_3/sn_4/sn_5/sn_6/sn_7 |
| 锌 ZN | 7 | zn_0/zn_1/zn_3/zn_4/zn_5/zn_6/zn_7 |
| 铝 AL | 4 | al_0/al_3/al_4/al_6 |
| 铜 CU | 5 | cu_0/cu_2/cu_4/cu_4_4/cu_4_5 |
| 铅 PB | 1 | pb_stock_v2（已归档） |

**根因**：五金属的"板块聚合页"（如 `zn_3.html`）是 `build_5m_batch.py` 批量生成产物，但 `index.html` 的 `PAGE_MAP` 只映射到子节点页（如 `zn_3_1_1.html`），未映射到聚合页。用户只能通过直接输入 URL 访问。

---

## 四、GitHub Pages 部署版本核验

### 4.1 部署机制

- 仓库 `algo23-yunqingtian/framework-tree` 无 `.github/workflows`，Pages 部署由 **push to main** 自动触发。
- `indicator-correction-win` 分支的 commit 尚未 merge 到 main，**但 Pages 已部署该分支内容**。

### 4.2 部署版本比对

| 比对项 | 结果 |
|---|---|
| Pages `index.html` md5 vs 分支 HEAD | **不同**（main 的 index.html 与分支有 64 行差异） |
| Pages `al_2_1.html` md5 vs 分支 HEAD | **完全一致**（`b820aea0...`） |
| Pages `al_2_1.html` md5 vs main HEAD | **完全一致** |

**结论**：GitHub Pages 当前部署的是 **main 分支 HEAD（`217cb86`）**，而非 `indicator-correction-win` 分支 HEAD（`38bf48c`）。两个分支的 HTML 产物**几乎完全一致**（al_2_1.html md5 相同），但 index.html 存在 64 行差异（main 比 branch 多 1850 字节，可能含 Dsharnes-B 角色定义审计报告的更新）。

**判定**：Pages 部署版本与 main 同步。`indicator-correction-win` 分支的指标修正工作（P1 v2/v3 的 CU/AL/NI/SN 修正）**已 merge 到 main**，因此 Pages 已包含这些修正。**不存在 Pages 落后于分支的情况**。

---

## 五、缺陷汇总表

| # | 缺陷 | 严重度 | 影响范围 | 根因 |
|---|---|---|---|---|
| A1 | chart_registry 未覆盖 50 页/798 图 | 🔴 高 | ZN/NI/SI/SN/LI 五金属 | `build_chart_registry.py` 正则不识别聚合页/品种首页 |
| B1 | 327 条指标串台 | 🔴 高 | 全品种 | 板块聚合页跨板块收录 + node 页指标归属错误 |
| C1 | 62 条自身重复 "vs" 标题 | 🟡 中 | AL/CU/LI/NI | `chart_dual` 消歧函数不完整 |
| D1 | chart_registry 49 条 🔴 异常 | 🟡 中 | 全品种 | 规则引擎关键词覆盖不全 |
| E1 | 52 个孤岛页面无入站链接 | 🟡 中 | ZN/NI/SI/SN/LI | PAGE_MAP 未映射聚合页 |
| F1 | index.html PAGE_MAP 仅 94 条 | 🟡 中 | 全品种 | 总览页→子节点页有链接，聚合页无 |

---

## 六、建议修复优先级

1. **P0**：修复 `build_chart_registry.py` 的 `parse_node_code`，支持聚合页（`zn_3.html`）和品种首页（`zn_0.html`）格式，使注册表覆盖率达 100%。
2. **P1**：审查 327 条串台，区分"设计意图"（聚合页跨板块收录）和"真实缺陷"（node 页指标错放），修正后者。
3. **P2**：修复 `chart_dual` 的 `_mid_suffix` 消歧函数，覆盖近月/远月/均值/标准差/分位等全部情况，消除自身重复 "vs"。
4. **P3**：在 `index.html` 的 `PAGE_MAP` 中补充聚合页入口，或在总览页增加聚合页链接。

---

> **审计声明**：本报告仅做只读审计，未修改任何源码。所有数据从 `git show origin/indicator-correction-win:{path}` 提取，不依赖工作区文件状态。
