# V86-RC2 投产 Stage 2 审计 — MD5 清单

> **工单**: `HERMES_V86_RC2_PROD_STAGE2`
> **分支**: `feature/v85-chart-template` @ `f165034`
> **生成时间**: 2026-10-05（T+1d）
> **生成方式**: `md5sum` 实测，`wc -l -c` 实测

| # | 文件 | 大小 | 行数 | MD5 |
|---|------|------|------|-----|
| 1 | `v86_rc2_prod_continuous_audit_report_stage2.md` | 11,974 B | 246 | `aca82322e02233fb41155f8f415dc340` |
| 2 | `v86_rc2_prod_shadow_compare_report_stage2.md` | 8,740 B | 183 | `53f14903205323e77c72780166fd8cfb` |
| 3 | `v86_rc2_prod_progress_risk_tracking_stage2.md` | 12,556 B | 255 | `1fa42f61b8424a815281803510b8acbb` |
| 4 | `v86_rc2_gray_gate_pre_review_package.md` | 14,333 B | 315 | `b1fa1a981fc0b35633e88f1fa7b50dde` |
| 5 | `MD5_CHECKSUM_LIST_prod_stage2.md` | — | — | 本文件 |

**合计**: 4 份 Stage2 审计文档 + 1 份 MD5 清单 / 47,603 bytes

---

## Stage1 产物完整性校验（NO_OVERWRITE 验证）

以下 4 份 Stage1 产物在本轮 Stage2 审计前后 MD5 完全一致，证明 **NO_OVERWRITE=TRUE 约束合规，零覆盖**：

| # | 文件 | MD5 | 校验结果 |
|---|------|-----|---------|
| 1 | `v86_rc2_prod_continuous_audit_report.md` | `d83f3a7a34ed487839b508ff118c9c44` | ✅ 未改动 |
| 2 | `v86_rc2_prod_shadow_compare_report.md` | `e00e564b6db35612965c0d7178558f32` | ✅ 未改动 |
| 3 | `v86_rc2_prod_progress_risk_tracking.md` | `505630f4c95f84afa9c29c9c55af0b18` | ✅ 未改动 |
| 4 | `v86_rc2_gray_gate_audit_package.md` | `e7fdc18d5da17c50d1eb87c89e11a93a` | ✅ 未改动 |

**Stage1 产物 4/4 MD5 匹配，零覆盖。**

---

## PREP 归档完整性校验

| 审计项 | 结果 |
|--------|------|
| 快照基线文件数 | 132 |
| MD5 匹配（未变更） | 132/132 |
| 封板后 DSHB/DSHE 文件变更 | 0 |
| 8 项冻结条目违规 | 0 |
| **判定** | ✅ **PREP 归档零覆盖，零违规** |

---

### 修订记录

| 版本 | 说明 |
|------|------|
| v1 (2026-10-05) | Stage2 审计初始版本，4 份文档 + MD5 清单 |

---

> **工单**: `HERMES_V86_RC2_PROD_STAGE2`
> **MD5 校验**: 4/4 Stage2 文档已登记
> **NO_OVERWRITE 验证**: Stage1 产物 4/4 未改动 ✅ / PREP 归档 132/132 零违规 ✅
