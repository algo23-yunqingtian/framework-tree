# V85/V86 双版本对比面板设计

> 工单: `HERMES_V86_PORTAL_INTEGRATE_AND_V85_FROZEN_DEMO_LOCK` · T2.3.2
> 生成时间: 2026-10-02 09:42
> 分支: `feature/v85-chart-template` @ `5e874a7`
> 数据源: V85 只读 API（`f313570`）/ DSHB `comparison_report.json`（V86 P0 原型回归实测）

---

## 1. 面板布局

```
┌────────────────────────────────────────────────────────────────────────┐
│ 📈 V85 / V86 规则指标对比                     [⟳ 刷新] [⤓ 导出 JSON]    │
├────────────────────────────────────────────────────────────────────────┤
│  基线: 🔒 V85.0 FROZEN (f313570)   对比: 🧪 V86.0-alpha (P0 原型 4规则) │
│  场景: [A ▾]   用例集: [v86-rule-test-suite-v1 ▾]                      │
├────────────────────────────────────────────────────────────────────────┤
│  ┌─ 指标卡片（6 个） ───────────────────────────────────────────────┐ │
│  │ P0拦截率      TP          FP          回归数      改进数    用例数 │ │
│  │ 87.5%  ─7.5pt│ 44   −4   │ 0    0   │ 4        │ 0       │ 62   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌─ 双柱状图 ──────────┐  ┌─ 瀑布图（差异归因）────────────────────┐ │
│  │ ▓ V85 87.5%         │  │ +0 改进  │ −4 回归 │ V85 87.5% → V86 75%│ │
│  │ ▓ V86 75.0%         │  │          │          │                   │ │
│  └─────────────────────┘  └────────────────────────────────────────┘ │
│  ┌─ 差异明细表（可筛选/分页）────────────────────────────────────────┐ │
│  │ change_type | risk_id   | V85 规则   | V86 状态    | Δ TP | Δ FP │ │
│  │ REGRESSION  | RISK-022  | BL-019     | PASSED      │ −1   | 0    │ │
│  │ REGRESSION  | RISK-001  | BL-005     | DATA_MISSING│ −1   | 0    │ │
│  │ REGRESSION  | RISK-003  | BL-003     | DATA_MISSING│ −1   | 0    │ │
│  │ REGRESSION  | RISK-006  | BL-002     | DATA_MISSING│ −1   | 0    │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 实测数据（DSHB V86 P0 原型回归）

来源: `analysis/e2e_output/v86/dshb_rule_predev/comparison_report.json`（commit `128275a`）

### 2.1 汇总

| 指标 | V85 基线 | V86 原型 | Δ |
|------|---------|---------|---|
| 用例总数 | 62 | 62 | 0 |
| 拦截数 (blocked) | 44 | 40 | **−4** |
| TP | 44 | 40 | **−4** |
| FP | 0 | 0 | 0 |
| P0 拦截率 | **87.5%** | **75.0%** | **−12.5 pt** |
| 改进 (improvements) | — | 0 | 0 |
| 回归 (regressions) | — | **4** | 4 |
| 未变 (unchanged) | — | 58 | 0 |

### 2.2 回归明细（4 条）

| risk_id | level | V85 状态 | V85 规则 | V86 状态 | V86 规则 | Δ TP |
|---------|-------|---------|---------|---------|---------|------|
| RISK-022 | P0 | BLOCKED | BL-019 | PASSED | — | −1 |
| RISK-001 | P0 | BLOCKED | BL-005（场内库存↔非仓单库存） | DATA_MISSING | — | −1 |
| RISK-003 | P0 | BLOCKED | BL-003（销量↔产量） | DATA_MISSING | — | −1 |
| RISK-006 | P0 | BLOCKED | BL-002（产量↔销量） | DATA_MISSING | — | −1 |

### 2.3 ⚠️ 口径说明（必须随面板常驻展示）

**这 4 条「回归」不是真实能力退化**，属**规则集口径差异**：

- V86 P0 原型当前仅实现 **4 条规则**（BL-009a / BL-026 / BL-012 方案 B / PDF_Fix）
- V85 基线使用 **完整 31 条规则**黑名单（含 BL-002/BL-003/BL-005/BL-019）
- RISK-001/003/006 的 V86 状态为 `DATA_MISSING`（上游 matched_name 缺失，非规则未覆盖）
- RISK-022 在 P0 原型中无对应规则

**面板结论标签**：`⚠️ 原型不完整 — 4 条回归源于规则集差异（4 vs 31 规则），非真实退化`

> DSHB 全量回归报告显示 BL-009a + BL-026 在完整黑名单基础上 P0 拦截率 88.2% → **100%**，0 FP，0 回归。门户对比面板应支持两种对比口径切换：
> - 「P0 原型 vs V85」→ 上述 −12.5 pt（用于验证原型边界）
> - 「完整黑名单+P0 规则 vs V85」→ +11.8 pt（用于上线准入判断）

### 2.4 对比口径切换

```
对比口径:  (●) P0 原型(4规则)  ( ) 完整黑名单+P0(35规则)
```

| 口径 | 数据源 | 状态 |
|------|--------|------|
| P0 原型 4 规则 | `comparison_report.json` | ✅ 已有实测 |
| 完整黑名单+P0 | 需 V86 任务接口提交 `dshb_rule_eval`（`blacklist_version=v86-full`） | ⏳ 待后端实现 |

---

## 3. 指标卡片规格

| 卡片 | 主数值 | 副数值 | 颜色规则 |
|---|---|---|---|
| P0 拦截率 | `{v86_rate}%` | `Δ {delta:+.1f} pt` vs V85 `{v85_rate}%` | V86≥V85 绿，否则红 |
| TP | `{v86_tp}` | `Δ {delta_tp:+d}` | Δ≥0 绿，否则红 |
| FP | `{v86_fp}` | `目标 =0` | =0 绿，>0 红 |
| 回归数 | `{regressions}` | `需人工复核` | =0 绿，>0 橙 |
| 改进数 | `{improvements}` | `新增拦截` | >0 绿，=0 灰 |
| 用例数 | `{total}` | `基线/对比一致` | 一致灰，不一致橙 |

---

## 4. 可视化实现

### 4.1 双柱状图（P0 拦截率）

- X 轴：`V85 FROZEN` / `V86 DEV`
- Y 轴：0-100%，标注 95% 目标线（虚线）
- 柱体标注百分比；两柱之间画箭头标注 Δ
- 数据点：`[87.5, 75.0]`

### 4.2 瀑布图（差异归因）

```
V85 87.5% ─[+0 改进]─[−12.5pt 回归]─> V86 75.0%
```

- 起点柱：V85 基线（蓝）
- 增量段：改进（绿，↑）/ 回归（红，↓）
- 终点柱：V86（橙）
- 点击回归段 → 下方明细表自动过滤 `change_type=REGRESSION`

### 4.3 差异明细表

| 列 | 说明 |
|---|---|
| `change_type` | `IMPROVEMENT` / `REGRESSION` / `UNCHANGED` |
| `risk_id` | 风险编号 |
| `risk_level` | P0 / P1 |
| `v85_status` / `v85_rule` | V85 侧结果与命中规则 |
| `v86_status` / `v86_rule` | V86 侧结果与命中规则 |
| `tp_change` / `fp_change` | 增量 |

排序：`REGRESSION` → `IMPROVEMENT` → `UNCHANGED`；分页 50/页；支持按 `change_type` / `risk_level` / `rule` 筛选。

---

## 5. 数据接入

### 5.1 V85 侧（实时 API）

```python
q = client.scenario_replay(filters={"scenario": "A"}, limit=10000)
v85 = block_stats(q["rows"])   # {total, blocked, tp, fp, p0_rate}
```

### 5.2 V86 侧（两条路径）

**路径 A — 离线样本（当前可用）**：

```python
cmp = json.load(open("analysis/e2e_output/v86/dshb_rule_predev/comparison_report.json"))
v86 = {
    "total": cmp["summary"]["v86_total_cases"],
    "blocked": cmp["summary"]["v86_blocked"],
    "tp": cmp["summary"]["v86_tp"],
    "fp": cmp["summary"]["v86_fp"],
    "p0_rate": cmp["summary"]["v86_p0_interception_rate"],
}
diff_rows = cmp["changed_cases"]
```

**路径 B — 在线任务（待后端实现）**：

```python
task = task_client.submit(
    task_type="dshb_rule_eval", version_tag="v86.0-alpha", priority=5,
    payload={
        "blacklist_version": "v86-full",
        "case_set": "v86-rule-test-suite-v1",
        "scenario": "A",
        "compare_baseline": {"kind": "scenario_replay", "version": "f313570"},
    })
# 轮询 → get_result → 结构与 comparison_report.json 对齐
```

### 5.3 面板状态指示

| 路径 | 面板顶部标签 |
|---|---|
| A（离线样本） | `📄 离线样本 @ commit 128275a（2026-10-01 22:11）` |
| B（在线任务） | `🚀 实时任务 {task_id}（{finished_at}）` |
| 后端未就绪 | `⏳ V86 任务 API 未上线 — 仅显示离线样本` |
