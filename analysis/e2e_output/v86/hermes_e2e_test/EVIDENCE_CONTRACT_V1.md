# EVIDENCE_CONTRACT_V1 — 三方证据包契约基线

> **契约版本**: `EVIDENCE_CONTRACT_V1`
> **工单**: 工单-HERMES / T3.2 三方证据包契约 V1 基线文档
> **分支**: `feature/v85-chart-template` @ commit `dcf7194`
> **编制方**: HERMES（L3 审计方）
> **日期**: 2026-10-15
> **对齐团队**: DSHB（L1 自测方）+ DSHE（L2 独立校验方）+ HERMES（L3 预审审计方）
> **校验实现**: `evidence_auditor_v2.py`（R-CONTRACT-V1 / CV-01~CV-05）
> **关联契约**: `v86_rc2_dep_registry_common_spec.md`（DEP 登记与状态机）
> **约束**: NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **状态**: BASELINE — 三方强制对齐（任何字段变更必须升级版本）

---

## 0. 契约定位

### 0.1 为什么需要这份契约

三级流水线（L1 DSHB 自测 → L2 DSHE 独立校验 → L3 HERMES 预审）此前缺少**统一证据包格式**：

- DSHB L1 与 DSHE L2 各自定义 JSON 结构，字段名不一致（如 L1 用 `short_id`，L2 用 `zhiji_short_id`）；
- 审计器无法用同一套校验逻辑处理两类包；
- 跨团队 DEP 台账字段无统一定义，责任归因无从对齐。

本契约把 L1/L2 证据包**收敛为一份可机读、可校验、可版本化的格式规范**，作为全系统基线。

### 0.2 强制效力

| 团队 | 角色 | 义务 |
|------|------|------|
| **DSHB** | L1 证据包生产者 | 提交的 L1 包必须符合 §3 结构，`call_type=DSHB_L1_SELF_TEST` |
| **DSHE** | L2 证据包生产者 | 提交的 L2 包必须符合 §4 结构，`call_type=DSHE_INDEPENDENT_ZHIJI` |
| **HERMES** | 契约守门方 | 按 §7 校验规则执行审计，不合规即拒收 |

### 0.3 契约不满足的后果

证据包缺必填字段或缺 `contract_version` → `evidence_auditor_v2.py` 触发 CV-01~CV-04（HIGH），
包被标记 `CONDITIONAL_PASS` 或 `FAIL`，**不得进入下一级流水线**。

---

## 1. 契约元数据

| 项 | 值 |
|----|-----|
| 契约标识 | `EVIDENCE_CONTRACT_V1` |
| 主版本号 | 1（字段结构变更时 +1） |
| 次版本号 | 0（字段语义澄清/新增可选字段时 +1，不破坏兼容） |
| 生效日期 | 2026-10-15 |
| 校验器版本 | `evidence_auditor_v2.py` v2.0.0 |
| 用例库版本 | CASE-LIB v2.0（23 用例） |

### 1.1 版本命名规则

```
EVIDENCE_CONTRACT_V{MAJOR}[.y]
```

- **MAJOR 变更**：字段删除、字段改名、字段类型变更、必填性变更 → 破坏兼容，须三方评审；
- **次版本变更**：仅新增可选字段、语义澄清 → 向后兼容，无需全体重签。

---

## 2. 证据包顶层结构

```json
{
  "contract_version": "EVIDENCE_CONTRACT_V1",
  "fingerprint": "DSHE-20261015_100007-A3F2B1C4",
  "run_id": "20261015_100007",
  "session_id": "A3F2B1C4",
  "caller": "DSHE_V86_RC2_L2_AUDIT",
  "total_calls": 42,
  "generated_at": "2026-10-15T10:00:11+08:00",
  "dshb_reuse": false,
  "metadata_rate": 1.0,
  "real_fetchable_rate": 0.0,
  "bridge_rate": 0.0,
  "control_check": { "http_status": 200, "has_nonzero_value": true },
  "script_audit": {
    "uses_search_passthrough": false,
    "has_id_consistency_assert": true,
    "zero_value_counts_as_pass": false,
    "retains_raw_payload": true
  },
  "md5_manifest": { "evidence_package": "<self-md5>" },
  "dep": {
    "registry": { "dep_registry_id": "DEP-REG-001", "current_status": "BLOCKED" },
    "dshb_view": {},
    "dshe_view": {}
  },
  "calls": [ { "trace_id": "...", ... } ],
  "notes": { "summary": "..." }
}
```

### 2.1 必填顶层字段（7 项，缺任一触发 CV-03）

| # | 字段 | 类型 | 必填 | 说明 |
|---|------|------|------|------|
| 1 | `contract_version` | string | ✅ | 固定值 `EVIDENCE_CONTRACT_V1`（缺→CV-01） |
| 2 | `fingerprint` | string | ✅ | 审计指纹，唯一标识本次运行 |
| 3 | `run_id` | string | ✅ | 运行ID，格式 `YYYYMMDD_HHMMSS` |
| 4 | `session_id` | string | ✅ | 会话ID（≥8 位） |
| 5 | `caller` | string | ✅ | 生产方标识（DSHB_/DSHE_ 前缀） |
| 6 | `dshb_reuse` | bool | ✅ | L2 包必须 `false`（`true` 触发 D03.2 阻断） |
| 7 | `generated_at` | string | ✅ | ISO 8601 带时区 |

### 2.2 可选顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `total_calls` | int | 独立调用总数（应与 `calls[].length` 一致） |
| `metadata_rate` | float | 元数据完成率 `[0,1]` |
| `real_fetchable_rate` | float | 真实可取数率 `[0,1]`（唯一有效桥接率口径） |
| `bridge_rate` | float | 声明的桥接率（须与双栏口径一致，否则 D02.1/D02.3） |
| `control_check` | object | 对照组检查 `{http_status, has_nonzero_value}` |
| `script_audit` | object | 脚本审计 4 项布尔（缺→G-09 不可判定） |
| `md5_manifest` | object | 自述校验清单（缺→CV-05） |
| `dep` | object | DEP 登记关联（见 §6） |
| `claimed_completed_count` | int | 声明的 COMPLETED 数（供 LC-01 比对） |
| `notes` | object | 备注（含摘要文本，供 LC-02 术语扫描） |
| `retired` | bool | 作废标记（`true`→L2-R08 禁止复用） |
| `superseded_by` | string | 被哪个 run_id 取代 |
| `reused_from_run_id` | string | 引用已退回 run_id（触发 L2-R08 阻断） |

---

## 3. L1 证据包规范（DSHB 自测）

### 3.1 L1 特有约束

| 项 | 要求 |
|----|------|
| `call_type` | 必须为 `DSHB_L1_SELF_TEST` |
| `dshb_reuse` | 必须为 `false`（自测包本身不构成复用） |
| 职责边界 | L1 仅证明 DSHB 自身自测结果，**不构成 L2 独立校验** |

### 3.2 L1 调用条目结构

```json
{
  "trace_id": "DSHB-20261015_090001-11A2B3C4-001",
  "indicator_id": "j25_tc",
  "zhiji_short_id": "j25_tc",
  "request_payload": {
    "requested_id": "j25_tc",
    "independent": true,
    "http_url": "/api/series?id=j25_tc&start=2026-01-01&end=2026-10-15"
  },
  "response_payload": {
    "id": "j25_tc",
    "resolved_id": "j25_tc",
    "http_status": 500,
    "error": "无法识别指标来源(id前缀): j25_tc",
    "points": []
  },
  "status": "DEPENDENCY_BLOCK",
  "call_type": "DSHB_L1_SELF_TEST",
  "dep_classification": "DEPENDENCY_BLOCK",
  "dep_registry_id": "DEP-REG-001"
}
```

### 3.3 L1 判定语义

| `status` | 含义 | 条件 |
|----------|------|------|
| `COMPLETED` | 元数据 + 取数双证据齐全 | `points` 含 ≥1 非零点 |
| `INDEPENDENT_FETCH_OK` | 取数成功（L1 自测通过） | HTTP 200 + 非零点 |
| `DEPENDENCY_BLOCK` | 外部阻塞（合规） | 无外部阻塞证据则降级内部缺陷 |
| `PENDING` | 缺任一证据 | 缺 payload 或全 0 |

---

## 4. L2 证据包规范（DSHE 独立校验）

### 4.1 L2 特有约束

| 项 | 要求 |
|----|------|
| `call_type` | 必须为 `DSHE_INDEPENDENT_ZHIJI` |
| `dshb_reuse` | 必须为 `false`（**背书式引用即阻断**，D03.2） |
| 调用链独立性 | 必须为 DSHE 独立 zhiji 调用，禁止转述 DSHB 数字 |
| 职责边界 | L2 是进入 L3 预审的**唯一有效证据** |

### 4.2 L2 调用条目结构（完整字段）

```json
{
  "trace_id": "DSHE-20261015_100007-A3F2B1C4-001",
  "timestamp": "2026-10-15T10:00:08+08:00",
  "indicator_id": "i1",
  "zhiji_short_id": "a10193708",
  "request_payload": {
    "action": "search",
    "short_id": "a10193708",
    "requested_id": "i1",
    "caller": "DSHE_V86_RC2",
    "independent": true,
    "dsbh_reuse": false
  },
  "response_payload": {
    "id": "i1",
    "resolved_id": "i1",
    "short_id": "a10193708",
    "found": true,
    "series_count": 42,
    "latest_date": "2026-10-14",
    "data_points": 42,
    "points": [ { "date": "2026-10-14", "value": "12500" } ]
  },
  "status": "INDEPENDENT_FETCH_OK",
  "error": null,
  "call_type": "DSHE_INDEPENDENT_ZHIJI",
  "caller": "DSHE_V86_RC2",
  "dshb_reuse": false,
  "dep_classification": null,
  "dep_registry_id": null
}
```

### 4.3 必填调用字段（6 项，缺任一触发 CV-04）

| # | 字段 | 类型 | 说明 |
|---|------|------|------|
| 1 | `trace_id` | string | 调用追踪ID（缺→D03.1 阻断） |
| 2 | `indicator_id` | string | 业务指标ID |
| 3 | `request_payload` | object | 完整请求（含 `requested_id`） |
| 4 | `response_payload` | object | 完整响应（含 `resolved_id` + `points`） |
| 5 | `status` | string | 调用状态（见 §3.3） |
| 6 | `call_type` | string | `DSHE_INDEPENDENT_ZHIJI` |

### 4.4 字段类型约束

| 字段 | 类型 | 合法值/范围 |
|------|------|-----------|
| `trace_id` | string | 唯一，格式 `{fingerprint}-{NNN}` |
| `indicator_id` | string | 非空 |
| `zhiji_short_id` | string? | 非空（元数据证据之一） |
| `request_payload.requested_id` | string | 必须 == `indicator_id`（否则 D04.2） |
| `response_payload.resolved_id` | string | 必须 == `requested_id`（否则 D04.2 阻断） |
| `response_payload.points` | array | 每项 `{date: ISO, value: string}` |
| `response_payload.value` | string | **`≠ "0"` 且 `≠ ""` 才计有效**（D01.2） |
| `status` | enum | `COMPLETED` / `INDEPENDENT_FETCH_OK` / `DEPENDENCY_BLOCK` / `PENDING` |
| `call_type` | enum | `DSHE_INDEPENDENT_ZHIJI` / `DSHB_L1_SELF_TEST` |
| `dep_classification` | enum? | `DEPENDENCY_BLOCK` / `FULLY_AVAILABLE` / `RENDER_ANOMALY` |
| `dep_registry_id` | string? | 格式 `DEP-REG-NNN` |

---

## 5. 审计指纹与 traceID 规范

### 5.1 审计指纹（fingerprint）

```
fingerprint = "{CALLER}-{run_id}-{session_id}"
```

| 组成 | 说明 | 示例 |
|------|------|------|
| `CALLER` | 团队前缀 | `DSHE` |
| `run_id` | `YYYYMMDD_HHMMSS` | `20261015_100007` |
| `session_id` | ≥8 位会话标识 | `A3F2B1C4` |
| **完整示例** | | `DSHE-20261015_100007-A3F2B1C4` |

**唯一性铁律**：同一 fingerprint 全生命周期只出现一次；退回后重新运行必须生成**新 fingerprint**
（复用旧 run_id 触发 L2-R08 阻断）。

### 5.2 traceID

```
trace_id = "{fingerprint}-{NNN}"     # NNN 从 001 起递增
```

| 规则 | 说明 |
|------|------|
| 唯一性 | 同一包内 trace_id 不可重复（重复→D03.1 HIGH） |
| 可溯源 | 必须能反查原始 request/response payload |
| 不可伪造 | trace_id 由调用时生成，不可批量生成后填数据 |

---

## 6. DEP 登记关联规范

### 6.1 依赖 `v86_rc2_dep_registry_common_spec.md`

证据包的 `dep` 字段结构：

```json
"dep": {
  "registry": {
    "dep_registry_id": "DEP-REG-001",
    "current_status": "BLOCKED",
    "state_history": [
      { "event": "DEP_REGISTER", "status_after": "ACTIVE" },
      { "event": "DEP_BLOCK", "status_after": "BLOCKED" }
    ]
  },
  "dshb_view": { ... },
  "dshe_view": { ... }
}
```

### 6.2 6 状态与迁移（引用共用规范 §3）

`ACTIVE → BLOCKED → RECOVERY → RECOVERED → ROLLED_BACK → CLOSED`

非法迁移（DS-02）与声明错误（DS-03）**一律 CRITICAL 阻断**。

### 6.3 跨团队台账交叉比对（9 字段）

`dep_registry_id`、`current_status`、`registration_time`、`last_change_timestamp`、
`max_pause_days`、`rollback_window_min`、`risk_level`、`impact_scope`、`change_log_count`

- `current_status` 允许 DSHB↔DSHE 映射等价（`API_ERROR ≡ BLOCKED` 等）；
- 其他字段必须完全一致，不一致 → DS-05 **CRITICAL 阻断**。

---

## 7. 校验规则总表（evidence_auditor_v2.py 实现）

| 检测点 | 规则 | 触发条件 | 级别 |
|--------|------|---------|------|
| CV-01 | 契约版本存在 | 缺 `contract_version` | HIGH |
| CV-02 | 契约版本匹配 | ≠ `EVIDENCE_CONTRACT_V1` | HIGH |
| CV-03 | 顶层必填完整 | 缺 7 必填字段任一 | HIGH |
| CV-04 | 调用必填完整 | `calls[]` 缺 6 必填字段任一 | HIGH |
| CV-05 | MD5 清单存在 | 缺 `md5_manifest` | MEDIUM |
| D01.2 | 双证据取数 | COMPLETED 但无 payload 或全 0 | CRITICAL |
| D04.2 | 一致性断言 | `requested_id != resolved_id` | CRITICAL |
| D03.1 | 审计溯源 | 缺 trace_id / fingerprint | CRITICAL |
| D03.2 | 独立调用链 | `dshb_reuse=true` / calls 为空 | CRITICAL |
| L2-R08 | 退回作废 | `reused_from_run_id` 存在 | CRITICAL |

---

## 8. MD5 与审计指纹规则

### 8.1 md5_manifest 结构

```json
"md5_manifest": {
  "evidence_package": "<本包自身 md5>",
  "calls_file": "<calls 导出文件 md5, 可选>",
  "generated_by": "evidence_auditor_v2.py --check-md5"
}
```

### 8.2 校验方式

```bash
python3 evidence_auditor_v2.py --check-md5 <包.json> --expect <manifest值>
```

### 8.3 MD5 用途边界

| 用途 | 是否适用 |
|------|---------|
| 证据包完整性校验（传输/存储未被篡改） | ✅ |
| 判定证据真实性 | ❌（MD5 只能证明"是这份文件"，不能证明"数据为真"） |
| 审计追溯 | ✅（配合 fingerprint/trace_id） |

> **铁律**：MD5 通过 ≠ 审计通过。MD5 只保证包未被篡改，数据真实性须由
> D01.2/D04.5 等真实取数检测点判定。

---

## 9. 契约变更流程

### 9.1 变更分级

| 变更类型 | 版本变化 | 流程 |
|---------|---------|------|
| 字段删除/改名/类型变更 | MAJOR +1 | 三方评审 + 全体重签 |
| 必填性变更（可选↔必填） | MAJOR +1 | 三方评审 + 全体重签 |
| 新增可选字段 | 次版本 +1 | 通知三方 + 校验器适配 |
| 语义澄清（不改结构） | 次版本 +1 | HERMES 单方发布 |

### 9.2 变更流程步骤

```
1. 提出变更方提交 RFC（说明动机、影响面、向后兼容分析）
2. 三方评审（DSHB/DSHE/HERMES 各一人）
3. HERMES 更新 evidence_auditor_v2.py 校验规则 + 用例库
4. 运行 --self-test，全部通过
5. 更新本契约文档 + 版本号
6. 三方在 STATUS.md 确认签署
```

### 9.3 变更红线

1. **禁止无版本号的字段变更**——任何结构变更必须体现在 `contract_version`；
2. **禁止 MAJOR 变更未经三方评审**；
3. **禁止校验器规则与契约文档脱节**——文档改则校验器必须同步，`--self-test` 必须通过；
4. **禁止旧版本包在新契约下自动放行**——`CV-02` 会拦截版本不匹配的包，须显式迁移。

---

## 10. 三方对齐确认矩阵

| 契约项 | DSHB | DSHE | HERMES |
|--------|------|------|--------|
| L1 包结构（§3） | 生产者 | — | 校验方 |
| L2 包结构（§4） | — | 生产者 | 校验方 |
| 审计指纹格式（§5） | 遵循 | 遵循 | 校验 |
| DEP 关联（§6） | 提供 `dshb_view` | 提供 `dshe_view` | 交叉比对 |
| 校验规则（§7） | 接受 | 接受 | 维护 |
| MD5 规则（§8） | 生成 | 生成 | 校验 |
| 变更流程（§9） | 参与评审 | 参与评审 | 主导 |

---

## 11. 契约合规性自证

| 要素 | 状态 |
|------|------|
| L1 结构规范 | §3（含必填/可选/status 语义） |
| L2 结构规范 | §4（含 6 必填字段 + 类型约束表） |
| 契约元数据 | §1（版本命名 + 变更规则） |
| 审计指纹/traceID | §5（格式 + 唯一性铁律） |
| DEP 关联 | §6（引用共用规范，6 状态 + 9 字段交叉比对） |
| 校验规则 | §7（11 检测点，含级别） |
| MD5 规则 | §8（含"MD5 通过 ≠ 审计通过"边界） |
| 变更流程 | §9（分级 + 6 步骤 + 4 红线） |
| 三方对齐矩阵 | §10 |
| 校验器实现 | `evidence_auditor_v2.py`（CV-01~CV-05 已实现，23 用例自回归 PASS） |

**状态标记**：`HERMES_EVIDENCE_CONTRACT_V1_BASELINE=TRUE`
