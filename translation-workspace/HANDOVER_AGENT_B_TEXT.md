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

## 协同机制

1. **每完成一个板块就提交**
   ```bash
   git add translation-workspace/audit/
   git commit -m "{品种}: {板块} 审计完成"
   git push origin translation-workflow
   ```

2. **全部完成后通知 Agent A**（飞书消息）
   ```
   我已完成 SN/SI/LI 的 Step 1 同花顺审计，
   文件已推送到 translation-workflow 分支。
   请执行 Step 2 知几搜索。
   ```

3. **Agent A 会做**：
   - 拉取你的审计回复
   - 提取精确指标名
   - 跑知几API搜索（限流1次/秒）
   - 生成映射表

4. **你审核映射表**（Agent A 发给你）
   - A级（高置信）→ 确认
   - B级（可能匹配）→ 人工判断
   - C级（搜不到）→ 标备用库

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
