# V86-RC2 CASE-A01 失败用例根因归档与回归步骤（T3.2）

> **工单**: 工单-HERMES / T3.2 CASE-A01失败用例根因归档
> **分支**: `feature/v85-chart-template` @ `629ccb7`
> **编制方**: HERMES (L3 审计方)
> **日期**: 2026-10-15
> **状态**: ✅ 归档完成（3项预期失败，DEP恢复后回归路径清晰）
> **约束**: NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE

---

## 1. 归档概览

CASE-A01真实预发执行共8项断言，5 PASS / 3 FAIL。3项FAIL均为**DEP-001阻塞的预期行为**，非代码缺陷。

| 断言 | 描述 | 实测 | 根因 | 类型 |
|------|------|------|------|------|
| A8 | verdict=PASS | **FAIL** (verdict=FAIL) | DEP-001 BLOCKED → 审计器产出CRITICAL → verdict=FAIL | 预期行为 |
| A9 | CRITICAL=0 | **FAIL** (CRITICAL=1) | DEP-001 BLOCKED 产生 DEPENDENCY_BLOCK CRITICAL 事件 | 预期行为 |
| A10 | short_circuit=0 | **FAIL** (短路触发) | P1批存在CRITICAL → 短路跳过10批 | 预期行为 |

---

## 2. 根因分析

### 2.1 根因链（三个FAIL共因）

```
DEP-001 短ID解析服务未就绪
  └─ zhiji_api.py series j25_tc → HTTP 500「无法识别指标来源(id前缀)」
      └─ 证据包 dep_registry 中 DEP-001 状态 = BLOCKED
          └─ 审计器v3 check_dep_state → 产出 CRITICAL 事件 (DEPENDENCY_BLOCK)
              └─ verdict() 短路判定: P1批存在CRITICAL
                  ├─ A9 FAIL (CRITICAL=1)
                  ├─ A10 FAIL (短路触发, 跳过10批)
                  └─ A8 FAIL (verdict=FAIL)
```

### 2.2 各FAIL详情

#### A8 verdict=PASS FAIL

- **期望**: verdict=PASS（正向用例）
- **实测**: verdict=FAIL
- **证据链路**: `dep_registry[0].status=BLOCKED` → `check_dep_state` → CRITICAL `DEP-001未就绪: BLOCKED` → `_verdict_full`/短路判定产出FAIL
- **根因**: DEP-001服务侧故障（服务器返回HTTP 500，非HERMES代码问题）
- **预期行为**: ✅ **正确**。DEP未就绪时判定FAIL是审计器的设计意图——防止未验证链路上线。

#### A9 CRITICAL=0 FAIL

- **期望**: CRITICAL=0（正向）
- **实测**: CRITICAL=1（DEPENDENCY_BLOCK）
- **证据链路**: 同上
- **根因**: DEP-001 BLOCKED
- **预期行为**: ✅ **正确**。CRITICAL事件如实反映DEP阻塞，不隐藏。

#### A10 short_circuit=0 FAIL

- **期望**: short_circuit=0（不短路）
- **实测**: 短路触发，跳过10批（dual_evidence/trace_fingerprint/bridge_rate/dep_state/dep_flap/dep_xreg/data_fetch/legacy_caliber/dep_classification/retire_flag）
- **证据链路**: `short_circuit={'enabled': True, 'skipped_batches': [...], 'skip_reason': 'P1 Gate 强制项 CRITICAL', 'skipped_count': 10}`
- **根因**: 设计使然——P1批CRITICAL强制短路，避免在已知阻塞下继续审计无意义批次
- **预期行为**: ✅ **正确**。短路是性能优化+风险控制，DEP阻塞时跳过下游审计是合理设计。

---

## 3. 判定标准（为什么这些算PASS的"预期失败"）

| 标准 | 说明 |
|------|------|
| 根因在外部 | DEP-001为B团队部署的服务，故障在服务器侧 |
| 行为符合设计 | 审计器设计为「DEP阻塞→CRITICAL→短路→FAIL」 |
| 不掩盖问题 | CRITICAL事件如实记录，未吞掉异常 |
| 恢复后应通过 | DEP恢复后重跑，3项应转PASS |

---

## 4. DEP恢复后的回归验证步骤

### 前置条件

- [ ] B团队确认DEP-001状态=RECOVERED
- [ ] `zhiji_api.py series j25_tc 2026-08-01 2026-08-31` 返回HTTP 200 + 非空
- [ ] `zhiji_api.py series i1 2026-08-01 2026-08-31` 返回HTTP 200 + 非空
- [ ] `zhiji_api.py series i2 2026-08-01 2026-08-31` 返回HTTP 200 + 非空

### 回归步骤（Step 1-5 重跑）

1. **Step 1 证据包**: 将 `dep_registry[0].status` 改为 `RECOVERED`，保留相同 calls
2. **Step 2 Gate**: 重跑 `gate_pre_check_auto_v5.py`（期望G05桥接率≥80%）
3. **Step 3 审计**: 重跑 `case_a01_run2.py` 等价逻辑（期望verdict=PASS, CRITICAL=0, 短路不触发）
4. **Step 4 WAL**: 重跑写入+去重（期望与上轮一致：写入PASS/去重PASS）
5. **Step 5 面板**: 重跑端口连通（期望200）

### 回归断言（8项全PASS）

| 断言 | 回归期望 |
|------|----------|
| A8 verdict=PASS | PASS |
| A9 CRITICAL=0 | PASS |
| A10 short_circuit=0 | PASS |
| A11 elapsed≤15ms | PASS |
| A12 事件全写入 | PASS |
| A13 journal_mode=wal | PASS |
| A14 去重生效 | PASS |
| A15 面板端口连通 | PASS |

### 回归判定标准

- **8/8 PASS**: 回归通过，CASE-A01完整闭环
- **任一FAIL**: 记录偏差，检查DEP恢复是否完整（j25_tc/i1/i2三ID都要200）

---

## 5. 关联风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| DEP-001恢复不完整（部分短ID仍500） | A8/A9/A10仍FAIL | 回归前置条件要求三ID全200 |
| 短ID解析修复引入新字段 | 审计器字段兼容 | 载荷容错测试覆盖（T3.4） |
| G05桥接率在真实取数后跳变 | Gate判定波动 | 灰度阶梯阈值分阶段（G0/G1:80%, G2+:90%） |

---

*本归档为CASE-A01 3项预期失败用例的根因说明、预期行为与DEP恢复后回归步骤。恢复后按§4重跑即可验证闭环。*
