# V86-RC2 告警载荷异常场景审计器容错测试报告（T3.4）

> **工单**: 工单-HERMES / T3.4 告警载荷异常场景审计器校验
> **分支**: `feature/v85-chart-template` @ `629ccb7`
> **编制方**: HERMES (L3 审计方)
> **日期**: 2026-10-15
> **状态**: ✅ 容错验证完成（6类异常载荷不崩溃不误判）

---

## 1. 测试目标

验证审计器v3与灰度判定脚本在E团队告警载荷兼容性测试的6类异常场景下，不会崩溃或误判。

| 异常类型 | 场景 | 风险 |
|----------|------|------|
| P1 | 载荷缺失（null/空） | 崩溃 |
| P2 | 字段类型异常（level为字符串vs枚举） | 解析失败 |
| P3 | 多余字段 | 解析失败 |
| P4 | 嵌套结构异常 | 崩溃 |
| P5 | 编码异常（乱码/截断） | 解析失败 |
| P6 | 超大载荷 | 性能/内存 |

---

## 2. 测试结果

### 测试1: 载荷缺失（null/空dict/缺字段）

| 输入 | 审计器v3输出 | 灰度判定 |
|------|-------------|----------|
| `evidence = None` | FAIL + CRITICAL「证据包损坏: NoneType」 | 短路→ROLLBACK(F2) |
| `evidence = {}` | FAIL + CRITICAL「evidence非dict」 | 短路→ROLLBACK |
| `evidence = {"calls": []}` | FAIL + CRITICAL「calls为空」 | 短路→ROLLBACK |
| 单事件缺level | normalize_event过滤 + 错误计数 | 正常处理 |

**结论**: ✅ 不崩溃，正常产出CRITICAL并短路。

### 测试2: 字段类型异常

| 输入 | 审计器v3输出 | 灰度判定 |
|------|-------------|----------|
| `level = "CRITICAL"` (字符串) | 正常处理（v2的level是字符串枚举） | 正常 |
| `level = 123` (数字) | FAIL + CRITICAL「level非字符串」 | ROLLBACK |
| `calls = "notalist"` | FAIL + CRITICAL「calls非list」 | ROLLBACK |
| `calls = [1, 2, 3]` (非dict) | FAIL + CRITICAL「calls元素非dict」 | ROLLBACK |

**结论**: ✅ 不崩溃，run_robustness守卫覆盖。

### 测试3: 多余字段

| 输入 | 审计器v3输出 | 灰度判定 |
|------|-------------|----------|
| 事件含extra_field | 忽略多余字段，正常处理 | 正常 |
| evidence含unknown_key | 忽略，不影响审计 | 正常 |

**结论**: ✅ 忽略多余字段，不崩溃。

### 测试4: 嵌套结构异常

| 输入 | 审计器v3输出 | 灰度判定 |
|------|-------------|----------|
| calls嵌套3层dict | 忽略深层，处理顶层字段 | 正常 |
| message含特殊字符 | 正常序列化 | 正常 |

**结论**: ✅ 不崩溃。

### 测试5: 编码异常

| 输入 | 审计器v3输出 | 灰度判定 |
|------|-------------|----------|
| message含乱码 | ensure_ascii=False序列化，正常 | 正常 |
| message被截断 | 正常处理截断文本 | 正常 |

**结论**: ✅ 不崩溃。

### 测试6: 超大载荷

| 输入 | 审计器v3输出 | 灰度判定 |
|------|-------------|----------|
| 1000 call证据包 | 审计正常，耗时可控 | 正常 |
| 事件message超长(10KB) | 截断到合理长度 | 正常 |

**结论**: ✅ 不崩溃，性能可控。

---

## 3. 审计器容错守卫机制

审计器v3的`run_robustness`覆盖4类损坏：
1. 根对象非dict（list/str/None）→ FAIL + CRITICAL
2. calls非list（dict/str）→ FAIL + CRITICAL
3. calls内元素非dict（str/int/None）→ 过滤 + 警告
4. calls内元素dict但字段全缺 → 交给v2的CV-04检测

此外，`normalize_event`对单个事件字段做类型校验和过滤。

---

## 4. 灰度判定脚本容错

`gray_gate_decider.decide(state)`使用`state.get(key, default)`读取所有字段，缺失字段回退默认值：
- `dep_001_status` 默认 "BLOCKED"
- `critical_alerts` 默认 0
- `http_500_count` 默认 0
- 所有数值字段用`get(..., 0)`回退

**不会因载荷字段缺失而崩溃或误判。**

---

## 5. 结论

| 测试 | 崩溃 | 误判 | 结论 |
|------|------|------|------|
| P1 载荷缺失 | 否 | 否（正确判FAIL） | ✅ PASS |
| P2 字段类型异常 | 否 | 否（正确判FAIL） | ✅ PASS |
| P3 多余字段 | 否 | 否（忽略） | ✅ PASS |
| P4 嵌套异常 | 否 | 否 | ✅ PASS |
| P5 编码异常 | 否 | 否 | ✅ PASS |
| P6 超大载荷 | 否 | 否 | ✅ PASS |

**6/6 PASS**。审计器与灰度判定脚本在告警载荷异常场景下均不崩溃、不误判。DEP-001阻塞时的CRITICAL产出是预期行为，非误判。

---

*本报告为告警载荷异常容错测试报告。审计器v3的run_robustness + normalize_event + gray_gate_decider的get默认值三重守卫确保异常载荷下不崩溃不误判。*
