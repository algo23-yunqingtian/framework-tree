# 交接文档 v6：硅锂对照表建页后的质量问题诊断（待新会话系统修复）

**生成时间**: 2026-09-02
**HEAD**: origin/main = `904b42a`
**一句话**: **硅锂对照表 P0–P3 已闭环（12 页 274 图，门禁全绿），但用户实测发现**多类指标映射/频率/数据质量问题**——本轮不解决，下轮按此清单逐项诊断+系统修复**。

---

## 0. 上一轮已完成（不要重做）

| 任务 | 状态 | 关键产物 |
|---|---|---|
| P0 解析脚本修复 | ✅ | `scripts/parse_correction_register.py` v2，SI 57 / LI 121，空 ID 行 0 |
| P1 ID 注册 | ✅ | 79 条新增入 indicators_v1.json，888 条，v3.46 |
| 遗留 bug 修复 | ✅ | `step3_si_li_register.py` 顶层 version 数字解析 |
| P2 建页 | ✅ | 12 页 / 274 图（SI 6 页 135 图 + LI 6 页 139 图） |
| P3 门禁 | ✅ | check_html 223/223 + verify_render 224/224 + reclaim 12/0 |
| 推送 | ✅ | `904b42a` on origin/main |

---

## 1. 用户反馈的质量问题（本轮不修，下轮系统诊断）

### 【问题 A】碳酸锂 3.1.5 加工费节点 —— 指标映射错 + 频率解析错

**症状**：
- 用户看到 LI 3.1.5 页面中，预期对应"碳酸锂加工费"的图表，实际显示的是**"生产毛利"**（hit_name 不对）
- 图表 note/标题把该指标的 **freq 字段错误渲染**（用户描述"显示是轴周数据，但是画在图里就变成阅读数据"——疑似"读周数据"或 freq 值非预期）

**怀疑根因**（待下轮逐条诊断）：
1. `correction_register_plan.json` 的 LI 3.1.5 行**概念→ID 对应错了**（"生产毛利"的 zhiji_id 被填进"加工费"concept）
2. `fill_plan_cache.py` 写入缓存时 `freq` 字段未对齐（可能读 indicators_v1 拿到的 freq 是空/错，回退用了 plan 里不准确的 freq）
3. 知几系列返回的 `frequency` 字段本身异常（如 `"读周数据"` 或 `"周"` 被误读）

**优先排查**：
```
python3 -c "
import json
plan=json.load(open('analysis/iwencai/correction_register_plan.json'))
for r in plan['LI']['3.1.5'].get('rows',[]):
    print(json.dumps(r, ensure_ascii=False, indent=2))
"
```
→ 看 3.1.5 的 rows 里 concept/ids 是不是真对应"加工费"。

---

### 【问题 B】碳酸锂单节点指标数量偏少

**症状**：用户说"他这个指标应该也是会推荐更多的应该不止一个指标吧"——单节点只有 1-2 个指标，密度不够。

**怀疑根因**：
1. `sync_plan_to_mapping.py` 只同步 plan 里**plan 新行对应的 smm_id/mysteel_id**，plan 本身行就少（同花顺发散阶段给的少，或被解析脚本过滤掉）
2. `parse_correction_register.py` 解析 markdown 时把某些列/行丢掉了
3. 新 ID 在缓存里空数据 → build_translation 自动过滤（`MIN_POINTS=8`）

**下轮动作**：
- 对比旧 SI 3.2.1 页面（同花顺推荐 10+ 条 → 页面 3 图）vs 新 LI 3.x 页面，量化差距
- 看 plan 原始行 vs 页面最终图表数，找哪个环节在丢

---

### 【问题 C】LI 3.2.1 按钮点不开（页面渲染/跳转故障）

**症状**：工业硅 3.2.1 页面能打开正常，碳酸锂 3.2.1 页面**按钮点击无响应 / 页面空白**。

**怀疑根因**：
1. `li_3.html` 中 3.2.1 板块的 chart 容器/cid 生成异常（可能该节点 0 图被过滤后 HTML 生成出错）
2. 面包屑 nav 或子节点跳转 JS 报错
3. `build_translation.py` 对某 LI 节点 kept=0 时跳过了，但 `verify_render` 的 PAGES 注册里还有 `li_321` → 注册指向了不存在的页面

**优先排查**：
```
grep -n '3.2.1\|li_321' scripts/check_html.py scripts/verify_render.js
grep -n '3.2.1' li_3.html | head -10
```

---

### 【问题 D】SI 3.2.1 混入不相关商品指标

**症状**：硅 3.2.1 页面里出现了"多晶硅产量"、"产能利用率"、"规模开工率"等**不相关商品**（多晶硅 ≠ 工业硅 / 规模不明），跨品种污染。

**怀疑根因**：
1. 同花顺发散阶段就推荐错了（把多晶硅的指标混入工业硅节点）
2. `step3_5m_judge.py` 六重校验（品种词命中）**漏检了"多晶硅"≠"工业硅"的区分**
3. `sync_plan_to_mapping.py` 没有做品种语义校验（直接把 plan 行同步进 mapping）

**下轮动作**：
- 对比 SI 3.2.1 页面里每个图的 `hit_name`，列出哪些是"多晶硅"、哪些是"工业硅"
- 回溯 plan 里 SI 3.2.1 的 rows → 看是同花顺给的还是映射时串台

---

## 2. 问题性质分类

| 问题 | 环节 | 是否系统性 |
|---|---|---|
| A 指标映射错 | plan 生成 / ID 对应 | ⚠️ 单点但影响建页语义 |
| A freq 解析错 | 缓存写入 / 页脚渲染 | ⚠️ 可能影响所有新页 |
| B 单节点指标少 | plan 行密度 / 过滤 | ⚠️ 可能影响所有新页 |
| C LI 3.2.1 打不开 | build / JS | 🔴 功能性 bug |
| D SI 3.2.1 混入不相关商品 | 发散 / 校验 / 同步 | ⚠️ 系统性风险 |

**结论**：A/D 大概率不是个例，而是**从同花顺发散到建页全链路**都缺一次"品种语义校验 + 频次强类型化"关卡。下轮应做**系统诊断 → 写校验脚本 → 批量修复**。

---

## 3. 下轮诊断计划（建议）

### 3.1 单点问题定位（快）

对每个问题跑一次探查脚本，产出"这个页面对应 plan 的哪几行 → 缓存里的哪几条 → 页面渲染的哪个 cid"：

```
# A
python3 -c "import json; d=json.load(open('analysis/iwencai/correction_register_plan.json')); [print(json.dumps(r,ensure_ascii=False)) for r in d['LI']['3.1.5']['rows']]"
sqlite3 scripts/api_cache.db "SELECT metric,name,freq FROM indicator_cache WHERE name LIKE '%毛利%' AND code='LI';"

# C
grep -n '3.2.1\|li_321' scripts/check_html.py scripts/verify_render.js
python3 -c "import json; d=json.load(open('translation-workspace/mapping/LI/step2_match_LI.json')); [print(k,v) for k,v in d.items() if '3.2.1' in k]"

# D
grep -n '多晶硅\|规模' si_3.html | head -20
```

### 3.2 系统性校验（慢但值得做）

写一个 `scripts/audit_si_li_quality.py`，批量扫描：
1. 遍历 SI/LI 每个页面 → 提取所有 `hit_name` + `freq` 显示
2. 对照 indicators_v1 的 `_origin` / `_nodes` / `_tier` 看**是否在正确节点**
3. 品种词校验（工业硅页是否出现"多晶硅"、碳酸锂页是否出现"磷酸铁锂"等串台词）
4. freq 字段合法性校验（是否出现非"日度/月度/年度"的值）
5. 输出"问题清单 JSON + 修复建议"

### 3.3 修复动作

根据审计结果：
- 单点映射错 → patch plan 对应行，重跑 `sync_plan_to_mapping.py --only <node>`
- 系统性串台 → 加品种词校验进 `sync_plan_to_mapping.py`（参照旧 `step3_5m_judge.py` 的品种词规则）
- freq 错 → patch `fill_plan_cache.py` 的 freq 拼装逻辑，重跑缓存

---

## 4. 当前工作区最终状态（下轮开工前必查）

```
HEAD: 904b42a = origin/main
git status: 干净
indicators_v1.json: 888 条, v3.46
api_cache.db: SI 32 verified + LI 43 verified + 107 plan-alt-id 填充（裸 ID metric）
新建脚本: scripts/fill_plan_cache.py / scripts/sync_plan_to_mapping.py
新建 HTML: si_2/3/4/5/6/7.html + li_2/3/4/5/6/7.html（12 页 274 图）
修改 HTML: si_2/3/4/5/6/7.html + li_2/3/4/5/6/7.html（原有）
```

### 下轮开工基线核验（强制）
```bash
cd /home/ubuntu/framework-tree && git fetch origin && git log --oneline -3
python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print('指标数:',len(d['indicators']),'版本:',d['version'])"
# 必须输出 888 / v3.46，少了说明基线旧
```

---

## 5. 关键教训（防止再犯）

1. **plan→mapping 同步缺品种语义校验**：`sync_plan_to_mapping.py` 直接照抄 plan，没有做 `step3_5m_judge.py` 六重校验那种"品种词命中"关卡 → 多晶硅串到工业硅页。**修复方向**：加一个 `reject_if_other_variety(hit_name, variety)` 过滤函数。
2. **freq 字段未强类型化**：plan 里 freq 是自由文本，缓存写入时没有枚举校验 → 异常值直接流到页脚。**修复方向**：在 fill/sync 时把 freq 规范化到 `{daily, monthly, yearly, weekly}` 四个合法值。
3. **build_translation --skip-series-check 副作用**：绕过了 /tmp/series_ok.json 的实测过滤，可能让"hit_id 在 indicators_v1 有 ID 但实际无序列"的假 ID 混进页面。**修复方向**：新 ID 拉缓存后重新生成 series_ok.json（填进去）。
4. **LI 3.2.1 打不开**：暴露了建页脚本对 kept=0 节点的容错问题。**修复方向**：`build_translation.py` 遇到 kept=0 时至少写一个占位空卡片（"该节点无数据"），而不是留一个坏按钮。

---

## 6. 验收清单（下轮收尾前全部打勾才算完成）

- [ ] 问题 A 定位+修复（LI 3.1.5 指标+freq 全对）
- [ ] 问题 B 定性（指标少是发散少还是过滤丢？+ 补救）
- [ ] 问题 C 定位+修复（LI 3.2.1 按钮可点开）
- [ ] 问题 D 定位+修复（SI 3.2.1 无跨品种污染）
- [ ] 系统性审计脚本 `scripts/audit_si_li_quality.py` 跑完
- [ ] 全量重新 build_translation（--skip-series-check 已废弃，重新生成 series_ok.json）
- [ ] 三道门禁全绿（应比 223/223 更高）
- [ ] STATUS.md 更新 + `[A-SI-LI-FIX]` commit push