# MD5 Checksum List V4 — V86 别名引擎 Gate 终审 V4 最终归档

> 任务: `DSHE_V86_ALIAS_MONITORING_GAP_CLASSIFICATION_AND_FINAL_V4_ARCHIVE` · T3.4
> 分支: `feature/v85-chart-template`
> 版本: `v86.0.0-frozen`
> DSHB 基线: commit 311f82c (FULL_PASS FINAL)
> 生成日期: 2026-10-03
> 约束: NO_ZHIJI_API_CALL / NO_MODIFY_V85 / NO_OVERWRITE

---

## V4 终版交付物 (dshe_alias_gate_final_v4/)

```
MD5 校验和  文件大小(B)  文件名
F0B2D42AADC661A65839B0C59DD9DA2F  00027587  v86_alias_final_archive_bundle_v4.md
D7041E8A445DEAE09A75B3B09D0418E0  00065874  v86_alias_gate_final_demo_v5.md
44D80858A9DDA0C0C38FA906EE6AAB7A  00061858  v86_alias_portal_caliber_second_review_v3.md
7B70451CEF74D9963B27591A5D176F49  00068543  v86_alias_risk_monitoring_review_v3.md
```

**v4 小计**: 4 文件, 223,862 字节

---

## V3 交付物 (dshe_alias_gate_final_v3/)

```
MD5 校验和  文件大小(B)  文件名
F4742AA74706CC6D60F77C2AE6885186  00022695  v86_alias_final_archive_bundle_v3.md
9DCC2735D82760214785077DB1A71FD9  00035914  v86_alias_gate_final_demo_v4.md
B6C79212F2538321502F04A6C2C0E678  00041813  v86_alias_portal_caliber_second_review_v2.md
9D001487524FE9F990BF11890A4F5DDF  00039533  v86_alias_risk_monitoring_review_v2.md
```

**v3 小计**: 4 文件, 139,955 字节

---

## V2 交付物 (dshe_alias_gate_final_v2/)

```
MD5 校验和  文件大小(B)  文件名
080E8D51105126678EDF93ED7D939592  00004986  MD5_CHECKSUM_LIST_v2.md
FF70B0078685580E084D546F80434B12  00031183  v86_alias_final_archive_bundle_v2.md
9DADDB56D5C4B48DC9DB4EC05FFAB3DE  00032107  v86_alias_gate_final_demo_v3.md
1B70000204DAD44E729D5A6C05B9EEC0  00032330  v86_alias_portal_caliber_second_review.md
AB5638EDC93CF64AF4111F79B5C47AD9  00029765  v86_alias_risk_monitoring_review.md
```

**v2 小计**: 5 文件, 130,371 字节

---

## V1 交付物 (dshe_alias_gate_final/)

```
MD5 校验和  文件大小(B)  文件名
DF5470C442D26FE8463B22E3DDFDF0DF  00004380  MD5_CHECKSUM_LIST.md
022CDDAC5F54F36674C44FE40D339716  00029230  v86_alias_caliber_final_audit.md
3D87DFE2AF99FF60A56E1D369B9A9DB3  00032140  v86_alias_final_archive_bundle.md
29242B40022C2D1F607C73F4952F20C1  00037752  v86_alias_gate_final_demo_package.md
0706108693FAC5DADAE4F047CC78B20B  00066123  v86_alias_grafana_panels_final.md
E29D7B1F3DDA4FFC83C0531C4BCC3A08  00048879  v86_alias_portal_deviation_fix_report.md
```

**v1 小计**: 6 文件, 218,504 字节

---

## DSHB Gate 终审升级 (dshb_gate_upgrade_review/)

```
MD5 校验和  文件大小(B)  文件名
—  00026713  v86_gate_upgrade_assessment_report.md
—  00052671  v86_conditional_conditions_closure_v2.md
—  00046427  v86_open_risks_disposition_v2.md
—  00031348  v86_dependency_gap_impact_assessment.md
—  00083225  v86_preflight_checklist_v2.md
—  00006408  MD5_MANIFEST_v2.md
```

**DSHB 升级小计**: 6 文件

---

## 校验和统计

| 目录 | 文件数 | 总大小 | 说明 |
|------|--------|--------|------|
| v4 终版 | 4 | 223,862 B | SOP对齐 + 口径v3 + 演示v5 + 归档v4 |
| v3 | 4 | 139,955 B | 缺口分级 + 口径复核v2 + 演示v4 + 归档v3 |
| v2 | 5 | 130,371 B | 风险监控 + 口径复核 + 演示v3 + 归档v2 |
| v1 | 6 | 218,504 B | 门户修复 + 面板 + 口径终审 + 演示 + 归档 |
| DSHB 升级 | 6 | — | Gate 升级 + 风险处置 + 前置清单V2 |
| **DSHE 总计** | **19** | **712,692 B** | **~696 KB** |
| **全部总计** | **25** | **~929 KB** | **含 DSHB** |

---

## 校验命令

```bash
# 验证 v4 文件完整性
cd analysis/e2e_output/v86/dshe_alias_gate_final_v4/
Get-FileHash v86_alias_risk_monitoring_review_v3.md -Algorithm MD5
Get-FileHash v86_alias_portal_caliber_second_review_v3.md -Algorithm MD5
Get-FileHash v86_alias_gate_final_demo_v5.md -Algorithm MD5
Get-FileHash v86_alias_final_archive_bundle_v4.md -Algorithm MD5

# 验证 v3 文件完整性
cd ../dshe_alias_gate_final_v3/
Get-FileHash v86_alias_risk_monitoring_review_v2.md -Algorithm MD5
Get-FileHash v86_alias_portal_caliber_second_review_v2.md -Algorithm MD5
Get-FileHash v86_alias_gate_final_demo_v4.md -Algorithm MD5
Get-FileHash v86_alias_final_archive_bundle_v3.md -Algorithm MD5

# 验证 v2 文件完整性
cd ../dshe_alias_gate_final_v2/
Get-FileHash v86_alias_risk_monitoring_review.md -Algorithm MD5
Get-FileHash v86_alias_portal_caliber_second_review.md -Algorithm MD5
Get-FileHash v86_alias_gate_final_demo_v3.md -Algorithm MD5
Get-FileHash v86_alias_final_archive_bundle_v2.md -Algorithm MD5

# 验证 v1 文件完整性
cd ../dshe_alias_gate_final/
Get-FileHash v86_alias_portal_deviation_fix_report.md -Algorithm MD5
Get-FileHash v86_alias_grafana_panels_final.md -Algorithm MD5
Get-FileHash v86_alias_caliber_final_audit.md -Algorithm MD5
Get-FileHash v86_alias_gate_final_demo_package.md -Algorithm MD5
Get-FileHash v86_alias_final_archive_bundle.md -Algorithm MD5
```

---

*MD5 Checksum List V4 由 DSHE_V86_ALIAS_MONITORING_GAP_CLASSIFICATION_AND_FINAL_V4_ARCHIVE T3.4 生成*
*分支: feature/v85-chart-template · 资产版本: v86.0.0-frozen*
*DSHB 基线: commit 311f82c (FULL_PASS FINAL, 114 项前置清单, 5/5 PASS)*
