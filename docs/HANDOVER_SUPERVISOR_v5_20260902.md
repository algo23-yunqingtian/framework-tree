# 监督者交接文档 v5 · 全量指标丢弃检测 + 季节粒度 bug + 重上线计划

> 角色: 监督者(主脑) | 2026-09-02 第5轮 | 基于: v4
> 本轮成果: ①全量丢弃检测完成(8品种×30节点≈198份divergence) ②确认季节图粒度bug根因 ③重上线计划
> **先处理⚠️安全事件**: 工作区有未完成 merge

---

## 0. 🚨 最高优先级: 工作区处于未完成 merge 状态

**实测**: `.git/MERGE_HEAD` 存在, 时间 2026-09-02 16:36;`git merge origin/indicator-correction-win` 已启动但**冲突未解决**;`data/indicators_v1.json` 含 `<<<<<<< HEAD` 标记, **JSON 已损坏**。win 分支最新 `f73bccb v3.48`(比 main 的 888 v3.46 新)。

**为什么发生**: 疑似 Windows agent 刚 push `f73bccb` 后有人(可能它在另一会话)对本机 checkout 执行了 merge, 未完成。

**处理建议(用户拍板)**:
- 方案A: `git merge --abort` 回到干净 main(丢弃已 staged 的 162 个 win correction 文件, 但文件在 win 分支仍在)
- 方案B: 手动解决 indicators_v1.json 冲突(HEAD v3.46 888 条 vs win v3.48 930 条), 合并后 commit
- **风险**: 直接 merge win 分支 = 全量重建 317 页冲突 + 删 79 条指标(v3 结论) — **不建议方案B直接合, 应先 abort 再走增量注册**

---

## 1. 全量丢弃检测结果(核心发现)

**方法**: 解析 198 份 `divergence_*.md`(同花顺实际推荐) → 概念指标提取 → 与 `indicators_v1.json`(HEAD v3.46 888条)名称/`_origin` 匹配。

```
TOTAL: 推荐 3196 概念指标 / 未注册 1211 (38%)
[AL] 无 divergence 记录(0)   ← 铝走的是别的流程
[CU] 推荐156 未注册124 (79%)   ← 最严重
[ZN] 推荐654 未注册264 (40%)
[NI] 推荐792 未注册296 (37%)
[SI] 推荐587 未注册205 (35%)
[SN] 推荐633 未注册209 (33%)
[LI] 推荐374 未注册113 (30%)
```

**⚠️ 注意**: 这个数字是"概念名粗匹配", 含 3 类**合理未注册**(不算真丢弃):
① 知几确实无序列(如 LME 锂/工业硅期货价根本不存在) ② 多月差/期限结构/占比等**衍生指标**(同花顺爱列但无独立序列) ③ 已入备用库的跨类指标(归属优先规则)。
**真丢弃估算**: 约 2/3 是合理未注册(①+②), 1/3(≈400 条)是**建页环节漏注册的可得指标**——典型就是锂 3.2.1 的 4 工艺产量(a12715549/48, ID01707134/137/140/ID02226352 全部有 31-80 点序列但没上图)。

**代表性必须补的**(已逐条验证有数据, 见 v5 会话实测):
- LI: 电池级/工业级碳酸锂产量、分原料(辉石/云母/盐湖/回收)月度+周度
- CU: 铜杆开工率/原料库存天数、LME/COMEX/SHFE 三所库存、电解铜检修量
- ZN/NI/SN/SI: 各节点开工率/检修量/排产计划/分国别进口(按品种对应)

---

## 2. 季节图粒度 bug(用户发现, 确认属实)

**根因**(`scripts/chart_kits.py:136-140 _detect_gran`): 只分两档——近120点平均间隔 <3天 → 日度(365类目); 否则一律月度(12类目)**周度数据被注释明确"归入月度近似"**。

**后果**: 周度(如锂周产量、社库周度)、部分半周数据画的季节图横轴是 12 个月, 把周度波动压平成月度均值, 丢失季节性细节。用户看到的"所有季节图都是月度" = 这个 bug。

**修复方案(新对话做)**:
1. `_detect_gran` 三档化: `daily(<3天) / weekly(3-10天) / monthly(>10天)`
2. 新增 `__seasonalizeByWeek`(52 周类目, 按 ISO 周年周对齐)+ 周度调色板
3. `chart_kits.py` 季节生成分支: daily→ByDay, weekly→ByWeek, monthly→ByYear
4. `verify_render.js` 兼容 52 类目长度检查(当前按月/日硬编码)
5. 重建全部受影响页面(周度数据页), 门禁全绿后 push
   **⚠️ 影响面**: 需先统计哪些页含周度数据(scan `freq: "weekly"` in indicators + HTML), 估算 ~30-60 页

---

## 3. 重上线计划(按优先级)

| # | 任务 | 步骤 | 预估 |
|---|---|---|---|
| P0 | **解 merge 冲突**(abort 恢复 clean main) | 用户拍板方案A/B → `git reset` 后验证 indicators 可解析 | 10min |
| P1 | **修季节粒度 bug** | chart_kits 三档化 + ByWeek + verify_render + 重建周度页 | 2-3h |
| P2 | **补锂 3.2.1 产量细分**(示范) | 注册 10 个已验证 ID(4工艺×月/周+电池/工业级) → 重建 li_3_2_1 7图 | 1h |
| P3 | **全量补丢弃指标** | 从 divergence 提取"有序列可得"指标清单 → 批量注册 → 重建对应节点页 | 2-3天分批 |
| P4 | **快速上线机制**(用户需求: 改指标秒上线) | 建 `regen_all.sh`: refresh_cache → 门禁 → push; 改指标只改 `indicators_v1.json` 一行 → 跑脚本 | 1h |
| P5 | 数据快照刷新(8/31→9/2) | 拉数据+重建+push | 1h |

---

## 4. 关键命令存档

```bash
# merge 状态确认
cd /home/ubuntu/framework-tree && ls .git/MERGE_HEAD && git status | head
# abort(方案A)
git merge --abort && python3 -c "import json;d=json.load(open('data/indicators_v1.json'));print(len(d['indicators']))"
# 弃检测重跑(从 HEAD/win 版本读, 不碰工作区)
git show HEAD:data/indicators_v1.json > /tmp/ind_head.json
python3 /tmp/scan_drops.py
# 季节粒度检测: 数 HTML 里周度页
grep -l 'weekly' *_*.html | wc -l
```

---

## 5. 文件状态

- 本文件: `docs/HANDOVER_SUPERVISOR_v5_20260902.md`
- 复用脚本: `/tmp/scan_drops.py`(丢弃检测)、`/tmp/verify_li_ids.sh`(ID序列验证)
- ⚠️ `data/indicators_v1.json` 当前损坏(冲突标记), 任何读它的工具都会失败, 先解 P0
- 检测脚本从 git 历史读版本, 未污染工作区; 已写 v3/v4/v5 三份交接文档