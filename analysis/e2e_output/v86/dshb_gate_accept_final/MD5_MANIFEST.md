# V86 Gate Acceptance MD5 Manifest
#
# Task: DSHB_V86_RULE_ALIAS_JOIN_PROD_STRESS_GATE_ACCEPT_AND_RISK_REGISTER
# Branch: feature/v85-chart-template
# Generated: 2026-10-02
#
# Files in this task:
#   6 files total
#
# Verification:
#   Get-FileHash <filename> -Algorithm MD5
#
# ---
# File MD5 Checksums:
# ---

0773805B4044B5723FB4148E4EBF51BA  v86_preflight_checklist.md
5C6B7BA7629E3BE43BA0791004DA23B2  v86_join_prod_stress_test_report.md
834315DC7C43454355BB6AFF16834403  v86_gate_acceptance_final_report.md
9D95563EB922C5443FBC1200122FC703  stress_test_results.json
E3EC8165A20451FDA6E6D8AF3A6114DB  v86_launch_risk_register.md
F6D2C06C4E9E3CF2545D1103AE2E027A  joint_prod_stress_test.py

# ---
# File Sizes:
# ---

joint_prod_stress_test.py             (script - benchmark-derived simulation)
stress_test_results.json              (JSON - all stress test results)
v86_join_prod_stress_test_report.md   (report - joint stress test results)
v86_gate_acceptance_final_report.md   (report - comprehensive gate acceptance)
v86_launch_risk_register.md           (report - P0/P1/P2 risk register)
v86_preflight_checklist.md            (checklist - pre-flight verification)

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
