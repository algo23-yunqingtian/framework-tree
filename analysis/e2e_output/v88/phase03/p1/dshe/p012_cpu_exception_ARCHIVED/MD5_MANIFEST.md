# MD5_MANIFEST — V88_PHASE03_P1_DSHE_P012_CPU_THRESHOLD_EXCEPTION_HANDLER_JOB

> 更新时间: 2026-10-16 18:15 UTC+8
> 前置: c271f59 (P012_FINAL_TRIPLEFIX)

## 新增交付物

| 文件 | MD5(12位) | MD5(全量) | 大小 |
|------|-----------|-----------|------|
| v88_phase03_p012_cpu_threshold_exception_note.md | 338C81BA3523 | 338C81BA3523576E055AAB8EF155666B | 6270 |
| p012_optimization_option_evaluation.md | B5C1F086BF87 | B5C1F086BF87664C1A458A65805E8574 | 6845 |
| p012_gate_threshold_apply_exemption.md | 2E20AE46CD70 | 2E20AE46CD70D8EF4C33BF9FC26C7FC7 | 5159 |
| v88_phase03_r3_e2e_regression_after_exception_handle.md | 8F9FDF5C9B41 | 8F9FDF5C9B415727F572EC9B2678D531 | 2626 |
| v88_phase03_p1_dshe_risklist.md | EF4D9BB12AC9 | EF4D9BB12AC9C5F027D7AB42F248E123 | 2727 |
| frozen/p012_gate_manifest.json | A4FB9C55ECFB | A4FB9C55ECFBB708CBA4EBFC9A0BC9DE | 1787 |
| frozen/v88_p012_full_link_cpu_compare.json | C10D5A32ECCB | C10D5A32ECCB8A0D5866B872538F7C5A | 8911 |
| frozen/v88_phase03_p012_cpu_threshold_exception_note.md | 338C81BA3523 | 338C81BA3523576E055AAB8EF155666B | 6270 |
| frozen/p012_optimization_option_evaluation.md | B5C1F086BF87 | B5C1F086BF87664C1A458A65805E8574 | 6845 |
| frozen/p012_gate_threshold_apply_exemption.md | 2E20AE46CD70 | 2E20AE46CD70D8EF4C33BF9FC26C7FC7 | 5159 |

## 前置交付物（c271f59，MD5 不变）

| 文件 | MD5(12位) | MD5(全量) | 大小 |
|------|-----------|-----------|------|
| v88_p012_full_link_cpu_compare.json | C10D5A32ECCB | C10D5A32ECCB8A0D5866B872538F7C5A | 8911 |
| v88_phase03_p012_final_triplefix_note.md | 5ADBCAEAB11A | 5ADBCAEAB11A8F8E253A89D9667D6E4A | 3318 |
| v88_p012_full_link_bench_collector.py | C14E9044F6F9 | C14E9044F6F9D01412223E9F870C49CD | 9765 |

## 门禁复测结果
- P0-12: FAIL (口径已通过, 数值99.4871% > 1.75%)
- 门禁actual: "全链路优化后峰值 99.4871% (目标 ≤1.75%)"
- 豁免申请: 已提交 (FAIL→WARN)
- R-V88-034: 🟡 P2 EXEMPTION_REQUESTED
- R3 E2E: 8/8 PASS (含1项已知项)
