# V86规则任务接入后端API适配文档

> 任务: DSHB_V86_RULE_ENGINE_PREDEV_AND_BL_REGRESSION_TEST · T2.5
> 分支: feature/v85-chart-template
> 对接: E的V86 task_api_design (commit bcd64dd, b7c62ba)
> 前置: v86_task_api_design.md + v86_backend_schema_design.md
> 约束: NO_ZHIJI_API_CALL=TRUE, V85核心规则只读, 仅新增V86原型代码

---

## 一、适配总览

### 1.1 目标

本文档定义V86规则引擎与后端任务调度API的适配契约，包括:
1. 规则任务入参规范 (task payload)
2. 规则任务出参规范 (task result)
3. 错误码约定 (error codes)
4. 任务类型映射 (task_type mapping)
5. 与E后端task_api设计的对齐关系

### 1.2 与E后端对齐

| 维度 | E后端设计 | V86规则适配 |
|------|-----------|------------|
| 任务接口 | POST /api/v1/tasks | 复用 |
| task_type | dshb_rule_eval | ✅ 对齐 |
| 角色 | task_submit / task_read / task_admin | ✅ 复用 |
| 状态机 | queued→running→succeeded/failed/cancelled/timeout | ✅ 复用 |
| 幂等 | X-Idempotency-Key | ✅ 复用 |
| 回调 | callback_url | ✅ 复用 |

---

## 二、任务类型定义

### 2.1 V86规则任务类型

| task_type | 说明 | 对应E设计 |
|-----------|------|----------|
| `dshb_rule_eval` | 规则计算：对一批模板/指标组合跑黑名单判定 | ✅ 对齐 |
| `dshb_rule_regression` | 规则回归测试：执行完整回归测试套件 | 🆕 新增 |
| `dshb_rule_boundary` | 边界测试：执行24+条边界用例 | 🆕 新增 |
| `dshb_rule_pdf_fix_check` | PDF数据缺失检测：扫描matched_name空值 | 🆕 新增 |
| `dshb_rule_compare_v85` | V85/V86对比：批量计算指标差异 | 🆕 新增 |

### 2.2 任务优先级建议

| task_type | 建议priority | 说明 |
|-----------|-------------|------|
| dshb_rule_eval | 5 (默认) | 标准评估任务 |
| dshb_rule_regression | 3 (高) | 回归测试需优先执行 |
| dshb_rule_boundary | 4 | 边界测试 |
| dshb_rule_pdf_fix_check | 2 (最高) | 数据缺失检测优先级最高 |
| dshb_rule_compare_v85 | 6 | 对比分析，可延后 |

---

## 三、入参规范 (Task Payload)

### 3.1 dshb_rule_eval — 规则计算

```json
{
  "task_type": "dshb_rule_eval",
  "version_tag": "v86.0-alpha",
  "priority": 5,
  "payload": {
    "template_ids": ["TPL-LC-054", "TPL-NI-008", "THS-NI-2.3"],
    "blacklist_version": "v86-p0-proto",
    "rules_subset": ["BL-009a", "BL-026", "BL-012", "BL-022", "BL-020", "BL-021"],
    "include_complementary": true,
    "pdf_fix_simulation": false,
    "variety_aware": true,
    "bidirectional_check": true,
    "output_format": "csv",
    "include_details": true
  },
  "callback_url": "https://portal.internal/callbacks/task",
  "ttl_seconds": 3600
}
```

**Payload字段说明:**

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| template_ids | string[] | 是 | — | 模板ID列表 |
| blacklist_version | string | 否 | "v86-p0-proto" | 规则集版本 |
| rules_subset | string[] | 否 | null (全部) | 仅运行指定规则子集 |
| include_complementary | bool | 否 | true | 包含互补规则(BL-009, BL-018, BL-018a等) |
| pdf_fix_simulation | bool | 否 | false | 启用PDF修复模拟 |
| variety_aware | bool | 否 | true | 启用BL-012方案B品种感知前置过滤 |
| bidirectional_check | bool | 否 | true | 启用双向包含检测(BOUNDARY-018修复) |
| output_format | string | 否 | "csv" | 输出格式: csv / json / parquet |
| include_details | bool | 否 | true | 包含逐case详情 |

### 3.2 dshb_rule_regression — 回归测试

```json
{
  "task_type": "dshb_rule_regression",
  "version_tag": "v86.0-alpha",
  "priority": 3,
  "payload": {
    "test_suite_path": "analysis/e2e_output/v86/dshb_rule_predev/v86_rule_test_suite.json",
    "v85_baseline_path": "analysis/e2e_output/v85/dshb_review_simulation/sim_sceneA_result.csv",
    "run_boundary_tests": true,
    "run_pdf_fix_tests": true,
    "run_comparison": true,
    "output_format": "json"
  }
}
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| test_suite_path | string | 是 | — | 测试用例集JSON路径 |
| v85_baseline_path | string | 否 | null | V85基线CSV路径(启用对比) |
| run_boundary_tests | bool | 否 | true | 运行边界测试 |
| run_pdf_fix_tests | bool | 否 | true | 运行PDF修复测试 |
| run_comparison | bool | 否 | true | 运行V85/V86对比 |
| output_format | string | 否 | "json" | 输出格式 |

### 3.3 dshb_rule_boundary — 边界测试

```json
{
  "task_type": "dshb_rule_boundary",
  "version_tag": "v86.0-alpha",
  "priority": 4,
  "payload": {
    "boundary_testset_path": "analysis/e2e_output/v85/miss_risk_mining/blacklist_boundary_testset.json",
    "rules_subset": ["BL-009a", "BL-026", "BL-012"],
    "min_pass_rate": 100.0
  }
}
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| boundary_testset_path | string | 是 | — | 边界测试集JSON路径 |
| rules_subset | string[] | 否 | null | 仅测试指定规则 |
| min_pass_rate | float | 否 | 100.0 | 最低通过率阈值(%) |

### 3.4 dshb_rule_pdf_fix_check — PDF数据缺失检测

```json
{
  "task_type": "dshb_rule_pdf_fix_check",
  "version_tag": "v86.0-alpha",
  "priority": 2,
  "payload": {
    "data_source": "risk_db",
    "template_count": 488,
    "simulate_post_fix": true,
    "known_missing_risks": ["RISK-010", "RISK-011", "RISK-013", "RISK-005"]
  }
}
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| data_source | string | 是 | "risk_db" | 数据源 |
| template_count | int | 否 | 488 | 模板总数 |
| simulate_post_fix | bool | 否 | true | 启用修复后模拟 |
| known_missing_risks | string[] | 否 | null | 已知数据缺失风险ID列表 |

### 3.5 dshb_rule_compare_v85 — V85/V86对比

```json
{
  "task_type": "dshb_rule_compare_v85",
  "version_tag": "v86.0-alpha",
  "priority": 6,
  "payload": {
    "v85_baseline": "analysis/e2e_output/v85/dshb_review_simulation/sim_sceneA_result.csv",
    "v85_scene": "A",
    "thresholds": {
      "min_p0_rate_delta": 0.0,
      "max_fp_delta": 0,
      "max_regression": 0
    },
    "output_format": "json"
  }
}
```

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| v85_baseline | string | 是 | — | V85基线CSV路径 |
| v85_scene | string | 否 | "A" | 场景: A / B |
| thresholds | object | 否 | 见默认值 | 告警阈值 |
| output_format | string | 否 | "json" | 输出格式 |

---

## 四、出参规范 (Task Result)

### 4.1 dshb_rule_eval 结果

```json
{
  "task_id": "TASK-DH-2026-10-01-00001",
  "result_format": "json",
  "result": {
    "engine_version": "v86.0-alpha-proto",
    "rules_loaded": 6,
    "rules_evaluated": ["BL-009a", "BL-026", "BL-012", "BL-022", "BL-020", "BL-021"],
    "total_templates": 3,
    "total_evaluated": 3,
    "metrics": {
      "blocked": 2,
      "passed": 1,
      "data_missing": 0,
      "tp": 2,
      "fp": 0,
      "p0_interception_rate": 100.0
    },
    "results": [
      {
        "template_id": "TPL-LC-054",
        "indicator_name": "碳酸锂 三元523需求",
        "matched_name": "SMM: 碳酸锂现金生产利润: 外购三元极片黑粉",
        "result": "BLOCKED",
        "triggered_rules": ["BL-009a"],
        "blocked_by": "BL-009a",
        "severity": "P0",
        "risk_id": "RISK-002",
        "risk_level": "P0"
      },
      {
        "template_id": "TPL-NI-008",
        "indicator_name": "中国电解镍净进口量",
        "matched_name": "N/A",
        "result": "DATA_MISSING",
        "triggered_rules": [],
        "blocked_by": null,
        "severity": null,
        "risk_id": "RISK-010",
        "risk_level": "P0",
        "pdf_fix_needed": true,
        "intended_rule": "BL-022"
      }
    ],
    "fetched_at": "2026-10-01T22:00:00+08:00"
  }
}
```

### 4.2 dshb_rule_regression 结果

```json
{
  "task_id": "TASK-DH-2026-10-01-00002",
  "result_format": "json",
  "result": {
    "engine_version": "v86.0-alpha-proto",
    "test_suite_version": "v86-rule-test-suite-v1",
    "total_cases": 48,
    "groups": 13,
    "metrics": {
      "total_cases": 48,
      "passed": 45,
      "failed": 0,
      "skipped": 3,
      "pass_rate": 100.0,
      "tp": 32,
      "fp": 0,
      "regression": 0
    },
    "group_results": [
      {
        "group_id": "GROUP-001",
        "group_name": "BL-009a正向触发用例",
        "rule_id": "BL-009a",
        "total": 4,
        "passed": 4,
        "failed": 0,
        "pass_rate": 100.0
      }
    ],
    "comparison_summary": {
      "v85_p0_interception_rate": 88.2,
      "v86_p0_interception_rate": 100.0,
      "delta_p0_rate": 11.8,
      "delta_tp": 4,
      "delta_fp": 0,
      "total_improvements": 4,
      "total_regressions": 0,
      "regression_detected": false
    },
    "fetched_at": "2026-10-01T22:00:00+08:00"
  }
}
```

### 4.3 dshb_rule_boundary 结果

```json
{
  "task_id": "TASK-DH-2026-10-01-00003",
  "result_format": "json",
  "result": {
    "engine_version": "v86.0-alpha-proto",
    "boundary_testset_version": "v85-boundary-testset",
    "total_cases": 24,
    "metrics": {
      "total": 24,
      "passed": 24,
      "failed": 0,
      "pass_rate": 100.0
    },
    "by_category": {
      "正向危险样例": {"total": 10, "passed": 10, "rate": 100.0},
      "安全负向样例": {"total": 7, "passed": 7, "rate": 100.0},
      "数据缺失样例": {"total": 7, "passed": 7, "rate": 100.0}
    },
    "failed_cases": [],
    "min_pass_rate_met": true,
    "fetched_at": "2026-10-01T22:00:00+08:00"
  }
}
```

### 4.4 dshb_rule_pdf_fix_check 结果

```json
{
  "task_id": "TASK-DH-2026-10-01-00004",
  "result_format": "json",
  "result": {
    "engine_version": "v86.0-alpha-proto",
    "total_templates_scanned": 488,
    "data_missing_detected": 4,
    "known_missing_risks": ["RISK-010", "RISK-011", "RISK-013", "RISK-005"],
    "missing_cases": [
      {
        "risk_id": "RISK-010",
        "template_id": "TPL-NI-008",
        "indicator_name": "中国电解镍净进口量",
        "matched_name": "N/A",
        "intended_rule": "BL-022",
        "fix_description": "PDF模板matched_name为空",
        "post_fix_simulated": {
          "simulated_matched_name": "中国海关:镍:净进口量:月度",
          "will_trigger": false,
          "note": "修复后BL-022需确认matched_name质量"
        }
      }
    ],
    "post_fix_simulation": {
      "total_simulated": 4,
      "will_trigger": 2,
      "need_further_review": 2
    },
    "fetched_at": "2026-10-01T22:00:00+08:00"
  }
}
```

### 4.5 dshb_rule_compare_v85 结果

```json
{
  "task_id": "TASK-DH-2026-10-01-00005",
  "result_format": "json",
  "result": {
    "engine_version": "v86.0-alpha-proto",
    "v85_baseline": "sim_sceneA_result.csv",
    "v85_scene": "A",
    "metrics": {
      "v85_p0_interception_rate": 88.2,
      "v86_p0_interception_rate": 100.0,
      "delta_p0_rate": 11.8,
      "v85_tp": 30,
      "v86_tp": 34,
      "delta_tp": 4,
      "v85_fp": 0,
      "v86_fp": 0,
      "delta_fp": 0
    },
    "change_summary": {
      "total_cases": 63,
      "new_blocks": 4,
      "new_passes": 0,
      "regressions": 0,
      "unchanged": 59
    },
    "changed_cases": [
      {
        "case_id": "RISK-002",
        "risk_id": "RISK-002",
        "change_type": "NEW_BLOCK",
        "v85_status": "NOT_BLOCKED",
        "v86_status": "BLOCKED",
        "v86_rule": "BL-009a",
        "risk_level": "P0"
      }
    ],
    "thresholds_met": {
      "min_p0_rate_delta": true,
      "max_fp_delta": true,
      "max_regression": true
    },
    "overall_verdict": "PASS",
    "fetched_at": "2026-10-01T22:00:00+08:00"
  }
}
```

---

## 五、错误码约定

### 5.1 规则引擎错误码

| 错误码 | HTTP状态 | 场景 | 可重试 |
|--------|----------|------|--------|
| `RULE_ENGINE_LOAD_FAILED` | 500 | 规则集加载失败 | 否 |
| `RULE_NOT_FOUND` | 400 | 请求的规则ID不存在 | 否 |
| `RULE_CONFLICT` | 400 | 规则集冲突(如重复rule_id) | 否 |
| `PATTERN_EMPTY` | 400 | left_patterns或right_patterns为空 | 否 |
| `VARIETY_DETECT_FAILED` | 500 | 品种检测失败 | 是 |
| `BIDIRECTIONAL_CHECK_ERROR` | 500 | 双向包含检测异常 | 是 |
| `PDF_DATA_MISSING` | 200 | matched_name为空(非错误，正常返回) | — |

### 5.2 任务调度错误码

| 错误码 | HTTP状态 | 场景 | 可重试 |
|--------|----------|------|--------|
| `BAD_PAYLOAD` | 400 | 参数错误 | 否 |
| `UNKNOWN_TASK_TYPE` | 400 | 未知任务类型 | 否 |
| `MISSING_REQUIRED_FIELD` | 400 | 缺少必填字段 | 否 |
| `PAYLOAD_UNACCEPTABLE` | 422 | payload过大/缺字段 | 否 |
| `TEST_SUITE_NOT_FOUND` | 404 | 测试用例集文件不存在 | 否 |
| `BASELINE_NOT_FOUND` | 404 | V85基线文件不存在 | 否 |
| `BOUNDARY_TESTSET_NOT_FOUND` | 404 | 边界测试集文件不存在 | 否 |
| `THRESHOLD_EXCEEDED` | 200 | 指标未达阈值(非错误，标记在结果中) | — |
| `REGRESSION_DETECTED` | 200 | 检测到回归(非错误，标记在结果中) | — |
| `QUEUE_FULL` | 503 | 队列已满 | 是 |
| `NO_WORKER_AVAILABLE` | 503 | 无可用Worker | 是 |

### 5.3 统一错误响应格式

```json
{
  "error": true,
  "code": "RULE_NOT_FOUND",
  "message": "Rule 'BL-999' not found in ruleset 'v86-p0-proto'",
  "detail": {
    "requested_rule": "BL-999",
    "available_rules": ["BL-009a", "BL-026", "BL-012", "BL-022", "BL-020", "BL-021"]
  },
  "timestamp": "2026-10-01T22:00:00+08:00"
}
```

---

## 六、规则集版本管理

### 6.1 V86规则集版本

| 版本 | 规则数 | 变更 | 日期 |
|------|--------|------|------|
| v86-p0-proto | 6 (4 P0 + 2 P1) | 初始原型 | 2026-10-01 |
| v86-p0-alpha | 待定 | Alpha发布 | 待定 |
| v86-beta | ≥10 | Beta发布 | 待定 |
| v86-ga | ≥16 | GA发布 | 待定 |

### 6.2 规则集加载契约

```python
# Worker 加载规则集
def load_ruleset(version_tag: str, rules_subset: List[str] = None):
    """
    加载指定版本的规则集。
    
    Args:
        version_tag: 规则集版本 (e.g. "v86-p0-proto")
        rules_subset: 仅加载指定规则子集 (e.g. ["BL-009a", "BL-026"])
    
    Returns:
        V86RuleEngine instance
    
    Raises:
        RULE_ENGINE_LOAD_FAILED: 规则集文件不存在或解析失败
        RULE_NOT_FOUND: 指定规则不在规则集中
    """
    engine = V86RuleEngine(rules=create_v86_p0_rules())
    
    # 根据version_tag加载不同的规则集
    # v86-p0-proto: 当前原型规则
    # v86-p0-alpha: Alpha发布规则集
    # v86-beta: Beta规则集
    
    if rules_subset:
        engine = filter_rules(engine, rules_subset)
    
    return engine
```

---

## 七、与E后端task_api的对齐关系

### 7.1 端点对应

| E后端端点 | 方法 | V86规则适配 | 说明 |
|-----------|------|------------|------|
| POST /api/v1/tasks | POST | ✅ 复用 | 提交规则任务 |
| GET /api/v1/tasks/{task_id} | GET | ✅ 复用 | 查询任务状态 |
| GET /api/v1/tasks | GET | ✅ 复用 | 批量查询 |
| GET /api/v1/tasks/{task_id}/result | GET | ✅ 复用 | 获取结果 |
| POST /api/v1/tasks/{task_id}/cancel | POST | ✅ 复用 | 取消任务 |
| GET /api/v1/tasks/queue | GET | ✅ 复用 | 队列状态 |

### 7.2 状态机对齐

```
E后端状态机:
  queued → running → succeeded / failed / cancelled / timeout

V86规则任务状态:
  queued:     任务已提交，等待Worker认领
  running:    Worker执行中(规则引擎评估)
  succeeded:  任务完成，结果已回写
  failed:     任务失败(规则引擎异常/超时)
  cancelled:  任务被取消
  timeout:    任务超时(默认3600秒)
```

### 7.3 幂等性对齐

```
E后端: X-Idempotency-Key header
V86规则: 复用E后端的幂等机制

提交规则任务时:
  Header: X-Idempotency-Key: <sha256(submitter|task_type|payload)[:32]>
  
同一 submitter + 相同 payload + 相同幂等键 → 返回原 task_id
```

### 7.4 回调对齐

```
E后端: callback_url + 3次指数退避
V86规则: 复用E后端的回调机制

回调body:
{
  "task_id": "TASK-DH-2026-10-01-00001",
  "status": "succeeded",
  "result_ref": "s3://v86-results/2026/10/01/TASK-DH-2026-10-01-00001.json",
  "finished_at": "2026-10-01T22:05:00+08:00"
}
```

---

## 八、部署与运维

### 8.1 Worker资源需求

| 维度 | 要求 |
|------|------|
| Python版本 | ≥3.8 |
| 内存 | ≥256MB (规则集<10MB) |
| CPU | 1核 |
| 磁盘 | ≥100MB (规则集+测试集+结果) |
| 网络 | 无需外部网络(纯本地计算) |

### 8.2 配置项

```yaml
# v86_rule_worker_config.yaml
engine:
  version: v86.0-alpha-proto
  ruleset_path: analysis/e2e_output/v86/dshb_rule_predev/
  test_suite_path: analysis/e2e_output/v86/dshb_rule_predev/v86_rule_test_suite.json
  
scheduler:
  max_concurrent_tasks: 4
  task_timeout_seconds: 3600
  retry_max: 3
  retry_backoff: exponential
  
thresholds:
  boundary_min_pass_rate: 100.0
  regression_max_fp: 0
  regression_max_loss: 0
  p0_interception_min_delta: 0.0
```

### 8.3 监控指标

| 指标 | 类型 | 告警阈值 |
|------|------|---------|
| rule_eval_duration_ms | 延迟 | P99 > 5000ms |
| rule_eval_error_rate | 错误率 | > 1% |
| regression_detected_count | 回归数 | > 0 |
| boundary_pass_rate | 边界通过率 | < 100% |
| p0_interception_rate | P0拦截率 | < 95% |
| task_queue_depth | 队列深度 | > 50 |
| task_timeout_count | 超时数 | > 3/小时 |

---

## 九、约束合规声明

- ✅ 不调用zhiji API (NO_ZHIJI_API_CALL=TRUE)
- ✅ 不修改V85核心规则/模板/黑名单源文件 (READ_ONLY=TRUE)
- ✅ V86原型代码独立隔离，不覆盖V85生产逻辑
- ✅ 仅新增V86原型代码、测试集、报告文档
- ✅ 分支锁定feature/v85-chart-template
- ✅ 对接E的V86 task_api_design (commit bcd64dd)
- ✅ 复用E后端的任务调度、状态机、幂等、回调机制
- ✅ 规则集版本化管理，支持v86-p0-proto → v86-p0-alpha → v86-beta → v86-ga演进

---

*本文档基于E的V86 task_api_design.md适配生成，定义V86规则引擎与后端调度的契约。*
*生成时间: 2026-10-01 22:00:00*
