# 同花顺→知几→Framework-Tree 指标匹配交接手册

> 日期：2026-09-06
> 作者：主脑 agent（服务器A）
> 目标读者：本地 agent（你）—— 有自己的知几 API 和本地搜索方法
> 仓库：`git@github.com:algo23-yunqingtian/framework-tree.git`（已有读写权限）

---

## 一、你的任务概述

把同花顺问财已发散的 198 个节点回复，逐一对应到知几数据库的真实指标，找到能用的 zhiji_id，回传给主脑统一管理，最终上线到 framework-tree 看板。

**工作流**：读同花顺回复 → 提取推荐指标名 → 在知几搜索 → 验证口径 → 回传 zhiji_id 清单 → 主脑合并到 indicators_v1.json → 建 HTML 页面上线

---

## 二、同花顺产物在哪（GitHub 已上线）

### 产物①：逐节点发散（198份）

路径：`analysis/iwencai/<品种>/decision_<节点号>.md`

| 品种 | 目录 | 文件数 | 说明 |
|---|---|---|---|
| 铜(CU) | `analysis/iwencai/CU/` | 60 | decision_2.1.md ~ decision_7.3.md |
| 铝(AL) | `analysis/iwencai/AL/` | 60 | 同上格式 |
| 锌(ZN) | `analysis/iwencai/ZN/` | 60 | 同上格式 |
| 镍(NI) | `analysis/iwencai/NI/` | 60 | 同上格式 |
| 锡(SN) | `analysis/iwencai/SN/` | 60 | 同上格式 |
| 工业硅(SI) | `analysis/iwencai/SI/` | 58 | 缺 7.3 |
| 碳酸锂(LI) | `analysis/iwencai/LI/` | 19 | 只到 4.4，5.x~7.3 缺 |
| 铅(PB) | `analysis/iwencai/PB/` | 12 | 旧格式：51_diversify_response.md 等，覆盖 5.1/5.2/5.3/7.1/7.2/7.3 |

**每份 decision_*.md 的结构**：含同花顺对该节点的指标推荐（指标名+频率+优先级+理由），约 800~2800 字。

### 产物②：分类范式（48份，宏观框架）

路径：`analysis/iwencai_classify/<品种>_<板块>.md`

8 品种 × 6 板块 = 48 份，每份含：
- **拆分树**（总量→子类→孙类）
- **重点地区/工艺识别**（哪个仓点/工艺最重要）
- **指标推荐 + 优先级排序**（必看/重要/可选/不看）
- **排除理由**（基于工艺占比做减法）

**用法**：分类范式是宏观框架（告诉你该板块该看什么），逐节点发散是微观落地（具体到每个子节点选哪几个指标）。两者配合使用。

### 缺口清单（60个节点未做发散）

| 缺口类型 | 数量 | 说明 |
|---|---|---|
| PB 2.1~4.5（前4板块全缺） | 27 | PB 只做了 5.x/7.x 的旧格式发散 |
| LI 4.5~7.3（后半段缺） | 11 | LI 只做到 4.4 |
| SI 7.3 | 1 | 单个缺口 |
| 板块8 全品种（8.1/8.2/8.3） | 24 | 供需平衡板块，所有品种都没发散 |
| **合计** | **60** | |

> 这 60 个缺口不在你本次任务范围内。主脑会另行安排同花顺补发。

---

## 三、知几搜索原则（核心方法论）

### 3.1 搜索命令

```bash
# 搜索（返回匹配指标列表）
python3 ~/.hermes/scripts/zhiji_api.py search "关键词 关键词 关键词"

# 拉序列（验证口径是否正确）
python3 ~/.hermes/scripts/zhiji_api.py series <zhiji_id> 2015-01-01 2026-09-06
```

> **你的知几 API key 和搜索脚本可能和主脑不同**——你用你自己的工具，搜索原则和方法论通用。

### 3.2 搜索关键词技巧（实测教训）

**铁律：关键词之间用空格分隔**

- ❌ "新加坡铅仓单" → 知几当作整词，返回钴/铝/锡等误命中
- ✅ "新加坡 铅 仓单" → 精准命中 `FU00023414` LME铅注册仓单新加坡

**格式**：`品种 + 仓库/地区 + 指标类型`，三者用空格分隔
- "LME 新加坡 锌"
- "铜 保税区 库存"
- "碳酸锂 产量 中国"
- "锌精矿 加工费"

**备选词策略**（一个指标准备 3-5 个搜索词）：
1. 原词（同花顺推荐的指标名）
2. 同义词（库存↔社库↔厂库，开工率↔产能利用率）
3. 中英混用（warrant=仓单，premium=升贴水）
4. 数字边界（TC加工费搜"50%Zn 加工费"）
5. 英文字母（TOM=三个月期，WAR=仓单）

### 3.3 命中判定标准

| 级别 | 判定 | 处置 |
|---|---|---|
| A 真命中 | name 前缀确为品种名，且字段与指标一致 | ✅ 写入回传清单 |
| B 弱匹配 | name 部分匹配但频率/口径不符 | ⚠️ 标注"占位/需补充" |
| C 未命中 | name 无品种前缀或字段缺失 | ❌ 标注"无公开数据" |

**必须人工审核 name 前缀**：滑动窗口分词法会把"铅锭社会库存"的"社会库存"配到"镁锭社会库存"。

### 3.4 验证口径（搜到≠能直接用）

对每个搜到的 ID，拉最近几期 series 数据验证：
1. **单位对不对**（元/吨 vs 美元/吨 vs 万吨）
2. **频率对不对**（日/周/月/季——同花顺说"周频"但你搜到的是"月频"→口径不对）
3. **数值合理吗**（LME 锌库存应该在几万~几十万吨级，如果数值离谱→可能配错了指标）

### 3.5 典型搜索结果（锌库存实测案例）

| 同花顺推荐 | 知几搜索结果 | 状态 |
|---|---|---|
| LME锌注销仓单 | `FU00016166` LME：锌：注销仓单（日） | ✅ 直接命中 |
| LME锌总库存 | `FU00016163` LME：锌：期货库存（日） | ✅ 直接命中 |
| LME荷兰鹿特丹仓单 | `FU00023481` LME：锌：注册仓单：荷兰：鹿特丹（日） | ✅ 直接命中 |
| 国产锌精矿TC加工费 | `ID01510737` 锌精矿：50%Zn：加工费：白银（日） | ⚠️ 只有白银TC，无国产总量 |
| SMM七地社会库存 | `ID01167321` 锌：库存：中国（月） | ⚠️ 只有月频全国，无周频七地 |
| 上期所广东/天津仓单明细 | 无 | ❌ 知几无仓单地区拆分 |

**经验**：大约 50% 的必看指标知几能直接支撑，30% 搜到但口径不对，20% 完全搜不到。搜不到的进备用库标注"待外部源"。

---

## 四、你与主脑的协作流程

### 4.1 你负责做什么

1. **读同花顺发散**：从 `analysis/iwencai/<品种>/decision_<节点>.md` 提取推荐指标名
2. **知几搜索**：用你的 API 和搜索方法，逐个指标搜索知几
3. **验证口径**：拉 series 验证单位/频率/数值合理性
4. **回传清单**：按指定格式产出 JSON 文件

### 4.2 回传格式

每个品种产出一份 JSON 文件，路径：`analysis/zhiji_match/<品种>_zhiji_match.json`

```json
{
  "variety": "ZN",
  "agent": "你的标识",
  "date": "2026-09-06",
  "matches": [
    {
      "node": "4.1",
      "node_name": "交易所库存",
      "iwencai_indicator": "LME锌总库存",
      "iwencai_priority": "必看",
      "zhiji_id": "FU00016163",
      "zhiji_name": "LME：锌：期货库存（日）",
      "zhiji_freq": "日",
      "zhiji_unit": "吨",
      "match_level": "A",
      "verified": true,
      "notes": ""
    },
    {
      "node": "4.1",
      "iwencai_indicator": "上期所广东仓单",
      "iwencai_priority": "重要",
      "zhiji_id": null,
      "zhiji_name": null,
      "match_level": "C",
      "verified": false,
      "notes": "知几无仓单地区拆分，需接上期所原始数据源"
    }
  ]
}
```

### 4.3 提交方式

```bash
# 在你的分支上提交
git checkout -b task/<品种>_zhiji_match
git add analysis/zhiji_match/<品种>_zhiji_match.json
git commit -m "[B] <品种>知几指标匹配结果: X命中/Y弱匹配/Z未命中"
git push origin task/<品种>_zhiji_match
# 开 PR
gh pr create --fill
```

### 4.4 主脑负责做什么

1. **回收校验**：`python3 scripts/reclaim.py` 校验你的 PR
2. **合并到 indicators_v1.json**：主脑为底，只追加你的已验证条目
3. **建 HTML 页面**：用 build 脚本生成页面 + 数据 + 门禁
4. **推 GitHub Pages**：最终上线到 framework-tree 看板

---

## 五、framework-tree 仓库导航

### 5.1 树结构定义

`data/tree_config.json` 定义了完整的指标树：

```
8品种 × 6板块 × 33个节点
板块: 价格信号(2.x) / 供给(3.x) / 库存(4.x) / 需求(5.x) / 进出口(6.x) / 成本利润(7.x) / 供需平衡(8.x)
```

### 5.2 指标元数据

`data/indicators_v1.json`（1290 条，v3.62）—— 指标定义/知几ID/单位/主图副图归属的唯一真源。

### 5.3 既有页面

HTML 页面在仓库根目录（`zn_4_1.html` 等），数据点硬编码焊死在 HTML 里。

### 5.4 必读文档

| 文档 | 内容 |
|---|---|
| `AGENTS.md` | 新 agent 入职总入口 |
| `STATUS.md` | 当前进度唯一真源 |
| `docs/COLLABORATION_PLAYBOOK.md` | 全流程 11 章 |
| `docs/iwencai_methodology_20260903.md` | 同花顺通用6条标准+4层校验 |
| `docs/iwencai_board_paradigm_20260903.md` | 分板块 P0-P4 分层范式 |
| `docs/iwencai_P0P4_copper_demo_20260903.md` | 铜库存 P0-P4 完整分析演示 |
| `docs/HANDOVER_20260904_zn_stock.md` | 锌库存试点验证结果 |

### 5.5 开工前必做

```bash
git clone git@github.com:algo23-yunqingtian/framework-tree.git
cd framework-tree
git fetch origin && git rebase origin/main
bash scripts/bootstrap_agent.sh   # 6项自检
python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print('指标数:', len(d['indicators']))"
# 指标数必须 ≥ 1290（当前 main 版本）
```

---

## 六、与研究员数据库的对比（你提到的）

你提到打算把同花顺推荐指标与研究员数据库对比，看能否添加。建议流程：

1. 从同花顺发散中提取所有推荐指标名（约 10-15 个/节点）
2. 在知几搜索后，把"搜不到"的指标整理成清单
3. 拿这份清单去研究员数据库比对：
   - 研究员数据库有 → 直接引用数据源，标注来源
   - 研究员数据库也没有 → 标注"无公开数据源，需调研获取"
4. 把比对结果一并在 JSON 的 `notes` 字段标注

---

## 七、P0-P4 分析范式（同花顺方法论精华）

主脑在9月3日从同花顺现场提问中提炼了 P0-P4 分层体系，对指标筛选有直接指导：

| 层级 | 回答什么 | 通用标准 |
|---|---|---|
| P0 定方向 | 供需松还是紧 | 全球/全国总量口径，官方源 |
| P1 定节奏 | 拐点何时来 | 内部结构占比，领先信号 |
| P2 验真实 | 总量真实吗 | 第三方高频调研 |
| P3 找错配 | 为什么矛盾 | 地理/品牌结构 |
| P4 防失真 | 数据会骗我吗 | 隐性变量 |

**主图只放 P0+P1**，P2-P4 进辅助。搜索知几时，优先找 P0 层指标（总量口径），其次 P1（结构占比）。

### 三个"不要"

1. 不要用价格代理指标替代节点指标（价格是结果变量）
2. 不要用高频但窄口径数据替代总量口径（如用分库替代全球总量）
3. 不要忽略内外口径映射关系（LME主图+SHFE副图）

---

## 八、协作任务卡（一键整段可复制转发）

```text
# 知几指标匹配任务

## 你的任务
读 framework-tree 仓库里 analysis/iwencai/<品种>/ 目录下的同花顺发散文件（decision_<节点>.md），
为每个节点推荐的指标在知几数据库搜索对应的 zhiji_id，验证口径后回传 JSON。

## 开工步骤
1. git clone git@github.com:algo23-yunqingtian/framework-tree.git
2. cd framework-tree && git fetch origin && git rebase origin/main
3. bash scripts/bootstrap_agent.sh
4. 选一个品种开始（建议从 ZN 锌开始，主脑已做过试点验证可对照）
5. 读 analysis/iwencai/ZN/decision_2.1.md，提取所有推荐指标
6. 逐个在知几搜索：python3 ~/.hermes/scripts/zhiji_api.py search "品种 关键词 指标类型"
7. 拉 series 验证口径：python3 ~/.hermes/scripts/zhiji_api.py series <id> 2015-01-01 2026-09-06
8. 产出 analysis/zhiji_match/ZN_zhiji_match.json（格式见 docs/IWENCAI_ZHIJI_HANDBOOK_20260906.md 第四章）
9. git checkout -b task/ZN_zhiji_match && git add analysis/zhiji_match/ && git commit -m "[B] ZN知几指标匹配" && git push origin task/ZN_zhiji_match && gh pr create --fill

## 搜索原则（铁律）
- 关键词之间用空格分隔："新加坡 锌 仓单" 不是 "新加坡锌仓单"
- 每个指标准备 3-5 个备选搜索词（原词+同义词+中英混用）
- 搜到后必须拉 series 验证：单位对不对、频率对不对、数值合理吗
- 滑动窗口会误匹配（"铅锭社库"配到"镁锭社库"），必须人工审核 name 前缀
- 约50%直接命中、30%口径不对、20%完全搜不到——搜不到的标注"无公开数据"

## 完成标准
- 每个品种一份 JSON，含所有节点的匹配结果（A命中/B弱匹配/C未命中）
- PR 标题格式：[B] <品种>知几指标匹配: X命中/Y弱匹配/Z未命中
- 完成一个品种后再做下一个，不要同时开多个品种

## 主脑会做什么
- 回收你的 PR，校验格式
- 把 A 级命中合并到 indicators_v1.json
- 用 build 脚本建 HTML 页面 + 数据 + 门禁
- 推 GitHub Pages 上线

## 优先级
ZN > CU > AL > NI > SN > SI > LI > PB（ZN 已有试点验证，最适合先做）
```

---

## 九、注意事项

1. **同花顺回复有噪音**：同花顺 AI 回复本身含归属错配（如把"LME镍库存·迪拜分库"当成正主），不能盲抄，必须人工判断口径
2. **correction 文档也有噪音**：`translation-workspace/correction/` 目录下的矫正文档虽是 A 级，但同花顺原始回复的归属错配会带进来
3. **知几 API 配额**：每日有搜索次数限制（约 10000 次），省着用，批量搜索时注意计数
4. **板块8（供需平衡）特殊**：这 24 个节点全品种都没发散，不需要你搜索——主脑会另行安排
5. **PB 品种格式不同**：PB 的发散文件是旧格式（`51_diversify_response.md`），不是 `decision_*.md`，读取时注意文件名映射
6. **LI 品种只到 4.4**：LI 的 5.x~7.3 共 14 个节点没有发散文件，不在你本次任务范围内

---

## 十、联系主脑

- 你提交 PR 后，主脑会自动收到通知
- 如果遇到搜索方法论问题（搜不到/口径对不上），在 PR description 里写明，主脑会 review 后给建议
- 如果发现同花顺回复本身有错（推荐的指标不属于该节点），标注在 JSON 的 notes 字段
- **不要直接 push main**，所有提交走 PR
