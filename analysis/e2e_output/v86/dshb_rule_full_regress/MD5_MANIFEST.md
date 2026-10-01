# MD5 Checksum Manifest

> Task: DSHB_V86_RULE_ENGINE_FULL_INTEGRATION_REGRESSION_AND_DOC_FINALIZE
> Branch: feature/v85-chart-template
> Generated: 2026-10-02 00:08
> Directory: analysis/e2e_output/v86/dshb_rule_full_regress/

## Deliverable Files

| File | MD5 | Size (bytes) |
|------|-----|-------------|
| ci_report_enhanced.json | 110843BBF4A439F666CDEFC6B39F4787 | — |
| ci_result_enhanced.txt | D4D55E58C33263E5370EC38BCF1BAA42 | — |
| ci_rule_alias_enhanced.py | 1CE4CE251DADE910DCE38E19361C7D5A | 72576 |
| joint_regression_results.json | 264ACAE99408B6C242AB528FCD1DE52C | 58983 |
| joint_regression_runner.py | EBE5B1CF7B19882CE7F4562951C5E293 | 36123 |
| v86_metric_caliber_doc.md | 1728DB0DBAA14FA9CF43757EE332CFF5 | 20150 |
| v86_rule_alias_joint_regression.md | 11B135D949FE231F5A46EFB1A17D7034 | 14586 |
| v86_rule_asset_bundle.md | B6981C7470B07611F469AFDDF189EC16 | — |
| v86_rule_error_code_spec.md | B94EAF89B73E684AF54E952B840A7D65 | 35350 |

## Verification

```
cd analysis/e2e_output/v86/dshb_rule_full_regress
certutil -hashfile ci_rule_alias_enhanced.py MD5
certutil -hashfile joint_regression_runner.py MD5
certutil -hashfile v86_rule_alias_joint_regression.md MD5
certutil -hashfile v86_metric_caliber_doc.md MD5
certutil -hashfile v86_rule_error_code_spec.md MD5
certutil -hashfile v86_rule_asset_bundle.md MD5
certutil -hashfile joint_regression_results.json MD5
certutil -hashfile ci_report_enhanced.json MD5
certutil -hashfile ci_result_enhanced.txt MD5
```
