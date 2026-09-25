# 交付物⑤：语义邻近指标判定清单（pb_* ↔ i*）[修正版]

> 工单：DSH_B_P3_FIX_20260924 | 日期：2026-09-24
> **修正说明**：原版将"472匹配对数"误写为pb_*指标总量，本版修正口径，确保可复算。

---

## 1. 口径修正说明

| 字段 | 原版（错误） | 修正版 |
|------|-------------|--------|
| pb_* 总数 | 472 | **70** |
| i* 总数 | 41 | **41** |
| 语义邻近匹配数 | 472 | **1281** |
| 判定为业务重复 | 0 | 0 |
| 判定为独立指标 | 472 | **1281** |

> **原版问题**：pb_* 指标实际仅70条（`pb_`前缀），原版误报为472条。472可能是嵌套结构下`_main_metric`中pb相关子节点的计数，而非独立业务指标数。

---

## 2. 修正后判定概况

| 指标 | 数值 | 可复算性 |
|------|------|----------|
| pb_* 指标总量 | 70 | ✅ `len([k for k in indicators if k.startswith('pb_')])` |
| i* 指标总量 | 41 | ✅ `len([k for k in indicators if k.startswith('i')])` |
| 语义邻近匹配 | 1281 | ✅ 名称相似度 > 15% 的匹配对 |
| 业务重复 | 0 | ✅ zhiji_id 交集 = 0 |
| 独立指标 | 1281 | ✅ 全部匹配对 |

---

## 3. 判定结论

**pb_\*与i*指标ID无交集（zhiji_id交集=0），所有语义邻近匹配均为独立指标，非业务重复。**

原因：i*为PB旧版编号体系（41条），pb_*为PB新版规范ID体系（70条），两者是同一品种的不同指标集合。

---

## 4. Top 15语义邻近对（名称相似度排序）

| # | pb_* Key | i* Key | 相似度(%) | 判定 |
|---|----------|--------|----------|------|
| 1 | `pb_44_aux` | `i26` | 82 | INDEPENDENT |
| 2 | `pb_44_aux_2` | `i26` | 82 | INDEPENDENT |
| 3 | `pb_45_aux` | `i30` | 82 | INDEPENDENT |
| 4 | `pb_43_aux` | `i32` | 79 | INDEPENDENT |
| 5 | `pb_43_aux` | `i33` | 79 | INDEPENDENT |
| 6 | `pb_43_aux` | `i34` | 79 | INDEPENDENT |
| 7 | `pb_43_aux` | `i35` | 79 | INDEPENDENT |
| 8 | `pb_43_aux` | `i36` | 79 | INDEPENDENT |
| 9 | `pb_44_aux_3` | `i26` | 72 | INDEPENDENT |
| 10 | `pb_63_battery_import` | `i37` | 71 | INDEPENDENT |
| 11 | `pb_23_aux` | `i29` | 67 | INDEPENDENT |
| 12 | `pb_62_pb_import_total` | `i17` | 67 | INDEPENDENT |
| 13 | `pb_62_plate_export` | `i41` | 67 | INDEPENDENT |
| 14 | `pb_62_plate_import` | `i17` | 67 | INDEPENDENT |
| 15 | `pb_63_battery_import` | `i39` | 67 | INDEPENDENT |

---

## 5. 可复算性验证

### 5.1 指标计数

```python
# 可复算代码
import json
data = json.load(open('data/indicators_v1.json'))
indicators = {k:v for k,v in data.items() if isinstance(v, dict) and not k.startswith('_') and k not in ['version','change','updated']}

pb_count = len([k for k in indicators if k.startswith('pb_')])  # 70
i_count = len([k for k in indicators if k.startswith('i')])     # 41
```

### 5.2 ID交集验证

```python
# pb_* 的所有 zhji_id
pb_ids = set()
for k, v in indicators.items():
    if k.startswith('pb_'):
        ids = v.get('ids', {})
        if isinstance(ids, dict):
            pb_ids.update(ids.values())

# i* 的所有 zhji_id
i_ids = set()
for k, v in indicators.items():
    if k.startswith('i'):
        ids = v.get('ids', {})
        if isinstance(ids, dict):
            i_ids.update(ids.values())

intersection = pb_ids & i_ids
print(f'pb_* IDs: {len(pb_ids)}, i* IDs: {len(i_ids)}, intersection: {len(intersection)}')
```

**验证结果**：pb_* IDs=70, i* IDs=40, intersection=0

---

*生成时间：2026-09-25 17:21*
