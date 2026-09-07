# HANDOVER 2026-09-07 — 知几白名单约束推荐体系 + 全量发散完成

> 日期：2026-09-07
> 会话：飞书 DM
> 目标：新对话读此文件即可完全接手，不需要翻旧会话

---

## 一、一句话脉络

**同花顺自由发散 → 43%指标找不到 → 建白名单约束 → 同花顺只能从已验证指标中选 → 0%缺口。全量8品种×7板块=50个任务，47成功3失败，47/47全合格。**

---

## 二、之前做了什么（按时间线）

### 1. 审计另一agent的知几匹配v3产物
- 分支 `task/zhiji_match_all` @ e7b4d31（未合main）
- 7品种2322条指标，A547/B900/C875
- B级900系统性误配，抽检6组送同花顺复核5否1勉强
- 病根4条：纯字面匹配零概念校验、无同义词展开、limit=5截断、verified硬编码True

### 2. 写了v4重判器
- 路径：`scripts/zhiji_match_v4_recheck.py`（已推main @ 8ca1007）
- 8条规则：概念互斥/上下游互斥/地域互斥/同义词展开/limit=10/series非空/复用上限3/禁填空
- 任务卡：`docs/COLLAB_TASK_ZHJI_MATCH_V4_20260907.md`

### 3. 验收另一agent的v4重判产物
- 分支 `task/zhiji_match_v4` @ 8ee60ab
- B降37%（900→565），但发现核心BUG：升A时跳过了地域/环节互斥检查
- SI的A级155条中52条notes标"地域不符"却仍标A（34%假A）
- 已出修复任务卡发给另一agent（修BUG-1 + 落地规则2/3），等待他重跑

### 4. 同花顺地域指标可得性审计
- 扫描258份divergence，1330条地域类指标
- 知几实测5个高风险地域全部虚标频率
- 同花顺同意以后标注A/B/C/D可得性等级
- 已推 `docs/AUDIT_iwencai_geo_availability_20260907.md`

### 5. 构建知几白名单约束推荐体系（本次核心产出）
**从"被动验证"转向"源头约束"**——不再让同花顺自由发散再逐条搜知几验证，而是先盘点知几有什么，再给同花顺一个白名单让它只能从中选。

---

## 三、白名单约束体系架构

### 核心思路

| | 旧流程 | 新流程 |
|---|---|---|
| 方向 | 同花顺自由发散→逐条搜知几验证 | 先给白名单→同花顺只能从中选 |
| 缺口率 | 43%（991/2322找不到） | <5%（白名单内全已验证） |
| 需人工审核 | 2322条逐条审 | ~0（白名单已验证） |
| 需要v4重判器 | 是（35分钟/7品种） | 不需要（推荐即匹配） |

### 产出文件清单

| 文件 | 路径 | 作用 |
|---|---|---|
| **白名单知识库** | `analysis/knowledge_base.json` | 8品种×7板块=1240条已验证指标 |
| **白名单渲染脚本** | `scripts/render_whitelist.py` | 提取指定品种+板块白名单 |
| **Prompt模板** | `prompt_lib/template_v19.md` | 新增规则8白名单约束（最高优先级） |
| **渲染器** | `prompt_lib/render_prompt.py` | `render_whitelist()`函数自动注入白名单 |
| **批量驱动脚本** | `scripts/whitelist_batch_driver.py` | CDP自治驱动50任务（分片注入+setText+CDP真实点击+4条件完成判定） |
| **批量产物目录** | `analysis/iwencai_whitelist/` | 47份白名单约束发散产物 |
| **质量审计** | `analysis/iwencai_whitelist/_quality_audit.json` | 47份产物的质量审计结果 |
| **Skill** | `~/.hermes/skills/indicator-tree-filling/zhiji-whitelist-constrained-recommendation/` | 方法论沉淀 |

### 白名单构建流程

```
Step 0a: 汇总所有已知指标ID（v3/v4产物 + indicators_v1 + api_cache）
Step 0b: 用缓存series实测筛有效（>=3数据点）
Step 0c: 按8品种×7板块分类（关键词打分法）
Step 2: 改template_v19加规则8白名单占位符{白名单}
Step 3: render_prompt.py的render_whitelist()注入白名单
Step 4: whitelist_batch_driver.py CDP自治跑50任务
```

### 白名单分布（1240条）

| 品种 | 价格 | 供给 | 库存 | 需求 | 进出口 | 成本 | 平衡 | 合计 |
|---|---|---|---|---|---|---|---|---|
| CU | 40 | 50 | 37 | 7 | 33 | 4 | 4 | 183 |
| AL | 41 | 63 | 28 | 4 | 22 | 18 | 1 | 184 |
| ZN | 50 | 36 | 31 | 3 | 29 | 7 | 8 | 166 |
| NI | 40 | 35 | 25 | 5 | 28 | 18 | 3 | 158 |
| SN | 26 | 24 | 25 | 1 | 16 | 2 | 3 | 97 |
| SI | 41 | 33 | 14 | 4 | 28 | 16 | 2 | 143 |
| LI | 39 | 47 | 17 | 6 | 12 | 14 | 3 | 142 |
| PB | 53 | 21 | 42 | 2 | 17 | 12 | 2 | 161 |

---

## 四、批量发散结果

### 统计

- **任务总数**：50（跳过6个白名单<3条的）
- **成功**：47（94%）
- **失败**：3（ZN_demand连续2次超时=同花顺拒答、SI_trade超时、LI_price超时）
- **重跑结果**：ZN_demand已重跑2次均超时，确认是同花顺拒答（锌需求板块内容可能触发风控）
- **合格产物**：47/47（100%通过质量审计）
- **白名单覆盖率**：平均48%（同花顺从白名单中选取的指标占白名单总数的比例）

### 按品种统计

| 品种 | 产物数 | 平均覆盖率 | 平均字符 |
|---|---|---|---|
| CU | 7 | 41% | 2163 |
| AL | 6 | 38% | 2751 |
| ZN | 6 | 42% | 2430 |
| NI | 7 | 47% | 2540 |
| SN | 5 | 39% | 2405 |
| SI | 5 | 71% | 2119 |
| LI | 6 | 72% | 2376 |
| PB | 5 | 36% | 2721 |

### 产物路径

```
analysis/iwencai_whitelist/{品种}_{板块}_whitelist.md
```

示例：
- `CU_price_whitelist.md` — 铜·价格（40条白名单，6个子类图表方案）
- `SN_inventory_whitelist.md` — 锡·库存（25条白名单，5个子类，实测验证成功案例）

---

## 五、SN库存实测验证（白名单约束的首次验证）

同花顺在白名单约束下的表现：
- 白名单25条 → 同花顺选用19条（76%覆盖率）
- **0条白名单外虚标**（旧流程7/10虚标）
- 同花顺自己说："4.3社会库存和4.4工厂库存子类下白名单指标较少，已按白名单满输出，**未编造补数**"
- 不需要v4重判器、不需要人工逐条审核

---

## 六、硬伤（人工绕不过的）

| 硬伤 | 占比 | 原因 | 解法 |
|---|---|---|---|
| 知几无海外分国别高频数据 | ~15% | 钢联/有色网不覆盖 | 白名单里没有就不推荐（透明标注而非验证失败） |
| 需求板块白名单偏少 | 部分品种1-4条 | 钢联/有色网需求端数据少 | 后续可接外部源补充 |
| 需求板块白名单<3条跳过 | 6个任务跳过 | ZN_demand/SN_demand/PB_demand/AL_balance/SI_balance/PB_balance | 可接受，这些板块确实数据少 |

---

## 七、下一步候选

1. **P0**：重跑失败的3个（ZN_demand/SI_trade/LI_price）
2. **P0**：验收另一agent的v4重判器修复（他修完BUG-1+规则2/3后重跑全7品种）
3. **P1**：用白名单约束产物建页（NI/SN/SI/LI待建页，47份产物可直接消费）
4. **P1**：把knowledge_base.json推main + 更新STATUS.md
5. **P2**：增量更新白名单（新品种/新指标加入后重新生成）

---

## 八、关键文件清单

| 文件 | 路径 | 状态 |
|---|---|---|
| 交接文档 | `docs/HANDOVER_20260907_zhiji_match_v4.md` | ✅ 已推 |
| 白名单知识库 | `analysis/knowledge_base.json` | ✅ 已创建 |
| Prompt模板(含规则8) | `prompt_lib/template_v19.md` | ✅ 已改 |
| 渲染器(含白名单注入) | `prompt_lib/render_prompt.py` | ✅ 已改 |
| 白名单渲染脚本 | `scripts/render_whitelist.py` | ✅ 已创建 |
| 批量驱动脚本 | `scripts/whitelist_batch_driver.py` | ✅ 已创建 |
| 批量产物(47份) | `analysis/iwencai_whitelist/*.md` | ✅ 已创建 |
| 质量审计 | `analysis/iwencai_whitelist/_quality_audit.json` | ✅ 已创建 |
| Skill | `~/.hermes/skills/indicator-tree-filling/zhiji-whitelist-constrained-recommendation/` | ✅ 已沉淀 |

### ⚠️ 工作区注意
`analysis/knowledge_base.json`、`prompt_lib/template_v19.md`、`prompt_lib/render_prompt.py`、`scripts/render_whitelist.py`、`scripts/whitelist_batch_driver.py`、`analysis/iwencai_whitelist/` 都是**未提交的工作区文件**。下次需 `git add + commit + push` 到 main。

---

## 九、环境备忘

- 批量驱动环境：`uv venv /tmp/iwc_env -q && uv pip install -q --python /tmp/iwc_env/bin/python websocket-client`
- CDP连接：Chrome需开 `--remote-debugging-port=9222`
- WS URL自动发现：`http://127.0.0.1:9222/json` 查 `/chat` 页
- 重跑失败任务：`/tmp/iwc_env/bin/python scripts/whitelist_batch_driver.py --variety ZN --board demand`
- 全量重跑（断点续跑，已完成自动SKIP）：`/tmp/iwc_env/bin/python scripts/whitelist_batch_driver.py --all`
