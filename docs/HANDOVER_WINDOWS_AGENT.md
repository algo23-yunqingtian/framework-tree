# Windows Agent 任务卡：8 品种指标纠正协作

**发件**: 本机主脑（Linux Hermes）  
**收件**: Windows Hermes agent  
**任务**: 8 品种指标纠正协作 — 你负责铜/铝/镍/锡 4 品种  
**开始时间**: 2026-09-01  
**交付**: 每完成一个板块就 git commit + push 到 `indicator-correction` 分支

---

## 一、你负责的任务

你负责 **4 个品种 × 全板块** 的指标纠正：

| 品种 | 已建页面 | 待纠正节点 |
|-----|--------|---------|
| 铜(CU) | 19 页面 | 全部 19 节点 |
| 铝(AL) | 19 页面 | 全部 19 节点 |
| 镍(NI) | 23 页面 | 全部 23 节点 |
| 锡(SN) | 22 页面 | 全部 22 节点 |
| **合计** | **83 页面** | **83 节点** |

**不用做**：铅(PB，已完整)、锌(ZN，主脑做)、锂(LI，主脑做)、硅(SI，主脑做)。

---

## 二、你的环境要求

1. **Chrome 浏览器** — 已登录同花顺问财（iwencai.com），保持登录态
2. **知几 API** — `zhiji_api.py` 已配置好（路径可能是 `C:\Hermes\scripts\zhiji_api.py` 或 `~/.hermes/scripts/zhiji_api.py`）
3. **Git** — 能 clone/push 到 GitHub，repo：`algo23-yunqingtian/framework-tree`
4. **Python 3** — 能跑 `zhiji_api.py search` 和 `series`

**测试环境**：
```powershell
# 测同花顺
打开 Chrome，访问 https://www.iwencai.com/chat，确认已登录（看到"田允晴"头像）

# 测知几
python3 ~/.hermes/scripts/zhiji_api.py search "锌 社会库存" all 5
# 应该返回若干结果，如果报错检查 API key
```

---

## 三、完整工作流（每个节点 4 步）

### Step 1：读现有映射（知道旧错在哪）

每个品种每个板块都有旧的映射文件：

```
translation-workspace/mapping/{品种}/step2_match_{品种}.json
```

用 Python 读取，找出属于你要做的板块的所有"概念指标"和"旧 zhiji_id"。

例如铜·供给端（3.x 节点）：
```python
import json
data = json.load(open('translation-workspace/mapping/CU/step2_match_CU.json'))
for k, v in data.items():
    if v.get('subnode','').startswith('3.'):
        print(v.get('name','')[:50], '→', v.get('hit_name',''))
```

### Step 2：发 prompt 给同花顺

**打开 Chrome → 访问 https://www.iwencai.com/chat → 注入 prompt**

**Prompt 模板 A**（有旧映射时，先纠正）：

```
不是不是，你帮我看看这里是关于金属{品种名}{板块}的指标，你看看哪些是不相关的？

| 概念指标 | 旧映射 | 旧命中 |
|---|---|---|
| {指标名1} | {旧zhiji_id} | {旧命中名} |
| {指标名2} | {旧zhiji_id} | {旧命中名} |
...
```

**Prompt 模板 B**（追问具体全称，必须发第二遍）：

```
好，继续。再帮我看看这里是关于金属{品种名}{板块}的指标，你帮我给出每个指标对应的SMM有色网和Mysteel钢联的官方全称、数据频率和单位。

| 我需要的指标 | 说明 |
|---|---|
| {指标名1} | {用途说明} |
| {指标名2} | {用途说明} |
...

请按表格输出：
| 指标 | SMM有色网官方全称 | Mysteel钢联官方全称 | 数据源 | 频率 | 单位 | 备注 |
```

**浏览器操作步骤**（每次）：

```
1. Chrome 访问 https://www.iwencai.com/chat
2. 在 [contenteditable] 输入框里粘贴 prompt（用 JS 注入，见下）
3. 点发送按钮
4. 等 20-30 秒，检查回复是否完成（出现"内容由AI生成，不构成投资建议"）
5. 复制回复内容，保存到文件
6. 间隔 90 秒再发下一个
```

**注入 JS**（在 Chrome DevTools 控制台执行）：

```javascript
(() => {
  const ce = document.querySelector('[contenteditable]');
  if (!ce) return 'no CE';
  const txt = `你的prompt文本放在这里`;
  ce.innerHTML = '<p>' + txt.replace(/\n/g, '<br>') + '</p>';
  ce.dispatchEvent(new Event('input',{bubbles:true}));
  ce.dispatchEvent(new InputEvent('input',{bubbles:true,cancelable:false,data:'x',inputType:'insertText'}));
  ce.dispatchEvent(new KeyboardEvent('keydown',{key:'a',code:'KeyA',bubbles:true}));
  ce.dispatchEvent(new KeyboardEvent('keyup',{key:'a',code:'KeyA',bubbles:true}));
  ce.dispatchEvent(new Event('blur',{bubbles:true}));
  return 'injected len=' + ce.innerText.length;
})()
```

**发送 JS**：

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

**检查完成 JS**：

```javascript
(() => {
  const t = document.body.innerText;
  return t.length + ' | DONE=' + t.includes('内容由AI生成，不构成投资建议');
})()
```

### Step 3：搜知几验证

拿到同花顺给的 SMM 全称 和 Mysteel 全称后，**压缩成 2-3 个核心词**再搜知几。

**压缩规则**：删掉机构前缀(SMM/Mysteel/USGS/海关) + 频率(周度/月度) + 单位(元/吨) + 口径注释(50%品位/分大中小) + 调研样本数(130家/55家)

**示例**：
- 同花顺给：`SMM国产锌精矿周度加工费（SMM，50%品位，元/金属吨）`
- 压缩后搜：`国产 锌精矿 加工费`

**API 调用**：
```bash
python3 ~/.hermes/scripts/zhiji_api.py search "压缩后的搜索词" all 10
```

**从返回结果里选**：
- 优先选 Mysteel 源（ID 前缀 `IDxxxx` 或 `FUxxxx`）
- 同时记录 SMM 源（前缀 `a1xxxx`）
- 平权记录，不默认优先用哪个

### Step 4：写纠正对照表

每个板块输出一份 markdown：

```
translation-workspace/correction/{品种}_correct_{板块}_{日期}.md
```

**表格格式**（SMM 和 Mysteel 平权，两列都放 zhiji_id）：

```markdown
| # | 概念指标 | 旧映射 | 同花顺SMM全称 | 同花顺Mysteel全称 | 知几SMM zhiji_id | 知几Mysteel zhiji_id | 频率 | 单位 |
|---|---------|--------|------------|---------------|----------------|-------------------|------|-----|
| 1 | xxx | 旧→错 | SMM xxx | Mysteel xxx | a1xxxxxx | IDxxxxxx | 周 | 元/吨 |
```

---

## 四、产物归档

所有产物保存到 GitHub：

```
git clone https://github.com/algo23-yunqingtian/framework-tree.git
cd framework-tree
git checkout -b indicator-correction-win
```

**每个板块做完后**：
```
git add translation-workspace/correction/
git commit -m "[B] {品种} {板块} 指标纠正"
git push origin indicator-correction-win
```

---

## 五、每日汇报格式

每完成一个板块，在飞书/微信汇报：

```
【铜·供给端】完成
- 同花顺纠正：X 条指标，Y 条剔除
- 知几验证：命中 Z 条，缺项 W 条
- 产物文件：translation-workspace/correction/CU_correct_supply_20260901.md
```

---

## 六、已知坑

1. **同花顺限流** — 两次发送间隔 ≥ 90 秒，否则触发"抱歉，暂时处理不过来了"
2. **prompt 长度上限** — 一次 ≤ 10000 字，一个板块发一个 prompt
3. **同花顺第一轮只给方向** — 必须发第二遍追问具体全称
4. **知乎 SMM/Mysteel 平权** — 两个来源的 zhiji_id 都记录，不要只取第一个
5. **同花顺偶有拒答** — 如果返回"我是同花顺研发的投资助理问财..."，等 5 分钟重发
6. **知几缺项** — 搜不到不要硬凑，标注"知几无数据，需外部源补充"

---

## 七、协作规则

1. **你只做 铜/铝/镍/锡**，主脑做 锌/锂/硅 + 最终上线
2. **不要改 main 分支**，用 `indicator-correction-win` 分支
3. **不要改 chart_kits.py / indicators_v1.json / tree_config.json** — 这些只有主脑能改
4. **每个板块做完就 push**，不要攒着
5. **所有 prompt 原文 + 同花顺回复原文** 都保存到文件，明天抽查