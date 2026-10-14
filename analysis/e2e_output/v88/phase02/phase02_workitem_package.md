# V88 Phase02 工单包

> **生成时间**: 2026-10-14 20:32
> **生成Agent**: HERMEShf (V88_PHASE02_INIT_PLAN_PREP)
> **上游基线**: phase02_master_plan.md
> **用途**: 下发给 DSHB / DSHE / HERMEShf 三方执行
> **状态**: PHASE02_READY，等待正式下发

---

## 1. 通用约束（三方共享）

```
BRANCH_LOCKED: feature/v88-g1
NO_OVERWRITE: TRUE (append-only)
NO_MODIFY_V87: TRUE (MD5 0bcd94a8 / a0030737)
NO_EDIT_RELEASE_TAG: TRUE (26d58a8)
NO_ZHIJI_API_CALL: TRUE (Phase02 全程零调用)
CPU_FUSE_THRESHOLD: 2.0% (不变)
文件锁: python3 ~/.hermes/scripts/file_write_lock.py acquire/release
STATUS.md 回传: 改产物必写 STATUS.md（pre-commit 强制）
```

---

## 2. DSHB Phase02 业务工单

> **TASK_ID**: V88_PHASE02_DSHB_DATA_SUPPLY
> **AGENT**: DSHB
> **目标**: 全量指标持续供给 + 数据质量保障

### 任务清单

| # | 任务 | 说明 |
|---|---|---|
| D1 | 全量指标持续供给 | 146 指标（123 matched + 24 partial）持续入库，采集成功率 ≥95% |
| D2 | 数据质量巡检 | 每日 DQA 巡检，DQA ERROR=0，产出 DQA 日报 |
| D3 | 6 个 pending 指标备选参考数据输出 | 9 组 Y 级备选方案（见 pending_index_simulation.py），按参考口径输出替代序列 |
| D4 | 长稳压测数据源供给 | 7 天观测期内保障数据源稳定性 |
| D5 | 数据侧性能监控 | 采集 P50/P99 延迟、入库延迟，延迟 ≤T+1d |

### 交付物

| 交付物 | 路径 | 格式 |
|---|---|---|
| D1 数据入库记录 | analysis/e2e_output/v88/phase02/dshb/data_ingestion_log.md | MD |
| D2 DQA 日报 | analysis/e2e_output/v88/phase02/dshb/dqa_daily_report.md | MD |
| D3 备选参考数据 | analysis/e2e_output/v88/phase02/dshb/pending_reference_output.md | MD |
| D5 性能周报 | analysis/e2e_output/v88/phase02/dshb/performance_weekly.md | MD |

### 门禁

- 采集成功率 ≥95%
- DQA ERROR = 0
- 入库延迟 ≤T+1d
- P50/P99 持续记录

### 排期

- 3 天内启动数据供给（与 P2-A 同步）
- 7 天长稳观测期持续供给
- 验收时提交 D1-D5 全部交付物

---

## 3. DSHE Phase02 业务工单

> **TASK_ID**: V88_PHASE02_DSHE_RENDER_DEPLOY
> **AGENT**: DSHE
> **目标**: 88 张图表全量上线 + 渲染性能保障

### 任务清单

| # | 任务 | 说明 |
|---|---|---|
| E1 | 88 张图表合并上线部署 | 将 Phase01 已交付的 101 图表（88 周报子集+13 扩展）合并入生产渲染链路 |
| E2 | fallback 降级渲染全量回归验证 | 16 张 pending 图表降级链路（real→simulated→placeholder）全量回归 |
| E3 | 并发查询压力测试 | 并发查询 P99 加载时延 <500ms，报错率=0 |
| E4 | 前端监控大盘部署 | 渲染性能监控面板，包含 P50/P99/报错率/降级触发次数 |
| E5 | 渲染性能指标采集 | 持续采集渲染性能指标，写入性能指标库 |

### 交付物

| 交付物 | 路径 | 格式 |
|---|---|---|
| E1 上线部署记录 | analysis/e2e_output/v88/phase02/dshe/deployment_record.md | MD |
| E2 fallback 回归报告 | analysis/e2e_output/v88/phase02/dshe/fallback_regression_report.md | MD |
| E3 并发压测报告 | analysis/e2e_output/v88/phase02/dshe/concurrency_stress_test.md | MD |
| E4 监控大盘 | analysis/e2e_output/v88/phase02/dshe/monitor_dashboard_url.txt | TXT |
| E5 渲染性能库 | analysis/e2e_output/v88/phase02/dshe/render_perf_metrics.json | JSON |

### 门禁

- P99 加载时延 <500ms
- 并发查询报错率 = 0
- fallback 降级链路生效且无 ERROR
- 88 图表全部可访问

### 排期

- 3 天部署 + 2 天压测（P2-A + P2-B 并行窗口）
- 7 天长稳观测期持续监控
- 验收时提交 E1-E5 全部交付物

---

## 4. HERMEShf Phase02 持续监控工单

> **TASK_ID**: V88_PHASE02_HERMESHF_CONTINUOUS_AUDIT
> **AGENT**: HERMEShf
> **目标**: 全链路持续审计 + IC/IR 漂移核验 + 最终验收

### 任务清单

| # | 任务 | 说明 |
|---|---|---|
| H1 | 全链路持续审计 | DSHB/DSHE 提交独立核验，审计快照 v5+ |
| H2 | 长稳稳定性监控 | 7 天观测期 0 P0/P1 判定，稳定观测日志 |
| H3 | IC/IR 漂移自动核验 | 每日采集 IC/IR，与历史阈值比对，超阈值触发告警 |
| H4 | 阶段性快照产出 | 每周/里程碑产出审计快照 |
| H5 | Phase02 最终验收复核 | 门禁矩阵全维度复核，输出 Phase02_ACCEPT 判定 |

### 交付物

| 交付物 | 路径 | 格式 |
|---|---|---|
| H1-H4 审计日志 | analysis/e2e_output/v88/phase02/audit/v88_phase02_audit_log.md | MD |
| H3 漂移核验 | analysis/e2e_output/v88/phase02/audit/ic_ir_drift_log.md | MD |
| H5 验收报告 | analysis/e2e_output/v88/phase02/audit/phase02_acceptance_report.md | MD |
| MD5 清单 | analysis/e2e_output/v88/phase02/audit/MD5_MANIFEST.md | MD |

### 门禁

- 7 天长稳观测 0 P0/P1
- 每日 IC/IR 完整采集
- 门禁矩阵全维度通过
- CPU 熔断阈值维持 2.0% 不变
- V87 基线 + Release Tag 全程不变

### 排期

- 与 DSHB/DSHE 同步启动
- 7 天长稳观测期全程运行
- 观测期结束后 2 天内完成验收复核

---

## 5. 交付物目录结构

```
analysis/e2e_output/v88/phase02/
├── phase02_master_plan.md              # 顶层规划（本文档上游）
├── phase02_workitem_package.md         # 本工单包
├── dshb/
│   ├── data_ingestion_log.md           # D1 数据入库记录
│   ├── dqa_daily_report.md             # D2 DQA 日报
│   ├── pending_reference_output.md     # D3 备选参考数据
│   └── performance_weekly.md           # D5 性能周报
├── dshe/
│   ├── deployment_record.md            # E1 上线部署记录
│   ├── fallback_regression_report.md   # E2 fallback 回归报告
│   ├── concurrency_stress_test.md      # E3 并发压测报告
│   ├── monitor_dashboard_url.txt       # E4 监控大盘
│   └── render_perf_metrics.json        # E5 渲染性能库
└── audit/
    ├── v88_phase02_audit_log.md        # H1-H4 审计日志
    ├── ic_ir_drift_log.md              # H3 漂移核验
    ├── phase02_acceptance_report.md    # H5 验收报告
    └── MD5_MANIFEST.md                 # MD5 清单
```

> 注：上述子目录及交付物文件由 DSHB/DSHE/HERMEShf 各自创建，本工单包仅定义路径与格式要求。

---

## 6. 状态标记

- **PHASE02_READY**: TRUE
- **PHASE02_DEPLOY**: 等待正式下发
- **DSHB_PENDING_START**: TRUE（等待工单下发）
- **DSHE_PENDING_START**: TRUE（等待工单下发）
- **HERMEShf_PENDING_START**: TRUE（等待工单下发）
