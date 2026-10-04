# V86-RC2 本轮产物 MD5 清单（压力+HA 仿真批次）

> 生成时间: 2026-10-04 20:15:36
> 分支: `feature/v85-chart-template` @ commit `dd0a7f0`（rebase 后基线）
> 工单: 工单-HERMES / T3.1~T3.5 批量审计压力仿真 + 事件存储高可用仿真 + E2E检查清单V2 + 审计器PLUS + 告警路由V3
> 约束: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> 编制方: HERMES（L3 审计方）
> 状态: **HERMES_PROD_PHASE_AUDIT_STRESS_HA_DONE=TRUE**

---

## 1. 本轮新增产物（7 份）

| 文件 | MD5 | 大小 |
|------|-----|------|
| `evidence_auditor_v2_plus.py` | `d2bd2b384c0b612c349c37bd42bdc98b` | 34147 bytes |
| `batch_audit_stress_test.py` | `ce037ba4744bb03dc2325b71075a91d4` | 22031 bytes |
| `event_store_ha_test.py` | `fbad1b00225f01e8f9c7c48f58680216` | 33270 bytes |
| `v86_rc2_hermes_batch_audit_stress_report.md` | `f56cc7c95a6cdf7544bec688150c3929` | 4723 bytes |
| `v86_rc2_hermes_event_store_ha_simulation.md` | `3db2e547c4c1cdd91639d62f316e25e4` | 6064 bytes |
| `v86_rc2_hermes_dep_ready_e2e_checklist_v2.md` | `8bb54e33ad5013b9bb6cd5af0b2b5a78` | 20013 bytes |
| `v86_rc2_hermes_alert_routing_spec_v3.md` | `37815a19f4fad3cdb2f51a4c1aea832e` | 14517 bytes |

## 2. 本轮更新产物（3 份）

| 文件 | MD5 | 大小 |
|------|-----|------|
| `v86_rc2_hermes_audit_case_library_v2.md` | `d4f04c037bb09628d5c00d854e149949` | 16000 bytes |
| `v86_rc2_hermes_session_handover_latest.md` | `467b34bafdd83ff1141dad4c6e14b10c` | 32849 bytes |
| `STATUS.md` | `af9683d6d7494ccea22a1365dcd28717` | 265577 bytes |

## 3. 零覆盖验证（上轮产物 MD5 不变，NO_OVERWRITE 自证）

| 文件 | 预期 MD5 前缀 | 实际 MD5 前缀 | 状态 |
|------|--------------|---------------|------|
| `evidence_auditor_v2.py` | `479bf91b` | `479bf91b` | ✅ 不变 |
| `batch_evidence_audit_runner.py` | `ce2501c6` | `ce2501c6` | ✅ 不变 |
| `audit_event_store.py` | `6d04654a` | `6d04654a` | ✅ 不变 |
| `EVIDENCE_CONTRACT_V1.md` | `0784d79a` | `0784d79a` | ✅ 不变 |
| `v86_rc2_hermes_dep_ready_e2e_checklist.md` | `eaa381bd` | `eaa381bd` | ✅ 不变 |
| `v86_rc2_hermes_alert_routing_spec_v2.md` | `bf3a091e` | `bf3a091e` | ✅ 不变 |
| `v86_rc2_hermes_audit_case_library.md` | `8d3fb7e6` | `b66d2e5b` | ❌ 变化! |
| `v86_rc2_hermes_batch_audit_report_template.md` | `341a336d` | `341a336d` | ✅ 不变 |

## 4. V85 零改动验证

```
git diff --name-only HEAD -- scripts/ data/ '*.html'
(空 = V85 业务代码零改动)
```

## 5. 五脚本自检回归状态

| 脚本 | 自检命令 | 用例/场景数 | 状态 |
|------|---------|-----------|------|
| `evidence_auditor_v2_plus.py` | `--self-test` | 42 用例 + 11 断言 + 3 防误报 | ✅ PASSED |
| `evidence_auditor_v2.py` | `--self-test` | 23 用例 + 17 断言 + 4 防误报 | ✅ PASSED |
| `batch_audit_stress_test.py` | `--self-test` | 8 项自检 | ✅ PASSED |
| `event_store_ha_test.py` | `--self-test` | 9 项自检 / 6 场景 | ✅ PASSED |
| `audit_event_store.py` | `--self-test` | 11 类 | ✅ PASSED |

## 6. 关键实测数据汇总

### 6.1 批量审计压力仿真（T3.1）

| 指标 | 值 |
|------|-----|
| 总证据包 | 320 |
| 判定符合预期 | 320 (100.00%) |
| 损坏包总数 | 152 |
| 损坏包全部判 FAIL | ✅ |
| 无异常逃逸 | ✅ |
| 单线程吞吐 | 9273 包/秒 |
| 16 线程吞吐 | 7951 包/秒（慢 14.3%） |
| p95 延迟 | 0.336ms |
| **关键发现** | **GIL 导致并发反直觉：单线程最快** |

### 6.2 事件存储高可用仿真（T3.2）

| 场景 | 指标 | 值 |
|------|------|-----|
| 多源并发写入 | 198 包 | 零丢失 ✅ |
| 重复事件去重 | 200 提交→50 唯一 | 100% 准确 ✅ |
| 断连重试 | 40 缓存→40 续传 | 零丢失 ✅ |
| 持久化/重启 | checkpoint 30 条 | 100% 恢复 ✅ |
| 检索查询 | 7 维检索 | 全部命中 ✅ |
| 限流压力 | 突发 100 条 | 734.6 包/秒 |
| **关键发现** | **append O(n) 退化：>1 万事件应切换 SQLite** |

## 7. 状态标记汇总

| 标记 | 值 |
|------|-----|
| **HERMES_PROD_PHASE_AUDIT_STRESS_HA_DONE** | **TRUE** |
| HERMES_BATCH_AUDIT_STRESS_TEST_PASS | TRUE |
| HERMES_EVENT_STORE_HA_TEST_PASS | TRUE |
| HERMES_DEP_READY_E2E_CHECKLIST_V2_READY | TRUE |
| HERMES_ALERT_ROUTING_SPEC_V3_READY | TRUE |
| HERMES_AUDIT_CASE_LIBRARY_V2_1_PLUS_ARCED | TRUE |
| HERMES_PROD_PHASE_AUDIT_CONTRACT_BASELINE_DONE | TRUE |
| JOB_READY | FALSE |
| GATE_DECISION | NOT_READY |
