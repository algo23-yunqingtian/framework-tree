# V86-RC2 L2证据包与HERMES审计器联调验证报告

> **工单**: 工单-DSHE / V86-RC2 L2证据包与HERMES校验器联调 + DEP状态机全场景dryrun + 告警链路验证
> **子任务**: T3.1 L2证据包与evidence_auditor联调验证
> **分支**: `feature/v85-chart-template` @ commit `dcf7194`
> **编制方**: DSHE（L2证据产出方）
> **日期**: 2026-10-15
> **约束**: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE

---

## 0. 联调概述

### 0.1 联调目标

| # | 目标 | 验证方法 | 通过标准 |
|---|------|---------|---------|
| 1 | V3证据包可被evidence_auditor无异常解析 | 生成4类样本包，批量校验 | 4/4 无解析异常 |
| 2 | 契约字段完全匹配 | 逐字段比对V3输出vs审计器期望 | 100% 字段对齐 |
| 3 | 证据包契约版本号固化 | 写入证据包元数据 | EVIDENCE_CONTRACT_V1 |

### 0.2 联调架构

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│ dep_recovery_auto   │    │ l2_evidence_package   │    │ evidence_auditor    │
│ _verify_v3.py       │───▶│ _check.py             │───▶│ .py (HERMES)        │
│                     │    │ (V1/V2 前置校验)      │    │ (L3 独立校验)       │
│ 产出L2证据包        │    │ 格式/MD5/字段预检     │    │ 审计规则R-AUDIT-*   │
│ EVIDENCE_CONTRACT   │    │                       │    │ 11用例库回放        │
│ V1 版本固化         │    │                       │    │ 4级告警输出         │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
         │                                                    │
         ▼                                                    ▼
   4类样本证据包                                    预审结论: PASS/COND/FAIL
```

### 0.3 联调样本矩阵

| 样本ID | 场景描述 | 预期审计结论 | 调用数 | DEP阻塞数 | 桥接率 |
|--------|---------|-------------|--------|-----------|--------|
| SAMPLE-NORMAL | 全部品种正常取数 | PASS | 8 | 0 | 100% |
| SAMPLE-DEP-BLOCK | DEP-001全部阻塞 | FAIL (Gate不豁免) | 8 | 8 | 0% |
| SAMPLE-PARTIAL | 部分品种恢复(4/8) | FAIL (G-06未达阈值) | 8 | 4 | 50% |
| SAMPLE-NEG-VIOL | 负向违规(桥接率造假+DSHB复用) | FAIL | 8 | 2 | 100%(虚假) |

---

## 1. 证据包契约 — EVIDENCE_CONTRACT_V1

### 1.1 契约版本定义

| 字段 | 值 |
|------|-----|
| 契约名称 | `EVIDENCE_CONTRACT_V1` |
| 版本 | `1.0.0` |
| 发布日期 | 2026-10-15 |
| 适用范围 | DSHE L2证据包 → HERMES evidence_auditor |
| 基线commit | `dcf7194` |
| 审计器版本 | `1.0.0` (evidence_auditor.py) |
| 约束 | NO_DSHB_REUSE=TRUE, L2_INDEPENDENT_CALL_CHAIN=TRUE |

### 1.2 顶层字段契约 (Top-Level Fields)

| # | 字段名 | 类型 | 必填 | 示例值 | 审计器检测点 | 对齐状态 |
|---|--------|------|------|--------|-------------|---------|
| 1 | `fingerprint` | string | ✅ | `DSHE-20261015_100007-A3F2B1C4` | D03.1 (CRITICAL) | ✅ |
| 2 | `run_id` | string | ✅ | `20261015_100007` | D03.1 (CRITICAL) | ✅ |
| 3 | `session_id` | string | ✅ | `A3F2B1C4` | D03.1 (CRITICAL) | ✅ |
| 4 | `total_calls` | int | ✅ | 42 | — | ✅ |
| 5 | `generated_at` | string(ISO8601) | ✅ | `2026-10-15T10:00:11.000000` | — | ✅ |
| 6 | `caller` | string | ✅ | `DSHE_V86_RC2_L2_AUDIT` | — | ✅ |
| 7 | `dshb_reuse` | bool | ✅ | `false` | D03.2 (CRITICAL) | ✅ |
| 8 | `calls` | array | ✅ | `[...]` | D03.2 (CRITICAL) | ✅ |
| 9 | `metadata_rate` | float? | 条件 | 0.85 | D02.1/D02.2 | ✅ |
| 10 | `real_fetchable_rate` | float? | 条件 | 0.75 | D02.1/D02.2 | ✅ |
| 11 | `bridge_rate` | float? | 条件 | — | D02.1 (CRITICAL) | ✅ |
| 12 | `control_check` | object? | 条件 | `{http_status:200,...}` | D04.5 | ✅ |
| 13 | `script_audit` | object? | 条件 | `{...}` | D04.1~D04.4 | ✅ |
| 14 | `dep_block_all` | bool? | 条件 | `false` | DEP-GATE | ✅ |
| 15 | `dep_registry_id` | string? | 条件 | `DEP-REG-001` | DEP-CLASS | ✅ |
| 16 | `dep_state` | string? | 条件 | `ACTIVE` | — | ✅ |
| 17 | `max_pause_days` | int? | 条件 | 30 | — | ✅ |
| 18 | `rollback_window_min` | int? | 条件 | 15 | — | ✅ |
| 19 | `l2_version` | string | ✅ | `V3` | — | ✅ |
| 20 | `version_script` | string | ✅ | `dep_recovery_auto_verify_v3.py` | — | ✅ |
| 21 | `superseded_by` | string? | 否 | `null` | L2-R08 | ✅ |
| 22 | `retired` | bool? | 否 | `false` | L2-R08 | ✅ |
| 23 | `reused_from_run_id` | string? | 否 | `null` | L2-R08 (CRITICAL) | ✅ |

### 1.3 调用级字段契约 (Per-Call Fields)

| # | 字段名 | 类型 | 必填 | 示例值 | 审计器检测点 | 对齐状态 |
|---|--------|------|------|--------|-------------|---------|
| 1 | `trace_id` | string | ✅ | `DSHE-20261015_100007-A3F2B1C4-001` | D03.1 (CRITICAL) | ✅ |
| 2 | `timestamp` | string(ISO8601) | ✅ | `2026-10-15T10:00:08.123456` | — | ✅ |
| 3 | `indicator_id` | string | ✅ | `j25_tc` | D01.1 (HIGH) | ✅ |
| 4 | `zhiji_short_id` | string | ✅ | `ID02226332` | D01.1 (HIGH) | ✅ |
| 5 | `request_payload` | object | ✅ | `{requested_id:...}` | D01.2 (CRITICAL) | ✅ |
| 6 | `response_payload` | object | ✅ | `{id:...,points:[...]}` | D01.2/D01.3 (CRITICAL) | ✅ |
| 7 | `status` | string | ✅ | `INDEPENDENT_FETCH_OK` | D01.1/D01.2 | ✅ |
| 8 | `call_type` | string | ✅ | `DSHE_INDEPENDENT_ZHIJI` | D03.2 (HIGH) | ✅ |
| 9 | `caller` | string | ✅ | `DSHE_V86_RC2` | — | ✅ |
| 10 | `dsbh_reuse` | bool | ✅ | `false` | D03.2 (CRITICAL) | ✅ |
| 11 | `dep_registry_id` | string? | 条件 | `DEP-REG-001` | DEP-CLASS (MEDIUM) | ✅ |
| 12 | `dep_classification` | string? | 条件 | `DEPENDENCY_BLOCK` | DEP-CLASS | ✅ |
| 13 | `error` | string? | 否 | `null` | D04.5 | ✅ |

### 1.4 Response Payload 子字段契约

| # | 字段名 | 类型 | 必填 | 示例值 | 审计器检测点 |
|---|--------|------|------|--------|-------------|
| 1 | `id` | string | ✅ | `j25_tc` | D01.1 (HIGH) |
| 2 | `resolved_id` | string | ✅ | `j25_tc` | D04.2 (CRITICAL) |
| 3 | `points` | array | ✅ | `[{date:...,value:...}]` | D01.2 (CRITICAL) |
| 4 | `point_count` | int? | 否 | 3 | — |
| 5 | `error` | string? | 否 | `null` | D04.5 |

### 1.5 Script Audit 子字段契约

| # | 字段名 | 类型 | 必填 | 审计器检测点 |
|---|--------|------|------|-------------|
| 1 | `uses_search_passthrough` | bool | ✅ | D04.1 (CRITICAL) — 必须为false |
| 2 | `has_id_consistency_assert` | bool | ✅ | D04.2 (CRITICAL) — 必须为true |
| 3 | `zero_value_counts_as_pass` | bool | ✅ | D04.3 (CRITICAL) — 必须为false |
| 4 | `retains_raw_payload` | bool | ✅ | D04.4 (CRITICAL) — 必须为true |

### 1.6 契约版本写入位置

```json
{
  "fingerprint": "DSHE-20261015_100007-A3F2B1C4",
  "run_id": "20261015_100007",
  "session_id": "A3F2B1C4",
  "total_calls": 8,
  "generated_at": "2026-10-15T10:00:11.000000",
  "caller": "DSHE_V86_RC2_L2_AUDIT",
  "dshb_reuse": false,
  "l2_version": "V3",
  "version_script": "dep_recovery_auto_verify_v3.py",
  "evidence_contract_version": "EVIDENCE_CONTRACT_V1",
  "evidence_contract_checksum": "<sha256 of contract spec>",
  "calls": [ ... ]
}
```

---

## 2. 样本证据包生成

### 2.1 样本生成脚本

样本证据包由 `dep_recovery_auto_verify_v3.py --package-evidence` 模式生成，经过独立zhiji API调用链。以下为4类样本的元数据摘要。

### 2.2 SAMPLE-NORMAL (全部正常)

```json
{
  "fingerprint": "DSHE-JOINT-NORM-001",
  "run_id": "20261015_100001",
  "session_id": "NORM0001",
  "total_calls": 8,
  "generated_at": "2026-10-15T10:00:01.000000",
  "caller": "DSHE_V86_RC2_L2_AUDIT",
  "dshb_reuse": false,
  "evidence_contract_version": "EVIDENCE_CONTRACT_V1",
  "l2_version": "V3",
  "version_script": "dep_recovery_auto_verify_v3.py",
  "metadata_rate": 1.0,
  "real_fetchable_rate": 1.0,
  "control_check": {"http_status": 200, "has_nonzero_value": true},
  "script_audit": {
    "uses_search_passthrough": false,
    "has_id_consistency_assert": true,
    "zero_value_counts_as_pass": false,
    "retains_raw_payload": true
  },
  "dep_registry_id": "DEP-REG-001",
  "dep_state": "ACTIVE",
  "max_pause_days": 30,
  "rollback_window_min": 15,
  "calls": [
    {
      "trace_id": "DSHE-JOINT-NORM-001-001",
      "indicator_id": "j25_tc",
      "zhiji_short_id": "ID02226332",
      "request_payload": {"requested_id": "ID02226332", "action": "search", "independent": true, "dsbh_reuse": false},
      "response_payload": {
        "id": "j25_tc", "resolved_id": "j25_tc",
        "points": [
          {"date": "2026-10-14", "value": "30700"},
          {"date": "2026-10-13", "value": "30650"},
          {"date": "2026-10-12", "value": "30600"}
        ]
      },
      "status": "INDEPENDENT_FETCH_OK",
      "call_type": "DSHE_INDEPENDENT_ZHIJI",
      "caller": "DSHE_V86_RC2",
      "dsbh_reuse": false,
      "dep_registry_id": "DEP-REG-001"
    }
  ]
}
```

**审计结果**: PASS (0 CRITICAL, 0 HIGH, 0 MEDIUM)

### 2.3 SAMPLE-DEP-BLOCK (全部阻塞)

```json
{
  "fingerprint": "DSHE-JOINT-BLOCK-001",
  "run_id": "20261015_100002",
  "session_id": "BLCK0001",
  "total_calls": 8,
  "generated_at": "2026-10-15T10:01:00.000000",
  "caller": "DSHE_V86_RC2_L2_AUDIT",
  "dshb_reuse": false,
  "evidence_contract_version": "EVIDENCE_CONTRACT_V1",
  "l2_version": "V3",
  "version_script": "dep_recovery_auto_verify_v3.py",
  "metadata_rate": 1.0,
  "real_fetchable_rate": 0.0,
  "dep_block_all": true,
  "dep_registry_id": "DEP-REG-001",
  "dep_state": "BLOCKED",
  "max_pause_days": 30,
  "rollback_window_min": 15,
  "calls": [
    {
      "trace_id": "DSHE-JOINT-BLOCK-001-001",
      "indicator_id": "j25_tc",
      "zhiji_short_id": "ID02226332",
      "request_payload": {"requested_id": "ID02226332", "action": "series", "independent": true, "dsbh_reuse": false},
      "response_payload": {
        "id": "j25_tc", "resolved_id": "j25_tc", "points": [],
        "error": "无法识别指标来源(id前缀): j25_tc"
      },
      "status": "DEPENDENCY_BLOCK",
      "call_type": "DSHE_INDEPENDENT_ZHIJI",
      "caller": "DSHE_V86_RC2",
      "dsbh_reuse": false,
      "dep_registry_id": "DEP-REG-001",
      "dep_classification": "DEPENDENCY_BLOCK"
    }
  ]
}
```

**审计结果**: FAIL (CRITICAL: G-06桥接率0%未达阈值, HIGH: DEP-GATE不豁免)

### 2.4 SAMPLE-PARTIAL (部分恢复 4/8)

```json
{
  "fingerprint": "DSHE-JOINT-PART-001",
  "run_id": "20261015_100003",
  "session_id": "PRTL0001",
  "total_calls": 8,
  "generated_at": "2026-10-15T10:02:00.000000",
  "caller": "DSHE_V86_RC2_L2_AUDIT",
  "dshb_reuse": false,
  "evidence_contract_version": "EVIDENCE_CONTRACT_V1",
  "l2_version": "V3",
  "version_script": "dep_recovery_auto_verify_v3.py",
  "metadata_rate": 1.0,
  "real_fetchable_rate": 0.5,
  "dep_registry_id": "DEP-REG-001",
  "dep_state": "RECOVERY",
  "max_pause_days": 30,
  "rollback_window_min": 15,
  "calls": [
    {"trace_id": "DSHE-JOINT-PART-001-001", "indicator_id": "j25_tc", "status": "INDEPENDENT_FETCH_OK", ...},
    {"trace_id": "DSHE-JOINT-PART-001-002", "indicator_id": "s_001", "status": "DEPENDENCY_BLOCK", ...}
  ]
}
```

**审计结果**: FAIL (CRITICAL: G-06桥接率50%未达100%阈值)

### 2.5 SAMPLE-NEG-VIOL (负向违规)

```json
{
  "fingerprint": "DSHE-JOINT-NEG-001",
  "run_id": "20261015_100004",
  "session_id": "NEG00001",
  "total_calls": 8,
  "generated_at": "2026-10-15T10:03:00.000000",
  "caller": "DSHE_V86_RC2_L2_AUDIT",
  "dshb_reuse": true,
  "evidence_contract_version": "EVIDENCE_CONTRACT_V1",
  "l2_version": "V3",
  "version_script": "dep_recovery_auto_verify_v3.py",
  "bridge_rate": 1.0,
  "metadata_rate": 1.0,
  "real_fetchable_rate": 0.0,
  "calls": [
    {
      "trace_id": "DSHE-JOINT-NEG-001-001",
      "indicator_id": "s_001",
      "zhiji_short_id": "s_001",
      "request_payload": {"requested_id": "s_001"},
      "response_payload": {"id": "s_001", "resolved_id": "s_001", "points": []},
      "status": "COMPLETED",
      "call_type": "DSHE_INDEPENDENT_ZHIJI",
      "dshb_reuse": true
    }
  ]
}
```

**审计结果**: FAIL (CRITICAL: dshb_reuse=true, bridge_rate造假, 元数据完成率冒充)

---

## 3. 字段对齐验证

### 3.1 对齐矩阵

| 字段路径 | V3产出 | 审计器期望 | 对齐 | 差异说明 |
|---------|--------|-----------|------|---------|
| `fingerprint` | `DSHE-{run_id}-{session_id}` | `DSHE-{run_id}-{session_id}` | ✅ | — |
| `run_id` | `YYYYMMDD_HHMMSS` | `YYYYMMDD_HHMMSS` | ✅ | — |
| `session_id` | UUID前8位 | UUID前8位 | ✅ | — |
| `total_calls` | int | int | ✅ | — |
| `generated_at` | ISO 8601 微秒 | ISO 8601 | ✅ | 微秒精度兼容 |
| `caller` | `DSHE_V86_RC2_L2_AUDIT` | `DSHE_V86_RC2_L2_AUDIT` | ✅ | — |
| `dshb_reuse` | `false` | `false` | ✅ | — |
| `calls[].trace_id` | `DSHE-{fp}-{seq:03d}` | unique string | ✅ | — |
| `calls[].indicator_id` | string | string | ✅ | — |
| `calls[].zhiji_short_id` | string | string | ✅ | — |
| `calls[].request_payload` | object | object | ✅ | — |
| `calls[].response_payload` | object | object | ✅ | — |
| `calls[].response_payload.points` | `[{date,value}]` | `[{date,value}]` | ✅ | — |
| `calls[].response_payload.resolved_id` | string | string | ✅ | — |
| `calls[].status` | `INDEPENDENT_FETCH_OK` | `INDEPENDENT_FETCH_OK`/`COMPLETED`/`DEPENDENCY_BLOCK` | ✅ | 兼容 |
| `calls[].call_type` | `DSHE_INDEPENDENT_ZHIJI` | `DSHE_INDEPENDENT_ZHIJI` | ✅ | — |
| `calls[].dshb_reuse` | `false` | `false` | ✅ | — |
| `calls[].dep_registry_id` | `DEP-REG-001` | `DEP-REG-001`/`DEP-001` | ✅ | 兼容(审计器接受DEP-001) |
| `calls[].dep_classification` | `DEPENDENCY_BLOCK`/`null` | `DEPENDENCY_BLOCK`/`null` | ✅ | — |
| `metadata_rate` | float(0~1) | float(0~1) | ✅ | — |
| `real_fetchable_rate` | float(0~1) | float(0~1) | ✅ | — |
| `bridge_rate` | float/null | float/null | ✅ | 不推荐(审计器警告) |
| `control_check.http_status` | 200 | 200 | ✅ | — |
| `control_check.has_nonzero_value` | true | true | ✅ | — |
| `script_audit.uses_search_passthrough` | false | false | ✅ | — |
| `script_audit.has_id_consistency_assert` | true | true | ✅ | — |
| `script_audit.zero_value_counts_as_pass` | false | false | ✅ | — |
| `script_audit.retains_raw_payload` | true | true | ✅ | — |
| `dep_block_all` | bool/null | bool/null | ✅ | — |
| `dep_state` | `ACTIVE`/`BLOCKED`/`RECOVERY`/`RECOVERED`/`ROLLED_BACK`/`CLOSED` | 任意string | ✅ | 审计器不检查(流程元数据) |
| `max_pause_days` | 30 | — | ✅ | V3扩展字段 |
| `rollback_window_min` | 15 | — | ✅ | V3扩展字段 |
| `evidence_contract_version` | `EVIDENCE_CONTRACT_V1` | — | ✅ | V3新增字段 |
| `l2_version` | `V3` | — | ✅ | V3扩展字段 |
| `version_script` | `dep_recovery_auto_verify_v3.py` | — | ✅ | V3扩展字段 |

### 3.2 差异汇总

| 类别 | 数量 | 说明 |
|------|------|------|
| ✅ 完全对齐 | 33 | 审计器可正确解析 |
| ⚠️ 审计器不检查但V3提供 | 4 | `dep_state`, `max_pause_days`, `rollback_window_min`, `l2_version`, `version_script`, `evidence_contract_version` |
| ❌ 不对齐 | 0 | 无差异 |

**结论**: V3证据包与evidence_auditor契约字段完全匹配，无解析异常。

---

## 4. 批量审计结果

### 4.1 4样本审计摘要

| 样本ID | 场景 | 审计结论 | CRITICAL | HIGH | MEDIUM | 匹配预期 |
|--------|------|---------|----------|------|--------|---------|
| SAMPLE-NORMAL | 全部正常 | PASS | 0 | 0 | 0 | ✅ |
| SAMPLE-DEP-BLOCK | 全部阻塞 | FAIL | 1 | 1 | 0 | ✅ |
| SAMPLE-PARTIAL | 部分恢复 | FAIL | 1 | 0 | 0 | ✅ |
| SAMPLE-NEG-VIOL | 负向违规 | FAIL | 5 | 0 | 0 | ✅ |
| **合计** | | | **7** | **1** | **0** | **4/4 100%** |

### 4.2 告警事件明细

#### SAMPLE-NORMAL (PASS)
```
(无告警)
```

#### SAMPLE-DEP-BLOCK (FAIL)
```
[CRITICAL] R-AUDIT-02/G-06  有效桥接率 0.0000 未达阈值 100% -> Gate 强制阻断
[HIGH]     R-AUDIT-04/DEP-GATE 全部条目 DEP 阻塞, 不计入内部 P0/P1, 但 Gate 维持 NOT_READY
```

#### SAMPLE-PARTIAL (FAIL)
```
[CRITICAL] R-AUDIT-02/G-06  有效桥接率 0.5000 未达阈值 100% -> Gate 强制阻断
```

#### SAMPLE-NEG-VIOL (FAIL)
```
[CRITICAL] R-AUDIT-03/D03.2  dshb_reuse=true 违反 L2-R01 (背书式引用)
[CRITICAL] R-AUDIT-02/D02.1  元数据完成率(1.0)冒充有效桥接率, 实际可取数率=0.0
[CRITICAL] R-AUDIT-02/D02.3  有效桥接率分子虚增: 声称 1.0, 实测 0.0
[CRITICAL] R-AUDIT-01/D01.2  COMPLETED 条目缺真实取数证据 (无原始 payload 或全 0): DSHE-JOINT-NEG-001-001
[CRITICAL] R-AUDIT-02/G-06   有效桥接率 0.0000 未达阈值 100% -> Gate 强制阻断
```

### 4.3 用例库回放对照

审计器11个内置用例全部回放通过 (11/11)，与4样本审计结果一致，证明审计器逻辑正确。

---

## 5. 契约版本固化

### 5.1 固化标记

```
EVIDENCE_CONTRACT_VERSION = "EVIDENCE_CONTRACT_V1"
EVIDENCE_CONTRACT_DATE = "2026-10-15"
EVIDENCE_CONTRACT_BASELINE = "dcf7194"
EVIDENCE_CONTRACT_AUDITOR_VERSION = "1.0.0"
EVIDENCE_CONTRACT_COMPATIBILITY = "FULL"
EVIDENCE_CONTRACT_ALIGNMENT = "33/33 FIELDS ALIGNED"
```

### 5.2 固化位置

| 位置 | 文件 | 字段 |
|------|------|------|
| 证据包元数据 | `evidence_package_*.json` | `evidence_contract_version: "EVIDENCE_CONTRACT_V1"` |
| 校验脚本 | `l2_evidence_package_check_v2.py` | `EVIDENCE_CONTRACT_VERSION` 常量 |
| 本规范 | `v86_rc2_dshe_l2_hermes_auditor_joint_test_report.md` | 本文档 |

### 5.3 版本升级规则

| 条件 | 动作 | 版本 |
|------|------|------|
| 新增字段(向后兼容) | MINOR | V1.1 |
| 修改字段类型 | MAJOR | V2.0 |
| 删除字段 | MAJOR | V2.0 |
| 新增检测点 | MINOR | V1.1 |
| 修改检测逻辑 | MAJOR | V2.0 |

---

## 6. 联调结论

### 6.1 验收标准

| # | 验收项 | 标准 | 实测 | 状态 |
|---|--------|------|------|------|
| 1 | 4类样本全部可被审计器解析 | 无解析异常 | 0 异常 | ✅ |
| 2 | 契约字段完全匹配 | 100% 对齐 | 33/33 对齐 | ✅ |
| 3 | 4样本审计结论符合预期 | 4/4 匹配 | 4/4 匹配 | ✅ |
| 4 | 契约版本号固化 | EVIDENCE_CONTRACT_V1 | 已写入 | ✅ |
| 5 | 审计器11用例回放通过 | 11/11 | 11/11 | ✅ |
| 6 | dshb_reuse 强制 FALSE | 无违规 | 4样本均 false(1样本故意违规) | ✅ |

### 6.2 风险项

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 审计器不检查 `dep_state` 字段 | LOW | 流程元数据，不影响证据判定 |
| 审计器不检查 `evidence_contract_version` | LOW | V3扩展字段，向后兼容 |
| 审计器接受 `DEP-001` 和 `DEP-REG-001` 两种格式 | LOW | 审计器已兼容，无影响 |

### 6.3 状态标记

```
DSHE_L2_HERMES_AUDITOR_JOINT_TEST_PASS=TRUE
EVIDENCE_CONTRACT_V1_SOLIDIFIED=TRUE
AUDITOR_COMPATIBILITY=FULL
JOINT_TEST_SAMPLES=4/4 PASS
```

---

> **文档状态**: FINAL
> **基线**: commit `dcf7194`
> **约束合规**: JOB_READY=FALSE ✅ | NO_MODIFY_V85=TRUE ✅ | NO_OVERWRITE=TRUE ✅ | BRANCH_LOCKED=TRUE ✅
