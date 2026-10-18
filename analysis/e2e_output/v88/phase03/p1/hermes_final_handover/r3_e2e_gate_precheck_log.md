# R3 E2E Gate Pre-Check Log

> **Run**: 2026-10-18 16:35:09 
> **Job**: V88_PHASE03_P14_C4_INDEX_FIX_JOB + DEPLOY_FIX
> **Result**: 9/9 PASS

## 门禁矩阵

| Gate | 描述 | 结果 | 细节 |
|:---:|------|:---:|------|
| R3-G1 | asset_index.lst 计数=22 | ✅ | count=22 |
| R3-G2 | 挂载目录资产 22/22 可达且 MD5 全匹配 | ✅ | reachable=22/22, md5_ok=22/22 |
| R3-G3 | wiki_admission_gate.md 已移出 github_pages/ | ✅ | moved |
| R3-G4 | 归档副本存在 (backup/v88/phase03/P14_C4_INDEX_FIX/) | ✅ | OK |
| R3-G5 | 归档副本 MD5=3286e1469f7ce6b23bedfef061fbc63f | ✅ | OK |
| R3-G6 | 部署副本 MD5 全匹配源 | ✅ | OK (verified in T2) |
| R3-G7 | 公共路径 p1/pickup.flag 存在 | ✅ | OK |
| R3-G8 | 封签链 v3/v4/v5/index 未变 | ✅ | OK (verified in T2) |
| R3-G9 | 原私有 pickup.flag MD5 未变 | ✅ | OK |

## Index 22 项明细校验

- 计数: 22/22 ✅
- 挂载目录可达: 22/22 ✅
- MD5 一致: 22/22 ✅
- 缺失项: 无

## 关键决策

- R3-G2 初次误报 FAIL 因 parts[0] 误取 MD5 字段作路径；正确取 parts[1] 后 22/22 全部可达
- 索引基路径基准 = `hermes/` 目录，相对路径 = `github_pages/*` + `web_asset/*`

---
*R3 E2E 门禁预校验 | 2026-10-18 16:35:09 *
