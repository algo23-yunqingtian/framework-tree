# 监督者交接文档 v2 · Windows agent(CU/AL/NI/SN)产出验收 + framework-tree 待办

> 角色: 监督者(本 agent) | 续接: 2026-09-02 第2轮 | 基于: v1(HANDOVER_SUPERVISOR_20260902.md)
> 范围: Windows 侧四金属指标纠正成果验收 + 实时数据架构决策 + 主脑侧未闭环项
> 仓库: github.com/algo23-yunqingtian/framework-tree

---

## 0. 本轮回响结论(速记)

| 块 | 结论 |
|---|---|
| Windows agent 自报"做完了" | **部分属实**:110条指标已注册+24板块HTML齐全,但格式未对齐主脑、同花顺→知几存在伪命中未清、P1未验证是否merge进main |
| 实时数据架构 | **已定路A**(GitHub Pages + 每日cron推data.json),与lithium/nickel同构 |
| 主脑侧硅锂 R1-R6 | **仍未修**(v1遗留,未闭环) |
| 红线 db.bak | **已清**(本轮d89a431) |

---

## 1. Windows agent 产出核查(2026-09-02 实测)

### 1.1 分支状态
- 分支: `origin/indicator-correction-win`,最新 `2ad8ed6 [Txx] CU/AL/NI/SN correction: 质量修正+补缺+目录重构+P1注册110指标`(2026-09-02 12:09)
- 自 main 起 5 个 commit,改 102 个文件(+32859 / -11436 行)
- **注意**: 该分支**未 rebase 最新 main**(其基线停在五金属建页阶段),merge 时会有冲突面

### 1.2 P1 注册进 indicators_v1.json — ✅ 已做(数量对,质量待验)
| 维度 | main | Windows分支 |
|---|---|---|
| 指标数 | 888 (vv3.46) | **919** (vv3.46) |
| 新增 | — | **+110** |
| 品种分布 | — | cu=30 / al=38 / ni=31 / sn=11 |
| `_origin` 标记 | — | **110/110 全标** ✅ |

### 1.3 24板块 HTML 页面 — ✅ 齐全(对比缺口清单已全部补上)
按板块统计(cu/al/ni/sn 各 7 板块 = 24板块,均覆盖):
- **cu**: 2(8) 3(10) 4(6) 5(2) 6(3) 7(4) 总42页
- **al**: 2(7) 3(9) 4(7) 5(4) 6(4) 7(3) 总34页
- **ni**: 2(8) 3(11) 4(7) 5(5) 6(5) 7(5) 总41页
- **sn**: 2(8) 3(10) 4(7) 5(5) 6(6) 7(5) 总41页
- 合计 **158 页**,分支总HTML 317页 vs main 320页

> v1 缺口清单(CU 5.1-5.3/6.1-6.4/7.1-7.3, AL 2.1-2.6/5.1-5.3/7.1-7.3, NI 6.1-6.4)对照: **已全部有对应板块页** ✅

### 1.4 质量返工 4 项 — 部分已修,部分存疑
| 返工项 | 状态 | 证据 |
|---|---|---|
| CU 价格信号 18指标14个B级伪命中(全指ID01659225) | ✅ **已清** | 全库grep ID01659225 = **0处** |
| NI 价格信号膨胀(要求≤20) | ✅ 达标 | NI含"价格"=**18**个 |
| AL 供给/进出口 100% A级存疑 | ⚠️ **未独立抽查**,待验 |
| 4份文件规范不达标(缺独立prompt原文) | ✅ **已补** | 每品种6份对照表 + 6份_prompt.txt + 6份_zhiji_search.json + 同花顺回复,齐全 |

### 1.5 自查机制 — ✅ 脚本齐全且产物完整(但有疑点)
- 14 个 step3_*.py 脚本(verify/judge/register/fetch/finalize/fix_nodes 等),全部 09-02 12:09 运行过
- 分析产物齐全: search_results(4.8MB)、verdict_rule(4.4MB)、verify_summary(283KB)、register_plan(248KB)、final(460KB)
- **两份最终报告**:
  - `step3_report.md`(CU/AL): CU 129指标→B级73, AL 193→A级96+B级28, **AL A级靠子代理人工判定**
  - `step3_report_5m.md`(ZN/NI/SN/SI/LI): 1099指标→B级322(29%),14项知几完全无序列

⚠️ **自查可信度疑点**(待下一轮复核):
1. `step3_verify_summary.json` 的 CU/AL 内部是**字符串数组**(指标名列表),**不是结构化通过/失败判定** — 看不出每条指标的最终 A/B/C 等级和命中率,自查是否真逐条过审存疑
2. `step3_report.md` 的 Tier A 96条(AL)依赖"子代理逐条人工判定",未留存判定记录细节,可追溯性弱
3. **自查脚本与主脑侧 step3 脚本命名完全相同**(step3_register.py 等) — 疑似 Windows agent 复制了主脑早期脚本,可能版本落后于 main 的修正版

### 1.6 格式是否对齐主脑 — ❌ 部分未对齐
| 要求 | 实际 |
|---|---|
| 目录 `correction/{品种}/` | ✅ 对齐 |
| 文件名后缀 `_correction_` | ⚠️ **混合**:新对照表用 `_correction_20260902.md` ✅,但同花顺回复用 `_iwencai_reply.md`(无后缀)、旧版遗留 `_correct_20260902.md`(**错拼**)⚠️ |
| 每板块4份文件(对照表+知几json+iwencai回复+prompt原文) | ✅ 齐全 |
| **关键不一致**:同花顺"对话状态/回复" | ⚠️ 部分板块**无 iwencai_reply**(如 cu_价格信号 只有2份同花顺回复对应6份对照表) — 说明有些对照表是直接搜知几、没走同花顺发散,与主脑"先发散后验证"流程不一致 |

### 1.7 ⚠️ 与主脑流程一致性的核心风险
- 主脑规定:同花顺发散 → 概念指标 → **SMM/Mysteel全称** → 知几空格搜全称关键字 → 人工比对(2026-09-01转向)
- Windows agent 产物里 `iwencai_reply` 文件数 < `correction` 对照表数,暗示**部分指标跳过了同花顺发散**,直接进了知几验证
- **P1 注册是否用了修正后的命名规范**(`re.sub` 避主脑遗留bug):脚本 `step3_register.py` 命名 `ni_/cu_/al_/sn_<节点短码>_<slug>`,需实测确认是否踩了 version 解析bug

### 1.8 是否进 228 子页 + chip 对应 — ❌ **尚未**
- Windows 分支的 158 页 HTML 是**全新建的**(cu/al/ni/sn 板块页),main 侧原有 320 页(含铅锌旧页)
- **228 子页节点**是 framework-tree 的总盘子;Windows 这 158 页需要被:
  1. `index.html` 的 PAGE_MAP / OVERVIEW_MAP 接入(目前 main 的 index 还没有 cu/al/ni/sn 的新映射键)
  2. 240 个 chip(用户提到的)与子页一一对应
- **当前状态:分支 HTML 已建,但主站导航(chip→页面)的映射尚未合并** ❌

---

## 2. 实时数据架构 — 已定路A

**决策**: GitHub Pages 静态 + 每日 cron 推 `data.json`(与 lithium / nickel / macro 三看板同构)
- 页面加载时 `fetch(data.json)`,当天首开拉最新,cron 每日刷新
- **不采用路B**(常驻 Flask api_server),用户明确选A
- **待办**: framework-tree 现有 228 页数据焊死在 `__data` 里,需迁到"页面读 data.json" — **较大重构,等 agent 都收工、数据层稳定后再动**
- 本地缓存 `api_cache.db` 已是最新(9月2日),刷新管道可用

---

## 3. 主脑侧 硅锂 R1-R6 返工 — ❌ 仍未闭环(v1遗留)

| # | 问题 | 实测 |
|---|---|---|
| R1 | li_3_1_5 挂ID01349545(应为7.2毛利) | ⚠️ 待复查 |
| R2 | li_3_1_5 硬编码229点__data,不从缓存拉 | 🔴 仍3处__data |
| R3 | index缺li_3_2_1/si_3_2_1映射键,按钮打不开 | 🔴 映射=0 |
| R4 | 锂供给3.2.1仅1指标 | ⚠️ 待补 |
| R5 | si_3_2_1串入多晶硅/硅锰 | 🔴 仍在 |
| R6 | 41页页脚v3.45 vs 库v3.46 | 🔴 未同步 |

主脑本地 main 比远端多2个commit(未push),正处硅锂返工中。

---

## 4. 本轮已完成
- ✅ 红线 `api_cache.db.bak_step3` 清除(commit d89a431)
- ✅ Windows agent 产出核查(见§1)
- ✅ 实时架构决策定案(路A)

---

## 5. 下一轮待办(按优先级,用户问题已标记)

| # | 待办 | 对应你的问题 | 优先级 |
|---|---|---|---|
| T1 | **抽查Windows新增110条指标质量**:AL 100% A级存疑、CU伪命中是否真清、NI价格收敛是否合理 | "有没有像之前说的那种问题" | 🔴高 |
| T2 | **核实自查可信度**:step3_verify_summary.json 无结构化判定、Tier A人工判定无记录、脚本是否落后主脑版本 | "自救自查机制有没有在进行/做到哪了" | 🔴高 |
| T3 | **Windows分支merge前**:rebase最新main(基线旧,有冲突)+ 跑三道门禁(check_html/verify_render/reclaim) | "是否可以做chip和228子页对应" | 🔴高 |
| T4 | **补index.html PAGE_MAP**:cu/al/ni/sn 158页接入导航 + 240 chip↔子页对应 | "240个chip和228子页对应" | 🟠中 |
| T5 | **格式归一**:统一`_correction_`后缀(修`_correct_`错拼)、补齐缺失的iwencai_reply | "格式修改有没有和爱马仕保持一致" | 🟠中 |
| T6 | **主脑侧R1-R6返工**:修index缺键→li_3_1_5→si_3_2_1归属过滤→补锂指标→页脚v3.46→跑门禁 | v1遗留 | 🔴高 |
| T7 | **数据刷新**:等主脑+Windows都收工后,refresh_cache+重建HTML+push,让Pages数据到最新 | "感觉没更新到最新" | 🟠中 |
| T8 | **实时架构重构(路A)**:页面改读data.json+每日cron — **数据层稳定后再做** | "每天首次点开自动更新" | 🟡后 |
| T9 | 格式错拼审计:`_correct_` vs `_correction_`全仓grep | T5子项 | 🟡低 |

---

## 6. 关键路径/命令(复用)
```bash
cd /home/ubuntu/framework-tree
# Windows分支核查
git log origin/indicator-correction-win --oneline
git diff --stat main...origin/indicator-correction-win
# 指标数核验
python3 -c "import json;d=json.load(open('data/indicators_v1.json'));print(len(d['indicators']),d.get('version'))"
# 门禁
python3 scripts/check_html.py && node scripts/verify_render.js && python3 scripts/reclaim.py
# 缓存刷新(安全,不碰HTML)
python3 scripts/refresh_cache.py
```

---

## 7. 风险提示(跨机协作)
- ⚠️ 本地 main 比远端多2个commit(未push),任何操作前先 `git status` 确认主脑有没有推送
- ⚠️ Windows 分支基线旧,**不可直接 merge**,需先 rebase main
- ⚠️ 主脑正处于硅锂返工,避免同时动 li/si HTML 和 index.html
- ⚠️ 数据刷新(重建HTML+push)与 agent 在建页有冲突 — **等两方都收工再做**