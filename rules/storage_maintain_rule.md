# 服务器存储维护规则

> 制定日期：2026-09-12  
> 依据：2026-09-11 盘点报告 + 2026-09-12 清理处置报告  
> 维护者：Hermes Agent (主脑)  

---

## 一、复盘小结（2026-09-12 清理操作）

### 执行概况

| 维度 | 数值 |
|------|------|
| 盘点日期 | 2026-09-11 |
| 清理执行日期 | 2026-09-12 |
| 删除项数 | 116项（6批） |
| 归档项数 | 6类（移动至 ~/archive/，未删除） |
| 释放空间 | ~1.2GB |
| 清理前磁盘 | 29G/40G (75%) |
| 清理后磁盘 | 28G/40G (74%) |

### 经验教训

1. **日志积累是主因**：35个LME邮件日志 + 130个session dump + 8个看板旧日志 = 占用超40M，无人清理会持续增长
2. **备份DB不设保留策略 = 定时炸弹**：db_backups/每日生成滚动备份，不清理2天后已达165M；旧版品种DB备份（铅6.9M + 锌18M）散落根目录无人回收
3. **config.yaml.bak 泛滥**：20+个历史备份文件，每次模型切换都生成一个，从未清理
4. **废弃实验目录遗忘**：3个镍看板备份目录 + 1个旧HTML归档 = 15M，远端已有最新版但本地未清理
5. **venv重复占用**：.venv_mysteel 41M 已被 unified_venv 替代但未及时删除
6. **归档优于删除**：废弃实验目录（prompt_optimizer_demo等）移动至 archive/ 而非直接删除，保留可回溯性

---

## 二、长期维护规则

### 规则1：日志保留策略（90天）

| 日志类型 | 路径 | 保留期 | 清理方式 |
|----------|------|--------|----------|
| LME邮件导入日志 | ~/logs/lme_base_email_import_*.log | 90天 | 超期自动删除 |
| Hermes agent日志 | ~/.hermes/logs/agent.log* | 90天 | 轮转5M×4，超期清理 |
| 看板日志 | ~/macro_dashboard/logs/*.log | 90天 | 超期自动删除 |
| Cron输出 | ~/cron_output/ | 90天 | 超期自动删除 |
| Session dump | ~/.hermes/sessions/request_dump_*.json | 14天 | 超期自动删除（体积大） |

**执行方式**：weekly_maintenance.py cron（每周一02:00）自动扫描并清理超期日志。

### 规则2：数据库备份保留策略（最近3份）

| 备份类型 | 路径 | 保留份数 | 说明 |
|----------|------|----------|------|
| 滚动DB备份 | ~/db_backups/ | 最近3份 | cron每日生成，保留最新3个文件 |
| 品种DB手动备份 | ~/[品种]_v*_backup_*.db | 最近1份 | 手动导入前生成，导入成功后删除 |
| Hermes config备份 | ~/.hermes/config.yaml.bak* | 最近3份 | 每次模型切换生成，保留最新3个 |
| Framework-tree指标表备份 | framework-tree/data/indicators_v1.json.bak_* | 最近3份 | 归档至 ~/archive/framework-tree_bak/ |

**执行方式**：
- db_backups：weekly_maintenance.py 自动清理超期
- 手动备份：操作完成后立即清理，不留散落文件
- config备份：monthly盘点时清理超量文件

### 规则3：月度定期盘点冗余备份

| 频率 | 执行时间 | 范围 | 产出 |
|------|----------|------|------|
| 每月1次 | 每月第1个周一 | 全服务器冗余扫描 | 盘点报告 + 清理处置报告 |

**盘点清单（必查项）**：

1. `~/` 根目录散落 .py / .md / .html / .db 文件（非项目目录内的）
2. `~/db_backups/` 备份文件数量（应≤3）
3. `~/.hermes/config.yaml.bak*` 备份数量（应≤3）
4. `~/.hermes/sessions/request_dump_*.json` 数量（应≤14天量）
5. `~/archive/` 归档目录是否有新增可清理项
6. 废弃实验目录（无远端remote + 无活跃引用）
7. venv重复（检查是否有被unified_venv替代但未删除的旧venv）
8. 各看板项目 logs/ 目录大小
9. `~/lc_futures_data/` 是否有新的 backup_*.tar.gz
10. `~/lithium_calendar/static/` 是否有 .bak 文件

**盘点分级**（与盘点报告一致）：

| 级别 | 符号 | 标准 | 处置 |
|------|------|------|------|
| 安全冗余 | 🔴 | 纯缓存/日志/中间输出，可自动删除 | 分批删除 |
| 谨慎冗余 | 🟡 | 有远端备份或已被替代 | 移至 ~/archive/，不直接删除 |
| 禁止触碰 | ❌ | 生产代码/活跃项目/无远端备份 | 不处理 |

---

## 三、禁止清理清单（永久保护）

以下目录/文件**任何情况下不得清理**：

| 路径 | 理由 |
|------|------|
| ~/unified_venv/ | 统一Python虚拟环境，zinc_venv/.mysteel_venv符号链接至此 |
| ~/.hermes/ | Hermes Agent核心（config/skills/cron/scripts/memory） |
| ~/macro_dashboard/ | 生产看板（Supervisor管理） |
| ~/lithium_calendar/ | 生产看板（Supervisor管理，含DB） |
| ~/data-harbor/ | 生产API（98指标/20376点） |
| ~/analysis/ | 核心分析库（品种框架/数据引擎/临时资讯） |
| ~/framework-tree/ | 活跃开发（80页看板体系） |
| ~/lithium_gh_static/ ~/zinc_dashboard_gh/ ~/nickel_dashboard_gh/ | GH Pages推送源 |
| ~/lithium-engine/ | HAM策略引擎（暂停但保留） |
| ~/framework-tree-cu/ ~/framework-tree-export/ | worktree（暂停但保留） |
| ~/lc_futures_data/ | 碳酸锂期货数据（活跃使用） |
| 所有 *.db 文件（在上述目录内的） | 生产数据库 |

---

## 四、待处理风险项

| 风险项 | 状态 | 建议 |
|--------|------|------|
| 碳酸锂日历项目目录无远端remote | ⚠️ 已标注 | 后续评估是否推送远端备份 |
| model配置残留噪音字符串 | ⚠️ 已告警 | 后续维护窗口期统一清理 |
| 模型降级兜底（阿里百炼端点） | ⏳ 延后 | 后续单独处理 |
| state.db 724M（全服务器最大单文件） | ⏳ 观测 | 超过1G时考虑VACUUM+旧会话清理 |

---

## 五、自动化维护脚本

| 脚本 | 调度 | 功能 |
|------|------|------|
| ~/.hermes/scripts/weekly_maintenance.py | 每周一 02:00 | 磁盘清理+DB备份保留+日志清理+hygiene报告 |
| ~/macro_dashboard/auto_restart.sh | 每5分钟 | 宏观看板自动重启 |
| ~/.hermes/scripts/weixin_keepalive.py | 每5分钟 | 三通道保活续接 |

**weekly_maintenance.py 需补充**：
- [ ] db_backups 保留策略从"2天"改为"最近3份"
- [ ] 新增根目录散落文件扫描（月度盘点清单第1项）
- [ ] 新增 config.yaml.bak 数量检查（应≤3）
