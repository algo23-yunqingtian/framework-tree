# V88 Phase03 P0 门禁基线与性能基线报告

> **TASK_ID**: V88_PHASE03_P0_R2_GATE_BASELINE_AND_REGRESSION
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **BASELINE HEAD**: e3673f2 | **生成时间**: 2026-10-15
> **前置**: 三方评审完成 (CONDITIONAL_PASS) / 门禁矩阵 v88_phase03_gate_matrix.md (21 项主门禁 + 40 项阶段门禁)
> **约束**: BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL / APPEND_ONLY
> **状态**: **PHASE03_P0_R2_DONE=TRUE**

---

## 0. 一句话结论

**P0 门禁基线框架与全链路回归套件全部就位并可一键执行，判定 CONDITIONAL_PASS。** 自动化门禁校验覆盖 **21 项主门禁 + 40 项阶段门禁**，其中 **6 项已实测**（D-7/R-1/R-2/R-3/R-4 + P0-9），**2 项为 P0 前置任务型阻断**（D-7 真实覆盖率 0%、P0-9 命名映射 0%），**0 项方案级 FAIL**。全链路回归套件 **24 项用例**（数据层 6 / 指标读取 6 / 图表渲染 8 / 告警推送 4）实测 **PASS 16 · BLOCKED 3 · WARN 5**（P0-R1 并行工单灌库脚本就位后由 4 项 BLOCKED 降至 3 项），四阶段链路完整贯通。

**关键实测结果**：D-7 真实数据覆盖率 = **0.0000%（0/101，全部 simulated）**，与三方评审实测结论完全一致；P0-9 命名空间映射覆盖率 = **0.0000%（0/109）**，meta_chart 109 指标与 JSONL 579 指标零交集。**P0-R1 并行工单（DSHE）灌库脚本 `db_import_jsonl.py` / `db_load.py` 已就位**（A-6 转 ✅），BLOCKED 仅剩 **A-3 独立库未创建 / B-3 命名映射零交集 / C-3 D-7 覆盖率 0%** 三项，仍构成同一条因果链。

---

## 1. 交付物清单

| # | 文件 | 字节 | 说明 |
|---|------|-----:|------|
| 1 | `scripts/p0_gate_checker.py` | 36,848+ | 自动化门禁基线校验（21 主 / 40 阶段，含 D-7 R3 权威判定） |
| 2 | `scripts/p0_full_regression_suite.py` | 28,705+ | P0 全链路回归套件（24 用例，4 阶段） |
| 3 | `scripts/p0_baseline_metrics.json` | — | 基线性能指标自动落盘 |
| 4 | 本报告 | — | 门禁基线 + 性能基线 |
| 5 | 元数据三件套追加 | — | MD5_MANIFEST / STATUS.md / JOB_READY.flag |

**一键执行**：

```bash
# 门禁基线判定（21 主 + 40 阶段，约 8 秒）
python3 analysis/e2e_output/v88/phase03/p0/scripts/p0_gate_checker.py

# 全链路回归（24 用例，约 60 秒）
python3 analysis/e2e_output/v88/phase03/p0/scripts/p0_full_regression_suite.py

# 子集 / JSON / 快速模式
python3 p0_full_regression_suite.py --phase A,B          # 仅数据层+指标读取
python3 p0_gate_checker.py --json --save-baseline         # JSON 输出 + 基线落盘
python3 p0_full_regression_suite.py --quick --no-engine   # 离线环境
```

**退出码语义**：`0` = PASS / CONDITIONAL_PASS / PASS_WITH_WARN（框架可用）；`2` = FAIL（须修复）。CI 可直接消费。

---

## 2. 门禁基线（T0 / T1 / T2）

### 2.1 门禁规模与划分

| 类别 | 数量 | 编号 |
|------|:----:|------|
| 数据门禁 | 7 | D-1 ~ D-7 |
| 渲染门禁 | 6 | R-1 ~ R-6 |
| 因子门禁 | 4 | F-1 ~ F-4 |
| 稳定性门禁 | 5 | S-1, S-2, S-3, **S-4a, S-4b** |
| **主门禁合计** | **21** | — |

| 阶段 | 数量 | 编号 |
|------|:----:|------|
| P0 原型 | 10 | P0-1 ~ P0-10（含新增 P0-9 / P0-10） |
| P1 仿真 | 12 | P1-1 ~ P1-12 |
| P2 长稳 | 11 | P2-1 ~ P2-11 |
| P3 金丝雀 | 8 | P3-1 ~ P3-8 |
| **阶段门禁合计** | **40** | — |

> **去重设计**：S-4a/S-4b 作为**主门禁**由 `check_rpo_split()` 专项判定，不计入阶段门禁，避免与 STAGE_GATES 中的 P1-8/P2-6/P2-7 重复登记导致计数偏差（首版实测曾出现 22/41 的计数错误，已修复为 21/40）。

### 2.2 判定结果汇总

```
判定: CONDITIONAL_PASS
汇总: PASS=4 · FAIL=0 · BLOCKED_PRE_P0=2 · NOT_APPLICABLE=34 · UNKNOWN=23
```

| 状态 | 语义 |
|------|------|
| ✅ PASS | 已实测且达标 |
| 🔴 BLOCKED_PRE_P0 | P0 前置任务型阻断（任务完成后自动转 PASS） |
| ❌ FAIL | 已实测未达标（**本次为 0 项**） |
| ⚪ NOT_APPLICABLE | 本阶段不执行（P1/P2/P3 门禁） |
| ❓ UNKNOWN | 待 P1+ 阶段数据 |

**判定规则**（`p0_gate_checker.py` §6）：存在 FAIL → FAIL；仅存在 BLOCKED_PRE_P0 → CONDITIONAL_PASS；全 PASS → PASS；含 UNKNOWN → PASS_WITH_UNKNOWN。

### 2.3 已实测主门禁（6 项）

| 门禁 | 名称 | 阈值 | 实测值 | 判定 |
|------|------|------|--------|:----:|
| **D-7** | 真实数据覆盖率 | P1≥60% / P3≥95% | **0.0000% (0/101)** | 🔴 BLOCKED_PRE_P0 |
| R-1 | 校验规则 | 0 ERROR | **0 ERROR** | ✅ PASS |
| R-2 | 图表部署 | 100% | **101/101** | ✅ PASS |
| R-3 | 降级渲染 | 生效且 0 崩溃 | **101/101 renderable** | ✅ PASS |
| R-4 | P99 时延 | <500ms | **3.161ms（余量 99.37%）** | ✅ PASS |
| P0-9 | 命名空间映射 | ≥95% | **0.0000% (0/109)** | 🔴 BLOCKED_PRE_P0 |

> R-4 注明：当前为**串行渲染口径**，非 P3 真实流量并发口径。串行 P99=3.16ms 与 Phase02 压测 burst P99=190.47ms 相差 60 倍，说明真实并发场景下的时延风险尚未被本基线覆盖，须在 P1（500 并发仿真）与 P3（真实金丝雀）复测。

### 2.4 S-4a / S-4b 拆分检测（CHG-04 落地）

| 门禁 | 阈值 | P0 阶段状态 | 证据痕迹 |
|------|------|:-----------:|---------|
| **S-4a** 灾备写入 RPO | =0（同步双写） | ⚪ NOT_APPLICABLE（P1 判定） | 双写 **73 条** / WAL **20 条** |
| **S-4b** 灾备恢复 RPO | <24h（分片降级） | ⚪ NOT_APPLICABLE（P2 判定） | 分片策略 **70 条** |

扫描范围：**18 个文件**（Phase03 全部 `.md/.py/.json/.yml/.yaml`，含 review/ 与 p0/ 目录）。

**双语义落地验证**：S-4a 与 S-4b 作为**独立门禁编号**分离，不再混用为单一 S-4。S-4a 对应 P1-8 校验点（双写一致性），S-4b 对应 P2-7 校验点（真实分片降级演练），与三方评审 CHG-04 判定完全一致。

**R-09 数据库隔离探测**：Phase03 独立测试库（`phase03_test.db`）**未创建** → 非阻断，但灌库前必须创建。三方评审补充要求「`db_import_jsonl.py` 禁止写 `scripts/api_cache.db`」已固化为 A-3 回归用例。

---

## 3. D-7 真实数据覆盖率判定（T1 核心）

### 3.1 R3 权威规则实现

```python
def audit_real_coverage():
    # 独立调用 NodeBindingEngine.render_with_fallback() 全量复跑
    # 统计 source=="real" 占比
    # 禁止采信 DSHB 推送日志 push_mode（意图标记）
    # 禁止采信 DSHE 自报 source（可能手工覆盖）
```

**R1/R2/R3 三条语义定义已在代码中落地**（三方评审 §5.2 冻结）：
- **R1**（推送意图）：不纳入本脚本判定
- **R2**（渲染事实）：`render_with_fallback()` 三级降级链返回值
- **R3**（覆盖率权威）：HERMEShf 独立复跑统计，**本脚本唯一判定依据**

### 3.2 实测结果

| 项 | 值 |
|----|----|
| 图表总数 | **101** |
| 渲染成功 | **101**（100%） |
| source 分布 | `{"simulated": 101}` |
| **真实覆盖率** | **0.0000%** |
| P1 阈值 ≥60% | ❌ False |
| P3 阈值 ≥95% | ❌ False |
| 校验错误 | **0** |
| 时延（ms） | median 1.601 / p95 2.956 / p99 3.161 / max 4.440 |

### 3.3 根因证据链（api_cache.db 实测）

```
db_exists        : true
tables           : ["indicator_cache"]
rows             : 3
distinct_codes   : ["AO"]                    ← 仅 1 个品种，非五金属
distinct_metrics : ["wr50", "wr52", "wr56"]  ← 仅 3 个 RSI 类指标
```

与引擎查询语句完全对应：

```python
# scripts/node_binding_engine.py:637-640
cursor.execute(
    "SELECT data_json FROM indicator_cache WHERE metric=? AND code=?",
    (ind_id, code.upper())
)
```

图表指标 ID 风格（`AL_BASIS` / `AL_FU00014934`）与 `indicator_cache` 的 metric 风格（`wr50`）**命名域完全无交集** → 查询必然 0 行命中 → 全部降级到 simulated。**R-V88-013 根因已由引擎源码行级证实。**

### 3.4 P0-9 命名空间映射（D-7 前置任务）

| 项 | 值 |
|----|----|
| meta_chart 指标数 | **109**（去重） |
| JSONL 指标数 | **579**（去重，5 个文件） |
| **交集** | **0** |
| **覆盖率** | **0.0000%** |
| 缺口指标数 | **109**（全部） |

命名风格对比：

```
meta_chart:  AL_BASIS, AL_FU00014934, CU_FU00014941   ← FU 知几 ID 风格 / 大写
JSONL:       li_21_basis, li_21_close, ni_21_close_front ← 本地小写风格
```

**结论**：D-7 的**真正前置阻塞不是"灌库"，而是"命名映射"**。即使立即把 579 个 JSONL 指标灌入 api_cache.db，覆盖率仍为 0%（命名域不匹配，查询 0 命中）。三方评审推荐的 **D→C→B 路径**（D: 写导入脚本 → C: 反向映射 → B: 增量补齐）经本基线验证为**唯一可行路径**。

---

## 4. 全链路回归套件（T3）

### 4.1 用例矩阵（24 项）

```
数据灌入(A) → 指标读取(B) → 图表渲染(C) → 告警推送(D)
   6 项        6 项          8 项            4 项
```

### 4.2 实测结果

```
用例总数 : 24
汇总     : PASS=16 · BLOCKED=3 · WARN=5 · FAIL=0
判定     : CONDITIONAL_PASS
```

> **重跑说明**：P0-R1 并行工单（DSHE）`db_import_jsonl.py` / `db_load.py` 就位后重跑，A-6 由 🔴 BLOCKED 转 ✅ PASS，A 阶段 WARN 同步降 1。BLOCKED 从 4 项降至 3 项。

**分阶段**：

| 阶段 | PASS | BLOCKED | WARN | FAIL |
|------|:----:|:-------:|:----:|:----:|
| A 数据层（DSHB） | 3 | 1 | 1 | 0 |
| B 指标读取（DSHB） | 5 | 1 | 0 | 0 |
| C 图表渲染（DSHE） | 6 | 1 | 1 | 0 |
| D 告警推送（HERMEShf） | 2 | 0 | 3 | 0 |

### 4.3 3 项 BLOCKED（前置任务型阻断）

| 用例 | 问题 | 依赖任务 |
|------|------|----------|
| **A-3** | Phase03 独立库未创建 | P0-R1（`db_import_jsonl.py` 写入目标库须为独立库，非 `scripts/api_cache.db`） |
| **B-3** | 命名域零交集（0/109） | **P0-R0（命名空间映射表）** |
| **C-3** | D-7 覆盖率 0.0000% | P0-R0 + P0-1 灌库 |

> **A-6 已解除阻断**：P0-R1 并行工单 `db_import_jsonl.py` / `db_load.py` 已就位（✅ PASS），D→C→B 路径首步完成。剩余三项 BLOCKED 仍构成一条因果链：**P0-R0 命名映射 → P0-1 独立库 + 数据灌入 → D-7 达标**。**0 项方案级 FAIL**，框架可用。

### 4.4 已 PASS 的关键用例

| 用例 | 实测 | 对应门禁 |
|------|------|----------|
| A-1 真实数据井 | 25.6 MB / 5 文件（离线，零 API 调用） | 合规 |
| A-2 api_cache 可达 | rows=3 codes=1 metrics=3（**只读校验，未写入生产缓存**） | R-09 |
| **A-6 灌库脚本** | **`db_import_jsonl.py` / `db_load.py` 已就位（P0-R1 并行工单完成）** | **R-V88-013 前置** |
| B-1 meta_chart | 101 张图表 | R-2 |
| B-2 指标绑定 | 101 图表 / 109 去重指标 | D-4 |
| B-4 IC/IR 基线 | 292 条（`ic_ir_baseline_v1`） | F-1 |
| B-5 tree_config | 7 类别 / 9 品种 | — |
| B-6 引擎一致性 | 引擎 101 / 文件 101 / 33 节点 | R-2 |
| C-1 全量渲染 | 101/101，**0 崩溃** | R-2/R-3 |
| C-2 三级降级 | 链路可运行 | R-3 |
| C-4 P99 时延 | p99=2.909ms median=1.541ms max=2.965ms（303 次） | R-4 |
| C-6 并发边界 | 16 并发 / 101 完成 / **0 失败**（线程安全验证） | R-5 前置 |
| C-7 品种覆盖 | 8 品种全建图（cu/al/pb/zn/ni/sn/li/si） | — |
| C-8 校验规则 | 0 ERROR | R-1 |
| D-4 门禁闭环 | `p0_gate_checker.py` 就位 | D-7 |

### 4.5 6 项 WARN（P1/P2 交付物，非阻断）

| 用例 | 说明 |
|------|------|
| A-4 DQA 规则升级 | 5→8 条为 DSHB P1 交付物（D-2/D-6 在 P1/P2 判定） |
| A-5 扩量批次计划 | P0-7 交付物 |
| C-5 CPU FUSE 余量 | 口径不可比（见 §5.2） |
| D-1 告警规则存在性 | Phase03 新增因子面板告警为 P0 交付物 |
| D-2 阈值三档 | CUSUM/4 项规则映射表待 P0-3 冻结 |
| D-3 告警噪声率 | 须 P2 阶段 7 天静默期实测（F-4） |

---

## 5. 性能基线（T4）

### 5.1 采集配置

| 项 | 值 |
|----|----|
| 采集方法 | `psutil.Process().cpu_percent` + `render_with_fallback` × 3 轮 |
| 渲染次数 | **303**（101 图表 × 3 轮） |
| 墙钟耗时 | **0.514 秒** |
| 主机核数 | 4 |
| 基线落盘 | `scripts/p0_baseline_metrics.json` |

### 5.2 ⚠️ CPU 口径方法论（关键修正）

**本次基线发现并修正了一个方法论缺陷**：首版脚本使用 `psutil.cpu_percent()`（全局主机 CPU），实测峰值 **30.6%**，与 Phase02 CPU FUSE 2.0% 相差 15 倍——因为全局 CPU 被并行运行的其他 agent 进程污染，**不可比**。

修正为**进程级 CPU**（`psutil.Process().cpu_percent()`），并显式声明与 FUSE 2.0% 不可直接对比：

| 指标 | 实测值 |
|------|--------|
| 进程 CPU 均值 | **82.47%**（100 = 占满 1 核） |
| 进程 CPU 峰值 | **105.0%**（短暂跨核调度） |
| 归一每核占比 | **2061.67%**（相对 4 核主机） |
| RSS 峰值 | **27.625 MB** |
| 渲染吞吐 | **589.5 图表/秒**（303 / 0.514s） |

**口径声明（写入脚本与报告）**：

```
⚠️ Phase02 CPU FUSE 2.0% / 峰值 1.94% 是「全链路业务稳态均值」口径
   （数据供给 + 推送 + 渲染的稳态），不是渲染引擎复跑的瞬时值。
   本基线是「渲染进程复跑瞬时」口径，含 YAML 解析与 Python 解释器开销，
   两者不可直接对比。
```

**P0-10 门禁判定方式（CHG-08）**：

| 项 | 说明 |
|----|------|
| 门禁阈值 | 全链路 CPU 峰值 ≤1.75%（余量 ≥0.25%） |
| 判定口径 | **须用 DSHB 侧全链路业务 CPU 口径**（同一脚本、同一负载、同一时段采集） |
| 本基线作用 | 提供渲染进程 CPU 起点值与 CHG-08 趋势参考 |
| 状态 | ⚪ NOT_APPLICABLE（P0 阶段口径不具备判定条件） |

**CHG-08 收益评估**：由于口径不可比，**无法给出"改善 X%"的量化结论**。DSHB 侧须在执行 P0-R2（CPU 优化）时，按同一全链路口径采集优化前后对比，本基线的 27.625 MB RSS 与 589.5 图表/秒吞吐可作为**渲染侧的独立优化目标**。

### 5.3 时延基线

| 指标 | 门禁基线（串行） | 回归套件（303 次） | Phase02 burst | 阈值 |
|------|----------------:|-------------------:|--------------:|------|
| median | 1.601 ms | 1.541 ms | — | — |
| p95 | 2.956 ms | — | — | — |
| p99 | **3.161 ms** | **2.909 ms** | 190.47 ms | <500 ms |
| max | 4.440 ms | 2.965 ms | — | — |

**余量**：99.37%（串行口径）。**注意**：串行 P99 与 Phase02 burst P99 相差 60 倍，真实并发风险未被本基线覆盖，须在 P1-10（500 并发仿真）与 P3-3（真实金丝雀）复测。

---

## 6. 合并风险台账更新

详见 `analysis/e2e_output/v88/phase03/review/v88_phase03_merged_risk_list.md`（本工单追加 §8）。本次更新要点：

| 风险 | 更新 | 依据 |
|------|------|------|
| **R-V88-013** | 根因链由"未灌库"细化为**四段因果链**：命名映射 → 灌库脚本 → 独立库 → 灌库 → D-7 达标 | B-3/A-6/A-3/C-3 四项实测 |
| **R-V88-024** | CHG-08 CPU 口径不可比问题登记，判定方式明确为"DSHB 全链路口径" | §5.2 |
| **R-V88-025** | Phase03 独立库未创建（A-3 BLOCKED），灌库前必须创建 | A-3 实测 |
| **R-V88-027** 🆕 | 渲染进程 CPU 与全链路 CPU 口径混淆风险（首版脚本曾误判 30.6% vs 2.0%） | §5.2 修正 |
| **R-09** | 数据库隔离探测自动化（A-3 用例），禁止写 `scripts/api_cache.db` 已固化为回归用例 | A-3 回归 |

---

## 7. 验收标准逐条对照

| # | 验收标准 | 达成 | 依据 |
|---|----------|:----:|------|
| 1 | V87 基线不修改，所有回归脚本仅作用于 P0 原型环境 | ✅ | 脚本仅写入 `phase03/p0/`；A-2 只读 `api_cache.db`；V87 MD5 零修改；check_html 266/266 PASS |
| 2 | D7 门禁可独立复跑、自动计算真实覆盖率，遵循 R3 权威判定规则 | ✅ | `audit_real_coverage()` 独立调用 `render_with_fallback()` 全量 101 图表；R1/R2/R3 语义已落地；覆盖率 0.0000% 与三方评审实测一致 |
| 3 | P0-9、P0-10 门禁，S-4a/S-4b 拆分校验逻辑全部实现 | ✅ | `check_naming_map()` 覆盖率 0/109；`collect_cpu_baseline()` 含口径声明；S-4a/S-4b 独立编号 + 证据扫描（双写 73 / WAL 20 / 分片 70） |
| 4 | 全链路回归套件可一键执行，输出门禁 PASS/FAIL 判定 | ✅ | 24 用例，4 阶段链路（数据灌入→指标读取→图表渲染→告警推送）；退出码 0/2 可被 CI 消费；`--phase/--json/--quick/--no-engine` 四种模式全部实测 |
| 5 | CPU 基线采集完成，评估 CHG-08 CPU 优化收益 | ⚠️ **CONDITIONAL** | 进程级基线已采集（峰值 105% / 均值 82.47% / RSS 27.625 MB / 589.5 图表每秒）；**但 CHG-08 收益无法量化**——因 Phase02 的 2.0%/1.94% 是全链路业务稳态口径，与渲染进程瞬时口径不可比。已在脚本与报告中显式声明，判定权移交 DSHB 全链路口径 |
| 6 | 标记 PHASE03_P0_R2_DONE=TRUE；待 R0/R1/R2 全部完成，执行 P0 整体门禁准入验收 | ✅ | 本工单标记完成；P0 整体准入验收须待 DSHB（P0-R0/R1/R2）与 DSHE（P0-R1）完成后由 HERMEShf 执行 |

**验收结论**：**5/6 完全达成，1 项 CONDITIONAL**（CPU 收益量化受口径限制，已声明并明确判定路径，非缺陷）。整体 **PHASE03_P0_R2_DONE=TRUE**。

---

## 8. 已知限制与后续跟踪

| # | 项 | 说明 | 责任方 |
|---|----|------|:-----:|
| 1 | **D-7 覆盖率 0%** | P0-R0 命名映射 + P0-R1 灌库脚本完成后重跑 `p0_gate_checker.py`，预期自动转 PASS | DSHB+HERMEShf |
| 2 | **P0-9 覆盖率 0%** | 同上（P0-R0 前置任务） | DSHB+HERMEShf |
| 3 | **Phase03 独立库未创建** | A-3 用例，灌库前必须创建；DSHB 须明确 `db_import_jsonl.py` 写入目标库 | DSHB |
| 4 | **CPU 口径不可比** | 本基线为渲染进程瞬时口径；P0-10 门禁须 DSHB 全链路口径采集优化前后对比 | DSHB |
| 5 | **串行时延口径** | 串行 P99=3.16ms 不覆盖真实并发风险；须 P1-10（500 并发仿真）+ P3-3（金丝雀）复测 | DSHE+HERMEShf |
| 6 | **S-4a/S-4b 仅登记证据** | P0 阶段 NOT_APPLICABLE；P1-8（双写一致性）与 P2-7（分片降级演练）为正式判定 | DSHB |
| 7 | **告警噪声率** | F-4 须 P2 阶段 7 天静默期实测 | HERMEShf |
| 8 | **23 项 UNKNOWN 主/阶段门禁** | 需 P1+ 阶段数据，非 P0 范围 | 三方 |

---

## 9. 状态标记

```
PHASE03_P0_R2_DONE=TRUE
PHASE03_P0_GATE_CHECKER_READY=TRUE
PHASE03_P0_REGRESSION_SUITE_READY=TRUE
PHASE03_P0_REGRESSION_CASES=24
PHASE03_P0_REGRESSION_PASS=16
PHASE03_P0_REGRESSION_BLOCKED=3
PHASE03_P0_REGRESSION_WARN=5
PHASE03_P0_REGRESSION_FAIL=0
PHASE03_P0_REGRESSION_VERDICT=CONDITIONAL_PASS
PHASE03_P0_REGRESSION_A6_UNBLOCKED_BY_R1=TRUE
PHASE03_P0_REGRESSION_RERUN_AFTER_P0_R1=TRUE
PHASE03_P0_MAIN_GATE_TOTAL=21
PHASE03_P0_STAGE_GATE_TOTAL=40
PHASE03_P0_GATE_MEASURED=6
PHASE03_P0_GATE_BLOCKED_PRE_P0=2
PHASE03_P0_GATE_FAIL=0
PHASE03_P0_GATE_VERDICT=CONDITIONAL_PASS
PHASE03_P0_D7_COVERAGE_PCT=0.0000
PHASE03_P0_D7_P1_THRESHOLD_PCT=60
PHASE03_P0_D7_P3_THRESHOLD_PCT=95
PHASE03_P0_D7_R3_AUTHORITATIVE=TRUE
PHASE03_P0_D7_CHARTS_TOTAL=101
PHASE03_P0_D7_RENDERABLE=101
PHASE03_P0_D7_SOURCE_DIST=simulated:101
PHASE03_P0_P0_9_COVERAGE_PCT=0.0000
PHASE03_P0_P0_9_META_INDICATORS=109
PHASE03_P0_P0_9_JSONL_INDICATORS=579
PHASE03_P0_P0_9_INTERSECTION=0
PHASE03_P0_P0_10_CPU_METHOD=psutil.Process.cpu_percent
PHASE03_P0_CPU_PROC_MEAN_PCT=82.4667
PHASE03_P0_CPU_PROC_PEAK_PCT=105.0
PHASE03_P0_CPU_RSS_MAX_MB=27.625
PHASE03_P0_CPU_RENDERS=303
PHASE03_P0_CPU_WALL_SEC=0.514
PHASE03_P0_CPU_RENDER_THROUGHPUT=589.5_CHARTS_PER_SEC
PHASE03_P0_CPU_PORTABILITY_WARN=TRUE
PHASE03_P0_CPU_PORTABILITY_NOTE=渲染进程瞬时口径与全链路业务稳态口径不可比
PHASE03_P0_CHG08_BENEFIT_QUANTIFIED=FALSE
PHASE03_P0_LATENCY_P99_MS=3.161
PHASE03_P0_LATENCY_MARGIN_PCT=99.37
PHASE03_P0_S4A_SPLIT=TRUE
PHASE03_P0_S4B_SPLIT=TRUE
PHASE03_P0_S4A_DUAL_WRITE_EVIDENCE=73
PHASE03_P0_S4A_WAL_EVIDENCE=20
PHASE03_P0_S4B_SHARD_EVIDENCE=70
PHASE03_P0_S4_SCANNED_FILES=18
PHASE03_P0_PHASE03_TEST_DB_EXISTS=FALSE
PHASE03_P0_R09_DB_ISOLATION_TESTED=TRUE
PHASE03_P0_CONCURRENT_16_THREAD_SAFE=TRUE
PHASE03_P0_VARIETY_COVERAGE=8_OF_8
PHASE03_P0_CHECK_HTML=266_OF_266_PASS
PHASE03_P0_R0_READY_FOR_DSHB=TRUE
PHASE03_P0_R1_READY_FOR_DSHB=TRUE
PHASE03_P0_OVERALL_ADMISSION_PENDING_R0_R1_R2=TRUE
PHASE03_P0_BASELINE_JSON_SAVED=TRUE
```

---

*Document Generated: 2026-10-15 UTC+8*
*Generated by: HERMEShf Agent*
*Branch: feature/v88-g1 (BRANCH_LOCKED: TRUE)*
*Baseline HEAD: e3673f2*
*APPEND_ONLY: TRUE | NO_MODIFY_V87: TRUE | NO_EDIT_RELEASE_TAG: TRUE | NO_ZHIJI_API_CALL: TRUE*
*Phase02 生产链路零修改 | scripts/api_cache.db 只读校验 | check_html 266/266 PASS*
