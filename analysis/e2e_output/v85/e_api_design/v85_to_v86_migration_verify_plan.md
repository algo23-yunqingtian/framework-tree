# V85 → V86 迁移校验方案

> 任务：`E_V85_READONLY_API_AND_V86_BACKEND_DESIGN` · T2.4
> 分支：`feature/v85-chart-template`
> 输入：V85 冻结基线（HERMES `a2815c4` / DSHB `6771406` / DSHE `f313570`）
> 依赖：`v85_artifact_api.py`（同目录，只读接口）、`v86_backend_schema_design.md`、`v86_task_api_design.md`
> 未就绪依赖：`v85_version_freeze_decision.md`、`v86_init_backlog_total.md`（HERMES 产出，`DEPENDENCY_NOT_READY=TRUE`）
> 约束：本方案**仅定义校验流程与脚本方案**，不执行任何实际迁移，不修改 V85 数据。

---

## 1. 迁移目标

| 目标 | 描述 |
|---|---|
| **等价性验证** | V86 引擎输出与 V85 冻结基线在关键指标上对齐（P0 拦截率、TP/FP 一致） |
| **回归检测** | 14 项 Gate 全绿，且无新增误报 |
| **可回滚** | 任何指标劣化都能定位到具体规则/别名，一键回滚到 V85 |
| **可追溯** | 每次迁移校验有不可变记录（`task_run` + `gate_result` + 审计） |

---

## 2. 校验流程总览

```
┌──────────────────────────────────────────────────────────────┐
│  Stage 1: 环境准备                                            │
│  - 校验 V85 只读接口可用                                       │
│  - 拉取基线制品 MD5 校验                                       │
│  - 创建 V86 引擎候选（engine_variant: base / f1 / f3 / f3+f4） │
└──────────────────────────────────────────────────────────────┘
                            │
                            v
┌──────────────────────────────────────────────────────────────┐
│  Stage 2: 别名对齐校验                                          │
│  - V85 别名库（CSV）→ V86 别名表（DB）灌库                     │
│  - 逐条比对 alias_norm / canonical_key / confidence           │
│  - 输出 alias_diff_report.md                                  │
└──────────────────────────────────────────────────────────────┘
                            │
                            v
┌──────────────────────────────────────────────────────────────┐
│  Stage 3: 规则对齐校验                                          │
│  - V85 黑名单 31 规则 → V86 rule_registry + rule_version     │
│  - 逐规则校验 patterns / severity / category                  │
│  - 输出 rule_diff_report.md                                   │
└──────────────────────────────────────────────────────────────┘
                            │
                            v
┌──────────────────────────────────────────────────────────────┐
│  Stage 4: 行为回归校验                                          │
│  - 488 模板场景 A/B 回放                                      │
│  - 14 项 Gate 全量运行                                        │
│  - 别名冲突集 893 用例回归                                    │
│  - 输出 gate_result / task_run 记录                          │
└──────────────────────────────────────────────────────────────┘
                            │
                            v
┌──────────────────────────────────────────────────────────────┐
│  Stage 5: 指标对齐与判定                                        │
│  - P0 拦截率对比                                              │
│  - TP/FP 一致性                                              │
│  - 逐规则命中率                                              │
│  - 应用判定阈值                                              │
│  - 输出 migration_verify_report.md                            │
└──────────────────────────────────────────────────────────────┘
                            │
                            v
┌──────────────────────────────────────────────────────────────┐
│  Stage 6: 结果处置                                              │
│  - PASS: 发布 V86 候选                                       │
│  - FAIL: 分析根因、修正、重跑                                  │
│  - ABORT: 回滚到 V85                                          │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. 指标对比脚本方案

### 3.1 脚本文件（伪代码，非交付物）

`migration_verify.py`（放在 V86 仓库，非本任务目录）

```python
#!/usr/bin/env python3
"""V85 → V86 迁移校验脚本。

用法：
    python migration_verify.py \
        --baseline-version f313570 \
        --target-version v86.0-alpha \
        --engine-variant f3+f4 \
        --report-out migration_verify_report_20261001.md
"""

from v85_artifact_api import ArtifactAPI
from v86_task_api import TaskAPI  # 假设已实现

def main():
    args = parse_args()

    # 1) 基线 MD5 校验（V85 只读）
    api_v85 = ArtifactAPI(repo_root=REPO_ROOT, token=TOKEN)
    baseline_meta = api_v85.get_artifact_meta("risk_db", version=args.baseline_version)
    if not api_v85.verify_artifact_md5("risk_db", baseline_meta["md5"], verify_file=True)["match"]:
        abort("V85 基线 risk_db 已被篡改")

    # 2) 拉取 V85 基线数据
    v85_risks = api_v85.query("risk_db", filters={}, limit=10000)["rows"]
    v85_replay = api_v85.query("scenario_replay", filters={}, limit=10000)["rows"]

    # 3) 触发 V86 回放任务
    task_api = TaskAPI()
    task = task_api.submit(
        task_type="risk_db_replay",
        version_tag=args.target_version,
        payload={
            "engine_variant": args.engine_variant,
            "template_count": 488,
            "scenario": "both",
            "baseline_artifact": {"kind": "risk_db", "version": args.baseline_version, "md5": baseline_meta["md5"]}
        },
        submitter="migration_verify"
    )
    result = task_api.wait_for(task["task_id"], timeout=3600)

    # 4) 拉取 V86 结果
    v86_result = result["result"]

    # 5) 指标对齐
    comparison = compare_metrics(v85_risks, v85_replay, v86_result, args.engine_variant)

    # 6) 应用阈值
    verdict = apply_thresholds(comparison, args.thresholds)

    # 7) 生成报告
    report = render_report(comparison, verdict, args)
    write_report(report, args.report_out)

    return 0 if verdict["overall"] == "PASS" else 1

def compare_metrics(v85_risks, v85_replay, v86_result, engine_variant):
    """计算核心指标。"""
    metrics = {
        "p0_interception_rate": {
            "v85": compute_p0_interception(v85_replay),
            "v86": v86_result["p0_interception_rate"],
        },
        "p1_interception_rate": {
            "v85": compute_p1_interception(v85_replay),
            "v86": v86_result["p1_interception_rate"],
        },
        "false_positive_rate": {
            "v85": compute_fp_rate(v85_replay),
            "v86": v86_result["false_positive_rate"],
        },
        "per_rule_hit": {
            "v85": compute_per_rule_hit(v85_replay),
            "v86": v86_result["per_rule_hit"],
        },
        "canonical_resolve_consistency": {
            "v85": None,  # V85 无统一 canonical resolve
            "v86": v86_result["canonical_resolve_consistency"],
        },
        "alias_conflict_handling": {
            "v85": compute_v85_conflict_handling(v85_replay),
            "v86": v86_result["alias_conflict_handling"],
        },
        "cross_variety_p0": {
            "v85": compute_cross_variety_p0(v85_replay),
            "v86": v86_result["cross_variety_p0"],
        },
    }
    return metrics

def apply_thresholds(comparison, thresholds):
    """应用判定阈值。"""
    verdicts = {}
    for metric_name, data in comparison.items():
        if metric_name.startswith("per_rule") or metric_name.startswith("canonical"):
            continue  # 逐规则单独判定
        v85_val = data.get("v85")
        v86_val = data.get("v86")
        if v85_val is None or v86_val is None:
            verdicts[metric_name] = "N/A"
            continue
        delta = abs(v86_val - v85_val)
        if delta <= thresholds.get(metric_name, 0.02):
            verdicts[metric_name] = "PASS"
        elif delta <= thresholds.get(metric_name, 0.02) * 2:
            verdicts[metric_name] = "WARN"
        else:
            verdicts[metric_name] = "FAIL"
    return verdicts
```

### 3.2 关键指标定义

| 指标 | 定义 | 数据来源 |
|---|---|---|
| **P0 拦截率** | P0 命中数 / 全部模板数 | `scenario_replay` 中 `new_risk_label=BLOCKED` 且 `old_risk_label=BLOCKED`（P0 拦截保留）的比例 |
| **P1 拦截率** | P1 命中数 / 全部模板数 | 同上，P1 |
| **误报率（FP）** | 误拦数 / 全部模板数 | `new_risk_label=BLOCKED` 但 `is_cross_variety_p0=NO` 且 `verify_status ∈ {FILLED, MISSING}` |
| **TP** | 正确拦截 | `new_risk_label=BLOCKED` 且 `old_risk_label=BLOCKED` 且 `verify_status=VALID` |
| **逐规则命中率** | 每条黑名单规则的命中次数分布 | `per_rule_hit` 字典（BL-001..BL-031） |
| **规范键解析一致率** | V86 canonical_resolve 输出中，同一 alias_norm 一致映射到同一 canonical_key 的比例 | V86 引擎输出 |
| **别名冲突处理率** | V86 对 `multi_canonical_conflicts_165.csv` 的处理结果中，被明确判定的比例 | 165 条冲突集 |
| **跨品种 P0** | `is_cross_variety_p0=YES` 的比例 | `scenario_replay` |

### 3.3 逐规则对比

对 31 条黑名单规则，逐条计算：
```
rule_id | v85_hit | v86_hit | delta | verdict
BL-001  |  15    |  15    |   0  | PASS
BL-002  |   8    |   8    |   0  | PASS
BL-009a |   1    |   1    |   0  | PASS
BL-020  |   0    |   0    |   0  | N/A (zero-hit)
...
```

- `delta = 0`：PASS
- `|delta| ≤ 3`：WARN（人工复核）
- `|delta| > 3`：FAIL（回滚触发）
- 两条都 `= 0`：N/A（无法判定，如死规则 BL-019a/BL-020/BL-021）

---

## 4. 判定规则

### 4.1 阈值表

| 指标 | PASS | WARN | FAIL |
|---|---|---|---|
| P0 拦截率 | Δ ≤ 2 pp | 2 pp < Δ ≤ 5 pp | Δ > 5 pp |
| P1 拦截率 | Δ ≤ 3 pp | 3 pp < Δ ≤ 6 pp | Δ > 6 pp |
| 误报率 | Δ ≤ 1 pp | 1 pp < Δ ≤ 3 pp | Δ > 3 pp |
| 跨品种 P0 | Δ = 0 | Δ ≤ 1 | Δ > 1 |
| 规范键解析一致率 | ≥ 99% | 95% ≤ x < 99% | < 95% |
| 别名冲突处理率 | ≥ 90% | 70% ≤ x < 90% | < 70% |
| 逐规则命中 | |Δ| ≤ 1 | 1 < |Δ| ≤ 3 | |Δ| > 3 |

**说明**：
- `pp` = percentage point（百分点）
- 阈值为经验值，首次运行后可基于历史数据调整
- `跨品种 P0` 是硬指标：任何新增跨品种 P0 都视为严重回归

### 4.2 总判定

| 条件 | 总判定 |
|---|---|
| 所有指标 PASS | ✅ PASS |
| 至少一个 WARN，无 FAIL | ⚠️ WARN（需人工复核） |
| 至少一个 FAIL | ❌ FAIL（回滚触发） |
| 关键指标 N/A（如逐规则 N/A） | 按剩余指标判定 |

### 4.3 硬门禁（不允许降级）

- 14 项 Gate 中任一 FAIL → 总判定强制 FAIL
- `is_cross_variety_p0` 数量增加 → 强制 FAIL
- V86 canonical_resolve 出现 V85 未出现过的自配对 BLOCK → 强制 FAIL

---

## 5. 异常处理

### 5.1 任务层异常

| 异常 | 处理 |
|---|---|
| V85 基线 MD5 不匹配 | ABORT（数据被篡改，终止校验） |
| V86 引擎变体不存在 | ABORT（配置错误，终止校验） |
| 任务超时（> 3600s） | TIMEOUT（可重试） |
| Worker 崩溃 | 自动重试（最多 3 次） |
| 结果对象缺失 | FAIL（数据完整性错误） |

### 5.2 数据层异常

| 异常 | 处理 |
|---|---|
| V86 结果缺少某指标 | 该指标记 N/A，其他指标继续判定 |
| 逐规则命中数据缺失 | 该规则记 N/A |
| 别名冲突集为空 | ABORT（测试集损坏） |
| 规范键解析一致率无法计算 | 该指标记 N/A |

### 5.3 阈值层异常

| 异常 | 处理 |
|---|---|
| 阈值为空 | 使用默认值（§4.1） |
| 阈值非法（负数、> 100%） | ABORT（配置错误） |
| 指标 delta 为 NaN | 记 N/A |

---

## 6. 版本回滚策略

### 6.1 回滚触发条件

- 总判定 FAIL
- 任一硬门禁触发
- 人工复核判定为不可接受

### 6.2 回滚流程

```
┌──────────────────────────────────────────────────────────────┐
│  1. 检测回滚触发                                               │
│     - migration_verify_report.md 生成                        │
│     - verdict.overall = "FAIL" 或硬门禁触发                   │
└──────────────────────────────────────────────────────────────┘
                            │
                            v
┌──────────────────────────────────────────────────────────────┐
│  2. 分析根因（自动）                                            │
│     - 定位到具体指标（P0 拦截率 / 误报率 / 逐规则）             │
│     - 定位到具体规则/别名（通过 gate_result.detail）           │
│     - 生成 root_cause_analysis.md                            │
└──────────────────────────────────────────────────────────────┘
                            │
                            v
┌──────────────────────────────────────────────────────────────┐
│  3. 决策回滚范围                                               │
│     - 全量回滚：V86 → V85                                      │
│     - 部分回滚：只回滚具体规则/别名                             │
│     - 降级上线：V86 但关闭某功能（如 F3）                      │
└──────────────────────────────────────────────────────────────┘
                            │
                            v
┌──────────────────────────────────────────────────────────────┐
│  4. 执行回滚                                                   │
│     - 更新 config_snapshot.activated_at（切换版本）            │
│     - 或提交新的 rule_version（deprecate 当前版本）             │
│     - 或切换 engine_variant 到 base                            │
│     - 触发新的 migration_verify 任务验证回滚后状态              │
└──────────────────────────────────────────────────────────────┘
                            │
                            v
┌──────────────────────────────────────────────────────────────┐
│  5. 回滚确认                                                   │
│     - 重新跑全量校验                                            │
│     - 若 PASS：回滚成功，记录 audit_log                        │
│     - 若仍 FAIL：升级到人工介入                                 │
└──────────────────────────────────────────────────────────────┘
```

### 6.3 回滚粒度

| 粒度 | 适用场景 | 操作 |
|---|---|---|
| **引擎变体** | F3/F4 单独上线导致回归 | 切换 `engine_variant` 到上一稳定版本 |
| **规则版本** | 某规则修改引入回归 | 提交新 `rule_version`，`deactivated_at` 当前版本 |
| **别名映射** | 某别名变更引入误报 | `alias_mapping.status='deprecated'` |
| **全量** | 系统性回归 | 切换 `version_tag` 到 V85，走只读接口 |

### 6.4 回滚不可逆性

- 回滚后不允许"再回滚"（避免振荡）
- 如需再次迁移，必须走新 `task_run` + 新 `migration_verify`
- 审计日志保留完整链

---

## 7. 输出报告结构

`migration_verify_report.md`：

```markdown
# V85 → V86 迁移校验报告

## 1. 元信息
- 基线版本: f313570 (v85.0)
- 目标版本: v86.0-alpha
- 引擎变体: f3+f4
- 提交者: migration_verify@internal
- 开始时间: 2026-10-01 16:20:00 +0800
- 结束时间: 2026-10-01 16:23:45 +0800
- 总耗时: 3m 45s
- Task ID: TASK-MV-2026-10-01-00001

## 2. 基线校验
- risk_db MD5: 819cb85a... ✓
- alias_library MD5: ... ✓
- blacklist_v85_final MD5: ... ✓

## 3. 核心指标对比
| 指标 | V85 | V86 | Δ | 判定 |
|---|---|---|---|---|
| P0 拦截率 | 100.00% | 100.00% | 0.00 pp | PASS |
| P1 拦截率 | 68.54% | 69.12% | +0.58 pp | PASS |
| 误报率 | 5.28% | 5.10% | -0.18 pp | PASS |
| 跨品种 P0 | 0 | 0 | 0 | PASS |
| 规范键解析一致率 | N/A | 99.86% | N/A | PASS |
| 别名冲突处理率 | N/A | 92.73% | N/A | PASS |

## 4. 逐规则命中对比
| 规则 | V85 | V86 | Δ | 判定 |
|---|---|---|---|---|
| BL-001 | 15 | 15 | 0 | PASS |
| ... | ... | ... | ... | ... |

## 5. Gate 结果
| Gate | 判定 | 备注 |
|---|---|---|
| G1 | N/A | patched variants 不可证伪 |
| G2 | PASS | ... |
| G4 | PASS | 边界 FP 11/18 |
| ... | ... | ... |

## 6. 总判定
- **OVERALL: PASS**
- 无 FAIL 指标
- 无硬门禁触发
- 建议：可发布 V86.0-alpha

## 7. 附录
- Task ID: TASK-MV-2026-10-01-00001
- Gate run ID: GATE-2026-10-01T162000-00001
- Result ref: s3://v86-results/2026/10/01/TASK-MV-2026-10-01-00001.json
```

---

## 8. 与只读接口的集成

### 8.1 读取 V85 基线

```python
api = ArtifactAPI(repo_root=REPO_ROOT, token=TOKEN)
# 基线 MD5 校验
baseline_meta = api.get_artifact_meta("risk_db", version="f313570")
assert api.verify_artifact_md5("risk_db", baseline_meta["md5"], verify_file=True)["match"]

# 拉取基线数据
v85_replay = api.query("scenario_replay", filters={}, limit=10000)["rows"]
```

### 8.2 V86 结果注册

V86 校验结果写入 `analysis/e2e_output/v86/migration_verify/<task_id>/result.json`，并注册到 V86 只读接口白名单：

```python
# V86 制品注册表（示意）
V86_ARTIFACTS = {
    "migration_verify_result": {
        "relpath": "migration_verify/TASK-MV-2026-10-01-00001/result.json",
        "type": "json",
        ...
    }
}
```

客户端可通过 `ArtifactAPI.get_file("migration_verify_result", version="v86.0-alpha")` 拉取。

### 8.3 审计链

```
task_run (task_id=TASK-MV-2026-10-01-00001)
  → gate_run (run_id=GATE-2026-10-01T162000-00001)
    → gate_result (14 项)
  → result_ref (S3 或本地路径)
    → V86 只读接口制品
  → audit_log (谁在何时提交了任务、谁审批了回滚)
```

---

## 9. 与 `v85_version_freeze_decision.md` 的关系

未就绪依赖。若该文档提供：
- **锁定版本列表**：本方案中的 `baseline_version` 必须来自该列表
- **锁定策略**（永久/临时）：影响回滚策略的"永久冻结"选项
- **解锁流程**：影响本方案的"再迁移"路径

**当前处理**：默认基线 = `f313570`（DSHE 最新提交）。未来若 freeze_decision 引入多基线，走 `--baseline-version` 参数扩展。

---

## 10. 未覆盖事项（明确非目标）

1. **不做在线 A/B 测试**：迁移校验是离线批处理
2. **不做灰度发布**：V86 上线是"切换 version_tag"，非渐进
3. **不做跨集群校验**：单集群部署
4. **不做性能基准**：本方案关注功能正确性，不关注性能
5. **不做数据迁移脚本**：别名/规则灌库脚本是独立任务（见 `v86_backend_schema_design.md` §7）

---

## 11. 依赖声明

| 依赖 | 状态 | 影响 |
|---|---|---|
| `v85_version_freeze_decision.md` | **未就绪**（HERMES 产出） | 基线版本选择暂用 `f313570`；未来扩展 `--baseline-version` |
| `v86_init_backlog_total.md` | **未就绪**（HERMES 产出） | 若 backlog 引入新的迁移指标，走 `add_metric()` 扩展 |
| V85 只读接口 | 已交付 | 基线读取 |
| V86 存储 schema | 已交付 | task_run / gate_result / audit_log |
| V86 任务 API | 已交付 | 提交迁移任务 |

---

## 12. 约束合规

- ✅ 不修改 V85 冻结数据（通过只读接口读取）
- ✅ 不调用 zhiji API
- ✅ 不执行任何实际迁移（本方案仅定义流程与脚本方案）
- ✅ 分支锁定 `feature/v85-chart-template`
- ✅ 只新增设计文档
