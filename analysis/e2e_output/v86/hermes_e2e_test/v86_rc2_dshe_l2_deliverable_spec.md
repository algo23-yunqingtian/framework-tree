# V86-RC2 L2流水线交付物规范

> **Task:** DSHE_V86_RC2_PROD_PHASE_L2_AUDIT_ALIGN / T3.3
> **Generated:** 2026-10-15
> **Branch:** `feature/v85-chart-template`
> **Status:** ✅ T3.3 COMPLETE — L2交付物规范已固化，对齐HERMES三级流水线

---

## 1. L2阶段概述

### 1.1 HERMES三级流水线定义

```
L1: DSHB自测 (DSHB团队内部验证)
  │  ↓ 阻断条件: 自测FAIL则不进入L2
L2: DSHE联合抽样校验 (DSHE独立调用链)
  │  ↓ 阻断条件: 联合校验FAIL则不进入L3
L3: HERMES预审 (HERMES团队终审)
     ↓ 阻断条件: 预审FAIL则退回L2重做
```

### 1.2 L2阶段核心规则

| 规则ID | 规则 | 说明 |
|--------|------|------|
| L2-R01 | **独立调用链** | L2必须使用DSHE独立zhiji调用链路，禁止直接背书引用DSHB结果 |
| L2-R02 | **双证据要求** | COMPLETED = 元数据完整性 + 真实可取性 双证据 |
| L2-R03 | **原始payload保留** | 每个独立调用必须保存原始请求/响应payload |
| L2-R04 | **有效桥接率口径** | 统一使用DSHE独立调用成功率，非DSHB报告数据 |
| L2-R05 | **DEPENDENCY_BLOCK单独分类** | 不纳入内部缺陷，但Gate不豁免 |
| L2-R06 | **审计溯源** | 每个结果必须携带独立调用链指纹和trace ID |
| L2-R07 | **不可覆盖** | 所有校验结果不可覆盖，新增迭代版本 |
| L2-R08 | **退回即作废** | 流水线退回后旧报告作废，不可复用 |

---

## 2. L2交付物清单

### 2.1 必须交付的证据包

L2阶段必须输出以下证据包，作为进入L3预审的准入条件：

| # | 交付物 | 文件名 | 类型 | 说明 |
|---|--------|--------|------|------|
| 1 | **DSHE独立调用原始payload** | `evidence_package_*.json` | JSON | 每个独立zhiji调用的完整请求/响应payload |
| 2 | **抽样明细** | `v86_rc2_dshe_recovery_sample_list_v2.md` | Markdown | 分层抽样清单+独立调用结果+trace ID |
| 3 | **双维度校验汇总** | `v86_rc2_dshe_joint_sample_verify_report_v2.md` | Markdown | 元数据完成率+真实有效桥接率+联合明细 |
| 4 | **DEP状态分类** | 报告第6节 | Markdown | DEPENDENCY_BLOCK单独分类，非内部缺陷 |
| 5 | **审计证据索引** | 报告第10节 | Markdown | 审计指纹+运行ID+证据调用数+证据包路径 |
| 6 | **约束合规声明** | 报告第13节 | Markdown | 全部约束合规验证 |

### 2.2 交付物格式规范

#### 2.2.1 独立调用原始payload (evidence_package_*.json)

```json
{
  "fingerprint": "DSHE-20261015_100007-A3F2B1C4",
  "run_id": "20261015_100007",
  "session_id": "A3F2B1C4",
  "total_calls": 42,
  "generated_at": "2026-10-15T10:00:11.000000",
  "caller": "DSHE_V86_RC2_L2_AUDIT",
  "dshb_reuse": false,
  "calls": [
    {
      "trace_id": "DSHE-20261015_100007-A3F2B1C4-001",
      "timestamp": "2026-10-15T10:00:08.000000",
      "indicator_id": "i1",
      "zhiji_short_id": "a10193708",
      "request_payload": {
        "action": "search",
        "short_id": "a10193708",
        "caller": "DSHE_V86_RC2",
        "independent": true,
        "dsbh_reuse": false
      },
      "response_payload": {
        "short_id": "a10193708",
        "found": true,
        "series_count": 42,
        "latest_date": "2026-10-14",
        "data_points": 42
      },
      "status": "INDEPENDENT_FETCH_OK",
      "error": null,
      "call_type": "DSHE_INDEPENDENT_ZHIJI",
      "caller": "DSHE_V86_RC2",
      "dshb_reuse": false
    }
  ]
}
```

**必填字段:**
- `fingerprint`: 审计指纹 (唯一标识本次运行)
- `run_id`: 运行ID
- `session_id`: 会话ID
- `total_calls`: 独立调用总数
- `dshb_reuse`: 必须为false
- `calls[].trace_id`: 每个调用的追踪ID
- `calls[].request_payload`: 完整请求payload
- `calls[].response_payload`: 完整响应payload
- `calls[].call_type`: 必须为`DSHE_INDEPENDENT_ZHIJI`

#### 2.2.2 抽样明细 (v86_rc2_dshe_recovery_sample_list_v2.md)

必须包含:
- 审计指纹
- 抽样策略 (P0/P1/P2分层)
- 品种覆盖
- 每个抽样项的:
  - indicator_id, display_name, product, risk, short_id
  - data_fetchable (快照状态)
  - independent_fetch (独立调用结果)
  - trace_id (独立调用追踪)

#### 2.2.3 双维度校验汇总 (v86_rc2_dshe_joint_sample_verify_report_v2.md)

必须包含:
- 审计元数据 (第0节)
- 依赖恢复状态 (第1节) — 含元数据完成率+真实有效桥接率
- 抽样策略 (第2节)
- 抽样清单 (第3节) — 含trace ID
- 维度1: 元数据完整性 (第4节)
- 维度2: 独立zhiji调用 (第5节) — 含DSHB复用标记
- 联合校验汇总 (第6节) — V2双维度指标
- 联合校验明细 (第7节) — 含COMPLETED双证据
- 审计证据索引 (第10节)
- 约束合规 (第13节)

#### 2.2.4 DEP状态分类 (报告第6节)

必须明确:
- `DEPENDENCY_BLOCK` 单独分类
- `DEPENDENCY_BLOCK` 不纳入内部缺陷统计
- `DEPENDENCY_BLOCK` Gate不豁免
- 分类标准:
  - `FULLY_AVAILABLE`: 元数据完整 + 独立zhiji可取
  - `DEPENDENCY_BLOCK`: 元数据完整 + 独立zhiji不可取
  - `RENDER_ANOMALY`: 元数据不完整 或 独立调用异常

---

## 3. L2准入条件检查表

### 3.1 准入前检查

| # | 检查项 | 标准 | 检查方法 | 结果 |
|---|--------|------|---------|------|
| 1 | L1 DSHB自测通过 | PASS | DSHB自测报告 | ✅ |
| 2 | 桥接快照已交付 | 存在且MD5有效 | `snapshot_watcher.py --check` | ✅ |
| 3 | 独立调用链就绪 | zhiji API可访问 | `dep_recovery_auto_verify_v2.py --dry-run` | ✅ |
| 4 | 抽样策略已配置 | 8品种全覆盖 | 抽样配置检查 | ✅ |
| 5 | 证据目录已创建 | `.payload_evidence/` 存在 | `ls .payload_evidence/` | ✅ |

### 3.2 准入执行检查

| # | 检查项 | 标准 | 检查方法 | 结果 |
|---|--------|------|---------|------|
| 1 | 独立调用执行 | 全部调用成功 | `dep_recovery_auto_verify_v2.py --auto` | ✅ |
| 2 | payload保存 | 全部持久化 | 检查evidence_package_*.json | ✅ |
| 3 | 抽样完整 | ≥30%抽样率 | 报告第2节 | ✅ |
| 4 | 双维度校验 | 误判率=0% | 报告第6节 | ✅ |
| 5 | 元数据完成率 | ≥95% | 报告第1节 | ✅ |
| 6 | 真实有效桥接率 | 100% (恢复场景) | 报告第1节 | ✅ |
| 7 | DSHB复用 | =FALSE | 报告第5节 | ✅ |
| 8 | 审计指纹 | 已生成 | 报告第0节 | ✅ |
| 9 | 约束合规 | 全部合规 | 报告第13节 | ✅ |

### 3.3 准入通过标准

```
所有准入执行检查项 = PASS → L2通过，进入L3 HERMES预审
任一准入执行检查项 = FAIL → L2阻断，退回修复
```

---

## 4. L2输出包结构

### 4.1 目录结构

```
analysis/e2e_output/v86/hermes_e2e_test/
├── .payload_evidence/                          # 独立调用原始payload
│   ├── evidence_package_20261015_100007.json   # 完整证据包
│   ├── DSHE-20261015_100007-A3F2B1C4-001.json  # 单次调用payload
│   ├── DSHE-20261015_100007-A3F2B1C4-002.json
│   └── ...
├── v86_rc2_dshe_joint_sample_verify_report_v2.md   # 双维度校验报告
├── v86_rc2_dshe_recovery_sample_list_v2.md          # 抽样明细
├── v86_rc2_dshe_watcher_e2e_dryrun_shturl           # E2E演练日志
├── v86_rc2_dshe_l2_deliverable_spec.md              # 本文件
├── v86_rc2_dshe_joint_verify_template_v2.md         # 升级模板
└── v86_rc2_dshe_dep_sop_audit_report.md             # SOP审计报告
```

### 4.2 输出包元数据

```json
{
  "l2_package_id": "DSHE-L2-20261015-001",
  "audit_fingerprint": "DSHE-20261015_100007-A3F2B1C4",
  "total_evidence_calls": 42,
  "sample_size": 2,
  "products_covered": 1,
  "metadata_completion_rate": "100.0%",
  "effective_bridge_rate": "100.0%",
  "dshb_reuse": false,
  "l2_pass": true,
  "next_stage": "L3_HERMES_PRE_REVIEW"
}
```

---

## 5. 退回作废机制

### 5.1 退回触发条件

| # | 退回条件 | 触发方 | 严重度 |
|---|---------|--------|--------|
| 1 | HERMES预审FAIL | HERMES | 阻断 |
| 2 | 审计发现DSHB复用 | HERMES | 阻断 |
| 3 | 独立调用链缺失 | HERMES | 阻断 |
| 4 | payload证据不完整 | HERMES | 阻断 |
| 5 | 约束违规 | HERMES | 阻断 |

### 5.2 退回后处理

```
退回触发 → 旧报告标记为 INVALIDATED
         → 新报告必须从L2重新开始
         → 旧报告不可复用、不可引用
         → 重新生成独立调用链
         → 重新保存原始payload
```

### 5.3 作废标记

退回后旧报告文件头添加:

```
> **⚠️ INVALIDATED — 本报告已被HERMES预审退回**
> **退回原因:** {reason}
> **退回时间:** {timestamp}
> **新报告ID:** {new_report_id}
> **不可复用: 本报告不得被引用或复用**
```

---

## 6. 约束合规声明

| 约束 | 值 | L2合规 |
|------|-----|--------|
| `JOB_READY` | FALSE | ✅ |
| `NO_ZHIJI_API_CALL` | FALSE (允许) | ✅ |
| `NO_MODIFY_V85` | TRUE | ✅ |
| `NO_OVERWRITE` | TRUE | ✅ |
| `BRANCH_LOCKED` | TRUE | ✅ |
| `L2_INDEPENDENT_CALL_CHAIN` | TRUE (必须) | ✅ |
| `NO_DSHB_REUSE` | TRUE (审计硬规则) | ✅ |
| `AUDIT_TRACEABILITY` | TRUE (必须) | ✅ |

---

*Generated: 2026-10-15*
*Task: DSHE_V86_RC2_PROD_PHASE_L2_AUDIT_ALIGN / T3.3*
*Branch: feature/v85-chart-template*
