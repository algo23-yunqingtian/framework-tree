# 本会话自留交接文档（下一轮用）v2

**时间**: 2026-09-01 22:xx  
**会话**: 8 品种指标纠正协作启动 + 锌供给 5 节点纠正完成  
**上下文**: 本会话即将超限，需开新会话继续

---

## 一、全局状态

| 项目 | 状态 |
|-----|------|
| 锌·供给 5 节点 | ✅ 同花顺纠正完成，对照表已写 |
| 旧分词脚本 step2_zhiji_verify.py | ✅ 分词函数已彻底删除 |
| 方法论 + 任务分配 + 交接文档 | ✅ 已 git push 到 main（6 文件） |
| Windows agent 提示词卡 | ✅ 已发给用户，待其复制 |
| 本机待做 102 节点 | ⏳ 未开始 |

---

## 二、本机待做（按优先级）

### 2.1 锌·库存/需求/进出口/成本/价格信号（20 节点）

**起点**：同花顺对话还在打开，直接追加 prompt  
**产物**：`translation-workspace/correction/ZN/ZN_correct_{板块}_{日期}.md`

优先级顺序：
1. 库存 4.1-4.5（5 节点）— 同花顺纠正
2. 需求 5.1-5.3（3 节点）
3. 进出口 6.1-6.4（4 节点）
4. 成本利润 7.1-7.2（2 节点）
5. 价格信号 2.1-2.6（5 节点）

### 2.2 铅·全板块（29 节点）

**特殊**：铅没有 audit 文件，需要从已建 HTML 页面反推概念指标  
页面文件：`pb_21_price_structure.html` 等 37 个  
每页面 grep 指标 ID + 文字描述 → 整理成"概念指标"列表 → 发同花顺

### 2.3 硅·全板块（27 节点）

有 step2_match_SI.json（138 条），待纠正  
从 audit 文件看，硅已有 audit 记录，可参考

### 2.4 锂·全板块（26 节点）

有 step2_match_LI.json（92 条）  
缺页：需求 5.1-5.3、进出口 6.1-6.4、成本 7.1-7.3  
策略：同花顺先发散 → 搜知几 → 建页 + 纠正并行

---

## 三、同花顺对话状态

- **当前对话 share link**：`https://www.iwencai.com/chat/share/?traceId=20003020178826796736100000000894,20003020178826802693500000000895`
- 已用 5 轮（锌供给），还开着
- **下次继续**：直接在同花顺同一对话框里追加 prompt，不要开新对话
- **注意**：同花顺 90 秒冷却期

---

## 四、关键 JS 操作代码（快速复制用）

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
  const cards = [...document.querySelectorAll('[class*="chat-item"]', ...
  const last = cards[cards.length - 1];
  return last ? last.innerText.slice(0, 8000) : 'NONE';
})()
```

---

## 五、Prompt 模板

### 第一轮（有旧映射时）

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

---

## 六、知乎搜索压缩规则

从同花顺给的全称压缩成 2-3 个核心词再搜知几：

- 删：机构前缀（SMM/Mysteel/USGS/海关）、频率（周度/月度）、单位（元/吨）、口径注释（50%品位/分大中小）、调研样本数（130家）
- 保留：品种词 + 产品形态 + 指标类型 + 地域（如适用）
- 示例：`SMM国产锌精矿周度加工费（SMM，50%品位，元/金属吨）` → 搜 `国产 锌精矿 加工费`

---

## 七、产物格式

每个板块完成后写：

```
translation-workspace/correction/{品种}/{品种}_correct_{板块}_{日期}.md
```

表头：

```markdown
| # | 概念指标 | 旧映射 | 旧命中 | 同花顺SMM全称 | 同花顺Mysteel全称 | 知几SMM zhiji_id | 知几Mysteel zhiji_id | 频率 | 单位 | 备注 |
```

每板块做完 git add + commit + push。

---

## 八、关键文件索引

| 文件 | 用途 |
|-----|-----|
| `docs/METHODOLOGY_INDICATOR_CORRECTION.md` | 方法论（同花顺纠错逻辑 5 规则 + 操作流程） |
| `docs/TASK_ALLOCATION_8VARIETIES.md` | 8 品种 × 30 节点任务分配表 |
| `docs/HANDOVER_WINDOWS_AGENT_FULL.md` | Windows agent 任务卡（已 push main） |
| `translation-workspace/correction/ZN_supply_correction_20260901.md` | 锌供给纠正对照表（已完成） |
| `translation-workspace/audit/{品种}/audit_{板块}.md` | 各品种同花顺审计原文 |
| `translation-workspace/mapping/{品种}/step2_match_{品种}.json` | 各品种旧映射 |

---

## 九、GitHub 分支状态

- `main` — 6 份文档已 push（方法论+任务分配+3 份交接文档+锌对照表）
- `translation-workflow` — 同上（已 rebase 到 main）
- Windows agent 的产物推 `indicator-correction-win`
- 本机的产物推 `main` 或单独 `indicator-correction-linux`