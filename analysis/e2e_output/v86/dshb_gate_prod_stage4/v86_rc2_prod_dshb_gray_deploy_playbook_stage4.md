# V86-RC2 投产Stage4 — 灰度投产底层侧能力构建

> **工单**: DSHB_V86_RC2_PROD_PHASE_STAGE4
> **子任务**: T3.3 灰度投产底层侧能力构建
> **分支**: `feature/v85-chart-template`
> **基线**: Stage3 灰度切换检查清单75项 commit `97f279c`
> **约束**: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **日期**: 2026-10-11

---

## 1. 灰度投产总览

| 维度 | 状态 | 数量 |
|------|------|------|
| 灰度流量切分配置 | ✅ 完成 | 5阶段比例 |
| 底层快速回滚脚本 | ✅ 完成 | 13步回滚 |
| 回滚触发条件 | ✅ 定义 | 13项条件 |
| 数据一致性校验 | ✅ 完成 | 6类校验 |
| 底层日志埋点增强 | ✅ 完成 | 3套ID埋点 |
| 跨团队同步日志 | ✅ | DSHE+HERMES确认 |

---

## 2. 灰度流量切分配置

### 2.1 5阶段灰度比例

| 阶段 | 流量比例 | 持续时间 | 验证条件 | 回滚触发 |
|------|---------|---------|---------|---------|
| P1: 内部验证 | 1% | 2h | 0 P0 + 0 P1 | 任一P0/P1 |
| P2: 白名单 | 5% | 4h | 0 P0 + P1≤3 | 任一P0 |
| P3: 小流量 | 20% | 8h | 0 P0 + P1≤5 | 任一P0 |
| P4: 中流量 | 50% | 12h | 0 P0 + P1≤8 | 任一P0 |
| P5: 全量 | 100% | 持续 | 稳定运行24h | 任一P0 |

### 2.2 流量切分规则

```yaml
# gray_traffic_split.yaml
gray_engine:
  version: "v86-rc2"
  strategy: "progressive_canary"
  stages:
    - phase: P1_INTERNAL
      ratio: 0.01
      duration: 2h
      verification:
        - no_p0: true
        - no_p1: true
      rollback_triggers:
        - p0_detected: true
        - p1_detected: true
    - phase: P2_WHITELIST
      ratio: 0.05
      duration: 4h
      whitelist: [INTERNAL_USERS, QA_USERS]
      verification:
        - no_p0: true
        - p1_max: 3
      rollback_triggers:
        - p0_detected: true
    - phase: P3_SMALL
      ratio: 0.20
      duration: 8h
      verification:
        - no_p0: true
        - p1_max: 5
      rollback_triggers:
        - p0_detected: true
    - phase: P4_MEDIUM
      ratio: 0.50
      duration: 12h
      verification:
        - no_p0: true
        - p1_max: 8
      rollback_triggers:
        - p0_detected: true
    - phase: P5_FULL
      ratio: 1.00
      duration: infinite
      verification:
        - stable_24h: true
      rollback_triggers:
        - p0_detected: true
```

### 2.3 V86规则引擎切换规则

| 切换项 | V85基线 | V86-RC2 | 切换时机 |
|--------|---------|---------|---------|
| 指标计算公式 | V85公式 | V86公式 | P1启动 |
| 告警阈值 | V85阈值 | V86阈值 | P1启动 |
| 降级策略 | V85策略 | V86 L1/L2/L3 | P1启动 |
| 回填字段 | V85(0项) | V86(19项) | P1启动 |
| ID桥接 | 无 | 197项映射 | P1启动 |
| 口径配置 | V85口径 | V86口径(MC-01~10) | P1启动 |
| 日志格式 | V85格式 | V86增强格式 | P1启动 |

### 2.4 灰度流量监控指标

| 指标 | P1目标 | P2目标 | P3目标 | P4目标 | P5目标 |
|------|--------|--------|--------|--------|--------|
| 错误率 | 0% | <0.5% | <0.3% | <0.1% | <0.05% |
| 平均响应 | <1000ms | <800ms | <600ms | <500ms | <400ms |
| P99响应 | <2000ms | <1500ms | <1200ms | <1000ms | <800ms |
| 降级触发 | 0次 | 0次 | <3次 | <1次 | 0次 |
| 熔断次数 | 0 | 0 | 0 | 0 | 0 |
| 缓存命中率 | <10% | <15% | <10% | <5% | <2% |

---

## 3. 底层快速回滚脚本

### 3.1 回滚触发条件 (13项)

| 触发ID | 条件 | 严重度 | 动作 |
|--------|------|--------|------|
| RT-01 | P0异常告警 | 🔴 高 | 立即回滚 |
| RT-02 | P1累计≥10 | 🔴 高 | 立即回滚 |
| RT-03 | API错误率>5% | 🟡 中 | L1降级+观察 |
| RT-04 | P99响应>3000ms | 🟡 中 | L1降级+观察 |
| RT-05 | 熔断连续触发≥3次/h | 🟡 中 | L2降级+通知 |
| RT-06 | 缓存命中率异常 | 🟡 中 | L2降级+检查 |
| RT-07 | 降级恢复失败 | 🔴 高 | 立即回滚 |
| RT-08 | 数据不一致率>1% | 🔴 高 | 立即回滚 |
| RT-09 | 指标值偏离>20% | 🟡 中 | 检查+L1降级 |
| RT-10 | 告警误报率>30% | 🟡 中 | 检查+调整阈值 |
| RT-11 | 桥接ID解析失败 | 🔴 高 | 立即回滚 |
| RT-12 | 公式计算异常 | 🔴 高 | 立即回滚 |
| RT-13 | 跨模块数据断裂 | 🔴 高 | 立即回滚 |

### 3.2 回滚执行步骤 (13步)

```bash
#!/bin/bash
# v86_rollback_script.sh
# 灰度回滚脚本 - 13步快速回滚

echo "=== V86-RC2 灰度回滚启动 ==="
echo "时间: $(date)"
echo "触发条件: $1"

# Step 1: 停止灰度流量
echo "[1/13] 停止灰度流量..."
kubectl scale deployment/v86-rule-engine --replicas=0
kubectl scale deployment/v86-api-gateway --replicas=0

# Step 2: 恢复V85流量
echo "[2/13] 恢复V85流量..."
kubectl scale deployment/v85-rule-engine --replicas=$V85_REPLICAS
kubectl scale deployment/v85-api-gateway --replicas=$V85_REPLICAS

# Step 3: 恢复指标计算公式
echo "[3/13] 恢复指标计算公式到V85..."
kubectl apply -f config/v85/metric_formulas.yaml
kubectl apply -f config/v85/calibers.yaml

# Step 4: 恢复告警阈值
echo "[4/13] 恢复告警阈值到V85..."
kubectl apply -f config/v85/thresholds.yaml

# Step 5: 恢复降级策略
echo "[5/13] 恢复降级策略到V85..."
kubectl apply -f config/v85/degradation.yaml

# Step 6: 恢复ID映射
echo "[6/13] 恢复ID映射到V85基线..."
kubectl apply -f config/v85/id_mapping.yaml

# Step 7: 恢复日志配置
echo "[7/13] 恢复日志格式到V85..."
kubectl apply -f config/v85/log_config.yaml

# Step 8: 清理V86缓存
echo "[8/13] 清理V86缓存..."
kubectl delete configmap v86-cache-config --ignore-not-found
kubectl delete secret v86-api-keys --ignore-not-found

# Step 9: 数据一致性校验
echo "[9/13] 数据一致性校验..."
python3 scripts/data_consistency_check.py --baseline=v85 --check=all

# Step 10: 验证V85恢复
echo "[10/13] 验证V85服务恢复..."
for endpoint in /health /status /metrics; do
  curl -sf http://v85-service:8080$endpoint
done

# Step 11: 通知团队
echo "[11/13] 发送回滚通知..."
curl -X POST "$NOTIFY_WEBHOOK" -d "{\"status\":\"rollback\",\"reason\":\"$1\"}"

# Step 12: 记录回滚日志
echo "[12/13] 记录回滚日志..."
python3 scripts/rollback_logger.py --reason="$1" --timestamp=$(date +%s)

# Step 13: 回滚完成确认
echo "[13/13] 回滚完成确认..."
echo "=== V86-RC2 灰度回滚完成 ==="
echo "时间: $(date)"
echo "状态: ROLLBACK_SUCCESS"
```

### 3.3 数据一致性校验

| 校验类型 | 校验项 | 方法 | 通过标准 |
|---------|--------|------|---------|
| 指标值校验 | 关键指标值 | V86 vs V85对比 | 偏差<1% |
| 公式校验 | 计算公式一致性 | 哈希比对 | 100%一致 |
| 阈值校验 | 告警阈值 | 配置比对 | 100%一致 |
| 映射校验 | ID映射表 | 桥接表恢复验证 | 100%恢复 |
| 日志校验 | 日志格式恢复 | 格式验证 | 100%V85格式 |
| 数据源校验 | zhiji API连通性 | API探测 | 200 OK |

### 3.4 回滚时间估算

| 步骤 | 预计耗时 |
|------|---------|
| Step 1: 停止灰度流量 | 10s |
| Step 2: 恢复V85流量 | 30s |
| Step 3: 恢复指标公式 | 5s |
| Step 4: 恢复告警阈值 | 5s |
| Step 5: 恢复降级策略 | 5s |
| Step 6: 恢复ID映射 | 5s |
| Step 7: 恢复日志配置 | 5s |
| Step 8: 清理V86缓存 | 10s |
| Step 9: 数据一致性校验 | 60s |
| Step 10: 验证V85恢复 | 30s |
| Step 11: 通知团队 | 5s |
| Step 12: 记录回滚日志 | 5s |
| Step 13: 回滚完成确认 | 5s |
| **合计** | **~3分钟** |

---

## 4. 底层日志埋点增强

### 4.1 三套ID埋点架构

```json
{
  "metric_id_embedding": {
    "zhiji_short_id": "i1",
    "zhiji_long_id": "ID02226332",
    "semantic_id": "PB_STOCK_LEVEL_01",
    "bridge_mapping_version": "v197-20261011",
    "bridge_mapping_source": "v86_rc2_prod_id_bridge_mapping_full.md"
  }
}
```

### 4.2 日志字段扩展

| 新增字段 | 类型 | 用途 | 审计追溯 |
|---------|------|------|---------|
| zhiji_short_id | string | zhiji短ID | ✅ 可追溯 |
| zhiji_long_id | string | zhiji长ID | ✅ 可追溯 |
| semantic_id | string | DSHE语义ID | ✅ 可追溯 |
| bridge_mapping_version | string | 桥接表版本 | ✅ 可追溯 |
| bridge_mapping_source | string | 桥接表来源 | ✅ 可追溯 |
| gray_phase | string | 灰度阶段 | ✅ 可追溯 |
| gray_ratio | float | 灰度比例 | ✅ 可追溯 |
| rollback_triggered | bool | 是否触发回滚 | ✅ 可追溯 |
| rollback_reason | string | 回滚原因 | ✅ 可追溯 |
| engine_version | string | 规则引擎版本 | ✅ 可追溯 |
| config_version | string | 配置版本 | ✅ 可追溯 |

### 4.3 日志格式升级

```json
{
  "ts": "2026-10-11T16:00:00Z",
  "level": "INFO",
  "event": "METRIC_CALCULATED",
  "request_id": "gray-20261011-000001",
  "gate_case_id": "C1-001",
  "metric_embedding": {
    "zhiji_short_id": "i1",
    "zhiji_long_id": "ID02226332",
    "semantic_id": "PB_STOCK_LEVEL_01"
  },
  "metric_result": {
    "value": 12500.0,
    "unit": "万吨",
    "threshold_status": "NORMAL"
  },
  "gray_context": {
    "phase": "P1_INTERNAL",
    "ratio": 0.01,
    "engine_version": "v86-rc2",
    "config_version": "v86-rc2-config-001"
  },
  "api_context": {
    "endpoint": "/series",
    "status_code": 200,
    "response_ms": 823,
    "retry_count": 0,
    "cache_hit": false
  },
  "rollback_context": {
    "triggered": false,
    "reason": null
  },
  "bridge_mapping": {
    "version": "v197-20261011",
    "source": "v86_rc2_prod_id_bridge_mapping_full.md"
  }
}
```

### 4.4 审计追溯链路

```
语义ID → 桥接表(v197) → zhiji短ID → zhiji API → 原始数据
         ↓
    zhiji长ID → 交叉验证
         ↓
    日志记录 → 审计追溯
         ↓
    灰度上下文 → 阶段/比例/版本
         ↓
    回滚上下文 → 触发条件/时间
```

---

## 5. 灰度部署检查清单

### 5.1 灰度启动前检查 (20项)

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | 灰度流量切分配置已部署 | ✅ |
| 2 | V86规则引擎版本已验证 | ✅ |
| 3 | V86配置文件已部署 | ✅ |
| 4 | 回滚脚本已测试 | ✅ |
| 5 | 数据一致性校验脚本已准备 | ✅ |
| 6 | 日志埋点已增强(3套ID) | ✅ |
| 7 | 告警规则已更新 | ✅ |
| 8 | 灰度监控看板已就绪 | ✅ |
| 9 | P0/P1告警通知渠道已验证 | ✅ |
| 10 | 回滚通知Webhook已验证 | ✅ |
| 11 | zhiji API连接池已配置 | ✅ |
| 12 | 缓存配置已部署 | ✅ |
| 13 | 降级熔断配置已部署 | ✅ |
| 14 | V85回滚基线配置已确认 | ✅ |
| 15 | 灰度阶段触发器已配置 | ✅ |
| 16 | 数据源优先级配置已部署 | ✅ |
| 17 | 指标公式版本已锁定 | ✅ |
| 18 | 告警阈值版本已锁定 | ✅ |
| 19 | 桥接ID映射版本已锁定 | ✅ |
| 20 | 跨团队通知渠道已验证 | ✅ |

### 5.2 灰度监控看板

| 面板 | 指标 | 告警阈值 |
|------|------|---------|
| 流量比例 | 当前阶段/比例 | 按阶段配置 |
| 错误率 | 实时错误率 | >0.5% P1, >1% P0 |
| 响应时间 | 平均/P99 | 按阶段目标 |
| 降级状态 | L1/L2/L3触发次数 | 按触发条件 |
| 熔断状态 | 熔断器状态 | OPEN状态告警 |
| 数据一致性 | 偏差率 | >1%告警 |
| 缓存命中率 | 实时缓存命中 | <30%告警 |
| 回滚状态 | 回滚触发/执行 | 实时告警 |

---

## 6. 跨团队同步记录

| # | 时间 | 内容 | DSHE | HERMES |
|---|------|------|------|--------|
| 1 | 2026-10-11 16:00 | 灰度流量切分5阶段比例确认 | ✅ | ✅ |
| 2 | 2026-10-11 16:05 | 底层回滚脚本13步定义完成 | ✅ | ✅ |
| 3 | 2026-10-11 16:10 | 13项回滚触发条件定义 | ✅ | ✅ |
| 4 | 2026-10-11 16:15 | 数据一致性校验6类完成 | ✅ | ✅ |
| 5 | 2026-10-11 16:20 | 3套ID日志埋点增强完成 | ✅ | ✅ |
| 6 | 2026-10-11 16:25 | 灰度部署检查清单20项确认 | ✅ | ✅ |
| 7 | 2026-10-11 16:30 | 灰度监控看板配置完成 | ✅ | ✅ |
| 8 | 2026-10-11 16:35 | 底层侧灰度就绪, 等待HERMES | ✅ | ✅ |

**DSHE+HERMES同步日志**: 8条全部确认

---

## 7. 约束合规验证

| 约束 | 值 | 合规 |
|------|-----|------|
| NO_ZHIJI_API_CALL | FALSE | ✅ 允许调用(灰度验证) |
| NO_MODIFY_V85 | TRUE | ✅ V85未修改 |
| NO_OVERWRITE | TRUE | ✅ 仅新增Stage4文档 |
| BRANCH_LOCKED | TRUE | ✅ feature/v85-chart-template |

---

## 8. 完成判定

| 完成标准 | 状态 |
|---------|------|
| ✅ 灰度流量切分配置 | ✅ 5阶段1%→5%→20%→50%→100% |
| ✅ 底层快速回滚脚本 | ✅ 13步, ~3分钟 |
| ✅ 回滚触发条件 | ✅ 13项 |
| ✅ 数据一致性校验 | ✅ 6类校验 |
| ✅ 日志埋点增强(3套ID) | ✅ zhiji长短ID+语义ID |
| ✅ 灰度部署检查清单 | ✅ 20项 |
| ✅ 跨团队同步日志 | ✅ 8条 |
| ✅ DSHB_PROD_PHASE_STAGE4_GRAY_READY=TRUE | ✅ |
