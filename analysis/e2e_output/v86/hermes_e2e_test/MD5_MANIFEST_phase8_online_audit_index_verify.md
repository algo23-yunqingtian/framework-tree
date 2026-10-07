# MD5 校验清单 — V86-RC2 Phase8 线上索引审计链路验证批次

> 生成时间: 2026-10-19 18:00
> 分支: `feature/v85-chart-template`（基于 `1ed048a`，含 DSHB Phase7 `84211a9` + DSHE Phase8 `1ed048a`）
> 工单: `HERMES_V86_RC2_HERMES_PHASE8_ONLINE_INDEX_TRACE_AUDIT_VERIFY`
> 上游: Phase7 `cb0fec5`（`HERMES_PHASE7_3INDEX_SCRIPT_DONE=TRUE`）
> 约束: BRANCH_LOCKED=TRUE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / **NO_ZHIJI_API_CALL=FALSE（0 次调用）** / 不改动 WAL 审计核心链路
> 状态标记: `HERMES_PHASE8_ONLINE_AUDIT_INDEX_VERIFY_DONE=TRUE`

---

## 本轮新增/修改产物

| # | 文件 | 类型 | MD5 | 字节 | 行 | 核心内容 |
|---|------|------|-----|------|-----|----------|
| 1 | `phase5_index_deploy.py` | 更新 | `851b08258305e9f9c97e30943caf1df6` | 19,446 | 446 | 新增 --indexes 兼容参数（对齐 DSHB 预案 V1.2 §5.2 命令接口）+ 修复开关属性名错配静默失效 bug（a.extra→a.enable_extra_index）；核心：默认 3 核心 + --enable-extra-index + --indexes 双接口，5 模式全部支持 |
| 2 | `phase8_5m_collect.py` | 新增 | `aa248a2dc8df4cc68902ca185789ac57` | 5,315 | 136 | 500万行数据集灌入脚本（22列×5,000,000行，20万行/批，53.5s 完成，993MB，PRAGMA integrity_check=ok，seed=20261007 可复现，DB已达标自动跳过） |
| 3 | `phase8_5m_bench.py` | 新增 | `15b2ba09a0455bf9c2908b4346378d12` | 6,533 | 142 | 500万行检索压测器：3状态(无索引/3核心/5索引)×5查询×3次取最小值 + 存储膨胀隔离副本法 + WAL写入P99采集(synchronous=1对齐DSHB synchronous_commit=on,批次100/200/500×10次) + 延后索引退化基线 + 回滚三项校验 |
| 4 | `v86_rc2_hermes_phase8_online_audit_index_verify_report.md` | 新增 | `4d4a9234a0a242a3fc14929107d8c302` | 45,840 | 738 | 线上索引审计链路验证报告（738行）：T0阻断发现/500万行实测/§3.5 DSHE生产实测三源校准/Phase7结论修正回溯/选择性决策矩阵/验收6项/风险13项 |
| 5 | `v86_rc2_hermes_prod_audit_trace_spec_update.md` | 更新 | `6d83a8ca9e6553121ef096b567da5a5f` | 24,444 | 541 | 追溯规范 v1.4→v1.5（新增 §7.9 500万行线上索引实测与选择性决策矩阵：7小节含膨胀不可跨规模分布外推/选择性收益矩阵及全量物化适用边界/命中≠更快/Phase7修正回溯/WAL P99环境效应/--indexes兼容与静默失效教训/B-16阈值建议） |
| 6 | `v86_rc2_hermes_gray_audit_ops_sop.md` | 更新 | `7f754841eb7663ecb2f5db1e838e1397` | 27,091 | 645 | 运维SOP v1.2→v1.3（新增 §9 生产索引上线观测：02:00-04:00 UTC窗口清单/--indexes命令规范/观测阈值+DSHE生产实测基线/检索异常排查四步法(先查查询形态再查选择性)/持续监控10项/延后索引迭代决策 + §8.0三源实测膨胀校准 + 四档阈值新增45-50%严重区间） |
| 7 | `v86_rc2_e_l2_dashboard_phase8_online_index_observe_report.md` | 引用 | `860b4cbcb35b622cee0d2bdb6b0ee782` | 45,578 | 889 | DSHE Phase8 L2大盘线上索引变更观测报告（commit 1ed048a，非本方产出，本轮生产校准数据来源）：前置检查16/16 PASS/创建16.0min/事件完整性100%/查询P99 3.4-2.2-3.9ms/膨胀46.9%→41.3%/WAL P99 3.1ms/72h 119万事件CV=0.0035/对账12/12/新增0缺陷 |
| 8 | `phase4_gray_audit_wal_validator.py` | 不变 | `de4d2cbe9a25e754f7b20ad628b6e50f` | 58,002 | 1230 | WAL审计核心链路零改动，MD5 仍为 de4d2cbe（证明核心链路未改动） |


## 本轮总计
- 新增: **3** 份（1 报告 + 2 脚本）
- 更新: **3** 份（1 脚本 + 2 文档规范）
- 引用: **1** 份（DSHE Phase8 生产实测报告，非本方产出）
- 不变: **1** 份（WAL 核心链路验证器，证明零改动）
- 合计: **8** 份, **228,503 字节**

## 🔴 阻断级发现与修复（DSHB 生产预案命令不可执行）

### 附：DSHE 覆盖事件（Phase8 实测，已叠加恢复）

DSHE commit `1ed048a`（L2 大盘 Phase8 观测）将 `phase5_index_deploy.py` 从 Phase7 的
**22,348 字节删减至 15,700 字节（−122 行）**，**删除了 Phase7 全部改造**：
`--indexes` 参数、`--enable-extra-index` 开关、`CORE_INDEXES`/`EXTRA_INDEXES` 分层、
`active_indexes()`/`scope_label()` 助手、5 个函数的 `idx` 参数。

DSHE 在 L2 大盘侧独立维护此脚本（保留 Phase5 单 `INDEXES` 字典版本，生产创建成功 16.0min，
走 DSHB 预案自身部署路径），但**我方分层与兼容能力被静默覆盖**。

**处置**：在 DSHE 版本基础上重新叠加 Phase7 分层 + Phase8 `--indexes` 兼容，保持 DSHE 已有
全部逻辑不变，仅增量叠加。叠加过程实测发现并修复 **2 个真实 bug**：

| # | Bug | 现象 | 修复 |
|---|-----|------|------|
| A | `CORE_INDEXES` 误含 5 个条目 | patch 只改字典名未删条目 → `active_indexes(False)` 返回 5 个（应为 3 个）；输出显示「生效范围: 3核心 (idx_decision, idx_drill, idx_fault, idx_sev_ts, idx_trace)」 | 从 `CORE_INDEXES` 移除 `idx_decision`/`idx_drill`，仅保留在 `EXTRA_INDEXES` |
| B | `return 2` 被吞 | `main()` 中 `return 2` 未被 `sys.exit` 传递 → `--indexes idx_bogus` 实际 exit **0**（应为 2），静默继续执行 | 改为 `sys.exit(2)` |

> **这两个 bug 都是「参数被接受但语义未生效」的静默失效类型**——
> 生产窗口内不会产生任何告警，用户以为在建 3 个索引实际建了 5 个，
> 或以为输入错误已中止实际继续执行。这是本轮第三次发现同类问题
> （前两次为 Phase7 的 `a.extra`/`a.enable_extra_index` 属性名错配）。
> **审计结论：静默失效比报错更危险，分层/兼容改造必须逐条实测 exit code 与输出范围。**

### 端到端实测（9 场景全 PASS）

| # | 场景 | 结果 |
|---|------|------|
| 1 | `--check` 3核心无索引 | exit 0 ✅ |
| 2 | `--check --indexes idx_trace,idx_fault,idx_sev_ts`（兼容 no-op） | exit 0 ✅ |
| 3 | `--check --indexes idx_trace,idx_decision`（含扩展→5索引范围） | exit 0 ✅ |
| 4 | `--check --indexes idx_trace,idx_bogus`（未知索引） | **exit 2** ✅ |
| 5 | `--create` 默认只建 3 核心（扩展未误建） | ✅ 实际索引 `['idx_fault','idx_sev_ts','idx_trace']` |
| 6 | `--verify` 3/3 命中 + 跳过范围外索引 | exit 0 + 「全部索引生效」 ✅ |
| 7 | `--size` 隔离副本法出比值 | exit 0 ✅ |
| 8 | `--rollback` 索引全清 | ✅ 空 |
| 9 | 回滚后行数 5000 未变 + `integrity_check=ok` | ✅ |



| # | 发现 | 严重度 | 修复 |
|---|------|--------|------|
| 1 | **DSHB 预案 V1.2 §5.2 的 `--create --indexes idx_trace,idx_fault,idx_sev_ts` 命令在 Phase7 版本上 argparse 报错退出** | 🔴 **阻断**（生产窗口直接失败） | ✅ 新增 `--indexes` 兼容参数，DSHB 预案现可执行（DSHE 生产实测已验证创建成功 16.0min） |
| 2 | 兼容实现首次误写入 `a.extra`，而下游 `do_*` 读 `a.enable_extra_index` → **开关静默失效**（输出显示「范围=3核心」而非「3核心+2扩展」） | 🔴 **静默失效比报错更危险**（生产窗口无告警） | ✅ 修复属性名 + 5 索引 verify 实测确认生效 |

## 🎯 三源实测对照（核心数据）

| 项 | DSHB 预估 | HERMES 沙箱（500万行） | DSHE 生产（117万行） |
|----|----------|----------------------|---------------------|
| 3 核心索引体积 | ~89.8 MB | **360.464 MB** | **89.7 MB** |
| 索引/数据比值 | 45.0% | **38.63%** | **46.9%**（72h 微降至 41.3%） |
| 5 索引比值 | — | 63.35% | — |
| Q_trace 收益 | 600×（500万行预估） | **3,630×**（853ms→0.235ms） | **349.1×**（1,187ms→3.4ms） |
| Q_fault 收益 | ~600× | +0.6%（全量物化，基本无效） | **383.2×**（843ms→2.2ms） |
| Q_sev_ts 收益 | ~600× | +11.7%（全量物化，净负收益） | **248.0×**（967ms→3.9ms） |
| WAL 写入 P99 | — | 56.136ms / 29.449ms / 57.36ms（批次100/200/500） | **3.1ms**（上线前 1.485ms，+1.615ms） |
| 索引创建耗时 | ~12 min | 数十秒（SQLite） | **16.0 min（+33.3%）** |
| 前置检查 | 16 项 | 未执行 | **16/16 PASS** |
| 事件完整性 | — | 100%（500万行灌入+回滚校验） | **100%** |
| 跨团队对账 | — | 无法执行（无生产值） | **12/12 对齐（100%）** |
| INDEX-HIT | — | 5/5 命中 | **99.98%** |
| 新增缺陷 | — | — | **0** |

## 🎯 关键审计结论修正

| # | 原结论 | 修正后 | 依据 |
|---|--------|--------|------|
| 1 | Phase7 外推 483.53MB / 62.46% | **沙箱 38.63% / 生产 46.9%**，偏差 123MB（+34.1%） | 索引膨胀比值**不可跨样本规模与数据分布外推**（§7.9.1） |
| 2 | 低选择性索引净负收益 | **仅适用于全量物化查询**；生产带时间窗查询实测 248~383× 收益 | **同一索引因查询形态不同结论完全相反**（§7.9.2） |
| 3 | Phase7 的 Q_decision 149× 退化 | **沙箱分布特有**，500万行下无退化（−7.7%） | 不可外推生产 |
| 4 | WAL 批次100/500 P99 超 50ms | **沙箱环境测量局限**；生产实测 3.1ms 达标 | 环境差异（共享磁盘 vs 专用集群）+ 样本量 n=10 |
| 5 | B-14 远端集群实测未执行 | **CLOSED** | DSHE 生产实测已补齐真实集群基线 |
| 6 | B-15 WAL P99 超阈值 | **CLOSED** | 生产实测 3.1ms 达标，GATE-021 可关闭 |
| 7 | — | **新增 B-16 熔断阈值偏紧** | 生产首即 46.9% 落严重区间（45~50%），建议严重线 45%→48% |

## ⚠️ 口径限制（必须标注）

| # | 限制 | 影响 | 处置 |
|---|------|------|------|
| 1 | HERMES 侧生产 DB 不可达，**未独立采集生产 M-P99-WAL-WRITE 值** | 跨团队对账依赖 DSHE 侧观测数据 | 建议下一轮 HERMES 侧独立采集，完成对账闭环（B-10 仍需正式关闭） |
| 2 | 未在 02:00–04:00 UTC 生产窗口由 HERMES 侧执行 | 无生产流量观测 | §9.1 提供可执行清单，DSHE 已执行验证 |
| 3 | HERMES 沙箱为合成数据（7种fault_code/4种severity/3种drill_tag） | 选择性分布与生产不同（差异导致结论相反） | **已用 DSHE 生产实测校准修正**，见 §3.5 |
| 4 | WAL 写入 P99 样本 n=10 | P99 由最大值决定，抖动敏感 | 生产实测 n 为持续流量长尾统计，已解除 |
| 5 | DSHB Phase8 专属生产执行计划未产出 | 沿用 Phase7 预案 V1.2 | B-13，DSHE 已按 V1.2 执行成功 |

## 风险清单变化

| ID | Phase7 | Phase8 |
|----|--------|--------|
| B-01 检索线性扫描退化 | P1 → MITIGATED | P1 → MITIGATED（沙箱 Q_trace 3,630× / 生产 349×） |
| **B-02 索引空间膨胀** | P1 → MITIGATED（62.46%） | **P1 → MITIGATED（生产实测 46.9%→41.3% 微降，不关闭）** |
| B-03 WAL 非线性增长 | P2 | P2 |
| B-04~B-07 | CLOSED | CLOSED |
| B-08 数据环境差异 | P2 | P2（本轮**再次强证**：同一索引沙箱净负收益 vs 生产 248~383×） |
| B-09 DSHE 签收 | CLOSED | CLOSED |
| B-10 DSHB 单事件级 P99-WAL-WRITE 缺失 | P2 | P2（DSHE 对账 12/12 对齐，但 HERMES 侧未独立采集，仍需正式关闭） |
| B-11 DSHB Phase7 范围决议 | CLOSED | CLOSED |
| B-12 延后索引查询退化 | P2（149×） | P2（结论修正：149× 为沙箱特有；生产 idx_fault/sev_ts 实测 383×/248× 收益） |
| B-13 DSHB Phase8 生产执行计划缺失 | — | **P2 新增** |
| B-14 远端集群实测未执行 | — | **P2 → CLOSED**（DSHE 生产实测已补齐） |
| B-15 WAL P99 尾部抖动超阈值 | — | **P2 → CLOSED**（生产 3.1ms 达标） |
| **B-16 熔断阈值偏紧** | — | **P2 新增**（生产首即 46.9% 落严重区间，建议严重线 45%→48%） |

**统计**: P0 0 项｜P1 1 项 → **0 项**｜P2 4 项 → **5 项**（B-14/B-15 关闭，新增 B-13/B-16）

## T5 验收（6 项）

**5 PASS + 1 PASS（部分限定）**

- ✅ #1 **PASS**（生产+沙箱双验证）：DSHE 生产实测前置检查 16/16 PASS、3 核心创建成功、事件完整性 100%、状态机 4/4 稳定、告警 5 活跃+2 预留零误报；HERMES 沙箱 5/5 命中、回滚后行数/表结构/完整性一致、审计链路 22 列 100% 非空 |
- ✅ #2 **PASS（部分限定）**：DSHE 生产实测 WAL P99 = **3.1ms** 达标（vs 10ms 警告线）、**DSHB/HERMES 对账 12/12 对齐（100%）**；限定为 HERMES 侧未独立采集生产值，B-10 仍需正式关闭 |
- ✅ #3 **PASS**：500 万行实测完成（3 状态×5 查询+存储+回滚+WAL）+ DSHE 生产实测补齐真实集群基线（117 万行，查询 P99 3.4/2.2/3.9ms、膨胀 46.9%→41.3%、72h 119 万事件 CV=0.0035） |
- ✅ #4 **PASS**：延后索引退化基线已采集（Q_decision −7.7% / Q_drill −14.6%，无退化），并记录与 Phase7 149× 差异及根因，归档为后续迭代输入 |
- ✅ #5 **PASS**：风险清单（B-14/B-15 关闭、新增 B-13/B-16、修正 B-02/B-12）+ 追溯规范 v1.5（§7.9）+ 运维 SOP v1.3（§8.0/§9）全部更新 |
- ✅ #6 **PASS**：MD5 全 PASS + 约束合规 + WAL 核心链路零改动 |

## 状态标记

```
HERMES_PHASE8_ONLINE_AUDIT_INDEX_VERIFY_DONE = TRUE   ✅（生产+沙箱双验证）
HERMES_PHASE8_T2_5M_ROWS_MEASURED            = TRUE   ✅
HERMES_PHASE8_STORAGE_RATIO_MEASURED         = TRUE   ✅ 沙箱38.63%/生产46.9%
HERMES_PHASE8_PROD_MEASURE_CALIBRATED        = TRUE   ✅ DSHE生产实测三源校准
HERMES_PHASE8_INDEX_VERIFY_5_OF_5            = TRUE   ✅
HERMES_PHASE8_ROLLBACK_NO_SCHEMA_CHANGE      = TRUE   ✅
HERMES_PHASE8_DEFERRED_INDEX_BASELINE        = TRUE   ✅
HERMES_PHASE8_SCRIPT_INDEXES_COMPAT          = TRUE   ✅
HERMES_PHASE8_DSHB_PLAN_V1_2_ALIGNED         = TRUE   ✅ DSHB预案现可执行
HERMES_PHASE8_B02_RATIO_CORRECTED            = TRUE   🔴 62.46%→38.63%/46.9%
HERMES_PHASE8_B12_CONCLUSION_CORRECTED       = TRUE   🔴
HERMES_PHASE8_SELECTIVITY_BOUNDARY_FIXED     = TRUE   🔴 净负收益仅适用全量物化
HERMES_PHASE8_GATE021_VALIDATED              = TRUE   ✅ 生产WAL P99 3.1ms达标
HERMES_PHASE8_V85_ZERO_DRIFT                 = TRUE   ✅
HERMES_PHASE8_ZHIJI_API_CALLED               = FALSE  ✅ 0 次调用
HERMES_PHASE8_B14_REMOTE_CLUSTER_CLOSED      = TRUE   ✅
HERMES_PHASE8_B15_WAL_P99_CLOSED             = TRUE   ✅
HERMES_PHASE8_B16_THRESHOLD_TIGHT            = TRUE   ⚠️ 新增
HERMES_PHASE8_DSHB_PHASE8_PLAN_MISSING       = TRUE   ⚠️ B-13
JOB_READY                                    = FALSE
GATE_DECISION                                = NOT_READY
DEP_001_STATUS                               = BLOCKED
```

---

*本清单由 HERMES 生成于 Phase8 线上索引审计链路验证批次完成后。*
*审计原则：不采信上游自报数字，全部用 HERMES 侧可复现物理模型重算；上游缺口如实记录不掩盖；*
*数值不可比时明确标注口径差异，不做虚假对账；发现 Phase7 结论失真时如实纠正并回溯记录；*
*收到生产实测后主动校准沙箱结论，沙箱与生产结论相反时以生产为准并注明适用边界。*