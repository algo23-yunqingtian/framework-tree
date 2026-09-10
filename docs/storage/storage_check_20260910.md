# 存储自检与冗余清理报告
生成时间：2026-09-10  · 主机：腾讯云 (Ubuntu, /dev/vda2)

## 1. 磁盘总览

| 项 | 值 |
|---|---|
| 总容量 | 40 GB |
| 已用 | 29 GB (77%) |
| 可用 | 8.7 GB |
| 风险 | ⚠️ 偏高，但主要是可清理的滚动备份占用 |

`df` 显示 `df: error` 无；根分区单分区 `/dev/vda2`。

## 2. 占用 Top 目录（`du --max-depth=1`）

| 大小 | 路径 | 性质 |
|---|---|---|
| 9.8G | /home/ubuntu | 用户家目录汇总 |
| 4.4G | .hermes | Hermes Agent 本体（含 node_modules/venv） |
| 1.2G | db_backups | **数据库滚动备份（最大冗余源）** |
| 614M | .local | Python 本地包 |
| 572M | macro_dashboard | 宏观看板 |
| 502M | analysis | 分析工作区（含 345M db_backups） |
| 490M | unified_venv | 统一 venv |
| 469M | .cache | pip/uv 包缓存 |
| 248M | output | 产出物（agent_setup 140M / agent_split 80M） |
| 216M | framework-tree | 看板主仓 |
| 179M | zinc_dashboard_gh | 锌看板静态 |
| 169M | nickel_dashboard_gh | 镍看板静态 |
| 94M | framework-tree-export | 看板导出副本 |
| 14M | lithium-engine | **HAM 回测项目本体（很小）** |

## 3. 冗余文件清单（按可清理度分类）

### ✅ 可安全清理（重复备份副本 / 临时缓存）—— 约 1.5 GB

| 大小 | 路径 | 理由 |
|---|---|---|
| ~1.1G | db_backups/lme_bloomberg_data_20260828~0910_*.db (14份×68M) | 每日滚动备份，同一天内容，仅保留最新 1-2 份 |
| ~140M | db_backups/有色日度数据_20260828~0903_*.db (6份×15M) | 同上，保留最新 |
| ~290M | analysis/db_backups/indicator_tree_before_20260831_*.db (5份) | 8/31 灌库前快照，已灌完无需保留全部 |
| ~56M | analysis/db_backups/api_cache_before_jsonl_*.db (2份) | JSONL 导出前快照 |
| 223M | .cache/pip | pip 包缓存，可 `pip cache purge` |
| 251M | .cache/uv | uv 包缓存，可 `uv cache prune` |
| ~39M | framework-tree/analysis/backups/api_cache_before_plan_fill_*.db | 旧备份 |

### ⚠️ 需谨慎（先备份再处理，原始数据）

| 路径 | 说明 |
|---|---|
| db_backups/lme_bloomberg_data_20260910_*.db (最新68M) | LME 原始邮件数据库备份，**保留** |
| db_backups/有色日度数据_20260910_*.db (最新15M) | 有色日度最新备份，**保留** |
| ~/.hermes/state.db / kanban.db / cron/*.db | Agent 运行状态库，**禁止删** |
| lithium_calendar/*.db, lc_futures_data/data/*.db | 碳酸锂生产 DB，敏感，**禁止删** |
| nickel_v1.db / mysteel_delivery.db / lead_v2_backup_*.db | 基本面前端 DB，**禁止删** |

### ❌ 禁止删除

| 路径 | 理由 |
|---|---|
| .hermes/hermes-agent/node_modules (1.6G) | Hermes 运行依赖 |
| .hermes/hermes-agent/venv (1.1G) | Hermes 运行依赖 |
| unified_venv (490M) | 分析脚本运行环境 |
| .git (各仓) | commit 历史 |
| *.md 交接文档 / 实验报告 | 核心产出 |

## 4. HAM 项目磁盘占用

HAM 回测项目本体仅 **14M**（lithium-engine 全仓，model_ham 7.1M）。
- 23 个 exp 实验目录（exp404~exp424），每个含 data/reports 子目录
- raw_data/：4 份 CSV（lithium_future 50K / smm_daily 103K / spot_price 21K / fundamental_balance 12K）
- **无大文件**（最大单文件 0.3M）
- 结论：**HAM 本身不是空间瓶颈**，迁移价值在「计算与数据接口」而非「磁盘」

## 5. framework-tree 项目

- 总 216M（.git 80M，非 git 132M）
- 非 git 最大：step3_5metals_search_results.json 4.8M、indicators_v1.json 700K
- analysis/backups 含 1 个 39M 旧 DB 备份 + 若干 JSON 快照
- 全部已在 git 管理内，git log 最新 6cb757f

## 6. 清理建议优先级

| 优先级 | 动作 | 预计释放 | 风险 |
|---|---|---|---|
| P0 | 保留 db_backups 每类最新 1 份，删旧 | ~1.0G | 低（需保留最新） |
| P0 | analysis/db_backups 删 8/31 灌库快照（除最新） | ~290M | 低 |
| P1 | pip/uv cache 清理 | ~470M | 无（可随时重建） |
| P1 | framework-tree 旧 DB 备份删 | ~39M | 低 |
| P2 | 评估 output/agent_setup+agent_split 是否仍需要 | ~220M | 需确认 |

**合计可释放：约 1.8 GB**，磁盘从 77% 降至 ~66%。

> ⚠️ 本报告仅为评估，**未执行任何删除**。等待用户确认后操作。
