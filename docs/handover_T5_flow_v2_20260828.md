# T5 交接文档 — 指标树补全流程 v2 定稿（2026-08-28）

> 本文档是给**新会话**的交接。新会话第一步：读 `analysis/iwencai/PB/test6_results/compare_A_vs_B.md`（本次测试全记录）+ 本文件，然后按「下次对话提示词」执行。
> GitHub 仓库：`algo23-yunqingtian/framework-tree`（SSH 推送）

---

## 一、本次会话已完成（不需要重做）

### 1. 同花顺问财用法纠错（用户 2026-08-28 明确纠正，铁律）
- ❌ **绝不用** `iwencai.com/search` 的 AI搜索入口——它不输出文字、只返回 A 股/"未找到数据"
- ✅ **正确入口**：左侧标签栏「新对话」按钮 或「最近 7 天」历史条目点进去 → 页面**底部聊天框**（`[contenteditable].ql-editor`）粘贴完整 prompt → 点右下 `.send-button` 发送
- ⚠️ 同花顺深度思考 7-30 秒生成；**两次连续请求间隔 ≥30 秒**（实测连发触发"抱歉，暂时处理不过来了"限流）

### 2. Prompt 版本确定：v18_generic（题材精准枚举器·复合图设计师）
- 位置：`analysis/iwencai/PB/prompt_v18_generic.md`
- 占位符：`{品种}` / `{维度}` / `{子类列表}` / `{正例关键词}` 全可替换
- 每张图必带 **观测用途**（=用户在遇到什么问题会优先看这张图、反映什么矛盾——用户 2026-08-28 明确这是他要的"图备注+分析条件"合并表达）
- 旧版 v5/v7/v8 **全部弃用**

### 3. 发散方式实测对比：逐节点发 = 正确答案
- 方式 A（一次发 6.1–6.4 四节点）→ 7 图，且 6.1 混入 TC、6.4 用 LME库存/沪伦凑数（归属错误）
- 方式 B（逐节点发 ×4）→ **18 图**，每类带 HS 编码（7801 未锻轧铅 / 85071000 启动型铅酸 / 85072000 其他铅酸）、真实月度数据（2026.7 精炼铅进口 9214.78 吨，印度 3626/澳洲 1613）、政策变量（海合会反倾销税率 25.8-74%，2026.1.13 生效）
- **结论：每个子节点单独发一次，绝不批量发**

### 4. Skill 已更新（新会话直接加载即可）
- `indicator-tree` skill：Step 1 改为 v18+逐节点+正确入口；**新增 Step 1.5 本地 AI 自检**（✅采纳/⚠️存疑/❌剔除 + 必带字段 + 4 问自检）；旧 prompt 版本标记弃用
- `iwencai-ai-answer-browser-ops` / `iwencai-browser-operate` 两个 skill 的部分内容（AI搜索入口、AI答案 tab）**已过时**，以 memory + indicator-tree skill 为准

### 5. Memory 已更新
- 同花顺问财 v18 定稿（正确入口 + 逐节点发 + 实测对比结论）已写入

---

## 二、完整 6 步流程 v2（新会话执行基线）

```
Step 1  同花顺发散（v18 · 逐节点发）
  · 入口=新对话/最近7天 → 底部聊天框发 prompt → .send-button 发送
  · 每子节点单独发一次，间隔≥30s
  · 原始返回落盘 analysis/iwencai/{品种}/{节点}_diversify_{日期}.md

Step 1.5  本地 AI 自检（新增，用户要求）
  · 逐条审核：✅采纳 / ⚠️存疑(交用户) / ❌剔除(入 indicator_correction.db)
  · 必答4问：相关性质疑 / 归属质疑 / 派生形态质疑 / 复合图覆盖
  · 每条指标带：图名/观测用途/数据源/形态/HS编码(若适用)/落地判定

Step 2  知几验证（指标名 → 拆关键词 → 空格分词 → smm+mysteel 双源搜 → series 校验频率）
  · 已知坑：search 必须显式传 source(smm/mysteel)，不传=返回0结果误判不存在
  · 多关键词发散：品种名+英文代码+产品形态，防分词盲区

Step 3  拆表入库（indicators_v1.json bump version + changelog + api_cache.db 刷时序）
  · 单一真源：指标 ID 唯一真源 = data/indicators_v1.json，脚本不手写 dict
  · 更新后跑条目数 diff + 重跑 refresh_cache.py

Step 4  build 静态页（每子类 2-3 图：主图 + 复合/双轴 + 季节/代理）
  · 复用 scripts/build_pb_61.py / build_pb_62_demo.py（chart_line_t / chart_dual 通用签名）
  · Kion：ECharts 离线（assets/echarts.min.js）、反拷贝保护、{ } 转义选一条走到底

Step 5  push GitHub Pages + 线上验证
  · git 走 SSH（github.com:443 被拦，remote 已切 ssh://git@github.com/algo23-yunqingtian/framework-tree.git）
  · push 后 curl 验证线上 last-modified + grep 关键特征，不能只看 git log
```

---

## 三、6.1–6.4 待做（下一步主任务）

方式 B 的发散结果已完备（18 图清单在 compare_A_vs_B.md），新会话直接进入 Step 1.5 之后。

| 子节点 | 推荐主图（同花顺 v18 已给出） | 需要知几验证的关键词 |
|---|---|---|
| **6.1 原料进口** | ①铅矿砂精矿进口季节性 ②进口来源国集中度(堆叠+占比) ③港口到港+库存双轴 ④银精矿伴生含铅量 ⑤累计来源热力图 | 铅精矿进口量(已有i40=a10017055)、分国别、银精矿进口、港口库存、港口到港、TC排除 |
| **6.2 精炼金属** | ①HS7801进出口总量季节 ②粗铅+铅合金结构 ③来源国堆叠 ④出口目的地 ⑤双向月度时序 | 精炼铅进口(已有i17=a10017037)、精炼铅出口、粗铅进口、铅合金进口、分国别 |
| **6.3 制品出口** | ①铅酸电池出口季节 ②净出口双轴 ③目的地堆叠 ④启动型/其他100%堆叠 ⑤零件出口 ⑥耗铅量估算 | 铅蓄电池出口(已有i37=a10017078)、i38起动型(a10151429)、进口量、零件、分国别 |
| **6.4 海外发运** | ①LME新加坡库存+注销双轴 ②在途+到港季节 ③精炼铅来源国堆叠 ④提单量+提单库存 ⑤来源国热力图 ⑥接货强度 | LME新加坡(已有i19/i20=FU00023414/FU00023622)、到港量、提单量、来源国(印度/韩国/哈国) |

**建议执行顺序（新会话 P1 试点 → P2 批量）**：
1. **P1 试点：先做 6.4 完整闭环**（发散已完成 → 自检 → 知几 → 入库 → build → push），用户验收流程质量
2. **P2 批量：6.1 → 6.2 → 6.3**（每个节点完整闭环后 push）

---

## 四、遗留问题（本次会话已识别，未解决）

1. **6.1 旧页面 `pb_61_raw_material_import.html` 的图2 用了 i17（海关铅锭进口）**——那是 6.2 范畴，6.1 应用 i40 海关铅精矿进口。重做 6.1 时必须修正
2. **旧页每页只有 2 图**（6.1-6.4 各 2 图），按新流程每子节点应扩到 2-3 张复合图
3. **用户之前反映旧页"有一个图显示不出来"**——还没定位，新会话重做时顺带验证（build 后必须 browser_console 查 `__inst_*` 是否 null）
4. **知几 search 为什么必须传 smm/mysteel**：这是已验证的 API 行为（不传返回 0），不是流程可选项——已向用户解释，新会话不用再问
5. **framework-tree STATUS.md 需要更新**：本次 v18 测试 + 流程 v2 定稿，需在 STATUS.md 加变更记录

---

## 五、当前上下文占用（发文档时）

- ~80%，**已建议用户开新对话**，本次交接文档即为此准备

---

## 产物路径速查

| 内容 | 路径 |
|---|---|
| 本次测试全记录（对比） | `/home/ubuntu/analysis/iwencai/PB/test6_results/compare_A_vs_B.md` |
| v18 prompt 模板 | `/home/ubuntu/analysis/iwencai/PB/prompt_v18_generic.md` |
| 指标唯一真源 | `/home/ubuntu/framework-tree/data/indicators_v1.json` |
| 时序缓存 | `/home/ubuntu/framework-tree/scripts/api_cache.db` |
| build 模板 | `/home/ubuntu/framework-tree/scripts/build_pb_61.py` / `build_pb_62_demo.py` / `build_pb_63.py` / `build_pb_64.py` |
| 目录树盘点 | `/home/ubuntu/analysis/iwencai/PB/t4_node_inventory_20260828.md` |
| 同花顺操作 skill | `indicator-tree`（已更新）+ `iwencai-ai-answer-browser-ops`（部分过时） |