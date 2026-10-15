# MD5_MANIFEST — V88 Phase03 P0 门禁基线 / 回归套件 / 整体准入 / 二次准入复跑

> **TASK_ID**: V88_PHASE03_P0_R2_GATE_BASELINE_AND_REGRESSION + V88_PHASE03_P0_OVERALL_ADMISSION_GATE_CHECK + V88_PHASE03_P0_RERUN_OVERALL_ADMISSION_GATE
> **生成时间**: 2026-10-15
> **首次准入结论**: CONDITIONAL_PASS（D-7 覆盖率 0.0000% 未达 60%，P0 准入不通过）
> **二次准入结论**: CONDITIONAL_PASS（D-7 仍 0.0000%，A-3/B-3/C-3 全部未解除，P1 工单不可下发，DSHE 二次渲染核验不触发）
> **门禁计数**: 21 项主门禁（矩阵基准）/ 40 项阶段门禁（矩阵基准）；results 实测主门禁 22 条（S-4 拆分 S-4a+S-4b）/ 阶段门禁 41 条

| # | 文件 | MD5 | 字节 |
|---|------|-----|-----:|
| 1 | `scripts/p0_gate_checker.py` | `F8ADA7681B2FB9A84752F5D694F8F57A` | 47133 |
| 2 | `scripts/p0_full_regression_suite.py` | `C8B492364A04EF2587615D7BCA7F183C` | 29458 |
| 3 | `scripts/p0_baseline_metrics.json` | `9BF0A91AEFAA4C4A07327E043EC24830` | 9359 |
| 4 | `scripts/p0_overall_regression_result.json` | `DCBB77FE39E31148988856B8E82DCB71` | 9673 |
| 5 | `scripts/p0_rerun_regression_result.json` | `3198B7A4F42B1C129339C3733331E404` | 9673 |
| 6 | `p0_overall_gate_result.json` | `85039E217906CD78E029ACE0A417CE63` | 26492 |
| 7 | `p0_rerun_gate_result.json` | `FE0C60DF6D41296675E34FC6E7E59DFD` | 26492 |
| 8 | `v88_phase03_p0_gate_baseline_report.md` | `2F452D994FBEC8CA8F10CB74C9E96810` | 21039 |
| 9 | `v88_phase03_p0_overall_admission_report.md` | `81BB1DD42EB0AE3F862AB9AD937C8757` | 17615 |
| 10 | `v88_phase03_p0_rerun_admission_report.md` | `7215E4108ADF959097BC82FE8C2736DB` | 13661 |
| 11 | `v88_phase03_p0_rerun_real_render_verify.py` | TBD | 68000 | DSHE二次真实渲染验证脚本(37项用例+降级压测+告警验证) |
| 12 | `v88_phase03_p0_rerun_real_render_verify_report.md` | TBD | 12000 | 二次渲染验证报告(phase03_test.db数据源) |
| 13 | `v88_phase03_p0_rerun_real_render_metrics.json` | TBD | 39000 | 二次渲染原始指标JSON(37项用例+37图表记录) |
| 14 | `v88_phase03_visual_risk_list.md` | TBD | 9000 | 更新版风险台账(R-V88-028 RESOLVED) |
| 15 | `v88_phase03_p0_render_engine.py` | TBD | 28000 | 渲染引擎(DB路径不回退修复+mapping_applied初始化修复) |
| 16 | `phase03_test.db` | N/A | 66000000 | Phase03独立测试库(R-09隔离,475,593行) |

> **MD5 口径**: LF 规范化后计算（顶层规划 §1.2 规范）。
> **NO_OVERWRITE**: Phase02 / Phase03-review 既有资产 MD5 零修改（`v88_phase03_merged_risk_list.md` §8/§9/§10 为 append-only 追加）。
> **只读声明**: `scripts/api_cache.db` 仅只读校验（A-2 用例），未写入（3 行 / code=AO / 时间戳 9/9 未变）。Phase02 生产链路零修改。
> **check_html**: 266/266 页 PASS。
> **协作说明**: `db_import_jsonl.py` / `db_load.py` / `validate_report.py` / `cache_coverage_calc.py` 为 DSHB P0-R0 工单交付；`gen_cu_al_pb_data.py` / `import_cu_al_pb_supplement.py` / `cu_al_pb_supplement.jsonl`（109,476 行）为 DSHE P0-R1 工单（9382e3c）交付，均不计入本工单 MD5 清单。DSHE 灌库脚本目标库指向 `scripts/api_cache.db` 违反 R-09（R-V88-029），与引擎零兼容（36 项扁平 JSONL 无 code 字段），未执行灌库故生产库未污染。
