# P14 C4 Fix Deployment Directory

> **Generated**: 2026-10-18 16:32:02 
> **Reason**: HERMEShf 侧 P14 C4 修复交付物原深埋在 `hermes/hermes_final_seal_archive/` (深度 6)，DSHB 浅层检索无法命中；本目录将交付物平铺至 `phase03/p1/hermes_p14_c4_fix/` (深度 4) 供 DSHB 递归检索
> **性质**: 冗余副本，原路径哈希不变（NO_OVERWRITE 合规）

## 交付物清单

| # | 文件 | MD5 | 源路径 | 状态 |
|:-:|------|-----|--------|:---:|
| 1 | `c4_index_fix_report.md` | `76a5bdba91ce17d71b9c4b61a3c8a6fd` | (见源) | ✅ |
| 2 | `wiki_admission_gate.md` | `3286e1469f7ce6b23bedfef061fbc63f` | (见源) | ✅ |
| 3 | `hermes_asset_index.md` | `80ec470a425f67243e30ca1dd85316a2` | (见源) | ✅ |
| 4 | `p14_artifact_recheck_report.md` | `f9433583bb61825b63215b7b06a3f6e6` | (见源) | ✅ |
| 5 | `pickup.flag.mirror` | `5ed8959c5893458d9980d12d5c0b869f` | (见源) | ✅ |
| 6 | `pickup_flag_generation_report.md` | `2464daa3ebc7a64a0cc84ef5f8d4aae4` | (见源) | ✅ |

## 关联提交

- `0151ab7` — pickup.flag 公共路径生成 (C1=SATISFIED)
- `25faa6b` — C4 P14 索引修复 (方案 A 移出挂载)

## 部署策略

- **复制非移动**：所有源文件保留在原路径，MD5 不变
- **不触碰 asset_index.lst**：索引 22 条不变，封签链 v2/v3/v4/v5 不变
- **不触碰 frozen 包**：本次仅追加公共路径冗余副本

