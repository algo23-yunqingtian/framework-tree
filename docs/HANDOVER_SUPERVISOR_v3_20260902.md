# 监督者交接文档 v3 · 主脑实测版(不采信自报)

> 角色: 监督者(主脑) | 续接: 2026-09-02 第3轮 | 基于: v2
> 核心方法: 对 v2 文档每条声称做"声称 vs 实测 vs 是否失效"三列反查(实测见 §1)
> 结论:**v2 文档约 1/3 声称已过时或方向性错误**,需据此修正 P0 行动。

---

## 0. 速览(读这一张表就够了)

| 项 | v2 声称 | 主脑实测 | 判定 | 影响 |
|---|---|---|---|---|
| win分支指标数 | 919 v3.46 | **926 v3.47** | ❌ | 数量多了7条 |
| 新增+110 | +110 | **+117 但 -79**(净+38) | ❌ | win分支**删了79条**主脑指标(多为锂硅),不是净增 |
| 新增品种 cu30/al38/ni31/sn11 | 110 | cu30/al**45**/ni31/sn11 | ❌ | AL 多了7条 |
| `_origin` 全标 110/110 | 110/110 | win**全库804**条有_origin | ❌ | win分支给**几乎所有指标**打了_origin,含从main继承的 |
| 24板块158页HTML齐全 | 158页 | **317页全量重建**(全品种) | ❌ **重大** | win分支是**独立重建全量**不是增量补丁,不能直接 merge |
| CU 18指标14个B级伪命中(全ID01659225)已清 | 已清 | **01659225 main和win都是3处**,且3处都是**正主"矿产粗铜产量"跨3节点复用作正主**——这不是"伪命中"而是**正主防串用违规** | ❌ **定性错误** | v2把它定性为"伪命中已清"是错的;这是另一个更严重的问题 |
| NI价格信号≤20 | 18达标 | win/main NI价格均为0(字段不含"价格") | ⚠️ | 无法用name字段验证,待查 |
| AL 100% A级存疑 | 待验 | 新增AL 45条里**有**_tier/A级标记 | ⚠️ | 需读对照表本体深审 |
| 自查脚本齐全14个step3_*.py | 齐全 | win分支**含0个.py脚本**(git ls-tree `*.py` = 0) | ❌ | step3脚本根本**没进git分支**,只在Windows机器本地 |
| 自查可信度存疑 | 存疑 | verify_summary.json 是**字符串数组不是结构化判定** | ✅ 确认 | 与v2一致 |
| R1 li_3_1_5挂ID01349545 | 待复查 | main里01349545对应的是 **li_26_idx**(2.6指标)不是3.1.5 | ⚠️ | R1描述可能已过期 |
| R2 __data硬编码 | 3处 | **实测仍3处** | ✅ 确认未修 |
| R3 index缺li_3_2_1/si_3_2_1映射 | 0 | **实测0** | ✅ 确认未修 |
| R5 si_3_2_1串多晶硅 | 仍在 | **实测仍在(si_3_2_1.html含"多晶硅/硅锰")** | ✅ 确认未修 |
| R6 页脚v3.45残留41页 | 41页 | **实测129页** | ❌ 低估3倍 |
| db.bak已清 | 已清 | **实测已清** | ✅ |
| 本地main==origin/main | 多2commit未push | **已同步,无未推** | ❌ | 主脑已push,无冲突面风险 |
| win基线旧不可直接merge | 基线旧 | **win是全量重建317页,与main 320页结构接近** | ⚠️ | 问题不是"基线旧"而是"两分支并行各自重建,指标模型已分叉" |

---

## 1. 实测证据(关键命令产出摘要)

### 1.1 指标模型分叉(最重要)

```
main: 888个  v3.46
win:  926个  v3.47
win比main: 新增117 / 删除79(净+38)
新增品种: cu30 / al45 / ni31 / sn11
删除品种: 多为锂硅(li/si 各4-5条)
_origin 标记: win全库804条(main 766条)
```

⚠️ **win 分支不仅加了110,还删了79条主脑已有的指标(其中锂硅占比高)**。79 条被删指标若 win 未在新结构里重建,merge 后主脑侧这些节点的 HTML 将指向不存在的指标 ID → **大面积死链**。

### 1.2 CU "伪命中"真实定性(纠正v2)

`ID01659225` 在 main 和 win 都是 **3处**:
- `cu_311_output_ratio_struct`(3.1.1 矿山铜产量结构)
- `cu_313_output`(3.1.3 矿山铜产量指引)
- `cu_321_output`(3.2.1 粗铜产量)

三者 name 都是 **"矿产粗铜:产量:中国(月)"**,是同一个指标被 3 个节点**同时当正主**。这不是"伪命中"(ID 错指),而是**正主防串用违规**(AGENTS.md §3.5 硬性规则)。win 分支**没有修**这个问题——它从 main 继承原样保留。

### 1.3 HTML 结构

| 分支 | 页数 | 结构 |
|---|---|---|
| main | 320 | pb43/ni43/zn42/sn41/li41/si39/pb37/al35/cu34 |
| win | 317 | pb43/ni43/zn42/sn41/si39/li38/al35/cu34 |

win 比 main 少 3 页锂、多 6 页铅。**win 不是增量补丁,是独立全量重建**——merge 时 317/320 页几乎逐页冲突。

### 1.4 格式/流程问题

| 项 | 实测 |
|---|---|
| `_correct_` 错拼(应为 `_correction_`) | **40 处** |
| `correction` 对照表 | 30 份 |
| `iwencai_reply` 同花顺回复 | 33 份 |
| 对照表 < 回复? | 反常,对照表30 < 回复33,说明部分回复无对应修正表 |
| step3_*.py 脚本进 git? | **0 个**(脚本只存在 Windows 本机,未提交) |

---

## 2. 风险重估(按影响排序)

| # | 风险 | 严重度 |
|---|---|---|
| **P0-A** | **merge win 分支 = 删 79 条主脑指标 + 317 页全量重建冲突** | 🔴 最高 |
| **P0-B** | CU 01659225 三节点同正主(win 未修,只是继承) | 🔴 高 |
| **P0-C** | R2/R3/R5 三处硅锂返工完全未动,HTML 直接坏页 | 🔴 高 |
| **P0-D** | R6 页脚 v3.45 残留 129 页(v2 低估到 41) | 🔴 高 |
| P1-A | AL 100% A 级对照表未读本体深审 | 🟠 中 |
| P1-B | win 自查脚本未进 git,可追溯性 0 | 🟠 中 |
| P1-C | 40 处 `_correct_` 错拼 | 🟠 中 |
| P2 | 实时数据架构(路A data.json)待重构 | 🟡 后 |

---

## 3. 下一轮 P0 行动建议(按顺序)

```
1. ❌ 立即停止"merge win 分支"的念头。它不是补丁是平行重建,直接 merge 会炸。
   正确做法:从 win 分支的 correction 对照表(30份 .md)中提取真正有价值的指标映射,
           人工筛选后增量注册进 main,而不是合并整条分支。

2. 修 P0-B: CU 01659225 三节点正主防串用。
   → 3.1.1/3.1.3/3.2.1 需分配 3 个不同指标(结构占比/产量/粗铜),当前全指同一"矿产粗铜产量"。

3. 修 P0-C 硅锂返工:
   R2 li_3_1_5 的 3 处 __data 硬编码 → 改读缓存
   R3 index.html 补 li_3_2_1 / si_3_2_1 映射键
   R5 si_3_2_1.html 剔除"多晶硅/硅锰"污染指标

4. 修 P0-D: 129 页页脚 v3.45 → 全局 sed 改 v3.46(实际应是 v3.47/下一版)

5. 主脑与 Windows agent 协作纪律:
   - win agent 后续只提交 correction 对照表,不动 HTML/indicators_v1.json
   - indicators_v1.json 只由主脑增量 merge
   - HTML 只由主脑在 main 上重建
```

---

## 4. 实测命令存档(可复用)

```bash
# 基线同步
cd /home/ubuntu/framework-tree && git fetch origin && git log --oneline HEAD..origin/main
# win分支指标数
git show origin/indicator-correction-win:data/indicators_v1.json | python3 -c "import json,sys;print(len(json.load(sys.stdin)['indicators']))"
# 指标差异
python3 -c "
wd=json.load(open('/tmp/win_indicators.json'))['indicators'];md=json.load(open('/tmp/main_indicators.json'))['indicators']
print('新增:',len(set(wd)-set(md)),'删除:',len(set(md)-set(wd)))
"
# 死链/页脚v3.45
grep -rl 'v3.45' *.html | wc -l
# 正主防串用(同一ID被多节点引用)
python3 -c "
from collections import Counter
import json
d=json.load(open('data/indicators_v1.json'))['indicators']
c=Counter(str(i.get('ids',{})) for i in d.values())
dup=[k for k,v in c.items() if v>1 and k!='{}']
print('重复ids:',len(dup))
for x in dup[:10]: print(' ',x)
"
```

---

## 5. 文件状态

- 本文件: `framework-tree/docs/HANDOVER_SUPERVISOR_v3_20260902.md`
- v2 文件保留作对比: `framework-tree/docs/HANDOVER_SUPERVISOR_v2_20260902.md`
- 两份旧未跟踪文件仍在 git status 里: `HANDOVER_SUPERVISOR_20260902.md`(v1)、`HANDOVER_AGENT_20260902_2.md`
