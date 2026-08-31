# 交接文档：指标翻译工作流 — 2026-09-01

## 一、任务总目标

把同花顺 divergence 文件里的**概念指标名**翻译成**SMM/Mysteel/LME 真实指标名**，建立完整映射表，为后续看板重建提供精准的指标ID。

**核心原则**：图表设计方案保留，只改指标名。

---

## 二、分工

| Agent | 服务器 | 负责品种 | divergence现状 |
|-------|--------|---------|---------------|
| Agent A（主脑） | 本台 | ZN + NI + CU + AL | 各30个，完整 |
| **Agent B（你）** | **另一台** | **SN + SI + LI + PB** | SN:30 / SI:29(缺7.3) / LI:19(缺11个) / PB:0 |

---

## 三、你的任务清单

### Step 0：提取概念指标+去重（脚本自动，~5分钟/品种）

**输入**：`analysis/iwencai/{品种}/divergence_*.md`
**输出**：`analysis/iwencai/{品种}/concept_indicators.json`

脚本逻辑：
1. 正则提取每个 divergence 文件中的表格行（`| 序号 | 图名称 | 包含指标...`）
2. 提取每行的「包含指标」列，按顿号/逗号拆分为独立指标名
3. 去除单位后缀（`（元/吨）`、`（万吨）`、`（%）`等）
4. 跨节点去重（完全匹配+去除空格后匹配）
5. 按6大板块分组输出

```python
import re, json, os, glob

def extract_concepts(variety_dir):
    """从divergence文件提取概念指标"""
    results = {}  # {node_id: [{indicator_name, chart_name, chart_type}]}
    
    for f in sorted(glob.glob(f"{variety_dir}/divergence_*.md")):
        node_id = re.search(r'divergence_(.+)\.md', f).group(1)
        with open(f) as fh:
            content = fh.read()
        
        indicators = []
        # 匹配表格行
        for m in re.finditer(r'\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*直接相关', content):
            chart_name = m.group(2).strip()
            raw_indicators = m.group(3).strip()
            # 拆分指标名
            for ind in re.split(r'[、,，]', raw_indicators):
                ind = ind.strip()
                # 去除单位后缀
                ind = re.sub(r'[（(].+?[）)]', '', ind).strip()
                if ind and len(ind) >= 2:
                    indicators.append({
                        'name': ind,
                        'chart_name': chart_name
                    })
        results[node_id] = indicators
    return results

def deduplicate(all_concepts):
    """跨节点去重"""
    unique = {}
    for node_id, indicators in all_concepts.items():
        seen = set()
        deduped = []
        for ind in indicators:
            key = ind['name'].replace(' ', '').replace('（', '').replace('）', '')
            if key not in seen:
                seen.add(key)
                deduped.append(ind)
        unique[node_id] = deduped
    return unique

# 按6大板块分组
DIM_MAP = {
    '2': '价格信号',
    '3': '供给',
    '4': '库存',
    '5': '需求',
    '6': '进出口',
    '7': '成本利润'
}

def group_by_dim(concepts):
    """按板块分组"""
    groups = {}
    for node_id, indicators in concepts.items():
        dim = node_id.split('.')[0]
        dim_name = DIM_MAP.get(dim, dim)
        if dim_name not in groups:
            groups[dim_name] = {}
        groups[dim_name][node_id] = indicators
    return groups

# 主流程
for variety in ['SN', 'SI', 'LI']:
    variety_dir = f"/home/ubuntu/framework-tree/analysis/iwencai/{variety}"
    if not os.path.exists(variety_dir):
        # 尝试其他路径
        variety_dir = f"/home/ubuntu/analysis/iwencai/{variety}"
    
    concepts = extract_concepts(variety_dir)
    deduped = deduplicate(concepts)
    grouped = group_by_dim(deduped)
    
    output = {
        'variety': variety,
        'total_nodes': len(concepts),
        'groups': {
            dim: {
                'nodes': nodes,
                'unique_indicators': list(set(
                    ind['name'] for node_inds in nodes.values() for ind in node_inds
                ))
            }
            for dim, nodes in grouped.items()
        }
    }
    
    out_path = f"{variety_dir}/concept_indicators.json"
    with open(out_path, 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"{variety}: {len(concepts)} nodes → {out_path}")
```

### Step 1：同花顺审计+重设计（每组1次提问，每组~10-15分钟等待回复）

**重要**：不是按单个子节点问，是按**板块组**问。8个品种×6个板块 = 最多48次提问。

#### Prompt 模板

```
你是{品种}基本面资深分析师，同时也是期货公司研报图表设计的审稿专家。

以下是我现有的「{品种}·{板块名}」维度共{N}个子节点的全部图表和指标方案。请你做以下5项工作：

【任务1：删除不合格指标】严格删除以下类型：
- 统计派生类：近N年均值、标准差、分位数、环比、同比、增速、日增减、变化方向
- 临时不可追踪：检修量、排产计划、停产通知、减产损失量
- 不相关凑数：如在TC/成本图里出现产量指标
- 无意义重复：同一指标的不同频率版本只保留最核心的那个

【任务2：跨节点去重+归属调整】
- 同一指标出现在多个子节点 → 只保留最贴切的那个子节点
- 某指标更适合其他子节点 → 移动过去，说明理由

【任务3：补充遗漏指标】
- 删除后如有空位，推荐能说明该子节点核心问题的指标替代
- 参考主流期货公司研报（中信/国泰君安/金瑞/一德/中泰等）的图表习惯
- 每个子节点目标 5-6 张图，不要太少也不要太多

【任务4：重新设计图表组合】
- 每张图只放强相关指标，不强凑多个弱相关指标
- 优先单指标时序图，复合图仅限真正强相关的2个指标（如TC+利润）
- 删除所有季节性统计图（近N年叠加+分位带这种），除非该指标确实有强季节性且市场关注
- 图表形态要参考研报惯例（如TC一般画历史时序，不画季节性）

【任务5：精确指标名（最重要！）】
对最终保留的每个指标，用表格输出：
| 子节点 | 图名称 | 指标名 | SMM官方全称 | Mysteel官方全称 | LME英文变量名(如适用) | 频率 | 单位 |

如果是LME相关指标（升贴水、价差、仓单、持仓等），务必给出LME的精确英文变量名。
如果某指标在SMM和Mysteel都没有对应，标注"待外部源"并推荐最接近的替代指标。

【现有方案如下】
（此处粘贴该板块所有子节点的divergence文件内容）
```

#### 每组提问的操作步骤
1. 打开 https://www.iwencai.com/chat
2. 点"新对话"
3. 粘贴上面的prompt + 该板块所有divergence文件内容
4. 等待回复（约5-10分钟）
5. 保存回复到 `analysis/iwencai/{品种}/audit_{板块名}.md`

### Step 2：知几API搜索验证（脚本自动）

等 Step 1 全部完成后，从同花顺回复中提取精确指标名，脚本自动搜知几。

**此步骤由 Agent A 统一执行**（因为需要知几API密钥和缓存DB）。你只需把 Step 1 的回复文件发给我。

### Step 3：人工审核映射表

Agent A 生成映射表后，你负责审核 SN/SI/LI/PB 的部分。

---

## 四、特殊处理

### PB（铅）—— 没有 divergence 文件
PB 的 `analysis/iwencai/PB/` 下只有旧格式 `*_diversify_*.md`，没有标准 divergence 格式。
**两个选择**：
1. 跳过 PB，等其他品种做完再补
2. 先从旧 diversify 文件中提取指标名，直接进入 Step 1 翻译

**建议**：先跳过 PB，最后集中补。

### SI（硅）—— 缺7.3
直接跳过7.3，先跑已有的29个节点。

### LI（碳酸锂）—— 缺 4.5/5.1-5.3/6.1-6.4/7.1-7.3（共11个）
先跑已有的19个节点。如果之前另一台服务器的agent已补了divergence，合并后再跑。

### 价格信号(2.x) —— LME变量名精确化
价格信号板块的提问要额外强调：
- LME Cash-3M spread（现货-3月期价差）
- LME cancellation ratio（注销仓单比）
- LME warranted vs unwarranted stocks（注册仓单 vs 注销仓单）
- SHFE-LME比价/进口盈亏
- 近月-远月价差（back/contango）
务必让同花顺给出精确英文变量名。

---

## 五、输出文件清单

| 文件 | 内容 | 路径 |
|------|------|------|
| concept_indicators.json | 提取+去重后的概念指标 | `analysis/iwencai/{品种}/concept_indicators.json` |
| audit_{板块}.md | 同花顺审计回复（每组1个） | `analysis/iwencai/{品种}/audit_{板块名}.md` |
| mapping_{品种}.json | 最终映射表（Agent A 生成） | `analysis/iwencai/{品种}/mapping.json` |

---

## 六、时间预估

| 步骤 | SN(30) | SI(29) | LI(19) | PB(0) | 合计 |
|------|--------|--------|--------|-------|------|
| Step 0 提取去重 | 2min | 2min | 2min | 跳过 | 6min |
| Step 1 同花顺审计 | 6组×10min=60min | 6组×10min=60min | 4组×10min=40min | 跳过 | ~3h |
| **你的总工作量** | | | | | **~3.5h** |

---

## 七、协同机制

1. **你做完 Step 1 后**，把 `audit_*.md` 文件路径发给我（飞书消息）
2. **我统一执行 Step 2**（知几搜索），生成映射表
3. **我发映射表给你审核**（SN/SI/LI部分），你确认后入库
4. **PB 最后集中处理**

---

## 八、立即开始

```bash
# 1. 先跑 Step 0 脚本（上面的Python代码）
# 2. 查看输出的 concept_indicators.json
# 3. 按板块逐个提问同花顺
```
