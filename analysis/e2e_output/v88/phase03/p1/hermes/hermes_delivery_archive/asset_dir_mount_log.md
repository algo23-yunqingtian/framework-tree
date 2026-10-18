# V88 Phase03 P11 资产目录挂载日志 (asset_dir_mount_log.md)

> **TASK_ID**: V88_PHASE03_P11_HERMESHF_DISPATCH_CONSUME
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 | **生成**: 2026-10-20T00:00 +0800

## 一、挂载动作

| 挂载点 | 源 | 类型 | 文件数 | 目录数 |
|--------|-----|------|:---:|:---:|
| `hermes/web_asset/` | (原目录, 已在位) | 只读锁定 | 10 | 0 |
| `hermes/github_pages/` | hermes_web_dashboard_archive/github_pages/ | 复制挂载 | 13 | 1 |

**挂载目的**: 补齐 C3 条件 —— 使 DSHE 可按 `asset_index.lst` 的相对路径直接探测到 22 项资产，
无需知道 github_pages 在 `hermes_web_dashboard_archive/` 子目录下的原始位置。

## 二、只读锁定明细

- 文件权限: `0444` (r--r--r--)
- 目录权限: `0555` (r-xr-xr-x)
- 锁定范围: web_asset/ + github_pages/ 全递归
- 保护目标: 22 项可视化资产禁止写入/修改/删除

| 目录 | 相对路径 | 锁定文件数 | 锁定目录数 |
|------|----------|:---:|:---:|
| web_asset | `web_asset` | 10 | 0 |
| github_pages | `github_pages` | 13 | 1 |

## 三、22 项资产探测可达性复核

| # | 资产路径 (asset_index.lst) | MD5 一致 | 大小一致 | 只读 |
|:-:|---------------------------|:---:|:---:|:---:|
| 1 | `github_pages/README.md` | ✅ | ✅ | ✅ |
| 2 | `github_pages/assets/01_kpi_cards.html` | ✅ | ✅ | ✅ |
| 3 | `github_pages/assets/01_kpi_cards.png` | ✅ | ✅ | ✅ |
| 4 | `github_pages/assets/02_factor_heatmap.html` | ✅ | ✅ | ✅ |
| 5 | `github_pages/assets/02_factor_heatmap.png` | ✅ | ✅ | ✅ |
| 6 | `github_pages/assets/03_scenario_bars.html` | ✅ | ✅ | ✅ |
| 7 | `github_pages/assets/03_scenario_bars.png` | ✅ | ✅ | ✅ |
| 8 | `github_pages/assets/04_risk_progress.html` | ✅ | ✅ | ✅ |
| 9 | `github_pages/assets/04_risk_progress.png` | ✅ | ✅ | ✅ |
| 10 | `github_pages/assets/05_caliber_matrix.html` | ✅ | ✅ | ✅ |
| 11 | `github_pages/assets/05_caliber_matrix.png` | ✅ | ✅ | ✅ |
| 12 | `github_pages/index.html` | ✅ | ✅ | ✅ |
| 13 | `web_asset/01_kpi_cards.html` | ✅ | ✅ | ✅ |
| 14 | `web_asset/01_kpi_cards.png` | ✅ | ✅ | ✅ |
| 15 | `web_asset/02_factor_heatmap.html` | ✅ | ✅ | ✅ |
| 16 | `web_asset/02_factor_heatmap.png` | ✅ | ✅ | ✅ |
| 17 | `web_asset/03_scenario_bars.html` | ✅ | ✅ | ✅ |
| 18 | `web_asset/03_scenario_bars.png` | ✅ | ✅ | ✅ |
| 19 | `web_asset/04_risk_progress.html` | ✅ | ✅ | ✅ |
| 20 | `web_asset/04_risk_progress.png` | ✅ | ✅ | ✅ |
| 21 | `web_asset/05_caliber_matrix.html` | ✅ | ✅ | ✅ |
| 22 | `web_asset/05_caliber_matrix.png` | ✅ | ✅ | ✅ |

**结论: 22/22 项资产 MD5+大小+只读全部通过，DSHE 可探测到 P18 交付目录 (C3 条件就绪)**

## 四、DSHE 探测入口

```
analysis/e2e_output/v88/phase03/p1/hermes/
├── hermes_dispatch/p18_delivery_ready.flag    ← 就绪标记 (SEAL_V3_SHA256)
├── hermes_dispatch/pickup.flag                ← HERMEShf 拾取签收
├── hermes_delivery_archive/
│   ├── asset_index.lst                        ← 22 项索引
│   └── asset_seal_v3.txt                      ← P18 双哈希终封
├── web_asset/                                 ← 10 项 (只读)
└── github_pages/                              ← 12 项 (只读, 本任务挂载)
```

---

*V88 Phase03 P11 T2 | HERMEShf | 2026-10-20T00:00 +0800*
