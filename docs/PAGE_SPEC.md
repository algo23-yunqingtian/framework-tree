# 页面统一规范 v1（2026-08-29 生效）

> **唯一真源**。任何新增/重建页面必须严格遵守。改动此规范需先 `git pull`，走 PR，主脑 review 后合并。
> 新 agent 每次开工前先读本文件 + `STATUS.md`，再动手。

---

## 0. 适用范围

所有品种（cu/al/pb/zn/ni/sn/li/si）× 所有板块（2 价格信号 / 3 供给 / 4 需求 / 5 成本利润 / 6 进出口 / 7 供需平衡 / 8 库存）的子页 + 总览页。

---

## 1. 页头（Header）三段式

固定结构，顺序不可调：

```
[▮▮ 有色金属研究框架 METALS FRAMEWORK v2]  [面包屑]  [数据源快照]
```

**面包屑格式**（硬规定）：
```
{品种}({代码}) · {板块号} {板块名} · {子节点号} {子节点名} · v{页版本号} {图数} 图
```

反例（❌ 违规）：
- `铅(PB) · 6.1 原料进口 · v3 3 图(带图备注)` ← 括号尾巴禁止
- `铅(PB) · 6 进出口 · 6.1 原料进口 · v3 3 图(带图备注+双向)` ← 双括号尾巴禁止

正例（✅ 合规）：
- `铅(PB) · 2 价格信号 · 2.1 盘面结构 · v1 3 图`
- `铅(PB) · 6 进出口 · 6.1 原料进口 · v3 3 图`

**版本号语义**：页本身的重建次数（v1/v2/v3），不是 indicators_v1.json 版本号。

---

## 2. 导航回链（新，v1 规范必备）

页头下方第一行必须放两个回链按钮：

```html
<div class="nav-back">
  <a href="{总览页.html}">← 回板块{N}总览</a>
  <a href="index.html">← 回主站</a>
</div>
```

- 总览页文件名：`{品种前缀}_{板块号}_overview.html`，如 `pb_2_overview.html` / `pb_6_overview.html`
- 主站文件名：`index.html`（永远）
- 样式在 `chart_kits.py` 的 CSS 常量里已定义，不要重复写

**总览页**自己不需要「回板块总览」，只需要「← 回主站」。

---

## 3. 图表卡片结构

每张图必须包含：

```html
<div class="chart">
  <div class="chart-title">标题</div>
  <div class="chart-sub">数据源 · 频率 · 单位 · 指标ID N 点 · 起止日期</div>
  <div id="echart_{NN}_c{M}" style="width:100%;height:320px"></div>
  [可选] <button onclick="window.__tgl('...',this)">☀ 季节</button>
  <div class="chart-note">📌 什么时候看：…<br>怎么看：…</div>
</div>
```

**chart-note 硬规定**（客户读图必备）：
- 第一行 `📌 什么时候看：` 说明买家/交易员何时打开这张图
- 第二行 `怎么看：` 说明图内指标的关系和判断口径
- 多指标图必须写「指标关系」；单指标图可省略

---

## 4. 页面底部 note 块

在 `.panel` 内最下方，`<div class="note">` 结构：

- `{子节点号} 定义：` 说明这个子节点在看什么
- `指标组：` 列出所有 zhiji_id + 单位 + 频率
- `数据源：` 说明数据来源
- 可选：`v{N} 关键修正：` / `数据源缺口：` / `待外部源：` 说明限制

---

## 5. Footer

```
有色金属产业指标树 · {品种}({代码}) {子节点号} {子节点名} · v{页版本号}（{图数} 图 · {数据特征} · {口径}）· indicators_v1.json v{版本号}
```

- `indicators_v1.json v{版本号}` 是**当前页构建时的快照版本**，各页可以不同（快照时点差异是合理的）
- 不要写「合计」「汇总」等禁用词

---

## 6. 反拷贝保护

`chart_kits.py` 的 `ANTI` 常量已包含：
- 禁止右键 `document.oncontextmenu`
- 禁止 Ctrl+C/S/P/U
- 禁止选中 `document.onselectstart`

**不要覆盖或跳过** `ANTI`。

---

## 7. 季节图规则

- 日频数据 → `__seasonalizeByDay`（365 类目，MM-DD 对齐）
- 月频数据 → `__seasonalizeByYear`（12 类目）
- 默认视图由 `chart_line_t(..., default_seasonal=True)` 决定
- 按钮文字：`☀ 季节` = 当前是时序；`⏱ 时序` = 当前是季节

---

## 8. 数据内嵌（零服务器依赖）

- 页面数据**必须**在 build 脚本读库后硬编码进 HTML
- **不许**在页面里出现 `fetch(` / `XMLHttpRequest` / `axios` / `127.0.0.1:`
- 验证：`grep -c 'fetch(' xxx.html` 必须为 0

---

## 9. 目录 + 命名规范

| 类型 | 文件名 | 例 |
|---|---|---|
| 子页 | `{品种前缀}_{板块子节点号}_{slug}.html` | `pb_21_price_structure.html` |
| 总览页 | `{品种前缀}_{板块号}_overview.html` | `pb_2_overview.html` |
| build 脚本 | `scripts/build_{对应HTML文件名前缀}.py` | `scripts/build_pb_21.py` |

品种前缀：cu/al/**pb**/zn/ni/sn/li/si（小写，硅用 si 不用 sg，锂用 li）

---

## 10. 三道门禁（提交前必跑）

```bash
python3 scripts/check_html.py     # 静态校验（面包屑/回链/note/footer）
node scripts/verify_render.js     # jsdom + ECharts mock 渲染校验
python3 scripts/reclaim.py        # 格式契约 + 产物完整性
```

三道全 PASS 才算完成。FAIL 修复后重跑，不许带病提交。

---

## 11. 提交前必更

- `STATUS.md` 近期变更记录表加一行
- commit 前缀：`[A]` 架构 / `[B]` 数据 / `[Txx]` 任务 / `[DOC]` 文档
- 不许直接 push main，走分支 + PR

---

## 修订记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-08-29 | v1 | 首版。统一面包屑格式、加导航回链、明确 chart-note 硬规、明确数据内嵌零服务器依赖。 |
