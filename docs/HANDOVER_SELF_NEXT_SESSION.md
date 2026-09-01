# 本会话自留交接文档 v3（下一轮用）

**时间**: 2026-09-02 00:40
**会话**: 8 品种指标纠正协作 · 锌+铅全板块完成，硅/锂待跑
**上下文**: 上一轮（09-01 深夜）在锌+铅完成后因上下文超限中断，本轮交接 v3 供下一轮无缝续跑
**实测核验**（2026-09-02 00:35，交接前必做）：
- `git fetch origin` 后 HEAD=main@3a06b99 = origin/main，`git status` 干净 ✅
- 无并行 agent 写入（60min 内无新文件、无 step/zhiji 进程）✅
- correction 目录 13 份对照表已全部落盘（ZN 6 + PB 7）✅
- 同花顺 Chrome 两个 tab 仍在 `iwencai.com/chat`（target 3DD9... 与 897AB...）✅ 直接续用
- 知几 API 正常（`python3 ~/.hermes/scripts/zhiji_api.py search "硅 开工率" all 3` 返回 6 条）✅

---

## 一、全局状态

| 项目 | 状态 |
|-----|------|
| 锌·全板块 6 板块 20 节点 | ✅ 同花顺纠正+知几验证完成，对照表已 push |
| 铅·全板块 6 板块 30 节点 | ✅ 从 37 个 HTML 反推概念指标→同花顺纠正→知几验证完成，已 push |
| 旧分词脚本 step2_zhiji_verify.py 分词函数 | ✅ 已彻底删除 |
| 方法论 + 任务分配 + 交接文档 | ✅ 已 git push 到 main |
| Windows agent 提示词卡 | ✅ 已发（其只产出内容，提交统一转主脑） |
| **本机待做：硅 27 节点 + 锂 26 节点** | ⏳ 未开始 |

**累计 push 进度**：git log `7e6af09`→`3a06b99`，共 13 个提交（锌 6 + 铅 6 + 反推清单 1）。

---

## 二、本机待做（下一轮直接开工，按优先级）

### 2.1 硅·全板块 27 节点（P0）

- **数据源**：`translation-workspace/mapping/SI/step2_match_SI.json`（138 条旧映射，A 级为主）
- **特殊性**：硅**没有 audit 文件**（audit 目录只有 AL/CU/NI/ZN），需**直接从 mapping 提取概念指标**发同花顺（铅无 audit 走 HTML 反推，硅有 mapping 可直接用）
- **节点明细**（29 个 subnode 有 mapping，目标板块 6 个：价格2/供给3/库存4/需求5/进出口6/成本7）：
  - 价格信号 2.1-2.6：2.1(A4)/2.2(A2+C2)/2.3(A4+C1)/2.4(A5)/2.5(A4)/2.6(A5)
  - 供给 3.1.1-3.2.4：全 A 为主（3.1.2 有1个B、3.2.3/3.2.4 各1个B）
  - 库存 4.1-4.5：全 A
  - 需求 5.1-5.3：5.1 有1个B，其余 A
  - 进出口 6.1-6.4：全 A
  - 成本利润 7.1-7.2：7.1 有2个B、7.2 有1个B
- **产物**：`translation-workspace/correction/SI/SI_correct_{板块}_{日期}.md`（目录需新建）
- **策略**：A 级映射直接保留进同花顺纠正表；B/C 级重点交给同花顺纠正。每板块 1-2 轮同花顺 prompt（见第五节模板）→ 知几逐条验证 → 写对照表。

### 2.2 锂·全板块 26 节点（P1，硅完成后）

- **数据源**：`translation-workspace/mapping/LI/step2_match_LI.json`（92 条旧映射）
- **特殊性**：锂**没有 audit 文件**；mapping 覆盖 19 个 subnode（2.1-4.4），**缺需求5/进出口6/成本7**（5.1-5.3、6.1-6.4、7.1-7.3 无旧映射）——这几个板块需**同花顺先发散 → 搜知几 → 建页+纠正并行**
- **节点明细**：2.1-2.6（价格，2.3 有 B1+C2）、3.1.1-3.2.4（供给，3.1.1 有 C3 需重点纠正）、4.1-4.4（库存）；5.x/6.x/7.x 无映射需发散
- **产物**：`translation-workspace/correction/LI/LI_correct_{板块}_{日期}.md`（目录需新建）

### 2.3 硅/锂跑完后的下一步（P0 完成后）

1. **注册**：把对照表 verified 的 zhiji_id 合入 `data/indicators_v1.json`（append-only，写前备份到 analysis/backups/）
2. **建页**：`python3 scripts/build_translation.py --variety SI` / `--variety LI`（需确认脚本已支持 SI/LI 字典，见 STATUS.md [A-STEP5b]）
3. **门禁**：`python3 scripts/check_html.py` + `node scripts/verify_render.js` + `python3 scripts/reclaim.py` 三道全绿
4. **更新 STATUS.md**「近期变更记录」→ `git commit [DOC]` → push（GIT_CURL_OPT 限频）

---

## 三、同花顺对话状态

- **当前对话 share link**：`https://www.iwencai.com/chat/share/?traceId=20003020178826796736100000000894,20003020178826802693500000000895`
- Chrome target：`3DD9B096E6674985A5C68F8279134724`（主）与 `897AB83B3E8D214B7002BC99A6C53D5D`（worker 关联）
- 已用 5 轮（锌供给），还开着
- **下次继续**：直接在同一对话框追加 prompt，不要开新对话
- **注意**：同花顺 90 秒冷却期；prompt ≤ 10000 字

---

## 四、关键 JS 操作代码（CDP Runtime.evaluate 注入）

### 注入 prompt

```javascript
(() => {
  const ce = document.querySelector('[contenteditable]');
  if (!ce) return 'no CE';
  const txt = `PROMPT_TEXT_PLACEHOLDER`;
  ce.innerHTML = '<p>' + txt.replace(/\n/g, '<br>') + '</p>';
  ce.dispatchEvent(new Event('input',{bubbles:true}));
  ce.dispatchEvent(new InputEvent('input',{bubbles:true,cancelable:false,data:'x',inputType:'insertText'}));
  ce.dispatchEvent(new KeyboardEvent('keydown',{key:'a',code:'KeyA',bubbles:true}));
  ce.dispatchEvent(new KeyboardEvent('keyup',{key:'a',code:'KeyA',bubbles:true}));
  ce.dispatchEvent(new Event('blur',{bubbles:true}));
  return 'injected len=' + ce.innerText.length;
})()
```

### 发送

```javascript
(async () => {
  for (let i = 0; i < 10; i++) {
    const sb = document.querySelector('.send-button');
    if (sb) {
      const r = sb.getBoundingClientRect();
      const o = {bubbles:true, cancelable:true, view:window, clientX:r.x+r.width/2, clientY:r.y+r.height/2, button:0};
      [new PointerEvent('pointerdown',o), new MouseEvent('mousedown',o), new PointerEvent('pointerup',o), new MouseEvent('mouseup',o), new MouseEvent('click',o)].forEach(e => sb.dispatchEvent(e));
      return 'sent';
    }
    await new Promise(r => setTimeout(r, 500));
  }
  return 'no send';
})()
```

### 检查生成完成

```javascript
(() => {
  const t = document.body.innerText;
  return t.length + ' | DONE=' + t.includes('内容由AI生成，不构成投资建议');
})()
```

### 取最后一条回复

```javascript
(() => {
  const cards = [...document.querySelectorAll('[class*="chat-item"]')];
  const last = cards[cards.length - 1];
  return last ? last.innerText.slice(0, 8000) : 'NONE';
})()
```

---

## 五、Prompt 模板

### 第一轮（有旧映射时，硅/锂大部分节点用这个）

```
不是不是，你帮我看看这里是关于金属{品种}{板块}的指标，你看看哪些是不相关的？

| 概念指标 | 旧映射 | 旧命中 |
|---|---|---|
| {name1} | {hit_id1} | {hit_name1} |
| {name2} | {hit_id2} | {hit_name2} |
...
```

### 第二轮（追问具体全称，必须发）

```
好，继续。再帮我看看这里是关于金属{品种}{板块}的指标，你帮我给出每个指标对应的SMM有色网和Mysteel钢联的官方全称、数据频率和单位。

| 我需要的指标 | 说明 |
|---|---|
| {指标名1} | {用途说明} |
...

请按表格输出：
| 指标 | SMM有色网官方全称 | Mysteel钢联官方全称 | 数据源 | 频率 | 单位 | 备注 |
```

### 锂缺口板块（无旧映射时，先发散）

```
帮我看看金属锂{板块}的指标，我需要：{子节点列表}。请给出每个子节点下最核心的 3-5 个指标，以及对应的SMM有色网和Mysteel钢联官方全称、数据频率、单位。
请按表格输出：| 指标 | SMM有色网官方全称 | Mysteel钢联官方全称 | 数据源 | 频率 | 单位 | 备注 |
```

---

## 六、知几搜索压缩规则

从同花顺给的全称压缩成 2-3 个核心词再搜知几：

- 删：机构前缀（SMM/Mysteel/USGS/海关）、频率（周度/月度）、单位（元/吨）、口径注释（50%品位/分大中小）、调研样本数（130家）
- 保留：品种词 + 产品形态 + 指标类型 + 地域（如适用）
- 示例：`SMM国产锌精矿周度加工费（SMM，50%品位，元/金属吨）` → 搜 `国产 锌精矿 加工费`
- 命令：`python3 ~/.hermes/scripts/zhiji_api.py search "压缩词" all 10`
- 搜不到的标「🔴 缺项」，**不许伪造 zhiji_id**

---

## 七、产物格式

每个板块完成后写：

```
translation-workspace/correction/{品种}/{品种}_correct_{板块}_{日期}.md
```

表头（参考已完成的 ZN/PB 对照表）：

```markdown
| # | 概念指标 | 同花顺·SMM全称 | 同花顺·Mysteel全称 | 知几·SMM zhiji_id | 知几·Mysteel zhiji_id | 命中名 | 频率 | 单位 |
```

每板块做完 `git add + commit [DOC] + push`（GIT_CURL_OPT="--max-time 300 --retry 5 --retry-delay 10"）。

---

## 八、关键文件索引

| 文件 | 用途 |
|-----|-----|
| `docs/METHODOLOGY_INDICATOR_CORRECTION.md` | 方法论（同花顺纠错逻辑 5 规则 + 操作流程） |
| `docs/TASK_ALLOCATION_8VARIETIES.md` | 8 品种 × 30 节点任务分配表 |
| `docs/HANDOVER_WINDOWS_AGENT_FULL.md` | Windows agent 任务卡 |
| `translation-workspace/correction/ZN/*.md`（6份） | 锌 6 板块对照表（已完成，格式参考） |
| `translation-workspace/correction/PB/*.md`（7份） | 铅 6 板块对照表 + 反推清单（已完成） |
| `translation-workspace/mapping/SI/step2_match_SI.json` | 硅旧映射（138 条） |
| `translation-workspace/mapping/LI/step2_match_LI.json` | 锂旧映射（92 条） |
| `translation-workspace/audit/{AL,CU,NI,ZN}/` | 各品种同花顺审计原文（硅/锂无） |
| `scripts/build_translation.py` | 建页引擎（SI/LI 已支持） |
| `data/indicators_v1.json` | 指标元数据唯一真源（当前 786 v3.43） |

---

## 九、GitHub 分支状态

- `main` — 13 份对照表 + 方法论 + 任务分配 + 交接文档已 push（HEAD=3a06b99）
- `translation-workflow` — 已 rebase 到 main
- Windows agent 的产物推 `indicator-correction-win`
- 本机产物推 `main`（当前策略）

---

## 十、验收标准（硅/锂跑完 = 才算完成）

- [ ] 硅 27 节点对照表（6 板块文件）全部产出并 push
- [ ] 锂 26 节点对照表（6 板块文件）全部产出并 push（含 5/6/7 板块发散）
- [ ] 缺项均标 🔴 缺项，无伪造 zhiji_id
- [ ] 三道门禁：check_html + verify_render + reclaim 全绿
- [ ] STATUS.md 变更记录已更新，HEAD=origin/main
