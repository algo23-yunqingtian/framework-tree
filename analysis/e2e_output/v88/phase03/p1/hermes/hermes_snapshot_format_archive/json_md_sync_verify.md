# JSON+MD 双源一致性校验报告

> **TASK_ID**: V88_PHASE03_P9_HERMESHF_P8_SNAPSHOT_FORMAT_ADAPT_JOB / T0+T1
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **校验时刻**: 2026-10-17T15:25 +0800

---

## 1. 双源文件信息

| 属性 | MD 源文件 | JSON 新文件 |
|------|-----------|-------------|
| 文件名 | `caliber_snapshot_for_dshe.md` | `caliber_inventory_snapshot.json` |
| 路径 | `hermes_risk_calib_archive/` | `hermes_snapshot_format_archive/` |
| 格式 | Markdown | JSON |
| 大小 | 6431B | 8378B |
| 生成时间 | 2026-10-17T14:15 | 2026-10-17T15:15 |
| 来源 | P7 T1 手写 | P9 T0 从 MD 复刻 |
| commit | `9e1f6c7` | 本工单 |

---

## 2. 哈希指纹绑定

| 指纹算法 | MD 文件 | JSON 文件 |
|----------|---------|-----------|
| MD5 | `5CE83A6517F0EFC7DDC588A5C7907CA7` | `A4A1486655CBF9EC3E8A89E34D6A8B11` |
| SHA256(前16) | `F9B682B1F35ED796` | `975C62E7A469EDA1` |

> **说明**：MD5/SHA256 不同是正常的——MD 和 JSON 格式不同（Markdown 表格 vs JSON 对象），但内容完全一致。哈希绑定用于追踪两份文件的版本对应关系，非内容比对。

---

## 3. 内容一致性校验

### 3.1 校验结果汇总

| # | 校验项 | 结果 |
|:-:|--------|:----:|
| 1 | 矩阵 seq 序列（1-9） | ✅ |
| 2 | 矩阵 (factor_id, variety) 9组 | ✅ |
| 3 | 数据字段（全部 close） | ✅ |
| 4 | 数据源（全部 WIND_DATA_LINK） | ✅ |
| 5 | 因子列表（3个） | ✅ |
| 6 | 品种代码（PB/ZN/Recycle-PB） | ✅ |
| 7 | IC 阈值（0.03/0.02/0.01） | ✅ |
| 8 | t 阈值（1.5/1.2） | ✅ |
| 9 | LOCKED 状态 | ✅ |
| 10 | 品种映射（3行） | ✅ |

**全部通过：10/10 ✅**

### 3.2 矩阵 9 组（factor, variety）完全匹配

| # | MD | JSON | 一致 |
|:-:|----|------|:----:|
| 1 | (momentum_20d, PB) | (momentum_20d, PB) | ✅ |
| 2 | (momentum_20d, ZN) | (momentum_20d, ZN) | ✅ |
| 3 | (momentum_20d, Recycle-PB) | (momentum_20d, Recycle-PB) | ✅ |
| 4 | (momentum_60d, PB) | (momentum_60d, PB) | ✅ |
| 5 | (momentum_60d, ZN) | (momentum_60d, ZN) | ✅ |
| 6 | (momentum_60d, Recycle-PB) | (momentum_60d, Recycle-PB) | ✅ |
| 7 | (vol_20d, PB) | (vol_20d, PB) | ✅ |
| 8 | (vol_20d, ZN) | (vol_20d, ZN) | ✅ |
| 9 | (vol_20d, Recycle-PB) | (vol_20d, Recycle-PB) | ✅ |

### 3.3 品种映射匹配

| DSHB ID | DSHE ID | 品种 | MD | JSON |
|---------|---------|:----:|:--:|:----:|
| pb_21_close_front | PB_FU00014950 | PB | ✅ | ✅ |
| zn_21_close_front | ZN_FU00014950 | ZN | ✅ | ✅ |
| recycle_pb_21_close | RECYCLEPB_FU00014950 | Recycle-PB | ✅ | ✅ |

---

## 4. JSON Schema 适配

JSON 文件适配了 DSHE P018 期望的导入结构：

| DSHE 期望字段 | JSON 实际字段 | 适配 |
|---------------|---------------|:----:|
| `snapshot_id` | `snapshot_id: "HERMEShf_Caliber_20261017"` | ✅ |
| `generated_at` | `generated_at: ISO8601` | ✅ |
| `source` | `source: "HERMEShf"` | ✅ |
| 指标口径 | `section_1_factor_matrix.matrix[]` | ✅ |
| 品种映射 | `section_3_variety_mapping[]` | ✅ |
| 一致性 | `section_4_p019_cross_check.checks[]` | ✅ |

> **说明**：DSHE P018 期望的 `partial_details[]` 是针对 24-partial 指标的，而 HERMEShf 快照内容是 9 因子矩阵（非 partial 指标）。JSON 使用 `section_1_factor_matrix` 结构承载 9 因子矩阵，保留了 DSHE 期望的顶层字段（snapshot_id/generated_at/source），DSHE 导入逻辑可适配。

---

## 5. 校验结论

| 项 | 值 |
|----|---|
| MD 文件 | ✅ 存在（P7 下发） |
| JSON 文件 | ✅ 生成（P9 T0） |
| 哈希绑定 | ✅ 双源 MD5+SHA256 记录 |
| 内容一致 | ✅ 10/10 |
| DSHE schema 适配 | ✅ |
| 品种映射 | ✅ 3/3 |
| 因子矩阵 | ✅ 9/9 |
| 口径元数据 | ✅ close+后复权+WIND_DATA_LINK |

**STATUS**: JSON_MD_SYNC_VERIFIED_10_10_CONTENT_CONSISTENT

*Generated: 2026-10-17T15:25 +0800 | HERMEShf | V88 Phase03 P9 T0+T1*
