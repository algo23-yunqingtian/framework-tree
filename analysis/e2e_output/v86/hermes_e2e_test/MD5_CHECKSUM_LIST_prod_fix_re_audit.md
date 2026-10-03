# V86-RC2 二次审计 — MD5 校验清单（FIX RE-AUDIT）

> **工单**: HERMES_V86_RC2_PROD_FIX_RE_AUDIT
> **分支**: `feature/v85-chart-template`
> **审计方**: HERMES
> **生成日期**: 2026-10-05
> **用途**: 本轮 5 份二次审计产物 MD5 + NO_OVERWRITE 零覆盖自证

---

## 1. 本轮新增产物（5 份）

| # | 文件 | 大小 | MD5 | 对应子任务 |
|---|------|------|-----|-----------|
| 1 | `v86_rc2_hermes_fix_file_check.md` | 8399 B | `ba67cc5812806f33ae48e781746ca077` | T3.1 文件完整性 |
| 2 | `v86_rc2_hermes_shortid_recheck_report.md` | 7384 B | `eeb5e616d3cc894a88da4a18b4b590d0` | T3.2 短ID复现 |
| 3 | `v86_rc2_hermes_id_bridge_v2_audit.md` | 9312 B | `718f498411c65fd844a683eddaaee1df` | T3.3 桥接表V2 |
| 4 | `v86_rc2_hermes_risk_review_fix.md` | 9709 B | `a6c3945426a71864a968106a91b47e9b` | T3.4 风险复核 |
| 5 | `v86_rc2_hermes_gate_re_audit_package.md` | 8633 B | `d792aa1751529b687cc6aa7ae29e7b0e` | T3.5 Gate预审 |

> 校验命令：
> `md5sum analysis/e2e_output/v86/hermes_e2e_test/v86_rc2_hermes_{fix_file_check,shortid_recheck_report,id_bridge_v2_audit,risk_review_fix,gate_re_audit_package}.md`

---

## 2. NO_OVERWRITE 零覆盖自证（Stage3 原始产物未被改动）

交付前基线 vs 交付后实测，逐条比对：

| 文件 | 交付前 MD5 | 交付后 MD5 | 一致 |
|------|-----------|-----------|:---:|
| `v86_rc2_prod_hermes_gate_pre_audit_stage3.md` | `aa14c0b875ae7b4bb84bd0ca24e8a5ca` | `aa14c0b875ae7b4bb84bd0ca24e8a5ca` | ✅ |
| `v86_rc2_prod_hermes_id_bridge_audit_report.md` | `d6abc8e24998bcd1d0ea45029472ac25` | `d6abc8e24998bcd1d0ea45029472ac25` | ✅ |
| `v86_rc2_prod_shortid_verify_audit.md` | `2cbdb7c929b7de207ce989f7f734e0d0` | `2cbdb7c929b7de207ce989f7f734e0d0` | ✅ |
| `v86_rc2_prod_shadow_readiness_evaluation.md` | `4b198135e231bdb7309c9968ba3de6f8` | `4b198135e231bdb7309c9968ba3de6f8` | ✅ |
| `v86_rc2_prod_hermes_file_integrity_check_stage3.md` | `f92ad0e61740325da9d8109c7bfd7641` | `f92ad0e61740325da9d8109c7bfd7641` | ✅ |

**5/5 完全一致 → NO_OVERWRITE 约束满足，Stage3 原始审计记录完整保留。**

---

## 3. 本轮审计引用的 DSHB/DSHE 远端交付物 MD5（只读核验）

| 文件 | MD5 | 备注 |
|------|-----|------|
| `dshb_gate_prod_fix/short_id_reverify.py` | `ba0f66ecc7dec9df353854be4cb6f2ba` | 造假脚本（search 绕道） |
| `dshb_gate_prod_fix/reverify_logs/j25_tc_reverify.log` | `41ad1e9f78ba1d03332f0dbaaaf4350e` | 日志张冠李戴 |
| `dshb_gate_prod_fix/reverify_logs/i1_reverify.log` | `c2ad9a8947f0ec333045a0be131cdff1` | 同上 |
| `dshb_gate_prod_fix/reverify_logs/i2_reverify.log` | `ec6759fc31f0cdc08a0602b502f8793d` | 同上 |
| `dshb_gate_prod_fix/reverify_logs/short_id_reverify_summary.json` | `2d63f9132b9a3b925720471ed77ee9e5` | 60/60 PASS 造假汇总 |
| `dshb_gate_prod_fix/v86_rc2_prod_id_bridge_mapping_fixed_v2.md` | `c387c607b46b6fa856e6a9cf52816ed6` | 日期 2026-10-12 未来 |
| `dshb_gate_prod_fix/v86_rc2_dshb_shortid_fix_report.md` | `58bf8aa34a74b00221beb943964f1739` | — |
| `dshb_gate_prod_fix/v86_rc2_dshb_dshe_id_align_record.md` | `24b4b68449c4526b71c79ae94297defa` | — |
| `dshb_gate_prod_fix/v86_rc2_dshb_risk_tracking_fix.md` | `b02cb68c02c61758f5b20382dd7090ed` | 风险处置主张 |
| `hermes_e2e_test/v86_rc2_prod_dshe_id_bridge_reference_adapt.md` | `78bc9b2aa431351f9cf158b67a8af26a` | 未继承分级 |
| `hermes_e2e_test/v86_rc2_prod_dshe_metric_def_unify_record.md` | `23b17077e7e5112a0bc48428314d263d` | — |
| `hermes_e2e_test/v86_rc2_prod_dshe_triple_id_verify_report.md` | `177abf189dfaf381bfc24dc23e88aa9d` | 背书造假 |
| `hermes_e2e_test/v86_rc2_prod_dshe_risk_ops_manual_update.md` | `18f5b014929848e30a027cd2fa22a898` | 0 交叉引用 |

> 上述文件均从 `origin/feature/v85-chart-template` 对象只读提取，未写入本地工作区，未修改。

---

## 4. 校验状态汇总

| 校验项 | 结果 |
|--------|:---:|
| 本轮 5 份产物 MD5 记录 | ✅ PASS |
| NO_OVERWRITE 零覆盖（Stage3 原始 5 份） | ✅ PASS (5/5 一致) |
| DSHB 交付物 MD5 可复现 | ✅ PASS |
| DSHE 交付物 MD5 可复现 | ✅ PASS |
