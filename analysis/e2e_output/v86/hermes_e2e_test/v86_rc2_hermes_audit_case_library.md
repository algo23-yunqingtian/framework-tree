# V86-RC2 审计测试用例库（固化归档版）

> **工单**: 工单-HERMES / T3.1 审计测试用例库固化归档
> **分支**: `feature/v85-chart-template` @ commit `caa2410`
> **编制方**: HERMES（L3 审计方）
> **日期**: 2026-10-15
> **判定基准**: `v86_rc2_hermes_audit_canonical_spec.md`（五级术语 + 三级桥接率 + 脚本审计）
> **契约输入**: `v86_rc2_dshe_l2_deliverable_spec.md`（DSHE L2 证据包结构契约）
> **约束**: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **文档状态**: FINAL — 可重复回放基线
> **上轮基线**: `v86_rc2_hermes_pipeline_e2e_simulation_report.md` / `_gate_simulation_report.md` / `_audit_rule_validation_report.md` / `_dep_gate_logic_verify.md`（本轮归档并结构化为用例）

---

## 0. 用例库定位与使用方式

### 0.1 定位

本用例库把前一轮（commit `fa4974f`）四级仿真结论**结构化为可重复回放的用例集**，补齐三类前一轮未固化的场景（正向完整链路、部分 DEP 恢复），并为 T3.2 `evidence_auditor.py` 提供**标准输入载荷与预期输出**。

每个用例固化五元组：

| 字段 | 说明 |
|------|------|
| `input_payload` | 送入流水线的完整提交包结构 |
| `expected_result` | 期望的流水线流转结果与 Gate 结论 |
| `audit_intercept_point` | 预期命中的审计检测点（D0x.x） |
| `alert_output` | 预期审计告警文本 |
| `pipeline_flow` | 预期流转路径（L1→L2→L3→Gate） |

### 0.2 回放方式

用例库可直接驱动 T3.2 校验器：每个用例的 `input_payload` 即 `evidence_auditor.py` 的输入。回放命令见 §6。

### 0.3 本轮 zhiji 实测取证（用例真实证据基线，2026-10-15）

| ID | 实测结果 | 用途 |
|----|---------|------|
| `ID02226332`（对照组，长ID） | HTTP 200，8 点，value=30700/20875/26950… 非零 | **证明环境健康**（非数据源挂断） |
| `j25_tc` | HTTP 500「无法识别指标来源(id前缀)」 | 短ID 解析缺失实证 |
| `s_001` | HTTP 500（同左） | 伪造ID 实证 |
| `ID_FAKE001` | HTTP 500（同左） | 伪造ID 实证 |
| `i1` | permission_state=-4，0 点 | 未映射/无权限实证 |

> **对照组是全部负向用例结论成立的前提**：它把"短ID 取不到"归因锁定为**服务器侧解析能力缺失**（`ValueError: 无法识别指标来源` 抛自 `commodity_api.py:443`），而非凭据失效或数据源故障。

---

## 1. 审计检测点全集（用例判定依据）

四条硬审计规则展开为 16 个可判定检测点：

### R-AUDIT-01｜双证据 COMPLETED

| 检测点 | 判定逻辑 | 阻断级别 |
|--------|---------|---------|
| D01.1 | COMPLETED 条目是否有元数据证据（短ID+长ID+语义ID 三字段齐全） | 缺→PENDING |
| D01.2 | COMPLETED 条目是否有真实取数证据（原始 payload + value≠0 + 语义匹配） | 缺→**PENDING+告警** |
| D01.3 | 是否存在"桥接表填 ID 即标 COMPLETED"（无取数证据） | **阻断·造假模式** |

### R-AUDIT-02｜唯一有效桥接率口径

| 检测点 | 判定逻辑 | 阻断级别 |
|--------|---------|---------|
| D02.1 | 是否以"元数据完成率"冒充"有效桥接率" | **阻断·口径混淆** |
| D02.2 | 是否出现单一未拆分的 bridge rate 数字 | 告警+要求双栏拆分 |
| D02.3 | 有效桥接率分子是否含"仅元数据完成"条目 | **阻断·分子虚增** |

### R-AUDIT-03｜L2 独立调用链

| 检测点 | 判定逻辑 | 阻断级别 |
|--------|---------|---------|
| D03.1 | L2 记录是否含独立 API 调用 URL + 响应体 | 缺→**阻断·背书式** |
| D03.2 | L2 PASS 结论是否引用 DSHB 自报数字 | 是→**阻断·零价值** |
| D03.3 | L2 是否按 COMPLETED/PENDING 分级 | 否→**阻断** |

### R-AUDIT-04｜G-09/G-10 强制准入

| 检测点 | 判定逻辑 | 阻断级别 |
|--------|---------|---------|
| D04.1 | 脚本入参是否 search 中转/自动替换 ID | 是→**G-09 FAIL** |
| D04.2 | 是否有 `requested_id==resolved_id` 断言 | 无→**G-09 FAIL** |
| D04.3 | 是否全 0 计 PASS | 是→**G-09 FAIL** |
| D04.4 | 是否留存原始 payload | 无→**G-09 FAIL** |
| D04.5 | 对照组 + COMPLETED 实测取数是否通过 | 否→**G-10 FAIL** |

---

## 2. 大类一：正向成功场景

### CASE-A01｜DEP 就绪 + 双指标达标，完整链路流转

| 字段 | 内容 |
|------|------|
| **用例ID** | CASE-A01 |
| **场景描述** | 数据平台完成短ID 解析（DEP-001 → RESOLVED），DSHB 提交 178 条全量，L2 独立调用全部成功 |
| **input_payload** | `metadata_rate=1.0`，`real_fetchable_rate=1.0`，`completed=178/178`，每条含 `trace_id` + 原始 request/response payload，`requested_id==resolved_id`，`value≠0` |
| **expected_result** | L1 PASS → L2 PASS → L3 PASS → **Gate READY** |
| **audit_intercept_point** | 无拦截（全部通过） |
| **alert_output** | 无（仅 LOW 级 INFO 事件：正常提交记录） |
| **pipeline_flow** | `L1自测→L2独立抽样→L3预审→Gate终审(READY)` |

### CASE-A02｜对照组驱动的合规提交（最小可放行单元）

| 字段 | 内容 |
|------|------|
| **用例ID** | CASE-A02 |
| **场景描述** | 最小放行样本：仅以已知可用长ID 提交（如 `ID02226332`），双证据齐全 |
| **input_payload** | `indicator_id=ID02226332`，`requested_id=ID02226332`，`resolved_id=ID02226332`，response.points=8，value 非零，payload 完整 |
| **expected_result** | L1 PASS → L2 PASS（DSHE 独立复核同样返回 8 点非零）→ L3 PASS → Gate READY |
| **audit_intercept_point** | 无拦截；D01.1/D01.2/D04.2/D04.4/D04.5 全部满足 |
| **alert_output** | 无 |
| **pipeline_flow** | `L1→L2→L3→Gate(READY)` |

> **用例价值**：CASE-A02 是 DEP 未就绪期间唯一可实测跑通的**正向最小单元**，用于验证流水线代码路径本身无缺陷（与 CASE-N 类区分）。

---

## 3. 大类二：旧口径造假场景

### CASE-N01｜元数据完成 + 真实取数 0%（虚假桥接率）

| 字段 | 内容 |
|------|------|
| **用例ID** | CASE-N01 |
| **场景描述** | 复刻 git 提交 `86c1f6e` 形态：170 条桥接表填 ID 即标 COMPLETED，桥接率表述为"100%" | [OLD_CALIBER - METADATA_ONLY, HERMES_INVALID]
| **input_payload** | `completed=170/170`，`bridge_rate="100%"`，`metadata_rate=1.0`，`real_fetchable_rate=0.0`，无原始 payload，脚本入参为 `search关键词→取长ID→查长ID` |
| **expected_result** | **L1 即被阻断**，不进入 L2；Gate NOT_READY |
| **audit_intercept_point** | D01.2（缺取数证据）→ R-AUDIT-01；D01.3（填ID即COMPLETED）→ 阻断；D02.1（元数据率冒充）→ R-AUDIT-02；D02.3（分子虚增）→ 阻断；D04.1（search 中转）→ G-09 FAIL；D04.2（无一致性断言）→ G-09 FAIL；D04.4（无 payload）→ G-09 FAIL |
| **alert_output** | `CRITICAL R-AUDIT-01: 170 条 COMPLETED 缺真实取数证据，全部降级 PENDING`；`CRITICAL R-AUDIT-02: 桥接率口径混淆，声称 100% 实际 0%`；`CRITICAL G-09: 脚本入参造假（search 中转），本批次结果作废` |
| **pipeline_flow** | `L1提交→[审计引擎拦截]→阻断（不进入L2），旧证据包作废` |

### CASE-N02｜桥接率口径单一数字不拆分

| 字段 | 内容 |
|------|------|
| **用例ID** | CASE-N02 |
| **场景描述** | 提交包只给单一 `bridge_rate=85%`，未区分元数据/真实两栏 |
| **input_payload** | `bridge_rate=0.85`（单值），`metadata_rate` / `real_fetchable_rate` 字段缺失 |
| **expected_result** | L1 告警并**要求双栏拆分后重提**，暂不阻断流转但标记 CONDITIONAL |
| **audit_intercept_point** | D02.2（单一未拆分数字） |
| **alert_output** | `HIGH R-AUDIT-02: 桥接率未拆分口径，须提供元数据完成率与真实可取数率双栏` |
| **pipeline_flow** | `L1提交→[CONDITIONAL 标记]→退回DSHB补口径→重新提交` |

### CASE-N03｜L2 背书式引用（零价值背书）

| 字段 | 内容 |
|------|------|
| **用例ID** | CASE-N03 |
| **场景描述** | L2 报告仅写"DSHB 报 60/60 通过，L2 确认通过"，无独立调用 |
| **input_payload** | `dshb_reuse=true`，`calls=[]`（无独立调用），`conclusion="与DSHB一致"` |
| **expected_result** | **L2 判定无效**，退回 DSHE 重做独立调用；不进入 L3 |
| **audit_intercept_point** | D03.1（无独立调用 URL+响应体）→ 阻断；D03.2（引用自报数字）→ 阻断；`dshb_reuse=true` 违反 L2-R01 |
| **alert_output** | `CRITICAL R-AUDIT-03: L2 背书式引用，零价值，证据包作废` |
| **pipeline_flow** | `L1→L2提交→[L2证据包无效]→退回DSHE独立重测` |

### CASE-N04｜伪造ID 提交（s_xxx / ID_XXX 不存在于 zhiji）

| 字段 | 内容 |
|------|------|
| **用例ID** | CASE-N04 |
| **场景描述** | 提交包含 `s_001` / `ID_FAKE001` 等不存在于 zhiji 的 ID |
| **input_payload** | `indicator_id=s_001`（标记 COMPLETED，无 payload） |
| **expected_result** | 阻断；判定为内部缺陷（映射登记错误），非 DEPENDENCY_BLOCK |
| **audit_intercept_point** | D01.2（无取数证据）；实测 HTTP 500「无法识别指标来源(id前缀)」；**关键：此类 ID 不可豁免为外部阻塞** |
| **alert_output** | `HIGH 内部缺陷: s_001/ID_FAKE001 不存在于 zhiji，属桥接表登记错误，计入内部 P1，禁止归类 DEPENDENCY_BLOCK` |
| **pipeline_flow** | `L1提交→[审计引擎拦截]→阻断，退回DSHB修正映射` |

---

## 4. 大类三：DEP 全阻塞场景

### CASE-D01｜短ID 解析全阻塞（合规阻塞，非造假）

| 字段 | 内容 |
|------|------|
| **用例ID** | CASE-D01 |
| **场景描述** | DEP-001 OPEN：脚本入参正确（`?id=j25_tc` 直连），但服务器无解析能力 |
| **input_payload** | `requested_id=j25_tc`，`resolved_id=j25_tc`（一致，断言通过），HTTP 500，直连测试记录留存，无 search 中转 |
| **expected_result** | **不判造假**；归类 DEPENDENCY_BLOCK；Gate 仍 NOT_READY（准入条件不满足，不豁免） |
| **audit_intercept_point** | D04.1/D04.2/D04.4 **均通过**（脚本合规）；D04.5 FAIL（对照组通过但目标取数失败）→ G-10 FAIL |
| **alert_output** | `HIGH DEPENDENCY_BLOCK: DEP-001 阻塞，短ID 解析缺失（HTTP 500），不计入内部 P0/P1，Gate 维持 NOT_READY` |
| **pipeline_flow** | `L1提交→L2独立复核(同样失败)→L3预审→Gate(NOT_READY，责任归外部)` |

### CASE-D02｜以外部阻塞为借口伪造日志（不可豁免）

| 字段 | 内容 |
|------|------|
| **用例ID** | CASE-D02 |
| **场景描述** | 声称 DEP 阻塞，但提供的"证据"是伪造的日志片段 |
| **input_payload** | `error_log="HTTP 500 ..."` 但无请求 URL、无时间戳、无 trace_id；`requested_id` 与 `resolved_id` 不一致 |
| **expected_result** | **阻断**，判定内部缺陷 P0（造假），DEP 标记无效 |
| **audit_intercept_point** | D01.3（无真实直连记录）；D04.2（一致性断言失败）；D04.4（无原始 payload）；违反 DEP 规范 §2.1「造假/伪造日志永不构成 DEPENDENCY_BLOCK」 |
| **alert_output** | `CRITICAL R-AUDIT-01: 疑似伪造阻塞证据，DEP-001 归类无效，升级内部 P0` |
| **pipeline_flow** | `L1提交→[审计引擎拦截]→阻断，上报主脑` |

---

## 5. 大类四：部分 DEP 恢复场景（本轮新增，前一轮未固化）

### CASE-P01｜部分短ID 已就绪（混合状态）

| 字段 | 内容 |
|------|------|
| **用例ID** | CASE-P01 |
| **场景描述** | 数据平台分批上线：部分短ID 前缀已可解析，其余仍阻塞 |
| **input_payload** | 178 条中 60 条 `real_fetchable=true`（有 payload + value≠0），118 条 HTTP 500；两栏桥接率 `metadata_rate=1.0`，`real_fetchable_rate=60/178=0.337` |
| **expected_result** | L1/L2/L3 通过审计（口径正确、脚本合规）；**Gate 仍 NOT_READY**（G-06 有效桥接率未达阈值） |
| **audit_intercept_point** | 无审计拦截；D02.1/D02.3 通过（口径拆分正确）；Gate G-06 FAIL（0.337 < 阈值） |
| **alert_output** | `MEDIUM 部分恢复: 真实可取数率 33.7% (60/178)，审计合规但 Gate 未达准入阈值` |
| **pipeline_flow** | `L1→L2→L3(审计全通过)→Gate(NOT_READY，等待DEP-001全量就绪)` |

### CASE-P02｜恢复后残留旧口径（增量污染）

| 字段 | 内容 |
|------|------|
| **用例ID** | CASE-P02 |
| **场景描述** | 部分恢复后，提交包同时含新就绪条目（合规）与旧残留条目（仍标 COMPLETED 但无取数证据） |
| **input_payload** | 60 条合规 COMPLETED + 118 条"填ID即COMPLETED"（无 payload，沿用旧脚本） |
| **expected_result** | **阻断**。已就绪部分有效，残留部分被降级 |
| **audit_intercept_point** | D01.2 + D01.3 命中残留 118 条；有效桥接率从声称 100% 纠正为 33.7% |
| **alert_output** | `CRITICAL R-AUDIT-01: 残留 118 条仅元数据即标 COMPLETED，降级 PENDING；有效桥接率 100%→33.7%` |
| **pipeline_flow** | `L1提交→[审计引擎拦截残留]→退回DSHB删除旧脚本产出，仅重交合规 60 条` |

### CASE-P03｜DEP-001 状态机迁移（OPEN→IN_PROGRESS→RESOLVED）

| 字段 | 内容 |
|------|------|
| **用例ID** | CASE-P03 |
| **场景描述** | DEP-001 状态机迁移过程，验证各状态下的判定 |
| **input_payload** | 状态 = `OPEN` / `IN_PROGRESS`（外部方已认领）/ `RESOLVED`（外部方上线） |
| **expected_result** | OPEN/IN_PROGRESS → Gate NOT_READY + 复审可暂停；RESOLVED → 触发 CASE-P01/P02 重跑，Gate 按实测判定 |
| **audit_intercept_point** | 不属审计拦截点，属 DEP 状态机；每状态迁移须更新登记表 + 提交记录 |
| **alert_output** | `LOW INFO: DEP-001 状态迁移 OPEN→IN_PROGRESS`；`LOW INFO: DEP-001 RESOLVED，触发三级流水线重跑` |
| **pipeline_flow** | 按 DEP 规范 §4 状态机流转，RESOLVED 后强制全量重跑 |

---

## 6. 用例回放机制

### 6.1 用例 → 校验器输入映射

本用例库的 `input_payload` 结构即 `evidence_auditor.py` 的输入契约（见 T3.2）。回放：

```bash
cd analysis/e2e_output/v86/hermes_e2e_test
# 用例库内置测试夹具，一键回放全部 11 个用例
python3 evidence_auditor.py --run-case-library
```

### 6.2 用例与预期判定对照表

| 用例 | 大类 | 预期校验器结论 | 关键拦截检测点 |
|------|------|--------------|--------------|
| CASE-A01 | 正向 | **PASS** | 无 |
| CASE-A02 | 正向 | **PASS** | 无 |
| CASE-N01 | 造假 | **FAIL** | D01.2/D01.3/D02.1/D02.3/D04.1/D04.2/D04.4 |
| CASE-N02 | 造假 | **CONDITIONAL_PASS** | D02.2 |
| CASE-N03 | 造假 | **FAIL** | D03.1/D03.2 |
| CASE-N04 | 造假 | **FAIL** | D01.2（内部缺陷，非 DEP） |
| CASE-D01 | DEP阻塞 | **FAIL**（Gate） | D04.5 → G-10 |
| CASE-D02 | DEP阻塞 | **FAIL** | D01.3/D04.2/D04.4 |
| CASE-P01 | 部分恢复 | **FAIL**（Gate） | G-06 阈值 |
| CASE-P02 | 部分恢复 | **FAIL** | D01.2/D01.3（残留） |
| CASE-P03 | 部分恢复 | **CONDITIONAL_PASS** | DEP 状态机 |

### 6.3 不可覆盖归档

- 用例库为**新增迭代版本**，未覆盖任何历史规范/仿真报告（NO_OVERWRITE）；
- 每个用例标注来源场景（正向前一轮 §2 场景1 / 造假前一轮场景2 / DEP 前一轮场景3 / 部分恢复本轮新增）；
- 用例集版本号：`CASE-LIB v1.0`，后续新增用例递增小版本，禁止原地改写已固化用例的判定预期。

---

## 7. 用例库完整性自证

| 覆盖维度 | 覆盖情况 |
|---------|---------|
| 正向成功 | 2 用例（全量 + 最小单元） |
| 旧口径造假 | 4 用例（虚假桥接率 / 口径不拆分 / L2 背书 / 伪造ID） |
| DEP 全阻塞 | 2 用例（合规阻塞 / 借借口伪造） |
| 部分恢复 | 3 用例（混合状态 / 旧口径残留 / 状态机迁移） |
| **合计** | **11 用例，4 大类全覆盖** |
| 四条审计规则 | R-AUDIT-01/02/03/04 全部有对应用例触发 |
| 全部 16 检测点 | D01.1~D04.5 全部至少被 1 个用例覆盖 |
| zhiji 实测证据 | 5 个 ID 实测（1 对照 + 3 HTTP500 + 1 permission-4） |

**状态标记**：`HERMES_AUDIT_CASE_LIBRARY_ARKED=TRUE`（CASE-LIB v1.0 固化完成）
