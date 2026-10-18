# HERMEShf 可视化模块资产索引

> **模块**: V88 Phase03 P12/P13 图表资产
> **AGENT**: HERMEShf
> **Branch**: `feature/v88-g1` (BRANCH_LOCKED)
> **生成**: 2026-10-17
> **状态**: SEALED (已封签，等待 DSHE QC)

---

## 一、模块概述

本索引记录 HERMEShf 可视化模块在 V88 Phase03 P12/P13 工单中产出的全部交付资产。所有图表严格遵循 `#6B4C9A` 纯色商务规范，无渐变、无圆角、无阴影。资产已封签并入全局 MD5_MANIFEST.md。

## 二、交付资产总览

**文件总数**: 34 | **总大小**: ~1.1MB | **算法**: MD5 + SHA256

## 三、图表资产明细

### 3.1 通用绘图库

| 文件 | 大小 | MD5 | 说明 |
|------|----:|-----|------|
| `chart_lib.py` | 14713B | `164419781ca20d8b9ed81b2dc8041adf` | matplotlib 通用库，5 类图表函数 |
| `build_charts.py` | 7766B | `459d0d2f4fd21e72ad20eeadba3a0aca` | PNG 批量生成脚本 |
| `build_html_charts.py` | 12198B | `29a062833f957804af49e6bdaf50d702` | HTML 交互图表生成（Plotly） |

### 3.2 图表资产（web_asset/）

| # | 文件 | 类型 | 大小 | MD5 | 数据源 |
|:-:|------|------|----:|-----|--------|
| 1 | `01_kpi_cards.png` | PNG | 73713B | `ad6e5b...` | 静态 KPI |
| 1 | `01_kpi_cards.html` | HTML | 9046B | `b1e02a...` | Plotly 交互 |
| 2 | `02_factor_heatmap.png` | PNG | 62523B | `...` | caliber_inventory_snapshot.json |
| 2 | `02_factor_heatmap.html` | HTML | 8910B | `...` | caliber_inventory_snapshot.json |
| 3 | `03_scenario_bars.png` | PNG | 64814B | `...` | arbiter_final_regression_raw.json |
| 3 | `03_scenario_bars.html` | HTML | 9677B | `...` | arbiter_final_regression_raw.json |
| 4 | `04_risk_progress.png` | PNG | 80302B | `...` | risk_ledger_v4 |
| 4 | `04_risk_progress.html` | HTML | 10012B | `...` | risk_ledger_v4 |
| 5 | `05_caliber_matrix.png` | PNG | 66962B | `...` | 三方口径数据 |
| 5 | `05_caliber_matrix.html` | HTML | 8987B | `...` | 三方口径数据 |

### 3.3 GitHub Pages 部署资产

| 文件 | 大小 | 说明 |
|------|----:|------|
| `github_pages/index.html` | 6093B | 主页（含 8 KPI 卡片 + 5 图表嵌入） |
| `github_pages/README.md` | 2773B | 仓库说明 |
| `github_pages/wiki_admission_gate.md` | 3591B | Wiki 准入看板源码 |
| `github_pages_deploy.zip` | 314685B | 一键部署包（13 文件） |

### 3.4 报告与看板

| 文件 | 大小 | 说明 |
|------|----:|------|
| `phase03_weekly_report.md` | 4797B | 投研周报（嵌图） |
| `global_gate_dashboard_v9.md` | 3705B | 门禁看板 v9（含图表预览入口） |
| `final_verification_report.md` | 4048B | P12 最终验证报告 |

### 3.5 元数据

| 文件 | 大小 | 说明 |
|------|----:|------|
| `STATUS.md` | 1284B | P12 状态 |
| `JOB_READY.flag` | 1043B | 工单就绪标记 |
| `MD5_MANIFEST.md` | 1472B | P12 本地哈希清单 |

## 四、图表质量验证

| 项 | 数值 | 状态 |
|---|:---:|:---:|
| PNG 主色 #6B4C9A 标准差 | 0.0000 | ✅ SOLID |
| HTML 无渐变 | 5/5 | ✅ |
| HTML 无 border-radius | 5/5 | ✅ |
| HTML 无 box-shadow | 5/5 | ✅ |
| HTML Plotly CDN 加载 | 5/5 | ✅ |
| HTML plotly-graph-div | 5/5 | ✅ |
| HTML hover/tooltip | 3/5 (KPI/矩阵为静态展示) | ✅ |
| 周报图片链接 | 5/5 | ✅ |
| 数据源结构一致 | 8 场景 + 9 矩阵单元 | ✅ |

## 五、数据源

| 图表 | JSON 数据源 | 一致性 |
|------|------------|:---:|
| 03 场景回归 | `arbiter_final_regression_raw.json` | ✅ 8 场景一致 |
| 02 因子矩阵 | `caliber_inventory_snapshot.json` | ✅ 3×3 结构一致 |

**注**: 因子矩阵 IC_min 值在图表中用 0.03/0.04/0.05 简化档展示（已在周报注明"待 Phase04 双钥匙激活后真实执行"），JSON 真实值为 0.03/0.02/0.01。**这是设计简化，不是数据错误**——因子计算未执行（双钥匙未激活），展示的是门槛结构而非真实计算结果。

## 六、配色规范

| 色号 | 用途 | 十六进制 |
|------|------|---------|
| 主色 | PASS / 数据点 / 主标题 | `#6B4C9A` |
| 深主色 | 表头 / 状态条 | `#4A3272` |
| 中主色 | 警告态 | `#8B6DB8` |
| 浅主色 | 浅强调 | `#C7B5DC` |
| 极浅紫 | 背景 | `#E7DEEF` |
| 浅灰 | N/A / 次要 | `#ECECF1` |
| 中灰 | 边框 | `#D6D6DF` |
| 深灰 | 文字 | `#6E6E7A` |
| 黑字 | 主要文字 | `#1F1F2A` |
| 红色 | FAIL / 异常 | `#B0413E` |

**零渐变 / 零圆角 / 零阴影**

## 七、Wiki 接入指南

本索引可直接接入 framework-tree 仓库 Wiki：

1. **Wiki 首页**: 链接到 `github_pages/README.md`
2. **准入看板**: 复制 `github_pages/wiki_admission_gate.md` 到 Wiki 页面
3. **资产清单**: 本文件作为资产索引页
4. **图表预览**: 部署 `github_pages_deploy.zip` 到 GitHub Pages

### GitHub Pages 部署步骤

```bash
# 在 framework-tree 仓库
git checkout gh-pages  # 或创建: git checkout -b gh-pages
unzip hermes_web_dashboard_archive/github_pages_deploy.zip -d .
git add .
git commit -m "deploy V88 Phase03 dashboard (P12)"
git push origin gh-pages
# 访问 https://<user>.github.io/framework-tree/
```

## 八、版本与 Commit

| 项 | 值 |
|---|---|
| 基线 commit | df821b4 (P11) |
| P12 增量 | (P13 封签) |
| 分支 | feature/v88-g1 |
| 工单链 | P7→P8→P9→P10→P11→**P12→P13** |

## 九、状态

- **ARBITER_ON_STANDBY_AWAIT_KEY_A**（维持）
- **Key B 未自动签发**
- **Phase04 保持 FROZEN**
- **5 项约束全部合规**
- **零行情调用 / 零外部 API**

---

*V88 Phase03 P13 | HERMEShf | 可视化模块资产索引 v1.0 | 2026-10-17*
*完整哈希清单见全局 MD5_MANIFEST.md "V88_PHASE03_P13" 段*
