# V86规则引擎运维巡检清单

> 任务: DSHB_V86_RULE_ENGINE_STRESS_TEST_AND_CI_PIPELINE_PROTOTYPE · T2.6
> 分支: feature/v85-chart-template
> 基线: commit:128275a (V86 P0规则原型)
> 引擎版本: v86.1-alpha-proto

---

## 一、巡检概览

### 1.1 巡检周期

| 巡检类型 | 频率 | 责任人 | 产出 |
|----------|------|--------|------|
| 日常巡检 | 每日1次 | 值班工程师 | 巡检报告 |
| 每周巡检 | 每周1次 | 高级工程师 | 周报 |
| 深度巡检 | 每月1次 | 技术负责人 | 月报 |
| 应急巡检 | 按需 | 值班工程师 | 应急报告 |

### 1.2 巡检范围

1. 引擎运行状态
2. 性能指标
3. 错误率与异常
4. 规则集完整性
5. 数据质量
6. CI流水线状态
7. 资源使用
8. 安全与合规

---

## 二、日常巡检清单 (每日)

### 2.1 引擎状态检查

| # | 检查项 | 检查方法 | 正常标准 | 异常处理 |
|---|--------|---------|---------|---------|
| 1 | 引擎进程存活 | `ps aux \| grep v86_rule` | 进程存活 | 重启引擎 |
| 2 | 引擎版本 | `python -c "import v86_p1_rule_prototype; print(v86_p1_rule_prototype.VERSION)"` | v86.1-alpha-proto | 检查版本一致性 |
| 3 | 规则加载数 | `engine.get_rule_count()` | 18 (6 P0 + 12 P1) | 检查规则集完整性 |
| 4 | 错误历史 | `len(engine.get_error_history())` | < 10 | 分析错误原因 |

### 2.2 性能指标检查

| # | 检查项 | 检查方法 | 正常标准 | 告警阈值 |
|---|--------|---------|---------|---------|
| 5 | 单Case延迟 | 抽样100次评估 | < 0.5 ms | > 1.0 ms |
| 6 | 批量吞吐 | 1000条评估 | > 5000 cases/sec | < 3000 cases/sec |
| 7 | p95延迟 | 1000条评估 | < 0.35 ms | > 0.50 ms |
| 8 | 内存占用 | `ps -o rss` | < 50 MB | > 100 MB |
| 9 | CPU使用率 | `top` / `taskmgr` | < 30% | > 60% |

### 2.3 错误率检查

| # | 检查项 | 检查方法 | 正常标准 | 告警阈值 |
|---|--------|---------|---------|---------|
| 10 | EMPTY_INDICATOR错误率 | 统计error_history | < 0.1% | > 1% |
| 11 | DATA_MISSING比例 | 统计评估结果 | < 5% | > 10% |
| 12 | INTERNAL_ERROR | 统计error_history | 0 | > 0 |
| 13 | 超长文本拒绝 | 统计error_history | < 0.01% | > 0.1% |

### 2.4 CI流水线状态

| # | 检查项 | 检查方法 | 正常标准 | 异常处理 |
|---|--------|---------|---------|---------|
| 14 | 最近CI状态 | 检查ci_report.json | PASS | 分析阻断原因 |
| 15 | 门禁通过率 | 检查gate_checks | 10/10 PASS | 修复阻断门禁 |
| 16 | CI耗时 | 检查duration_ms | < 10000 ms | 检查性能回归 |

---

## 三、每周巡检清单

### 3.1 性能趋势分析

| # | 检查项 | 检查方法 | 正常标准 |
|---|--------|---------|---------|
| 17 | 周延迟趋势 | 对比本周vs上周延迟 | 变化 < 10% |
| 18 | 周吞吐趋势 | 对比本周vs上周吞吐 | 变化 < 10% |
| 19 | 周错误趋势 | 对比本周vs上周错误率 | 变化 < 20% |
| 20 | 周内存趋势 | 对比本周vs上周内存 | 变化 < 15% |

### 3.2 规则集完整性

| # | 检查项 | 检查方法 | 正常标准 |
|---|--------|---------|---------|
| 21 | 规则数量 | `engine.get_rule_count()` | 18 |
| 22 | P0规则 | `len(engine.get_p0_rules())` | 6 |
| 23 | P1规则 | `len(engine.get_p1_rules())` | 12 |
| 24 | 规则状态 | 所有规则status=ACTIVE | 全部ACTIVE |
| 25 | 规则冲突 | 检查重复rule_id | 0冲突 |

### 3.3 数据质量

| # | 检查项 | 检查方法 | 正常标准 |
|---|--------|---------|---------|
| 26 | PDF数据缺失率 | 统计DATA_MISSING比例 | < 5% |
| 27 | 别名映射冲突 | 运行AliasMappingValidator | 冲突数与上周持平 |
| 28 | 品种检测失败 | 统计VARIETY_DETECT_FAILED | 0 |
| 29 | 双向包含跳过率 | 统计bidirectional跳过 | < 5% |

### 3.4 CI流水线

| # | 检查项 | 检查方法 | 正常标准 |
|---|--------|---------|---------|
| 30 | 周CI通过率 | 检查7天CI报告 | > 90% |
| 31 | 门禁阻断次数 | 检查gate_checks | < 3次 |
| 32 | 性能回归 | 对比本周vs上周性能 | 无回归 |

---

## 四、深度巡检清单 (每月)

### 4.1 性能基准测试

| # | 检查项 | 检查方法 | 正常标准 |
|---|--------|---------|---------|
| 33 | 单Case延迟 | 运行100次单Case测试 | avg < 0.5 ms |
| 34 | 批量吞吐 | 运行5000条批量测试 | > 5000 cases/sec |
| 35 | 并发性能 | 运行4线程并发测试 | > 4000 cases/sec |
| 36 | 超长文本 | 运行超长文本测试 | p95 < 25 ms |
| 37 | 内存泄漏 | 运行10000次评估后检查内存 | 增长 < 10 MB |

### 4.2 规则引擎压力测试

| # | 检查项 | 检查方法 | 正常标准 |
|---|--------|---------|---------|
| 38 | 全量评估 | 488条模板全量评估 | < 100 ms |
| 39 | 回归测试 | 运行完整回归测试套件 | 0 FAIL |
| 40 | 容错测试 | 运行完整容错测试 | 100% PASS |
| 41 | 别名校验 | 运行完整别名校验 | 冲突数可控 |

### 4.3 数据一致性

| # | 检查项 | 检查方法 | 正常标准 |
|---|--------|---------|---------|
| 42 | V85/V86对比 | 运行v85_v86_rule_compare.py | 0回归 |
| 43 | P0拦截率 | 统计P0拦截率 | >= 88.2% |
| 44 | FP数量 | 统计FP数量 | 0 |
| 45 | 边界测试 | 运行边界测试 | 100% PASS |

### 4.4 安全与合规

| # | 检查项 | 检查方法 | 正常标准 |
|---|--------|---------|---------|
| 46 | zhiji API调用 | 检查日志 | 0调用 |
| 47 | V85文件修改 | git diff检查V85文件 | 0修改 |
| 48 | 代码权限 | 检查文件权限 | 只读 |
| 49 | 数据泄露 | 检查日志输出 | 无敏感信息 |

---

## 五、告警阈值

### 5.1 P0级告警 (立即处理)

| 告警名 | 条件 | 处理方式 |
|--------|------|---------|
| ALARM_ENGINE_DOWN | 引擎进程不存活 | 立即重启引擎 |
| ALARM_INTERNAL_ERROR | INTERNAL_ERROR > 0 | 分析error_history，修复bug |
| ALARM_GATE_BLOCKED | CI门禁阻断 | 分析阻断原因，修复问题 |
| ALARM_REGRESSION | 回归测试失败 | 回滚或修复规则 |
| ALARM_FP_DETECTED | FP > 0 | 分析FP原因，修复规则 |

### 5.2 P1级告警 (当日处理)

| 告警名 | 条件 | 处理方式 |
|--------|------|---------|
| WARN_LATENCY_HIGH | 单Case延迟 > 1.0 ms | 检查性能瓶颈 |
| WARN_THROUGHPUT_LOW | 吞吐 < 3000 cases/sec | 检查系统负载 |
| WARN_ERROR_RATE_HIGH | 错误率 > 1% | 分析错误原因 |
| WARN_MEMORY_HIGH | 内存 > 100 MB | 检查内存泄漏 |
| WARN_P0_RATE_DROP | P0拦截率 < 85% | 分析规则变更 |

### 5.3 P2级告警 (本周处理)

| 告警名 | 条件 | 处理方式 |
|--------|------|---------|
| INFO_PERF_DEGRADED | 性能下降 > 10% | 分析性能趋势 |
| INFO_ALIAS_CONFLICTS | 别名冲突数增加 | 审查别名映射 |
| INFO_DATA_MISSING_HIGH | DATA_MISSING > 10% | 检查PDF数据质量 |
| INFO_RULE_COUNT_CHANGED | 规则数量变化 | 检查规则集变更 |

---

## 六、常见故障排查

### 6.1 引擎无法启动

```bash
# 症状: 引擎进程启动后立即退出
# 排查步骤:
1. 检查Python版本: python --version  (需3.12)
2. 检查依赖: pip list | grep -E "dataclass|enum"
3. 检查文件权限: ls -la v86_p1_rule_prototype.py
4. 检查导入: python -c "from v86_p1_rule_prototype import V86P1RuleEngine"
5. 检查日志: 查看stderr输出

# 常见原因:
- Python版本不兼容
- 文件路径错误
- 权限不足
- 依赖缺失
```

### 6.2 评估结果异常

```bash
# 症状: 评估结果与预期不符
# 排查步骤:
1. 检查规则集: engine.get_all_rule_ids()
2. 检查规则状态: 所有规则status应为ACTIVE
3. 检查规则pattern: 查看规则的left/right patterns
4. 检查品种检测: engine._detect_variety(indicator)
5. 检查双向包含: 查看engine.evaluate()返回的triggered_rules
6. 检查DATA_MISSING: matched_name是否为空/N/A

# 常见原因:
- 规则未加载 (is_v86_p0/is_v86_p1标记错误)
- 规则status不是ACTIVE (Enum类型不匹配)
- 品种检测失败
- 双向包含检测误跳过
```

### 6.3 性能下降

```bash
# 症状: 延迟增加或吞吐下降
# 排查步骤:
1. 检查系统负载: top / taskmgr
2. 检查CPU使用率: 是否接近100%
3. 检查内存使用: 是否内存不足
4. 检查规则数量: 是否新增了规则
5. 检查输入数据: 是否有超长文本
6. 运行基准测试: python ci_rule_verify_pipeline.py --performance

# 常见原因:
- 系统负载过高
- 规则数量增加 (每条规则增加~0.002ms)
- 输入文本过长 (> 1000字符)
- Python GC压力增大
```

### 6.4 CI门禁阻断

```bash
# 症状: CI流水线返回BLOCKED
# 排查步骤:
1. 查看ci_result.txt: 找到阻断的门禁
2. GATE-002 P0拦截率: 检查P0测试用例是否通过
3. GATE-003 FP: 检查是否有误报
4. GATE-004 回归: 检查是否有回归
5. GATE-006/007/008 性能: 检查性能指标
6. GATE-009 容错: 检查容错测试

# 常见原因:
- 规则变更导致P0拦截率下降
- 新增规则引入FP
- 性能回归 (规则数量增加或代码变更)
- 容错测试失败 (输入验证逻辑变更)
```

### 6.5 别名映射冲突

```bash
# 症状: 别名校验报告冲突
# 排查步骤:
1. 查看冲突类型: CANONICAL_MISMATCH / VARIETY_MISMATCH / AMBIGUOUS_MAPPING
2. 查看冲突详情: alias_validator.validate()返回的conflict描述
3. 检查别名映射源: 查看原始别名映射文件
4. 检查规范名: 确认canonical是否正确

# 常见原因:
- 同一别名映射到不同规范名
- 同一别名的品种标签不一致
- 多个别名映射到同一规范名 (可能是正常的)
```

---

## 七、运维脚本

### 7.1 快速巡检脚本

```python
#!/usr/bin/env python3
"""快速巡检脚本 - 5秒完成基础检查"""

import sys, os, time
sys.path.insert(0, 'analysis/e2e_output/v86/dshb_rule_predev')
sys.path.insert(0, 'analysis/e2e_output/v86/dshb_rule_ci_stress')

from v86_p1_rule_prototype import V86P1RuleEngine, create_v86_p1_rules
from v86_p0_rule_prototype import create_v86_p0_rules

print("=" * 50)
print("V86规则引擎快速巡检")
print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 50)

# 1. 引擎初始化
try:
    engine = V86P1RuleEngine()
    engine._add_rules(create_v86_p0_rules())
    engine._add_rules(create_v86_p1_rules())
    print(f"[PASS] 引擎初始化成功")
    print(f"       版本: v86.1-alpha-proto")
    print(f"       规则数: {engine.get_rule_count()}")
except Exception as e:
    print(f"[FAIL] 引擎初始化失败: {e}")
    sys.exit(1)

# 2. 单Case评估
start = time.perf_counter_ns()
result = engine.evaluate("碳酸锂 三元523需求", "SMM: 碳酸锂现金生产利润")
elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000

if result["result"] == "BLOCKED" and result["blocked_by"] == "BL-009a":
    print(f"[PASS] 单Case评估: BLOCKED by BL-009a")
else:
    print(f"[FAIL] 单Case评估: 结果异常 {result['result']}")

print(f"       延迟: {elapsed_ms:.3f}ms")

# 3. 批量吞吐
import random
cases = []
for i in range(100):
    cases.append(("碳酸锂价格", "碳酸锂:价格:日度"))
    cases.append(("电解铜库存", "铜库存"))

start = time.perf_counter_ns()
for ind, mtd in cases:
    engine.evaluate(ind, mtd)
elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000

throughput = len(cases) / (elapsed_ms / 1000)
print(f"[{'PASS' if throughput > 5000 else 'WARN'}] 批量吞吐: {throughput:.0f} cases/sec")

# 4. 错误检查
errors = engine.get_error_history()
if len(errors) == 0:
    print(f"[PASS] 错误历史: 0错误")
else:
    print(f"[WARN] 错误历史: {len(errors)}错误")

# 5. 容错测试
result = engine.evaluate(None, "test")
if result["error_code"] == "EMPTY_INDICATOR":
    print(f"[PASS] 容错测试: 空输入正确拒绝")
else:
    print(f"[FAIL] 容错测试: 空输入处理异常")

print("=" * 50)
print("巡检完成")
```

### 7.2 性能基线检查

```python
#!/usr/bin/env python3
"""性能基线检查脚本"""

import sys, time, json
sys.path.insert(0, 'analysis/e2e_output/v86/dshb_rule_predev')
sys.path.insert(0, 'analysis/e2e_output/v86/dshb_rule_ci_stress')

from v86_p1_rule_prototype import V86P1RuleEngine, create_v86_p1_rules, PerformanceBenchmarkRunner
from v86_p0_rule_prototype import create_v86_p0_rules

engine = V86P1RuleEngine()
engine._add_rules(create_v86_p0_rules())
engine._add_rules(create_v86_p1_rules())

bench = PerformanceBenchmarkRunner(engine)
results = bench.run_stress_suite([
    {"name": "batch_1000_sequential", "count": 1000, "iterations": 1, "workers": 1},
])

r = results[0]["details"]
print(f"基准检查: batch_1000")
print(f"  吞吐: {r['cases_per_sec']} cases/sec")
print(f"  avg: {r['avg_ms_per_case']:.3f} ms")
print(f"  p50: {r['p50_ms']:.3f} ms")
print(f"  p95: {r['p95_ms']:.3f} ms")
print(f"  状态: {'PASS' if r['cases_per_sec'] > 5000 else 'FAIL'}")
```

---

## 八、巡检报告模板

### 8.1 日常巡检报告

```
============================================================
V86规则引擎日常巡检报告
日期: 2026-10-01
巡检人: [值班工程师]
============================================================

[引擎状态]
  版本: v86.1-alpha-proto
  规则数: 18 (6 P0 + 12 P1)
  错误历史: 0

[性能指标]
  单Case延迟: 0.14 ms (标准: < 0.5 ms)
  批量吞吐: 7000 cases/sec (标准: > 5000)
  p95延迟: 0.17 ms (标准: < 0.35 ms)
  内存: 22 MB (标准: < 50 MB)

[错误率]
  EMPTY_INDICATOR: 0%
  DATA_MISSING: 0%
  INTERNAL_ERROR: 0

[CI流水线]
  最近状态: PASS
  门禁: 10/10 PASS
  耗时: 287 ms

[结论]
  状态: 正常
  异常: 无
  建议: 无需操作

============================================================
```

### 8.2 异常巡检报告

```
============================================================
V86规则引擎异常巡检报告
日期: 2026-10-01
巡检人: [值班工程师]
异常ID: [INC-20261001-001]
============================================================

[异常描述]
  异常类型: CI门禁阻断
  异常时间: 2026-10-01 22:55:00
  异常级别: P0

[异常详情]
  阻断门禁: GATE-002 (P0拦截率)
  阈值: >= 88.2%
  实际: 66.7%
  原因: BL-009a规则未正确触发

[影响范围]
  受影响规则: BL-009a
  受影响模板: 3条
  影响程度: P0风险未拦截

[处理措施]
  1. 检查规则集: BL-009a规则已加载
  2. 检查规则状态: status=ACTIVE (Enum类型匹配)
  3. 检查pattern: left/right patterns正确
  4. 检查双向包含: 未误跳过
  5. 修复: Enum类型比较修复 (rule.status.value != "active")

[验证结果]
  P0拦截率: 66.7% → 100.0%
  CI门禁: BLOCKED → PASS

[结论]
  状态: 已解决
  根因: Enum类型不匹配导致规则被跳过
  建议: 增加Enum类型兼容性检查

============================================================
```

---

## 九、附录

### 9.1 关键命令速查

```bash
# 查看引擎版本
python -c "from v86_p1_rule_prototype import VERSION; print(VERSION)"

# 运行自测
python v86_p1_rule_prototype.py --self-test

# 运行CI流水线
python ci_rule_verify_pipeline.py --full

# 运行基准测试
python ci_rule_verify_pipeline.py --performance

# 查看规则列表
python v86_p1_rule_prototype.py --list-rules

# 单Case评估
python v86_p1_rule_prototype.py --eval "碳酸锂 三元523需求" "SMM: 碳酸锂现金生产利润"

# 别名验证
python v86_p1_rule_prototype.py --alias-validate alias_map.json
```

### 9.2 文件路径

| 文件 | 路径 |
|------|------|
| P1规则原型 | analysis/e2e_output/v86/dshb_rule_ci_stress/v86_p1_rule_prototype.py |
| P1测试用例 | analysis/e2e_output/v86/dshb_rule_ci_stress/v86_p1_rule_test_suite.json |
| CI流水线 | analysis/e2e_output/v86/dshb_rule_ci_stress/ci_rule_verify_pipeline.py |
| CI报告 | analysis/e2e_output/v86/dshb_rule_ci_stress/ci_report.json |
| 性能报告 | analysis/e2e_output/v86/dshb_rule_ci_stress/v86_rule_performance_report.md |
| 容错文档 | analysis/e2e_output/v86/dshb_rule_ci_stress/v86_rule_fault_tolerance.md |
| P0规则原型 | analysis/e2e_output/v86/dshb_rule_predev/v86_p0_rule_prototype.py |
| 对比脚本 | analysis/e2e_output/v86/dshb_rule_predev/v85_v86_rule_compare.py |

### 9.3 告警阈值汇总

| 指标 | P2(信息) | P1(警告) | P0(严重) |
|------|---------|---------|---------|
| 单Case延迟 | > 0.30 ms | > 0.50 ms | > 1.00 ms |
| 批量吞吐 | < 6000 cps | < 5000 cps | < 3000 cps |
| p95延迟 | > 0.20 ms | > 0.35 ms | > 0.50 ms |
| 内存 | > 30 MB | > 50 MB | > 100 MB |
| 错误率 | > 0.5% | > 1% | > 5% |
| P0拦截率 | < 90% | < 85% | < 80% |
| CI耗时 | > 5000 ms | > 10000 ms | > 30000 ms |
