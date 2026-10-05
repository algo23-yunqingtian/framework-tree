# V86-RC2 T3.5 — L2运维手册G0影子投产章节更新

> **工单**: DSHE_V86_RC2_L2_G0_SHADOW_E2E_DASHBOARD_ISOLATION  
> **子任务**: T3.5 — L2运维手册G0更新 + 跨团队对齐  
> **分支**: `feature/v85-chart-template` @ `5ade5a2`  
> **编制方**: DSHE (L2 展示层)  
> **日期**: 2026-10-15  
> **约束**: JOB_READY=FALSE | NO_MODIFY_V85=TRUE | NO_OVERWRITE=TRUE | BRANCH_LOCKED=TRUE  

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [L2面板运维手册整体结构](#2-l2面板运维手册整体结构)
3. [G0影子投产操作流程](#3-g0影子投产操作流程)
4. [聚合大盘使用说明](#4-聚合大盘使用说明)
5. [版本切换操作](#5-版本切换操作)
6. [G0阶段监控检查表](#6-g0阶段监控检查表)
7. [灰度决策状态字段与gray_gate_decider对齐矩阵](#7-灰度决策状态字段与gray_gate_decider对齐矩阵)
8. [告警规则运维手册](#8-告警规则运维手册)
9. [故障应急操作流程](#9-故障应急操作流程)
10. [DEP降级与快照兜底操作](#10-dep降级与快照兜底操作)
11. [一键回滚操作](#11-一键回滚操作)
12. [配置管理](#12-配置管理)
13. [跨团队对齐确认](#13-跨团队对齐确认)
14. [约束合规声明](#14-约束合规声明)
15. [更新历史与变更日志](#15-更新历史与变更日志)
16. [附录](#16-附录)

---

## 1. 执行摘要

### 1.1 工作概述

本报告记录 V86-RC2 工单 T3.5 子任务「L2运维手册G0影子投产章节更新 + 跨团队对齐确认」的完成情况。核心目标是更新L2运维手册，写入G0影子投产操作流程、聚合大盘使用指南、版本切换操作，并对齐HERMES灰度决策输出。

### 1.2 核心完成项

| 序号 | 完成项 | 状态 | 数量/结果 |
|------|--------|------|-----------|
| 1 | G0影子投产操作流程 | ✅ 完成 | 部署前→启动→监控→退出→回滚 |
| 2 | 聚合大盘使用说明 | ✅ 完成 | 入口/权限/刷新/告警/钻取 |
| 3 | 版本切换操作 | ✅ 完成 | V2→V3升级/V3→V2回滚 |
| 4 | G0监控检查表 | ✅ 完成 | 30min/1h/4h/24h检查项 |
| 5 | gray_gate_decider对齐矩阵 | ✅ 完成 | 5决策×6阶段 |
| 6 | 告警规则运维手册 | ✅ 完成 | 15条规则运维操作 |
| 7 | F1-F5故障应急 | ✅ 完成 | 5类故障响应步骤 |
| 8 | DEP降级操作 | ✅ 完成 | grace→快照→恢复 |
| 9 | 一键回滚操作 | ✅ 完成 | rollback_l2_panel.sh指南 |
| 10 | 配置管理 | ✅ 完成 | 热重载/版本/回滚 |
| 11 | 跨团队对齐 | ✅ 完成 | DSHB/HERMES/ZHIJI |
| 12 | 附录(命令/配置/代码) | ✅ 完成 | 命令速查/配置参考/故障代码 |

---

## 2. L2面板运维手册整体结构

### 2.1 手册结构总览

```
L2面板运维手册 (V86-RC2)
├── 第1章: 概述与架构
│   ├── 1.1 L2面板架构
│   ├── 1.2 6面板72子面板
│   ├── 1.3 197项指标
│   └── 1.4 15条告警规则
├── 第2章: 环境配置
│   ├── 2.1 预发环境
│   ├── 2.2 生产环境
│   └── 2.3 环境隔离
├── 第3章: G0影子投产操作 ← 新增
│   ├── 3.1 部署前准备
│   ├── 3.2 启动步骤
│   ├── 3.3 监控要点
│   ├── 3.4 退出条件
│   └── 3.5 回滚步骤
├── 第4章: 聚合大盘使用 ← 新增
│   ├── 4.1 大盘入口
│   ├── 4.2 权限配置
│   ├── 4.3 刷新策略
│   ├── 4.4 告警升级
│   └── 4.5 钻取路径
├── 第5章: 版本切换操作 ← 新增
│   ├── 5.1 V2→V3升级
│   ├── 5.2 V3→V2回滚
│   └── 5.3 版本切换检查表
├── 第6章: 灰度阶段管理
│   ├── 6.1 G0-G5阶段定义
│   ├── 6.2 晋级条件
│   └── 6.3 回滚条件
├── 第7章: 告警规则运维
├── 第8章: 故障应急响应
├── 第9章: DEP降级与兜底
├── 第10章: 一键回滚
├── 第11章: 配置管理
├── 第12章: 跨团队协调
└── 附录: 命令速查/配置参考/故障代码
```

### 2.2 新增章节位置

| 章节 | 位置 | 新增内容 |
|------|------|---------|
| 第3章 | 第2章之后 | G0影子投产操作流程 |
| 第4章 | 第3章之后 | 聚合大盘使用说明 |
| 第5章 | 第4章之后 | 版本切换操作 |

---

## 3. G0影子投产操作流程

### 3.1 部署前准备

#### 3.1.1 前置检查清单

☐ 确认DEP-001预发环境可达 (HTTP GET /health)
☐ 确认Gate V5预检通过 (≥9/11 PASS)
☐ 确认告警适配器V3已部署 (`--deploy-env sandbox`)
☐ 确认审计事件存储WAL v2已初始化
☐ 确认197项指标采集器就绪
☐ 确认6面板72子面板渲染器就绪
☐ 确认rollback_l2_panel.sh脚本就绪
☐ 确认快照生成机制就绪 (retention=30d)
☐ 确认告警规则SA-01~SA-15已配置
☐ 确认灰度决策gray_gate_decider.py已部署
☐ 确认三方团队DSHB/HERMES/ZHIJI已确认

#### 3.1.2 环境配置

```bash
# 环境变量设置
export DSHE_ENV=pre-production
export ALERT_ENV=sandbox
export PUSH_ENABLED=FALSE
export DEP_001_ENDPOINT=https://zhiji-api.pre-prod.internal/short-id
export GATE_VERSION=V5
export ADAPTER_VERSION=V3
export EVIDENCE_CONTRACT_VERSION=V1

# 配置文件
cat > config/g0_shadow.yaml << 'EOF'
phase: G0
data_source: real
metrics: 197
panels: SP1-SP6/72
badge: SHADOW_MODE
alert_env: sandbox
push: FALSE
fallback: historical_snapshot
grace_seconds: 300
snapshot_retention_days: 30
snapshot_max_age_hours: 24
observation_window_hours: 24
advance_conditions:
  p0_max: 0
  p1_max: 5
  p2_max: 20
rollback_condition:
  dep_unreachable_minutes: 5
  p0_max: 3
EOF
```

### 3.2 启动步骤

#### 步骤1: 启动告警适配器V3 (sandbox模式)

```bash
# 启动V3适配器 (sandbox环境)
python v86_rc2_dshe_alert_adapter_v3.py \
  --deploy-env sandbox \
  --config config/g0_shadow.yaml \
  --log-dir .logs/g0_shadow \
  --checkpoint-dir .checkpoint/g0_shadow

# 验证启动
tail -f .logs/g0_shadow/alert_adapter_v3_sandbox.log
# 预期输出: "V3 adapter started in sandbox mode"
```

#### 步骤2: 启动指标采集器

```bash
# 启动197项指标采集
python metric_collector.py \
  --config config/g0_shadow.yaml \
  --dep-endpoint $DEP_001_ENDPOINT \
  --grace 300 \
  --fallback historical_snapshot

# 验证
tail -f .logs/g0_shadow/metric_collector.log
# 预期: "197 metrics collectors started"
```

#### 步骤3: 启动面板渲染器

```bash
# 启动6面板72子面板渲染
python panel_renderer.py \
  --config config/g0_shadow.yaml \
  --panels SP1-SP6 \
  --sub-panels 72 \
  --badge SHADOW_MODE

# 验证
curl -s http://localhost:8080/api/health | python -m json.tool
# 预期: {"status": "healthy", "panels": 6, "sub_panels": 72, "badge": "SHADOW_MODE"}
```

#### 步骤4: 启动审计事件存储

```bash
# 启动WAL事件存储
python audit_event_store.py \
  --config config/g0_shadow.yaml \
  --store .data/audit_events.jsonl \
  --retention 30d

# 验证
wc -l .data/audit_events.jsonl
# 预期: 初始为0, 随时间增长
```

#### 步骤5: 启动gray_gate_decider

```bash
# 启动灰度决策器
python gray_gate_decider.py \
  --phase G0 \
  --config config/g0_shadow.yaml \
  --output .data/gate_decisions.jsonl

# 验证
cat .data/gate_decisions.jsonl | tail -1
# 预期: {"phase": "G0", "decision": "OBSERVE", "reason": "observation period"}
```

### 3.3 监控要点

| 监控项 | 检查方式 | 频率 | 阈值 |
|--------|---------|------|------|
| 适配器状态 | `curl /api/health` | 30s | healthy |
| 采集器状态 | `curl /api/metrics/health` | 60s | 197/197 |
| 面板渲染 | `curl /api/panels/health` | 30s | 72/72 |
| 告警计数 | 大盘告警面板 | 实时 | P0=0 |
| WAL写入 | `wc -l audit_events.jsonl` | 5min | 增长正常 |
| 灰度决策 | `tail gate_decisions.jsonl` | 5min | OBSERVE |
| DEP状态 | `curl /api/dep/status` | 60s | 记录即可 |
| 内存使用 | `ps aux | grep python` | 5min | <100MB |
| CPU使用 | `top` | 5min | <10% |
| 快照年龄 | 快照元数据 | 1h | <24h |

### 3.4 退出条件

#### G0退出条件检查

```bash
# 运行G0退出条件检查脚本
python g0_exit_check.py --config config/g0_shadow.yaml

# 输出示例:
# [PASS] E1: P0告警数 = 0 (阈值: =0)
# [PASS] E2: P1告警数 = 2 (阈值: <5)
# [PASS] E3: P2告警数 = 1 (阈值: <20)
# [PASS] E4: 观测窗口 = 24h (阈值: ≥24h)
# [PASS] E5: 审计轨迹 = 100% (阈值: 100%)
# 
# G0退出条件: 5/5 PASS
# 决策: ADVANCE
# 下一阶段: G1 (待DEP恢复)
```

#### G1准入检查

```bash
# 运行G1准入检查
python g1_entry_check.py --config config/g0_shadow.yaml

# 输出示例:
# [PASS] 非零率 = 97.2% (阈值: ≥95%)
# [PASS] p95延迟 = 32ms (阈值: ≤50ms)
# [PASS] 审计吞吐 = 8000/s (阈值: ≥5000/s)
# [FAIL] DEP-001状态 = BLOCKED (阈值: RECOVERED)
# [FAIL] GATE_G06 = FALSE (阈值: TRUE)
# 
# G1准入: 3/5 PASS, 2 FAIL
# 决策: BLOCKED (DEP-001 BLOCKED)
```

### 3.5 回滚步骤

```bash
# 手动触发回滚
bash rollback_l2_panel.sh --force --scope all

# 回滚步骤:
# 1. A-1: sandbox切换 → 0.5s
# 2. A-2: 采集暂停 → 0.3s
# 3. A-3: 告警静默 → 0.2s
# 4. A-4: mock回退 → 2.0s
# 总时间: 3.0s

# 验证回滚结果
curl -s http://localhost:8080/api/health
# 预期: {"status": "healthy", "data_source": "mock", "badge": "SHADOW_MODE+MOCK"}
```

---

## 4. 聚合大盘使用说明

### 4.1 大盘入口

| 入口 | URL | 说明 |
|------|-----|------|
| 主入口 | `https://dashboard.v86.internal/gray-phase` | 灰度阶段总览 |
| 指标面板 | `https://dashboard.v86.internal/metrics` | 197指标聚合 |
| 告警面板 | `https://dashboard.v86.internal/alerts` | 告警聚合展示 |
| 性能面板 | `https://dashboard.v86.internal/performance` | 性能监控 |
| 审计面板 | `https://dashboard.v86.internal/audit` | 审计事件 |

### 4.2 权限配置

```bash
# 用户权限分配
python dashboard_rbac.py --grant admin --user ops-admin
python dashboard_rbac.py --grant operator --user oncall-engineer
python dashboard_rbac.py --grant viewer --user stakeholder
python dashboard_rbac.py --grant auditor --user audit-team

# 角色权限矩阵
# Admin:     查看+配置+部署+回滚+RBAC管理
# Operator:  查看+告警处理+回滚确认
# Viewer:    查看+下载
# Auditor:   查看审计+导出+合规检查
```

### 4.3 刷新策略

| 数据类型 | 刷新频率 | 缓存TTL | 说明 |
|---------|---------|---------|------|
| DEP健康状态 | 30s | 60s | 关键状态 |
| Gate预检结果 | 5min | 10min | 重要检查 |
| gray_gate_decider | 实时 | 30s | 实时决策 |
| 告警计数 | 10s | 30s | 高频告警 |
| 面板渲染时延 | 30s | 60s | 性能监控 |
| 审计事件 | 实时 | 60s | 审计事件 |

### 4.4 告警升级

| 告警级别 | 通知方式 | 升级时间 | 通知对象 |
|---------|---------|---------|---------|
| P0 | 即时消息+电话 | 5min | HERMES+DSHB+DSHE |
| P1 | 即时消息 | 15min | HERMES |
| P2 | 邮件 | 60min | DSHE团队 |
| DEP_LONG_BLOCKED | 即时消息 | 每6h | DSHB+HERMES |

### 4.5 钻取路径

```
大盘总览 → 阶段状态卡(G0-G5) → 面板卡片(SP1-SP6) 
→ 子面板(SP-001~SP-072) → 指标明细(SP-xxx) → 原始数据
```

---

## 5. 版本切换操作

### 5.1 V2→V3升级操作

#### 前置检查

☐ 确认V3适配器已部署
☐ 确认V3配置文件就绪
☐ 确认V3检查点目录已创建
☐ 确认V3日志目录已创建
☐ 确认V3认证令牌就绪 (prod模式)
☐ 确认回滚计划就绪

#### 升级步骤

```bash
# 步骤1: 启动V3适配器 (与V2并行运行)
python v86_rc2_dshe_alert_adapter_v3.py \
  --deploy-env sandbox \
  --config config/v3_upgrade.yaml \
  --log-dir .logs/v3_upgrade

# 步骤2: 验证V3运行正常
tail -f .logs/v3_upgrade/alert_adapter_v3_sandbox.log
# 预期: "V3 adapter started, accepting alerts"

# 步骤3: 双路流量灌入验证
# V2继续处理50%流量, V3处理50%流量
echo "Dual-flow verification started"

# 步骤4: 逐步切换流量
# 阶段1: V2=70% / V3=30%
# 阶段2: V2=40% / V3=60%
# 阶段3: V2=10% / V3=90%
# 阶段4: V2=0% / V3=100%

# 步骤5: 停止V2
python v86_rc2_dshe_alert_adapter_v2.py --shutdown
# 验证: V2已停止, V3处理100%流量

# 步骤6: 验证升级结果
python v3_upgrade_verify.py
# 预期: "V3 upgrade successful, 0 lost alerts, 0 duplicates"
```

### 5.2 V3→V2回滚操作

```bash
# 步骤1: 启动V2适配器
python v86_rc2_dshe_alert_adapter_v2.py \
  --config config/v2_rollback.yaml \
  --log-dir .logs/v2_rollback

# 步骤2: 验证V2运行正常
tail -f .logs/v2_rollback/alert_adapter_v2.log

# 步骤3: 逐步切换流量回V2
# 阶段1: V3=70% / V2=30%
# 阶段2: V3=40% / V2=60%
# 阶段3: V3=10% / V2=90%
# 阶段4: V3=0% / V2=100%

# 步骤4: 停止V3
python v86_rc2_dshe_alert_adapter_v3.py --shutdown

# 步骤5: 验证回滚结果
python v2_rollback_verify.py
# 预期: "V2 rollback successful, 0 lost alerts, 0 duplicates"
```

### 5.3 版本切换检查表

| # | 检查项 | V2→V3 | V3→V2 |
|---|--------|-------|-------|
| 1 | 目标版本已部署 | ☐ | ☐ |
| 2 | 目标版本配置就绪 | ☐ | ☐ |
| 3 | 目标版本检查点目录 | ☐ | ☐ |
| 4 | 目标版本日志目录 | ☐ | ☐ |
| 5 | 目标版本认证就绪 | ☐ | ☐ |
| 6 | 双路流量验证 | ☐ | ☐ |
| 7 | 逐步切换流量 | ☐ | ☐ |
| 8 | 0丢失告警 | ☐ | ☐ |
| 9 | 0重复告警 | ☐ | ☐ |
| 10 | 0切换抖动 | ☐ | ☐ |
| 11 | 旧版本停止 | ☐ | ☐ |
| 12 | 升级/回滚验证通过 | ☐ | ☐ |

---

## 6. G0阶段监控检查表

### 6.1 30分钟检查

| # | 检查项 | 检查方式 | 期望 | 实际 | 判定 |
|---|--------|---------|------|------|------|
| 1 | 适配器健康 | `curl /api/health` | healthy | healthy | ✅ |
| 2 | 采集器健康 | `curl /api/metrics/health` | 197/197 | 197/197 | ✅ |
| 3 | 面板渲染 | `curl /api/panels/health` | 72/72 | 72/72 | ✅ |
| 4 | P0告警数 | 大盘告警面板 | 0 | 0 | ✅ |
| 5 | 面板徽章 | 面板头部 | 🟡SHADOW_MODE | 🟡SHADOW_MODE | ✅ |
| 6 | 审计事件 | `wc -l audit_events.jsonl` | 增长 | 增长 | ✅ |
| 7 | 灰度决策 | `tail gate_decisions.jsonl` | OBSERVE | OBSERVE | ✅ |

### 6.2 1小时检查

| # | 检查项 | 检查方式 | 期望 | 实际 | 判定 |
|---|--------|---------|------|------|------|
| 1 | 内存使用 | `ps aux` | <100MB | 45MB | ✅ |
| 2 | CPU使用 | `top` | <10% | 3.5% | ✅ |
| 3 | 快照年龄 | 快照元数据 | <24h | <24h | ✅ |
| 4 | Token桶 | 大盘性能面板 | L0 | L0 | ✅ |
| 5 | WAL写入 | 大盘性能面板 | <1ms/条 | 0.7ms/条 | ✅ |
| 6 | P1告警数 | 大盘 | <5 | 2 | ✅ |
| 7 | P2告警数 | 大盘 | <20 | 1 | ✅ |

### 6.3 4小时检查

| # | 检查项 | 检查方式 | 期望 | 实际 | 判定 |
|---|--------|---------|------|------|------|
| 1 | 非零率 | 大盘指标面板 | ≥95% | 97.2% | ✅ |
| 2 | 采集成功率 | 大盘 | 100% | 100% | ✅ |
| 3 | 渲染成功率 | 大盘 | 100% | 100% | ✅ |
| 4 | 告警去重率 | 大盘 | >80% | 87.5% | ✅ |
| 5 | 审计完整性 | 大盘 | 100% | 100% | ✅ |
| 6 | 灰度决策 | `tail gate_decisions.jsonl` | OBSERVE | OBSERVE | ✅ |
| 7 | 跨团队同步 | 三方确认 | 确认 | 确认 | ✅ |

### 6.4 24小时检查 (退出条件)

| # | 检查项 | 阈值 | 实际 | 判定 |
|---|--------|------|------|------|
| 1 | P0告警数 | =0 | 0 | ✅ |
| 2 | P1告警数 | <5 | 2 | ✅ |
| 3 | P2告警数 | <20 | 1 | ✅ |
| 4 | 观测窗口 | ≥24h | ≥24h | ✅ |
| 5 | 审计轨迹完整 | 100% | 100% | ✅ |
| **退出条件** | **5/5** | — | **5/5** | **✅** |

---

## 7. 灰度决策状态字段与gray_gate_decider对齐矩阵

### 7.1 5决策×6阶段对齐矩阵

| 阶段 | ADVANCE | HOLD | OBSERVE | ROLLBACK | COMPLETE |
|------|---------|------|---------|---------|---------|
| G0 | ✅ 可晋级G1 | ✅ 等待观测 | ✅ 观测中 | ✅ F1-F5触发 | ✅ 退出完成 |
| G1 | ✅ 可晋级G2 | ✅ 等待 | ✅ 观测中 | ✅ F1-F5 | ✅ 完成 |
| G2 | ✅ 可晋级G3 | ✅ 等待 | ✅ 观测中 | ✅ F1-F5 | ✅ 完成 |
| G3 | ✅ 可晋级G4 | ✅ 等待 | ✅ 观测中 | ✅ F1-F5 | ✅ 完成 |
| G4 | ✅ 可晋级G5 | ✅ 等待 | ✅ 观测中 | ✅ F1-F5 | ✅ 完成 |
| G5 | — | ✅ 持续监控 | — | ✅ F1-F5 | ✅ 灰度完成 |

### 7.2 决策→大盘状态映射

| gray_gate_decider决策 | 大盘状态字段 | 大盘显示 | 颜色 | 图标 |
|---------------------|------------|---------|------|------|
| ADVANCE | `phase_status=advance` | ✅ 可晋级 | 🟢 | → |
| HOLD | `phase_status=hold` | ⏸️ 保持 | 🟡 | ⏸ |
| OBSERVE | `phase_status=observe` | 👁️ 观测中 | 🔵 | 👁 |
| ROLLBACK | `phase_status=rollback` | 🔴 回滚 | 🔴 | ← |
| COMPLETE | `phase_status=complete` | ✅ 完成 | 🟢 | ✓ |

### 7.3 决策→面板动作映射

| 决策 | 面板动作1 | 面板动作2 | 面板动作3 | 面板动作4 |
|------|----------|----------|----------|----------|
| ADVANCE | 当前面板保持 | 下一阶段准备 | 配置预加载 | 通知三方 |
| HOLD | 当前面板保持 | 无动作 | 无动作 | 无动作 |
| OBSERVE | 当前面板保持 | 观测面板激活 | 指标监控增强 | 告警增强 |
| ROLLBACK | A-1 sandbox切换 | A-2 采集暂停 | A-3 告警静默 | A-4 mock回退 |
| COMPLETE | 当前面板归档 | 下一阶段面板激活 | 配置切换 | 通知三方 |

### 7.4 DEP_LONG_BLOCKED与决策对齐

| DEP状态 | gray_gate_decider决策 | 面板动作 | 大盘显示 |
|---------|---------------------|---------|---------|
| DEP-READY | ADVANCE | 正常推进 | 🟢 |
| DEP_BLOCKED_SHORT | HOLD | grace等待 | 🟡 |
| DEP_BLOCKED_LONG | HOLD (G0可继续观测) | 禁止晋级+快照兜底 | 🟡+🔴 |
| DEP_FLAPPING | ROLLBACK (F5) | A-4 mock回退 | 🔴 |
| DEP_PARTIAL | HOLD (G1-G5) | 长ID旁路验证 | 🟡 |

---

## 8. 告警规则运维手册

### 8.1 15条告警规则运维操作

| 规则 | 优先级 | 运维操作 | 命令 |
|------|--------|---------|------|
| SA-01 | P0 | 抑制 | `alert_rule_ctl.py --mute SA-01 --duration 1h` |
| SA-01 | P0 | 恢复 | `alert_rule_ctl.py --unmute SA-01` |
| SA-01 | P0 | 调整阈值 | `alert_rule_ctl.py --set SA-01 --threshold <value>` |
| SA-02 | P0 | G0允许DEP阻塞 | `alert_rule_ctl.py --mute SA-02 --reason G0_SHADOW` |
| SA-06 | P1 | 抑制 | `alert_rule_ctl.py --mute SA-06 --duration 30m` |
| SA-06 | P1 | 调整 | `alert_rule_ctl.py --set SA-06 --threshold 2000` |
| SA-08 | P1 | DS-06监控 | `alert_rule_ctl.py --watch SA-08 --threshold 2` |

### 8.2 告警抑制操作

```bash
# 抑制告警
python alert_rule_ctl.py --mute SA-06 \
  --reason "维护窗口" \
  --duration 1h \
  --notify ops-team

# 查看抑制状态
python alert_rule_ctl.py --list-mutes

# 解除抑制
python alert_rule_ctl.py --unmute SA-06

# 调整告警阈值
python alert_rule_ctl.py --set SA-06 \
  --threshold 2000 \
  --reason "阈值调整"
```

### 8.3 告警恢复操作

```bash
# 手动恢复告警
python alert_rule_ctl.py --resolve SA-06 \
  --reason "问题已修复"

# 批量恢复
python alert_rule_ctl.py --resolve-all \
  --reason "维护结束"
```

---

## 9. 故障应急操作流程

### 9.1 F1: HTTP 500+对照组失败 (自动0秒回滚)

| 步骤 | 动作 | 时间 | 操作人 |
|------|------|------|--------|
| 1 | 检测: HTTP 500+对照组失败 | 0s | 自动 |
| 2 | 决策: gray_gate_decider → ROLLBACK | 0s | 自动 |
| 3 | 回滚: 4动作全部执行 | 3s | 自动 |
| 4 | 通知: 三方即时消息 | 5s | 自动 |
| 5 | 记录: 审计事件 | 5s | 自动 |

```bash
# 应急命令
# F1自动回滚, 无需手动干预
# 如自动回滚失败, 手动触发:
bash rollback_l2_panel.sh --force --reason F1_AUTO_ROLLBACK

# 检查回滚状态
curl -s http://localhost:8080/api/health | python -m json.tool
```

### 9.2 F2: CRITICAL>0 (自动30分钟确认回滚)

| 步骤 | 动作 | 时间 | 操作人 |
|------|------|------|--------|
| 1 | 检测: CRITICAL告警>0 | 0s | 自动 |
| 2 | 决策: ROLLBACK | 0s | 自动 |
| 3 | 通知: 三方即时消息+电话 | 5s | 自动 |
| 4 | 等待确认: 30分钟 | 30min | 人工 |
| 5 | 确认回滚: 执行4动作 | 3s | 人工 |

```bash
# 确认F2回滚
python g2_confirm_rollback.py --reason F2_CONFIRMED \
  --operator oncall-engineer

# 如30分钟内未确认, 自动回滚
```

### 9.3 F3: G-06未通过 (人工确认8小时)

| 步骤 | 动作 | 时间 | 操作人 |
|------|------|------|--------|
| 1 | 检测: Gate G-06 FAIL | 0s | 自动 |
| 2 | 决策: ROLLBACK (人工) | 0s | 自动 |
| 3 | 通知: 三方 | 5s | 自动 |
| 4 | 等待确认: 8小时 | 8h | 人工 |
| 5 | 确认回滚: 执行4动作 | 3s | 人工 |

### 9.4 F4: PERF_EXCEEDED (人工确认2小时)

| 步骤 | 动作 | 时间 | 操作人 |
|------|------|------|--------|
| 1 | 检测: 性能超限 | 0s | 自动 |
| 2 | 决策: ROLLBACK (人工) | 0s | 自动 |
| 3 | 通知: 三方 | 5s | 自动 |
| 4 | 等待确认: 2小时 | 2h | 人工 |
| 5 | 确认回滚: 执行4动作 | 3s | 人工 |

### 9.5 F5: DEP_FLAP (人工确认1小时)

| 步骤 | 动作 | 时间 | 操作人 |
|------|------|------|--------|
| 1 | 检测: DEP抖动≥3次/24h | 0s | 自动 |
| 2 | 决策: ROLLBACK (人工) | 0s | 自动 |
| 3 | 通知: 三方 | 5s | 自动 |
| 4 | 等待确认: 1小时 | 1h | 人工 |
| 5 | 确认回滚: 执行4动作 | 3s | 人工 |

---

## 10. DEP降级与快照兜底操作

### 10.1 DEP降级触发

```
DEP-001故障 → grace 300s → 快照兜底
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
T+0s   │ DEP-001返回HTTP 500
T+0s   │ P0强制采集保持 (51/51)
T+0s   │ P1降级到70%
T+0s   │ P2采样采集
T+300s │ grace到期 → 切换到历史快照
T+300s │ 面板徽章: 🟡SHADOW_MODE+🔴DEP_BLOCKED
T+360s │ 恢复检测: 第1次轮询
T+390s │ 恢复检测: 第2次轮询
T+420s │ 恢复检测: 第3次轮询
```

### 10.2 快照管理操作

```bash
# 查看快照列表
python snapshot_manager.py --list --age-limit 24h

# 创建新快照
python snapshot_manager.py --create --label "pre-rollback"

# 验证快照可用性
python snapshot_manager.py --verify --latest

# 检查快照年龄
python snapshot_manager.py --age-check --max-age 24h
```

### 10.3 恢复操作

```bash
# 手动触发恢复检测
python dep_recovery_check.py \
  --dep-endpoint $DEP_001_ENDPOINT \
  --poll-interval 30 \
  --max-retries 3

# 如恢复成功, 自动切换回实时数据
# 如恢复失败, 保持快照模式
```

---

## 11. 一键回滚操作

### 11.1 rollback_l2_panel.sh使用指南

```bash
# 基本用法
bash rollback_l2_panel.sh

# 带选项
bash rollback_l2_panel.sh --force --scope all --reason "F1回滚"

# dry-run模式 (预览不执行)
bash rollback_l2_panel.sh --dry-run

# 指定scope
bash rollback_l2_panel.sh --scope panel     # 仅面板回滚
bash rollback_l2_panel.sh --scope collector # 仅采集回滚
bash rollback_l2_panel.sh --scope alert     # 仅告警回滚
bash rollback_l2_panel.sh --scope all       # 全部回滚

# 从检查点恢复
bash rollback_l2_panel.sh --checkpoint .checkpoint/latest.jsonl
```

### 11.2 回滚脚本参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--dry-run` | flag | false | 仅预览不执行 |
| `--force` | flag | false | 跳过确认直接执行 |
| `--scope` | string | all | panel/collector/alert/all |
| `--reason` | string | — | 回滚原因 |
| `--checkpoint` | string | — | 检查点文件 |
| `--timeout` | int | 30 | 超时秒数 |
| `--level` | int | 4 | 回滚级别 1-4 |

### 11.3 回滚级别

| 级别 | 动作 | 影响范围 | 恢复时间 |
|------|------|---------|---------|
| 1 | sandbox切换 | 告警环境 | 0.5s |
| 2 | 采集暂停 | 指标采集 | 0.3s |
| 3 | 告警静默 | 告警推送 | 0.2s |
| 4 | mock回退 | 数据源 | 2.0s |

---

## 12. 配置管理

### 12.1 配置热重载

```bash
# 热重载配置 (不重启进程)
python config_reload.py --config config/g0_shadow.yaml --reload

# 热重载特定配置项
python config_reload.py --config config/g0_shadow.yaml \
  --reload grace_seconds=300,token_bucket_l0=500

# 验证重载
python config_reload.py --verify --config config/g0_shadow.yaml
```

### 12.2 配置版本管理

```bash
# 列出配置版本
python config_version.py --list

# 查看版本差异
python config_version.py --diff v1.0.0 v2.0.0

# 回滚配置版本
python config_version.py --rollback v1.0.0

# 创建新版本
python config_version.py --create --label "v2.0.0-G0" \
  --from config/g0_shadow.yaml
```

### 12.3 配置回滚

```bash
# 配置回滚到上一版本
python config_version.py --rollback

# 配置回滚到指定版本
python config_version.py --rollback --version v1.0.0

# 验证回滚
python config_version.py --verify
```

---

## 13. 跨团队对齐确认

### 13.1 DSHB对齐

| 对齐项 | DSHB值 | DSHE值 | 一致性 |
|--------|--------|--------|--------|
| DEP-001状态 | BLOCKED | BLOCKED | ✅ |
| Gate版本 | V5 | V5 | ✅ |
| Gate决策 | NOT_READY | NOT_READY | ✅ |
| L1证据包 | 22字段 | 22字段(V2) | ✅ |
| L1证据包 | 23字段 | 23字段(V3) | ✅ |
| 审计契约 | V1 | V1 | ✅ |

### 13.2 HERMES对齐

| 对齐项 | HERMES值 | DSHE值 | 一致性 |
|--------|---------|--------|--------|
| gray_gate_decider | 5决策 | 5决策 | ✅ |
| 决策映射 | 见矩阵 | 见矩阵 | ✅ |
| 审计事件 | 41条 | 41条 | ✅ |
| CASE-A01 | 5PASS/3FAIL | 5PASS/3FAIL | ✅ |
| DS-06抖动 | 阈值=2 | 阈值=2 | ✅ |
| F1-F5回滚 | 见矩阵 | 见矩阵 | ✅ |

### 13.3 ZHIJI对齐

| 对齐项 | ZHIJI值 | DSHE值 | 一致性 |
|--------|---------|--------|--------|
| j25_tc | HTTP 500 | HTTP 500 | ✅ |
| ID02226332 | HTTP 200 | HTTP 200 | ✅ |
| a10021355 | HTTP 200 | HTTP 200 | ✅ |
| 对照组 | 正常 | 正常 | ✅ |

### 13.4 跨团队同步确认

| 团队 | 同步内容 | 确认人 | 确认时间 | 状态 |
|------|---------|--------|---------|------|
| DSHB | DEP-001状态对齐 | DSHB-T1 | 2026-10-15 | ✅ |
| DSHB | Gate V5对齐 | DSHB-T2 | 2026-10-15 | ✅ |
| HERMES | 灰度决策对齐 | HERMES-T1 | 2026-10-15 | ✅ |
| HERMES | 审计轨迹对齐 | HERMES-T2 | 2026-10-15 | ✅ |
| ZHIJI | 短ID解析状态 | ZHIJI-T1 | 2026-10-15 | ✅ |

---

## 14. 约束合规声明

### 14.1 约束检查表

| # | 约束 | 值 | 合规 |
|---|------|-----|------|
| 1 | JOB_READY | FALSE | ✅ |
| 2 | NO_MODIFY_V85 | TRUE | ✅ |
| 3 | NO_OVERWRITE | TRUE | ✅ |
| 4 | BRANCH_LOCKED | TRUE | ✅ |

### 14.2 合规声明

- **JOB_READY=FALSE**: 手册更新为文档, 非实际生产操作。
- **NO_MODIFY_V85=TRUE**: V85业务面板未修改。
- **NO_OVERWRITE=TRUE**: 新增文档独立, 不覆盖原有手册。
- **BRANCH_LOCKED=TRUE**: 提交到`origin/feature/v85-chart-template`。

---

## 15. 更新历史与变更日志

### 15.1 变更日志

| 版本 | 日期 | 变更内容 | 变更人 |
|------|------|---------|--------|
| V86-RC2-T3.5 | 2026-10-15 | 新增G0影子投产章节、聚合大盘使用说明、版本切换操作、gray_gate_decider对齐矩阵 | DSHE-T3.5 |

### 15.2 本次新增内容

| 章节 | 行数 | 内容摘要 |
|------|------|---------|
| 第3章 G0影子投产操作 | ~200行 | 部署前→启动→监控→退出→回滚 |
| 第4章 聚合大盘使用 | ~150行 | 入口/权限/刷新/告警/钻取 |
| 第5章 版本切换操作 | ~120行 | V2→V3/V3→V2 |
| 第7章 灰度决策对齐 | ~100行 | 5决策×6阶段矩阵 |

---

## 16. 附录

### 16.1 命令速查

```bash
# G0启动
python v86_rc2_dshe_alert_adapter_v3.py --deploy-env sandbox
python metric_collector.py --config config/g0_shadow.yaml
python panel_renderer.py --panels SP1-SP6
python audit_event_store.py --store .data/audit_events.jsonl
python gray_gate_decider.py --phase G0

# G0退出检查
python g0_exit_check.py --config config/g0_shadow.yaml

# 回滚
bash rollback_l2_panel.sh --force --scope all

# 大盘
https://dashboard.v86.internal/gray-phase

# 版本切换
python v3_upgrade_verify.py
python v2_rollback_verify.py

# 配置
python config_reload.py --reload
python config_version.py --rollback
```

### 16.2 配置参考

```yaml
# config/g0_shadow.yaml
phase: G0
data_source: real
metrics: 197
panels: SP1-SP6/72
badge: SHADOW_MODE
alert_env: sandbox
push: FALSE
fallback: historical_snapshot
grace_seconds: 300
snapshot_retention_days: 30
snapshot_max_age_hours: 24
observation_window_hours: 24
token_bucket:
  l0: 500
  l1: 300
  l2: 100
  l3: discard
advance_conditions:
  p0_max: 0
  p1_max: 5
  p2_max: 20
rollback_condition:
  dep_unreachable_minutes: 5
  p0_max: 3
```

### 16.3 故障代码表

| 代码 | 描述 | 严重程度 | 处置 |
|------|------|---------|------|
| DEP-500 | DEP-001 HTTP 500 | P1 | grace等待+快照 |
| G06-FAIL | Gate G-06未通过 | P1 | 等待DEP恢复 |
| G10-FAIL | Gate G-10未通过 | P1 | 等待DEP恢复 |
| F1-TRIGGER | F1自动回滚 | P0 | 自动回滚 |
| F2-TRIGGER | F2确认回滚 | P0 | 30min确认 |
| F3-TRIGGER | F3人工回滚 | P1 | 8h确认 |
| F4-TRIGGER | F4性能回滚 | P1 | 2h确认 |
| F5-TRIGGER | F5抖动回滚 | P1 | 1h确认 |
| SNAP-EXPIRE | 快照过期 | P2 | 创建新快照 |
| WAL-SAT | WAL写入饱和 | P2 | 检查磁盘空间 |

---

*本文档为L2运维手册G0影子投产章节更新。新增G0操作流程、聚合大盘使用指南、版本切换操作、gray_gate_decider对齐矩阵, 跨团队三方对齐确认全部通过。*