# 任务卡 · 知几指标匹配 v4 修正（回传主脑审核后 merge）

> 日期：2026-09-07
> 接收人：task/zhiji_match_all 的 agent
> 主脑审计：`docs/AUDIT_zhiji_match_20260907.md`
> 你的提交：`e7b4d31`（7 品种 2322 指标，A547/B900/C875）

---

## 一、你的产物总体是好的

- ✅ 7 品种全节点覆盖、结构规范、**0 处跨品种串台**
- ✅ **A 级 547 条语义全对，可直接用**
- ✅ C 级 875 条 verified=false + zhiji_id 为空，标注诚实
- ❌ **只有 B 级 900 条有问题** —— 抽检 6 组送同花顺复核，5 组答"否"、1 组"勉强"

主脑的审计结论：**别重跑全量。A 级不动，只重跑 B 级。**

---

## 二、B 级为什么会错：4 处代码缺陷

问题不在你写 JSON 的逻辑，在 `zhiji_match_v3.py` 这两个函数：

### 缺陷 1：`classify_match()` 是纯字面命中，完全不做概念校验
```python
if has_variety and term_hits >= 2:  return 'A'
elif has_variety and term_hits >= 1: return 'B'
```
「目标=镍精矿**加工费**」，知几条目=「加拿大：镍精矿：**期末库存**」→ 都含「镍」「精矿」，`term_hits=2` → 判 A。
字面全对，**概念完全不同**。这就是 18 次复用的来源。

### 缺陷 2：`gen_keywords()` 只做词拼接，不生成领域同义词
```python
kws.append(f"{variety_cn} {parts[0]}")
```
「海外硅矿季度产量」→ 搜「工业硅 海外」→ 命中「工业硅：产量：广西（月）」。**没生成「硅石/硅矿/工业硅原料」这类上游词**，也没生成「海外→印尼/美国/巴西」的地域展开。

### 缺陷 3：`search_zhiji(kw)['results'][:5]` 只看前 5 条
真指标常在第 6-10 条（实测「电解铝 社会库存」的总量 `ID00188307` 排第 4，但「铝锭 厂库」的真指标 `a12760296` 排第 6，被截掉了）。

### 缺陷 4：`best_match['verified'] = True  # Assume verified for now`
第 514 行。**系列根本没拉**，就假设 verified=True。所以 B 级 900 条全是"自称已验证"。

---

## 三、v4 修正规则（必须全实现）

### 规则 1：八概念维度互斥校验（核心，挡住 80% 误配）
目标指标名归一到 8 个概念维度，候选条目维度不一致 → 直接 C：

```python
CONCEPTS = {
    '加工费': ['TC','加工费','RC','折价系数','扣率'],
    '库存':   ['库存','仓单','隐性库存','厂库','社库'],
    '进口量': ['进口量','进口数量','进口量'],          # 关键：排除"进口价格指数"
    '产量':   ['产量'],
    '开工率': ['开工率','产能利用率'],
    '利润':   ['利润','价差'],
    '价格':   ['价格','结算价','收盘价','最高价','最低价','指数','比值','升贴水'],
    '订单':   ['订单','排产','开工订单'],
}
def concept(name):
    """返回该名称涉及的概念集合"""
    return {c for c, kws in CONCEPTS.items() if any(k in name for k in kws)}

# 判定：目标要求"加工费"，候选只有"库存" → 维度不相交 → C
if concept(target) and concept(cand) and not (concept(target) & concept(cand)):
    return 'C'
```

⚠️ 「进口量」必须能区分「进口数量/进口量」和「进口TC指数/进口现货价」——后者属"价格"。这一条单独挡住了铜 15 次误配。

### 规则 2：产业链上下游互斥
```python
CHAIN = {
    '氧化铝': '上游', '电解铝': '中游', '铝锭': '中游', '铝加工': '下游',
    '铜矿': '上游', '铜精矿': '上游', '粗铜': '中游', '电解铜': '中游', '铜板带': '下游',
    '硅矿': '上游', '工业硅': '中游', '多晶硅': '下游',
    '镍矿': '上游', 'NPI': '中游', 'MHP': '中游', '电解镍': '中游', '不锈钢': '下游',
    '铅矿': '上游', '再生铅': '中游', '铅酸电池': '下游',
}
# 目标写"电解铝库存"，候选是"氧化铝库存" → 上/中环节不同 → C
```

### 规则 3：地域互斥
```python
OVERSEAS = ['海外','国外','全球','印尼','美国','巴西','南非','智利','秘鲁','蒙古',
            '澳大利亚','缅甸','俄罗斯','菲律宾','加拿大','几内亚','印尼','哈萨克斯坦']
DOMESTIC = ['中国','国内','广西','云南','四川','新疆','内蒙','江苏','山东','安徽','湖南','云南']
# 目标含海外词、候选只有国内词 → C（这条单独挡住硅29次+锌14次+锡14次误配）
```

### 规则 4：同义词展开（提高召回，减少"找不到就填空"）
目标名生成 5-8 个搜索词，必须含：
```
原词 + 空格分词 + 领域同义词 + 上游/下游产品名 + 地域展开 + 平台前缀
```
例：`"海外硅矿季度产量"` →
```
["工业硅 硅矿 产量", "硅石 产量", "金属硅 原料 产量",
 "工业硅 原料硅石 产量", "硅矿 产量 全球", "硅石 矿产 产量"]
```
例：`"镍精矿TC加工费"` →
```
["镍 精矿 TC", "镍 加工费", "镍矿 加工费", "NPI 加工费",
 "镍精矿 折价系数", "NICKEL 精矿 TC"]
```

### 规则 5：`search` limit 从 5 改 10，遍历全部结果找双匹配
```python
for result in data['results'][:10]:        # ← 5 改 10
    ...
# 且必须"品种词 + 核心关键词"双匹配才标 A，仅品种词匹配 = 假命中
```

### 规则 6：`series` 实测非空才算 verified
```python
s = get_series(zhiji_id)
points = len(s.get('data', [])) if s else 0
if points == 0:
    return 'C'   # 死数据，不许复用
verified = points >= 3
```
实测：`ID01445986 工业硅：产量：广西（月）` **series 为空**，却被复用了 29 次。

### 规则 7：单一 ID 复用上限 = 3 次，超了强制人工复核
```python
reuse_count = {}   # zhiji_id -> count
if reuse_count.get(zhiji_id, 0) >= 3:
    notes += '; ⚠️REUSE>3 需人工复核'
```
统计你的产物：281 组 ID 被重复引用，Top1 复用 29 次。

### 规则 8：找不到真指标 = 标 C，**禁止填空**
zhiji_id 留空 + verified=false + notes 写「知几无此指标，需外部源」。
**绝对不允许用字面相近的其他指标顶。** 这是 B 级 900 条全部出问题的唯一原因。

---

## 四、主脑实测对照表（7 个误配节点，你照这个改）

| 节点 | 原配（错） | 复用 | 同花顺判定 | 主脑实测改良搜索 → 真指标 |
|---|---|---|---|---|
| CU 2.1 沪伦比 | `a12853765` SMM**预测值** | 1 | — | `FU00015882` Mysteel：铜：沪伦比值（日）✅ |
| CU 2.1/3.1.4 铜精矿进口量 | `ID02407538` 进口**TC指数** | 15 | 否 | `CM0000206865` 铜精矿：进口数量初值：中国（月）✅ |
| CU 3.1.4 智利进口铜精矿量 | `ID02407538` TC指数 | 15 | 否 | `ID01537380` 铜精矿：发运量：智利（周）✅ + `CM0000451453` 铜矿砂：进口数量：智利→中国（月）✅ |
| AL 4.3 社会库存 | `ID01721697` **氧化铝**库存 | 17 | 否 | `ID00188307` 电解铝：现货库存：中国（日）✅ |
| AL 4.4 工厂库存 | `ID01721697` 氧化铝库存 | 17 | 否 | `a12760296` SMM: 铝锭厂库库存（分省）✅ |
| NI 3.1.5/3.2.1/3.2.2 镍精矿TC | `ID01929006` 加拿大镍精矿**库存** | 18 | 否 | **知几无此指标 → 应标 C**（搜「镍 加工费」只返回铅/锌精矿加工费） |
| SI 3.1.1 海外硅矿产量 | `ID01445986` 广西**工业硅**产量(series空) | 29 | 否 | **知几无此指标 → 应标 C**（搜「硅石 产量 全球」只返回稀土/碳化硅/汽车产量） |
| ZN 3.1.1 海外锌矿产量 | `ID00299790` USGS**澳大利亚**产量 | 14 | 勉强 | `ID00299372` ILZSG：锌矿：产量：全球（月）✅ |
| SN 3.1.1 海外锡精矿产量 | `ID00300777` 云南**年鉴**产量 | 14 | — | `a10003082` SMM: 全球精锡产量（年）✅（锡精矿级知几仅中国口径） |
| SN 5.2/5.3 焊锡订单排产 | `ID01319734` 焊锡条**价格** | 3 | 否 | **知几无此指标 → 应标 C**（订单/排产类知几全线无覆盖） |

**结论**：7 个误配节点里，5 个其实**有真指标只是没搜到**，2 个确实知几无数据（镍精矿TC、海外硅矿产量）——后者本该标 C，被你填了。

---

## 五、执行步骤

```bash
# 1. 同步基线（强制，别基于旧 commit 开工）
git fetch origin && git rebase origin/main
python3 -c "import json; print('指标数:', len(json.load(open('data/indicators_v1.json'))['indicators']))"

# 2. 开工前自检
bash scripts/bootstrap_agent.sh

# 3. 改造脚本（新增 analysis/zhiji_match_v4.py，别覆盖 v3）
#    必须实现上面 8 条规则，尤其是规则 1/2/3 三道互斥

# 4. 只重跑 B 级（别动 A 级和 C 级）
#    从 v3 的 JSON 里筛 match_level=='B' 的条目，按新规则重判
python3 analysis/zhiji_match_v4.py --recheck-b-only

# 5. 自检：复用次数 Top10 必须逐条人工过
python3 -c "
import json, collections
for v in ['CU','AL','ZN','NI','SN','SI','LI']:
    d = json.load(open(f'analysis/zhiji_match/{v}_zhiji_match.json'))
    c = collections.Counter(m['zhiji_id'] for m in d['matches'] if m['match_level'] in ('A','B'))
    print(v, c.most_common(5))
"

# 6. 质量门禁（三道全绿）
python3 scripts/check_html.py && node scripts/verify_render.js && python3 scripts/reclaim.py

# 7. 更新 STATUS.md + push 分支（别 push main，等主脑 review）
git add analysis/zhiji_match/*.json analysis/zhiji_match_v4.py STATUS.md
git commit -m "[B] 知几匹配v4: B级900条重判(八概念互斥+产业链互斥+地域互斥+series非空+复用上限3) ..."
GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10" git push origin task/zhiji_match_v4
```

---

## 六、验收标准（主脑按这个打分）

| 项 | 达标线 |
|---|---|
| B 级条目数 | 应从 900 降到 500 以下（大量转 C） |
| 单一 ID 复用 Top1 | ≤3 次 |
| 八概念维度校验 | 目标/候选维度不相交 = 0 条 |
| series 非空 | A/B 级 verified=True 的条目，series 点数 ≥3 |
| 上表 5 个"有真指标"节点 | 必须全部命中正确 ID |
| 上表 2 个"知几无数据"节点 | 必须标 C + notes 写"需外部源" |

---

## 七、不要做的事

- ❌ 别动 A 级 547 条（已审过，全对）
- ❌ 别改 `data/indicators_v1.json`（那是主脑合的，你只出 JSON）
- ❌ 别用整句搜知几（"Mysteel国产锌精矿TC"这种 19 字会命中"精炼镍库存"）
- ❌ 别把图表排版短语当指标搜（"避免左右双轴超过2个"会被搜出"硅锰利润"）
- ❌ 别只看结果第 1 条（真指标常在 6-10 条）

---

## 八、关键网址（你要能自己访问到）

| 项 | 地址 |
|---|---|
| GitHub 仓库 | https://github.com/algo23-yunqingtian/framework-tree |
| 你的分支 | `task/zhiji_match_all` @ e7b4d31 |
| 主脑审计 | `docs/AUDIT_zhiji_match_20260907.md` |
| 线上看板 | https://algo23-yunqingtian.github.io/framework-tree/ |
| 知几 API | `~/.hermes/scripts/zhiji_api.py`（`search` / `series <id> <start> <end>`） |
| 同花顺问财 | https://www.iwencai.com/chat （需登录态，本任务不需要你访问） |
| 已注册指标 | `data/indicators_v1.json` |
