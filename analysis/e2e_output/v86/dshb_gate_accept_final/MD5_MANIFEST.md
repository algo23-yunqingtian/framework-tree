# V86 Gate Acceptance MD5 Manifest
#
# Task: DSHB_V86_RULE_ALIAS_JOIN_PROD_STRESS_GATE_ACCEPT_AND_RISK_REGISTER
# Branch: feature/v85-chart-template
# Commit: 3044964
# Generated: 2026-10-02
#
# Files in this task:
#   6 deliverable files + 2 metadata files (MD5_MANIFEST.md, JOB_READY.flag)
#
# Verification:
#   PowerShell: Get-FileHash <filename> -Algorithm MD5
#   Linux:      md5sum <filename>
#
# ---
# File MD5 Checksums:
# ---

CAB25211493E500793BA51A4C1C76066  53912  joint_prod_stress_test.py
9D95563EB922C5443FBC1200122FC703  12091  stress_test_results.json
5C6B7BA7629E3BE43BA0791004DA23B2  13714  v86_join_prod_stress_test_report.md
476033F7F9C1A0A7FAF7EA7772C814F4  21131  v86_gate_acceptance_final_report.md
505B30E0949A49F13C0780A5DC78FEE5  33165  v86_launch_risk_register.md
DCEEFC84F2EE216F53B591477A6E73F8  31035  v86_preflight_checklist.md

# ---
# File Sizes (KB):
# ---

joint_prod_stress_test.py             52.6 KB  (benchmark-derived simulation script)
stress_test_results.json              11.8 KB  (JSON - all stress test results)
v86_join_prod_stress_test_report.md   13.4 KB  (report - joint stress test)
v86_gate_acceptance_final_report.md   20.6 KB  (report - gate acceptance)
v86_launch_risk_register.md           32.4 KB  (report - risk register)
v86_preflight_checklist.md            30.3 KB  (checklist - pre-flight)
JOB_READY.flag                         1.8 KB  (metadata - completion flag)
MD5_MANIFEST.md                        1.7 KB  (metadata - this file)

# Total: 164.6 KB across 8 files

# ---
# Related Deliverables (from prior tasks):
# ---

DSHB Rule Engine (commit f694618):
  analysis/e2e_output/v86/dshb_rule_ci_stress/
  analysis/e2e_output/v86/dshb_rule_full_regress/
  analysis/e2e_output/v86/dshb_rule_predev/
  analysis/e2e_output/v86/dshb_rule_prod_prep/

DSHE Alias Engine (commit 81268a6):
  analysis/e2e_output/v86/dshe_alias_joint_check/
  analysis/e2e_output/v86/dshe_alias_predev/
  analysis/e2e_output/v86/dshe_alias_prod_prep/
