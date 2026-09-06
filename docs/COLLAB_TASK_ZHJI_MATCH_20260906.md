# 任务卡 · 同花顺198份回复 → 知几指标搜索与落盘（今日完成）

> 派发方：主脑 agent（服务器A）
> 执行方：你（另一台服务器的 deepseek agent，有自己的知几API/浏览器搜索方法）
> 日期：2026-09-06
> 目标：今天内把仓库里已有的同花顺回复逐品种逐节点搜完知几，能搜到的落盘成可数据化管理表格，并汇报搜索结果。

## 一、你的任务（一句话）

读 framework-tree 仓库里 `analysis/iwencai/<品种>/` 下的同花顺发散文件，对每个节点推荐的指标在知几数据库搜索对应指标，验证口径，能搜到的落盘成「知几指标名+代码」JSON 表格，搜不到的明确标注，今天内完成并汇报。

## 二、开工步骤（照顺序执行）
## 二、关键网址与导航

### 2.1 GitHub 仓库
- 仓库地址：https://github.com/algo23-yunqingtian/framework-tree
- 克隆命令：git clone git@github.com:algo23-yunqingtian/framework-tree.git
- 仓库浏览器界面（看文件目录树、读文档、看 diff）：https://github.com/algo23-yunqingtian/framework-tree

### 2.2 GitHub Pages 线上看板（最终产出）
- 网址：https://algo23-yunqingtian.github.io/framework-tree/
- 这就是 framework-tree 指标看板的线上地址。你做完的指标最终会通过主脑 build 成 HTML 页面发布到这里。
- 你可以在浏览器里打开这个网址看看现有页面长什么样、哪些品种哪些节点已有页面。

### 2.3 同花顺问财（同花顺AI问答平台，本任务不需要你访问）
- 网址：https://www.iwencai.com/chat
- 同花顺的发散已经由主脑完成（仓库 analysis/iwencai/ 里的 decision_*.md 就是回复）。你不需要自己上同花顺提问，只需要读仓库里已有的回复文件。

### 2.4 知几数据库（你的搜索目标）
- 知几 API 客户端脚本：~/.hermes/scripts/zhiji_api.py（主脑版，你有你自己的就用你自己的）
- 搜索命令示例：python3 ~/.hermes/scripts/zhiji_api.py search "新加坡 锌 仓单"
- 拉序列验证：python3 ~/.hermes/scripts/zhiji_api.py series FU00016163 2015-01-01 2026-09-06
- 如果你有自己服务器上的知几搜索工具或浏览器搜索方法，用你自己的，搜索方法论通用。

### 2.5 仓库内关键文档（clone 后在本地读，或直接在 GitHub 网页上读）
| 文档 | 仓库内路径 | 说明 |
|---|---|---|
| 本任务卡 | docs/COLLAB_TASK_ZHJI_MATCH_20260906.md | 你正在读的这份 |
| 完整交接手册 | docs/IWENCAI_ZHIJI_HANDBOOK_20260906.md | 主方法论（搜索原则+命中判定+口径验证） |
| AGENTS.md | AGENTS.md | 新 agent 入职总入口（必读） |
| STATUS.md | STATUS.md | 全局进度唯一真源 |
| 树结构定义 | data/tree_config.json | 8品种×6板块×33节点的完整目录树 |
| 指标元数据 | data/indicators_v1.json | 1290条已注册指标（你的搜索结果最终合并到这里） |
| 同花顺逐节点发散 | analysis/iwencai/<品种>/decision_<节点>.md | 198份回复（你的搜索输入） |
| 同花顺分类范式 | analysis/iwencai_classify/<品种>_<板块>.md | 48份宏观框架（参考用） |
| 锌库存试点报告 | docs/HANDOVER_20260904_zn_stock.md | ZN库存知几搜索试点结果（可对照） |
| 同花顺P0-P4方法论 | docs/iwencai_methodology_20260903.md | 6条标准+4层校验+速查表 |
| 分板块P0-P4范式 | docs/iwencai_board_paradigm_20260903.md | 库存/供给/进出口分层 |
| 铜库存完整演示 | docs/iwencai_P0P4_copper_demo_20260903.md | P0-P4用铜走一遍的示例 |

## 三、开工步骤（照顺序执行）
1. git clone git@github.com:algo23-yunqingtian/framework-tree.git
2. cd framework-tree
3. git fetch origin && git rebase origin/main
4. 必读（按顺序，不要跳）：
   - AGENTS.md
   - docs/IWENCAI_ZHIJI_HANDBOOK_20260906.md（← 完整交接手册，主方法论都在这）
   - docs/COLLAB_TASK_ZHJI_MATCH_20260906.md（← 这张任务卡）
   - STATUS.md
   - 可选：打开浏览器看 https://algo23-yunqingtian.github.io/framework-tree/ 了解看板长什么样
5. 确认指标库基线：python3 -c "import json; d=json.load(open('data/indicators_v1.json')); print(len(d['indicators']))"
   → 必须 ≥ 1290。少了说明基线旧，先 git pull。
## 三、任务范围（已确认的418份同花顺产物）

### A. 逐节点发散（✱ 本次搜索的主体，198份）

路径 analysis/iwencai/<品种>/decision_<节点号>.md（约800-2800字/份，含推荐指标+频率+优先级+理由）：

- ZN 锌: 60份（2.1~7.3）← 主脑已做过试点，搜索完可与 docs/HANDOVER_20260904_zn_stock.md 对照
- CU 铜: 60份
- AL 铝: 60份
- NI 镍: 60份
- SN 锡: 60份
- SI 工业硅: 58份（缺 7.3）
- LI 碳酸锂: 19份（只到 4.4，5.x~7.3 没有，跳过）
- PB 铅: 6个节点的旧格式文件（51~53_diversify_response.md 对应节点5.1/5.2/5.3，71/72/73_diversify_response.md 对应7.1/7.2/7.3）

### B. 分类范式（参考用，48份，不用逐个搜）

路径 analysis/iwencai_classify/<品种>_<板块>.md
作用：8品种×6板块的宏观框架（拆分树+必看/重要/可选/不看+排除理由），帮你理解每个板块该看什么。搜节点指标前先读对应板块范式，理解优先级再动手。

### C. 明确的缺口（不用你做）

板块8(8.1/8.2/8.3 供需平衡)全品种24份、PB 2.x~6.x共27份、LI 5.x~7.3共11份、SI 7.3 共1份 —— 同花顺还没发散，均无回复文件，跳过。

## 四、知几搜索规范（铁律，违反会被打回）

### 4.1 限频
- 两次请求之间间隔 ≥1 秒（sleep 1），禁止连续快速请求。
- 批量搜索请写脚本循环 + 每轮 sleep 1，不要手动一条条敲。
- 优先用你自己的 zhiji API 客户端 / 浏览器搜索方法。若用浏览器：走你之前和主脑约定的本地 Chrome/CDP 流程，每搜一个指标摘录「指标名称+指标代码」，不要截图代替文字。

### 4.2 关键词构造（实测教训，最重要）
- 关键词之间必须用空格分隔：搜 "新加坡 锌 仓单"，不要搜 "新加坡锌仓单"（整词会误命中钴/铝/锡）。
- 格式：品种 + 仓库/地区 + 指标类型，三者空格分隔。例：
  - "LME 新加坡 锌"
  - "铜 保税区 库存"
  - "碳酸锂 产量 中国"
  - "锌精矿 加工费"
- 每个指标准备 3-5 个备选搜索词再放弃：原词 + 同义词（库存↔社库↔厂库、开工率↔产能利用率）+ 中英混用（warrant/仓单、premium/升贴水）+ 数字边界（TC加工费 → "50%Zn 加工费"）+ 英文词（TOM=三个月期、WAR=仓单）。
- 报「搜不到」前必须换至少3种关键词组合，别拿到第一个空结果就下结论。

### 4.3 命中判定
| 级别 | 判定标准 | 处置 |
|---|---|---|
| A 真命中 | name 前缀确为品种名，字段与指标一致 | 落盘 |
| B 弱匹配 | name 部分匹配但频率/口径不符 | 落盘但 match_level=B，notes 写明差异 |
| C 未命中 | name 无品种前缀 / 字段缺失 | 落盘 match_level=C，notes 写明"无公开数据/已试关键词" |

### 4.4 口径验证（搜到 ≠ 能直接用）
每个 A/B 级命中必须拉序列验证：
- 单位对不对（元/吨 vs 美元/吨 vs 万吨）
- 频率对不对（同花顺说周频，你搜到月频 → 口径不符 → B级）
- 数值合理吗（LME锌库存应在几万~几十万吨级，离谱=配错指标）
- 验证命令参考（你有自己的客户端就用自己的）：python3 ~/.hermes/scripts/zhiji_api.py series <zhiji_id> 2015-01-01 2026-09-06

### 4.5 红线
- 不要盲抄同花顺推荐名 — 同花顺回复本身会有归属错配（例如把"LME镍库存·迪拜分库"当正主），必须以知几实测为准。
- 不要把"铅锭社库"匹配到"镁锭社库"这类滑动窗口误命中 — 人工核对 name 前缀必须是正确品种。
- 拿不准的标记 B 级 + notes 说明，不要硬标 A。

## 五、落盘格式（每个品种一份 JSON，可数据化管理）

路径：analysis/zhiji_match/<品种>_zhiji_match.json，格式：

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
      "node_name": "交易所库存",
      "iwencai_indicator": "上期所广东仓单",
      "iwencai_priority": "重要",
      "zhiji_id": null,
      "zhiji_name": null,
      "zhiji_freq": null,
      "zhiji_unit": null,
      "match_level": "C",
      "verified": false,
      "notes": "知几无仓单地区拆分；已试'上期所 广东 仓单''广东 锌 仓单''SHFE 广东'均无"
    }
  ]
}

要求：
- 同一个品种内所有节点的指标都整理进这一份 JSON（一个品种一个文件，不要散）。
- B 级和 C 级必须写 notes（B 写差在哪：频率/口径/单位；C 写试过哪些关键词）。
- JSON 里不要写死任何敏感 key，只放指标元数据。

## 六、汇报要求

1. 每个品种完成后，在仓库 STATUS.md「近期变更记录」加一行（格式：[DOC] <品种>知几匹配 X命中/Y弱匹配/Z未命中）。
2. 全部完成后（或今晚收工时），把 git 提交推送到自己的分支并开 PR：
   - git checkout -b task/zhiji_match_all
   - git add analysis/zhiji_match/ STATUS.md
   - git commit -m "[B] 知几指标匹配: 各品种命中统计见STATUS"
   - git push origin task/zhiji_match_all
   - gh pr create --fill
3. 给用户/主脑的最终汇报（消息里直接写，别只在 PR 里）：
   - 每个品种：文件数、A命中数、B弱匹配数、C未命中数
   - 哪些高频指标知几完全没有（C 级汇总清单）
   - 有没有发现同花顺推荐本身有问题的（notes 里标了就行）

## 七、优先级与今日节奏

- 优先顺序：ZN（试点可对照）→ CU → AL → NI → SN → SI → LI → PB
- 建议节奏：先做 ZN 2.1~2.6（价格信号6个节点）当样板，跑通格式，再按品种铺开。
- 今日目标：198 份回复全部过一遍。做不完就按品种顺序做到哪算哪，但至少 ZN+CU+AL 三个主品种完成。

## 八、完成标准（主脑验收看什么）

- 每品种 analysis/zhiji_match/<品种>_zhiji_match.json 存在且字段齐全
- A/B 级命中都经过 series 验证（verified=true）
- C 级都有 notes 说明尝试过的关键词
- STATUS.md 有变更记录
- PR 已开，最终汇报已给