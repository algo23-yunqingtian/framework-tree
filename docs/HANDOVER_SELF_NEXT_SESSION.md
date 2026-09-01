# 本会话自留交接文档（下一轮用）

**时间**: 2026-09-01 22:00  
**会话主题**: 8 品种指标纠正协作启动  
**上下文**: 本会话即将超限，需开新会话继续

---

## 已完成

1. ✅ 锌·供给端 5 节点（3.1.1-3.1.5）同花顺纠正完成
   - 产物：`translation-workspace/correction/ZN_supply_correction_20260901.md`
   - 旧映射 30 条，旧版正确率 < 10%，新版命中率 70%（21/30）
   - 9 项知几缺项已确认（冶炼利润、开工率、锌焙砂、再生锌利润等）

2. ✅ 旧分词脚本 `step2_zhiji_verify.py` 分词函数已彻底删除

3. ✅ 方法论文档 `docs/METHODOLOGY_INDICATOR_CORRECTION.md` 已写

4. ✅ Windows agent 任务卡已写：
   - `docs/HANDOVER_WINDOWS_AGENT_FULL.md`（完整版，含 JS 操作代码）
   - `docs/HANDOVER_WINDOWS_AGENT.md`（旧版，已废弃）

5. ✅ 任务分配表 `docs/TASK_ALLOCATION_8VARIETIES.md` 已写
   - 本机：铅/锌/硅/锂 109 节点（锌供给已完）
   - Windows：铜/铝/镍/锡 110 节点

6. ✅ 4 份文档已 git commit 到 `translation-workflow` 分支

---

## 下一步（新会话继续）

### 本机要做的

**优先级从高到低**：

1. **锌·库存/需求/进出口/成本/价格信号** — 供给已完，其余 20 节点待纠正
   - 用同花顺对话框（已打开）逐板块发 prompt
   - 每板块 5-8 节点，一个 prompt 一批
   - 产物路径：`translation-workspace/correction/ZN/`

2. **铅·全板块** — 老牌正确率高，但仍需同花顺验证
   - 铅没有 audit 文件，需要从 `pb_*_*.html` 页面反推概念指标

3. **硅·全板块** — step2 有，待纠正

4. **锂·全板块** — step2 有 + 需求/进出口/成本缺页需补

### Windows agent 要做的

- 等用户把 `HANDOVER_WINDOWS_AGENT_FULL.md` 的内容复制给它
- 它负责 铜/铝/镍/锡 110 节点
- 产物推到 `indicator-correction-win` 分支

### 关键决策点（待用户确认）

1. **是否需要等 Windows agent 开始后再开工？** — 建议并行，不等
2. **铅的"老牌正确率"是否相信，还是需要全纠正？** — 用户已确认"铅也要纠正"
3. **锂缺的 3 板块（需求/进出口/成本）是否先用同花顺发散再纠正？** — 建议是

---

## 同花顺对话状态

- 当前对话：已用 5 轮（锌供给 5 节点），浏览器还开着
- 下次继续：直接在同一对话里追加 prompt，不要开新对话
- 注意：同花顺有 90 秒冷却期

---

## 关键文件索引

| 文件 | 用途 |
|-----|-----|
| `docs/METHODOLOGY_INDICATOR_CORRECTION.md` | 方法论（含 JS 操作代码） |
| `docs/TASK_ALLOCATION_8VARIETIES.md` | 任务分配表 |
| `docs/HANDOVER_WINDOWS_AGENT_FULL.md` | Windows agent 任务卡 |
| `translation-workspace/correction/ZN_supply_correction_20260901.md` | 锌供给纠正对照表 |
| `translation-workspace/audit/{品种}/audit_{板块}.md` | 各品种同花顺审计原文 |
| `translation-workspace/mapping/{品种}/step2_match_{品种}.json` | 各品种旧映射（已知大部分错） |