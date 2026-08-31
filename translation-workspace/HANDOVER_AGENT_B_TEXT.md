# Agent B 交接文档（纯文字版，可直接复制粘贴）

## 任务目标

把同花顺 divergence 文件里的**概念指标名**翻译成**SMM/Mysteel/LME 真实指标名**，建立完整映射表。

## 你的分工

- **SN（锡）**：30个节点 ✅
- **SI（硅）**：29个节点 ⚠️ 缺7.3
- **LI（碳酸锂）**：19个节点 ⚠️ 缺11个
- **PB（铅）**：0个节点 ❌ 跳过

**总计**：78个节点，约3小时工作量。

## 环境准备

### 1. 配置 GitHub SSH key

```bash
# 生成SSH key（如果没有）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 添加到 ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# 复制公钥
cat ~/.ssh/id_ed25519.pub

# 到 GitHub → Settings → SSH and GPG keys → New SSH key → 粘贴公钥
```

### 2. 克隆仓库

```bash
git clone git@github.com:algo23-yunqingtian/framework-tree.git
cd framework-tree
git fetch origin translation-workflow
git checkout translation-workflow
```

## 工作流（2步）

### Step 0：提取概念指标（脚本自动，5分钟）

```bash
cd translation-workspace
python scripts/step0_extract.py SN
python scripts/step0_extract.py SI
python scripts/step0_extract.py LI
```

输出：`analysis/iwencai/{品种}/concept_indicators.json`

### Step 1：同花顺审计（每组10-15分钟）

#### 操作流程

1. 打开 https://www.iwencai.com/chat
2. 点"新对话"
3. 复制 Prompt 模板（见下方）
4. 替换 `{品种}` 和 `{板块名}`
5. 粘贴该板块所有 divergence 文件内容
6. 等待回复（5-10分钟）
7. 保存到 `translation-workspace/audit/{品种}/audit_{板块名}.md`
8. 提交到 GitHub

```bash
mkdir -p translation-workspace/audit/SN
git add translation-workspace/audit/
git commit -m "SN: 供给板块审计完成"
git push origin translation-workflow
```

#### Prompt 模板

```
你是{品种}基本面资深分析师，同时也是期货公司研报图表设计的审稿专家。

以下是我现有的「{品种}·{板块名}」维度共{N}个子节点的全部图表和指标方案。请你做以下5项工作：

【任务1：删除不合格指标】严格删除以下类型：
- 统计派生类：近N年均值、标准差、分位数、环比、同比、增速、日增减、变化方向
- 临时不可追踪：检修量、排产计划、停产通知、减产损失量
- 不相关凑数：如在TC/成本图里出现产量指标
- 无意义重复：同一指标的不同频率版本只保留最核心的那个

【任务2：跨节点去重+归属调整】
- 同一指标出现在多个子节点 → 只保留最贴切的那个子节点
- 某指标更适合其他子节点 → 移动过去，说明理由

【任务3：补充遗漏指标】
- 删除后如有空位，推荐能说明该子节点核心问题的指标替代
- 参考主流期货公司研报（中信/国泰君安/金瑞/一德/中泰等）的图表习惯
- 每个子节点目标 5-6 张图，不要太少也不要太多

【任务4：重新设计图表组合】
- 每张图只放强相关指标，不强凑多个弱相关指标
- 优先单指标时序图，复合图仅限真正强相关的2个指标（如TC+利润）
- 删除所有季节性统计图（近N年叠加+分位带这种），除非该指标确实有强季节性且市场关注
- 图表形态要参考研报惯例（如TC一般画历史时序，不画季节性）

【任务5：精确指标名（最重要！）】

核心要求：
1. **指标名称必须与平台实际命名完全一致**（不是近似名），就像在平台搜索框里能直接搜到一样
2. **说明该指标的频率**（日频/周频/月频/季频）**和可得性**（公开/付费/仅VIP）
3. **如果平台没有统一口径，直接说"无统一口径"**，不要给近似替代
4. **如果两个平台命名不同，分别列出各自平台的最可能命中名称**

对最终保留的每个指标，用表格输出：
| 子节点 | 图名称 | 指标名 | SMM官方全称（精确） | Mysteel官方全称（精确） | LME英文变量名(如适用) | 频率 | 可得性 | 单位 |

如果是LME相关指标（升贴水、价差、仓单、持仓等），务必给出LME的精确英文变量名。
如果某指标在SMM和Mysteel都没有对应，直接说"无统一口径"，不要硬凑近似名。

品种术语参考：{品种术语}

【现有方案如下】
（此处粘贴该板块所有子节点的divergence文件内容）
```

#### 品种术语参考

**锡 (SN)**：精锡、锡精矿、再生锡、锡锭、焊锡、锡化工、锡材

**硅 (SI)**：工业硅、多晶硅、单晶硅、有机硅、硅合金、硅微粉、金属硅

**碳酸锂 (LI)**：碳酸锂、氢氧化锂、锂辉石、锂云母、盐湖卤水、电池级碳酸锂、工业级碳酸锂

#### 价格信号板块特殊要求

对于 2.x 价格信号板块，在 Prompt 末尾追加：

```
【特别要求：LME变量名精确化】
价格信号板块的指标务必给出LME精确英文变量名，包括但不限于：
- LME Cash-3M spread（现货-3月期价差）
- LME cancellation ratio（注销仓单比）
- LME warranted vs unwarranted stocks（注册仓单 vs 注销仓单）
- SHFE-LME比价/进口盈亏
- 近月-远月价差（back/contango）
- LME持仓集中度（COT report字段名）
```

#### 板块分组

| 板块 | 节点范围 | SN | SI | LI |
|------|---------|----|----|-----|
| 价格信号 | 2.1-2.6 | 6 | 6 | 6 |
| 供给 | 3.1.1-3.2.4 | 9 | 9 | 5 |
| 库存 | 4.1-4.5 | 5 | 5 | 4 |
| 需求 | 5.1-5.3 | 3 | 3 | 0 |
| 进出口 | 6.1-6.4 | 4 | 4 | 0 |
| 成本利润 | 7.1-7.3 | 3 | 2 | 0 |
| **合计** | | **30** | **29** | **19** |

## 完整工作流（4步端到端）

### Step 2：分词提取精确指标名（每个板块5-10分钟）

同花顺回复里会有一张指标表格，你需要从中提取 SMM/Mysteel 官方全称列，然后做分词拆解。

#### 2a. 从回复中提取指标名

从同花顺回复的表格里，提取以下列：
- 指标名（原始概念名）
- SMM官方全称（精确）
- Mysteel官方全称（精确）
- LME英文变量名

保存为 JSON：`translation-workspace/extracted/{品种}/{板块}_extracted.json`

格式：
```json
[
  {
    "concept_name": "锌精矿TC水平",
    "smm_name": "锌精矿加工费(国产)",
    "mysteel_name": "锌精矿加工费",
    "lme_name": "Zinc Concentrate TC",
    "frequency": "周频",
    "availability": "付费"
  }
]
```

#### 2b. 分词拆解（⚠️ 关键步骤！不要跳过）

**为什么必须分词？**
同花顺返回的"精确名"（如"锌精矿加工费(国产)"）直接拿去知几搜，大概率搜不到！因为知几的指标命名风格和同花顺不同。必须拆成关键词组合，用多个关键词去知几模糊搜索。

**分词示例**：

| 同花顺精确名 | 分词结果（搜索关键词） |
|------------|---------------------|
| 锌精矿加工费(国产) | ["锌精矿", "加工费"] → 搜"锌精矿 加工费" |
| 电解锌冶炼利润 | ["电解锌", "冶炼", "利润"] → 搜"电解锌 利润" 或 "冶炼利润 锌" |
| LME锌库存 | ["LME", "锌", "库存"] → 搜"LME 锌 库存" 或 "lme zinc stocks" |
| SHFE锌仓单注册量 | ["SHFE", "锌", "仓单"] → 搜"锌 仓单" |
| 精炼锌产量(月) | ["精炼锌", "产量"] → 搜"精炼锌 产量" 或 "锌锭 产量" |
| 锌矿进口盈亏 | ["锌矿", "进口", "盈亏"] → 搜"锌 进口盈亏" |

**分词规则**：
1. 英文部分（LME/SHFE/TC等）保持完整
2. 中文按"品种+产品+指标类型"三层拆分
3. 括号内修饰词（国产/进口）单独拆出
4. 去掉"近N年"、"同比"、"环比"、"月"、"周"等统计/频率词
5. 同一指标准备 2-3 组不同关键词组合（SMM风格 + Mysteel风格 + 通用风格）

**为什么准备多组关键词？**
知几数据库可能用SMM的命名，也可能用Mysteel的命名，也可能用通用命名。如果第一组搜不到，换第二组再搜。3组都搜不到才标C级。

#### 2c. 去重合并

所有板块提取完后，合并去重（同一指标可能在多个板块出现）：
```bash
cd translation-workspace
python scripts/step2_merge_extracted.py {品种}
```

输出：`translation-workspace/extracted/{品种}/all_unique_indicators.json`

### Step 3：知几网页搜索验证（每个指标2-3分钟，总计约2小时）

Agent B 自己去知几网页搜索每个指标。

#### 操作流程

1. 打开 https://zhiji.io （或知几数据平台地址）
2. 在搜索框输入分词后的关键词（如"锌精矿 加工费"）
3. 查看搜索结果，找到最匹配的指标
4. 记录知几ID（格式如 FU00014997）
5. 标记置信度：
   - **A级**（高置信）：名称完全一致或高度匹配
   - **B级**（可能匹配）：含义相近但名称有差异，需人工确认
   - **C级**（搜不到）：知几数据库无对应指标

#### 搜索技巧

1. **先用精确全称搜**（如"锌精矿加工费"），找不到再用分词关键词
2. **换关键词组合**：SMM名搜不到就换Mysteel名，再换LME英文名
3. **模糊搜索**：只搜核心词（如"锌 加工费"、"锌 TC"）
4. **英文搜索**：LME指标用英文搜（如"zinc stocks"、"zinc warrant"）
5. **搜3次还找不到**：标记C级，不要硬凑

#### 输出格式

保存为 JSON：`translation-workspace/zhiji_results/{品种}/zhiji_{板块}.json`

```json
[
  {
    "concept_name": "锌精矿TC水平",
    "search_keywords": ["锌精矿", "加工费", "TC"],
    "zhiji_id": "FU00014997",
    "zhiji_name": "锌精矿加工费(国产矿)",
    "confidence": "A",
    "source": "SMM"
  },
  {
    "concept_name": "锌精矿进口盈亏",
    "search_keywords": ["锌精矿", "进口", "盈亏"],
    "zhiji_id": null,
    "zhiji_name": null,
    "confidence": "C",
    "source": null
  }
]
```

### Step 4：生成映射表（每个品种10分钟）

合并所有板块的知几搜索结果，生成最终映射表：

```bash
cd translation-workspace
python scripts/step4_generate_mapping.py {品种}
```

输出：`translation-workspace/mapping/{品种}/final_mapping.csv`

格式：
| 同花顺概念名 | SMM/Mysteel精确名 | 知几ID | 知几名称 | 置信度 | 备注 |
|------------|-----------------|--------|---------|--------|------|
| 锌精矿TC水平 | 锌精矿加工费(国产) | FU00014997 | 锌精矿加工费(国产矿) | A | - |
| 锌精矿进口盈亏 | 锌矿进口盈亏 | - | - | C | 待备用库 |

#### 映射表汇总统计

每个品种完成后，输出统计：
- A级数量/占比（目标 >60%）
- B级数量/占比（需人工确认）
- C级数量/占比（进备用库）

### Step 5：提交 + 通知

1. 提交映射表到 GitHub：
```bash
git add translation-workspace/
git commit -m "{品种}: 完成端到端映射表"
git push origin translation-workflow
```

2. 通知 Agent A（飞书消息）：
```
我已完成 {品种} 的端到端翻译工作流：
- Step 1 同花顺审计 ✅
- Step 2 分词提取 ✅
- Step 3 知几搜索 ✅ (A级X个, B级Y个, C级Z个)
- Step 4 映射表 ✅
文件已推送到 translation-workflow 分支。
请拉取并合并到主映射表。
```

## 注意事项

1. **同花顺每天200次调用**，不要省着用
2. **图表设计原则**：单指标优先，复合图仅限强相关2个指标
3. **删除项**：统计派生、临时不可追踪、不相关凑数
4. **价格信号板块**：务必追问 LME 精确英文变量名
5. **每完成一个板块就提交**，方便 Agent A 同步进度

## 时间预估

| 步骤 | SN(30) | SI(29) | LI(19) | 合计 |
|------|--------|--------|--------|------|
| Step 0 | 2min | 2min | 2min | 6min |
| Step 1 | 60min | 60min | 40min | ~2.5h |
| **总计** | | | | **~3h** |

## 文件结构

```
framework-tree/
├── translation-workspace/
│   ├── scripts/step0_extract.py
│   ├── prompts/audit_prompt_template.md
│   └── audit/{品种}/audit_{板块}.md
├── analysis/iwencai/
│   ├── SN/divergence_*.md (30个)
│   ├── SI/divergence_*.md (29个)
│   └── LI/divergence_*.md (19个)
└── docs/
    ├── HANDOVER_AGENT_A.md
    └── HANDOVER_AGENT_B.md
```

## 常见问题

**Q: PB 怎么办？**  
A: 跳过，等其他品种做完后 Agent A 集中补。

**Q: SI 缺 7.3 / LI 缺 11 个节点？**  
A: 跳过缺失的节点，只跑现有的。

**Q: 同花顺返回格式不对？**  
A: 追问要求严格按表格格式输出，或手动整理后再保存。

**Q: 知几搜索谁做？**  
A: Agent A 统一做（它有API密钥）。你只需推送 Step 1 回复。
