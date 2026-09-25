# 任务书：PB 同花顺发散流水线（材料交接，暂不执行）

> 交付方：爱马仕（审计主脑）· 接收方：Dsharnes-B
> 日期 2026-09-13 · 分支 `indicator-correction-win` · HEAD `78631cc`
> ⚠️ **本文件仅为材料交接。收到启动指令前，不要执行完整发散任务。**
> 依赖前置：R1-R4 二次修复通过复审 + commit `78631cc` 上游治理通过复审。

---

## 〇、启动前必须先完成的两层复审（阻塞项）

| 层 | 项 | 当前状态 | 复审要点 |
|---|---|---|---|
| 前端 | R1 主图跨板块应降 🟢（60 条真串台） | ❌ 未修 | `judge_placement` 只放行辅助跨板块 |
| 前端 | R2 重跑 62 张 A-vs-A 页面 build | ❌ 未修 | disambig 是生成期函数，存量页面未重建 |
| 前端 | R3 Coverage_Report 补"期望图数"维度 | ❌ 未修 | 分母自指问题 |
| 前端 | R4 15 张 div id 非标准命名 | ❌ 未修 | echart div 1394 vs 注册 1379 |
| 上游 | 78631cc 匹配阈值 5→4 / 别名词典 / 幻觉清洗 | ⏳ 待复审 | 见 `REVIEW_CHART_REGISTRY_V2_20260913.md` 后续附件 |

> 详细复审基线见 `task_queue/feedback/REVIEW_CHART_REGISTRY_V2_20260913.md`

---

## 一、PB 现状（实测缺口）

| 项 | 实测值 | 说明 |
|---|---|---|
| `analysis/iwencai/PB/divergence_*` | **0 个** | PB 是唯一未走标准流水线的品种 |
| `decision_*` | **0 个** | 无 Step2 取舍决策 |
| 现有 diversify 文件 | 12 个 | 51/53 实测为**网页 UI 噪声**（噪声标记 6，有效表格行 0）→ 不可复用 |
| `indicators_v1.json` PB 指标 | **99 条** | 来源：人工定稿 `pb_prompt/Pb_看板指标定稿_v2~v4.md` |
| 其中 `_nodes=[]` | **99/99（100%）** | ⚠️ 唯一无节点标注的品种，无法按节点反查 |
| verified=True / 待验证 | 92 / 7 | — |
| `step3_register_plan.json` PB 条目 | **0** | by_metal 只有 zn/ni/si/sn/li |
| PB HTML / build 脚本 | 37 / 37 | 页面齐全 |
| `tree_config.json` 期望节点 | **33 个** | 含 8.1-8.3（板块 8 不做图表）→ 实际发散 **30 节点** |

**30 个待发散节点**：2.1-2.6 / 3.1.1-3.1.5 / 3.2.1-3.2.4 / 4.1-4.5 / 5.1-5.3 / 6.1-6.4 / 7.1-7.3

---

## 二、5 步流程

### Step 0：基线同步 + 拿锁
```bash
git fetch origin && git checkout indicator-correction-win
git checkout -b task/pb_divergence
python3 ~/.hermes/scripts/file_write_lock.py acquire /home/ubuntu/analysis agent:hermes-pb
```

### Step 1：同花顺发散（30 节点）
- 模板参考：`analysis/iwencai/ZN/divergence_2.1.md`（图表方案表格式，非独立指标枚举表——五金属实测此格式可解析）
- Prompt 参考：`pb_prompt/batch/PB_*_v19.md`（已有 6 个板块 prompt：价格/供给/库存/成本利润/进出口/需求）
- 输出：`analysis/iwencai/PB/divergence_{node}.md`
- 节点边界以 `tree_config.json` 该节点 `q` 字段为准

### Step 2：取舍决策
- 输出：`analysis/iwencai/PB/decision_{node}.md`
- 三栏：**候选指标（正主/辅助）** / **排除项（原因+归属）** / **节点边界说明**
- 遵循 AGENTS.md §3.5 指标取舍 5 规则

### Step 3：知几验证 + 分层
- 调用：`python3 ~/.hermes/scripts/zhiji_api.py search "<指标名>"`
- 阈值：**score≥12 = A**（可直接注册）/ 6-11 = B（建议抽查）/ <6 = C（备用库）
- ⚠️ 78631cc 已把知几匹配阈值从 5 调到 4，PB 应使用**新阈值**，不要沿用旧版 5
- 输出：A/B/C 分层 + 注册计划（补 `step3_register_plan.json` 的 `pb` 键）

### Step 4：三类差异比对（核心交付）
PB 发散结果 vs 现有 99 条人工定稿，输出**三类清单**：

| 类 | 定义 | 处置 |
|---|---|---|
| **A 类：发散推荐但定稿无** | 同花顺推荐，99 条里没有 | 待补充 → 进 Step 3 知几验证 |
| **B 类：定稿独有** | 99 条里有，发散没推荐 | 待知几验证保留（可能是人工补录的外部源指标） |
| **C 类：两边都有但口径不同** | 名称相似但单位/频率/口径不一致 | 待人工裁定 |

比对方法（名称模糊匹配，剥离 SHFE/LME/SMM/GFEX 前缀 + 子串包含）：
```python
def fuzzy(a, b):
    for p in ('SHFE','LME','SMM','Mysteel','GFEX','上期所'):
        a=a.replace(p,''); b=b.replace(p,'')
    return a in b or b in a
```
> ⚠️ 参考教训：五金属实测"同花顺→文档丢失率 84-100%"是**命名格式不匹配**所致（自然语言简称 vs 知几注册全称），非真实丢失。C 类清单必须逐条人工裁定，不要直接判丢失。

### Step 5：产出回传
- 产出写入 `task_queue/feedback/`，标记 **通过 / 待二次修复**
- 更新 `STATUS.md` 近期变更记录
- commit 前缀 `[Txx]`（任务）或 `[B]`（数据）
- **不直接 push main**，走 `task/pb_divergence` 分支 + PR

---

## 三、Prompt 硬约束（防图表名 / 防数据源幻觉）

以下约束**必须写进 Step 1 的同花顺 prompt**，来源是五金属 198 个 divergence 文件的实测缺陷统计：

### 3.1 禁止输出图表名（实测混入 62 条）
❌ 禁止：`LME锌库存时序图` / `工业硅冶炼利润分位时序图` / `上期所锌仓单与在途库存联动图` / `CFTC投机净多与COMEX价格联动图`
✅ 只输出：`LME：锌：期货库存（日）` / `工业硅：冶炼利润（日）` / `上期所锌仓单（日）`

### 3.2 禁止派生形态当独立指标（实测混入 45 条）
❌ 禁止单列：`日增减` / `周环比` / `月环比` / `同比` / `去化速度` / `累库幅度` / `环比率` / `分位数` / `变化方向` / `月度高点` / `月低点` / `增速` / `近月合约收盘价` / `远月合约收盘价`
✅ 合并为：`期限结构` / `库存总量`（派生形态作为该指标的呈现方式，不单列）

### 3.3 品种数据源白名单（防跨品种幻觉，实测 18 条）
| 品种 | 允许数据源 | 明确禁止 |
|---|---|---|
| **PB 铅** | SHFE / LME / SMM / Mysteel / 海关 / ILZSG / 百川 / 金仕坦 | ❌ **COMEX**（铅不在 COMEX 上市）/ ❌ GFEX / ❌ LME锂 / ❌ 碳酸锂 |
| LI 锂 | GFEX / SHFE / SMM / 百川 | ❌ COMEX（碳酸锂不在 COMEX 上市） |
| NI 镍 | LME / SHFE / SMM / MHP / 海关 | ❌ COMEX |
| SN 锡 | LME / SHFE / SMM / 海关 | ❌ COMEX |
| SI 硅 | GFEX / SMM / 百川 | — |

> 实测幻觉实例：LI divergence 推 `LME锂价与COMEX锂价（日）` / `COMEX仓单`；SI 推 `国内硅矿月产能利用率`（应归 LI）；NI/SN 推 COMEX 数据。

### 3.4 口径必须写全（实测 27 条模糊）
- `社会库存` → 必须写 **`社会库存：中国（周）`** 还是 `社会库存：全球（月）`
- `产量` → 必须标 **月/年**：`精炼铅产量：中国（月）` / `铅矿产量：全球（年）`
- `基差` → 必须标 **品种+合约**：`SHFE：铅：基差（日）`

### 3.5 数量与归属硬约束
- 每节点 **6-8 个指标，最多 10 个**（少比多好，宁缺勿滥）
- 归属优先：跨类指标**不删除**，在表末标注 `与其他子类更相关 + 应归属节点`
- 正主防串用：先 grep 该指标是否已是其他页面的正主，已在别页做正主的只能作辅助
- 每节点 1 个正主，其余为辅助/交叉验证

### 3.6 完整 prompt 骨架（可直接粘贴）
```
角色：你是有色金属产业研究的「题材精准枚举器·复合图设计师」。
品种：铅（PB）· 节点：{node_code} {node_name} · 边界：{tree_config.q}

【核心规则】
规则1 数量：只输出 6-8 个本子节点直接相关的独立基础指标，最多 10 个。
规则2 独立基础指标：只输出原始可量化指标（绝对量/结构占比/持有者/分地区/在途量/持有天数），
      禁止派生形态（环比/同比/增速/去化/分位/日增减/月高低点）。
规则3 题材对象一致：指标必须直接描述本节点题材对象，跨类指标在表末标注归属。
规则4 图表名禁止：只输出指标名，禁止"时序图/联动图/监控图/复合图"等图表类型命名。
规则5 数据源白名单：只允许 SHFE/LME/SMM/Mysteel/海关/ILZSG/百川/金仕坦。
      铅不在 COMEX 上市，禁止输出任何 COMEX 数据；禁止 GFEX/碳酸锂/GFEX多晶硅 等非铅数据源。
规则6 口径写全：库存标地区+频率（中国-周 / 全球-月）；产量标月或年；基差标品种+合约。

【输出格式】图表方案表（与 analysis/iwencai/ZN/divergence_2.1.md 完全一致）
| 序号 | 图表名称 | 包含指标(1-3个) | 数据源(渠道/频率/可得性) | 观测用途 |
```

---

## 四、回传格式契约

回执写入 `task_queue/feedback/`，命名 `PB_PIPELINE_RECEIPT_{YYYYMMDD}.md`，含：

```markdown
## 交付摘要
| 步骤 | 产出 | 数量 |
|---|---|---|
| Step1 divergence | analysis/iwencai/PB/divergence_*.md | {N}/30 |
| Step2 decision | analysis/iwencai/PB/decision_*.md | {N}/30 |
| Step3 分层 | A/B/C | {a}/{b}/{c} |
| Step4 差异 | A类补充/B类保留/C类裁定 | {x}/{y}/{z} |

## 三类差异清单
（A/B/C 三类各列全清单）

## 合规自查
- [ ] 0 条图表名
- [ ] 0 条派生形态
- [ ] 0 条 COMEX/GFEX 幻觉
- [ ] 99 条定稿全部标注 _nodes
- [ ] 门禁 check_html.py / verify_render.js / reclaim.py 全 PASS
```

---

## 五、状态与下一步

| 状态 | 值 |
|---|---|
| 材料交接 | ✅ 本文件 |
| 完整发散执行 | ⏸️ 阻塞，待启动指令 |
| 阻塞条件 | R1-R4 复审通过 + 78631cc 复审通过 |
