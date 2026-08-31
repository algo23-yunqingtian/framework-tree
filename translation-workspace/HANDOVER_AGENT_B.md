# 交接文档：指标翻译工作流 — Agent B

**日期**：2026-09-01  
**你的角色**：Agent B，负责 SN + SI + LI + PB 四个品种  
**协作方**：Agent A（主脑，另一台服务器），负责 ZN + NI + CU + AL

---

## 一、任务总目标

把同花顺 divergence 文件里的**概念指标名**翻译成**SMM/Mysteel/LME 真实指标名**，建立完整映射表，为后续看板重建提供精准的指标ID。

**核心原则**：图表设计方案保留，只改指标名。

---

## 二、你的分工

| 品种 | 节点数 | 状态 |
|------|--------|------|
| SN（锡） | 30 | ✅ 完整 |
| SI（硅） | 29 | ⚠️ 缺 7.3 |
| LI（碳酸锂） | 19 | ⚠️ 缺 4.5/5.1-5.3/6.1-6.4/7.1-7.3（共11个） |
| PB（铅） | 0 | ❌ 无 divergence 文件，需先补发散 |
| **合计** | **78（现有）** | - |

---

## 三、环境准备

### 3.1 克隆仓库

```bash
# 你的 GitHub 账号：algo23-yunqingtian
# 仓库：framework-tree

git clone git@github.com:algo23-yunqingtian/framework-tree.git
cd framework-tree

# 切到协作分支
git checkout translation-workflow
# 如果提示分支不存在，先 fetch
git fetch origin translation-workflow
git checkout translation-workflow
```

### 3.2 文件结构说明

```
framework-tree/
├── translation-workspace/          # 协作空间（Agent A 已创建）
│   ├── scripts/
│   │   └── step0_extract.py        # 提取去重脚本
│   ├── prompts/
│   │   └── audit_prompt_template.md # Prompt 模板（含品种术语）
│   ├── audit/                       # Step 1 输出目录
│   └── README.md
├── analysis/iwencai/               # 原始 divergence 文件
│   ├── SN/
│   │   └── divergence_*.md         # 30个文件
│   ├── SI/
│   │   └── divergence_*.md         # 29个文件（缺7.3）
│   ├── LI/
│   │   └── divergence_*.md         # 19个文件（缺11个）
│   └── PB/
│       └── （无标准divergence，只有旧diversify格式）
└── docs/
    ├── HANDOVER_AGENT_A.md          # Agent A 交接文档
    └── HANDOVER_AGENT_B.md          # 本文件
```

### 3.3 查看原始 divergence 文件

```bash
# 查看锡的某个节点
cat analysis/iwencai/SN/divergence_3.1.1.md

# 查看硅的所有节点
ls analysis/iwencai/SI/divergence_*.md
```

---

## 四、工作流（3步，你只做 Step 0 和 Step 1）

### Step 0：提取概念指标+去重（脚本自动，5分钟/品种）

**脚本位置**：`translation-workspace/scripts/step0_extract.py`

```bash
cd /home/ubuntu/framework-tree/translation-workspace

# 跑你负责的4个品种
python scripts/step0_extract.py SN
python scripts/step0_extract.py SI
python scripts/step0_extract.py LI
# PB 跳过（没有 divergence）
```

**输出**：`analysis/iwencai/{品种}/concept_indicators.json`

脚本会自动：
1. 提取每个 divergence 文件中的指标名
2. 跨节点去重
3. 按6大板块分组

### Step 1：同花顺审计+重设计（每组1次提问，每组~10-15分钟）

**重要**：不是按单个子节点问，是按**板块组**问。

#### 操作流程

1. **打开同花顺问财**
   ```
   https://www.iwencai.com/chat
   ```

2. **点"新对话"**

3. **复制 Prompt 模板**
   ```bash
   cat translation-workspace/prompts/audit_prompt_template.md
   ```

4. **粘贴模板 + 该板块所有 divergence 文件内容**
   
   例如问锡的供给板块（3.1.1-3.2.4，共9个节点）：
   ```
   [粘贴 Prompt 模板，替换 {品种}=锡, {板块名}=供给, {N}=9]
   
   【现有方案如下】
   [粘贴 divergence_3.1.1.md 全文]
   [粘贴 divergence_3.1.2.md 全文]
   ...
   [粘贴 divergence_3.2.4.md 全文]
   ```

5. **等待回复**（约5-10分钟）

6. **保存回复**
   ```bash
   mkdir -p translation-workspace/audit/SN
   # 把同花顺的回复保存到：
   # translation-workspace/audit/SN/audit_供给.md
   ```

7. **提交到 GitHub**
   ```bash
   git add translation-workspace/audit/SN/
   git commit -m "SN: 供给板块审计完成"
   git push origin translation-workflow
   ```

#### 板块分组

| 板块 | 节点范围 | SN节点数 | SI节点数 | LI节点数 |
|------|---------|----------|----------|----------|
| 价格信号 | 2.1-2.6 | 6 | 6 | 6 |
| 供给 | 3.1.1-3.2.4 | 9 | 9 | 5（缺3.2.5-3.2.4不存在） |
| 库存 | 4.1-4.5 | 5 | 5 | 4（缺4.5） |
| 需求 | 5.1-5.3 | 3 | 3 | 0（全缺） |
| 进出口 | 6.1-6.4 | 4 | 4 | 0（全缺） |
| 成本利润 | 7.1-7.3 | 3 | 2（缺7.3） | 0（全缺） |
| **合计** | | **30** | **29** | **19** |

#### 特殊处理

1. **价格信号(2.x)**：Prompt 末尾追加 LME 变量精确化要求（见模板）
2. **SI 缺 7.3**：只问 7.1 和 7.2
3. **LI 缺 11 个节点**：只问现有的 19 个节点
4. **PB 全部缺失**：跳过，等 Agent A 最后集中补发散

#### Prompt 模板关键规则

**删除项**（严格删除）：
- 统计派生：近N年均值、标准差、分位数、环比、同比、增速
- 临时不可追踪：检修量、排产计划、停产通知
- 不相关凑数：如TC图里出现产量

**图表设计原则**：
- 单指标时序图优先
- 复合图仅限强相关2个指标（如TC+利润）
- 删除季节性统计图（除非指标确实有强季节性）

**输出格式**：
```
| 子节点 | 图名称 | 指标名 | SMM官方全称 | Mysteel官方全称 | LME英文变量名 | 频率 | 单位 |
```

#### 品种术语参考（每个品种追加到 Prompt 末尾）

**锡 (SN)**：
```
品种术语参考：精锡、锡精矿、再生锡、锡锭、焊锡、锡化工、锡材
```

**硅 (SI)**：
```
品种术语参考：工业硅、多晶硅、单晶硅、有机硅、硅合金、硅微粉、金属硅
```

**碳酸锂 (LI)**：
```
品种术语参考：碳酸锂、氢氧化锂、锂辉石、锂云母、盐湖卤水、电池级碳酸锂、工业级碳酸锂
```

---

## 五、协同机制

### 你做完 Step 1 后

1. **提交审计回复到 GitHub**
   ```bash
   git add translation-workspace/audit/
   git commit -m "SN/SI/LI: Step 1 审计完成"
   git push origin translation-workflow
   ```

2. **通知 Agent A**（通过飞书消息）
   ```
   我已完成 SN/SI/LI 的 Step 1 同花顺审计，
   文件已推送到 translation-workflow 分支：
   translation-workspace/audit/{SN,SI,LI}/audit_*.md
   
   请执行 Step 2 知几搜索。
   ```

3. **Agent A 会做**：
   - 拉取你的审计回复
   - 提取精确指标名
   - 跑知几API搜索
   - 生成映射表

4. **你审核映射表**（Agent A 发给你）
   - A级（高置信）→ 确认
   - B级（可能匹配）→ 人工判断
   - C级（搜不到）→ 标备用库

5. **你确认后发回给 Agent A**，它统一入库

---

## 六、时间预估

| 步骤 | SN(30) | SI(29) | LI(19) | PB(0) | 合计 |
|------|--------|--------|--------|-------|------|
| Step 0 提取去重 | 2min | 2min | 2min | 跳过 | 6min |
| Step 1 同花顺审计 | 6组×10min=60min | 6组×10min=60min | 4组×10min=40min | 跳过 | ~2.5h |
| **你的总工作量** | | | | | **~3h** |

---

## 七、备份与回退

**备份分支**：`backup_pre_translation_20260901`  
**工作分支**：`translation-workflow`

如果出问题，随时可以：
```bash
git checkout backup_pre_translation_20260901
```

---

## 八、立即开始

```bash
# 1. 克隆并切到工作分支
git clone git@github.com:algo23-yunqingtian/framework-tree.git
cd framework-tree
git fetch origin translation-workflow
git checkout translation-workflow

# 2. 跑 Step 0（3个品种，PB跳过）
cd translation-workspace
python scripts/step0_extract.py SN
python scripts/step0_extract.py SI
python scripts/step0_extract.py LI

# 3. 查看提取结果
cat ../analysis/iwencai/SN/concept_indicators.json | head -50

# 4. 开始 Step 1 同花顺审计
# 按板块逐个提问，保存回复到 audit/{品种}/audit_{板块}.md
# 每完成一个板块就 commit + push
```

---

## 九、注意事项

1. **同花顺每天200次调用**，不要省着用，必要时可多问几次追问细节
2. **图表设计原则**：单指标优先，复合图仅限强相关2个指标
3. **删除项**：统计派生、临时不可追踪、不相关凑数
4. **价格信号板块**：务必追问 LME 精确英文变量名
5. **每完成一个板块就提交**，方便 Agent A 同步进度

---

## 十、常见问题

### Q: PB 怎么办？
A: 跳过 PB，等其他品种做完后，Agent A 会集中补 PB 的 divergence 发散。

### Q: SI 缺 7.3 怎么处理？
A: 只问 7.1 和 7.2，7.3 跳过。

### Q: LI 缺 11 个节点怎么处理？
A: 只问现有的 19 个节点，缺失的跳过。

### Q: 同花顺返回的格式不对怎么办？
A: 追问同花顺，要求严格按表格格式输出。如果还是不对，手动整理后再保存。

### Q: 知几搜索谁做？
A: Agent A 统一做（因为它有知几API密钥和缓存DB）。你只需要把 Step 1 的回复推送到 GitHub。
