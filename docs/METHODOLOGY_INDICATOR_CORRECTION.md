# ZN 指标纠正方法论（已验证版）

**时间**: 2026-09-01  
**验证品种**: 锌·供给端 5 节点（3.1.1-3.1.5）  
**状态**: ✅ 完成，命中率 70%（21/30），9 项知几确无数据已标记

---

## 方法论（三步）

### Step1：发"纠正"prompt 给同花顺

把每个节点已有的旧概念指标 + 旧映射（如果有的话）丢给同花顺，让它逐条纠正。

**模板**:

```
不是不是，你帮我看看这里是关于金属{品种}{板块}的指标，你看看哪些是不相关的？

| 概念指标 | 旧映射 | 旧命中 |
|---|---|---|
| {指标名1} | {旧zhiji_id} | {旧命中名} |
| {指标名2} | {旧zhiji_id} | {旧命中名} |
...
```

**关键**：如果旧映射是空白/第一次做，不要发"纠正"prompt，直接跳 Step1b。

### Step1b：发"推荐具体指标名"prompt 给同花顺

```
好，继续。再帮我看看这里是关于金属{品种}{板块}的指标，你帮我给出每个指标对应的SMM有色网和Mysteel钢联的官方全称、数据频率和单位。

| 我需要的指标 | 说明 |
|---|---|
| {指标名1} | {用途说明} |
| {指标名2} | {用途说明} |
...

请按表格输出：
| 指标 | SMM有色网官方全称 | Mysteel钢联官方全称 | 数据源 | 频率 | 单位 | 备注 |
```

**关键**：
- **必须追问"具体全称"**，同花顺第一轮通常只给方向不给具体名
- SMM 和 Mysteel 分两列要分别给（平权）
- 一次只发一个板块（~5-8 指标），prompt 不能超过 10000 字

### Step2：压缩搜索词，逐条搜知几

同花顺给的全称包含机构前缀+口径注释+单位，**不能直接搜**。压缩规则：

| 删掉 | 例子 |
|-----|------|
| 机构前缀 | SMM / Mysteel / USGS / 海关总署 |
| 频率 | 周度/月度/日度/季度 |
| 单位 | 元/吨、美元/干吨、万金属吨 |
| 口径注释 | 50%品位、低氟氯、分大中小 |
| 调研样本数 | 调研130家、统计5港 |
| 括号注释 | （含硫酸及小金属） |

**保留**：品种词 + 产品形态 + 指标类型 + 地域（如适用）

**示例**：
- 同花顺给：`SMM国产锌精矿周度加工费（SMM，50%品位，元/金属吨）`
- 搜知几：`国产 锌精矿 加工费`

**API 调用**：
```bash
python3 ~/.hermes/scripts/zhiji_api.py search "{压缩后搜索词}" all 10
```

**人工筛选**：从返回结果里挑"品种对+产品形态对+指标类型对"的最优 zhiji_id。

### Step3：生成对照表

对每个节点输出一张表：

| # | 概念指标 | 旧映射 | 同花顺纠正·SMM全称 | 同花顺纠正·Mysteel全称 | 知几·SMM zhiji_id | 知几·Mysteel zhiji_id | 频率 | 单位 |
|---|---------|--------|-----------------|-------------------|----------------|-------------------|------|-----|
| 1 | xxx | 旧→错 | SMM xxx | Mysteel xxx | a1xxxxxx | IDxxxxxx | 周 | 元/吨 |

---

## 同花顺纠错逻辑（5 条规则）

| # | 规则 | 触发条件 | 同花顺如何识别 |
|---|-----|---------|------------|
| 1 | 品种错 | 命中名含其他品种词 | 看命中名的品种词（白银≠锌） |
| 2 | 地域错 | 海外概念命中国内 | 理解国家归属（秘鲁≠中国） |
| 3 | 产业链错位 | 矿山概念命中冶炼端 | 理解"矿山→冶炼→加工"上下游 |
| 4 | 个股 vs 行业 | 命中含公司名 | 识别公司主体，判定非行业口径 |
| 5 | 单一 vs 整体 | 命中含具体仓库/工厂 | 判断样本代表性不足 |

**这些规则全基于语义理解，不是分词匹配能做到的。**

---

## 浏览器操作要点

**关键坑（已验证）**：
1. 每次发完 prompt，**等至少 20 秒**（同花顺生成完成标志：body 出现"内容由AI生成，不构成投资建议"）
2. **两次发送之间间隔 ≥ 90 秒**（同花顺限流）
3. prompt 长度 ≤ 10000 字（编辑器硬上限）
4. 用 `[contenteditable]` 元素注入 prompt，用完整鼠标事件序列点 `.send-button`

**注入 JS**：
```js
(() => {
  const ce = document.querySelector('[contenteditable]');
  if (!ce) return 'no CE';
  ce.innerHTML = '<p>' + '{PROMPT}'.replace(/\n/g, '<br>') + '</p>';
  ce.dispatchEvent(new Event('input',{bubbles:true}));
  ce.dispatchEvent(new InputEvent('input',{bubbles:true,cancelable:false,data:'x',inputType:'insertText'}));
  ce.dispatchEvent(new KeyboardEvent('keydown',{key:'a',code:'KeyA',bubbles:true}));
  ce.dispatchEvent(new KeyboardEvent('keyup',{key:'a',code:'KeyA',bubbles:true}));
  ce.dispatchEvent(new Event('blur',{bubbles:true}));
  return 'injected len=' + ce.innerText.length;
})()
```

**发送 JS**：
```js
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

**检查生成完成 JS**：
```js
(() => {
  const t = document.body.innerText;
  return t.length + ' | DONE=' + t.includes('内容由AI生成，不构成投资建议');
})()
```

---

## 产物规范

每个品种每个板块的纠正结果存到：

```
translation-workspace/correction/{品种}_correct_{板块}_{日期}.md
```

格式：markdown 表格（含旧映射、SMM 全称、Mysteel 全称、SMM zhiji_id、Mysteel zhiji_id、频率、单位）。

每完成一个板块就 `git commit + push`。