# 腾讯云服务器工程资产盘点报告

> 生成时间：2026-09-11  
> 扫描范围：/home/ubuntu 全量目录  
> 约束：只读巡检，未修改/删除任何文件  
> 生成者：Hermes Agent (glm-5.2)

---

## 模块一：当前运行进程 & 活跃项目清单

### 1.1 Systemd 服务（running）

| 服务名 | 用途 | 启动日期 |
|--------|------|----------|
| browser-vnc-chromium | VNC Chrome 浏览器（CDP远程调试） | 8月14日 |
| browser-vnc-xvnc | VNC 虚拟X服务器 | 8月14日 |
| browser-vnc-websockify | VNC WebSocket代理 | 8月14日 |
| browser-vnc-openbox | VNC 窗口管理器 | 8月14日 |
| browser-vnc-session | VNC D-Bus会话+输入法 | 8月14日 |
| caddy | 反向代理/HTTPS | 8月14日 |
| nginx | Web服务器/反向代理 | 8月14日 |
| supervisor | 进程管理（dashboards.conf） | 8月14日 |
| hermes-dashboard | Hermes Web Dashboard (loopback:9119) | 8月14日 |
| export-server | framework-tree 导出后端 (sandbox) | 9月01日 |
| ssh | SSH服务 | 8月14日 |
| cron | 定时任务守护 | 8月14日 |

### 1.2 Supervisor 管理的看板/应用（dashboards.conf）

| Program | 目录 | 端口 | 用途 | 启动日期 |
|---------|------|------|------|----------|
| lithium_calendar | /home/ubuntu/lithium_calendar | 8801 | 碳酸锂日历看板 | 8月14日 |
| macro_dashboard | /home/ubuntu/macro_dashboard | 8802 | 宏观看板(Flask) | 8月14日 |
| macro_gunicorn | /home/ubuntu/macro_dashboard | 8767 | 宏观看板(Gunicorn) | 8月16日 |
| overseas_lithium | /home/ubuntu/analysis/lithium_global | 8803 | 海外锂矿看板 | 8月16日 |
| lithium_inventory | /home/ubuntu/analysis | 8805 | 碳酸锂库存看板 | 8月21日 |
| nickel_dashboard | /home/ubuntu/nickel_dashboard | 8806 | 镍看板(Gunicorn) | 8月14日 |
| zinc_squeeze | /home/ubuntu/zinc_squeeze_analysis | 8770 | 锌挤兑分析 | 8月14日 |
| nav_server | （nav_server.py） | 8768 | 导航服务 | 8月14日 |
| commodity_dashboard | /home/ubuntu/commodity-dashboard | 8780 | 商品看板 | 8月15日 |
| zinc_gh_proxy | /home/ubuntu/zinc_dashboard_gh | 8775 | 锌GH Pages代理 | 8月17日 |
| nickel_gh_proxy | /home/ubuntu/nickel_dashboard_gh | 8774 | 镍GH Pages代理 | 8月16日 |
| report_app | （report_app.py） | 8773 | 报告服务 | 8月16日 |
| data_harbor | /home/ubuntu/data-harbor | 8765 | data-harbor API | 9月07日 |
| sensenova_proxy | sensenova_rate_limit_proxy | 8091 | 商汤限流代理 | 8月21日 |

### 1.3 其他活跃进程

| 进程 | PID | 用途 | 启动 |
|------|-----|------|------|
| hermes-agent gateway | 2491194 | Hermes消息网关(飞书/微信/QQ) | 9月10日 |
| pyright-langserver | 2501115 | LSP语言服务器 | 9月10日 |
| export-server (python) | 2965533 | framework-tree导出原型 | 9月01日 |

### 1.4 Crontab 定时任务（系统级）

| 调度 | 命令 | 用途 |
|------|------|------|
| 35 8 * * * | run_lme_base_email_import.sh | LME邮件每日导入 |
| @reboot | supervisord -c macro_dashboard/supervisor.conf | 开机启动看板 |
| @reboot | supervisord -c lithium_calendar/supervisor.conf | 开机启动日历 |
| */10 * * * * | lithium_supervisor.py --check | 海外锂矿巡检 |
| */5 * * * * | macro_dashboard/auto_restart.sh | 宏观看板自动重启 |
| 30 15 * * 1-5 | exp430_shadow_cron.sh | HAM影子交易cron |

### 1.5 Hermes Cron 任务（36个，22 ON / 14 OFF）

**活跃(no_agent=True)关键任务：**

| 名称 | 调度 | 脚本 |
|------|------|------|
| 碳酸锂每日数据更新 | 0 18 * * 1-5 | lc_daily_update.sh |
| 碳酸锂看板GH Pages推送 | 0 18 * * 1-5 | lithium_gh_update.sh |
| LME邮件数据导入 | 40 8 * * * | lme_email_importer.sh |
| 锌逻辑复盘页面更新 | 30 17 * * * | zinc_logic_review_update.sh |
| A1-LME库存日报 | 0 10 * * 1-5 | zinc_lme_inventory_monitor.py |
| A2-SHFE库存周报 | 0 18 * * 4 | zinc_shfe_inventory_monitor.py |
| B1-锌库存日报 | 0 18 * * * | zinc_inventory_daily_summary.py |
| B2-锌库存周报 | 0 18 * * 5 | zinc_inventory_weekly_report.py |
| 锌新闻日报 | 0 7 * * * | zinc_news_daily.py |
| 锌新闻周报 | 0 9 * * 1 | zinc_news_weekly_update.py |
| mysteel铅锌升贴水日报 | 30 12 * * 1-5 | mysteel_daily_sender.sh |
| 碳酸锂Agent每日更新 | 30 18 * * 1-5 | lithium_agents/agent_daily_update.sh |
| 广期所碳酸锂仓单+持仓 | 30 16 * * 1-5 | fetch_lc_data.sh |
| macro_dashboard_refresh | 0 8,14 * * * | macro_dashboard_refresh.py |
| macro_analysis | 30 8,14 * * * | macro_analysis.sh |
| macro-data-daily-update | 0 6 * * * | macro_data_daily_update.sh |
| macro-global-fetcher | 0 */6 * * * | macro_global_fetcher_wrapper.py |
| nickel-data-update | */30 * * * * | nickel_data_update.sh |
| zinc-data-update | */30 * * * * | zinc_data_update.sh |
| data_harbor_daily_backup | 30 23 * * * | harbor_backup_daily.sh |
| data-harbor健康巡检 | 0 11 * * 1-5 | harbor_watchdog_health.sh |
| watch-5m-jsonl | */10 * * * * | watch_db_export.sh |
| iwencai-classify-morning-report | 0 9 * * * | iwencai_classify_report.py |
| weekly-redundancy-cleanup | 0 2 * * 1 | weekly_maintenance.py |
| 三通道保活续接 | every 5m | weixin_keepalive.py |
| 会话自动续接 | every 10m | monitor_auto_resume.py |
| 夜间任务恢复 | every 5m | night_shift_recovery.py |
| Dashboard Health Check | 0 8 * * * | dashboard_health_check.py |

**已关闭(OFF)：** 百炼Token切换、晨间汇总、限流测试追踪、盯端口续接、session中断监控、dashboard-watchdog

### 1.6 项目活跃状态分类

| 分类 | 项目 |
|------|------|
| **持续在线运行** | macro_dashboard, lithium_calendar, data-harbor, overseas_lithium, lithium_inventory, nickel_dashboard, zinc_squeeze, commodity_dashboard, nickel_gh_proxy, zinc_gh_proxy, report_app, nav_server, sensenova_proxy, export-server, hermes-agent gateway |
| **暂停待完善** | lithium-engine (HAM系列exp436-research分支, 影子交易停摆), framework-tree-cu (铜品种task/cu_price分支), framework-tree-export (feature/export-module分支) |
| **已结题归档** | 碳酸锂日历项目目录(存档系统已上线), lead_cleaned_data, lead_supply_data |
| **废弃临时实验** | nickel_backup_20260816_163526, nickel_dashboard_gh_remote_backup_20260813, nickel_gh_static_backup_20260813, archive_duplicates_20260720, prompt_optimizer_demo, nickel_prompt_eval |

---

## 模块二：全服务器项目大类总表

| # | 项目名称 | 路径 | 状态 | 简述 | Git分支 | 最新Commit | Remote |
|---|---------|------|------|------|---------|-----------|--------|
| 1 | macro_dashboard | /home/ubuntu/macro_dashboard | 运行中 | 宏观经济看板(Flask+Gunicorn) | master | a3f38e3 | macro-dashboard.git |
| 2 | macro_gh_static | /home/ubuntu/macro_gh_static | 运行中 | 宏观看板静态GH Pages推送 | main | 8a1058c | macro-dashboard-gh.git |
| 3 | lithium_gh_static | /home/ubuntu/lithium_gh_static | 运行中 | 碳酸锂看板静态GH Pages推送 | main | 2d4434e | lithium-dashboard.git |
| 4 | zinc_dashboard_gh | /home/ubuntu/zinc_dashboard_gh | 运行中 | 锌看板GH Pages+代理 | main | 6274d8d | zinc-dashboard.git |
| 5 | nickel_dashboard_gh | /home/ubuntu/nickel_dashboard_gh | 运行中 | 镍看板GH Pages+代理 | main | 7400284 | nickel-dashboard.git |
| 6 | framework-tree | /home/ubuntu/framework-tree | 活跃开发 | 有色金属指标看板体系(80页) | main | c98c457 | framework-tree.git |
| 7 | framework-tree-cu | /home/ubuntu/framework-tree-cu | 暂停(worktree) | 铜品种看板开发分支 | task/cu_price | 4512520 | (worktree) |
| 8 | framework-tree-export | /home/ubuntu/framework-tree-export | 暂停(worktree) | 导出模块开发分支 | feature/export-module | a4a8bd0 | (worktree) |
| 9 | lithium-engine | /home/ubuntu/lithium-engine | 暂停 | 碳酸锂HAM策略引擎(exp436-research) | exp436-research | 1e5a21a | lithium-engine.git |
| 10 | data-harbor | /home/ubuntu/data-harbor | 运行中 | 自定义数据管理API(98指标/20376点) | master | 1d5bc0d | data-harbor.git |
| 11 | 碳酸锂日历项目 | /home/ubuntu/碳酸锂日历项目目录 | 已结题 | 碳酸锂基差月差日历(存档系统) | master | 4fd5277 | (无remote) |
| 12 | analysis | /home/ubuntu/analysis | 活跃 | 核心分析库(品种框架/临时资讯/数据) | (非git仓库) | — | — |
| 13 | lithium_calendar | /home/ubuntu/lithium_calendar | 运行中 | 碳酸锂日历Flask看板+持仓DB | (非git仓库) | — | — |
| 14 | lc_futures_data | /home/ubuntu/lc_futures_data | 运行中 | 碳酸锂期货数据(732行回填) | (非git仓库) | — | — |
| 15 | macro_dashboard (venv) | /home/ubuntu/macro_dashboard/venv | 运行中 | 宏观看板专用venv | — | — | — |
| 16 | nickel_dashboard | /home/ubuntu/nickel_dashboard | 运行中 | 镍看板(Gunicorn :8806) | (非git仓库) | — | — |
| 17 | zinc_squeeze_analysis | /home/ubuntu/zinc_squeeze_analysis | 运行中 | 锌挤兑分析看板 | (非git仓库) | — | — |
| 18 | commodity-dashboard | /home/ubuntu/commodity-dashboard | 运行中 | 商品综合看板(:8780) | (非git仓库) | — | — |
| 19 | futures-monitor | /home/ubuntu/futures-monitor | 暂停 | 期货实时监测系统(6大交易所90+合约) | (非git仓库) | — | — |
| 20 | minute_trading_monitor | /home/ubuntu/minute_trading_monitor | 暂停 | 分钟级行情监测 | (非git仓库) | — | — |
| 21 | inventory_dashboard | /home/ubuntu/inventory_dashboard | 暂停 | 库存看板 | (非git仓库) | — | — |
| 22 | nickel_analysis_framework | /home/ubuntu/nickel_analysis_framework | 暂停 | 镍分析框架 | (非git仓库) | — | — |
| 23 | zinc_assistant | /home/ubuntu/zinc_assistant | 暂停 | 锌助手 | (非git仓库) | — | — |
| 24 | zinc_data | /home/ubuntu/zinc_data | 暂停 | 锌数据目录 | (非git仓库) | — | — |
| 25 | lithium_stocks | /home/ubuntu/lithium_stocks | 暂停 | 锂库存数据 | (非git仓库) | — | — |
| 26 | lead_cleaned_data | /home/ubuntu/lead_cleaned_data | 已结题 | 铅清洗后数据(CSV) | (非git仓库) | — | — |
| 27 | lead_supply_data | /home/ubuntu/lead_supply_data | 已结题 | 铅供应数据 | (非git仓库) | — | — |
| 28 | 铅数据库模板 | /home/ubuntu/铅数据库模板 | 已结题 | 铅数据库模板 | (非git仓库) | — | — |
| 29 | output | /home/ubuntu/output | 归档 | 交接文档/任务卡/分析报告归档 | (非git仓库) | — | — |
| 30 | scripts | /home/ubuntu/scripts | 活跃 | 锌库存/新闻脚本集 | (非git仓库) | — | — |
| 31 | nickel_backup_20260816 | /home/ubuntu/nickel_backup_20260816_163526 | 废弃 | 镍看板完整备份(8月16日) | (含.git,旧版) | — | — |
| 32 | nickel_dashboard_gh_remote_backup | /home/ubuntu/nickel_dashboard_gh_remote_backup_20260813 | 废弃 | 镍看板远端备份(8月13日) | (非git仓库) | — | — |
| 33 | nickel_gh_static_backup | /home/ubuntu/nickel_gh_static_backup_20260813 | 废弃 | 镍静态站备份(8月13日) | (非git仓库) | — | — |
| 34 | archive_duplicates | /home/ubuntu/archive_duplicates_20260720 | 废弃 | 旧版看板HTML归档(7月20日) | (非git仓库) | — | — |
| 35 | prompt_optimizer_demo | /home/ubuntu/prompt_optimizer_demo | 废弃 | Prompt优化器演示 | (非git仓库) | — | — |
| 36 | nickel_prompt_eval | /home/ubuntu/nickel_prompt_eval | 废弃 | 镍Prompt评估 | (非git仓库) | — | — |
| 37 | awesun-cli | /home/ubuntu/awesun-cli | 废弃 | 远程控制工具 | (非git仓库) | — | — |
| 38 | unified_venv | /home/ubuntu/unified_venv | 运行中 | 统一Python虚拟环境(zinc_venv/.mysteel_venv符号链接至此) | — | — | — |
| 39 | export_proto_venv | /home/ubuntu/export_proto_venv | 运行中 | 导出原型venv | — | — | — |
| 40 | .venv_mysteel | /home/ubuntu/.venv_mysteel | 废弃 | 旧mysteel venv(41M,已被unified_venv替代) | — | — | — |

### 关键数据库文件

| 数据库 | 大小 | 路径 | 用途 |
|--------|------|------|------|
| lme_bloomberg_data.db | 68M | ~/lme_bloomberg_data.db | LME彭博数据(主) |
| 有色日度数据_optimized.db | 53M | ~/有色日度数据_optimized.db | 有色日度(优化版) |
| lme_base_data.db | 69M | ~/lme_base_data.db | LME基础数据 |
| 有色日度数据.db | 15M | ~/有色日度数据.db | 有色日度(原始) |
| zinc_v1.db | 18M | ~/zinc_v1.db | 锌数据库 |
| lead_v2.db | 14M | ~/lead_v2.db | 铅数据库 |
| lc_spot.db | — | ~/lc_futures_data/data/ | 碳酸锂现货(732行) |
| lithium.db | — | ~/lithium_calendar/ | 碳酸锂日历+持仓 |
| api_cache.db | — | ~/scripts/ | 知几API缓存 |
| nickel_v1.db | — | ~/nickel_v1.db | 镍数据库 |
| mysteel_delivery.db | — | ~/mysteel_delivery.db | Mysteel交割数据 |

---

## 模块三：冗余代码/文件清单（分级标注）

### 3.1 ✅ 安全冗余（可删除 — 临时缓存/日志/中间输出）

| 类型 | 路径/文件 | 大小 | 说明 |
|------|----------|------|------|
| DB备份(滚动) | ~/db_backups/ | 165M | 每日自动备份(有色日度+LME),保留2天滚动,可清旧 |
| LME邮件日志 | ~/logs/lme_base_email_import_*.log | 368K | 7月12日-至今每日导入日志 |
| __pycache__ | ~/__pycache__/ | 152K | 根目录Python缓存 |
| Hermes session dump | ~/.hermes/sessions/request_dump_*.json | ~20+文件 | 请求转储(可清旧) |
| cron_output | ~/cron_output/ | 472K | cron任务输出归档 |
| 交接文档(根目录) | ~/交接文档_*.md, ~/会话交接_*.md等 | ~200K | 多版本交接文档(v1-v5),保留最新 |
| 分析报告(根目录) | ~/2021-2026铅供需*.md, ~/2026H1_铅*.md等 | ~150K | 6月分析报告散落根目录 |
| 备份HTML | ~/今日备份_20260629.html, ~/完整备份_20260629.md | ~70K | 6月29日全量备份 |
| DB备份(铅) | ~/lead_v2_backup_20260627_202857.db | 6.9M | 铅数据库6月27日备份 |
| DB备份(锌) | ~/zinc_v1_backup_pre_import_20260705_155037.db | 18M | 锌数据库7月5日导入前备份 |
| DB备份(镍) | ~/nickel_backup_20260816_163526/ | 12M | 镍数据库8月16日备份(含旧git仓库) |
| ebike安全备份 | ~/backups_ebike_safe_20260828_2337.db | 159K | 8月28日安全备份 |
| backups目录 | ~/backups/framework-tree-t5*/t6*/ | 5.1M | framework-tree分支备份(8月28日) |
| .bak文件 | ~/lithium_dashboards.bak, ~/邮件增量更新_有色日度.py | — | 旧版备份 |
| 铅数据库模板 | ~/铅数据库模板/ | 32K | 已结题模板 |
| 有色日度数据_optimized.db.gz | — | 8.5M | 压缩版DB(已有未压缩版) |

### 3.2 ⚠️ 谨慎冗余（废弃实验源码 — 已推送到GitHub远端,可考虑本地清理）

| 类型 | 路径 | 大小 | 说明 | 远端状态 |
|------|------|------|------|----------|
| HAM实验目录 | ~/lithium-engine/model_ham/exp3_*~exp436_* | ~5M(共35个目录) | exp404~exp437系列,已推送到lithium-engine.git exp436-research分支 | ✅ 已推送 |
| 镍看板备份 | ~/nickel_backup_20260816_163526/nickel_dashboard_gh/ | 12M | 含完整.git仓库(旧commit 4387fb6) | ✅ 远端有更新版 |
| 镍远端备份 | ~/nickel_dashboard_gh_remote_backup_20260813_124928/ | 236K | 8月13日远端备份 | ✅ 已过期 |
| 镍静态备份 | ~/nickel_gh_static_backup_20260813_133217/ | 380K | 8月13日静态站备份 | ✅ 已过期 |
| 旧版HTML归档 | ~/archive_duplicates_20260720/ | 2.6M | 7月20日旧看板HTML | ✅ 已被新版替代 |
| 旧venv | ~/.venv_mysteel | 41M | 旧mysteel venv,已被unified_venv替代 | — |
| 临时tar.gz | ~/lc_futures_data/backup_*.tar.gz (11个) | ~50M | 7月30日碳酸锂数据多版本备份 | — |
| .bak文件(脚本) | ~/.hermes/scripts/*.bak_*, *.bak | — | 旧脚本备份 | — |
| .bak文件(日历) | ~/lithium_calendar/static/*.bak_*, app.py.bak_v5 | — | 日历旧版备份 | — |
| .bak文件(framework-tree) | ~/framework-tree*/data/indicators_v1.json.bak_* | — | 指标表多版本备份 | — |
| config.yaml备份 | ~/.hermes/config.yaml.bak* (20+个) | — | Hermes配置多版本备份 | — |

### 3.3 ❌ 禁止触碰（生产代码/活跃项目/影子盘）

| 路径 | 说明 | 理由 |
|------|------|------|
| /home/ubuntu/macro_dashboard/ | 宏观看板(生产) | 持续在线运行,Supervisor管理 |
| /home/ubuntu/lithium_calendar/ | 碳酸锂日历(生产) | 持续在线运行,Supervisor管理 |
| /home/ubuntu/data-harbor/ | data-harbor API(生产) | 持续在线运行,98指标/20376点 |
| /home/ubuntu/analysis/ | 核心分析库 | 品种框架/临时资讯/数据引擎 |
| /home/ubuntu/framework-tree/ | 有色金属看板体系(80页) | 活跃开发,80页已上线 |
| /home/ubuntu/lithium_gh_static/ | 碳酸锂GH Pages | 每日18:00 cron推送 |
| /home/ubuntu/zinc_dashboard_gh/ | 锌GH Pages | 每日cron推送 |
| /home/ubuntu/nickel_dashboard_gh/ | 镍GH Pages | 每30分钟cron推送 |
| /home/ubuntu/lc_futures_data/ | 碳酸锂期货数据 | 732行回填,活跃使用 |
| /home/ubuntu/.hermes/ | Hermes Agent核心 | 配置/skills/cron/scripts |
| /home/ubuntu/lithium-engine/ | HAM策略引擎(暂停) | exp436-research分支,虽暂停但保留 |
| /home/ubuntu/framework-tree-cu/ | 铜品种开发分支 | worktree,暂停但保留 |
| /home/ubuntu/framework-tree-export/ | 导出模块分支 | worktree,暂停但保留 |
| ~/lme_bloomberg_data.db, ~/lme_base_data.db | LME数据库(68M+69M) | 活跃使用,cron每日更新 |
| ~/有色日度数据.db, ~/有色日度数据_optimized.db | 有色日度DB | 活跃使用 |
| ~/zinc_v1.db, ~/lead_v2.db, ~/nickel_v1.db | 品种DB | 活跃使用 |
| ~/lithium_calendar/lithium.db, ~/lc_futures_data/data/lc_spot.db | 碳酸锂DB | 活跃使用 |

### 3.4 根目录散落py文件（55个）

根目录 `/home/ubuntu/` 下散落55个 `.py` 文件，大多为一次性脚本/调试工具：

**分类：**
- **LME/邮件相关**(8个): lme_email_importer.py, lme_base_importer.py, qq_email_lme_importer.py, import_lme_backup.py, reimport_lme_emails.py, build_dual_db_mapping.py, check_mapping.py, generate_lme_daily_report.py
- **有色日度相关**(6个): update_ysrsd_from_email.py, detect_data_gaps.py, verify_ysrsd.py, optimize_ysrsd_db.py, parse_ysrsd_sql.py, compare_email_ysrsd.py, inspect_rows.py, 邮件增量更新_有色日度.py
- **锌相关**(9个): zinc_calc.py, zinc_export_profit_calc.py, zinc_term_structure_prep.py, zinc_overseas_supply_tracker.py, zinc_logic_review_generator.py, zinc_logic_scorer_v2.py, zinc_logic_scorer_v3.py, zinc_shfe_position_tracker.py, zinc_news_impact.py, zinc_incremental_update.py, zinc_query.py, zinc_news_crawler.py, zinc_logic_engine.py, tmp_zinc_data.py, term_structure_cache.py
- **铅相关**(2个): lead_query.py, lead_supply_db.py
- **锂相关**(4个): lithium_analysis.py, lithium_db_investigation.py, lithium_db_investigation2.py, lithium_summary_json.py
- **Mysteel相关**(2个): mysteel_scraper.py, mysteel_daily_sender.py, mysteel_health_check.py
- **调试/检查**(8个): test_extract_ak.py, analyze_mismatches.py, investigate_mismatches.py, fix_macro_dashboard.py, check_dashboards.py, check_pre_feb_conflicts.py, quick_check.py, _verify_v3.py
- **其他**(5个): run_backtest.py, cleanup_empty_rows_cols.py, inject_prompt_data.py, email_fill_overwrite.py, compare_emails.py, run_email_fill.py

> 这些脚本大部分不再被主程序import调用，属于历史调试产物。但因涉及数据操作逻辑，归为⚠️谨慎级。

---

## 模块四：清理建议

### 推荐清理顺序

**第一批：纯缓存/日志（零风险，可直接清理）**
1. `~/__pycache__/` — 152K，Python自动生成
2. `~/logs/lme_base_email_import_*.log`（7月旧日志）— 保留近1月即可
3. `~/.hermes/sessions/request_dump_*.json`（旧session转储）— 保留近2周
4. `~/cron_output/`（旧cron输出）— 保留近1月
5. `~/有色日度数据_optimized.db.gz` — 8.5M，已有未压缩版

**第二批：旧备份DB（需确认无引用后清理）**
6. `~/lead_v2_backup_20260627_202857.db` — 6.9M，铅DB 6月备份
7. `~/zinc_v1_backup_pre_import_20260705_155037.db` — 18M，锌DB 7月备份
8. `~/db_backups/` 中超过7天的滚动备份 — 165M，cron每日生成
9. `~/backups_ebike_safe_20260828_2337.db` — 159K

**第三批：废弃备份目录（确认远端有更新版后清理）**
10. `~/nickel_backup_20260816_163526/` — 12M，含旧git仓库（远端有最新版）
11. `~/nickel_dashboard_gh_remote_backup_20260813_124928/` — 236K
12. `~/nickel_gh_static_backup_20260813_133217/` — 380K
13. `~/archive_duplicates_20260720/` — 2.6M，旧版HTML（已被新版替代）

**第四批：旧venv（确认无程序引用后清理）**
14. `~/.venv_mysteel/` — 41M，已被unified_venv替代（zinc_venv/.mysteel_venv均符号链接至unified_venv）

**第五批：lc_futures_data 旧备份（谨慎，确认有当前版本后清理）**
15. `~/lc_futures_data/backup_*.tar.gz`（11个文件，~50M）— 7月30日碳酸锂数据多版本备份

**第六批：HAM实验目录（确认远端有后，仅本地清理）**
16. `~/lithium-engine/model_ham/exp3_*` 到 `exp426_*`（保留exp428~exp436最新批次）— 已推送到lithium-engine.git exp436-research分支
17. ⚠️ 此项必须先执行 `git log --oneline exp436-research -- model_ham/exp4xx` 确认远端有完整提交

**第七批：根目录散落py脚本（需逐一确认无引用后归档/清理）**
17. ~/下的55个散落py文件 → 建议归档到 `~/scripts/legacy/` 或确认无引用后清理

### 绝对不能动的目录

| 目录 | 理由 |
|------|------|
| `~/.hermes/` | Hermes Agent核心（config/skills/cron/scripts/memory） |
| `~/macro_dashboard/` | 生产看板（Supervisor管理,含venv） |
| `~/lithium_calendar/` | 生产看板（Supervisor管理,含DB） |
| `~/data-harbor/` | 生产API（98指标/20376点） |
| `~/analysis/` | 核心分析库（品种框架/数据引擎/临时资讯） |
| `~/framework-tree/` | 活跃开发（80页看板体系） |
| `~/lithium_gh_static/` | GH Pages推送源 |
| `~/zinc_dashboard_gh/` | GH Pages推送源 |
| `~/nickel_dashboard_gh/` | GH Pages推送源 |
| `~/lithium-engine/` | HAM策略引擎（暂停但保留） |
| `~/framework-tree-cu/` | worktree（暂停但保留） |
| `~/framework-tree-export/` | worktree（暂停但保留） |
| `~/lc_futures_data/` | 碳酸锂期货数据（732行,活跃使用） |
| 所有 `.db` 文件（在上述目录内的） | 生产数据库 |

### 磁盘总览（深层扫描修正后）

> ⚠️ 重要修正：`macro_dashboard/venv/` 与 `unified_venv/` 的 site-packages **全部硬链接**（同 inode），`du` 报的 490M+490M 实际只占一份磁盘空间。`zinc_venv` 和 `.mysteel_venv` 是符号链接到 unified_venv。

| 类别 | 标称大小 | 实际占用 | 说明 |
|------|----------|----------|------|
| venv环境 | unified_venv 490M + macro_venv 490M + 其他 | ~537M | macro_venv与unified硬链接,不重复占盘; .venv_mysteel 41M可清理 |
| Hermes state.db | 724M | 724M | 625会话/58496消息/双FTS索引,是全服务器最大单文件 |
| 看板项目(含venv) | ~1.2G | ~710M | macro_dashboard非venv仅28M; zinc_gh 186M + nickel_gh 175M + framework-tree 216M |
| 数据库 | LME 137M + 有色日度 68M + db_backups 165M + 其他 | ~440M | db_backups每日滚动保留2天 |
| 分析库 | analysis 158M | 158M | 含db/97M + lithium_global/25M + output/5.3M |
| output目录 | 248M | 248M | agent_setup 138M(含DB副本) + agent_split 80M + zip 27M |
| Hermes日志 | 42M + sessions 64M | 106M | agent.log轮转5M×4 + gateway日志 + session dump |
| skills curator备份 | 20M + dev profile 27M | 47M | 自动备份,5份tar.gz |
| lc_futures_data备份 | 11个tar.gz | ~50M | 7月30日碳酸锂多版本备份 |
| 其他 | ~200M | ~200M | |
| **总计** | | ~2.5G(实际去重后~2.0G) | |

### 深层发现补充

#### state.db（724M）— 全服务器最大单文件
- 路径：`~/.hermes/state.db`
- 内容：625个会话 / 58496条消息 / 双FTS索引（messages_fts + messages_fts_trigram）
- FTS索引几乎等于消息正文大小（58496×4表 ≈ 23万行索引数据）
- ⚠️ 谨慎冗余：可考虑清理旧会话+VACUUM压缩（但属Hermes核心,归❌禁止触碰）

#### output/agent_setup（138M）— 跨服务器交接包
- 包含9个DB副本（lme_base_data.db 69M + lead_market.db 24M + zinc_v1.db 18M等）
- agent_setup_li_pz.zip 27M = 同内容压缩版
- ⚠️ 谨慎冗余：已完成交接,DB副本可清理(70M+)

#### macro_dashboard/logs（16M）
- error.log 12M（8月15日停止增长,看板已稳定）
- supervisord.log 3M
- ✅ 安全冗余：旧日志可清理

#### lithium_calendar/static 旧备份
- 5个 .bak_freq/.bak_v4/.bak_v5_20260730 HTML文件
- battlefield_agents_backup_20260730.html, index.html_backup_20260730.html
- 完整备份_20260629.md（在static目录中,位置不当）
- ✅ 安全冗余：旧版HTML备份

#### lithium_calendar 空DB文件
- lc_position.db (0字节), lithium_global.db (0字节), lithium_empty_backup.db (88K空库)
- ✅ 安全冗余：空/废弃DB

### 待补文档/任务

- lithium-engine: exp437结论归档完成，HAM降级为状态观测指标，项目边界已定稿。无待补
- framework-tree: 铜缺口5个(4.1/5.2/5.3/6.3/6.4)、铝缺口5个(3.1.2/3.1.4/6.1/6.4/7.3)、NI/SN/SI/LI建页待做
- data-harbor: P3证伪/哨兵修复完成，cron稳定
- macro_dashboard: UI已修复(scale:true + 响应式布局)，持续运行
