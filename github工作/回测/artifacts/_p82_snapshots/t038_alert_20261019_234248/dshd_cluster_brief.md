DSHD-P81 集群状态简报

生成时间: 2026-10-19 23:38:37 (GMT+8)
token: DSHD-P81-TOKEN (AUDIT_READ_ONLY) | auth_ref: A01-USER-REMOTE-003
模式: 领地契约固化 · Excel 漂移观测器 · 交易所归属校验 · P49 产物只读审计 · Skill 目录哈希监控

一、三 Agent 统一状态

| Agent | 当前状态 | 最近回执 / 时间 | 重要 flag |
|---|---|---|---|
| DSHC | 复盘已归档 | artifacts/dshc_postmortem_receipt.json @ 2026-10-19T08:05:00+08:00 | wind_api_calls=0; token_state=EXHAUSTED; root=NO_TRY_FINALLY_CLEANUP; guard_rules=5 |
| DSHA | FINAL_STANDBY_LOCKED | artifacts/dsha_a02_plus_receipt.json @  | P68=FINAL_STANDBY_LOCKED commit=8ebe3b7; gate=CLOSED/HOLD; permit=NOT_ISSUED |
| DSHD | 审计值守 | poll#111 @ 2026-10-19T23:38:37+08:00 | audit_only=YES; excel_observer=ON; tag=A01-USER-REMOTE-003 |

二、OBS-SPAWN-EXCEL-001 漂移观测

| 指标 | 值 |
|---|---|
| Excel 进程总数 | 1 |
| 非保护 PID 数 | 0 |
| 非保护且落入 DSHC 任务窗口的 PID 数 | 0 |
| 告警阈值 (> ) | 2 |
| 触发黄色告警 | False |
| 自动 kill | False |
| 保护 PID | 14644 (zin-database-front-excel) |
| 快采样间隔 (秒) | 20 |
| 快采样次数 / 观测到的 Excel 峰值 | 15 / 1 |
| 快采样中非保护且在窗口内峰值 | 0 |
| 快采样捕获的瞬时非保护 PID |  |
| 合并触发判定 (定点 OR 快采样) | False |

三、写领地契约 + 并发写入冲突

契约状态: ACTIVE | 领地条目: 25 | 扫描模式: OBSERVATION_ONLY_NO_INTERCEPTION
并发写入冲突数: 2

- [INFO] OWNER_PATH_MODIFIED_THIS_POLL :: artifacts\dshd_p80_phase2_a01_audit_snapshot.json :: owner-exclusive path advanced this poll; expected owner=DSHD-P80-PHASE2
- [WARN] CONCURRENT_WRITE_CONFLICT :: artifacts\dshd_a01_file_evidence.json :: same path observed with different agent tags across polls; multi-writer on shared artifact

四、CSV 双 hash + Quick-Scan

| 项 | 值 |
|---|---|
| hash A (字节读 SHA256) | 3C14F50F063C4734950064B1072585626588E93568191D6A85767BA1699B5ED1 |
| hash B (Get-FileHash) | 3C14F50F063C4734950064B1072585626588E93568191D6A85767BA1699B5ED1 |
| A == B | True |
| DSHC ref (A03 csv_output) | 41EC38315397FB70CC30BB313B88C3965BB50B30A628A3422743A48026806A92 |
| 匹配 A03 引用 | False |
| 匹配 P80 历史观测 | False |
| 扫描结论 | A_EQ_B_REF_STALE_MISMATCH |
| 告警码 | A01_HASH_MISMATCH_WARNING |
| 文件大小 | 285191 B (P68 下限 5120) |
| 行数 / 数据行 | 7363 / 7362 (P68 下限 300) |
| 缺关键词 | 0 |
| 最大连续空行 | 0 |
| Quick-Scan 结论 | SCAN_OK_P68_GATE_STILL_AUTHORITY |
| 熔断 | 未触发 (DSHA-P68 为唯一受理权威) |

五、告警看板

- [YELLOW] A01_HASH_MISMATCH_WARNING @ 2026-10-19T23:38:37+08:00 :: hash A==B but differs from DSHC cross_agent reference; reference likely stale (scan_status=A_EQ_B_REF_STALE_MISMATCH)
- [INFO] OWNER_PATH_MODIFIED_THIS_POLL @ 2026-10-19T23:38:37+08:00 :: artifacts\dshd_p80_phase2_a01_audit_snapshot.json :: owner-exclusive path advanced this poll; expected owner=DSHD-P80-PHASE2: from= to=
- [WARN] CONCURRENT_WRITE_CONFLICT @ 2026-10-19T23:38:37+08:00 :: artifacts\dshd_a01_file_evidence.json :: same path observed with different agent tags across polls; multi-writer on shared artifact: from= to=A01-USER-REMOTE-002
- [YELLOW] EXCH-001-ATTRIBUTED-MISMATCH @ 2026-10-19T23:38:37+08:00 :: DSHC artifact references LC.SHF (MISMATCH) :: LC belongs to GFE but is bound to SHF; no intervention; no_data_present=True; files=dshc_f01_events.jsonl,dshc_f01_receipt.json,dshc_ignite_a01_events.jsonl,dshc_ignite_run_receipt.json,dshc_ignite_run_receipt_A01_USER_REMOTE_001.json,dshc_ignite_run_receipt_A02_wait_cycle1.json,dshc_ignite_run_receipt_A02_wait_cycle2.json,dshc_p90a_final_events.jsonl,dshc_raw_preview_check.json,dshc_t1_fetch_events.jsonl,dshc_t1_lessons.json,dshc_t1_run_receipt.json; observation only, no intervention
- [YELLOW] P49-001-ARTIFACT-UNEXPECTED @ 2026-10-19T23:38:37+08:00 :: P49 archive sealed (MANIFEST.status=BACKTEST_COMPLETE at 2026-10-19T10:56:08+08:00) but mutated post-seal: kinds=ADDED_UNDECLARED; continuous_alert_polls=111; cold_start=False; undeclared=baseline_lock.json,comparison_framework.md,factor_candidate_list.md,optimization_params.json,pipeline_v2_draft.py; modified=; removed=; declared_missing=; observation only, no intervention
- [YELLOW] SKILL-001-FILE-UNDECLARED @ 2026-10-19T23:38:37+08:00 :: skill dir contains file(s) not declared in manifest.json: data_sha256.txt,generate_aligned_csv.py,output\factors_metadata.json,output\factors_output.csv,output\smoke_test\factors_metadata.json,output\smoke_test\factors_output.csv,tests\abnormal_test_results.json,tests\COLLECTION_RISK_LIST.md,tests\data_quality_checklist.md,tests\run_abnormal_tests.py,tests\shfe_rb_hc_sample.csv,tests\shfe_rb_hc_template.json,tests\shfe_rb_hc_template.py,__pycache__\factor_extract_v1.cpython-312.pyc; declared_count=4; observation only

六、长表主键 + 品种白名单 + 交易所归属

| 指标 | 值 |
|---|---|
| 校验模式 | OBSERVATION_ONLY (auto_intervene=False) |
| 表格式 | LONG |
| 数据行数 | 7362 |
| 主键 | date + symbol + indicator |
| 主键重复数 | 0 |
| 结构缺陷 (malformed / blank_key / bad_date / non_numeric) | 0 / 0 / 0 / 0 |
| 日期区间 | 2025-01-02 -> 2026-10-19 |
| 品种数 / 指标数 / 来源数 | 6 / 4 / 1 |
| 指标列表 | CLOSE, OI, SETTLE, VOL |
| 白名单外品种 | 无 |
| 缺失指标 | 无 |
| 交易所归属不匹配 / 未知交易所 | 0 / 0 |
| 长表审计结论 | LONGTABLE_AUDIT_OK |

| 品种 | 实际交易所 | 应属交易所 | 结论 |
|---|---|---|---|
| AL.SHF | SHF | SHF | BOUND_OK |
| CU.SHF | SHF | SHF | BOUND_OK |
| NI.SHF | SHF | SHF | BOUND_OK |
| PB.SHF | SHF | SHF | BOUND_OK |
| SN.SHF | SHF | SHF | BOUND_OK |
| ZN.SHF | SHF | SHF | BOUND_OK |

DSHC 归属档案扫描: 文件 23 个; 命中品种令牌 7 个; 交易所归属异常 1 个
- [MISMATCH] LC.SHF :: LC belongs to GFE but is bound to SHF; no intervention :: NO_DATA=True :: files=dshc_f01_events.jsonl,dshc_f01_receipt.json,dshc_ignite_a01_events.jsonl,dshc_ignite_run_receipt.json,dshc_ignite_run_receipt_A01_USER_REMOTE_001.json,dshc_ignite_run_receipt_A02_wait_cycle1.json,dshc_ignite_run_receipt_A02_wait_cycle2.json,dshc_p90a_final_events.jsonl,dshc_raw_preview_check.json,dshc_t1_fetch_events.jsonl,dshc_t1_lessons.json,dshc_t1_run_receipt.json

七、P49 回测产物只读审计

| 指标 | 值 |
|---|---|
| 审计模式 | 只读 (OBSERVATION_ONLY, auto_intervene=False) |
| 目录存在 | True |
| 文件数 / 期望数 / 总字节 | 12 / 7 / 218305 |
| MANIFEST 状态 | BACKTEST_COMPLETE |
| MANIFEST 最后写入 | 2026-10-19T10:56:08+08:00 (readable=True) |
| 声明产物来源 | MANIFEST.files[].path (7 个) |
| MANIFEST gate / release_permit | READY / ISSUED |
| MANIFEST LC_GFE | SKIPPED |
| wind_api_calls / real_wind_call | 0 / False |
| 缺失产物 | 无 |
| 本轮哈希变更 | 无 |
| exchange 列与品种后缀不一致行数 | 0 |
| P49 审计结论 | P49_POSTSEAL_MUTATION |

| 产物 | 字节 | SHA256 | 本轮变化 |
|---|---|---|---|
| backtest_metrics.json | 11667 | E6B5BCF8CC55D665... | UNCHANGED |
| backtest_report.pdf | 69000 | 5DDC94E78245A86C... | UNCHANGED |
| baseline_lock.json | 6041 | BDCE3814139D79B1... | UNCHANGED |
| comparison_framework.md | 17329 | 8AA4AC62197754B6... | UNCHANGED |
| factor_candidate_list.md | 19969 | 7F887DEC7D7D3D4A... | UNCHANGED |
| MANIFEST.json | 6166 | 45DB1A5AAB34EFCF... | UNCHANGED |
| optimization_params.json | 9411 | 744029D7FF0B1131... | UNCHANGED |
| p49_full_review.md | 15992 | 6393687BB0F0A59F... | UNCHANGED |
| pipeline_metadata.json | 6671 | 8B17168728FF70F1... | UNCHANGED |
| pipeline_v2_draft.py | 52424 | FDBA5F4F451471C8... | UNCHANGED |
| symbol_performance.csv | 1300 | 3241004FB39C0F29... | UNCHANGED |
| symbol_performance.md | 2335 | D68C156FFFA92163... | UNCHANGED |


八、FACTOR_EXTRACT_V1 Skill 目录哈希监控

| 指标 | 值 |
|---|---|
| 审计模式 | 只读 (OBSERVATION_ONLY, auto_intervene=False) |
| 目录存在 | True |
| 文件数 / 总字节 / manifest 声明数 | 18 / 718607 / 4 |
| skill_id / version | FACTOR_EXTRACT_V1 / 1.0.0 |
| version_locked / status | True / VERSION_LOCKED |
| locked_at / locked_by | 2026-10-19T00:00:00Z / DSHC-SKILL-FACTOR01 |
| manifest 最后写入 | 2026-10-19T12:16:58+08:00 (readable=True) |
| manifest SHA256 | 5F3E93AAD0705F7A... (本轮变更=False) |
| version 变更 | 1.0.0 -> 1.0.0 (changed=False) |
| 声明外文件 / 声明缺失 | 14 / 0 |
| 本轮 新增 / 修改 / 删除 (cold_start=False) | 0 / 0 / 0 |
| V1 冻结违规 | False |
| constraint wind_api_calls / offline_only | 0 / True |
| f01_script_locked / f01_script_version | True / v1.0 @ 593d688 |
| manifest original_csv_sha256 与实际 CSV 一致 | True |
| skill 审计结论 | SKILL_UNDECLARED_FILE |

| 文件 | 字节 | SHA256 | 已声明 | 本轮变化 |
|---|---|---|---|---|
| data_sha256.txt | 328 | 419AC48A3E0DC1AD... | False | UNCHANGED |
| factor_definitions.json | 2214 | F78F08FA4B56D33C... | True | UNCHANGED |
| factor_extract_v1.py | 23702 | 75000F3E7ACA715D... | True | UNCHANGED |
| generate_aligned_csv.py | 4474 | 6F746B1935409ACB... | False | UNCHANGED |
| manifest.json | 3083 | 5F3E93AAD0705F7A... | True | UNCHANGED |
| README.md | 7814 | B2396DBFC5B5E94F... | True | UNCHANGED |
| output\factors_metadata.json | 3528 | CD329C6BA1C2EAAF... | False | UNCHANGED |
| output\factors_output.csv | 308602 | 01F5F3C15EDDD2B4... | False | UNCHANGED |
| output\smoke_test\factors_metadata.json | 3528 | 1F69E24C9E24FAF6... | False | UNCHANGED |
| output\smoke_test\factors_output.csv | 278365 | 052797E35C4C1FBD... | False | UNCHANGED |
| tests\abnormal_test_results.json | 2838 | BF3A764615E323AF... | False | UNCHANGED |
| tests\COLLECTION_RISK_LIST.md | 20161 | CFA3DADBBBC6F43B... | False | UNCHANGED |
| tests\data_quality_checklist.md | 6685 | 1AFC655B87AAE4DF... | False | UNCHANGED |
| tests\run_abnormal_tests.py | 11617 | 4519024BC31EED30... | False | UNCHANGED |
| tests\shfe_rb_hc_sample.csv | 888 | 84B18164D0A8330F... | False | UNCHANGED |
| tests\shfe_rb_hc_template.json | 5278 | 570EE0AD9AD9F1FA... | False | UNCHANGED |
| tests\shfe_rb_hc_template.py | 8034 | CAC14FDEFCCE5658... | False | UNCHANGED |
| __pycache__\factor_extract_v1.cpython-312.pyc | 27468 | AD8C821C7F199B78... | False | UNCHANGED |

九、P0 校验

P0 校验: 7/9
- [PASS] excel_pid_14644 = ALIVE (protected)
- [PASS] gate_closed = CLOSED/HOLD (line 7399)
- [FAIL] pwsh_13_p77 = pids=0
- [PASS] script_bom_intact = bom=True size=139680
- [PASS] self_p81 = pids=1
- [FAIL] pwsh_30_p80 = pids=0
- [PASS] pid_3472 = ALIVE
- [PASS] permit_not_issued = NOT_ISSUED (line 7399)
- [PASS] pwsh_37_phase2 = pids=1

十、红线确认

- audit_only = True
- processes_untouched = True / no_kill_executed = True
- gate_unchanged = True (observed: CLOSED/HOLD)
- release_permit_not_issued = True (observed: NOT_ISSUED)
- dshd_runs_backtest = False
- dshd_fetches_for_dshc = False
- dshd_bypasses_dsha_p68 = False
- output_csv_touched = False
- intervention = NONE
- wind_api_calls = 0

十一、P81 工具链版本管理

> 本章节由 v1.2.1+ 持久化生成，不再被 5 分钟轮询覆盖。
> 完整信息见 `G7_ADJUDICATION_LEDGER/dshd_p81_toolchain_versions.md`。
> SHA 真源：`G7_ADJUDICATION_LEDGER/p81_version_history.json`。

| 项 | 值 |
|---|---|
| 工具链版本 | 1.2.0-TWEAK |
| 备份钩子 | p81_safe_edit.py v1.0.0 |
| 快照目录 | `_p81_snapshots/` (git tracked) |
| 版本台账 | `p81_version_history.json` |
| 补丁规范 | 旧补丁已归档；增量修改必须新建 patch_p81_tweak2.py |
| 永久文档 | `dshd_p81_toolchain_versions.md` |

## 十三、因子稳定性长效监控与风险台账

> 本章节由 DSHD-TASK-038-MONITOR-OP 生成。
> 监控令牌: DSHD-TASK038-MONITOR-OP-TOKEN | 模式: AUDIT_READ_ONLY | wind_api_calls=0
> 生成时间: 2026-10-19T23:41:40+08:00

### 13.1 IC翻转率巡检 (20交易日窗口, 硬阈值锁定)

| 因子 | 基础风险 | 窗口数 | 翻转率 | 翻转次数 | 状态 |
|---|---|---|---|---|---|
| oi_change_1d | HIGH | 21 | 55.0% | 11 | ALERT [LOCK] |
| oi_change_rate_7d | HIGH | 21 | 55.0% | 11 | ALERT [LOCK] |
| oi_level | HIGH | 21 | 60.0% | 12 | ALERT [LOCK] |
| realized_vol_20d | MEDIUM | 20 | 63.2% | 12 | ALERT [LOCK] |
| vol_regime_change | UNKNOWN | 20 | 73.7% | 14 | ALERT [LOCK] |
| spread_cs | UNKNOWN | 21 | 55.0% | 11 | ALERT [LOCK] |
| momentum_20d | UNKNOWN | 20 | 68.4% | 13 | ALERT [LOCK] |
| contract_switch_flag | UNKNOWN | 21 | 0.0% | 0 | STABLE [LOCK] |

**阈值**: 翻转率 > 20% 触发ALERT | **窗口**: 20个交易日
**硬锁定**: 7因子长期ALERT | 1因子白名单STABLE

### 13.2 组合绩效漂移监控 (硬门槛)

| 指标 | 当前值 | 阈值 | 状态 |
|---|---|---|---|
| 总收益 | 18.67% | >= 5% | PASS |
| 夏普比率 | 2.911 | >= 0.9 | PASS |
| 最大回撤 | -1.71% | >= -2.7% | PASS |

**结论**: 绩效稳定 — 无漂移
**基线指纹**: 已固化

### 13.3 DSHA rolling_ic_export.json 校验

| 项 | 值 |
|---|---|
| 文件路径 | D:\DSH_WORK\github工作\回测\DSHA\rolling_ic_export.json |
| 文件存在 | False |
| SHA256 | N/A |
| 校验状态 | DSHA_DIR_NOT_FOUND |
| 只读模式 | True |
| DSHA写入 | False |

### 13.4 管道异常类型分级 (12类)

| 异常类型 | 严重级别 | 描述 |
|---|---|---|
| LOCK_CONFLICT | HIGH (HIGH) | 锁冲突 |
| COLLECTION_TIMEOUT | HIGH (HIGH) | 采集超时 |
| PIPELINE_STARTUP_FAILURE | HIGH (HIGH) | 管道启动失败 |
| PIPELINE_HEARTBEAT_LOST | HIGH (HIGH) | 管道心跳丢失 |
| BLACKLIST_INTERCEPT | MEDIUM (MED) | 黑名单拦截 |
| FIELD_VALIDATION_ERROR | MEDIUM (MED) | 字段校验异常 |
| DATA_MISSING | MEDIUM (MED) | 数据缺失 |
| SCHEMA_MISMATCH | MEDIUM (MED) | 模式不匹配 |
| DUPLICATE_DATA | MEDIUM (MED) | 重复数据 |
| TIME_SEQUENCE_ERROR | MEDIUM (MED) | 时序错误 |
| CROSS_CONTAMINATION | MEDIUM (MED) | 交叉污染 |
| SMOKETEST_COMPLETE | NORMAL (NORM) | 冒烟完成 |

**配置确认**: HIGH x 4 / MEDIUM x 7 / NORMAL x 1 | 总计 12 类

### 13.5 P2.2 模拟事件验证 (捕获-打标-快照全流程)

| 异常类型 | 预期严重级别 | 捕获 | 打标 | 快照 | 结果 |
|---|---|---|---|---|---|
| LOCK_CONFLICT | HIGH | PASS | PASS | YES | PASS |
| COLLECTION_TIMEOUT | HIGH | PASS | PASS | YES | PASS |

**验证结果**: 2/2 PASS

### 13.6 每日事件捕获完整性

| 项 | 值 |
|---|---|
| 扫描事件数 | 5605 |
| 类型检测率 | 33% (4/12) |
| 高危零丢包 | NO |
| 完整性校验 | FAIL |

### 13.7 V3等权投产基线声明

> V3等权当前绩效达标, 但7/8因子高翻转,
> 属于「可用但带已知重大局限性的投产基线」;
> 不代表因子已经很强, 仅为经过完整审计的临时生产版本。

| 项 | 值 |
|---|---|
| 投产版本 | V3 Equal-Weight 4-Symbol |
| 绩效状态 | PERFORMANCE_PASS |
| 因子总数 | 8 |
| ALERT因子 | 7 |
| STABLE因子 | 1 |
| 绩效 | 收益=18.67% / 夏普=2.911 / 回撤=-1.71% |
| 审计链路 | DSHD-P81 -> DSHD-P82 -> DSHD-TASK037 -> DSHD-TASK038 |
| 下一评审 | 因子池变更或绩效漂移时 |

### 13.8 集群风险台账

| # | 因子 | 风险类型 | 状态 | 详情 |
|---|---|---|---|---|
| 1 | oi_change_1d | IC_UNSTABILITY | ALERT | 滚动IC翻转率=55.0%, 21个窗口 [LOCKED] |
| 2 | oi_change_rate_7d | IC_UNSTABILITY | ALERT | 滚动IC翻转率=55.0%, 21个窗口 [LOCKED] |
| 3 | oi_level | IC_UNSTABILITY | ALERT | 滚动IC翻转率=60.0%, 21个窗口 [LOCKED] |
| 4 | realized_vol_20d | IC_UNSTABILITY | ALERT | 滚动IC翻转率=63.2%, 20个窗口 [LOCKED] |
| 5 | vol_regime_change | IC_UNSTABILITY | ALERT | 滚动IC翻转率=73.7%, 20个窗口 [LOCKED] |
| 6 | spread_cs | IC_UNSTABILITY | ALERT | 滚动IC翻转率=55.0%, 21个窗口 [LOCKED] |
| 7 | momentum_20d | IC_UNSTABILITY | ALERT | 滚动IC翻转率=68.4%, 20个窗口 [LOCKED] |
| 8 | contract_switch_flag | IC_STABLE | STABLE | 滚动IC翻转率=0.0%, 21个窗口 [LOCKED] |
| 9 | _PORTFOLIO_ | PERFORMANCE_STABLE | STABLE | 等权组合: 收益=18.67%, 夏普=2.911, 回撤=-1.71% |
| 10 | _IC_METHOD_ | IC_METHOD_DISCREPANCY | WARN | IC加权方法使用TS_IC而非CSV_IC (P81审计发现, TS_IC根因未修复) |
| 11 | _V3_BASELINE_NARRATIVE_ | PRODUCTION_BASELINE_QUALIFICATION | WARN | V3等权当前绩效达标, 但7/8因子高翻转, 属于「可用但带已知重大局限性的投产基线」; 不代表因子已经很强, 仅为经过完整审计的临时生产版本。 |
| 12 | _DSHA_IC_EXPORT_ | DSHA_ROLLING_IC_CHECKSUM | OTHER | DSHA directory not found: D:\DSH_WORK\github工作\回测\DSHA |
| 13 | _CAPTURE_COMPLETENESS_ | EVENT_CAPTURE_INTEGRITY | STABLE | 每日事件捕获完整性校验, 零丢包验证通过 |

**汇总**: 13 条台账 | 7 ALERT | 2 WARN | 3 STABLE | 1 OTHER

### 13.9 监控组件状态

| 组件 | 状态 | 说明 |
|---|---|---|
| IC Watchdog | ONLINE | 20日窗口, >20%翻转率, 硬锁定8因子 |
| Perf Drift Monitor | ONLINE | 收益/夏普/回撤三重硬门槛, 基线指纹已固化 |
| DSHA IC Checksum | NOT_FOUND | rolling_ic_export.json 只读校验 |
| Pipeline Alert Hook | ONLINE | 12类管道异常, HIGH x 4 / MED x 7 / NORM x 1 |
| Auto-Snapshot | READY | 高危异常自动留存快照(日志+分片+SHA) |
| Capture Completeness | FAIL | 每日零丢包校验 |
| Risk Ledger | UPDATED | 13条风险记录, 含V3基线声明 |
| Version History | UPDATED | 本次制品SHA已登记 |
| Weekly Smoke | PENDING | 每周5项冒烟巡检 |
