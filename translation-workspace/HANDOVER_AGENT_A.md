# 交接文档：指标翻译工作流 — Agent A（主脑）

**日期**：2026-09-01  
**你的角色**：Agent A（主脑），负责 ZN + NI + CU + AL 四个品种  
**协作方**：Agent B（另一台服务器），负责 SN + SI + LI + PB

---

## 一、任务总目标

把同花顺 divergence 文件里的**概念指标名**翻译成**SMM/Mysteel/LME 真实指标名**，建立完整映射表，为后续看板重建提供精准的指标ID。

**核心原则**：图表设计方案保留，只改指标名。

---

## 二、你的分工

| 品种 | 节点数 | 状态 |
|------|--------|------|
| ZN（锌） | 30 | ✅ 完整 |
| NI（镍） | 30 | ✅ 完整 |
| CU（铜） | 30 | ✅ 完整 |
| AL（铝） | 30 | ✅ 完整 |
| **合计** | **120** | - |

---

## 三、工作流（4步）

### Step 0：提取概念指标+去重（脚本自动，5分钟/品种）

**脚本位置**：`translation-workspace/scripts/step0_extract.py`

```bash
cd /home/ubuntu/framework-tree/translation-workspace
python scripts/step0_extract.py ZN
python scripts/step0_extract.py NI
python scripts/step0_extract.py CU
python scripts/step0_extract.py AL
```

**输出**：`analysis/iwencai/{品种}/concept_indicators.json`

脚本逻辑：
1. 正则提取每个 divergence 文件中的表格行
2. 提取「包含指标」列，按顿号/逗号拆分
3. 去除单位后缀（`（元/吨）`、`（万吨）`等）
4. 跨节点去重（完全匹配+去除空格后匹配）
5. 按6大板块分组输出

### Step 1：同花顺审计+重设计（每组1次提问，每组~10-15分钟等待）

**重要**：不是按单个子节点问，是按**板块组**问。4个品种×6个板块 = 24次提问。

#### 操作流程

1. 打开 https://www.iwencai.com/chat
2. 点"新对话"
3. 粘贴 Prompt 模板 + 该板块所有 divergence 文件内容
4. 等待回复（约5-10分钟）
5. 保存回复到 `translation-workspace/audit/{品种}/audit_{板块名}.md`

#### Prompt 模板位置

`translation-workspace/prompts/audit_prompt_template.md`

#### 板块分组

| 板块 | 节点范围 | 节点数 |
|------|---------|--------|
| 价格信号 | 2.1-2.6 | 6 |
| 供给 | 3.1.1-3.2.4 | 9 |
| 库存 | 4.1-4.5 | 5 |
| 需求 | 5.1-5.3 | 3 |
| 进出口 | 6.1-6.4 | 4 |
| 成本利润 | 7.1-7.3 | 3 |

#### 特殊处理

- **价格信号(2.x)**：Prompt 末尾追加 LME 变量精确化要求
- **每个品种的术语参考**：见 prompt 模板末尾

### Step 2：知几API搜索验证（脚本自动，~100次/品种）

**注意**：知几API限流 1次/秒，脚本已内置 sleep(1)。

等 Step 1 全部完成后，从同花顺回复中提取精确指标名，脚本自动：
- jieba分词
- 搜知几API（SMM + Mysteel 各搜一次）
- 输出映射表：概念名 → 知几ID → 置信度(A/B/C)

**此步骤由你统一执行**（因为需要知几API密钥和缓存DB）。Agent B 会把 Step 1 的回复文件发给你。

### Step 3：人工审核映射表（30分钟/品种）

脚本生成映射表后：
- A级（高置信）→ 直接入库
- B级（可能匹配）→ 人工判断
- C级（搜不到）→ 标备用库

你负责审核 ZN/NI/CU/AL，Agent B 审核 SN/SI/LI/PB。

---

## 四、协同机制

1. **Agent B 做完 Step 1 后**，把 `audit_*.md` 文件推送到 GitHub `translation-workflow` 分支
2. **你 pull 后统一执行 Step 2**（知几搜索），生成映射表
3. **你发映射表给 Agent B 审核**（SN/SI/LI部分），它确认后你入库
4. **PB 最后集中处理**（PB 没有 divergence，需先补发散）

---

## 五、文件结构

```
/home/ubuntu/framework-tree/
├── translation-workspace/          # 新协作空间
│   ├── scripts/
│   │   └── step0_extract.py        # 提取去重脚本
│   ├── prompts/
│   │   └── audit_prompt_template.md # Prompt 模板
│   ├── audit/                       # Step 1 输出（同花顺审计回复）
│   │   ├── ZN/
│   │   │   ├── audit_价格信号.md
│   │   │   ├── audit_供给.md
│   │   │   └── ...
│   │   └── ...
│   └── README.md
├── analysis/iwencai/               # 原始 divergence 文件
│   ├── ZN/
│   │   ├── divergence_*.md         # 30个原始文件
│   │   └── concept_indicators.json # Step 0 输出
│   └── ...
└── docs/
    ├── HANDOVER_20260831_INDICATOR_MATCH.md      # 旧交接文档
    ├── HANDOVER_20260901_INDICATOR_TRANSLATION.md # 初版交接文档
    ├── HANDOVER_AGENT_A.md                        # 本文件
    └── HANDOVER_AGENT_B.md                        # Agent B 交接文档
```

---

## 六、时间预估

| 步骤 | ZN | NI | CU | AL | 合计 |
|------|----|----|----|----|------|
| Step 0 提取去重 | 2min | 2min | 2min | 2min | 8min |
| Step 1 同花顺审计 | 6组×10min=60min | 60min | 60min | 60min | 4h |
| Step 2 知几搜索 | 10min | 10min | 10min | 10min | 40min |
| Step 3 人工审核 | 30min | 30min | 30min | 30min | 2h |
| **你的总工作量** | | | | | **~6.5h** |

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
# 1. 切到工作分支（已切）
cd /home/ubuntu/framework-tree
git checkout translation-workflow

# 2. 跑 Step 0（4个品种）
cd translation-workspace
python scripts/step0_extract.py ZN
python scripts/step0_extract.py NI
python scripts/step0_extract.py CU
python scripts/step0_extract.py AL

# 3. 开始 Step 1 同花顺审计
# 按板块逐个提问，保存回复到 audit/{品种}/audit_{板块}.md
```

---

## 九、注意事项

1. **同花顺每天200次调用**，不要省着用，必要时可多问几次追问细节
2. **知几API限流 1次/秒**，脚本已内置 sleep
3. **图表设计原则**：单指标优先，复合图仅限强相关2个指标
4. **删除项**：统计派生、临时不可追踪、不相关凑数
5. **价格信号板块**：务必追问 LME 精确英文变量名
