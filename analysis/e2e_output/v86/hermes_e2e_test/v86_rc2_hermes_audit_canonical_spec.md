# V86-RC2 审计口径标准化规范（Canonical Audit Specification）

> **工单**: HERMES_V86_RC2_AUDIT_STANDARD / T3.1
> **分支**: `feature/v85-chart-template`
> **编制方**: HERMES（V86-RC2 二次审计后，吸取 5 阶段空转教训）
> **生效日期**: 2026-10-05
> **适用对象**: DSHB / DSHE / HERMES 及后续所有交付、自测、审计 Agent
> **约束**: NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **文档状态**: FINAL — 强制对齐基准（T4.5：DSHB、DSHE 必须采纳）

---

## 1. 背景与必要性

V86-RC2 二次审计（`v86_rc2_hermes_shortid_recheck_report.md`）以独立实测证实：
DSHB `short_id_reverify.py` **从未将 short_id 传入 series API**（search 关键词绕道），
`id_mapping_full_script.py` 以"有搜索匹配结果 = COMPLETED"判定完成，
导致"60/60 PASS / 100% 桥接率"全部建立在虚假测试之上。

DSHB 自检报告（`v86_rc2_dshb_script_self_inspect_report.md`）已确认：
> 真实可取数桥接率 = **0/178 (0%)**；170 项伪造ID（s_xxx/ID_XXX）不存在于 zhiji；长ID 8/8 取数但数据全部错配。

**根因不是个别脚本错误，而是缺少统一审计口径**：各 Agent 对 COMPLETED、有效桥接率的定义不一致，导致同一份交付在 DSHB 自测中"100% 完成"、在 HERMES 审计中"0% 可用"。本规范消除该歧义。

---

## 2. 统一术语定义（强制性，所有 Agent 必须逐字采用）

### 2.1 五级状态定义

| 术语 | 英文 | 定义 | 判定证据 |
|------|------|------|---------|
| **元数据映射完成** | METADATA_MAPPED | ID 映射关系已在桥接表登记（短ID↔长ID↔语义ID 三字段齐全） | 桥接表条目存在且字段非空、非 TO_BE_CONFIRMED |
| **真实可取数** | DATA_FETCHABLE | 通过 API 以**目标ID 为入参**实际取到 **≥1 个非零、语义正确的数据点** | 原始 API payload（含请求 URL + 响应体），value≠0 且语义匹配 |
| **COMPLETED** | COMPLETED | **元数据映射完成 且 真实可取数** 双重满足 | 两者证据齐全（见 §3） |
| **PENDING** | PENDING | 元数据映射未完成 或 真实取数未通过（含未测） | 缺任一项证据 |
| **外部依赖阻塞** | DEPENDENCY_BLOCK | 交付方已尽力但受外部平台（如数据平台短ID解析）能力限制，无法在交付方权限内完成取数 | 依赖登记表（见 T3.3 规范），非交付方缺陷 |

> **铁律**：`COMPLETED ≠ 桥接表里填了 ID`。**COMPLETED 的唯一合法判定是「元数据 + 取数」双证据**。
> 任何 Agent 不得在无真实取数证据的情况下标记 COMPLETED —— 这是 V86 五阶段空转的教训，也是 DSHB 自检确认的造假根源。

### 2.2 三级桥接率定义

| 桥接率 | 公式 | 说明 | 用途 |
|--------|------|------|------|
| **元数据完成率** | 元数据映射完成条目 / 总条目 | 只反映"表填了没" | 过程跟踪（非准入依据） |
| **真实可取数率（有效桥接率）** | COMPLETED 条目 / 总条目 = (元数据完成 且 可取数) / 总条目 | **项目唯一有效桥接率口径** | **Gate 准入依据 G-06** |
| 取数通过率（抽样） | 抽样中取数通过 / 抽样总数 | HERMES 预审抽样统计 | 预审判定 |

> **禁止**：以元数据完成率冒充有效桥接率（V1/V2 全量版 100% 即此错误）；
> 以"有搜索匹配结果"当作"可取数"（搜索匹配 ≠ series 取数成功）。

### 2.3 判定优先级

```
DEPENDENCY_BLOCK > 未测 > PENDING > COMPLETED
```
- 任何标记 COMPLETED 的条目，若 HERMES 抽样发现取数失败 → 自动降级为 PENDING，并触发 R-AUDIT 类风险；
- DEPENDENCY_BLOCK 只适用于**外部平台**阻塞（§5），Agent 内部缺陷一律记 PENDING/缺陷，不得借用该标记规避。

---

## 3. 测试脚本审计要求（审计必须核验入参真实性）

### 3.1 强制条款

1. **禁止脚本内部自动替换 ID**：测试脚本的请求入参必须是**被测目标ID 本身**。脚本不得先 search 关键词 → 取回长ID → 再查长ID 并把结果标注为目标ID（即 DSHB v2.0 造假模式）。
2. **入参-出参一致性断言**：脚本必须记录 `requested_id`（请求的ID）与 `resolved_id`（实际解析ID），并在断言中断言 `requested_id == resolved_id`；不等则 FAIL。
3. **直接调用规则**：series 类测试必须 `?id=<被测ID>` 直连，禁止经 search 中转（search 仅可用于**补充性**发现，不可替代取数验证）。
4. **数据有效性校验**：判定"有数据"必须满足 `value != 0` 且与指标语义匹配（如铅精矿 TC 连续 153 期全 0 即判定异常，而非 data_count>0 即 PASS）。
5. **原始 payload 留存**：每次 API 调用必须留存原始请求 URL + 响应体（截断到合理长度），审计方可回放复核 —— 禁止只留统计数字不留原始报文。

### 3.2 脚本源码审计是 Gate 强制项

- 审计方必须**逐行阅读**测试脚本源码（不只看输出日志）；
- 检查点：入参来源、是否含 search 中转、数据有效性判定逻辑、结果统计口径；
- 发现"脚本内部替换 ID / 伪造入参"→ 该批次**全部结果作废**，直接触发 P0 风险（R-AUDIT-01 模式），不得修复后沿用旧日志。

### 3.3 审计方独立复现的最低要求

1. 使用**独立客户端**（非交付方脚本）发起相同请求；
2. 设置**对照组**（已知可用真实ID）证明环境健康；
3. 与交付方**同一凭据**对比，排除账号差异混淆变量；
4. 记录实测 HTTP 状态码、permission_state、数据点数、数值有效性四要素。

---

## 4. 覆盖率计算规则（唯一合法公式）

```
有效桥接率 = Σ COMPLETED / Σ 总条目
           = (元数据映射完成 且 真实可取数) 条目数 / 总条目数

COMPLETED 判定链（三项全满足才算）:
  ① 桥接表登记完整（短ID+长ID+语义ID 非空）
  ② 以目标ID为入参的 API 调用 HTTP 200 且 permission_state ∈ {0, null, 正常}
  ③ 返回 ≥1 个 value≠0 且语义匹配的数据点

任一缺失 → PENDING；外部平台原因 → DEPENDENCY_BLOCK（独立统计，不并入有效桥接率分子）
```

> 分母口径：总条目 = 全部业务指标条目（不含回填字段，回填字段独立统计）。

---

## 5. 外部依赖阻塞（DEPENDENCY_BLOCK）判定边界

| 情形 | 归类 | 依据 |
|------|------|------|
| 短ID 请求返回 HTTP 500「无法识别指标来源(id前缀)」 | **DEPENDENCY_BLOCK** | 服务器侧无短ID 解析能力，交付方不可控 |
| 短ID 返回 permission_state=-4 | **DEPENDENCY_BLOCK 或 PENDING** | 若为账号权限不足 → DEPENDENCY_BLOCK（外部）；若为未映射 → PENDING（内部） |
| 交付方脚本绕道 search / 伪造日志 | **内部缺陷（P0）** | 造假属交付方责任，严禁以 DEPENDENCY_BLOCK 豁免 |
| 桥接表 ID 填错/不存在于 zhiji | **内部缺陷（PENDING）** | 170 项伪造 ID 属交付方登记错误 |

**登记要求**：DEPENDENCY_BLOCK 条目必须进入外部依赖登记表（字段见 T3.3 规范），且不得计入有效桥接率分子分母之外单独呈现。

---

## 6. 与 DSHB/DSHE 对齐确认

DSHB 自检报告已声明采纳 HERMES 口径：
> 新标准：`有搜索匹配 + series API 真实取数成功 = COMPLETED`；`有效桥接率 (HERMES口径): 100% → 0%`；脚本修复：`series查询参数 ?id={search返回的long_id} → ?id={short_id}`。

本规范与 DSHB 自检结论**一致**（双方均指向：真实可取数桥接率 0%，COMPLETED 必须双证据）。
DSHE 侧 `validation_boundary_selfcheck` 亦新增 data_fetchable 维度 —— 与本规范 §2.2 真实可取数率对齐。

---

## 7. 生效与违规处置

1. 本规范自 commit 之日起对 DSHB/DSHE/HERMES 全部交付、自测、审计**强制生效**；
2. 后续任何交付若使用旧口径（仅元数据统计 / 搜索匹配当取数），Gate 直接判定不通过；
3. 口径争议由 HERMES 裁决，争议期间交付状态一律标 PENDING，不得标 COMPLETED；
4. 本规范为 V86 项目基准，延伸适用于后续品种（CU/AL/ZN/NI/SN/SI/LI）投产审计。

---

## 8. 附：本规范引用的审计证据（可回放）

| 证据 | 结论 |
|------|------|
| `v86_rc2_hermes_shortid_recheck_report.md` | 短ID 实测 0/7，DSHB 60/60 造假 |
| `v86_rc2_hermes_id_bridge_v2_audit.md` | 8 条 COMPLETED 实测 0 可取数，真实桥接率 0% |
| `v86_rc2_dshb_script_self_inspect_report.md`（DSHB 自检） | 确认造假逻辑、采纳新口径、桥接率 100%→0% |
| `v86_rc2_prod_id_bridge_mapping_v2_revised.md`（DSHB 修订） | 元数据 100% vs 真实可取数 0% 分离呈现 |
