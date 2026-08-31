# 镍(NI) 指标归属数据库建设 — 交接文档

> 生成时间: 2026-08-31 17:54
> 上下文估算: ~72%（建议新对话开始）

## 一、问题背景

### 审计发现
- 镍看板30个节点，全部与同花顺发散标准答案不匹配（匹配度0/8）
- 根因：build脚本没有对标 `analysis/iwencai/NI/divergence_*.md` 标准答案
- 已完成的修复：
  - ✅ 万金油裁剪：`ni_21_close_front` 从18节点→2节点
  - ✅ 审计脚本升级：支持五维检测 + divergence对照
  - ✅ 生成对照矩阵：`docs/NI_FULL_MATRIX.md`

### 方案决策
采用**方案A（轻量版）**：在现有 `indicators_v1.json` 基础上扩展schema，加入归属关系字段。

## 二、新Schema设计

在现有指标对象基础上，增加5个字段：

```json
{
  "ni_21_close_front": {
    "name": "SHFE：镍：主力合约：收盘价（日）",
    "unit": "元/吨",
    "freq": "daily",
    "verified": false,
    "ids": {"NI": "FU00014997"},
    
    // ↓↓↓ 新增字段 ↓↓↓
    "variety": "NI",                    // 品种代码
    "board": "2",                       // 板块（2价格/3供给/4库存/5需求/6进出口/7成本）
    "node": "2.1",                      // 节点（如2.1/3.1.5/4.3）
    "chart_role": "主图",                // 在此节点的角色（主图/补充/普通）
    "lifecycle": "active"               // 生命周期（active/deprecated/replaced）
  }
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `variety` | string | 是 | 品种代码：NI/CU/AL/ZN/PB/SN/LI/SI |
| `board` | string | 是 | 板块编号：2/3/4/5/6/7 |
| `node` | string | 是 | 节点编号：2.1/2.2/.../7.3 |
| `chart_role` | string | 是 | 角色：主图/补充/普通 |
| `lifecycle` | string | 是 | 状态：active/deprecated/replaced |

### 使用规则

1. **一个指标只能归属一个节点**（防串用）
2. **每个节点必须有且仅有一个主图**（正主防串用）
3. **build脚本从JSON读归属关系**（声明式build）
4. **审计脚本验证HTML与JSON一致性**（自动检查）

## 三、当前镍指标现状

### 统计概览

| 维度 | 数值 |
|------|------|
| 总指标数 | 66 |
| 只被1个节点使用 | 54 |
| 被2个节点使用 | 10 |
| 被3+个节点使用 | 2 |

### 指标归属示例（前10个）

```json
[
  {
    "indicator_id": "ni_21_close_front",
    "name": "SHFE：镍：主力合约：收盘价（日）",
    "unit": "元/吨",
    "used_in_nodes": ['2.1', '2.2'],
    "node_count": 2,
    "suggested_node": "2.1",
    "suggested_role": "主图"
  },
  {
    "indicator_id": "ni_21_front_price",
    "name": "MHP：NI≥34%，CO≥2%：镍远期现货价格：中国主要港口（日）",
    "unit": "美元/金属吨",
    "used_in_nodes": ['2.2', '2.3'],
    "node_count": 2,
    "suggested_node": "2.2",
    "suggested_role": "普通"
  },
  {
    "indicator_id": "ni_21_lme_price",
    "name": "SMM: 进口盈亏: 镍: 现货: LME价格: 日度",
    "unit": "",
    "used_in_nodes": ['2.3'],
    "node_count": 1,
    "suggested_node": "2.3",
    "suggested_role": "普通"
  },
  {
    "indicator_id": "ni_21_near_price",
    "name": "MHP：NI≥34%，CO≥2%：镍远期现货价格：中国主要港口（日）",
    "unit": "美元/金属吨",
    "used_in_nodes": ['2.1'],
    "node_count": 1,
    "suggested_node": "2.1",
    "suggested_role": "普通"
  },
  {
    "indicator_id": "ni_21_premium",
    "name": "水淬镍：15-22%Ni：印尼产：升贴水（日）",
    "unit": "美元/金属吨",
    "used_in_nodes": ['2.1', '2.2', '4.1', '4.2'],
    "node_count": 4,
    "suggested_node": "2.1",
    "suggested_role": "补充"
  },
  {
    "indicator_id": "ni_21_volume_front",
    "name": "SHFE：镍：主力合约：单边交易：成交量（日）",
    "unit": "手",
    "used_in_nodes": ['2.1'],
    "node_count": 1,
    "suggested_node": "2.1",
    "suggested_role": "普通"
  },
  {
    "indicator_id": "ni_22_price",
    "name": "镍豆：Ni≥99.88%：澳大利亚产：现货到岸价格：中国（日）",
    "unit": "美元/吨",
    "used_in_nodes": ['2.2'],
    "node_count": 1,
    "suggested_node": "2.2",
    "suggested_role": "补充"
  },
  {
    "indicator_id": "ni_22_price_2",
    "name": "电解镍：Ni≥99.96%：俄罗斯产：现货到岸价格：中国（日）",
    "unit": "美元/吨",
    "used_in_nodes": ['2.4', '2.5'],
    "node_count": 2,
    "suggested_node": "2.4",
    "suggested_role": "主图"
  },
  {
    "indicator_id": "ni_22_price_3",
    "name": "镍生铁：13%＞Ni＞10%：印尼产：远期现货价格：中国主要港口（日）",
    "unit": "元/镍",
    "used_in_nodes": ['2.4'],
    "node_count": 1,
    "suggested_node": "2.4",
    "suggested_role": "普通"
  },
  {
    "indicator_id": "ni_22_price_nickel_powder",
    "name": "高冰镍：Ni≥65%，Co≥1%：钴远期现货价格：中国主要港口（日）",
    "unit": "美元/金属吨",
    "used_in_nodes": ['2.5'],
    "node_count": 1,
    "suggested_node": "2.5",
    "suggested_role": "普通"
  },
  ...
]
```

## 四、下一步任务清单

### Phase 1: Schema扩展（15分钟）

1. **修改 `data/indicators_v1.json`**
   - 为所有66个镍指标添加5个新字段
   - 根据当前HTML使用情况填充初始值
   - 验证JSON格式正确

2. **修改 `scripts/build_ni_*.py`（或新建统一build脚本）**
   - 从 `indicators_v1.json` 读取节点归属关系
   - 改为声明式：`build_node("2.1")` 自动读取该节点所有指标
   - 输出到 `ni_2_1.html`

### Phase 2: 镍看板重建（30-60分钟）

按节点逐个重建，流程：

```
1. 读取 divergence_2.1.md 标准答案
2. 从 indicators_v1.json 筛选 node="2.1" 的指标
3. 对比标准答案 vs 当前归属，标记差异
4. 更新 indicators_v1.json 的归属字段
5. 运行 build_node("2.1") 生成HTML
6. 运行 indicator_audit.py 验证
```

优先级：
- **P0**: 万金油已裁剪的16个节点（2.1/2.2/4.x/5.x/6.x/7.x）
- **P1**: 其余14个节点

### Phase 3: 回归验证（5分钟）

```bash
cd /home/ubuntu/framework-tree
python3 scripts/indicator_audit.py --variety NI
# 目标: 🔴数量降至0
```

## 五、关键文件路径

| 文件 | 路径 | 用途 |
|------|------|------|
| 指标元数据 | `data/indicators_v1.json` | 扩展schema，加5个字段 |
| 审计脚本 | `scripts/indicator_audit.py` | 五维检测 + divergence对照 |
| 对照矩阵 | `docs/NI_FULL_MATRIX.md` | 30节点标准答案 vs 实际 |
| 审计报告 | `docs/AUDIT_NI_REPORT.md` | 当前审计结果 |
| divergence文档 | `analysis/iwencai/NI/divergence_*.md` | 同花顺标准答案 |
| 镍HTML | `ni_*.html` | 30个节点页面 |

## 六、新对话启动指令

在新对话中粘贴以下内容：

```
继续镍(NI)指标归属数据库建设（方案A）。

交接文档已生成，请按以下步骤执行：

1. 读取交接文档了解背景
2. 扩展 `data/indicators_v1.json` schema（加5个字段）
3. 从节点2.1开始逐个重建镍看板
4. 每个节点完成后运行审计验证
5. 全部完成后生成最终报告

关键路径：
- indicators_v1.json: /home/ubuntu/framework-tree/data/indicators_v1.json
- 审计脚本: /home/ubuntu/framework-tree/scripts/indicator_audit.py
- divergence: /home/ubuntu/framework-tree/analysis/iwencai/NI/

完成后告诉我"镍重建完毕"，我会检查审计报告。
```

## 七、预期成果

完成后你将得到：

1. **扩展后的 `indicators_v1.json`**
   - 所有66个镍指标都有归属关系
   - 可作为锌铜铝的模板

2. **声明式build脚本**
   - `build_node("2.1")` 自动对标标准答案
   - 不再出现"build没看divergence"的问题

3. **验证通过的镍看板**
   - 审计报告🔴数量=0
   - 30个节点全部与标准答案对齐

4. **可复用的工作流**
   - 锌铜铝直接套用这个流程
   - build即对标，不需要事后审计修复

## 八、风险与注意事项

1. **JSON字段添加顺序**
   - 保持现有字段不动，新增字段放后面
   - 避免破坏其他品种的读取逻辑

2. **build脚本兼容性**
   - 如果现有build脚本是硬编码，可能需要重写
   - 建议新建统一的 `build_node.py` 函数

3. **审计脚本升级**
   - 当前版本已支持divergence对照
   - 可能需要加"验证indicators_v1.json归属关系"的检测

4. **数据一致性**
   - 修改JSON后必须重新build HTML
   - 否则审计会报"JSON与HTML不一致"

---

**交接完毕。新对话直接粘贴第六节的启动指令即可开始。**
