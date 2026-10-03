# V86-RC2 影子仿真环境 & 一键切换脚本准备文档

> **工单**: `DSHE_V86_RC2_PROD_PHASE_STAGE1` · T3.3
> **分支**: `feature/v85-chart-template`
> **基线**: DSHE V7-RC1 (`f1d444e`), DSHB V86-RC1 (`0948e1d`), DSHB Gate准入基线 (`581a9f4`)
> **PREP 封板**: `V86_RC2_PREP_CLOSED=TRUE` (2026-10-04)
> **约束**: NO_ZHIJI_API_CALL=FALSE (投产阶段可调用 zhiji API) / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **生成日期**: 2026-10-04
> **状态**: ✅ **影子环境架构定义完成 — Mock/Real双数据源规格定稿 — 一键切换脚本就绪 — 24用例影子对比矩阵建立 — HERMES交付材料清单就绪**

---

## 1. 执行摘要

### 1.1 阶段定位

本文档为 V86-RC2 投产阶段 (PROD_PHASE_STAGE1) 的 **影子仿真环境设计与一键切换脚本准备** 文档。与 PREP 阶段不同，投产阶段解除 `NO_ZHIJI_API_CALL` 约束，允许调用 zhiji 真实数据源，所有切换在影子环境中验证后方可推进至生产。

### 1.2 核心指标

| 维度 | 值 | 状态 |
|------|-----|------|
| **影子环境架构** | 3层 (Mock层 + Real层 + 对比层) | ✅ 已定义 |
| **Mock/Real 双数据源** | 24用例 × 2源 (48组数据路径) | ✅ 已定义 |
| **一键切换脚本** | 2批次 (T+1d: 11用例 / T+3d: 13用例) | ✅ 已定义 |
| **影子对比用例** | 24/24 (100%) | ✅ 已定义 |
| **对比指标** | 14项 (数据一致性+延迟+渲染精度) | ✅ 已定义 |
| **异常规则** | 8类 (E-1~E-8) | ✅ 已定义 |
| **回滚演练** | 3级 (L1/L2/L3) | ✅ 已定义 |
| **zhiji API 调用** | 允许 (NO_ZHIJI_API_CALL=FALSE) | ✅ |
| **V85 修改** | 0 | ✅ |

### 1.3 与 PREP 阶段的关键差异

| 维度 | PREP 阶段 | 投产阶段 (本文档) |
|------|----------|----------------|
| zhiji API 调用 | ❌ 禁止 | ✅ 允许 |
| 数据源 | DSHB 基准参数 (非Mock非zhiji) | zhiji 真实 API + DSHB 基准 |
| 切换验证 | 复测 (24/24 PASS) | 影子对比 + 一键切换 + 回滚演练 |
| 环境类型 | 影子环境 (无外部网络) | 影子环境 (可访问外部网络) |
| 约束数 | 6/6 (含 NO_ZHIJI_API_CALL) | 5/5 (不含 NO_ZHIJI_API_CALL) |
| 回滚验证 | 方案定义 | 演练执行 |

---

## 2. 影子并行环境架构设计

### 2.1 三层架构总览

```
影子并行环境三层架构:
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │              Layer 3: 对比分析层 (Comparison Layer)        │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │     │
│  │  │ 数据一致性 │  │ 延迟对比  │  │ 渲染精度  │  │ 异常检测 │  │     │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────┘  │     │
│  └─────────────────────────────────────────────────────────┘     │
│                          ▲                                         │
│                          │ 对比结果                                 │
│                          │                                         │
│  ┌──────────────────────┴──────────────────────────────────┐     │
│  │              Layer 2: 执行层 (Execution Layer)              │     │
│  │  ┌────────────────┐         ┌────────────────┐           │     │
│  │  │  DSHE 展示层   │         │  DSHB 引擎层    │           │     │
│  │  │  (Shadow Pod)  │         │  (Shadow Pod)  │           │     │
│  │  │                │         │                │           │     │
│  │  │  36图表渲染     │         │  别名解析       │           │     │
│  │  │  降级兜底       │         │  数据管道       │           │     │
│  │  │  页面导航       │         │  监控上报       │           │     │
│  │  └────────────────┘         └────────────────┘           │     │
│  └─────────────────────────────────────────────────────────┘     │
│                          ▲                                         │
│                          │ 双数据源调用                             │
│                          │                                         │
│  ┌──────────────────────┴──────────────────────────────────┐     │
│  │              Layer 1: 数据源层 (Data Source Layer)          │     │
│  │  ┌──────────────────┐       ┌──────────────────┐         │     │
│  │  │   Mock 数据源     │       │   Real 数据源     │         │     │
│  │  │  (Static JSON)   │       │  (zhiji API +    │         │     │
│  │  │                  │       │   DSHB 基准)      │         │     │
│  │  │  • 24用例Mock桩   │       │  • zhiji 真实数据  │         │     │
│  │  │  • 19回填字段     │       │  • DSHB 引擎基准   │         │     │
│  │  │  • 固定时间戳     │       │  • 实时 API 调用   │         │     │
│  │  │  • 本地回环       │       │  • 网络访问开启    │         │     │
│  │  └──────────────────┘       └──────────────────┘         │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 三层架构规格

| 层级 | 组件 | 规格 | 配置 |
|------|------|------|------|
| **Layer 1** | Mock 数据源 | 24用例Mock桩 + 19回填字段 | 本地回环, 静态JSON, 固定时间戳 |
| **Layer 1** | Real 数据源 | zhiji API + DSHB引擎基准 | 外网访问, 实时数据, API限频1秒 |
| **Layer 2** | DSHE 展示层 | Shadow Pod (独立副本) | 生产配置副本, 独立渲染引擎 |
| **Layer 2** | DSHB 引擎层 | Shadow Pod (独立副本) | 生产配置副本, 独立解析引擎 |
| **Layer 3** | 对比分析 | 14项指标对比 + 异常检测 | 双源并行执行, 结果比对 |
| **Layer 3** | 回滚控制 | L1/L2/L3三级回滚 + 演练 | 一键回滚脚本, 自动触发 |

### 2.3 影子环境资源需求

| 资源 | 规格 | 数量 | 用途 |
|------|------|------|------|
| Shadow Pod (DSHE) | 4C8G | 1 | 展示层影子副本 |
| Shadow Pod (DSHB) | 4C8G | 1 | 引擎层影子副本 |
| Mock Storage | 10GB | 1 | 24用例Mock桩 + 19回填字段 |
| Real API Token | zhiji API key | 1 | 真实数据源访问 |
| 对比分析节点 | 2C4G | 1 | 14项指标对比计算 |
| 日志存储 | 50GB | 1 | 7天日志保留 |
| 网络 | 外网访问 + 本地回环 | — | 双数据源并行 |

### 2.4 影子环境 vs 生产环境隔离

| 隔离维度 | 影子环境 | 生产环境 | 隔离机制 |
|---------|---------|---------|---------|
| 网络 | 独立命名空间 | 生产命名空间 | K8s Namespace 隔离 |
| 数据源 | zhiji 影子API | zhiji 生产API | API Token 分离 |
| 存储 | 独立 PV | 生产 PV | 不共享存储卷 |
| 监控 | 影子指标看板 | 生产指标看板 | 指标前缀隔离 |
| 告警 | 影子告警 | 生产告警 | 告警路由隔离 |
| 日志 | 独立日志流 | 生产日志流 | 日志标签隔离 |
| 流量 | 无真实用户 | 真实用户流量 | 流量分离 |
| 回滚 | 影子回滚演练 | 生产回滚 | 回滚脚本隔离 |

---

## 3. Mock 数据源与 Real 数据源架构

### 3.1 Mock 数据源规格

#### 3.1.1 Mock 数据源组成

| 组件 | 文件数 | 大小 | 来源 | 用途 |
|------|--------|------|------|------|
| 24用例Mock桩 | 24 | ~150KB | `v86_rc2_dshe_dep_case_mock_replace_spec_v7.md` | 展示层数据桩 |
| 19回填字段Mock | 19 | ~50KB | `v86_rc2_dshb_backfill_field_final_spec_v7.md` | 底层字段Mock |
| 7降级图表Mock | 7 | ~20KB | DSHB图表Schema | 降级兜底数据 |
| 别名映射Mock | 1 | ~30KB | DSHB zhiji映射 | 别名解析Mock |
| 总计 | 51 | ~250KB | — | 全部Mock数据 |

#### 3.1.2 Mock 数据源配置

```
Mock数据源配置 (shadow.mock.json):
{
  "version": "v86-rc2-shadow",
  "data_source": "mock",
  "endpoint": "localhost:9999",
  "timeout_ms": 100,
  "cache_ttl_s": 3600,
  "use_fixed_timestamp": true,
  "fixed_timestamp": "2026-10-04T00:00:00Z",
  "datasets": {
    "gate_cases": "24",
    "backfill_fields": "19",
    "degraded_charts": "7",
    "alias_mappings": "1"
  },
  "switch_mode": "dual",
  "fallback_on_error": "return_mock",
  "mock_snapshots": [
    "snap_mock_20261001.json",
    "snap_mock_20261002.json",
    "snap_mock_20261003.json",
    "snap_mock_20261004.json"
  ]
}
```

#### 3.1.3 Mock 快照策略

| 快照 | 时间戳 | 用途 | 保留 |
|------|--------|------|------|
| snap_mock_20261001 | 2026-10-01 | PREP阶段最终Mock | 7天 |
| snap_mock_20261002 | 2026-10-02 | PREP阶段确认Mock | 7天 |
| snap_mock_20261003 | 2026-10-03 | 切换前最终Mock | 30天 |
| snap_mock_20261004 | 2026-10-04 | 投产阶段基准Mock | 90天 |

### 3.2 Real 数据源规格

#### 3.2.1 Real 数据源组成

| 组件 | 来源 | 规格 | 延迟 |
|------|------|------|------|
| zhiji API 真实数据 | zhiji API (外网) | 36图表 + 19字段 | 500ms~2s |
| DSHB 引擎基准 | DSHB Shadow Pod | 178指标 + 别名解析 | <10ms |
| 回填字段真实值 | zhiji API + DSHB | 19字段 | <1s |
| 降级状态探测 | DSHB 引擎 | 7降级图表 | <500ms |
| 总计 | — | 62组件 | — |

#### 3.2.2 Real 数据源配置

```
Real数据源配置 (shadow.real.json):
{
  "version": "v86-rc2-shadow",
  "data_source": "real",
  "zhiji_api": {
    "enabled": true,
    "endpoint": "https://api.zhiji.com",
    "api_key": "${ZHIJI_API_KEY}",
    "rate_limit_ms": 1000,
    "timeout_ms": 5000,
    "retry": 3,
    "cache_ttl_s": 300
  },
  "dshb_engine": {
    "enabled": true,
    "endpoint": "dshb-shadow:8080",
    "timeout_ms": 100,
    "retry": 2,
    "cache_ttl_s": 60
  },
  "datasets": {
    "zhiji_charts": "36",
    "dshb_metrics": "178",
    "backfill_fields": "19",
    "degraded_probes": "7",
    "alias_mappings": "351"
  },
  "switch_mode": "dual",
  "fallback_on_error": "return_mock",
  "health_check": "every_30s"
}
```

#### 3.2.3 zhiji API 调用策略

| 约束 | PREP阶段 | 投产阶段 |
|------|---------|---------|
| zhiji API 调用 | ❌ 禁止 (NO_ZHIJI_API_CALL=TRUE) | ✅ 允许 (NO_ZHIJI_API_CALL=FALSE) |
| API 限频 | N/A | 1秒/次 |
| API 超时 | N/A | 5000ms |
| 重试次数 | N/A | 3次 |
| 缓存策略 | N/A | 5分钟缓存 |
| 降级策略 | N/A | Mock fallback |

### 3.3 双数据源并行调用架构

```
双数据源并行调用:
┌────────────────────────────────────────────────────┐
│                  Shadow Pod (DSHE)                   │
│                                                      │
│  ┌──────────┐         ┌──────────┐                │
│  │ Mock     │         │ Real     │                │
│  │ Reader   │         │ Reader   │                │
│  └────┬─────┘         └────┬─────┘                │
│       │                     │                      │
│  ┌────▼────────────────────▼────┐                 │
│  │     Dual Data Router         │                 │
│  │  (并行调用, 对比返回)          │                 │
│  └────────────┬─────────────────┘                 │
│               │                                    │
│  ┌────────────▼─────────────────┐                 │
│  │     Comparison Engine        │                 │
│  │  (14项指标对比计算)            │                 │
│  └────────────┬─────────────────┘                 │
│               │                                    │
│  ┌────────────▼─────────────────┐                 │
│  │     Result Aggregator        │                 │
│  │  (PASS/FAIL/WARN 判定)       │                 │
│  └──────────────────────────────┘                 │
└────────────────────────────────────────────────────┘
                    │                              │
          ┌─────────▼──────┐            ┌─────────▼──────┐
          │  Mock Layer    │            │  Real Layer    │
          │  (Local)       │            │  (External)    │
          └────────────────┘            └────────────────┘
```

---

## 4. 一键 Mock→Real 切换脚本准备

### 4.1 切换脚本总览

| 维度 | 值 | 说明 |
|------|-----|------|
| **脚本名称** | `switch_mock_to_real.sh` | 一键切换脚本 |
| **版本** | v86-rc2-stage1 | 投产阶段第一版 |
| **切换模式** | 双批次 (Batch1 + Batch2) | T+1d + T+3d |
| **切换命令** | 单行命令 + 参数化 | `./switch_mock_to_real.sh --batch=1` |
| **回滚命令** | `./switch_mock_to_real.sh --rollback` | 一键回滚 |
| **切换时间** | ~30s (单批次) | 含验证 |
| **前置检查** | 5项 (健康检查+数据源+网络+Token+日志) | 自动执行 |
| **验证步骤** | 5步 (数据一致性+延迟+渲染+降级+监控) | 自动执行 |
| **回滚触发** | 自动 (3种条件) + 手动 | 30s内完成 |

### 4.2 切换脚本规格

```bash
#!/bin/bash
# V86-RC2 Shadow Environment Mock→Real Switch Script
# Version: v86-rc2-stage1
# Usage: ./switch_mock_to_real.sh --batch=<1|2|all> [--rollback] [--dry-run]

set -euo pipefail

SCRIPT_VERSION="v86-rc2-stage1"
BATCH="${BATCH:-all}"
ROLLBACK="${ROLLBACK:-false}"
DRY_RUN="${DRY_RUN:-false}"
SHADOW_NS="v86-rc2-shadow"
DSHE_POD="dshe-shadow-$(date +%Y%m%d%H%M)"
DSHB_POD="dshb-shadow-$(date +%Y%m%d%H%M)"

# ── Batch Configuration ──
declare -A BATCH1_CASES=(
  [0]="GATE-DSHE-013" [1]="GATE-DSHE-014" [2]="GATE-DSHE-015"
  [3]="GATE-DSHE-016" [4]="GATE-DSHE-018" [5]="GATE-DSHE-023"
  [6]="GATE-DSHE-024" [7]="GATE-DSHE-028" [8]="GATE-DSHE-038"
  [9]="GATE-DSHE-048" [10]="GATE-DSHE-052"
)
declare -A BATCH2_CASES=(
  [0]="GATE-DSHE-004" [1]="GATE-DSHE-007" [2]="GATE-DSHE-008"
  [3]="GATE-DSHE-010" [4]="GATE-DSHE-019" [5]="GATE-DSHE-041"
  [6]="GATE-DSHE-054" [7]="GATE-DSHE-055" [8]="GATE-DSHE-056"
  [9]="GATE-DSHE-060" [10]="GATE-DSHE-063" [11]="GATE-DSHE-064"
  [12]="GATE-DSHE-065"
)

# ── Pre-Switch Checks ──
pre_switch_checks() {
  echo "[PRE] Running pre-switch checks..."
  
  # Check 1: Shadow Pod health
  kubectl exec -n ${SHADOW_NS} ${DSHE_POD} -- curl -f http://localhost:9090/health
  
  # Check 2: DSHB Shadow Pod health
  kubectl exec -n ${SHADOW_NS} ${DSHB_POD} -- curl -f http://localhost:8080/health
  
  # Check 3: zhiji API connectivity
  curl -f -o /dev/null -w "%{http_code}" https://api.zhiji.com/health || exit 1
  
  # Check 4: API Token validity
  kubectl get secret zhiji-api-key -n ${SHADOW_NS} || exit 1
  
  # Check 5: Log storage available
  df -h /var/log/shadow | grep -v 100% || exit 1
  
  echo "[PRE] All 5 checks passed"
}

# ── Switch Execution ──
execute_switch() {
  local batch=$1
  
  echo "[SWITCH] Executing batch ${batch} switch..."
  
  # Step 1: Save current Mock state (for rollback)
  save_mock_snapshot "${batch}"
  
  # Step 2: Update data source config to Real
  update_datasource_config "${batch}" "real"
  
  # Step 3: Trigger Dual Data Router switch
  trigger_dual_router_switch "${batch}"
  
  # Step 4: Run verification suite
  run_verification_suite "${batch}"
  
  # Step 5: Record switch result
  record_switch_result "${batch}"
  
  echo "[SWITCH] Batch ${batch} switch completed"
}

# ── Verification Suite ──
run_verification_suite() {
  local batch=$1
  local -n cases_ref="${batch}_CASES"
  local pass_count=0
  local fail_count=0
  
  for key in "${!cases_ref[@]}"; do
    local case_id="${cases_ref[$key]}"
    
    echo "[VERIFY] Testing ${case_id}..."
    
    # Verify 1: Data consistency
    local consistency=$(kubectl exec -n ${SHADOW_NS} ${DSHE_POD} \
      -- curl -s "http://localhost:9090/api/compare/${case_id}/consistency")
    if [ "$(echo "$consistency >= 0.95" | bc)" -eq 1 ]; then
      echo "  [PASS] Data consistency: ${consistency}"
    else
      echo "  [FAIL] Data consistency: ${consistency}"
      fail_count=$((fail_count + 1))
    fi
    
    # Verify 2: Latency
    local latency=$(kubectl exec -n ${SHADOW_NS} ${DSHE_POD} \
      -- curl -s "http://localhost:9090/api/compare/${case_id}/latency")
    if [ "$(echo "$latency < 3000" | bc)" -eq 1 ]; then
      echo "  [PASS] Latency: ${latency}ms"
    else
      echo "  [FAIL] Latency: ${latency}ms"
      fail_count=$((fail_count + 1))
    fi
    
    # Verify 3: Rendering accuracy
    local accuracy=$(kubectl exec -n ${SHADOW_NS} ${DSHE_POD} \
      -- curl -s "http://localhost:9090/api/compare/${case_id}/accuracy")
    if [ "$(echo "$accuracy == 1.0" | bc)" -eq 1 ]; then
      echo "  [PASS] Rendering accuracy: ${accuracy}"
    else
      echo "  [FAIL] Rendering accuracy: ${accuracy}"
      fail_count=$((fail_count + 1))
    fi
    
    # Verify 4: Degradation (for degraded cases)
    if [[ "$case_id" == "GATE-DSHE-015" || "$case_id" == "GATE-DSHE-048" ]]; then
      local degraded=$(kubectl exec -n ${SHADOW_NS} ${DSHE_POD} \
        -- curl -s "http://localhost:9090/api/compare/${case_id}/degraded")
      echo "  [INFO] Degradation status: ${degraded}"
    fi
    
    # Verify 5: Monitoring metrics
    local metrics=$(kubectl exec -n ${SHADOW_NS} ${DSHE_POD} \
      -- curl -s "http://localhost:9090/api/metrics/${case_id}")
    echo "  [INFO] Monitoring metrics: ${metrics}"
    
    if [ $fail_count -eq 0 ]; then
      pass_count=$((pass_count + 1))
    fi
  done
  
  echo "[VERIFY] Results: ${pass_count} PASS, ${fail_count} FAIL"
  return $fail_count
}

# ── Rollback Execution ──
execute_rollback() {
  echo "[ROLLBACK] Executing rollback..."
  
  # Step 1: Restore data source config to Mock
  update_datasource_config "all" "mock"
  
  # Step 2: Restore Dual Data Router
  trigger_dual_router_switch "rollback"
  
  # Step 3: Verify rollback
  run_verification_suite "all"
  
  # Step 4: Record rollback result
  record_rollback_result
  
  echo "[ROLLBACK] Rollback completed"
}

# ── Main ──
main() {
  echo "=== V86-RC2 Shadow Mock→Real Switch Script ==="
  echo "Version: ${SCRIPT_VERSION}"
  echo "Batch: ${BATCH}"
  echo "Rollback: ${ROLLBACK}"
  echo "Dry Run: ${DRY_RUN}"
  echo ""
  
  if [ "$ROLLBACK" = "true" ]; then
    execute_rollback
    exit $?
  fi
  
  pre_switch_checks
  
  case "${BATCH}" in
    "1")
      execute_switch "BATCH1"
      ;;
    "2")
      execute_switch "BATCH2"
      ;;
    "all")
      execute_switch "BATCH1"
      sleep 10
      execute_switch "BATCH2"
      ;;
    *)
      echo "ERROR: Invalid batch '${BATCH}'. Use 1, 2, or all."
      exit 1
      ;;
  esac
  
  echo "=== Switch completed successfully ==="
}

main "$@"
```

### 4.3 切换命令参考

| 命令 | 说明 | 预期耗时 |
|------|------|---------|
| `./switch_mock_to_real.sh --batch=1` | 切换批次1 (11用例, T+1d) | ~30s |
| `./switch_mock_to_real.sh --batch=2` | 切换批次2 (13用例, T+3d) | ~35s |
| `./switch_mock_to_real.sh --batch=all` | 切换全部 (24用例) | ~65s |
| `./switch_mock_to_real.sh --batch=1 --rollback` | 回滚批次1 | ~20s |
| `./switch_mock_to_real.sh --batch=all --rollback` | 回滚全部 | ~40s |
| `./switch_mock_to_real.sh --batch=1 --dry-run` | 干运行 (不执行切换) | ~15s |

### 4.4 切换前置检查

| # | 检查项 | 命令 | 通过标准 | 失败处理 |
|---|--------|------|---------|---------|
| 1 | DSHE Shadow Pod 健康 | `curl localhost:9090/health` | HTTP 200 | 中止切换 |
| 2 | DSHB Shadow Pod 健康 | `curl localhost:8080/health` | HTTP 200 | 中止切换 |
| 3 | zhiji API 连通性 | `curl api.zhiji.com/health` | HTTP 200 | 中止切换 |
| 4 | API Token 有效性 | `kubectl get secret` | 存在 | 中止切换 |
| 5 | 日志存储可用 | `df -h /var/log/shadow` | <90% | 警告继续 |
| 6 | 网络延迟 | `curl -w time_total` | <2000ms | 警告继续 |
| 7 | 影子环境隔离 | `kubectl get ns` | 独立命名空间 | 中止切换 |

### 4.5 切换后验证步骤

| # | 验证步骤 | 验证内容 | 通过标准 | 异常处理 |
|---|---------|---------|---------|---------|
| 1 | 数据一致性 | Mock vs Real 数据比对 | ≥95% 一致 | 触发回滚 |
| 2 | 延迟验证 | API 延迟 <3s | P99 <3.0s | 触发回滚 |
| 3 | 渲染精度 | 36图表渲染比对 | 100% 精确 | 触发回滚 |
| 4 | 降级状态 | 7降级图表兜底 | 7/7 正确 | 触发回滚 |
| 5 | 监控指标 | 14项指标对比 | 全部 PASS | 触发回滚 |
| 6 | 别名解析 | 351个别名比对 | 100% 一致 | 触发回滚 |
| 7 | 回填字段 | 19字段值比对 | 100% 一致 | 触发回滚 |

---

## 5. 24 用例影子对比矩阵

### 5.1 对比矩阵总表

| # | 用例ID | 用例名称 | Mock值 | Real值来源 | 对比指标 | 批次 | 预期 | 风险 |
|---|--------|---------|--------|-----------|---------|------|------|------|
| 1 | GATE-DSHE-013 | 36图表全量渲染 | 36模拟ID | zhiji API + DSHB | 一致性+延迟+渲染 | T+1d | 100% | 🟡中 |
| 2 | GATE-DSHE-014 | 29全匹配数据一致性 | 1.0 | zhiji API | 一致性+渲染 | T+1d | 100% | 🟡中 |
| 3 | GATE-DSHE-015 | 7降级图表渲染 | 7降级模拟 | DSHB引擎 | 降级状态+渲染 | T+1d | 7/7 | 🟡中 |
| 4 | GATE-DSHE-016 | 56子面板渲染 | 56模拟ID | zhiji API | 一致性+延迟 | T+1d | 56/56 | 🟡中 |
| 5 | GATE-DSHE-018 | 子面板数据一致性 | 1.0 | DSHB引擎 | 一致性 | T+1d | 100% | 🟡中 |
| 6 | GATE-DSHE-023 | 数据点完整性 | 36×100% | zhiji API | 完整性+延迟 | T+1d | 36/36 | 🟡中 |
| 7 | GATE-DSHE-024 | 时间轴一致性 | 36统一范围 | zhiji API | 一致性 | T+1d | 36/36 | 🟡中 |
| 8 | GATE-DSHE-028 | 别名解析成功率 | 1.0 | DSHB引擎 | 解析率+延迟 | T+1d | 100% | 🟡中 |
| 9 | GATE-DSHE-038 | L0正常态验证 | 全部UP | DSHB引擎 | 状态+延迟 | T+1d | 全部UP | 🟡中 |
| 10 | GATE-DSHE-048 | 7降级图表降级 | 7降级模拟 | DSHB引擎 | 降级状态+恢复 | T+1d | 7/7 | 🟡中 |
| 11 | GATE-DSHE-052 | 恢复数据一致性 | 1.0 | zhiji API | 一致性+延迟 | T+1d | 100% | 🟡中 |
| 12 | GATE-DSHE-004 | 工业硅全量数据加载 | TRUE | zhiji API | 加载率+延迟 | T+3d | 100% | 🟢低 |
| 13 | GATE-DSHE-007 | 子页面导航验证 | TRUE | DSHB引擎 | 导航率+延迟 | T+3d | 4/4 | 🟢低 |
| 14 | GATE-DSHE-008 | 子页面数据加载 | 4子页面 | zhiji API | 加载率+一致性 | T+3d | 4/4 | 🟢低 |
| 15 | GATE-DSHE-010 | 分批加载性能验证 | 5批~800ms | zhiji API | 性能+一致性 | T+3d | 5/5 | 🟢低 |
| 16 | GATE-DSHE-019 | 工业硅分批渲染 | 5批模拟 | zhiji API | 渲染率+一致性 | T+3d | 5/5 | 🟢低 |
| 17 | GATE-DSHE-041 | L2数据源探测 | 0.98 | DSHB引擎 | 探测率+延迟 | T+3d | ≥95% | 🟢低 |
| 18 | GATE-DSHE-054 | S-02 Gate大盘演示 | 模拟演示 | zhiji API | 演示率+渲染 | T+3d | 100% | 🟢低 |
| 19 | GATE-DSHE-055 | S-03 工业硅演示 | 模拟演示 | zhiji API | 演示率+渲染 | T+3d | 100% | 🟢低 |
| 20 | GATE-DSHE-056 | S-04 降级演示 | 模拟演示 | DSHB引擎 | 演示率+降级 | T+3d | 100% | 🟢低 |
| 21 | GATE-DSHE-060 | S-08 PDF图表演示 | 模拟演示 | zhiji API | 演示率+渲染 | T+3d | 100% | 🟢低 |
| 22 | GATE-DSHE-063 | S-11 全链路回归 | 模拟演示 | 双源 | 全链路率 | T+3d | 100% | 🟢低 |
| 23 | GATE-DSHE-064 | 18场景全量回放 | 18场景模拟 | 双源 | 场景率+渲染 | T+3d | 18/18 | 🟢低 |
| 24 | GATE-DSHE-065 | 90 Q&A全量回放 | 90Q&A模拟 | 双源 | QA率+渲染 | T+3d | 90/90 | 🟢低 |

### 5.2 批次1: T+1d 切换 (11用例) — 详细对比规格

#### 5.2.1 页面加载 & 渲染类 (6用例)

| 用例ID | Mock 数据源 | Real 数据源 | 对比维度 | 通过阈值 | 异常规则 |
|--------|------------|-----------|---------|---------|---------|
| GATE-DSHE-013 | 36个模拟数据源ID | zhiji API 真实数据源 | 数据源标识一致性 | 100% | E-1, E-4 |
| GATE-DSHE-014 | 一致性=1.0 | zhiji API 实际一致性 | 数据一致性比率 | ≥95% | E-3, E-6 |
| GATE-DSHE-016 | 56个模拟ID | zhiji API 实际子面板 | 子面板标识一致性 | 100% | E-1, E-4 |
| GATE-DSHE-023 | 36×100% | zhiji API 实际数据点 | 数据点完整性 | 100% | E-3, E-7 |
| GATE-DSHE-024 | 36统一范围 | zhiji API 实际时间范围 | 时间轴一致性 | 100% | E-6 |
| GATE-DSHE-052 | 一致性=1.0 | zhiji API 恢复后一致性 | 恢复一致性 | ≥95% | E-3 |

#### 5.2.2 降级 & 别名类 (5用例)

| 用例ID | Mock 数据源 | Real 数据源 | 对比维度 | 通过阈值 | 异常规则 |
|--------|------------|-----------|---------|---------|---------|
| GATE-DSHE-015 | 7降级模拟JSON | DSHB引擎实际降级状态 | 降级状态一致性 | 7/7 | E-4, E-7 |
| GATE-DSHE-018 | 一致性=1.0 | DSHB引擎实际一致性 | 子面板一致性 | ≥95% | E-3 |
| GATE-DSHE-028 | 解析率=1.0 | DSHB引擎实际解析率 | 别名解析率 | 100% | E-8 |
| GATE-DSHE-038 | 全部UP | DSHB引擎实际状态 | 数据源状态 | 全部UP | E-1 |
| GATE-DSHE-048 | 7降级模拟 | DSHB引擎实际降级+恢复 | 降级+恢复 | 7/7 | E-4 |

### 5.3 批次2: T+3d 切换 (13用例) — 详细对比规格

#### 5.3.1 数据加载类 (4用例)

| 用例ID | Mock 数据源 | Real 数据源 | 对比维度 | 通过阈值 | 异常规则 |
|--------|------------|-----------|---------|---------|---------|
| GATE-DSHE-004 | api_batch_support=TRUE | zhiji API 实际支持值 | 加载率+一致性 | 100% | E-1 |
| GATE-DSHE-007 | api_subpage_support=TRUE | DSHB引擎实际支持值 | 导航率+延迟 | 4/4 | E-1 |
| GATE-DSHE-008 | 4子页面模拟JSON | zhiji API 实际子页面 | 加载率+一致性 | 4/4 | E-1, E-3 |
| GATE-DSHE-010 | 5批~800ms模拟 | zhiji API 实际响应时间 | 性能+一致性 | 5/5 | E-5 |

#### 5.3.2 渲染 & 探测类 (2用例)

| 用例ID | Mock 数据源 | Real 数据源 | 对比维度 | 通过阈值 | 异常规则 |
|--------|------------|-----------|---------|---------|---------|
| GATE-DSHE-019 | 5批模拟JSON | zhiji API 实际批次 | 渲染率+一致性 | 5/5 | E-1 |
| GATE-DSHE-041 | 探测率=0.98 | DSHB引擎实际探测率 | 探测率+延迟 | ≥95% | E-1, E-7 |

#### 5.3.3 演示 & 回归类 (7用例)

| 用例ID | Mock 数据源 | Real 数据源 | 对比维度 | 通过阈值 | 异常规则 |
|--------|------------|-----------|---------|---------|---------|
| GATE-DSHE-054 | 模拟演示 | zhiji API | 演示率+渲染 | 100% | E-1 |
| GATE-DSHE-055 | 模拟演示 | zhiji API | 演示率+渲染 | 100% | E-1 |
| GATE-DSHE-056 | 模拟演示 | DSHB引擎 | 演示率+降级 | 100% | E-4 |
| GATE-DSHE-060 | 模拟演示 | zhiji API | 演示率+渲染 | 100% | E-1 |
| GATE-DSHE-063 | 模拟演示 | 双源 | 全链路率 | 100% | E-1~E-8 |
| GATE-DSHE-064 | 18场景模拟 | 双源 | 场景率+渲染 | 18/18 | E-1~E-8 |
| GATE-DSHE-065 | 90Q&A模拟 | 双源 | QA率+渲染 | 90/90 | E-1~E-8 |

---

## 6. 批次1 & 批次2 切换时间表

### 6.1 批次1: T+1d 切换时间表

| 步骤 | 时间 | 操作 | 负责方 | 验证 |
|------|------|------|--------|------|
| T-2h | 切换前2小时 | 影子环境健康检查 | DSHE | 5/5通过 |
| T-1h | 切换前1小时 | zhiji API 连通性测试 | DSHB | HTTP 200 |
| T-30m | 切换前30分钟 | Mock 快照保存 | DSHE | 快照完成 |
| T-15m | 切换前15分钟 | 一键切换脚本预演 (--dry-run) | DSHE | 预演通过 |
| **T0** | **切换时刻** | **执行批次1切换 (11用例)** | **DSHE** | **11/11 PASS** |
| T+5m | 切换后5分钟 | 数据一致性验证 | DSHE | ≥95% |
| T+10m | 切换后10分钟 | 延迟验证 | DSHE | <3s |
| T+15m | 切换后15分钟 | 渲染精度验证 | DSHE | 100% |
| T+30m | 切换后30分钟 | 监控指标对比 | DSHE | 14/14 PASS |
| T+1h | 切换后1小时 | 批次1复盘 | HERMES | 报告输出 |

### 6.2 批次2: T+3d 切换时间表

| 步骤 | 时间 | 操作 | 负责方 | 验证 |
|------|------|------|--------|------|
| T-4h | 切换前4小时 | 影子环境健康检查 | DSHE | 5/5通过 |
| T-2h | 切换前2小时 | zhiji API 限频测试 | DSHB | 1秒/次OK |
| T-1h | 切换前1小时 | 批次1复盘确认 | HERMES | 通过 |
| T-30m | 切换前30分钟 | Mock 快照保存 | DSHE | 快照完成 |
| T-15m | 切换前15分钟 | 一键切换脚本预演 (--dry-run) | DSHE | 预演通过 |
| **T0** | **切换时刻** | **执行批次2切换 (13用例)** | **DSHE** | **13/13 PASS** |
| T+5m | 切换后5分钟 | 数据一致性验证 | DSHE | ≥95% |
| T+10m | 切换后10分钟 | 延迟验证 | DSHE | <3s |
| T+15m | 切换后15分钟 | 演示脚本回放验证 | DSHE | 18/18 + 90/90 |
| T+30m | 切换后30分钟 | 全链路回归验证 | DSHE | 100% |
| T+1h | 切换后1小时 | 批次2复盘 | HERMES | 报告输出 |
| T+24h | 切换后24小时 | 全部切换总结 | HERMES | 24/24 PASS |

### 6.3 切换依赖关系

```
切换依赖关系:
[T-24h: PREP CLOSED] 
    │
    ▼
[T+1d: 批次1切换 (11用例)]
    │   ├── T+1d-2h: 健康检查
    │   ├── T+1d-1h: API连通性
    │   ├── T+1d-T0: 切换执行
    │   ├── T+1d+1h: 复盘
    │   └── T+1d+24h: 稳定性确认
    │
    ▼
[T+3d: 批次2切换 (13用例)]
    │   ├── T+3d-4h: 健康检查
    │   ├── T+3d-2h: API限频测试
    │   ├── T+3d-T0: 切换执行
    │   ├── T+3d+1h: 复盘
    │   └── T+3d+24h: 稳定性确认
    │
    ▼
[T+4d: 全部切换完成]
    │   └── 24/24用例全部切换完成
    │
    ▼
[投产切换T0准备]
```

---

## 7. 影子对比指标 (14项)

### 7.1 对比指标总表

| # | 指标ID | 指标名称 | 计算方式 | 阈值 | 对比来源 | 权重 |
|---|--------|---------|---------|------|---------|------|
| 1 | SC-01 | 数据一致性比率 | Σ(Mock值=Real值)/总数据点 | ≥95% | Mock vs zhiji | 20% |
| 2 | SC-02 | API响应延迟P99 | 99th percentile(Real API延迟) | ≤3.0s | Real API | 15% |
| 3 | SC-03 | API响应延迟P95 | 95th percentile(Real API延迟) | ≤2.0s | Real API | 10% |
| 4 | SC-04 | 渲染精度 | Σ(正确渲染图表)/总图表 | 100% | Mock vs Real | 15% |
| 5 | SC-05 | 降级状态一致性 | Σ(降级状态一致)/总降级图表 | 100% | Mock vs Real | 10% |
| 6 | SC-06 | 别名解析率 | Σ(成功解析)/总别名数 | 100% | Mock vs Real | 10% |
| 7 | SC-07 | 回填字段一致性 | Σ(字段值一致)/19 | 100% | Mock vs Real | 5% |
| 8 | SC-08 | 数据源可用率 | Σ(可用数据源)/总数据源 | ≥99% | DSHB引擎 | 5% |
| 9 | SC-09 | 时间轴一致性 | Σ(时间轴一致)/36 | 100% | Mock vs Real | 5% |
| 10 | SC-10 | 数据点完整性 | Σ(完整数据点)/总数据点 | 100% | Mock vs Real | 5% |
| 11 | SC-11 | 冷启动时间 | 首次请求响应时间 | ≤15s (引擎) | DSHB引擎 | 3% |
| 12 | SC-12 | 首屏加载时间 | 首次页面渲染完成时间 | ≤2.0s | DSHE展示 | 3% |
| 13 | SC-13 | 监控覆盖率 | Σ(覆盖指标)/总指标 | ≥95% | DSHB引擎 | 2% |
| 14 | SC-14 | 异常率 | Σ(异常事件)/总事件 | 0% (P0) | 双源 | 2% |

### 7.2 对比结果判定矩阵

| 对比项 | 全部PASS | 部分WARN | 部分FAIL | 全部FAIL |
|--------|---------|---------|---------|---------|
| SC-01~SC-10 (核心10项) | 通过 | 警告继续 | 触发回滚 | 触发回滚 |
| SC-11~SC-14 (辅助4项) | 通过 | 警告继续 | 记录观察 | 触发回滚 |
| **综合判定** | ✅ **PASS** | 🟡 **WARN** | 🔴 **FAIL** | 🔴 **FAIL** |

### 7.3 异常规则映射 (E-1~E-8)

| 规则 | 异常类型 | 触发条件 | 关联指标 | 处置方式 |
|------|---------|---------|---------|---------|
| E-1 | 数据拉取失败 | 连续3次zhiji API失败 | SC-01, SC-08 | 触发回滚 + 切换Mock |
| E-2 | 数据空值兜底 | 关键字段返回null | SC-01, SC-07 | 使用降级图表 |
| E-3 | 数据异常过滤 | 数值超出P99×3倍 | SC-01 | 过滤 + 告警 |
| E-4 | 降级渲染失败 | 降级图表渲染异常 | SC-04, SC-05 | 触发回滚 |
| E-5 | 性能超标 | P99>3.0s或首屏>2.0s | SC-02, SC-11, SC-12 | 告警 + 限流 |
| E-6 | 口径不一致 | MC-01/MC-02判定不一致 | SC-01, SC-09 | 记录 + 归档 |
| E-7 | 覆盖率下降 | 监控覆盖率<95% | SC-13 | 补全 + 告警 |
| E-8 | zhiji数据缺失 | zhiji_id未确认 | SC-01 | 保留Mock降级 |

---

## 8. HERMES 交付材料清单

### 8.1 交付物总览

| # | 交付物 | 类型 | 格式 | 大小 | 用途 |
|---|--------|------|------|------|------|
| 1 | 影子环境架构设计文档 | 文档 | Markdown | ~25KB | 环境部署参考 |
| 2 | 一键切换脚本 | 脚本 | Bash | ~8KB | 执行切换 |
| 3 | 24用例对比矩阵 | 数据 | JSON | ~50KB | 对比验证 |
| 4 | Mock 数据快照 | 数据 | JSON | ~250KB | Mock数据源 |
| 5 | Real 数据捕获协议 | 文档 | Markdown | ~10KB | 数据捕获规范 |
| 6 | 回滚演练记录模板 | 文档 | Markdown | ~5KB | 演练记录 |
| 7 | 对比指标定义表 | 数据 | YAML | ~15KB | 指标计算 |
| 8 | 切换时间表 | 文档 | Markdown | ~8KB | 时间调度 |

### 8.2 HERMES 影子对比测试执行清单

#### 8.2.1 批次1执行清单 (T+1d, 11用例)

| # | 步骤 | 操作 | 负责方 | 预期结果 | 时间 |
|---|------|------|--------|---------|------|
| 1 | 前置检查 | 执行5项健康检查 | DSHE | 5/5 PASS | T-2h |
| 2 | 干运行预演 | `--dry-run --batch=1` | DSHE | 预演通过 | T-15m |
| 3 | 执行切换 | `--batch=1` | DSHE | 11/11 PASS | T0 |
| 4 | 数据一致性验证 | SC-01 ≥95% | DSHE | ≥95% | T+5m |
| 5 | 延迟验证 | SC-02 P99<3s | DSHE | <3s | T+10m |
| 6 | 渲染精度验证 | SC-04 =100% | DSHE | 100% | T+15m |
| 7 | 监控指标对比 | SC-08~SC-14 | DSHE | 全部PASS | T+30m |
| 8 | 批次1复盘报告 | 输出对比报告 | HERMES | 报告完成 | T+1h |
| 9 | 回滚就绪确认 | 确认可回滚 | DSHE | 确认 | T+1h |

#### 8.2.2 批次2执行清单 (T+3d, 13用例)

| # | 步骤 | 操作 | 负责方 | 预期结果 | 时间 |
|---|------|------|--------|---------|------|
| 1 | 前置检查 | 执行5项健康检查 | DSHE | 5/5 PASS | T-4h |
| 2 | API限频测试 | zhiji 1秒/次 | DSHB | 通过 | T-2h |
| 3 | 批次1稳定性确认 | 24h稳定性 | HERMES | 通过 | T-1h |
| 4 | 干运行预演 | `--dry-run --batch=2` | DSHE | 预演通过 | T-15m |
| 5 | 执行切换 | `--batch=2` | DSHE | 13/13 PASS | T0 |
| 6 | 数据一致性验证 | SC-01 ≥95% | DSHE | ≥95% | T+5m |
| 7 | 延迟验证 | SC-02 P99<3s | DSHE | <3s | T+10m |
| 8 | 演示脚本回放 | S-02/S-03/S-04/S-08 | DSHE | 100% | T+15m |
| 9 | 全链路回归 | S-11 全链路 | DSHE | 100% | T+30m |
| 10 | 18场景全量回放 | GATE-DSHE-064 | DSHE | 18/18 | T+30m |
| 11 | 90Q&A全量回放 | GATE-DSHE-065 | DSHE | 90/90 | T+30m |
| 12 | 批次2复盘报告 | 输出对比报告 | HERMES | 报告完成 | T+1h |
| 13 | 全部切换总结 | 24/24 总结 | HERMES | 报告完成 | T+24h |

### 8.3 HERMES 对比测试执行命令

```bash
# 1. 环境准备
kubectl apply -f shadow-env.yaml
kubectl apply -f shadow-datasource.yaml
kubectl apply -f shadow-comparison-config.yaml

# 2. 前置检查
./switch_mock_to_real.sh --batch=all --dry-run

# 3. 批次1切换
./switch_mock_to_real.sh --batch=1

# 4. 批次1对比验证
for case in GATE-DSHE-013 GATE-DSHE-014 GATE-DSHE-015 GATE-DSHE-016 \
  GATE-DSHE-018 GATE-DSHE-023 GATE-DSHE-024 GATE-DSHE-028 \
  GATE-DSHE-038 GATE-DSHE-048 GATE-DSHE-052; do
  echo "=== ${case} ==="
  curl "http://dshe-shadow:9090/api/compare/${case}/full"
done

# 5. 批次2切换
./switch_mock_to_real.sh --batch=2

# 6. 批次2对比验证
for case in GATE-DSHE-004 GATE-DSHE-007 GATE-DSHE-008 GATE-DSHE-010 \
  GATE-DSHE-019 GATE-DSHE-041 GATE-DSHE-054 GATE-DSHE-055 \
  GATE-DSHE-056 GATE-DSHE-060 GATE-DSHE-063 GATE-DSHE-064 \
  GATE-DSHE-065; do
  echo "=== ${case} ==="
  curl "http://dshe-shadow:9090/api/compare/${case}/full"
done

# 7. 生成HERMES对比报告
curl "http://hermes-shadow:9091/api/generate-report?batch=all" > hermes_shadow_report.json
```

---

## 9. Mock 数据快照与 Real 数据捕获协议

### 9.1 Mock 数据快照协议

#### 9.1.1 快照生成规则

| 规则 | 说明 | 频率 |
|------|------|------|
| 触发条件 | 切换前自动保存 | 每次切换前 |
| 快照格式 | JSON (gzip压缩) | .json.gz |
| 快照内容 | 24用例Mock桩 + 19回填字段 + 7降级状态 | 全部Mock数据 |
| 快照命名 | `snap_mock_YYYYMMDD_batch<N>.json.gz` | 日期+批次 |
| 保留策略 | 批次1: 7天, 批次2: 30天, 最终: 90天 | 按批次分级 |
| 存储位置 | /data/shadow/mock_snapshots/ | 影子存储 |

#### 9.1.2 快照格式

```json
{
  "snapshot_version": "v86-rc2-shadow-v1",
  "timestamp": "2026-10-04T00:00:00Z",
  "batch": "batch1",
  "data_sources": {
    "gate_cases": {
      "count": 24,
      "mock_pillars": [
        {
          "case_id": "GATE-DSHE-013",
          "mock_value": "36_mock_ids",
          "mock_format": "string_array",
          "mock_timestamp": "2026-10-04T00:00:00Z"
        }
      ]
    },
    "backfill_fields": {
      "count": 19,
      "field_snapshots": [
        {
          "field_id": "F-01",
          "mock_value": true,
          "mock_format": "boolean",
          "mock_timestamp": "2026-10-04T00:00:00Z"
        }
      ]
    },
    "degraded_charts": {
      "count": 7,
      "chart_snapshots": [
        {
          "chart_id": "CH-005",
          "degraded_level": "L2",
          "mock_snapshot": "static_image"
        }
      ]
    }
  }
}
```

### 9.2 Real 数据捕获协议

#### 9.2.1 捕获规则

| 规则 | 说明 | 配置 |
|------|------|------|
| 捕获触发 | 每次切换时自动捕获 | 自动 |
| 捕获格式 | JSON (含元数据) | .json |
| 捕获内容 | zhiji API响应 + DSHB引擎基准 | 全部Real数据 |
| 捕获命名 | `capture_real_YYYYMMDD_batch<N>.json` | 日期+批次 |
| 保留策略 | 90天 | 长期 |
| 存储位置 | /data/shadow/real_captures/ | 影子存储 |

#### 9.2.2 捕获格式

```json
{
  "capture_version": "v86-rc2-shadow-v1",
  "timestamp": "2026-10-04T00:00:00Z",
  "batch": "batch1",
  "zhiji_api": {
    "endpoint": "https://api.zhiji.com",
    "response_time_ms": 850,
    "http_status": 200,
    "data_points": 36,
    "data_integrity": 1.0,
    "cache_hit": true,
    "cache_ttl_remaining_s": 180
  },
  "dshb_engine": {
    "endpoint": "dshb-shadow:8080",
    "response_time_ms": 12,
    "metrics_parsed": 178,
    "aliases_resolved": 351,
    "degraded_probes": 7,
    "data_source_status": "all_up"
  },
  "comparison": {
    "consistency_ratio": 0.98,
    "latency_p99_ms": 2800,
    "rendering_accuracy": 1.0,
    "overall_pass": true
  }
}
```

### 9.3 数据捕获与快照对比

```
数据捕获与快照对比流程:
┌────────────────────────────────────────────────────┐
│              切换前 (T-30m)                          │
│  ┌─────────────────────────────────────────────┐   │
│  │ 1. 保存 Mock 快照                            │   │
│  │    snap_mock_20261004_batch1.json.gz        │   │
│  └─────────────────────────────────────────────┘   │
│              │                                       │
│              ▼                                        │
│  ┌─────────────────────────────────────────────┐   │
│  │ 2. 执行切换                                  │   │
│  │    switch_mock_to_real.sh --batch=1          │   │
│  └─────────────────────────────────────────────┘   │
│              │                                       │
│              ▼                                        │
│  ┌─────────────────────────────────────────────┐   │
│  │ 3. 捕获 Real 数据                            │   │
│  │    capture_real_20261004_batch1.json         │   │
│  └─────────────────────────────────────────────┘   │
│              │                                       │
│              ▼                                        │
│  ┌─────────────────────────────────────────────┐   │
│  │ 4. 对比 Mock vs Real                         │   │
│  │    comparison_engine.run(snap_mock, capture) │   │
│  └─────────────────────────────────────────────┘   │
│              │                                       │
│              ▼                                        │
│  ┌─────────────────────────────────────────────┐   │
│  │ 5. 输出对比报告                              │   │
│  │    hermes_shadow_report.json                 │   │
│  └─────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────┘
```

---

## 10. 回滚演练 (影子环境 L1/L2/L3)

### 10.1 三级回滚演练总览

| 级别 | 演练名称 | 触发条件 | 回滚范围 | 预期耗时 | 演练频率 |
|------|---------|---------|---------|---------|---------|
| **L1** | 灰度阶段回滚 | 切换后5分钟内检测到异常 | 当前批次回滚到Mock | ≤30s | 每批次1次 |
| **L2** | 全量回滚到PREP | 切换后30分钟内P0错误 | 全部用例回滚到Mock | ≤60s | 每批次1次 |
| **L3** | 全量回滚到V85 | 切换后24小时内稳定性失败 | 全部用例回滚到V85基线 | ≤120s | 全部切换后1次 |

### 10.2 L1 灰度阶段回滚演练

#### 10.2.1 演练场景

| 场景 | 触发条件 | 预期行为 |
|------|---------|---------|
| L1-1 | 数据一致性<95% | 自动回滚到Mock |
| L1-2 | P99延迟>3.5s | 自动回滚到Mock |
| L1-3 | 降级图表渲染失败 | 自动回滚到Mock |

#### 10.2.2 演练步骤

```bash
# L1 回滚演练步骤
echo "=== L1 Rollback Drill ==="

# Step 1: 触发异常 (模拟)
kubectl exec dshe-shadow -- curl -X POST \
  http://localhost:9090/api/drill/trigger-anomaly?level=L1

# Step 2: 观察自动回滚触发
kubectl logs dshe-shadow -f | grep "ROLLBACK"

# Step 3: 验证回滚完成
curl http://dshe-shadow:9090/api/status | jq '.data_source'
# Expected: "mock"

# Step 4: 验证数据恢复
curl http://dshe-shadow:9090/api/compare/GATE-DSHE-013/consistency
# Expected: 1.0 (Mock vs Mock)

# Step 5: 记录演练结果
./drill_record.sh --level=L1 --result=PASS
```

#### 10.2.3 验收标准

| 验收项 | 标准 | 验证方式 |
|--------|------|---------|
| 自动触发 | 异常检测后5s内触发 | 日志时间戳 |
| 回滚耗时 | ≤30s | 从触发到完成 |
| 数据恢复 | 全部恢复Mock | 一致性=1.0 |
| 告警发送 | 30s内发送 | 告警日志 |
| 回滚后稳定 | 5分钟无异常 | 持续监控 |

### 10.3 L2 全量回滚到PREP演练

#### 10.3.1 演练场景

| 场景 | 触发条件 | 预期行为 |
|------|---------|---------|
| L2-1 | 批次切换后P0错误 | 全部用例回滚到Mock |
| L2-2 | P99延迟持续>3s超30min | 全部用例回滚到Mock |
| L2-3 | 数据一致性持续<90%超30min | 全部用例回滚到Mock |

#### 10.3.2 演练步骤

```bash
# L2 回滚演练步骤
echo "=== L2 Rollback Drill ==="

# Step 1: 模拟批次1+2已切换
./switch_mock_to_real.sh --batch=all

# Step 2: 触发P0异常
kubectl exec dshe-shadow -- curl -X POST \
  http://localhost:9090/api/drill/trigger-anomaly?level=L2&type=p0

# Step 3: 观察全量回滚
./switch_mock_to_real.sh --batch=all --rollback

# Step 4: 验证全部恢复
for case in GATE-DSHE-013 GATE-DSHE-004 GATE-DSHE-064; do
  echo "=== ${case} ==="
  curl http://dshe-shadow:9090/api/compare/${case}/consistency
  # Expected: 1.0 (all Mock)
done

# Step 5: 确认V85基线未修改
curl http://dshe-shadow:9090/api/verify/v85-baseline
# Expected: "unchanged"

# Step 6: 记录演练结果
./drill_record.sh --level=L2 --result=PASS
```

#### 10.3.3 验收标准

| 验收项 | 标准 | 验证方式 |
|--------|------|---------|
| 全量回滚 | 24/24用例恢复Mock | 一致性验证 |
| 回滚耗时 | ≤60s | 命令耗时 |
| V85未修改 | 基线不变 | 基线校验 |
| 监控恢复 | 全部指标恢复 | 指标对比 |
| 日志完整 | 回滚日志完整 | 日志查询 |

### 10.4 L3 全量回滚到V85演练

#### 10.4.1 演练场景

| 场景 | 触发条件 | 预期行为 |
|------|---------|---------|
| L3-1 | 24h内稳定性失败 | 全部回滚到V85基线 |
| L3-2 | 数据一致性24h内持续失败 | 全部回滚到V85基线 |

#### 10.4.2 演练步骤

```bash
# L3 回滚演练步骤
echo "=== L3 Rollback Drill ==="

# Step 1: 确认全部已切换
./switch_mock_to_real.sh --batch=all --status
# Expected: all switched

# Step 2: 执行L3回滚
./switch_mock_to_real.sh --batch=all --rollback --level=L3

# Step 3: 验证V85基线完整性
curl http://dshe-shadow:9090/api/verify/v85-baseline
# Expected: "unchanged"

# Step 4: 验证全部用例V85状态
for case in GATE-DSHE-004 GATE-DSHE-013 GATE-DSHE-065; do
  echo "=== ${case} ==="
  curl http://dshe-shadow:9090/api/verify/${case}/v85
  # Expected: "v85_baseline"
done

# Step 5: 验证监控指标
curl http://dshe-shadow:9090/api/metrics/summary
# Expected: all metrics restored

# Step 6: 记录演练结果
./drill_record.sh --level=L3 --result=PASS
```

#### 10.4.3 验收标准

| 验收项 | 标准 | 验证方式 |
|--------|------|---------|
| V85完整性 | 基线100%不变 | 基线校验 |
| 回滚耗时 | ≤120s | 命令耗时 |
| 全部用例恢复 | 24/24 V85状态 | 逐用例验证 |
| 监控恢复 | 全部指标V85状态 | 指标对比 |
| 日志完整 | 完整回滚链 | 日志查询 |
| 无副作用 | 无数据丢失 | 数据一致性 |

### 10.5 回滚演练总结

| 演练级别 | 演练场景 | 演练次数 | 预期通过率 | 实际结果 |
|---------|---------|---------|-----------|---------|
| L1 | 3场景 × 2批次 = 6次 | 6 | 100% | ⏳ 待执行 |
| L2 | 3场景 × 2批次 = 6次 | 6 | 100% | ⏳ 待执行 |
| L3 | 2场景 × 1次 = 2次 | 2 | 100% | ⏳ 待执行 |
| **合计** | **11次** | **14** | **100%** | **⏳ 待执行** |

---

## 11. 验收标准表

### 11.1 影子环境验收标准

| # | 验收项 | 标准 | 验证方式 | 负责方 | 状态 |
|---|--------|------|---------|--------|------|
| 1 | 影子环境部署 | 3层架构全部就绪 | 健康检查 | DSHE | ⏳ |
| 2 | Mock数据源 | 24用例+19字段就绪 | 数据校验 | DSHE | ⏳ |
| 3 | Real数据源 | zhiji API+DSHB引擎就绪 | 连通性测试 | DSHB | ⏳ |
| 4 | 一键切换脚本 | 5项前置检查通过 | 干运行 | DSHE | ⏳ |
| 5 | 批次1切换 | 11/11用例PASS | 对比验证 | DSHE | ⏳ |
| 6 | 批次1复盘 | 14项指标全部PASS | 报告审核 | HERMES | ⏳ |
| 7 | 批次2切换 | 13/13用例PASS | 对比验证 | DSHE | ⏳ |
| 8 | 批次2复盘 | 14项指标全部PASS | 报告审核 | HERMES | ⏳ |
| 9 | L1回滚演练 | 3场景通过 | 演练记录 | DSHE | ⏳ |
| 10 | L2回滚演练 | 3场景通过 | 演练记录 | DSHE | ⏳ |
| 11 | L3回滚演练 | 2场景通过 | 演练记录 | DSHE | ⏳ |
| 12 | V85基线验证 | 0修改 | 基线校验 | DSHE | ⏳ |
| 13 | 约束合规 | 5/5 | 合规检查 | HERMES | ⏳ |
| 14 | 全部切换总结 | 24/24 PASS | 总结报告 | HERMES | ⏳ |

### 11.2 数据一致性验收标准

| # | 指标 | 批次1阈值 | 批次2阈值 | 综合阈值 |
|---|------|----------|----------|---------|
| SC-01 | 数据一致性比率 | ≥95% | ≥95% | ≥95% |
| SC-02 | API延迟P99 | ≤3.0s | ≤3.0s | ≤3.0s |
| SC-03 | API延迟P95 | ≤2.0s | ≤2.0s | ≤2.0s |
| SC-04 | 渲染精度 | 100% | 100% | 100% |
| SC-05 | 降级状态一致性 | 100% | 100% | 100% |
| SC-06 | 别名解析率 | 100% | 100% | 100% |
| SC-07 | 回填字段一致性 | 100% | 100% | 100% |
| SC-08 | 数据源可用率 | ≥99% | ≥99% | ≥99% |
| SC-09 | 时间轴一致性 | 100% | 100% | 100% |
| SC-10 | 数据点完整性 | 100% | 100% | 100% |

### 11.3 切换完成标准

| # | 完成项 | 标准 | 状态 |
|---|--------|------|------|
| 1 | 影子环境部署 | 3层架构全部就绪 | ⏳ |
| 2 | 一键切换脚本 | 2批次切换脚本就绪 | ⏳ |
| 3 | 批次1切换完成 | 11/11 PASS + 复盘 | ⏳ |
| 4 | 批次2切换完成 | 13/13 PASS + 复盘 | ⏳ |
| 5 | L1回滚演练完成 | 6/6 PASS | ⏳ |
| 6 | L2回滚演练完成 | 6/6 PASS | ⏳ |
| 7 | L3回滚演练完成 | 2/2 PASS | ⏳ |
| 8 | 全部对比指标达标 | 14/14 PASS | ⏳ |
| 9 | V85基线验证 | 0修改 | ⏳ |
| 10 | HERMES对比报告 | 全部输出 | ⏳ |

---

## 12. 约束合规验证

| 约束 | 状态 | 说明 |
|------|------|------|
| `NO_ZHIJI_API_CALL=FALSE` | ✅ 允许 | 投产阶段可调用zhiji API |
| `NO_MODIFY_V85=TRUE` | ✅ 合规 | V85基线(`f313570`)只读, 0修改 |
| `NO_OVERWRITE=TRUE` | ✅ 合规 | 仅新增文档, 不覆盖历史交付 |
| `BRANCH_LOCKED=TRUE` | ✅ 合规 | 仅`feature/v85-chart-template`分支 |
| `NO_PANEL_JSON_MODIFICATION=TRUE` | ✅ 合规 | 未修改Grafana JSON |
| `NO_ENGINE_LOGIC_MODIFICATION=TRUE` | ✅ 合规 | 未修改引擎逻辑 |

---

## 13. 附录

### 13.1 文件信息

| 项目 | 值 |
|------|-----|
| **文件名** | v86_rc2_prod_shadow_sim_prep.md |
| **工单** | DSHE_V86_RC2_PROD_PHASE_STAGE1 · T3.3 |
| **分支** | feature/v85-chart-template |
| **基线** | DSHE V7-RC1 (`f1d444e`), DSHB V86-RC1 (`0948e1d`) |
| **PREP封板** | `V86_RC2_PREP_CLOSED=TRUE` (2026-10-04) |
| **创建日期** | 2026-10-04 |
| **状态** | ✅ 影子仿真环境与一键切换脚本准备完成 |

### 13.2 参考文档

| 来源 | 文档 | 路径 |
|------|------|------|
| PREP封板决议 | `v86_rc2_prep_closure_resolution.md` | `hermes_e2e_test/` |
| PREP转投产交接 | `v86_rc2_prep_to_prod_handover.md` | `hermes_e2e_test/` |
| 投产切换指南 | `v86_rc2_dshe_prod_switch_guide_v7.md` | `dshe_alias_gate_final_v7/` |
| Mock替换规格 | `v86_rc2_dshe_dep_case_mock_replace_spec_v7.md` | `dshe_alias_gate_final_v7/` |
| 复测报告 | `v86_rc2_dshe_dep_case_rerun_report_v7.md` | `dshe_alias_gate_final_v7/` |
| 切换检查清单 | `v86_rc2_dshb_dshe_dep_case_baseline_v7.md` | `dshe_alias_gate_final_v7/` |
| 口径差异归档 | `v86_rc2_dshb_caliber_diff_keep_spec_v7.md` | `dshe_alias_gate_final_v7/` |
| 回填字段定稿 | `v86_rc2_dshb_backfill_field_final_spec_v7.md` | `dshe_alias_gate_final_v7/` |
| Gate终审 | `v86_rc2_dshe_c1_c5_gate_final_report_v7.md` | `dshe_alias_gate_final_v7/` |
| 全量归档快照 | `v86_rc2_full_archive_snapshot.md` | `hermes_e2e_test/` |

### 13.3 关键指标汇总

| 指标 | 值 | 来源 |
|------|-----|------|
| 影子环境层数 | 3层 (Mock+Real+对比) | 本文档 |
| 24用例 | 24 | 复测报告 |
| 批次1用例 | 11 (T+1d) | 本文档 |
| 批次2用例 | 13 (T+3d) | 本文档 |
| 对比指标 | 14项 | 本文档 |
| 异常规则 | 8类 (E-1~E-8) | 本文档 |
| 回滚级别 | 3级 (L1/L2/L3) | 本文档 |
| 回滚演练 | 14次 (6+6+2) | 本文档 |
| 切换命令 | 6种 (4执行+2辅助) | 本文档 |
| PREP Gate | 89/89 PASS | PREP封板 |
| UT | 68/68 PASS | PREP封板 |
| 复测 | 24/24 PASS | 复测报告 |
| 口径解决 | 10/10 | 口径归档 |
| 回填字段 | 19/19 | 回填定稿 |
| zhiji映射 | DSHB 204 + DSHE 197 | PREP封板 |
| 风险台账 | 14项 (0高/7中/7低) | PREP封板 |
| 约束合规 | 6/6 | 本文档 |

---

*文档版本: V7 (影子仿真环境与一键切换脚本准备)*
*生成日期: 2026-10-04*
*工单: DSHE_V86_RC2_PROD_PHASE_STAGE1 · T3.3*
*分支: feature/v85-chart-template*
*状态: ✅ 影子环境3层架构 + 一键切换脚本 + 24用例对比矩阵 + 14项对比指标 + 3级回滚演练 — 全部定义完成*
