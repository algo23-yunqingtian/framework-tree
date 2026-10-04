# V86-RC2 DEP-001 就绪后 E2E 全链路测试检查清单（逐点可勾选版）

> **工单**: 工单-HERMES / T3.4 DEP就绪E2E测试详细检查清单
> **分支**: `feature/v85-chart-template` @ commit `dcf7194`
> **编制方**: HERMES（L3 审计方）
> **日期**: 2026-10-15
> **基础文档**: `v86_rc2_hermes_dep_ready_e2e_test_plan.md`（三阶段预案，本轮细化为逐点清单）
> **DEP 状态机**: `v86_rc2_dep_registry_common_spec.md` §3（6 状态 12 迁移）
> **工具链**: `evidence_auditor_v2.py --self-test` + `batch_evidence_audit_runner.py`
> **契约**: EVIDENCE_CONTRACT_V1
> **状态**: READY — DEP-001 恢复后逐项勾选执行

---

## 0. 使用说明

- 每个检查项格式：`[ ] 编号 描述 | 判定标准 | 失败后果 | 责任人 | 阻断级别`
- **阻断级别**：`STOP`（必须通过才能进入下一阶段）/ `BLOCK`（当前包阻断，可修复重提）/ `NOTE`（记录不阻断）
- 每项执行后勾选 `[x]` 并记录实测值
- 任一 `STOP` 项失败 → 立即停止并执行 §8 回滚

---

## 1. 阶段 P0：前置环境检查（STOP 级，全绿才启动）

| 勾选 | 编号 | 检查项 | 判定标准 | 失败后果 | 责任人 | 阻断 |
|------|------|--------|---------|---------|--------|------|
| [ ] | P0-1 | DEP-001 状态已置 RESOLVED | 依赖登记表 `current_status` 由 BLOCKED → RECOVERY | 判定 DEP 未就绪，禁止启动 | 数据平台 | STOP |
| [ ] | P0-2 | 数据平台书面确认上线 | 登记表 `state_history` 含 `DEP_RECOVERY_DETECT` 事件 | 同上 | 数据平台 | STOP |
| [ ] | P0-3 | 短ID 探测集全 HTTP 200 | `dep_recovery_auto_verify.py` 输出全 PASS | F1 链路级失败 → 回滚 | HERMES | STOP |
| [ ] | P0-4 | 对照组仍健康 | `ID02226332` 返回 200 且 ≥1 非零点 | 环境故障，禁止启动 | HERMES | STOP |
| [ ] | P0-5 | 对照组与短ID 归因分离 | 短ID 200 **且** 对照组 200（缺一不可） | 归因不清，禁止启动 | HERMES | STOP |
| [ ] | P0-6 | 审计器自回归通过 | `evidence_auditor_v2.py --self-test` → PASSED | 审计器退化，禁止使用 | HERMES | STOP |
| [ ] | P0-7 | 审计器 MD5 未被篡改 | `--check-md5 evidence_auditor_v2.py --expect <锁定值>` → PASS | 防篡改失败 → 停止 | HERMES | STOP |
| [ ] | P0-8 | 契约版本一致 | 三方确认 `EVIDENCE_CONTRACT_V1` | 契约不一致 → 停止 | 三方 | STOP |
| [ ] | P0-9 | 三方台账一致 | 交叉比对 9 字段全一致（DS-05 无告警） | DEP 归因错乱 → 停止 | DSHB+DSHE | STOP |

---

## 2. 阶段 P1：L1 自测（DSHB）

| 勾选 | 编号 | 检查项 | 判定标准 | 失败后果 | 责任人 | 阻断 |
|------|------|--------|---------|---------|--------|------|
| [ ] | P1-1 | L1 包符合契约 | `contract_version=EVIDENCE_CONTRACT_V1`（CV-01/02 无告警） | 拒收 | DSHB | STOP |
| [ ] | P1-2 | L1 必填字段齐全 | 7 顶层 + 6 调用字段齐全（CV-03/04 无告警） | 拒收 | DSHB | STOP |
| [ ] | P1-3 | `call_type` 正确 | 全部为 `DSHB_L1_SELF_TEST` | 拒收 | DSHB | STOP |
| [ ] | P1-4 | 脚本入参为被测 ID 本身 | `script_audit.uses_search_passthrough=false`（D04.1 无告警） | 造假冒入 → 阻断 | DSHB | BLOCK |
| [ ] | P1-5 | 一致性断言存在 | `has_id_consistency_assert=true`（D04.2 无告警） | G-09 FAIL | DSHB | BLOCK |
| [ ] | P1-6 | 非全 0 计 PASS | `zero_value_counts_as_pass=false` | G-09 FAIL | DSHB | BLOCK |
| [ ] | P1-7 | 原始 payload 留存 | `retains_raw_payload=true`（D04.4 无告警） | G-09 FAIL | DSHB | BLOCK |
| [ ] | P1-8 | COMPLETED 双证据齐全 | 每条含 payload + value≠0（D01.2 无告警） | PENDING 降级 | DSHB | BLOCK |
| [ ] | P1-9 | 桥接率双栏拆分 | `metadata_rate` + `real_fetchable_rate` 齐全（D02.2 无告警） | 退回补口径 | DSHB | BLOCK |
| [ ] | P1-10 | 无桥接率分子虚增 | 声明率 ≤ 实测率（D02.3 无告警） | 阻断 | DSHB | BLOCK |
| [ ] | P1-11 | 无存量旧口径残留 | LC-01/LC-02 无告警 | 阻断 | DSHB | BLOCK |
| [ ] | P1-12 | MD5 清单存在 | `md5_manifest` 存在（CV-05 无告警） | CONDITIONAL | DSHB | NOTE |
| [ ] | P1-13 | 未引用已退回 run_id | `reused_from_run_id` 为空（L2-R08 无告警） | 阻断 | DSHB | BLOCK |

---

## 3. 阶段 P2：L2 独立抽样（DSHE）

| 勾选 | 编号 | 检查项 | 判定标准 | 失败后果 | 责任人 | 阻断 |
|------|------|--------|---------|---------|--------|------|
| [ ] | P2-1 | L2 包符合契约 | CV-01~04 无告警 | 拒收 | DSHE | STOP |
| [ ] | P2-2 | `dshb_reuse=false` | 未为 `true`（D03.2 无告警） | 背书式 → 阻断 | DSHE | BLOCK |
| [ ] | P2-3 | 调用链独立 | 全部 `call_type=DSHE_INDEPENDENT_ZHIJI` | 零价值 → 阻断 | DSHE | BLOCK |
| [ ] | P2-4 | calls 非空 | `calls.length ≥ 1`（D03.2 无告警） | 阻断 | DSHE | BLOCK |
| [ ] | P2-5 | trace_id 唯一 | 无重复（D03.1 无 HIGH） | 溯源失败 | DSHE | BLOCK |
| [ ] | P2-6 | 审计指纹齐全 | `fingerprint`/`run_id`/`session_id` 齐全 | 阻断 | DSHE | BLOCK |
| [ ] | P2-7 | fingerprint 为新生成 | 不复用退回轮次 | 阻断 | DSHE | BLOCK |
| [ ] | P2-8 | 独立取数非背书引用 | 不引用 DSHB 自报数字 | 零价值 | DSHE | BLOCK |
| [ ] | P2-9 | 分层抽样覆盖 7 品种 | 每品种 ≥4 条 | 覆盖不足 → 退回 | DSHE | BLOCK |
| [ ] | P2-10 | P0/P1/P2 三层齐备 | 24/20/16 条分层 | 退回 | DSHE | BLOCK |
| [ ] | P2-11 | L2 verdict=PASS | 审计器判定 PASS | 退回 DSHE 重做 | DSHE | STOP |
| [ ] | P2-12 | DEP 分类有据 | `DEPENDENCY_BLOCK` 有外部证据（DEP-CLASS 无告警） | 降级内部缺陷 | DSHE | BLOCK |
| [ ] | P2-13 | DEP 关联登记ID | `dep_registry_id` 非空 | CONDITIONAL | DSHE | NOTE |
| [ ] | P2-14 | 跨团队台账一致 | DS-05 无告警 | 阻断 | DSHB+DSHE | BLOCK |

---

## 4. 阶段 P3：L3 HERMES 预审

| 勾选 | 编号 | 检查项 | 判定标准 | 失败后果 | 责任人 | 阻断 |
|------|------|--------|---------|---------|--------|------|
| [ ] | P3-1 | 批量调度执行 | `batch_evidence_audit_runner.py` 无扫描错误 | 停止 | HERMES | STOP |
| [ ] | P3-2 | 无 CRITICAL 告警 | 汇总 `CRITICAL=0` | 按 §5 路由派工 | HERMES | STOP |
| [ ] | P3-3 | 审计器自回归仍通过 | `--self-test` → PASSED（防中途退化） | 停止 | HERMES | STOP |
| [ ] | P3-4 | 用例库无退化 | 23 用例判定全符合预期 | 停止 | HERMES | STOP |
| [ ] | P3-5 | 契约版本校验 | CV-02 无告警 | 拒收 | HERMES | STOP |
| [ ] | P3-6 | 双证据合规 | D01.x 无 CRITICAL | 退回 | HERMES | BLOCK |
| [ ] | P3-7 | 桥接率口径合规 | D02.x 无 CRITICAL | 退回 | HERMES | BLOCK |
| [ ] | P3-8 | L2 独立性合规 | D03.x 无 CRITICAL | 退回 | HERMES | BLOCK |
| [ ] | P3-9 | Gate 强制项合规 | D04.x 无 CRITICAL | 退回 | HERMES | BLOCK |
| [ ] | P3-10 | DEP 状态机合法 | DS-02/DS-03 无告警 | 阻断 | HERMES | BLOCK |
| [ ] | P3-11 | 无旧口径残留 | LC-01/02/03 无告警 | 阻断 | HERMES | BLOCK |
| [ ] | P3-12 | 告警事件已持久化 | 事件写入含 dep_registry_id/trace_id | 记录缺失 | HERMES | NOTE |
| [ ] | P3-13 | 告警已路由 | 按责任方分发（DSHB/DSHE） | 派工缺失 | HERMES | NOTE |

---

## 5. 阶段 P4：Gate 评审（G01~G10）

| 勾选 | 编号 | Gate | 判定标准 | 失败后果 | 责任人 | 阻断 |
|------|------|------|---------|---------|--------|------|
| [ ] | P4-1 | G-01 | L1 自测包完整 | 退回 DSHB | HERMES | BLOCK |
| [ ] | P4-2 | G-02 | L2 独立调用链（`dshb_reuse=false` + trace 唯一） | 退回 DSHE | HERMES | BLOCK |
| [ ] | P4-3 | G-03 | 双证据齐全（178/178） | 退回 | HERMES | BLOCK |
| [ ] | P4-4 | G-04 | 元数据完成率 = 100% | 退回 | HERMES | BLOCK |
| [ ] | P4-5 | G-05 | 桥接率口径双栏齐全 | CONDITIONAL | HERMES | NOTE |
| [ ] | **P4-6** | **G-06** | **真实可取数率 = 100%** | **NOT_READY** | HERMES | **STOP** |
| [ ] | P4-7 | G-07 | DEP 登记 10 字段齐全 | 阻断 | HERMES | BLOCK |
| [ ] | P4-8 | G-08 | 无残留 Mock 数据 | NOT_READY | DSHB | STOP |
| [ ] | **P4-9** | **G-09** | **脚本审计（无 search 中转 + 一致性断言）** | **NOT_READY** | HERMES | **STOP** |
| [ ] | **P4-10** | **G-10** | **真实取数（对照组 + 目标全通过）** | **NOT_READY** | HERMES | **STOP** |

> **G-06 / G-09 / G-10 为强制项**：任一 FAIL 即 `Gate=NOT_READY`，无豁免路径。

---

## 6. 阶段 P5：灰度准入

| 勾选 | 编号 | 检查项 | 判定标准 | 失败后果 | 责任人 | 阻断 |
|------|------|--------|---------|---------|--------|------|
| [ ] | P5-1 | Gate 结论 READY | `gate_result=READY` | 禁止灰度 | HERMES | STOP |
| [ ] | P5-2 | 影子测试 5 项放行条件全满足 | 至少 3 项此前不满足者已恢复 | 禁止灰度 | DSHE | STOP |
| [ ] | P5-3 | 灰度范围限定 | 先单品种（建议 PB）后扩量 | 超范围 → 停止 | 运维 | STOP |
| [ ] | P5-4 | 面板渲染验证 | 灰度品种面板无渲染缺陷 | 停止 | DSHE | BLOCK |
| [ ] | P5-5 | 观测面板已配置 | 关键指标监控就绪 | 禁止扩量 | DSHE | STOP |
| [ ] | P5-6 | 告警通道已联通 | CRITICAL 可实时推送 | 禁止扩量 | HERMES | STOP |
| [ ] | P5-7 | 回滚窗口已开启 | 15 分钟窗口（`rollback_window_min=15`） | 禁止扩量 | 运维 | STOP |
| [ ] | P5-8 | 回滚责任人在线 | 值班确认 | 禁止扩量 | 运维 | STOP |

---

## 7. 阶段 P6：观测监控（7 天观测期）

| 勾选 | 编号 | 检查项 | 判定标准 | 失败后果 | 责任人 | 阻断 |
|------|------|--------|---------|---------|--------|------|
| [ ] | P6-1 | DEP 状态置 RECOVERED | `state_history` 含 `DEP_AUTO_VERIFY_PASS` | 状态错误 | HERMES | BLOCK |
| [ ] | P6-2 | 观测期开始记录 | 登记表更新时间戳 | 追溯缺失 | HERMES | NOTE |
| [ ] | P6-3 | 每日快照复核 | `snapshot_watcher` 无异常 | 触发 F2 | HERMES | BLOCK |
| [ ] | P6-4 | 数据质量监控 | 无新增全 0 / 语义错配 | 触发 F2 | HERMES | BLOCK |
| [ ] | P6-5 | 三方台账每日比对 | DS-05 持续无告警 | 触发 F3 | DSHB+DSHE | BLOCK |
| [ ] | P6-6 | 告警事件每日汇总 | 日报无 CRITICAL | 触发 F2 | HERMES | NOTE |
| [ ] | P6-7 | 超阈值监控 | 未超 `max_pause_days=30` | 触发 DEP_PAUSE_UPGRADE | 自动 | BLOCK |

---

## 8. 阶段 P7：回滚验证

| 勾选 | 编号 | 检查项 | 判定标准 | 失败后果 | 责任人 | 阻断 |
|------|------|--------|---------|---------|--------|------|
| [ ] | P7-1 | 回滚触发条件已判定 | F1/F2/F3 之一成立 | 不应回滚 → 停止 | 运维 | NOTE |
| [ ] | P7-2 | 证据包已冻结 | 标记 `retired=true` + 归档 MD5 | 追溯链断裂 | HERMES | BLOCK |
| [ ] | P7-3 | DEP 状态回退 | RECOVERED → ROLLED_BACK（DS-02 合法） | 状态机错误 | HERMES | BLOCK |
| [ ] | P7-4 | JOB_READY 已恢复暂停标记 | `GATE_REVIEW_PAUSED=TRUE` | 状态失真 | HERMES | BLOCK |
| [ ] | P7-5 | 旧证据包已作废 | 禁止复用（L2-R08） | 违规复用 | 全体 | BLOCK |
| [ ] | P7-6 | 数据平台已通知 | 附对照组证据 | 沟通缺失 | HERMES | NOTE |
| [ ] | P7-7 | 回滚事件已持久化 | CRITICAL 级 + dep_registry_id | 追溯缺失 | HERMES | NOTE |
| [ ] | P7-8 | 回滚完成记录 | `DEP_ROLLBACK_COMPLETE` 事件 | 流程未闭环 | 运维 | BLOCK |

---

## 9. 失败分级速查

| 级别 | 定义 | 处置 |
|------|------|------|
| **F1 链路级** | 短ID 仍 HTTP 500 / 对照组也失败 | 判定 DEP 未真正就绪或环境故障，**立即回滚**，DEP-001 重开 |
| **F2 审计级** | 链路通但审计 CRITICAL > 0 | 退回对应责任方（按 §5 路由），旧证据包作废 |
| **F3 Gate级** | 审计 PASS 但 G-06 未达阈值 | Gate NOT_READY，登记部分恢复，等待补齐 |

### 9.1 处置责任矩阵

| 触发规则 | 检测点 | 退回对象 | 处置动作 |
|---------|-------|---------|---------|
| R-AUDIT-01 | D01.2/D01.3 | **DSHB** | 删除旧脚本产出，重跑取数 |
| R-AUDIT-02 | D02.1/D02.3 | **DSHB** | 拆分双栏桥接率 |
| R-AUDIT-03 | D03.1/D03.2 | **DSHE** | 重做独立调用链 |
| R-AUDIT-04 | D04.1~D04.5 | **DSHB** | 修复脚本入参/payload 留存 |
| R-CONTRACT-V1 | CV-01~05 | 提交方 | 按契约补齐字段 |
| R-DEP-STATE | DS-02/03/05 | **DSHB/DSHE** | 修正状态机迁移/台账对齐 |
| R-LEGACY-CAL | LC-01/02/03 | **DSHB** | 清除旧口径残留表述 |
| G-06 | 桥接率 < 100% | 按缺失条目归属 | 补齐取数 |

---

## 10. 检查清单统计

| 阶段 | 检查项数 | STOP 级 | BLOCK 级 | NOTE 级 |
|------|---------|---------|---------|---------|
| P0 前置环境 | 9 | 9 | 0 | 0 |
| P1 L1 自测 | 13 | 1 | 11 | 1 |
| P2 L2 独立抽样 | 14 | 2 | 11 | 1 |
| P3 L3 预审 | 13 | 4 | 6 | 3 |
| P4 Gate 评审 | 10 | 3 | 4 | 1（G-05 NOTE）+ 2 STOP 强制项 |
| P5 灰度准入 | 8 | 7 | 1 | 0 |
| P6 观测监控 | 7 | 0 | 5 | 2 |
| P7 回滚验证 | 8 | 0 | 6 | 2 |
| **合计** | **76** | **25+** | **44** | **9** |

**状态标记**：`HERMES_DEP_READY_E2E_CHECKLIST_READY=TRUE`（76 项逐点清单，8 阶段）
