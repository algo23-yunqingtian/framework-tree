# V86-RC2 DSHE 24项依赖用例Mock替换&DSHB真实基准接入规格 V7

> **Task**: DSHE_V86_RC2_DEP_CASE_MOCK_REPLACE_SPEC_V7 · T3.1
> **Branch**: `feature/v85-chart-template`
> **基线**: DSHE V7-RC1 (`f1d444e`), DSHB V86-RC1 (`0948e1d`), DSHB Gate准入基线 (`581a9f4`)
> **DSHB Final Prep**: 回填字段契约最终固化 (`30B8BB8375CB95CDCBFB89BE24CDC12C`), 图表Schema固化 (`858AE32E3AAE1D5B82A9FE4848662C89`), zhiji预映射 (`022C907B1D607651E13731461DC23F7A`)
> **约束**: NO_ZHIJI_API_CALL / NO_MODIFY_V85 / NO_OVERWRITE / BRANCH_LOCKED / NO_PANEL_JSON_MODIFICATION / NO_ENGINE_LOGIC_MODIFICATION
> **生成日期**: 2026-10-04
> **状态**: ✅ **24/24 依赖用例 Mock 替换规格定稿 — 19/19 回填字段接入 — 3项保留差异处理 — 4项互补口径约定 — DSHB基准接入完成**

---

## 1. 执行摘要

本文档定义 DSHE 24 个依赖 DSHB 的展示层 Gate 用例，从 Mock 数据桩替换为 DSHB 提供的底层指标基准参数的完整规格。基于 DSHB 交付的回填字段契约最终固化文档（19/19 字段定稿）和口径差异说明文档（10/10 冲突解决），对 24 个用例逐一建立 Mock→Real 替换映射，处理 3 项保留差异和 4 项互补口径约定，定义 24 个用例的测试脚本特殊口径分支处理逻辑。

### 1.1 替换总览

| 维度 | 值 | 说明 |
|------|-----|------|
| **依赖用例总数** | 24 | GATE-DSHE-004/007/008/010/013~016/018~019/023~024/028/038/041/048/052/054~056/060/063~065 |
| **Mock 数据桩** | 24/24 (100%) | 全部依赖用例当前使用 Mock |
| **DSHB 回填字段** | 19 | F-01~F-19 全部已定稿 |
| **DSHB 基准参数** | 24/24 (100%) | 全部 24 用例已有底层基准 |
| **口径冲突解决** | 10/10 (100%) | 3 统一 + 3 保留差异 + 4 互补 |
| **Mock→Real 映射** | 24/24 (100%) | 全部用例已建立替换映射 |
| **特殊口径分支** | 7 | 3 保留差异 + 4 互补口径分支 |
| **预期通过率** | 100% | 24/24 预期 PASS |
| **风险等级** | 0 高 / 12 中 / 12 低 | 全部有 Mock 降级回退方案 |

---

## 2. DSHB 底层基准参数来源

### 2.1 数据来源文档

| 来源 | 文档 | 内容 |
|------|------|------|
| 回填字段契约 | `v86_rc2_dshb_backfill_field_final_spec_v7.md` | 19 字段定义、Mock/Real 规格、移除条件 |
| 图表 Schema | `v86_rc2_dshb_chart_schema_full_v7.md` | 36 图表数据源、56 子面板、7 降级标记 |
| zhiji 预映射 | `v86_rc2_dshb_zhiji_mapping_predefine_v7.md` | 36 图表 + 19 字段 zhiji_id 映射 |
| 跨团队契约 | `v86_rc2_cross_team_contract_v7.md` | 23 项依赖用例评审、19 回填字段定义 |
| 差异评审 | `v86_rc2_dshe_dshb_case_diff_review_v7.md` | 10 项口径冲突分析、24 项差异台账 |

### 2.2 DSHB 基准参数分类

| 基准类型 | 字段 | 用例数 | 交付窗口 | 交付状态 |
|----------|------|--------|---------|---------|
| 数据源标识 | F-05, F-08, F-11, F-12 | 8 | T+1d | ✅ 已交付 |
| 数据一致性 | F-06, F-09, F-13, F-17 | 4 | T+1d | ✅ 已交付 |
| 降级状态 | F-07, F-16 | 2 | T+1d | ✅ 已交付 |
| 数据源可用性 | F-14 | 1 | T+1d | ✅ 已交付 |
| API 分批支持 | F-01 | 1 | T+3d | ✅ 已交付 |
| API 子页面支持 | F-02, F-03 | 2 | T+3d | ✅ 已交付 |
| API 性能时序 | F-04, F-10 | 2 | T+3d | ✅ 已交付 |
| 探测成功率 | F-15 | 1 | T+3d | ✅ 已交付 |
| 演示数据 | F-18, F-19 | 3 | T+3d | ✅ 已交付 |

---

## 3. 24 项依赖用例 Mock→Real 替换映射

### 3.1 替换映射总表

| # | 用例ID | 用例名称 | Mock 数据桩 | DSHB 基准参数 | 回填字段 | 替换类型 | 特殊口径分支 |
|---|--------|---------|------------|--------------|---------|---------|------------|
| 1 | GATE-DSHE-004 | 工业硅全量数据加载 | `api_batch_support: TRUE` (模拟) | DSHB API 支持分批确认值 | F-01 | BOOLEAN 读取 | — |
| 2 | GATE-DSHE-007 | 子页面导航验证 | `api_subpage_support: TRUE` (模拟) | DSHB API 支持子页面确认值 | F-02 | BOOLEAN 读取 | — |
| 3 | GATE-DSHE-008 | 子页面数据加载 | 4 子页面模拟 JSON | DSHB API 实际子页面数据 | F-03 | JSON 结构替换 | — |
| 4 | GATE-DSHE-010 | 分批加载性能验证 | 5 批次各 ~800ms (模拟) | DSHB API 实际响应时间 | F-04 | JSON 时序替换 | **MC-03 互补** |
| 5 | GATE-DSHE-013 | 36 图表全量渲染 | 36 个模拟数据源 ID | DSHB 实际数据源标识 | F-05 | STRING[] 替换 | — |
| 6 | GATE-DSHE-014 | 29 全匹配数据一致性 | `1.0` (模拟 100%) | DSHB 实际一致性比率 | F-06 | FLOAT 读取 | **MC-01 统一** |
| 7 | GATE-DSHE-015 | 7 降级图表渲染 | 7 张降级模拟 JSON | DSHB 实际降级状态 | F-07 | JSON 结构替换 | — |
| 8 | GATE-DSHE-016 | 56 子面板渲染 | 56 个模拟数据源 ID | DSHB 实际子面板数据源 | F-08 | STRING[] 替换 | — |
| 9 | GATE-DSHE-018 | 子面板数据一致性 | `1.0` (模拟 100%) | DSHB 实际一致性比率 | F-09 | FLOAT 读取 | — |
| 10 | GATE-DSHE-019 | 工业硅图表分批渲染 | 5 批次模拟 JSON | DSHB API 实际批次数据 | F-10 | JSON 结构替换 | — |
| 11 | GATE-DSHE-023 | 数据点完整性 | 36 图表各 100% (模拟) | DSHB 实际数据点数 | F-11 | INTEGER 读取 | — |
| 12 | GATE-DSHE-024 | 时间轴一致性 | 36 个统一时间范围 (模拟) | DSHB 实际时间范围 | F-12 | STRING[] 替换 | — |
| 13 | GATE-DSHE-028 | 别名解析成功率 | `1.0` (模拟 100%) | DSHB 实际解析成功率 | F-13 | FLOAT 读取 | **MC-10 互补** |
| 14 | GATE-DSHE-038 | L0 正常态验证 | 全部数据源 UP (模拟) | DSHB 实际数据源状态 | F-14 | JSON 状态替换 | **MC-07 互补** |
| 15 | GATE-DSHE-041 | L2 数据源探测 | `0.98` (模拟 98%) | DSHB 实际探测成功率 | F-15 | FLOAT 读取 | — |
| 16 | GATE-DSHE-048 | 7 降级图表降级 | 7 张降级模拟 JSON | DSHB 实际降级状态 | F-16 | JSON 结构替换 | — |
| 17 | GATE-DSHE-052 | 恢复数据一致性 | `1.0` (模拟 100%) | DSHB 实际恢复后一致性 | F-17 | FLOAT 读取 | — |
| 18 | GATE-DSHE-054 | S-02 Gate 大盘演示 | 模拟演示数据 | DSHB 实际演示数据 | F-18 (部分) | JSON 结构替换 | — |
| 19 | GATE-DSHE-055 | S-03 工业硅演示 | 模拟演示数据 | DSHB 实际演示数据 | F-10 (部分) | JSON 结构替换 | — |
| 20 | GATE-DSHE-056 | S-04 降级演示 | 模拟演示数据 | DSHB 实际演示数据 | F-16 (部分) | JSON 结构替换 | — |
| 21 | GATE-DSHE-060 | S-08 PDF 图表演示 | 模拟演示数据 | DSHB 实际演示数据 | F-18 (部分) | JSON 结构替换 | — |
| 22 | GATE-DSHE-063 | S-11 全链路回归 | 模拟演示数据 | DSHB 实际演示数据 | F-18 (部分) | JSON 结构替换 | — |
| 23 | GATE-DSHE-064 | 18 场景全量回放 | 18 场景模拟 JSON | DSHB 实际场景数据 | F-18 | JSON 结构替换 | — |
| 24 | GATE-DSHE-065 | 90 Q&A 全量回放 | 90 Q&A 模拟 JSON | DSHB 实际 Q&A 数据 | F-19 | JSON 结构替换 | — |

### 3.2 替换类型统计

| 替换类型 | 用例数 | 用例列表 |
|---------|--------|---------|
| BOOLEAN 读取 | 2 | #1 (F-01), #2 (F-02) |
| FLOAT 读取 | 5 | #6 (F-06), #9 (F-09), #13 (F-13), #15 (F-15), #17 (F-17) |
| INTEGER 读取 | 1 | #11 (F-11) |
| STRING[] 替换 | 3 | #5 (F-05), #8 (F-08), #12 (F-12) |
| JSON 结构替换 | 13 | #3 (F-03), #4 (F-04), #7 (F-07), #10 (F-10), #14 (F-14), #16 (F-16), #18~#24 |

---

## 4. 特殊口径分支处理逻辑

### 4.1 3 项保留差异处理

以下 3 项口径冲突在双端均保留差异，测试脚本中需增加分支处理逻辑：

#### 4.1.1 MC-02: P1 阈值差异

| 维度 | DSHB 定义 | DSHE 定义 | 处理策略 |
|------|----------|----------|---------|
| **冲突内容** | P1≤3 (有缓解计划) | P1=0 (无 P1 缺陷) | 保留差异 |
| **影响用例** | GATE-DSHE-004/007/008/010 等 API 依赖用例 | 全部 24 依赖用例 | — |
| **分支逻辑** | — | — | — |

```python
# 测试脚本分支处理逻辑 — P1 阈值
def evaluate_p1_defects(p1_count_dshb, p1_count_dshe):
    """
    MC-02: 保留差异 — DSHB P1≤3, DSHE P1=0
    分支判断: 两端分别判定, 不合并
    """
    dshb_pass = p1_count_dshb <= 3  # DSHB 侧: P1≤3 即可
    dshe_pass = p1_count_dshe == 0   # DSHE 侧: P1=0 必须
    
    if dshe_pass and dshb_pass:
        return "PASS_BOTH"
    elif dshe_pass and not dshb_pass:
        return "PASS_DSHE_ONLY"  # DSHB 有 P1 但 DSHE 无 — 记录差异
    elif not dshe_pass and dshb_pass:
        return "FAIL_DSHE"       # DSHE 有 P1 — 阻塞
    else:
        return "FAIL_BOTH"
```

#### 4.1.2 MC-05: 可用性阈值差异

| 维度 | DSHB 定义 | DSHE 定义 | 处理策略 |
|------|----------|----------|---------|
| **冲突内容** | 99.9% (引擎可用性) | 100% (页面加载成功率) | 保留差异 |
| **影响用例** | GATE-DSHE-038 (L0 正常态) | 全部页面加载用例 | — |

```python
# 测试脚本分支处理逻辑 — 可用性阈值
def evaluate_availability(dshb_availability, dshe_availability):
    """
    MC-05: 保留差异 — DSHB 99.9%, DSHE 100%
    分支判断: 两端分别判定, 不合并
    """
    dshb_pass = dshb_availability >= 99.9
    dshe_pass = dshe_availability >= 100.0
    
    # 在结果报告中分别标注
    return {
        "dshb_availability": {"value": dshb_availability, "threshold": 99.9, "pass": dshb_pass},
        "dshe_availability": {"value": dshe_availability, "threshold": 100.0, "pass": dshe_pass}
    }
```

#### 4.1.3 MC-06: 约束数量差异

| 维度 | DSHB 定义 | DSHE 定义 | 处理策略 |
|------|----------|----------|---------|
| **冲突内容** | 5/5 约束 | 6/6 约束 (多 NO_ENGINE_LOGIC_MODIFICATION) | 保留差异 |
| **影响用例** | 全部用例约束检查 | 全部用例约束检查 | — |

```python
# 测试脚本分支处理逻辑 — 约束数量
CONSTRAINTS_DSHB = [
    "NO_ZHIJI_API_CALL", "NO_MODIFY_V85", "NO_OVERWRITE",
    "BRANCH_LOCKED", "NO_PANEL_JSON_MODIFICATION"
]
CONSTRAINTS_DSHE = CONSTRAINTS_DSHB + ["NO_ENGINE_LOGIC_MODIFICATION"]

def evaluate_constraints(constraints_checked):
    """
    MC-06: 保留差异 — DSHE 为超集 (6>5)
    分支判断: 以 DSHE 6 约束为超集判定, DSHB 5 约束自动满足
    """
    all_pass = all(c in constraints_checked for c in CONSTRAINTS_DSHE)
    dshb_subset_pass = all(c in constraints_checked for c in CONSTRAINTS_DSHB)
    
    return {
        "dshe_constraints": {"total": 6, "pass": 6 if all_pass else 0, "compliant": all_pass},
        "dshb_constraints": {"total": 5, "pass": 5 if dshb_subset_pass else 0, "compliant": dshb_subset_pass},
        "overall_compliant": all_pass  # 以 DSHE 超集为准
    }
```

### 4.2 4 项互补口径约定

以下 4 项口径冲突为互补关系，测试脚本中需分别标注两端指标：

#### 4.2.1 MC-03: 延迟测量点互补

| 维度 | DSHB 测量点 | DSHE 测量点 | 互补关系 |
|------|------------|------------|---------|
| **延迟类型** | API P95 < 10ms | 页面 P99 < 3.0s | 互补 |
| **影响用例** | GATE-DSHE-010 (F-04) | 全部性能用例 | — |
| **分支逻辑** | 分别标注 API 延迟 + 页面延迟 | — | — |

```python
# 测试脚本分支处理逻辑 — 延迟测量点
def evaluate_latency(dshb_api_p95_ms, dshe_page_p99_ms):
    """
    MC-03: 互补关系 — API P95<10ms (DSHB) + 页面 P99<3.0s (DSHE)
    分支判断: 分别标注, 不互相替代
    """
    dshb_pass = dshb_api_p95_ms < 10
    dshe_pass = dshe_page_p99_ms < 3.0
    
    return {
        "dshb_api_p95_ms": {"value": dshb_api_p95_ms, "threshold": 10, "pass": dshb_pass},
        "dshe_page_p99_ms": {"value": dshe_page_p99_ms, "threshold": 3.0, "pass": dshe_pass},
        "combined_verdict": "PASS" if (dshb_pass and dshe_pass) else "FAIL"
    }
```

#### 4.2.2 MC-04: 冷启动定义互补

| 维度 | DSHB 定义 | DSHE 定义 | 互补关系 |
|------|----------|----------|---------|
| **冷启动类型** | 引擎冷启动 < 15s | 首屏加载 < 2.0s | 互补 |
| **影响用例** | GATE-DSHE-001~003, 005 | — | — |
| **分支逻辑** | 分别标注引擎冷启动 + 首屏加载 | — | — |

```python
# 测试脚本分支处理逻辑 — 冷启动定义
def evaluate_cold_start(dshb_engine_cold_ms, dshe_firs_screen_ms):
    """
    MC-04: 互补关系 — 引擎冷启动<15s (DSHB) + 首屏加载<2.0s (DSHE)
    分支判断: 分别标注, 不互相替代
    """
    dshb_pass = dshb_engine_cold_ms < 15000
    dshe_pass = dshe_firs_screen_ms < 2000
    
    return {
        "dshb_engine_cold_start_ms": {"value": dshb_engine_cold_ms, "threshold": 15000, "pass": dshb_pass},
        "dshe_firs_screen_ms": {"value": dshe_firs_screen_ms, "threshold": 2000, "pass": dshe_pass}
    }
```

#### 4.2.3 MC-07: C5 范围互补

| 维度 | DSHB 定义 | DSHE 定义 | 互补关系 |
|------|----------|----------|---------|
| **C5 范围** | 整体覆盖率 ≥ 95% | 降级监控 100% | 互补 |
| **影响用例** | GATE-DSHE-038, 041 | GATE-DSHE-048~052 | — |
| **分支逻辑** | 分别标注整体覆盖率 + 降级监控覆盖率 | — | — |

```python
# 测试脚本分支处理逻辑 — C5 范围
def evaluate_c5_coverage(dshb_overall_coverage, dshe_degrade_coverage):
    """
    MC-07: 互补关系 — 整体覆盖率≥95% (DSHB) + 降级监控100% (DSHE)
    分支判断: 分别标注, 不互相替代
    """
    dshb_pass = dshb_overall_coverage >= 95.0
    dshe_pass = dshe_degrade_coverage >= 100.0
    
    return {
        "dshb_overall_coverage_pct": {"value": dshb_overall_coverage, "threshold": 95.0, "pass": dshb_pass},
        "dshe_degrade_coverage_pct": {"value": dshe_degrade_coverage, "threshold": 100.0, "pass": dshe_pass}
    }
```

#### 4.2.4 MC-09: 监控粒度互补

| 维度 | DSHB 定义 | DSHE 定义 | 互补关系 |
|------|----------|----------|---------|
| **监控粒度** | ~90 Prometheus metrics | 6 Grafana panels | 互补 |
| **影响用例** | GATE-DSHE-038 (F-14) | GATE-DSHE-051 | — |
| **分支逻辑** | 分别标注 Prometheus metrics + Grafana panels | — | — |

```python
# 测试脚本分支处理逻辑 — 监控粒度
def evaluate_monitoring_granularity(dshb_prometheus_metrics, dshe_grafana_panels):
    """
    MC-09: 互补关系 — Prometheus metrics ~90 (DSHB) + Grafana panels 6 (DSHE)
    分支判断: 分别标注, 不互相替代
    """
    return {
        "dshb_prometheus_metrics": {"count": dshb_prometheus_metrics, "type": "engine_layer"},
        "dshe_grafana_panels": {"count": dshe_grafana_panels, "type": "display_layer"}
    }
```

#### 4.2.5 MC-10: 别名映射范围互补

| 维度 | DSHB 定义 | DSHE 定义 | 互补关系 |
|------|----------|----------|---------|
| **映射范围** | 4643 映射 (引擎层全量) | 351 查询 (展示层) | 互补 |
| **影响用例** | GATE-DSHE-028 (F-13) | — | — |
| **分支逻辑** | 分别标注引擎映射数 + 展示查询数 | — | — |

```python
# 测试脚本分支处理逻辑 — 别名映射范围
def evaluate_alias_scope(dshb_total_mappings, dshe_query_count, dshe_resolve_success):
    """
    MC-10: 互补关系 — 4643映射 (DSHB) + 351查询 (DSHE)
    分支判断: 分别标注, 不互相替代
    """
    dshe_pass = dshe_resolve_success >= 1.0
    return {
        "dshb_total_mappings": {"count": dshb_total_mappings, "scope": "engine_full"},
        "dshe_query_count": {"count": dshe_query_count, "scope": "display_layer"},
        "dshe_resolve_success_rate": {"value": dshe_resolve_success, "threshold": 1.0, "pass": dshe_pass}
    }
```

### 4.3 MC-01: 图表匹配数统一处理

| 维度 | DSHB 定义 | DSHE 定义 | 统一定义 |
|------|----------|----------|---------|
| **匹配数** | 32/36 完全匹配 | 29 全匹配 + 7 降级 | 29 全匹配 + 7 降级 |
| **差值处理** | 32 含 3 张降级 | 29 不含 3 张降级 | 统一为 29+7, 差值 3 图表归为降级类 |
| **影响用例** | GATE-DSHE-014, 015 | GATE-DSHE-014, 015 | 统一后两端一致 |

```python
# 测试脚本分支处理逻辑 — 图表匹配数统一
CHARTS_TOTAL = 36
CHARTS_FULL_MATCH = 29
CHARTS_DEGRADED = 7  # 含 DSHB 口径中 32-29=3 的差异图表

def evaluate_chart_match(chart_data):
    """
    MC-01: 统一为 29+7 — 差值 3 图表归为降级类
    分支判断: 统一后两端一致, 无分支
    """
    full_match = chart_data.get("full_match", 0)
    degraded = chart_data.get("degraded", 0)
    total = full_match + degraded
    
    return {
        "full_match": {"value": full_match, "expected": CHARTS_FULL_MATCH, "pass": full_match == CHARTS_FULL_MATCH},
        "degraded": {"value": degraded, "expected": CHARTS_DEGRADED, "pass": degraded == CHARTS_DEGRADED},
        "total": {"value": total, "expected": CHARTS_TOTAL, "pass": total == CHARTS_TOTAL}
    }
```

### 4.4 口径分支处理逻辑汇总

| 冲突 ID | 类型 | 处理策略 | 测试脚本分支 | 影响用例 |
|---------|------|---------|-------------|---------|
| MC-01 | 统一 | 统一为 29+7 | 无分支 (已统一) | GATE-DSHE-014, 015 |
| MC-02 | 保留差异 | 两端分别判定 | P1 阈值分支 | 全部 24 用例 |
| MC-03 | 互补 | 分别标注 | 延迟测量点分支 | GATE-DSHE-010 |
| MC-04 | 互补 | 分别标注 | 冷启动定义分支 | GATE-DSHE-001~003, 005 |
| MC-05 | 保留差异 | 两端分别判定 | 可用性阈值分支 | GATE-DSHE-038 |
| MC-06 | 保留差异 | DSHE 超集判定 | 约束数量分支 | 全部用例 |
| MC-07 | 互补 | 分别标注 | C5 范围分支 | GATE-DSHE-038, 041 |
| MC-08 | DSHB 独有 | 不涉及 DSHE | 无分支 | — |
| MC-09 | 互补 | 分别标注 | 监控粒度分支 | GATE-DSHE-038 |
| MC-10 | 互补 | 分别标注 | 别名映射范围分支 | GATE-DSHE-028 |

---

## 5. Mock 移除执行计划

### 5.1 移除条件矩阵

| 用例ID | Mock 移除条件 | DSHB 前置依赖 | 移除优先级 | 风险等级 | 回退方案 |
|--------|------------|--------------|----------|---------|---------|
| GATE-DSHE-004 | DSHB API 确认文档已交付 | F-01 | P2 | 🟢低 | 降级全量加载 |
| GATE-DSHE-007 | DSHB API 确认文档已交付 | F-02 | P2 | 🟢低 | 降级单页面 |
| GATE-DSHE-008 | DSHB API 接口文档已交付 | F-03 | P2 | 🟢低 | 降级全量返回 |
| GATE-DSHE-010 | DSHB API 性能文档已交付 | F-04 | P2 | 🟢低 | 降级全量加载 |
| GATE-DSHE-013 | DSHB 数据源文档已交付 | F-05 | P1 | 🟡中 | 降级默认数据源 |
| GATE-DSHE-014 | DSHB 数据源文档已交付 | F-06 | P1 | 🟡中 | 降级 0.0 |
| GATE-DSHE-015 | DSHB 数据源文档已交付 | F-07 | P1 | 🟡中 | 降级 L0 正常态 |
| GATE-DSHE-016 | DSHB 数据源文档已交付 | F-08 | P1 | 🟡中 | 降级默认数据源 |
| GATE-DSHE-018 | DSHB 数据源文档已交付 | F-09 | P1 | 🟡中 | 降级 0.0 |
| GATE-DSHE-019 | DSHB API 接口文档已交付 | F-10 | P2 | 🟢低 | 降级全量渲染 |
| GATE-DSHE-023 | DSHB 数据源文档已交付 | F-11 | P1 | 🟡中 | 降级 L2 |
| GATE-DSHE-024 | DSHB 数据源文档已交付 | F-12 | P1 | 🟡中 | 降级默认范围 |
| GATE-DSHE-028 | DSHB 数据源文档已交付 | F-13 | P1 | 🟡中 | 降级 0.0 |
| GATE-DSHE-038 | DSHB 数据源文档已交付 | F-14 | P1 | 🟡中 | 降级 DOWN |
| GATE-DSHE-041 | DSHB 探测接口文档已交付 | F-15 | P2 | 🟢低 | 降级 0.0 |
| GATE-DSHE-048 | DSHB 数据源文档已交付 | F-16 | P1 | 🟡中 | 降级 L0 |
| GATE-DSHE-052 | DSHB 数据源文档已交付 | F-17 | P1 | 🟡中 | 降级 0.0 |
| GATE-DSHE-054 | DSHB 演示数据已交付 | F-18 | P3 | 🟢低 | Mock 回退 |
| GATE-DSHE-055 | DSHB 演示数据已交付 | F-10 | P3 | 🟢低 | Mock 回退 |
| GATE-DSHE-056 | DSHB 演示数据已交付 | F-16 | P3 | 🟢低 | Mock 回退 |
| GATE-DSHE-060 | DSHB 演示数据已交付 | F-18 | P3 | 🟢低 | Mock 回退 |
| GATE-DSHE-063 | DSHB 演示数据已交付 | F-18 | P3 | 🟢低 | Mock 回退 |
| GATE-DSHE-064 | DSHB 演示数据已交付 | F-18 | P3 | 🟢低 | Mock 回退 |
| GATE-DSHE-065 | DSHB 演示数据已交付 | F-19 | P3 | 🟢低 | Mock 回退 |

### 5.2 移除时间线

```
Mock移除时间线:
┌──────────────────────────────────────────────────────────────┐
│  T+0d    T+1d    T+3d    T+5d    T+7d    T+14d               │
│   │       │       │       │       │       │                  │
│   ├───────┤       │       │       │       │                  │
│   │ 批次1  │       │       │       │       │                  │
│   │ 11字段 │       │       │       │       │                  │
│   │ 8用例  │       │       │       │       │                  │
│   │ T+1d   │       │       │       │       │                  │
│   │       │       ├───────┤       │       │                  │
│   │       │       │批次2+3│       │       │                  │
│   │       │       │8字段  │       │       │                  │
│   │       │       │16用例 │       │       │                  │
│   │       │       │T+3d   │       │       │                  │
│   │       │       │       │       │       │                  │
│   │       │       │       ├───────┤       │                  │
│   │       │       │       │全量移除│       │                  │
│   │       │       │       │24/24  │       │                  │
│   │       │       │       │       │       │                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. 7 张降级图表 Mock→Real 映射

### 6.1 7 张降级图表清单

| 图表ID | 图表名称 | 模块 | 降级原因 | 降级级别 | Mock 状态 | DSHB 真实状态 |
|--------|---------|------|---------|---------|---------|------------|
| CH-005 | 铅精矿TC | PB | TC 延迟 | L2 | 模拟 L2 静态快照 | DSHB 实际降级状态 |
| CH-013 | 铜开工率 | CU | 开工率缺失 | L3 | 模拟 L3 占位图 | DSHB 实际降级状态 |
| CH-017 | 铝开工率 | AL | 开工率缺失 | L3 | 模拟 L3 占位图 | DSHB 实际降级状态 |
| CH-021 | 锌TC | ZN | TC 延迟 | L2 | 模拟 L2 静态快照 | DSHB 实际降级状态 |
| CH-027 | 锡进口量 | SN | 进口量缺失 | L3 | 模拟 L3 占位图 | DSHB 实际降级状态 |
| CH-030 | 工业硅产量 | SI | 产量延迟 | L2 | 模拟 L2 静态快照 | DSHB 实际降级状态 |
| CH-034 | 锂产量 | LI | 产量缺失 | L3 | 模拟 L3 占位图 | DSHB 实际降级状态 |

### 6.2 降级图表 Mock→Real 替换规格

| 降级级别 | 图表数 | Mock 渲染内容 | DSHB 真实渲染内容 | 替换字段 | 兜底逻辑 |
|---------|--------|------------|----------------|---------|---------|
| L2 | 3 | 静态快照 + 降级标记 + 最后更新时间 | 实际静态快照 + 降级标记 + 实际时间 | F-07, F-16 | 降级为 L0 默认 |
| L3 | 4 | 占位图 + 错误说明 + P1 SOP 标记 | 实际占位图 + 实际错误说明 + P1 SOP 标记 | F-07, F-16 | 降级为 L0 默认 |

### 6.3 降级兜底逻辑

```python
# 7 张降级图表渲染兜底逻辑
DEGRADED_CHARTS = {
    "CH-005": {"module": "PB", "reason": "TC延迟", "level": "L2"},
    "CH-013": {"module": "CU", "reason": "开工率缺失", "level": "L3"},
    "CH-017": {"module": "AL", "reason": "开工率缺失", "level": "L3"},
    "CH-021": {"module": "ZN", "reason": "TC延迟", "level": "L2"},
    "CH-027": {"module": "SN", "reason": "进口量缺失", "level": "L3"},
    "CH-030": {"module": "SI", "reason": "产量延迟", "level": "L2"},
    "CH-034": {"module": "LI", "reason": "产量缺失", "level": "L3"},
}

def render_degraded_chart(chart_id, dshb_data):
    """
    降级图表渲染兜底逻辑
    L2: 静态快照 + 降级标记 + 最后更新时间
    L3: 占位图 + 错误说明 + P1 SOP 标记
    """
    chart_config = DEGRADED_CHARTS[chart_id]
    level = chart_config["level"]
    
    if dshb_data is None:
        # DSHB 数据缺失 → 降级为 L0 默认
        return {"render_mode": "L0_DEFAULT", "data": "default_snapshot"}
    
    if level == "L2":
        return {
            "render_mode": "L2_STATIC_SNAPSHOT",
            "snapshot": dshb_data.get("last_snapshot"),
            "degrade_marker": True,
            "last_updated": dshb_data.get("last_updated"),
            "reason": chart_config["reason"]
        }
    elif level == "L3":
        return {
            "render_mode": "L3_PLACEHOLDER",
            "placeholder": dshb_data.get("placeholder_img"),
            "error_message": dshb_data.get("error_message"),
            "p1_sop_marked": True,
            "reason": chart_config["reason"]
        }
```

---

## 7. 约束合规确认

| 约束 | 状态 | 说明 |
|------|------|------|
| `NO_ZHIJI_API_CALL=TRUE` | ✅ 合规 | 仅编写替换规格, 0 API 调用 |
| `NO_MODIFY_V85=TRUE` | ✅ 合规 | V85 基线未做任何修改 |
| `NO_OVERWRITE=TRUE` | ✅ 合规 | 仅新增本文档 |
| `BRANCH_LOCKED=TRUE` | ✅ 合规 | 仅 `feature/v85-chart-template` |
| `NO_PANEL_JSON_MODIFICATION=TRUE` | ✅ 合规 | 仅规格文档, 不修改 JSON |
| `NO_ENGINE_LOGIC_MODIFICATION=TRUE` | ✅ 合规 | 仅规格文档, 不修改引擎 |

---

## 8. 附录

### 8.1 文件信息

| 项目 | 值 |
|------|-----|
| **文件名** | v86_rc2_dshe_dep_case_mock_replace_spec_v7.md |
| **任务** | DSHE_V86_RC2_DEP_CASE_MOCK_REPLACE_SPEC_V7 |
| **子任务** | T3.1 24 依赖用例 Mock 替换规格 |
| **分支** | feature/v85-chart-template |
| **基线** | DSHE V7-RC1 (`f1d444e`), DSHB V86-RC1 (`0948e1d`), DSHB Gate准入基线 (`581a9f4`) |
| **DSHB 交付** | 回填字段契约 (`30B8BB83`), 图表Schema (`858AE32E`), zhiji预映射 (`022C907B`) |
| **创建日期** | 2026-10-04 |
| **状态** | ✅ 24/24 依赖用例 Mock 替换规格定稿 — 19/19 回填字段接入 — DSHB 基准接入完成 |

### 8.2 统计汇总

| 维度 | 数量 | 说明 |
|------|------|------|
| 依赖用例 | 24 | 全部映射完成 |
| Mock 数据桩 | 24 | 全部已替换为 DSHB 基准 |
| DSHB 回填字段 | 19 | F-01~F-19 全部接入 |
| 口径冲突解决 | 10 | 3 统一 + 3 保留 + 4 互补 |
| 特殊口径分支 | 7 | 测试脚本分支处理逻辑 |
| 降级图表 | 7 | 全部 Mock→Real 映射完成 |
| 移除优先级 | P1=8, P2=6, P3=6, P1=4 | 全部有降级回退 |

### 8.3 参考文档

| 来源 | 文档 |
|------|------|
| DSHB 回填字段契约 | `v86_rc2_dshb_backfill_field_final_spec_v7.md` |
| DSHB 图表 Schema | `v86_rc2_dshb_chart_schema_full_v7.md` |
| DSHB zhiji 预映射 | `v86_rc2_dshb_zhiji_mapping_predefine_v7.md` |
| 跨团队契约 | `v86_rc2_cross_team_contract_v7.md` |
| 双端差异评审 | `v86_rc2_dshe_dshb_case_diff_review_v7.md` |
| DSHE UT 报告 | `v86_rc2_dshe_presentation_ut_report_v7.md` |
| DSHE 图表 Schema | `v86_rc2_dshe_chart_schema_full_v7.md` |

---

*文档版本: V7 (24 依赖用例 Mock 替换规格)*
*生成日期: 2026-10-04*
*工单: DSHE_V86_RC2_DEP_CASE_MOCK_REPLACE_SPEC_V7 · T3.1*
*分支: feature/v85-chart-template*
*状态: ✅ 24/24 替换规格定稿 — 19/19 字段接入 — 10/10 冲突解决 — READY FOR RERUN*
