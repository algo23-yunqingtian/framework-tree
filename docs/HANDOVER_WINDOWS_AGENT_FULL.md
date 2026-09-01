# Windows Agent 完整任务卡

**任务**: 8 品种指标纠正协作 — 你负责铜(CU)/铝(AL)/镍(NI)/锡(SN) 共 110 节点  
**主脑**: 本机（Linux），负责铅/锌/硅/锂  
**开始时间**: 2026-09-01  
**分支**: `indicator-correction-win`  
**产物目录**: `translation-workspace/correction/{品种}/`

---

## 一、先读这 3 个文件

全部在 GitHub `algo23-yunqingtian/framework-tree` 的 `docs/` 目录下：

1. **`docs/METHODOLOGY_INDICATOR_CORRECTION.md`** — 方法论（必先知）
2. **`docs/TASK_ALLOCATION_8VARIETIES.md`** — 任务分配表（看你要做哪些）
3. **`docs/HANDOVER_WINDOWS_AGENT.md`** — 本文件（详细操作步骤）

---

## 二、克隆仓库 + 建分支

```powershell
cd C:\projects
git clone https://github.com/algo23-yunqingtian/framework-tree.git
cd framework-tree
git checkout -b indicator-correction-win
```

**注意**：你的 `translation-workspace/` 目录下还没有 `correction/` 子目录，自己建。

---

## 三、你的 4 个品种 × 全板块

| 品种 | 板块 | 节点数 | 文件位置 |
|-----|-----|-------|---------|
| 铜(CU) | 价2/供3/库4/需5/进出6/成本7 | 27 | `mapping/CU/step2_match_CU.json` |
| 铝(AL) | 同上 | 28 | `mapping/AL/step2_match_AL.json` |
| 镍(NI) | 同上 | 28 | `mapping/NI/step2_match_NI.json` |
| 锡(SN) | 同上 | 27 | `mapping/SN/step2_match_SN.json` |

**每个 JSON 文件的结构**：
```json
{
  "3.1.1|全球铜矿产量": {
    "subnode": "3.1.1",
    "chart": "全球铜矿产量",
    "name": "全球铜矿产量",
    "hit_id": "xxxxxx",
    "hit_name": "可能错的命中名"
  }
}
```

**读取方式**：用 Python 按 `subnode` 前缀分组，每个板块 5-8 个节点一批。

---

## 四、每个节点 4 步工作流

### Step 1: 准备数据

对每个节点，从 JSON 里提取"概念指标名"和"旧 zhiji_id + 旧命中名"。

### Step 2: 发 prompt 给同花顺

**打开 Chrome（已登录同花顺）→ 访问 https://www.iwencai.com/chat**

**第一轮 prompt**（纠正旧的）：

```
不是不是，你帮我看看这里是关于金属{品种}{板块}的指标，你看看哪些是不相关的？

| 概念指标 | 旧映射 | 旧命中 |
|---|---|---|
| {name1} | {hit_id1} | {hit_name1} |
| {name2} | {hit_id2} | {hit_name2} |
...
```

**同花顺第一轮通常只给方向不给具体名** → **必须发第二轮**：

```
好，继续。再帮我看看这里是关于金属{品种}{板块}的指标，你帮我给出每个指标对应的SMM有色网和Mysteel钢联的官方全称、数据频率和单位。

| 我需要的指标 | 说明 |
|---|---|
| {指标名1} | {用途说明} |
...

请按表格输出：
| 指标 | SMM有色网官方全称 | Mysteel钢联官方全称 | 数据源 | 频率 | 单位 | 备注 |
```

**两次 prompt 之间等 ≥ 90 秒**（同花顺限流）。

**每轮等生成完成后**，检查 body 是否含"内容由AI生成，不构成投资建议"，然后复制回复全文保存到文件：

```
translation-workspace/correction/{品种}/{品种}_{板块}_{节点}_iwencai_reply.md
```

### Step 3: 搜知几验证

同花顺给的全称压缩成 2-3 个核心词再搜：

```bash
python3 ~/.hermes/scripts/zhiji_api.py search "{压缩搜索词}" all 10
```

**SMM 和 Mysteel 平权**：两个来源的 zhiji_id 都记录，不默认优先用哪个。

保存搜索结果到：
```
translation-workspace/correction/{品种}/{品种}_{板块}_{节点}_zhiji_search.json
```

### Step 4: 写对照表

每个板块 5-8 个节点做完后，汇总写一份 markdown：

```
translation-workspace/correction/{品种}/{品种}_correct_{板块}_{日期}.md
```

**表格格式**：

```markdown
| # | 概念指标 | 旧映射 | 旧命中 | 同花顺SMM全称 | 同花顺Mysteel全称 | 知几SMM zhiji_id | 知几Mysteel zhiji_id | 频率 | 单位 | 备注 |
|---|---------|--------|-------|------------|---------------|----------------|-------------------|------|-----|-----|
```

---

## 五、关键坑（必读）

1. **Chrome 必须用已登录同花顺的浏览器**，掉线需重新登录
2. **两次发送间隔 ≥ 90 秒**（实测，45 秒不够）
3. **prompt ≤ 10000 字**（编辑器硬上限）
4. **等"内容由AI生成，不构成投资建议"页脚**才算完成（不要用 setTimeout 等太久）
5. **同花顺偶有拒答**（返回"我是同花顺研发的投资助理问财..."）→ 等 5 分钟重发，还不行就标记卡点
6. **知几搜不到不要硬凑** → 标注"知几无数据，需外部源补充"
7. **SMM 和 Mysteel 两个来源平权记录**，不要只取第一个

---

## 六、每日汇报

每完成一个板块，发一条：

```
【{品种}·{板块}】完成
- 同花顺纠正：X 条指标，Y 条剔除
- 知几验证：命中 Z 条，缺项 W 条
- 产物文件：translation-workspace/correction/{品种}/{品种}_correct_{板块}_{日期}.md
```

---

## 七、完整个体操作示例（铜·供给·3.1.1）

1. 读 `step2_match_CU.json`，找到 subnode="3.1.1" 的所有条目
2. 整理成表格：

```
| 全球铜矿产量 | ID01001563 | 锌精矿：产量：中国 |
| 海外铜矿TC | ID01510737 | 铜精矿：50%Zn：加工费：白银 |
...
```

3. Chrome → iwencai.com/chat → 注入 prompt A → 发送 → 等 30 秒
4. 复制回复，保存
5. 等 90 秒 → 注入 prompt B → 发送 → 等 30 秒
6. 复制回复，保存
7. 从回复里提取每个指标的 SMM 全称和 Mysteel 全称
8. 压缩搜索词，逐条搜知几
9. 汇总写对照表

---

## 八、git push

每个板块做完后：

```powershell
cd C:\projects\framework-tree
git add translation-workspace/correction/
git commit -m "[B] {品种} {板块} 指标纠正"
git push origin indicator-correction-win
```