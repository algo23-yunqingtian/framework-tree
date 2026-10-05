# V86-RC2 灰度决策事件异常容错增强规范（T3.2）

> **载体**: `gray_gate_event_persist_v11_enhance.py`
> **分支**: `feature/v85-chart-template` @ `ba82d04`
> **版本**: 1.1
> **日期**: 2026-10-15
> **状态**: ✅ 12/12自检PASS

---

## 1. v1.0 → v1.1 增强对比

| 能力 | v1.0 | v1.1 增强 |
|------|------|-----------|
| 事件唯一性 | MD5(run_id+ts+decision) | MD5(run_id+ts+decision+seq) |
| 同秒多事件 | 合并丢失 ❌ | seq独立保留 ✅ |
| 时间戳注入 | 仅当前UTC | 支持外部timestamp(溯源/回放) |
| 字段缺失 | 写NULL ❌ | 兜底默认值 ✅ |
| 超大payload | 不截断 ❌ | 截断2000字符 ✅ |
| 重复投递 | 合并+dedup+1 | 先查再INSERT/UPDATE ✅ |
| 乱序写入 | 按写入序 | 按timestamp+seq排序 ✅ |
| Schema字段 | 22字段 | 26字段(+seq/dedup_count/source/drill_tag) |
| 演练标记 | 无 | drill_tag区分chaos/failover/normal |
| 来源标记 | 无 | source=hermes/dshb/dshe |

---

## 2. 容错场景验证（12项自检）

| # | 场景 | 结果 |
|---|------|------|
| T01 | 同秒告警唯一性(5个seq) | ✅ PASS |
| T02 | 重复投递去重(dedup_count=2) | ✅ PASS |
| T03 | 正常决策持久化 | ✅ PASS |
| T04 | 乱序容忍排序 | ✅ PASS |
| T05 | 超大payload截断(2025≤2050) | ✅ PASS |
| T06 | 非dict状态兜底 | ✅ PASS |
| T07 | 演练标记查询(drill_tag=chaos) | ✅ PASS |
| T08 | 来源字段(source=dshe) | ✅ PASS |
| T09 | 总数验证 | ✅ PASS |
| T10 | schema版本(1.1) | ✅ PASS |
| T11 | 决策事件计数 | ✅ PASS |
| T12 | 乱序无丢失 | ✅ PASS |

**12/12 PASS**

---

## 3. 事件Schema v1.1 (26字段)

```
v1.0 (22字段) + 4新增字段:
├── seq           INTEGER - 序列号(同秒去重, 默认1)
├── dedup_count   INTEGER - 重复投递次数(默认1)
├── source        TEXT - 事件来源(hermes/dshb/dshe)
└── drill_tag     TEXT - 演练标记(chaos/failover/normal)
```

### 3.1 新增字段说明

| 字段 | 用途 | 示例 |
|------|------|------|
| seq | 同秒多事件区分 | seq=1~5 |
| dedup_count | 重复投递追踪 | dedup_count=2(投递2次) |
| source | 事件来源 | hermes/dshb/dshe |
| drill_tag | 演练标记 | chaos/failover/normal |

---

## 4. 容错机制

### 4.1 事件唯一性

```python
event_id = MD5(f"{run_id}|{timestamp}|{decision}|{seq}")
```

seq参数解决同秒多事件合并问题。调用方传入seq=1,2,3...即可保证同秒事件唯一。

### 4.2 字段兜底

```python
def _safe_str(val, default=""):
    if val is None: return default
    if isinstance(val, (int, float, bool)): return str(val)
    return val  # str
```

所有字段缺失用默认值，不写NULL污染。

### 4.3 超大payload过滤

```python
MAX_MESSAGE_LEN = 2000
MAX_INPUT_STATE_LEN = 4000
def _truncate(val, max_len):
    if val and len(val) > max_len:
        return val[:max_len] + f"...[truncated {len(val)-max_len} chars]"
    return val
```

### 4.4 去重策略

```python
existing = SELECT dedup_count WHERE event_id = ?
if existing:
    UPDATE SET dedup_count = dedup_count + 1  # 重复投递计数
    return event_id
else:
    INSERT  # 新事件
```

### 4.5 乱序容忍

查询按`timestamp ASC, seq ASC`稳定排序，允许乱序写入。

---

## 5. 集成示例

```python
from gray_gate_event_persist_v11_enhance import GrayEventPersistorV11

p = GrayEventPersistorV11('/data/gray_events_v11.db')

# 正常决策事件
p.record_decision(result, state, timestamp='2026-10-15T16:00:25Z', seq=1, drill_tag='chaos')

# 同秒多告警(seq区分)
for i, alert in enumerate(alerts):
    p.record_alert('CRITICAL', alert, run_id='AL-001', timestamp=ts, seq=i+1, drill_tag='chaos')

# 来源标记
p.record_healthcheck(state, run_id='HC-001', source='dshe')

p.close()
```

---

## 6. 向后兼容

v1.1完全兼容v1.0：
- 22字段全部保留
- 4新增字段有默认值，旧数据查询不受影响
- 旧event_id生成方式仍可用（seq默认1）

---

*本规范为gray_gate_event_persist_v11_enhance.py容错增强规范。12/12自检PASS，覆盖乱序/重复/缺字段/超大payload全部场景。*
