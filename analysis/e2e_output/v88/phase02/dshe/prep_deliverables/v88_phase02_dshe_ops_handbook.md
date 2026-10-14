# V88 Phase02 — 渲染运维排查手册

**TASK_ID:** V88_PHASE02_DSHE_POST_DEPLOY_PREP
**AGENT:** DSHE
**BRANCH:** feature/v88-g1
**DATE:** 2028-05-18
**VERSION:** v1.0

---

## 1. 概述

本手册记录 V88 Phase02 渲染层常见报错、降级触发场景及排查步骤。
基于 `node_binding_engine.py` 引擎 (`scripts/node_binding_engine.py`)，
覆盖 `NodeBindingEngine` 类的加载、校验、绑定解析、渲染、回退全流程。

---

## 2. 快速诊断流程

```
渲染异常
    │
    ├─ 1. 检查图表是否存在 → engine.chart_index.get(chart_id)
    │     └─ None → 图表ID错误 → 检查YAML配置
    │
    ├─ 2. 检查数据状态 → cb.data_status
    │     ├─ "matchable" → 真实数据路径
    │     ├─ "pending_data" → 模拟/占位路径
    │     └─ "deprecated" → 已弃用 → 不应渲染
    │
    ├─ 3. 检查绑定解析 → cb.resolved_node / cb.resolved_commodity
    │     └─ 含"error" → 节点/品种未注册 → 检查tree_config.json
    │
    ├─ 4. 检查渲染数据 → render_result["render_data"]
    │     ├─ 空列表 → 无数据 → 触发占位符
    │     ├─ 有points → 正常
    │     └─ 字段缺失 → 数据格式问题
    │
    └─ 5. 检查source → "real" / "simulated" / "placeholder"
          └─ 非"real" → 已触发降级 → 检查数据源健康
```

---

## 3. 常见报错与排查

### 3.1 ERROR: chart not found

**现象:** `{"error": "chart <id> not found"}`

**原因:**
- 图表ID拼写错误
- 图表未在 `framework_tree_meta_chart.yaml` 中定义
- 引擎未正确加载 (`engine.load()` 返回 False)

**排查步骤:**
```python
# Step 1: 检查引擎加载
engine = NodeBindingEngine(repo_root=REPO_ROOT)
ok, msg = engine.load()
print(f"Load: {ok}, {msg}")

# Step 2: 检查图表索引
print(f"Total charts: {len(engine.charts)}")
print(f"Chart in index: {chart_id in engine.chart_index}")

# Step 3: 检查YAML文件
print(f"YAML path: {engine.yaml_path}")
print(f"File exists: {os.path.exists(engine.yaml_path)}")
```

**修复:**
- 修正图表ID拼写
- 在YAML中添加缺失的图表定义
- 检查YAML文件路径和权限

---

### 3.2 ERROR: 节点/品种未注册

**现象:** `cb.resolved_node` 或 `cb.resolved_commodity` 包含 `{"error": ...}`

**可能原因:**
- `tree_node_id` 在 `data/tree_config.json` 中不存在
- `commodity` 在 `tree_config.json` 的 commodities 列表中不存在

**排查步骤:**
```python
# Step 1: 检查节点索引
print(f"Node index keys: {list(engine.node_index.keys())}")
print(f"Node exists: {tree_node_id in engine.node_index}")

# Step 2: 检查品种索引
print(f"Commodity index keys: {list(engine.commodity_index.keys())}")
print(f"Commodity exists: {commodity in engine.commodity_index}")

# Step 3: 检查tree_config.json
with open(tree_config_path) as f:
    tc = json.load(f)
print(f"Categories: {len(tc['categories'])}")
print(f"Commodities: {len(tc['commodities'])}")
```

**修复:**
- 在 `tree_config.json` 中添加缺失节点或品种
- 检查图表绑定关系是否指向正确节点

---

### 3.3 ERROR: 渲染数据为空

**现象:** `render_result["render_data"]` 为空列表或无points

**可能原因:**
- 真实数据源 (api_cache.db) 不可用
- 模拟数据生成失败
- 指标ID不在 `SIMULATED_DATA_SEEDS` 中且派生种子失败

**排查步骤:**
```python
# Step 1: 检查数据源
from node_binding_engine import SIMULATED_DATA_SEEDS
ind_id = cb.indicators[0].get("indicator_id", "")
print(f"Seed exists: {ind_id in SIMULATED_DATA_SEEDS}")

# Step 2: 检查真实数据
db_path = os.path.join(engine.repo_root, "scripts", "api_cache.db")
print(f"DB exists: {os.path.exists(db_path)}")

# Step 3: 手动测试模拟数据生成
sim = engine._generate_simulated_data(cb)
print(f"Sim data: {len(sim)} series, points: {len(sim[0]['points']) if sim else 0}")

# Step 4: 手动测试占位符生成
ph = engine._generate_placeholder(cb)
print(f"Placeholder: {ph}")
```

**修复:**
- 确保 `api_cache.db` 存在且可读
- 在 `SIMULATED_DATA_SEEDS` 中添加缺失指标的种子参数
- 检查指标ID是否拼写正确

---

### 3.4 WARN: business_description 不一致

**现象:** `ValidationResult` 中 severity=WARN, rule_id=`auto_inherit_description`

**原因:**
- 图表的 `business_description` 与节点定义的 `{name}({q})` 不一致
- 通常是图表手动填写了描述而节点切换后未自动继承

**排查步骤:**
```python
# Step 1: 检查预期描述
node = engine.node_index[cb.tree_node_id]
expected = f"{node['name']}({node['q']})"
print(f"Expected: {expected}")
print(f"Actual:   {cb.business_description}")

# Step 2: 重新解析绑定
engine.resolve_binding(cb)
print(f"After resolve: {cb.business_description}")
```

**说明:** WARN级别不阻断渲染，引擎会自动继承节点描述。

---

### 3.5 ERROR: 并发渲染异常

**现象:** 多线程渲染时出现 `Thread 0x... raised` 或超时

**可能原因:**
- 多个线程创建新引擎实例 (加载开销过大)
- 线程间共享 `ChartBinding` 对象且未加锁
- 指标挂载/卸载操作与渲染并发

**排查步骤:**
```python
import threading

# 正确做法: 共享引擎实例, 仅测量渲染时延
engine = make_engine()  # 主线程加载一次

def render_task(cid):
    r = engine.render_with_fallback(cid)  # 渲染操作线程安全
    return r

# 检查引擎是否线程安全
# NodeBindingEngine 的 render_with_fallback 仅读取 cb 对象
# 节点切换/指标挂载等非只读操作需要加锁
```

**修复:**
- 使用共享引擎实例 (`make_engine()` 仅在 setUp 调用一次)
- 并发渲染时仅调用 `render_with_fallback` (只读操作)
- 节点切换和指标挂载操作需要 `threading.Lock` 保护

---

### 3.6 ERROR: fallback_trigger_rate 超阈值

**现象:** 监控大盘告警 `ALERT-005: fallback_trigger_rate_pct > 30%`

**原因:**
- 大量图表触发降级 (matchable→simulated 或 pending_data→simulated)
- 真实数据源 (api_cache.db) 不可用或数据缺失
- DSHB pending指标未就绪 (6项指标供给中)

**排查步骤:**
```python
# Step 1: 检查渲染数据源分布
results = engine.render_all(use_simulated=True)
source_counts = Counter()
for r in results.get("matchable", []) + results.get("pending_data", []):
    source_counts[r.get("source", "unknown")] += 1
print(f"Source distribution: {dict(source_counts)}")

# Step 2: 计算fallback率
fallback_count = source_counts.get("simulated", 0) + source_counts.get("placeholder", 0)
total = sum(source_counts.values())
rate = fallback_count / total * 100 if total else 0
print(f"Fallback rate: {rate:.1f}%")

# Step 3: 检查真实数据可用性
db_path = os.path.join(engine.repo_root, "scripts", "api_cache.db")
if os.path.exists(db_path):
    print(f"api_cache.db exists: {os.path.getsize(db_path)} bytes")
else:
    print("api_cache.db NOT FOUND - all renders fallback to simulated")
```

**修复:**
- 确保 `api_cache.db` 已刷新数据 (`scripts/refresh_cache.py`)
- 等待DSHB pending指标长稳完成后真实数据到达
- 对于 pending_data 图表，fallback 是预期行为

---

### 3.7 ERROR: 数据点字段缺失

**现象:** `KeyError: 'date'` 或 `KeyError: 'value'` 在渲染数据点中

**原因:**
- 数据格式不符合预期结构
- 外部数据源返回了非标准格式
- api_cache.db 中的数据已损坏

**排查步骤:**
```python
# Step 1: 检查数据点结构
for series in render_result["render_data"]:
    for point in series.get("points", []):
        required = ["date", "value"]
        missing = [f for f in required if f not in point]
        if missing:
            print(f"Missing {missing} in point: {point}")

# Step 2: 检查数据点数量
print(f"Total series: {len(render_result['render_data'])}")
for s in render_result["render_data"]:
    print(f"  Series '{s.get('name', '?')}': {len(s.get('points', []))} points")
```

**修复:**
- 清理损坏的 api_cache.db 数据
- 重新执行 `scripts/refresh_cache.py` 刷新缓存
- 检查数据源API返回格式

---

## 4. 降级触发排查

### 4.1 三级降级链路

```
Step 1: 尝试真实数据 (api_cache.db)
    │
    ├─ 成功 → source="real" → 正常渲染
    │
    └─ 失败 → Step 2
            │
Step 2: 尝试模拟数据 (SIMULATED_DATA_SEEDS)
    │
    ├─ 成功 → source="simulated" → 降级渲染
    │
    └─ 失败 → Step 3
            │
Step 3: 生成占位符
    │
    └─ 成功 → source="placeholder" → 占位符渲染
```

### 4.2 降级触发排查表

| 降级层级 | 触发条件 | 预期行为 | 排查方法 |
|:--------:|----------|----------|----------|
| real→simulated | api_cache.db不存在或指标无数据 | 自动生成120天模拟数据 | `os.path.exists(api_cache.db)` |
| simulated→placeholder | 指标无种子且派生失败 | 生成占位符 | `ind_id in SIMULATED_DATA_SEEDS` |
| pending→simulated | data_status=pending_data + use_simulated=True | 模拟数据渲染 | `cb.data_status == "pending_data"` |
| pending→placeholder | data_status=pending_data + use_simulated=False | 占位符渲染 | `cb.data_status == "pending_data"` |

### 4.3 降级链路验证命令

```python
# 验证全量101图表降级链路
results = engine.verify_pending_render_chain()
print(f"Pending: {results['total_pending']}")
print(f"Binding resolved: {results['binding_resolved']}")
print(f"Simulated OK: {results['simulated_data_ok']}")
print(f"Placeholder OK: {results['placeholder_ok']}")
print(f"Fallback OK: {results['fallback_ok']}")
print(f"Errors: {results['errors']}")
print(f"Success rate: {results['success_rate']}%")

# 全量渲染回退
for cb in engine.charts:
    r = engine.render_with_fallback(cb.chart_id)
    if not r.get("renderable"):
        print(f"FAIL: {cb.chart_id} -> {r.get('error', 'not renderable')}")
```

---

## 5. 性能问题排查

### 5.1 渲染时延过高

**排查步骤:**
```python
import time
import statistics

timings = []
for cb in engine.charts:
    t0 = time.time()
    r = engine.render_with_fallback(cb.chart_id)
    elapsed = time.time() - t0
    timings.append(elapsed)

avg = statistics.mean(timings)
p99 = statistics.quantiles(timings, n=100)[98] if len(timings) > 1 else timings[0]
print(f"Avg: {avg*1000:.2f}ms, P99: {p99*1000:.2f}ms")

# 定位慢图表
slow = [(t, cb.chart_id) for t, cb in zip(timings, engine.charts) if t > 0.1]
for t, cid in sorted(slow, reverse=True):
    print(f"  SLOW: {cid} = {t*1000:.2f}ms")
```

**阈值参考:**

| 指标 | 正常 | 警告 | 严重 |
|------|:----:|:----:|:----:|
| 单图表渲染 | <10ms | <50ms | >100ms |
| P99 (顺序) | <100ms | <300ms | >500ms |
| P99 (101并发) | <200ms | <400ms | >500ms |
| 引擎加载 | <100ms | <500ms | >1s |

### 5.2 并发性能退化

**排查步骤:**
```python
import threading

def concurrent_test(num_threads):
    chart_ids = [cb.chart_id for cb in engine.charts]
    timings = []
    lock = threading.Lock()

    def task(cid):
        t0 = time.time()
        r = engine.render_with_fallback(cid)
        elapsed = time.time() - t0
        with lock:
            timings.append(elapsed)

    threads = [threading.Thread(target=task, args=(chart_ids[i % len(chart_ids)],))
               for i in range(num_threads)]
    for t in threads: t.start()
    for t in threads: t.join()

    p99 = statistics.quantiles(timings, n=100)[98]
    return p99 * 1000
```

---

## 6. 运维操作速查

### 6.1 常用诊断命令

```python
# 1. 引擎自检
from node_binding_engine import NodeBindingEngine
engine = NodeBindingEngine(repo_root=REPO_ROOT)
ok, msg = engine.load()
engine.validate(strict=False)
engine.resolve_all()
stats = engine.get_stats()
print(stats)

# 2. 检查pending图表
pending = engine.get_pending_charts()
print(f"Pending charts: {len(pending)}")
for cb in pending:
    print(f"  {cb.chart_id} ({cb.commodity}/{cb.tree_node_id})")

# 3. 检查图表类型分布
from collections import Counter
types = Counter(cb.chart_type for cb in engine.charts)
print(dict(types))

# 4. 检查节点分布
nodes = Counter(cb.tree_node_id for cb in engine.charts)
print(dict(nodes))

# 5. 检查品种分布
comms = Counter(cb.commodity for cb in engine.charts)
print(dict(comms))
```

### 6.2 紧急降级操作

```python
# 场景: 真实数据源完全不可用
# 操作: 全量切换到模拟数据渲染
engine = make_engine()
for cb in engine.charts:
    if cb.data_status == "matchable":
        # 强制使用模拟数据
        sim = engine._generate_simulated_data(cb)
        # 正常渲染会先尝试真实数据，然后自动fallback
        r = engine.render_with_fallback(cb.chart_id)
        # r["source"] 应为 "simulated"

# 场景: 全量渲染
results = engine.render_all(use_simulated=True)
print(f"Matchable: {len(results['matchable'])}")
print(f"Pending: {len(results['pending_data'])}")
print(f"Deprecated: {len(results['deprecated'])}")
print(f"Errors: {len(results['errors'])}")
```

### 6.3 数据刷新检查

```python
# 检查 api_cache.db 状态
import os
import sqlite3

db_path = os.path.join(engine.repo_root, "scripts", "api_cache.db")
if not os.path.exists(db_path):
    print("api_cache.db NOT FOUND - 需要执行 scripts/refresh_cache.py")
else:
    size = os.path.getsize(db_path)
    print(f"api_cache.db size: {size/1024:.1f} KB")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM indicator_cache")
    count = cursor.fetchone()[0]
    print(f"Indicator cache entries: {count}")
    conn.close()
```

---

## 7. 告警响应流程

### 7.1 告警分级响应

| 级别 | 响应时间 | 响应方式 | 升级条件 |
|:----:|:--------:|----------|----------|
| P0 | 立即 | 电话+即时+邮件 | 5分钟未响应→升级P1 |
| P1 | 15分钟 | 即时+邮件 | 30分钟未恢复→升级P2 |
| P2 | 1小时 | 邮件 | 4小时未恢复→升级P1 |
| P3 | 24小时 | 台账 | 持续7天→升级P2 |

### 7.2 告警响应模板

**P1级告警响应模板:**
```
【P1告警】{alert_id}: {metric}={value}
影响范围: {affected_charts}张图表
触发时间: {timestamp}
当前状态: {fallback/placeholder/real}
处理方案:
1. 检查数据源: {action}
2. 检查绑定: {action}
3. 执行降级: {action}
预计恢复: {eta}
负责人: {owner}
```

### 7.3 常见告警与处理

| 告警ID | 指标 | 条件 | 级别 | 处理 |
|--------|------|:----:|:----:|------|
| ALERT-001 | chart_render_p99_ms | >500 | P2 | 检查慢图表, 考虑缓存 |
| ALERT-002 | chart_render_p95_ms | >300 | P3 | 记录趋势, 不紧急 |
| ALERT-003 | page_render_error_count | >0 | P1 | 立即排查渲染错误 |
| ALERT-004 | render_error_rate_pct | >1 | P1 | 检查数据源健康 |
| ALERT-005 | fallback_trigger_rate_pct | >30 | P2 | 检查api_cache.db |
| ALERT-006 | fallback_placeholder_count | >0 | P3 | 台账记录 |
| ALERT-007 | binding_resolve_error_count | >0 | P2 | 检查tree_config.json |
| ALERT-008 | concurrent_render_p99_ms | >500 | P2 | 检查并发竞争 |
| ALERT-009 | concurrent_render_error_rate_pct | >0 | P1 | 检查线程安全 |
| ALERT-010 | real_data_available_rate_pct | <60 | P3 | 检查数据源覆盖 |

---

## 8. 回滚与恢复

### 8.1 配置回滚

```bash
# 回滚图表配置 (YAML)
git checkout <previous_commit> -- analysis/e2e_output/v88/backlog/framework_tree_meta_chart.yaml

# 回滚节点配置
git checkout <previous_commit> -- data/tree_config.json

# 重新加载引擎
python scripts/node_binding_engine.py
```

### 8.2 数据源恢复

```python
# 恢复真实数据渲染
# Step 1: 刷新api_cache.db
import subprocess
subprocess.run(["python", "scripts/refresh_cache.py"], cwd=REPO_ROOT)

# Step 2: 验证数据加载
engine = make_engine()
for cb in engine.charts[:5]:
    r = engine.render_with_fallback(cb.chart_id)
    print(f"{cb.chart_id}: source={r['source']}")
    # 期望: source="real"
```

### 8.3 引擎重载

```python
# 强制重新加载引擎
def reload_engine():
    engine = NodeBindingEngine(repo_root=REPO_ROOT)
    ok, msg = engine.load()
    if not ok:
        print(f"Reload failed: {msg}")
        return None
    engine.validate(strict=False)
    engine.resolve_all()
    print(f"Reload OK: {len(engine.charts)} charts")
    return engine
```

---

## 9. 附录

### 9.1 引擎API速查

| 方法 | 说明 | 返回 |
|------|------|------|
| `load()` | 加载YAML+tree_config | `(bool, str)` |
| `validate(strict=True)` | 执行6条校验规则 | `[ValidationResult]` |
| `resolve_all()` | 批量解析绑定关系 | `int` (count) |
| `render_chart(cid, use_simulated=False)` | 渲染单图表 | `dict` |
| `render_all(use_simulated=True)` | 批量渲染 | `dict` (分组) |
| `render_with_fallback(cid)` | 三级降级渲染 | `dict` |
| `get_chart_binding(cid)` | 获取绑定上下文 | `ChartBinding` |
| `switch_node(cid, new_node_id)` | 切换节点 | `(bool, str)` |
| `mount_indicator(cid, name, id)` | 挂载指标 | `(bool, str)` |
| `unmount_indicator(cid, id)` | 卸载指标 | `(bool, str)` |
| `get_stats()` | 获取统计信息 | `dict` |
| `get_pending_charts()` | 获取pending图表 | `[ChartBinding]` |
| `verify_pending_render_chain()` | 验证降级链路 | `dict` |

### 9.2 关键文件路径

| 文件 | 路径 |
|------|------|
| 引擎代码 | `scripts/node_binding_engine.py` |
| 图表YAML | `analysis/e2e_output/v88/backlog/framework_tree_meta_chart.yaml` |
| 树配置 | `data/tree_config.json` |
| 数据缓存 | `scripts/api_cache.db` |
| Phase02测试 | `analysis/e2e_output/v88/phase02/dshe/test_phase02_render_ops.py` |
| 边界测试 | `analysis/e2e_output/v88/phase02/dshe/prep_deliverables/test_boundary_scenarios.py` |
| 监控配置 | `analysis/e2e_output/v88/phase02/dshe/monitoring_dashboard.json` |

---

*Document Generated: 2028-05-18 UTC+8*
*Generated by: DSHE Agent*
*Branch: feature/v88-g1*
*Version: v1.0*
