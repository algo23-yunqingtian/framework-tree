# HERMES 审计用例库 V3.0（V86-RC2 短路+WAL+灰度扩展版）

> **文档编号**: CASE-LIB v3.0
> **关联工单**: T3.4 审计用例库扩容与 self-test 更新
> **基线 commit**: `8fe68f3`
> **上一版**: `v86_rc2_hermes_audit_case_library_v2.md`（CASE-LIB v2.1-plus, **保留不删**）
> **本版载体**: `evidence_auditor_v3.py`（auditor v3.0.0, 短路+增量校验）+ `event_store_wal_v2.py` + `gray_stair_sim.py`
> **日期**: 2026-10-15
> **状态**: ✅ v3 self-test 全通过（50 用例 + 判定等价性零破坏 + 短路 5 项 + 增量 3 项 + LRU + 漂移）+ WAL 9 项 + 灰度 10 项

---

## 0. 版本演进总览

| 版本 | 载体 | 用例数 | 核心能力 | self-test |
|------|------|--------|---------|-----------|
| v1.0 | `evidence_auditor.py` | 12 | 基础规则审计 | — |
| v2.0 | `evidence_auditor_v2.py` | 23 | +48 项审计 + 5 项防误报 + 性能预算 | ✅ |
| v2.1 | 同上 | 23 | +批量调度 | ✅ |
| **v2.1-plus** | `evidence_auditor_v2_plus.py` | **42** | +性能守卫 PERF-GUARD +损坏包容错 ROB-01 +DEP 抖动 DS-06 +状态漂移 +11 断言 | ✅ |
| **v3.0** | **`evidence_auditor_v3.py`** | **50** | **+短路判定（5 项）+增量校验（3 项）+LRU 缓存 +状态漂移 +判定等价性自证** | **✅** |
| **WAL** | **`event_store_wal_v2.py`** | **9** | **WAL 模式 +读写并发 +UPSERT 去重 +崩溃恢复 +自动切换 +索引检索 +高容量 +checkpoint +崩溃去重** | **✅** |
| **灰度** | **`gray_stair_sim.py`** | **10** | **6 级灰度准入 +5 类故障注入 +回滚矩阵 +阈值收紧 +DEP 阻断** | **✅** |

**累计**：79 项自回归用例（v3: 50 + WAL: 9 + 灰度: 10 + 基线回归 10）。

---

## 1. V3 审计器新增用例（19 项：42 基线 + 5 短路 + 3 增量 + LRU + 漂移 + 等价性）

### 1.1 短路判定用例（5 项）

| 用例 | 描述 | 预期短路批次 | 跳过批次 |
|------|------|------------|---------|
| **SC-01** | PERF-GUARD 超时短路 | PERF-GUARD | 所有检测（直接 return） |
| **SC-02** | PERF-GUARD 调用数超限短路 | PERF-GUARD | 所有检测 |
| **SC-03** | ROB-01 损坏包短路 | ROB-01 | 所有检测 |
| **SC-04** | R-DEP-01 致命错误短路 | R-DEP-01 | 后续所有批次 |
| **SC-05** | R-DEP-01 缺失短路 | R-DEP-01 | 后续所有批次 |

**验证方式**：`get_short_circuit_batches()` 返回的短路批次列表非空。

### 1.2 增量校验用例（3 项）

| 用例 | 描述 | 预期模式 | 命中缓存 |
|------|------|---------|---------|
| **INC-01** | 首审 → 二审无变更 | FULL → CACHED | ✅ HIT |
| **INC-02** | 二审变更后增量重算 | FULL → INCREMENTAL | ❌ MISS |
| **INC-03** | 无上一版时全量审计 | FULL | ❌ MISS |

**验证方式**：`IncrementalAuditor.audit()` 返回的 `(result, hit, mode)` 三元组。

### 1.3 LRU 缓存用例

| 用例 | 描述 | 预期 |
|------|------|------|
| **LRU-01** | 缓存命中 | `stats.cache_hits > 0` |
| **LRU-02** | 缓存未命中（不同签名） | `stats.cache_misses > 0` |
| **LRU-03** | LRU 淘汰（超过 1000 上限） | 旧签名被淘汰 |

### 1.4 状态漂移检测用例

| 用例 | 描述 | 预期 |
|------|------|------|
| **DRIFT-01** | BLOCKED→RECOVERED→BLOCKED→RECOVERED | 漂移计数 = 2 |
| **DRIFT-02** | RECOVERED→BLOCKED（曾到达过） | 漂移计数 = 1 |
| **DRIFT-03** | 从未到达 RECOVERED | 漂移计数 = 0 |

### 1.5 ⚡ 判定等价性自证（核心用例，2 项）

| 用例 | 描述 | 预期 |
|------|------|------|
| **EQUIV-01** | v3 短路 vs v2_plus 全量（50 用例 × verdict） | **完全一致** |
| **EQUIV-02** | v3 短路 vs v2_plus 全量（50 用例 × 关键字段） | **完全一致** |

**验证方式**：`test_verdict_equivalence()` 逐用例对比 `verdict` + `gate_g06_verdict` +
`gate_g09_verdict` + `dep_rollback_count` + `perf_guard_triggered` 等关键输出字段。

**这是 v3 最重要的用例**：它证明了**短路优化不改变审计判定**——所有短路都发生在
判定已确定之后（非阻断检测被跳过，但阻断项的判定结果不受影响）。

---

## 2. WAL 事件存储新增用例（9 项）

### 2.1 WAL 存储用例矩阵

| 用例 | 描述 | 关键指标 | 结果 |
|------|------|---------|------|
| **WAL-01** | WAL 模式生效 | `journal_mode=wal` | ✅ |
| **WAL-02** | 读写并发 | 200 写 0 错，读 7 次不阻塞 | ✅ |
| **WAL-03** | UPSERT 去重 | 80 提交 → 20 唯一，dedup_count=[4,4,4,4,4] | ✅ |
| **WAL-04** | 崩溃恢复 | 100→100 条，SQLite 自动恢复 | ✅ |
| **WAL-05** | JSONL→WAL 自动切换 | 阈值 30 触发，50 条迁移，元数据记录 | ✅ |
| **WAL-06** | 6 维索引检索 | 7 维命中 + 不存在返回 0 | ✅ |
| **WAL-07** | 高容量写入 | 20000 事件完整，退化 1.11x | ✅ |
| **WAL-08** | checkpoint | `checkpointed=True, log_frames=9` | ✅ |
| **WAL-09** | 崩溃后去重保持 | count=10（幂等去重保持） | ✅ |

### 2.2 WAL 与 JSONL 对比用例

| 场景 | WAL 退化 | JSONL 退化 | 结论 |
|------|---------|-----------|------|
| 5000 事件 | 1.21x | 5.07x | WAL 恒定 |
| 20000 事件 | **1.11x** | **23.72x** | WAL 胜出 |

---

## 3. 灰度阶梯仿真用例（10 项）

### 3.1 灰度阶梯用例矩阵

| 用例 | 描述 | 结果 |
|------|------|------|
| **GRAY-01** | DEP 未就绪 G1~G5 全部不准入 | ✅ DEP_001 阻断 |
| **GRAY-02** | DEP 就绪 G1~G5 全部准入 ADVANCE | ✅ 全链路跑通 |
| **GRAY-03** | 5 类故障注入全部触发回滚 | ✅ F1~F5 |
| **GRAY-04** | F1 自动回滚，F3/F4/F5 需人工确认 | ✅ 判定矩阵 |
| **GRAY-05** | 阈值边界判定（HIGH 超限不准入） | ✅ |
| **GRAY-06** | 非零率阈值逐级收紧 | ✅ [0.95→0.995] |
| **GRAY-07** | p95 阈值逐级收紧 | ✅ [50→15ms] |
| **GRAY-08** | 品种数递增 [0,1,7,28,42,56] | ✅ G5=全量 |
| **GRAY-09** | 回滚条件 F1~F5 完整 | ✅ |
| **GRAY-10** | DEP 未就绪时仅 G0 可推进 | ✅ |

---

## 4. 本轮开发修复的缺陷（6 类）

| # | 模块 | 缺陷 | 症状 | 根因 |
|---|------|------|------|------|
| 1 | WAL | **INSERT 占位符错位** | `19 values for 18 columns`，全部写入失败 count=0 | VALUES 占位符 17 个应为 16 个（2 个字面量占 2 位） |
| 2 | WAL | **`force_wal` 逻辑反转** | 自动切换永不触发 | `self.switched = not force_wal` 应为 `bool(force_wal)` |
| 3 | WAL | **夹具随机破坏幂等** | 崩溃恢复后去重失效 count=20 | `make_event` 的 `rule_key=random.choice` 导致 event_id 不稳定 |
| 4 | WAL | `set_meta` 未 commit | 切换元数据为 None | 缺 `commit()` |
| 5 | WAL | `executescript` 隐式提交 | 事务状态异常 | 多语句 DDL 在 WAL 模式下需分阶段执行 |
| 6 | 灰度 | `observe_hours` KeyError | HOLD 状态访问不存在的键 | 分支判断不全 |

> **教训**：6 个缺陷中 3 个是**静默失败**（代码不报错但结果错误），只有 self-test 的
> 精确断言才能抓住。这是连续第四轮（v2→v2_plus→v3→WAL）由自回归发现的真实缺陷。

---

## 5. 三脚本自检汇总

| 脚本 | 版本 | 用例数 | self-test | 结论 |
|------|------|--------|-----------|------|
| `evidence_auditor_v3.py` | v3.0.0 | 50 + 短路 5 + 增量 3 + LRU + 漂移 + 等价性 | ✅ | SELF-TEST PASSED |
| `event_store_wal_v2.py` | v2.0.0-wal | 9 | ✅ | SELF-TEST PASSED |
| `gray_stair_sim.py` | v1.0.0 | 10 | ✅ | SELF-TEST PASSED |
| `evidence_auditor_v2_plus.py` | v2.1.0-plus | 42 + 11 + 3 | ✅ | SELF-TEST PASSED（回归） |
| `evidence_auditor_v2.py` | v2.0.0 | 23 + 11 | ✅ | SELF-TEST PASSED（回归） |

---

## 6. 状态标记

| 标记 | 值 | 说明 |
|------|-----|------|
| **HERMES_AUDIT_CASE_LIBRARY_V3_ARCED** | **TRUE** | CASE-LIB v3.0，79 项，三脚本自回归全 PASS |
| HERMES_AUDIT_CASE_LIBRARY_V2_1_PLUS_ARCED | TRUE | v2.1-plus 保持 |
| HERMES_AUDIT_CASE_LIBRARY_V2_ARCED | TRUE | v2.0 保持 |
| HERMES_EVENT_STORE_WAL_V2_DONE | TRUE | WAL 9 项 PASS |
| HERMES_GRAY_STAIR_SIM_DONE | TRUE | 灰度 10 项 PASS |

---

## 7. 自回归历史（四轮）

| 轮次 | 载体 | 发现的真实缺陷 | 教训 |
|------|------|--------------|------|
| v2 | `evidence_auditor_v2.py` | 5 项（R-DEP-01/R-DATA-01/DRIFT/R-SCHED-02/状态机） | 自回归价值首次确立 |
| v2_plus | `evidence_auditor_v2_plus.py` | 4 项（抖动检测语义/变量遮蔽/夹具期望/异常逃逸） | 抖动检测语义错误最隐蔽 |
| v3 | `evidence_auditor_v3.py` | 1 项（增量断言写反） | 短路不改变判定=等价性自证 |
| WAL | `event_store_wal_v2.py` | 6 项（占位符/逻辑反转/夹具随机/未commit/executescript/KeyError） | 静默失败必须靠精确断言 |

**四轮累计发现 16 项真实缺陷**，全部由自回归抓到，**无一由人工审查发现**。
