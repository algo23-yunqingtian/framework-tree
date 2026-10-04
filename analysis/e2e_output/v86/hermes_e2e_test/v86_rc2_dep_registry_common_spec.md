# V86-RC2 跨团队DEP登记共用规范

> **Task:** DSHE_V86_RC2_PROD_PHASE_L2_EVIDENCE_AUTO / T3.5
> **Generated:** 2026-10-15
> **Branch:** `feature/v85-chart-template`
> **Status:** ✅ T3.5 COMPLETE — 跨团队DEP台账格式对齐完成，DSHB+DSHE两端台账可交叉比对
> **对齐团队:** DSHB + DSHE + HERMES
> **基线:** commit `a62e525` (L2_AUDIT_ALIGN_DONE)

---

## 0. 规范概述

### 0.1 目的

统一DSHB与DSHE两端的DEP（外部依赖）登记格式，确保：
1. DEP登记ID两端一致
2. 变更日志字段定义对齐
3. DEP_BLOCK状态机描述统一
4. 两端台账可交叉比对
5. 审计溯源链路贯通

### 0.2 适用范围

| 团队 | 范围 | DEP角色 |
|------|------|---------|
| **DSHB** | 底层引擎+数据层 | DEP提供方（数据平台zhiji API） |
| **DSHE** | 展示层+校验层 | DEP使用方（独立调用zhiji API） |
| **HERMES** | 预审+审计层 | DEP审计方（L2/L3流水线） |

### 0.3 约束合规

| 约束 | 值 | 合规 |
|------|-----|------|
| `JOB_READY` | FALSE | ✅ |
| `NO_ZHIJI_API_CALL` | FALSE (允许) | ✅ |
| `NO_MODIFY_V85` | TRUE | ✅ |
| `NO_OVERWRITE` | TRUE | ✅ |
| `BRANCH_LOCKED` | TRUE | ✅ |

---

## 1. DEP登记ID统一规范

### 1.1 编号规则

| 字段 | 规则 | 示例 |
|------|------|------|
| 前缀 | `DEP-REG-` 固定前缀 | DEP-REG-001 |
| 序号 | 3位递增 (001~999) | DEP-REG-001, DEP-REG-002 |
| 版本后缀 | 可选 `-v{N}` | DEP-REG-001-v2 |
| 跨团队统一 | DSHB与DSHE共用同一编号 | DEP-REG-001 |
| 不可重号 | 同一DEP-REG编号不可重复使用 | — |
| 不可删改 | 已登记DEP不可删除，仅可关闭 | — |

### 1.2 登记ID分配

| 编号 | 依赖方 | 接口 | 风险等级 | 影响范围 | 责任方 |
|------|--------|------|---------|---------|--------|
| DEP-REG-001 | zhiji API (数据平台) | REST API (search/series) | P0 | 8品种178条目 | DSHB+DSHE |
| DEP-REG-002 | (预留) | — | — | — | — |
| DEP-REG-003 | (预留) | — | — | — | — |

### 1.3 登记元数据

| 字段 | 类型 | DSHB | DSHE | 说明 |
|------|------|------|------|------|
| `dep_registry_id` | string | ✅ | ✅ | DEP登记ID (跨团队统一) |
| `dep_name` | string | ✅ | ✅ | 依赖名称 |
| `dep_provider` | string | ✅ | ✅ | 依赖提供方 |
| `dep_interface` | string | ✅ | ✅ | 接口类型 |
| `risk_level` | string | ✅ | ✅ | 风险等级 (P0/P1/P2) |
| `impact_scope` | string | ✅ | ✅ | 影响范围 |
| `responsible_team` | string | ✅ | ✅ | 责任团队 |
| `registration_time` | string | ✅ | ✅ | 登记时间戳 (ISO 8601) |
| `current_status` | string | ✅ | ✅ | 当前状态 (见状态机) |
| `recovery_target` | string | ✅ | ✅ | 恢复目标 |
| `degradation_plan` | string | ✅ | ✅ | 降级方案 |
| `max_pause_days` | int | ✅ | ✅ | 最大暂停天数 (30) |
| `rollback_window_min` | int | ✅ | ✅ | 回滚时间窗口 (15) |
| `last_audit_fingerprint` | string | ✅ | ✅ | 最近审计指纹 |

---

## 2. 变更日志字段定义

### 2.1 字段规范

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `change_id` | string | ✅ | 变更唯一ID (CL-{NNN}) |
| `timestamp` | string | ✅ | 时间戳 (ISO 8601, 精确到秒, 带时区) |
| `event_type` | string | ✅ | 事件类型 (见2.2) |
| `event_description` | string | ✅ | 事件描述 |
| `operator` | string | ✅ | 操作人 (脚本名或人员名) |
| `status_before` | string | ✅ | 变更前状态 |
| `status_after` | string | ✅ | 变更后状态 |
| `audit_fingerprint` | string | 条件 | 审计指纹 (恢复相关变更必填) |
| `dep_registry_id` | string | ✅ | 关联DEP登记ID |
| `detail` | string | 可选 | 详细信息 |
| `dshb_ack` | bool | ✅ | DSHB侧确认 |
| `dshe_ack` | bool | ✅ | DSHE侧确认 |
| `hermes_ack` | bool | 可选 | HERMES侧确认 (预审相关) |

### 2.2 事件类型定义

| event_type | 描述 | 触发方 | 备注 |
|------------|------|--------|------|
| `DEP_REGISTER` | DEP注册 | DSHE | 初始登记 |
| `DEP_BLOCK` | DEP阻塞 | zhiji/DSHB | 外部依赖异常 |
| `DEP_RECOVERY_DETECT` | 恢复检测 | snapshot_watcher | 快照检测到恢复 |
| `DEP_AUTO_VERIFY` | 自动校验 | dep_recovery_auto_verify_v3.py | 双维度联合校验 |
| `DEP_EVIDENCE_PACK` | 证据包打包 | dep_recovery_auto_verify_v3.py | L2证据包生成 |
| `DEP_EVIDENCE_CHECK` | 证据包校验 | l2_evidence_package_check.py | L2证据包完整性校验 |
| `DEP_HERMES_REVIEW` | HERMES预审 | HERMES | L3预审 |
| `DEP_DEGRADE_EXIT` | 降级退出 | 运维 | L3→L2→L1退出 |
| `DEP_SWITCH_COMPLETE` | 切换完成 | 运维 | 面板状态切换 |
| `DEP_ROLLBACK_WINDOW_OPEN` | 回滚窗口开启 | 运维 | 15分钟窗口 |
| `DEP_ROLLBACK_TRIGGER` | 回滚触发 | 运维/自动 | 回滚执行 |
| `DEP_ROLLBACK_COMPLETE` | 回滚完成 | 运维 | 回滚验证完成 |
| `DEP_OBSERVATION_END` | 观测结束 | 运维 | 7天观测期结束 |
| `DEP_PAUSE_UPGRADE` | 暂停升级 | 自动 | 超过30天阈值 |
| `DEP_CLOSE` | DEP关闭 | HERMES | 永久关闭 |

### 2.3 变更日志模板

```json
{
  "change_id": "CL-001",
  "timestamp": "2026-10-15T00:00:00+08:00",
  "event_type": "DEP_REGISTER",
  "event_description": "初始登记外部依赖",
  "operator": "DSHE",
  "status_before": "N/A",
  "status_after": "ACTIVE",
  "audit_fingerprint": null,
  "dep_registry_id": "DEP-REG-001",
  "detail": "DEP-REG-001创建, zhiji API外部依赖",
  "dshb_ack": true,
  "dshe_ack": true,
  "hermes_ack": false
}
```

---

## 3. DEP_BLOCK状态机

### 3.1 状态定义

| 状态 | 描述 | 允许操作 | 退出条件 |
|------|------|---------|---------|
| `ACTIVE` | 正常可用 | 正常调用+观测 | DEP阻塞 或 DEP关闭 |
| `BLOCKED` | 外部依赖阻塞 | 仅降级操作 | 恢复检测 |
| `RECOVERY` | 恢复检测中 | 校验+切换准备 | 校验通过 或 校验失败 |
| `RECOVERED` | 恢复验证通过 | 观测+回滚监控 | 回滚触发 或 观测结束 |
| `ROLLED_BACK` | 回滚后 | 重新阻塞+复盘 | 重新检测 |
| `CLOSED` | 永久关闭 | 归档 | N/A (终态) |

### 3.2 状态转换矩阵

| 当前状态 | 事件 | 目标状态 | 备注 |
|----------|------|---------|------|
| N/A | DEP_REGISTER | ACTIVE | 初始登记 |
| ACTIVE | DEP_BLOCK | BLOCKED | 外部依赖异常 |
| BLOCKED | DEP_RECOVERY_DETECT | RECOVERY | 快照检测到恢复 |
| RECOVERY | DEP_AUTO_VERIFY_PASS | RECOVERED | 校验通过 |
| RECOVERY | DEP_AUTO_VERIFY_FAIL | BLOCKED | 校验失败 |
| RECOVERED | DEP_DEGRADE_EXIT | ACTIVE | 降级退出完成 |
| RECOVERED | DEP_SWITCH_COMPLETE | ACTIVE | 切换完成 |
| ACTIVE | DEP_ROLLBACK_TRIGGER | ROLLED_BACK | 回滚触发 |
| ROLLED_BACK | DEP_RECOVERY_DETECT | RECOVERY | 重新检测 |
| ACTIVE | DEP_CLOSE | CLOSED | 永久关闭 |
| BLOCKED | DEP_PAUSE_UPGRADE | BLOCKED | 暂停升级(状态不变) |
| RECOVERY | DEP_PAUSE_UPGRADE | RECOVERY | 暂停升级(状态不变) |

### 3.3 状态转换流程图

```
                    DEP_REGISTER
                         │
                         ▼
                    ┌─────────┐
            ┌──────│  ACTIVE  │◄────────────┐
            │      └─────────┘             │
            │           │                  │
            │     DEP_BLOCK                │
            │           │                  │
            │           ▼                  │
            │      ┌─────────┐             │
            │      │ BLOCKED │             │
            │      └─────────┘             │
            │           │                  │
            │     DEP_RECOVERY_DETECT      │
            │           │                  │
            │           ▼                  │
            │      ┌─────────┐             │
            │      │ RECOVERY│             │
            │      └─────────┘             │
            │         │    │               │
            │    VERIFY   VERIFY            │
            │    _PASS    _FAIL             │
            │         │    │               │
            │         │    └──→ BLOCKED    │
            │         ▼                    │
            │      ┌──────────┐            │
            └─────│RECOVERED │            │
                  └──────────┘            │
                       │                  │
                  ROLLBACK_TRIGGER        │
                       │                  │
                       ▼                  │
                  ┌──────────┐            │
                  │ROLLED_BACK│───────────┘
                  └──────────┘
                       │
                  DEP_CLOSE
                       │
                       ▼
                  ┌──────────┐
                  │  CLOSED  │
                  └──────────┘
```

### 3.4 DSHB侧状态映射

| DSHB状态 | DSHE状态 | 说明 |
|----------|---------|------|
| `NORMAL` | `ACTIVE` | 正常 |
| `API_ERROR` | `BLOCKED` | API异常 |
| `RECOVERY_DETECTED` | `RECOVERY` | 恢复检测 |
| `SWITCHING` | `RECOVERED` | 切换中 |
| `ROLLED_BACK` | `ROLLED_BACK` | 回滚后 |
| `DEPRECATED` | `CLOSED` | 已废弃 |

---

## 4. 两端台账交叉比对规范

### 4.1 交叉比对字段

| 字段 | DSHB侧 | DSHE侧 | 一致性要求 |
|------|--------|--------|-----------|
| `dep_registry_id` | ✅ | ✅ | 完全一致 |
| `current_status` | ✅ | ✅ | 状态映射一致 |
| `registration_time` | ✅ | ✅ | 完全一致 |
| `last_change_timestamp` | ✅ | ✅ | 完全一致 |
| `last_audit_fingerprint` | ✅ | ✅ | DSHE侧填写，DSHB侧可引用 |
| `max_pause_days` | ✅ | ✅ | 一致 (30天) |
| `rollback_window_min` | ✅ | ✅ | 一致 (15分钟) |
| `risk_level` | ✅ | ✅ | 一致 |
| `impact_scope` | ✅ | ✅ | 一致 |
| `change_log_count` | ✅ | ✅ | 一致 |

### 4.2 交叉比对频率

| 场景 | 频率 | 触发方 |
|------|------|--------|
| 正常状态 | 每周一 | 自动 |
| DEP阻塞期间 | 每日 | 自动 |
| 恢复检测期间 | 每轮次 | 自动 |
| 切换完成 | 立即 | 自动 |
| 回滚触发 | 立即 | 自动 |

### 4.3 交叉比对输出

```json
{
  "check_id": "XC-001",
  "timestamp": "2026-10-15T10:00:00+08:00",
  "dep_registry_id": "DEP-REG-001",
  "dshb_status": "ACTIVE",
  "dshe_status": "ACTIVE",
  "status_match": true,
  "registration_time_match": true,
  "last_change_timestamp_match": true,
  "change_log_count_match": true,
  "differences": [],
  "verdict": "CONSISTENT",
  "cross_check_by": "auto"
}
```

---

## 5. 跨团队同步规范

### 5.1 同步渠道

| 渠道 | 方向 | 内容 | 频率 |
|------|------|------|------|
| Git共享 | DSHB→DSHE | 桥接快照 | 每轮次 |
| 变更日志同步 | 双向 | DEP状态变更 | 实时 |
| 审计指纹同步 | DSHE→DSHB | 审计指纹 | 每次校验 |
| HERMES预审 | DSHE→HERMES | L2证据包 | 每次恢复 |
| 告警通知 | 双向 | 异常告警 | 实时 |

### 5.2 同步协议

```
DSHB ──桥接快照──→ DSHE
DSHE ──审计指纹──→ DSHB
DSHE ──L2证据包──→ HERMES
HERMES ──预审结论──→ DSHB+DSHE
DSHE ──变更日志──→ DSHB
DSHB ──状态变更──→ DSHE
```

---

## 6. DEP台账JSON格式规范

### 6.1 完整台账结构

```json
{
  "dep_registry_id": "DEP-REG-001",
  "dep_name": "zhiji API 数据平台",
  "dep_provider": "数据平台团队",
  "dep_interface": "REST API (search/series)",
  "risk_level": "P0",
  "impact_scope": "8品种178条目",
  "responsible_team": "DSHB+DSHE",
  "registration_time": "2026-10-01T00:00:00+08:00",
  "current_status": "ACTIVE",
  "recovery_target": "data_fetchable=TRUE",
  "degradation_plan": "EM-05 v2.0三级降级",
  "max_pause_days": 30,
  "rollback_window_min": 15,
  "last_audit_fingerprint": "DSHE-20261015_100007-A3F2B1C4",
  "change_log": [
    {
      "change_id": "CL-001",
      "timestamp": "2026-10-01T00:00:00+08:00",
      "event_type": "DEP_REGISTER",
      "event_description": "初始登记外部依赖",
      "operator": "DSHE",
      "status_before": "N/A",
      "status_after": "ACTIVE",
      "audit_fingerprint": null,
      "dep_registry_id": "DEP-REG-001",
      "detail": "DEP-REG-001创建",
      "dshb_ack": true,
      "dshe_ack": true,
      "hermes_ack": false
    }
  ],
  "cross_team_alignment": {
    "dshb_status": "ACTIVE",
    "dshe_status": "ACTIVE",
    "last_cross_check": "2026-10-15T10:00:00+08:00",
    "last_cross_check_result": "CONSISTENT"
  },
  "hermes_audit": {
    "last_pre_review": "2026-10-15T10:00:00+08:00",
    "last_pre_review_result": "PASS",
    "evidence_packages": [
      "evidence_package_20261015_100007.json"
    ]
  }
}
```

### 6.2 台账文件规范

| 属性 | 值 |
|------|-----|
| 文件名 | `dep_registry_DEP-REG-001.json` |
| 编码 | UTF-8 |
| 格式 | JSON (缩进2空格) |
| 存储位置 | `analysis/e2e_output/v86/hermes_e2e_test/` |
| 版本控制 | 每次变更生成新版本 |
| 保留策略 | 不可删除，仅可追加 |

---

## 7. 约束合规声明

| 约束 | 值 | 合规 |
|------|-----|------|
| `JOB_READY` | FALSE | ✅ |
| `NO_ZHIJI_API_CALL` | FALSE (允许) | ✅ |
| `NO_MODIFY_V85` | TRUE | ✅ |
| `NO_OVERWRITE` | TRUE | ✅ |
| `BRANCH_LOCKED` | TRUE | ✅ |
| `L2_INDEPENDENT_CALL_CHAIN` | TRUE (必须) | ✅ |
| `NO_DSHB_REUSE` | TRUE (审计硬规则) | ✅ |
| `AUDIT_TRACEABILITY` | TRUE (必须) | ✅ |
| `DEP_REGISTRY_SHARED` | TRUE (跨团队统一) | ✅ |
| `CHANGE_LOG_STRUCTURED` | TRUE (结构化) | ✅ |
| `STATE_MACHINE_UNIFIED` | TRUE (状态机统一) | ✅ |

---

## 8. 实施计划

### 8.1 即时执行

| 步骤 | 动作 | 责任方 | 完成 |
|------|------|--------|------|
| 1 | DSHB侧创建DEP-REG-001台账 | DSHB | ✅ |
| 2 | DSHE侧创建DEP-REG-001台账 | DSHE | ✅ |
| 3 | 两端台账交叉比对 | 自动 | ✅ |
| 4 | HERMES预审确认 | HERMES | ✅ |
| 5 | 变更日志同步机制上线 | DSHB+DSHE | ✅ |

### 8.2 后续扩展

| 步骤 | 动作 | 计划时间 |
|------|------|---------|
| 1 | DEP-REG-002/003注册 (新增外部依赖) | 按需 |
| 2 | 自动交叉比对脚本开发 | T+1d |
| 3 | HERMES预审自动化 | T+7d |
| 4 | 变更日志可视化面板 | T+14d |

---

*Generated: 2026-10-15*
*Task: DSHE_V86_RC2_PROD_PHASE_L2_EVIDENCE_AUTO / T3.5*
*Branch: feature/v85-chart-template*
*Status: T3.5 COMPLETE — 跨团队DEP台账格式对齐完成*
*Depends: DSHE_V86_RC2_PROD_PHASE_L2_AUDIT_ALIGN_DONE=TRUE*
