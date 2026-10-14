# V88 Phase02 MD5 清单

> 生成时间: 2026-10-14 21:10
> Agent: HERMEShf

## Phase02 轮询#1 交付物

`800d62bd8f14d2bcc320b591e6e0c19f  analysis/e2e_output/v88/phase02/audit/v88_phase02_monitor_shturl.md`
`02cfd447cfaa68773ad3f069e25ea07c  analysis/e2e_output/v88/phase02/audit/v88_phase02_audit_summary_report.md`
`228393b9a4dae37bb853426baa1d4e26  analysis/e2e_output/v88/phase02/audit/ic_ir_baseline.json`
`5d7bfe619162c0d6462d7a7985a029c2  analysis/e2e_output/v88/phase02/audit/ic_ir_drift_report.md`
`0240d7b83381511ff7d9291df9284c70  analysis/e2e_output/v88/phase02/scripts/ic_ir_drift_baseline.py`
`64aa264c1199130b0a4c7e391f601f81  analysis/e2e_output/v88/phase02/phase02_master_plan.md`
`812ec254b737f9fdf57da51ed060d0e5  analysis/e2e_output/v88/phase02/phase02_workitem_package.md`

## 基线校验

- V87 基线 #1: 0bcd94a8 (完整)
- V87 基线 #2: a0030737 (完整)
- Tag: 26d58a8 (不变)
- check_html.py: 266/266 PASS
- reclaim.py: PASS=9 FAIL=4 (历史遗留)

## 轮询#2 更新 (2026-10-14 21:30)

- `800d62bd8f14d2bcc320b591e6e0c19f` → `c2a3e8f1` (v88_phase02_monitor_shturl.md, 追加轮询#2)
- `02cfd447cfaa68773ad3f069e25ea07c` → 更新 (v88_phase02_audit_summary_report.md, 追加轮询#2)

### R-V88-006 澄清
- 146 = 123 matched + 24 partial (18转matched + 6 pending SMM)
- 已有数据 141/146 = 96.6%
- 6项pending与R-V88-004同源 (SMM付费)

## Phase02 DSHB 数据供给长稳交付物 (2026-10-15)

`C62F4E9526B62B610472AABB601A0749  analysis/e2e_output/v88/phase02/dshb/scripts/dshb_data_supply_engine.py`
`0F5D9A522338D0FF1F968EABA625CE22  analysis/e2e_output/v88/phase02/dshb/deliverables/v88_phase02_dshb_data_operation_report.md`
`AD6670CC78C53462A84C1991E2E9F06E  analysis/e2e_output/v88/phase02/dshb/deliverables/v88_phase02_dshb_7day_monitoring_report.md`
`C6305C853526376CFE67A06B123FB6DD  analysis/e2e_output/v88/phase02/dshb/logs/dqa_daily_log.json`
`4E131D7F26BC9400D1F8C92958FB7961  analysis/e2e_output/v88/phase02/dshb/logs/icir_time_series_log.json`
`E8C12FF84AE967714479C0ADF9017E6E  analysis/e2e_output/v88/phase02/dshb/logs/dshe_push_log.json`
`3CC0FC0705AF97075D22B91D679F9BCD  analysis/e2e_output/v88/phase02/dshb/logs/pending_alt_reference_data.json`

### DSHB 交付物摘要

| 文件 | MD5 | 大小 | 类型 |
|------|:---:|:----:|:----:|
| dshb_data_supply_engine.py | C62F4E95 | 25,577 | 数据供给引擎脚本 |
| v88_phase02_dshb_data_operation_report.md | 0F5D9A52 | 17,963 | 数据运维报告 |
| v88_phase02_dshb_7day_monitoring_report.md | AD6670CC | 3,400 | 7天监控报表 |
| dqa_daily_log.json | C6305C85 | 9,757 | DQA逐日日志 |
| icir_time_series_log.json | 4E131D7F | 13,992 | IC/IR时序日志 |
| dshe_push_log.json | E8C12FF8 | 11,515 | DSHE推送日志 |
| pending_alt_reference_data.json | 3CC0FC07 | 5,128 | Pending备选参考数据 |

### 约束合规

- V87 基线 #1: 0bcd94a8 (完整, 未修改)
- V87 基线 #2: a0030737 (完整, 未修改)
- Tag: 26d58a8 (不变, 未修改)
- check_html.py: 266/266 PASS
- reclaim.py: PASS=9 FAIL=4 (历史遗留, 非本阶段引入)
- APPEND_ONLY: 7份交付物全部新建, 无覆盖
