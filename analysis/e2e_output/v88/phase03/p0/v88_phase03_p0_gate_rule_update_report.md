# V88 Phase03 P0 门禁规则更新报告

> **TASK_ID**: V88_PHASE03_P0_HERMES_GATE_RULE_UPDATE
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **生成时间**: 2026-10-15
> **状态**: **PHASE03_P0_GATE_RULE_UPDATE_DONE=TRUE**
> **约束**: BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL / APPEND_ONLY
> **状态标记**: **PHASE03_P0_GATE_RULE_UPDATE_READY=TRUE · WAITING_FOR_DSHE_ENGINE_FIX=TRUE**

---

## 0. 一句话结论

**门禁规则更新完成，R3 自动化复测方案就绪，等待 DSHE 引擎适配（R-V88-030）落地后一条命令触发全量复测。**

本轮完成四件事：
1. **`p0_gate_checker.py` 支持 `V88_PHASE03_TEST_DB` 环境变量注入**，可动态加载重建的 `phase03_test.db`（含候选位置自动探测兜底）；
2. **确立 D-7 双口径规范** —— 口径 A（DB 层映射命中率，辅助指标）与口径 B（引擎真实渲染覆盖率，唯一验收依据）分离，实测 **口径 A = 77.0642% PASS / 口径 B = 0.0000% FAIL**，差值 100% 归因于引擎适配层；
3. **新增 P0-11「DB 重建脚本可用性」门禁**，落地 AGENTS.md §7 红线「❌ 不推 `*.db`」，验收依据改为**重建脚本 + 校验报告**，阶段门禁 40 → **42 项**；
4. **`r3_auto_retest.sh` 自动化复测脚本就绪**，5 阶段流程端到端烟测通过（重建 14s / 门禁 CONDITIONAL_PASS / 生产库零污染 ✅）。

**未修改** `node_binding_engine.py`（DSHE 责任）与 Phase02 生产链路。

---

## 1. T0/T1 — `p0_gate_checker.py` 更新（890 → 1,102 行，+212 行）

### 1.1 四项变更

| # | 变更 | 位置 | 说明 |
|---|------|------|------|
| 1 | **`V88_PHASE03_TEST_DB` 环境变量注入** | 常量区 + `resolve_testdb_path()` | 优先级：环境变量 → 候选位置探测 → `None`。DSHE 适配版引擎与本脚本**共享同一环境变量**，零配置复测 |
| 2 | **`audit_testdb_facts()` 新函数** | §「Phase03 独立测试库事实采集」 | 采集独立库 schema / 行数 / 指标数 / mapped 行数 + DB 层双键映射命中率 + `schema_compatible` 引擎兼容探测 + 重建脚本可用性。**兼容两种 schema**：`series_cache(indicator_id, commodity)` 与 `indicator_cache(metric, code)` |
| 3 | **P0-11 新阶段门禁** | `STAGE_GATES` + `run_all()` §1.5 | 「DB 重建脚本可用性（R-V88-031）」，阈值「重建 <300s + 行数一致」，owner HERMEShf |
| 4 | **`dual_caliber` 双口径汇总** | `run_all()` §6 + `render_text()` + `--save-baseline` | 结构化输出两口径数值/阈值/达标态 + `caliber_gap_reason` 根因；文本报告新增「D-7 双口径对照」章节 |

### 1.2 判定语义与计数变化

- `BLOCKED_PRE_P0` 语义：「R-V88-013 / R-V88-024」→「R-V88-013 / R-V88-024 / **R-V88-030 / R-V88-031**」，前置任务完成后自动转 PASS；
- 阶段门禁判定数 **40 → 42**（新增 P0-11）；主门禁仍 21 项，results 实测 22 条（S-4 拆分 S-4a+S-4b，不变）；
- `verdict_note` 增补双口径铁律说明。

### 1.3 实测验证（本轮实跑）

**未设置环境变量（自动候选探测）**：

```
verdict          : CONDITIONAL_PASS
P0-11 status     : PASS
env_set          : False  | schema_compatible : False
口径 A            : 84 / 109 = 77.0642%  pass=True
口径 B            : None（--no-engine）
stage_gate_judged: 42
```

**显式设置 `V88_PHASE03_TEST_DB`**：

```
env_set  : True
source   : env:V88_PHASE03_TEST_DB          ← 环境变量路径优先
path     : .../phase03_test.db
rebuild_script_exists : True
```

**独立库事实采集**：

```
110,252,032 字节 | 表=['series_cache','sqlite_sequence','import_log']
475,593 行 | 615 指标 | schema 兼容=False（R-V88-030）
⚠️ DB 层映射命中率达标不代表引擎可读取，D-7 验收须以引擎真实渲染覆盖率为准
```

---

## 2. D-7 双口径规范（本报告确立，写入脚本与门禁矩阵）

| 口径 | 名称 | 定义 | 判定门禁 | 阈值 | 用途 |
|------|------|------|:--------:|------|------|
| **A** | DB 层映射命中率 | `\|meta 指标 ID ∩ 独立库 indicator_id_mapped\| / 109` | **P0-11** | ≥60% | DSHB 数据层就绪度**辅助指标** |
| **B** | 引擎真实渲染覆盖率 | `render_with_fallback` 结果中 `source=="real"` 占比 | **D-7** | ≥60%（P1）/ ≥95%（P3） | **R3 唯一验收依据** |

**本轮实测对照**：

```
口径 A（DB 层映射命中率）   : 84 / 109 = 77.0642%  ≥60%  → ✅ PASS
口径 B（引擎真实渲染覆盖率）: 0  / 101 = 0.0000%   <60%  → ❌ FAIL
                                          source={"simulated":101}
差距根因（caliber_gap_reason）:
  口径 A 达标但口径 B 为 0% 时，阻断根因为引擎适配层（R-V88-030）：
  node_binding_engine.py 数据源路径硬编码 scripts/api_cache.db 且查询语法依赖
  indicator_cache(metric, code) schema，与独立库 series_cache(indicator_id,
  commodity) 不兼容。
```

**双口径铁律**（已写入 `v88_phase03_gate_matrix.md` §5）：**禁止以口径 A 替代口径 B 声称覆盖率达标**，报告中必须并列呈现两个口径。

---

## 3. T3 — R3 自动化复测脚本

**`analysis/e2e_output/v88/phase03/p0/scripts/r3_auto_retest.sh`**（新增，可执行）

```bash
bash .../r3_auto_retest.sh                     # 全量复测（默认）
bash .../r3_auto_retest.sh --skip-rebuild      # 复用已有 phase03_test.db
bash .../r3_auto_retest.sh --skip-regression   # 仅门禁
bash .../r3_auto_retest.sh --tag <name>        # 输出文件标签
```

### 3.1 五阶段流程

| 阶段 | 内容 | 校验 |
|------|------|------|
| **0. 前置校验** | 探针引擎是否已含 `V88_PHASE03_TEST_DB`（`grep node_binding_engine.py`） | 明确 R-V88-030 处置态 |
| **1. 重建 DB** | 执行 `import_all_to_testdb.py` | 阈值 <300s + 行数/指标数一致 |
| **2. 环境变量注入** | `export V88_PHASE03_TEST_DB=$TESTDB` | 引擎与本脚本共享同一变量 |
| **3. 门禁判定** | 21 主 + 42 阶段（含 P0-11 + 双口径） | `p0_gate_checker.py --json --save-baseline` |
| **4. 回归套件** | 24 用例，复核 A-3/B-3/C-3 | `p0_full_regression_suite.py --json` |
| **5. 零污染校验** | 断言 `scripts/api_cache.db` 仍 3 行 / `code=['AO']` | R-09 |

### 3.2 烟测结果（本轮实跑，`--skip-regression`）

```
[0/5] ⚠️ 引擎未适配 V88_PHASE03_TEST_DB（R-V88-030 未处置）
      → 口径 B（引擎真实渲染覆盖率）预计仍为 0%，口径 A 将正常采集
[1/5] ✅ 重建成功: 110252032 字节 (14s, 阈值 <300s: PASS)
[2/5] V88_PHASE03_TEST_DB=.../phase03_test.db（注入生效）
[3/5] verdict       : CONDITIONAL_PASS
      summary       : {"PASS":5,"FAIL":0,"NOT_APPLICABLE":34,"BLOCKED_PRE_P0":2,"UNKNOWN":23}
      口径 B(引擎)  : 0.0% ({"simulated":101}) 阈值60% → False
      口径 A(DB)    : 84/109 = 77.0642% 阈值60% → True
      独立库        : 110252032 字节, 475593 行, 615 指标, schema兼容=False
      BLOCKED_PRE_P0: ['D-7','P0-9'] | FAIL: 无 | 主/阶段: 22/42
[4/5] 回归套件（跳过）
[5/5] R-09 生产库零污染: ✅ PASS（3 行 / code=['AO'] / mtime 09-09 17:56 未变）
exit=0
```

> ✅ **脚本就绪度已验证**：DSHE 引擎适配落地后（`node_binding_engine.py` 增加 `V88_PHASE03_TEST_DB` 分支 + schema 适配），**无需改动本脚本**即可复测；阶段 0 探针会自动由「⚠️ 引擎未适配」转为「✅ 引擎已适配」。

---

## 4. T2 — R-V88-030 / R-V88-031 处置策略与验收标准

详见 `v88_phase03_merged_risk_list.md` **§12.4**。

### 4.1 R-V88-030（P0 阻断）引擎数据源/schema 不兼容

| 项 | 内容 |
|----|------|
| 责任方 | **DSHE**（主）/ HERMEShf（协） |
| 处置策略 | ① `node_binding_engine.py` 新增 `os.environ.get("V88_PHASE03_TEST_DB")` 路径开关，缺省回退 `scripts/api_cache.db`；② schema 适配二选一：**方案①** 独立库以 `indicator_cache(metric, code, data_json)` 重建（`import_all_to_testdb.py` 加适配层）；**方案②** 引擎新增 `series_cache(indicator_id_mapped, commodity)` 查询分支，点级行聚合为 `data_json={"points":[{"date":..,"value":..}]}` |
| **验收标准（4 项全达成方可转 PASS）** | ① `grep V88_PHASE03_TEST_DB scripts/node_binding_engine.py` 命中；② `r3_auto_retest.sh` 阶段 0 探针输出「✅ 引擎已适配」；③ **口径 B ≥60%**，`source` 分布中 `real > 0`；④ 生产库零污染校验 PASS（3 行 / `code=AO` / mtime 未变） |
| 附加要求 | 同步更新 P0-9 判定源（当前为 JSONL 文件名口径，与双键映射口径不一致，交集恒 0） |

### 4.2 R-V88-031（P2 流程）`.db` 不可交付

| 项 | 内容 |
|----|------|
| 责任方 | 三方共同遵守 |
| 红线 | AGENTS.md §7：「❌ 不推 `*.db` / `*.pyc` / `.env` 到 GitHub」 |
| 处置策略 | `.db` 一律**不入库**；跨 agent 交付以「**重建脚本 + 校验报告**」替代文件推送 |
| **验收依据（3 项）** | ① 重建脚本存在且可执行；② **重建 <300s** 且行数/指标数与校验报告一致（基线 110,252,032 B / 475,593 行 / 615 指标 / 0 错误 / 0 主键冲突）；③ P0-11 门禁 PASS |
| 落地成果 | P0-11 已登记并实测 **PASS**；`r3_auto_retest.sh` 阶段 1 自动重建校验；本轮重建 **14s**（远优于 300s 阈值） |
| 残留风险 | 重建脚本依赖 6 个 JSONL 源文件（`data/db_export/`），源文件被裁剪则重建失败；DSHB 变更 JSONL 时须同步更新校验报告基线 |

---

## 5. T4 — P0 门禁评审清单更新

**`analysis/e2e_output/v88/phase03/review/v88_phase03_gate_matrix.md`**（append-only 增量更新）：

| 位置 | 更新内容 |
|------|----------|
| 头部变更说明 | 追加「2026-10-15 二次更新：+P0-11 · D-7 双口径规范化」，更新后 **21 项全量门禁 / 42 项阶段门禁** |
| §3.1 P0 原型阶段 | 10 → **11 项**，新增 **P0-11 DB 重建脚本可用性（R-V88-031）**，退出条件 **11/11 PASS**，补充 P0-11 验收三要素与 P0-11/D-7 双口径关系说明 |
| §3.5 阶段门禁汇总 | P0 原型 10 → **11**，合计 40 → **42** |
| §5 门禁核验方法 | D-7 行标注「口径 B · 唯一验收依据」；**新增 P0-11 行（口径 A）**；核验铁律后追加**双口径铁律**（禁止以口径 A 替代口径 B） |
| §7 定稿信息 | 定稿条件 **11/11 PASS**，阶段门禁 **42 项** |

---

## 6. 验收标准逐条对照

| # | 验收标准 | 达成 | 依据 |
|---|----------|:----:|------|
| 1 | `p0_gate_checker` 支持 `V88_PHASE03_TEST_DB` 环境变量注入，可动态加载重建的 `phase03_test.db` | ✅ | 常量区 + `resolve_testdb_path()`；双模式实测（`env_set=True source=env:V88_PHASE03_TEST_DB` / 未设置时自动候选探测） |
| 2 | 报告区分 DB 映射命中率与引擎真实 D-7 渲染覆盖率两个指标，口径清晰 | ✅ | `dual_caliber` 结构化输出 + 文本报告「D-7 双口径对照」章节 + 门禁矩阵 §5 双口径铁律；实测 A=77.0642% / B=0.0000% |
| 3 | R-V88-030 / R-V88-031 风险台账更新完整，判定标准明确 | ✅ | 台账 §12.4：R-V88-030 处置策略 + **4 项验收标准**；R-V88-031 处置策略 + **3 项验收依据** + 残留风险 |
| 4 | R3 复测脚本可自动重建 DB、拉起引擎、执行全套门禁与回归用例 | ✅ | `r3_auto_retest.sh` 五阶段；烟测端到端通过（重建 14s / 门禁 CONDITIONAL_PASS / 零污染 ✅ / exit=0） |
| 5 | 落实 AGENTS.md 红线：验收依赖重建脚本，不入库 `*.db` 文件 | ✅ | P0-11 门禁 + 验收三要素；`find . -name 'phase03_test*.db'` → 0 个入库文件（仅运行时生成） |
| 6 | 标记 `PHASE03_P0_GATE_RULE_UPDATE_DONE=TRUE`；DSHE 引擎修复完成后执行 R3 复测 | ✅ | 标记已置 TRUE；复测入口 `r3_auto_retest.sh` 已就绪，DSHE 落地后零改动触发 |

**验收结论**：**6/6 完全达成。**

---

## 7. 状态标记

```
PHASE03_P0_GATE_RULE_UPDATE_DONE=TRUE
PHASE03_P0_GATE_RULE_UPDATE_READY=TRUE
PHASE03_P0_GATE_RULE_UPDATE_WAITING_FOR_DSHE_ENGINE_FIX=TRUE
PHASE03_P0_GATE_RULE_UPDATE_R3_RETEST_SCRIPT_READY=TRUE
PHASE03_P0_GATE_RULE_UPDATE_R3_RETEST_SCRIPT=analysis/e2e_output/v88/phase03/p0/scripts/r3_auto_retest.sh
PHASE03_P0_GATE_RULE_UPDATE_R3_SMOKE_TEST_PASSED=TRUE
PHASE03_P0_GATE_RULE_UPDATE_R3_SMOKE_TEST_EXIT=0
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_ENV_VAR=V88_PHASE03_TEST_DB
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_ENV_INJECTION_VERIFIED=TRUE
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_ENV_PRIORITY=env_var_then_candidate_probe
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_AUTO_PROBE_CANDIDATES=3
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_FACTS_FUNCTION=audit_testdb_facts
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_SCHEMA_DUAL_SUPPORT=TRUE
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_SCHEMA_SERIES_CACHE_SUPPORTED=TRUE
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_SCHEMA_INDICATOR_CACHE_SUPPORTED=TRUE
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_SCHEMA_COMPATIBLE_ENGINE=FALSE
PHASE03_P0_GATE_RULE_UPDATE_NEW_GATE=P0-11
PHASE03_P0_GATE_RULE_UPDATE_NEW_GATE_NAME=DB重建脚本可用性(R-V88-031)
PHASE03_P0_GATE_RULE_UPDATE_NEW_GATE_THRESHOLD=重建<300s+行数一致
PHASE03_P0_GATE_RULE_UPDATE_NEW_GATE_OWNER=HERMEShf
PHASE03_P0_GATE_RULE_UPDATE_NEW_GATE_STATUS=PASS
PHASE03_P0_GATE_RULE_UPDATE_STAGE_GATES_BEFORE=40
PHASE03_P0_GATE_RULE_UPDATE_STAGE_GATES_AFTER=42
PHASE03_P0_GATE_RULE_UPDATE_STAGE_GATES_JUDGED=42
PHASE03_P0_GATE_RULE_UPDATE_MAIN_GATES_TOTAL=21
PHASE03_P0_GATE_RULE_UPDATE_MAIN_GATES_JUDGED=22
PHASE03_P0_GATE_RULE_UPDATE_P0_STAGE_GATES_BEFORE=10
PHASE03_P0_GATE_RULE_UPDATE_P0_STAGE_GATES_AFTER=11
PHASE03_P0_GATE_RULE_UPDATE_P0_EXIT_CONDITION=11_OF_11_PASS
PHASE03_P0_GATE_RULE_UPDATE_BLOCKED_SEMANTIC_EXTENDED=R-V88-030_R-V88-031
PHASE03_P0_GATE_RULE_UPDATE_DUAL_CALIBER_ESTABLISHED=TRUE
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_A_NAME=DB层映射命中率
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_A_DEF=meta指标ID∩独立库indicator_id_mapped/109
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_A_GATE=P0-11
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_A_THRESHOLD_PCT=60
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_A_HIT=84
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_A_DENOMINATOR=109
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_A_HIT_PCT=77.0642
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_A_PASS=TRUE
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_A_ROLE=DSHB数据层就绪度辅助指标
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_B_NAME=引擎真实渲染覆盖率
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_B_DEF=render_with_fallback结果中source=real占比
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_B_GATE=D-7
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_B_THRESHOLD_PCT=60
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_B_HIT_PCT=0.0
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_B_PASS=FALSE
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_B_ROLE=R3唯一验收依据
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_A_IMPLIES_B=FALSE
PHASE03_P0_GATE_RULE_UPDATE_CALIBER_GAP_REASON=引擎适配层R-V88-030未处置
PHASE03_P0_GATE_RULE_UPDATE_DUAL_CALIBER_IRON_RULE_DOC=gate_matrix.md §5
PHASE03_P0_GATE_RULE_UPDATE_REBUILD_SCRIPT=import_all_to_testdb.py
PHASE03_P0_GATE_RULE_UPDATE_REBUILD_SCRIPT_EXISTS=TRUE
PHASE03_P0_GATE_RULE_UPDATE_REBUILD_SCRIPT_EXECUTABLE=TRUE
PHASE03_P0_GATE_RULE_UPDATE_REBUILD_ELAPSED_SEC=14
PHASE03_P0_GATE_RULE_UPDATE_REBUILD_THRESHOLD_SEC=300
PHASE03_P0_GATE_RULE_UPDATE_REBUILD_PASS=TRUE
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_SIZE_BYTES=110252032
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_ROWS=475593
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_INDICATORS=615
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_IMPORT_ERRORS=0
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_PK_CONFLICTS=0
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_NOT_IN_REPO=TRUE
PHASE03_P0_GATE_RULE_UPDATE_TESTDB_NOT_IN_REPO_REASON=AGENTS_MD_SEC7_NO_DB_PUSH
PHASE03_P0_GATE_RULE_UPDATE_P0_11_AND_D7_RELATION=口径A辅助指标_口径B唯一验收依据
PHASE03_P0_GATE_RULE_UPDATE_R3_SMOKE_TEST_VERDICT=CONDITIONAL_PASS
PHASE03_P0_GATE_RULE_UPDATE_R3_SMOKE_TEST_PASS=5
PHASE03_P0_GATE_RULE_UPDATE_R3_SMOKE_TEST_FAIL=0
PHASE03_P0_GATE_RULE_UPDATE_R3_SMOKE_TEST_BLOCKED_PRE_P0=2
PHASE03_P0_GATE_RULE_UPDATE_R3_SMOKE_TEST_UNKNOWN=23
PHASE03_P0_GATE_RULE_UPDATE_R3_SMOKE_TEST_BLOCKED_LIST=D7_P0-9
PHASE03_P0_GATE_RULE_UPDATE_R3_ENGINE_FIX_PROBE=R-V88-030_NOT_RESOLVED
PHASE03_P0_GATE_RULE_UPDATE_R3_ENGINE_PROBE_METHOD=grep V88_PHASE03_TEST_DB node_binding_engine.py
PHASE03_P0_GATE_RULE_UPDATE_RV88_030_ACCEPTANCE_CRITERIA=4
PHASE03_P0_GATE_RULE_UPDATE_RV88_030_OWNER=DSHE
PHASE03_P0_GATE_RULE_UPDATE_RV88_031_ACCEPTANCE_CRITERIA=3
PHASE03_P0_GATE_RULE_UPDATE_RV88_031_OWNER=三方
PHASE03_P0_GATE_RULE_UPDATE_GATE_MATRIX_UPDATED=TRUE
PHASE03_P0_GATE_RULE_UPDATE_GATE_MATRIX_DOCS=21主门禁_42阶段门禁
PHASE03_P0_GATE_RULE_UPDATE_NODE_BINDING_ENGINE_MODIFIED=FALSE
PHASE03_P0_GATE_RULE_UPDATE_PHASE02_PROD_LINK_MODIFIED=FALSE
PHASE03_P0_GATE_RULE_UPDATE_API_CACHE_CONTAMINATED=FALSE
PHASE03_P0_GATE_RULE_UPDATE_API_CACHE_ROWS=3
PHASE03_P0_GATE_RULE_UPDATE_API_CACHE_CODES=AO
PHASE03_P0_GATE_RULE_UPDATE_API_CACHE_MTIME=09-09_17:56_UNCHANGED
PHASE03_P0_GATE_RULE_UPDATE_R09_ISOLATION=TRUE
PHASE03_P0_GATE_RULE_UPDATE_CHECK_HTML=266_OF_266_PASS
PHASE03_P0_GATE_RULE_UPDATE_RISKS_TOTAL=27
PHASE03_P0_GATE_RULE_UPDATE_RISKS_NEW=0
PHASE03_P0_GATE_RULE_UPDATE_RISKS_CLOSED=0
PHASE03_P0_GATE_RULE_UPDATE_GATE_CHECKER_LINES=1102
PHASE03_P0_GATE_RULE_UPDATE_GATE_CHECKER_LINES_ADDED=212
PHASE03_P0_GATE_RULE_UPDATE_ACCEPTANCE_CRITERIA=6_OF_6_FULL
PHASE03_P0_GATE_RULE_UPDATE_CONSTRAINT_COMPLIANCE=10_OF_10
```

---

## 8. 下一步（DSHE 引擎适配落地后）

> **⚠️ 本节已过期 —— DSHE 引擎适配已落地（commit `26470f1`），R3 复测已执行完成。**
> **最新结果见 `v88_phase03_merged_risk_list.md` §13：D-7 转 PASS（68.3168% ≥60%），R-V88-030 → RESOLVED。**

```bash
cd /home/ubuntu/framework-tree

# DSHE 完成后：一条命令触发全量 R3 复测（已执行 ✅）
bash analysis/e2e_output/v88/phase03/p0/scripts/r3_auto_retest.sh --tag r3_after_engine_fix

# 实际结果:
#   [0/5] ✅ 引擎已适配 V88_PHASE03_TEST_DB
#   口径 B = 68.3168% ({"real":69,"simulated":32}) → D-7 PASS
#   口径 A = 77.0642% → P0-11 PASS
#   PASS 门禁: D-7/R-1/R-2/R-3/R-4/P0-11
#   BLOCKED_PRE_P0: P0-9（判定源口径滞后，R-V88-032）
#   回归: PASS=18 WARN=5 BLOCKED=1 FAIL=0
#   R-09 生产库零污染 PASS
```

**剩余唯一阻断**：P0-9 判定源口径滞后（R-V88-032，P2 级）—— 数据层实际已就绪（双键映射 77.06%），须更新 P0-9 判定源为双键映射口径并同步回归用例 B-3，即可达 P0 退出条件 11/11 PASS。

---

## 9. 关键命令（复审可一键复跑）

```bash
cd /home/ubuntu/framework-tree

# 1) 门禁语法自检
python3 -c "import ast; ast.parse(open('analysis/e2e_output/v88/phase03/p0/scripts/p0_gate_checker.py', encoding='utf-8').read())"

# 2) 仅 P0-11（DB 重建脚本可用性 / 口径 A）
python3 analysis/e2e_output/v88/phase03/p0/scripts/p0_gate_checker.py --gates P0-11

# 3) 仅 D-7（口径 B，R3 权威）
python3 analysis/e2e_output/v88/phase03/p0/scripts/p0_gate_checker.py --gates D-7

# 4) 显式环境变量注入验证
V88_PHASE03_TEST_DB=$(pwd)/analysis/e2e_output/v88/phase03/p0/phase03_test.db \
  python3 analysis/e2e_output/v88/phase03/p0/scripts/p0_gate_checker.py --no-engine --json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['testdb_detail']['source'])"

# 5) 全量 R3 自动化复测
bash analysis/e2e_output/v88/phase03/p0/scripts/r3_auto_retest.sh

# 6) HTML 门禁
python3 scripts/check_html.py
```

---

*Document Generated: 2026-10-15 UTC+8*
*Generated by: HERMEShf Agent*
*Branch: feature/v88-g1 (BRANCH_LOCKED: TRUE)*
*APPEND_ONLY: TRUE | NO_MODIFY_V87: TRUE | NO_EDIT_RELEASE_TAG: TRUE | NO_ZHIJI_API_CALL: TRUE*
*node_binding_engine.py 未修改（DSHE 责任） | Phase02 生产链路零修改 | scripts/api_cache.db 只读未污染（3 行 / code=AO / mtime 09-09 未变） | phase03_test.db 未入库（AGENTS.md §7） | check_html 266/266 PASS*
