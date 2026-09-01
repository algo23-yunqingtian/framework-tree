# 交接文档：framework-tree 图表主题修复 · 2026-09-01

> **生成时间**：2026-09-01
> **项目**：`/home/ubuntu/framework-tree`（GitHub Pages 有色金属指标看板）
> **状态**：主题匹配问题已诊断清楚，待修复

---

## 一、问题诊断

### 1. 用户反馈

> "锌的 3.1.5 要有巴林库存？哪里出问题了？"

### 2. 根因分析

**两层错误**：

| 层面 | 问题 | 证据 |
|---|---|---|
| 指标注册 | `zn_22_lme_inv`（LME锌库存）被错误归属到 10 个节点，包含 3.1.5 | `_nodes: ['2.2','2.3','2.4','2.6','3.1.4','3.1.5','3.2.4','4.1','4.2','5.3']` |
| 建页引擎 | 正主选择没做题材校验，优先"有数据"指标 | 3.1.5 页主图 = 巴林库存（43 点），而不是 TC（1081 点） |

### 3. 节点定义

```json
// data/tree_config.json
{"id":"s5","code":"3.1.5","name":"TC 加工费","q":"先行·矿紧松","comms":["cu","al","pb","zn","ni","sn","li"]}
```

**3.1.5 只能放 TC/加工费相关指标**，库存、收盘价、进口量都不相关。

---

## 二、批量检查结果

### 1. 检查脚本

```bash
cd /home/ubuntu/framework-tree
python3 << 'PYEOF'
import json, re

# 检查所有品种 3.1.5 节点的主图是否匹配 TC 加工费
for variety in ['zn','cu','al','pb','ni','sn','si','li']:
    html_file = f'{variety}_3_1_5.html'
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        titles = re.findall(r'<div class="chart-title">([^<]+)</div>', content)
        tc_related = sum(1 for t in titles if 'TC' in t or '加工费' in t)
        other = len(titles) - tc_related
        if other > 0:
            print(f'{variety}_3_1_5: TC相关{tc_related}图, 其他{other}图')
            for t in titles:
                if 'TC' not in t and '加工费' not in t:
                    print(f'  ❌ {t[:50]}')
    except:
        pass
PYEOF
```

### 2. 检查结果

| 品种 | 3.1.5 主图 | 节点定义 | 问题 |
|---|---|---|---|
| 锌 | ❌ LME巴林库存 | TC加工费 | 不相关 |
| 镍 | ❌ 主力合约收盘价 | TC加工费 | 不相关 |
| 锡 | ❌ 缅甸进口量 | TC加工费 | 不相关 |
| 硅 | ❌ 主力合约收盘价 | TC加工费 | 不相关 |
| 锂 | ❌ 碳酸锂毛利 | TC加工费 | 不相关 |
| 铜 | ✅ 铜精矿TC指数 | TC加工费 | 正确 |
| 铝 | ✅ 铝棒加工费 | TC加工费 | 正确 |

**结论**：8 个品种中 **5 个 3.1.5 全错**，只有铜铝正确。

---

## 三、昨晚审计的盲区

### 1. 昨晚做了什么

| 任务 | 内容 | 脚本 |
|---|---|---|
| P0 | 图表标题歧义（A vs A → A vs B） | `disambig_title()` |
| P1 | 跨品种串节点（锌页出现铝指标） | `audit_chart_quality_precise.py` |
| P2 | 页脚跨品种（锌页脚写"铝"） | 同上 |

### 2. 审计脚本判定规则

```python
# P1 WRONG_NODE：指标ID前缀 != 页面品种前缀
# 例如：zn_3_1_5.html 出现 al_25_tc → P1 硬bug
# 例如：zn_3_1_5.html 出现 zn_22_lme_inv → ✅ 不算P1（都是zn_）
```

### 3. 审计脚本的盲区

**没检查**：指标是否匹配节点主题（3.1.5 应该只有 TC 相关指标）

**结果**：
- 昨晚审计：P1=0 ✅（没有跨品种串台）
- 真实问题：锌 3.1.5 主图是巴林库存 → 审计脚本完全没发现

### 4. 我的疏忽

1. 昨晚主要解决"跨品种串台"（这是 P1 硬 bug）
2. "同品种跨节点主题不匹配"不在审计脚本里
3. 门禁三道全绿，让我误以为没问题
4. 时间紧迫，没逐页核对题材

---

## 四、过度归属指标清单

```bash
cd /home/ubuntu/framework-tree
python3 << 'PYEOF'
import json
d = json.load(open('data/indicators_v1.json'))
# 找_nodes节点数>5的指标
over_assigned = []
for k,v in d['indicators'].items():
    nodes = v.get('_nodes', [])
    if len(nodes) > 5:
        over_assigned.append((k, v.get('name',''), len(nodes), nodes[:10]))
over_assigned.sort(key=lambda x: -x[2])
for k, name, n, nodes in over_assigned:
    print(f'{k}: {name[:30]} | {n}节点 | {nodes}')
PYEOF
```

**结果**：

| 指标 | 名称 | 节点数 | 问题 |
|---|---|---|---|
| `ni_21_close_front` | SHFE镍主力合约收盘价 | 18 | 过度归属 |
| `sn_21_close_front` | SHFE锡主力合约收盘价 | 18 | 过度归属 |
| `si_21_close_front_industrial_si` | GFEX工业硅主力合约收盘价 | 12 | 过度归属 |
| `zn_22_lme_inv` | LME锌特高级原产国库存巴林 | 10 | **包含 3.1.5** |
| `zn_23_close_front` | SHFE锌主力合约收盘价 | 7 | 过度归属 |

**修复方向**：这些指标的 `_nodes` 应只保留真正相关的节点。

---

## 五、修复方案

### 1. 修正指标注册

**原则**：
- 收盘价 → 只放 2.1（盘面结构）、4.1/4.2（库存价格联动）
- 库存 → 只放 2.2/2.3（现货升贴水/海外价格）、4.1/4.2（交易所库存/仓单）
- TC → 只放 3.1.5（TC加工费）

**修复脚本**：

```bash
cd /home/ubuntu/framework-tree
# 备份
cp data/indicators_v1.json data/indicators_v1.json.bak

# 修正 zn_22_lme_inv：删除 3.1.5
python3 << 'PYEOF'
import json
d = json.load(open('data/indicators_v1.json'))
# zn_22_lme_inv 应只保留库存相关节点
if 'zn_22_lme_inv' in d['indicators']:
    d['indicators']['zn_22_lme_inv']['_nodes'] = ['2.2', '2.3', '4.1']
    print("✅ zn_22_lme_inv 修正：['2.2', '2.3', '4.1']")
json.dump(d, open('data/indicators_v1.json','w'), indent=2, ensure_ascii=False)
PYEOF
```

### 2. 加题材校验层

**建页引擎**：`scripts/build_5m_batch.py`

**加校验函数**：

```python
def check_theme_match(mid, node_code, indicators_meta):
    """检查指标是否匹配节点主题"""
    name = indicators_meta.get(mid, {}).get('name', '')
    
    # 3.1.5 节点必须有 TC 或 加工费
    if node_code == '3.1.5':
        if 'TC' not in name and '加工费' not in name:
            return False, f"3.1.5节点主图必须含TC/加工费，当前：{name}"
    
    # 4.1 节点必须有 库存
    if node_code == '4.1':
        if '库存' not in name and '仓单' not in name:
            return False, f"4.1节点主图必须含库存/仓单，当前：{name}"
    
    # 5.3 节点必须有 订单/开工率/需求
    if node_code == '5.3':
        keywords = ['订单', '开工率', '需求', '采购']
        if not any(kw in name for kw in keywords):
            return False, f"5.3节点主图必须含订单/开工率/需求，当前：{name}"
    
    return True, "OK"
```

### 3. 重跑建页

```bash
cd /home/ubuntu/framework-tree
# 修正指标注册后，重跑 3.1.5 节点
python3 scripts/build_5m_batch.py 3.1.5

# 跑门禁
python3 scripts/check_html.py
node scripts/verify_render.js
python3 scripts/reclaim.py
```

### 4. 加审计检查

**修改 `scripts/audit_chart_quality_precise.py`**：

```python
# 新增 P4：主题不匹配
p4 = []  # 同品种跨节点主题不匹配

# 检查规则
THEME_RULES = {
    '3.1.5': ['TC', '加工费'],
    '4.1': ['库存', '仓单'],
    '5.3': ['订单', '开工率', '需求'],
    # ... 其他节点
}

for f in all_html:
    # 提取节点号
    node_code = f.split('_')[1].replace('_', '.')
    if node_code not in THEME_RULES:
        continue
    
    # 检查主图标题
    first_chart_title = ...
    keywords = THEME_RULES[node_code]
    if not any(kw in first_chart_title for kw in keywords):
        p4.append({'file': f, 'node': node_code, 'title': first_chart_title})
```

---

## 六、当前状态

| 项目 | 状态 |
|---|---|
| main HEAD | `eef1eea` |
| 指标数 | 809 条 v3.45 |
| 页面数 | 224 页 |
| 门禁 | 223/223 + 224/224 + 12/0 ✅ |
| 跨品种串台 | P1=0 ✅ |
| **主题匹配** | **P4=5+ 待修** ❌ |

---

## 七、待做清单

| 优先级 | 任务 | 量 |
|---|---|---|
| P0 | 修正 7 条过度归属指标 | 7 条 |
| P0 | 重跑锌/镍/锡/硅/锂 3.1.5 建页 | 5 页 |
| P1 | 建页引擎加题材校验层 | 1 个脚本 |
| P1 | 审计脚本加主题匹配检查 | 1 个脚本 |
| P2 | 全面检查其他节点主题匹配度 | ~200 页 |

---

## 八、参考文件

| 文件 | 用途 |
|---|---|
| `data/tree_config.json` | 节点权威定义 |
| `data/indicators_v1.json` | 指标元数据（含 `_nodes` 归属） |
| `scripts/audit_chart_quality_precise.py` | 审计脚本（需加主题检查） |
| `scripts/build_5m_batch.py` | 建页引擎（需加题材校验） |
| `analysis/iwencai/*/divergence_*.md` | 同花顺发散结果（主题正确） |

---

## 九、反思

**昨晚的审计为什么没发现这个问题？**

1. **审计范围不够**：只查了"跨品种串台"，没查"同品种跨节点主题"
2. **门禁盲区**：门禁只检查文件/cid/版本，不检查题材
3. **时间紧迫**：P1/P2 修复后门禁全绿，让我误以为没问题
4. **没逐页核对**：应该抽检每个节点的主题匹配度

**后续改进**：
1. 审计脚本必须加主题匹配检查
2. 建页引擎必须加题材校验层
3. 新页面必须人工抽检主题
4. 同花顺发散结果要和最终页面对照

---

**交接文档路径**：`/home/ubuntu/framework-tree/docs/HANDOVER_20260901_THEME_FIX.md`