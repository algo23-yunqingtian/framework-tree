# framework-tree · V88 Phase03 准入门禁看板

> **AGENT**: HERMEShf | **Branch**: `feature/v88-g1` (BRANCH_LOCKED)
> **生成**: 2026-10-17 | **数据源**: 审计产物（无行情调用）

## 状态总览

| 项 | 状态 |
|---|---|
| 5 项分支约束 | ✅ 5/5 合规 |
| 风险台账 | ✅ 3/3 全部闭环 |
| 仲裁器 8 场景回归 | ✅ 5 ALL PASS + 3 SKIP（Key A 缺席合法跳过） |
| 假阳性 / 假阴性 | ✅ 0 / 0 |
| 3×3 因子质量门槛 | ✅ 9 单元 LOCKED（待双钥匙激活后执行） |
| 口径快照双源校验 | ✅ 10/10 |
| KEY_A (WIND_DATA_LINK_ONLINE.flag) | ❌ ABSENT（外部信号，等待中） |
| KEY_B (HERMES_TRIGGER_AUTHORIZED.flag) | ❌ ABSENT（不自动签发） |
| Phase04 点火 | 🧊 FROZEN，维持待命 |

**当前仲裁器状态**: `ARBITER_ON_STANDBY_AWAIT_KEY_A`

## 图表目录

完整图表位于 [`assets/`](assets/)（PNG 静态版 + HTML 交互版双份）：

| # | 图表 | PNG | HTML |
|:-:|------|-----|------|
| 1 | 核心指标 KPI 卡片 | [`01_kpi_cards.png`](assets/01_kpi_cards.png) | [`01_kpi_cards.html`](assets/01_kpi_cards.html) |
| 2 | 3×3 因子质量门槛矩阵 | [`02_factor_heatmap.png`](assets/02_factor_heatmap.png) | [`02_factor_heatmap.html`](assets/02_factor_heatmap.html) |
| 3 | 仲裁器 8 场景回归 | [`03_scenario_bars.png`](assets/03_scenario_bars.png) | [`03_scenario_bars.html`](assets/03_scenario_bars.html) |
| 4 | 风险台账闭环进度 | [`04_risk_progress.png`](assets/04_risk_progress.png) | [`04_risk_progress.html`](assets/04_risk_progress.html) |
| 5 | 三方口径一致性矩阵 | [`05_caliber_matrix.png`](assets/05_caliber_matrix.png) | [`05_caliber_matrix.html`](assets/05_caliber_matrix.html) |

## 设计规范

- 主色 `#6B4C9A`（品牌深紫，本工单指定"深蓝商务主色"）
- 辅助浅灰 `#ECECF1` / `#D6D6DF` / `#9A9AA8`
- 纯白底 `#FFFFFF`，无渐变、无圆角模块、无阴影
- 字型：Noto Sans CJK SC / WenQuanYi Zen Hei 回退链

## 快速开始

```bash
# 本地预览
python3 -m http.server 8786   # 在 github_pages/ 目录下

# 重新生成全部图表
python3.12 build_charts.py
python3.12 build_html_charts.py
```

## 交付物清单

- `chart_lib.py` — 通用绘图库（matplotlib，纯色商务规范）
- `build_charts.py` — PNG 批量生成脚本（读取审计产物 JSON）
- `build_html_charts.py` — HTML 交互图表生成脚本（Plotly）
- `web_asset/` — 全部 10 个图表文件
- `github_pages/` — GitHub Pages 静态站点（本目录）
- `github_pages_deploy.zip` — 一键上传部署包
- `phase03_weekly_report.md` — 投研周报（嵌图）
- `global_gate_dashboard_v9.md` — 门禁看板 v9

---

*V88 Phase03 P12 | HERMEShf | 状态: ARBITER_ON_STANDBY_AWAIT_KEY_A*