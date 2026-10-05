# V86-RC2 准入清单V4 自动化预核验扫描报告

> 扫描时间: 2026-10-05 16:15:45
> 扫描器: `prod_checklist_v4_scanner.py`
> 分支: `feature/v85-chart-template` @ `629ccb7`

## 扫描汇总

| 级别 | PASS | FAIL/ERROR | UNKNOWN | 总数 |
|------|------|------------|---------|------|
| P0 | 61 | 5 | 0 | 66 |
| P1 | 0 | 0 | - | 0 |
| P2 | 0 | - | - | 0 |

**Gate判定: NOT_READY**

## P0阻断项明细

| ID | 名称 | 类别 | 状态 | 详情 |
|----|------|------|------|------|
| G01 | 交付物完整性检查 | A | ✅ PASS | 文件数=184 >= 20 |
| G02 | 约束合规性检查 | A | ✅ PASS | 约束标记FOUND: NO_MODIFY_V85/NO_OVERWRITE/BRANCH_LOCKED |
| G03 | 文档口径一致性检查 | A | ✅ PASS | V4报告含OLD_CALIBER标注 |
| G04 | API调用日志完整性 | A | ❌ FAIL | 文件数=0 < 5 |
| G05 | 桥接表数据准确性 | A | ❌ FAIL | 真实取数率0% (DEP未就绪) |
| G06 | 风险台账完整性 | A | ✅ PASS | 五类台账文件存在 |
| G08 | 审计链路可追溯性 | A | ✅ PASS | 存在: MD5_CHECKSUM_LIST_prod_case_a01_real_run.md |
| G09 | 脚本审计 | A | ✅ PASS | 复测脚本已优化, 无搜索关键词违规 |
| G10 | DS-06 事件存储切换 | A | ✅ PASS | 存在: event_store_wal_v2.py |
| B01 | 证据包契约版本 | B | ✅ PASS | 存在: v86_rc2_hermes_case_a01_real_run_report.md |
| B02 | 审计事件完整性 | B | ✅ PASS | CASE-A01: 15/15事件写入 |
| B03 | WAL存储模式 | B | ✅ PASS | journal_mode=wal (实测) |
| B04 | 事件去重原子性 | B | ✅ PASS | INSERT OR IGNORE 去重生效 |
| B05 | 崩溃恢复完整性 | B | ✅ PASS | WAL压测: 0数据丢失 |
| B06 | 桥接率阈值 | B | ❌ FAIL | 真实取数率0% < 80% (DEP未就绪) |
| B09 | 分片边界完整性(N2) | B | ✅ PASS | DSHE L2分片修复已提交 |
| C01 | 审计耗时 | C | ✅ PASS | self-test exit 0 |
| C02 | 事件写入延迟 | C | ✅ PASS | 写入4.2ms/千条, JM=wal |
| C03 | WAL自动切换 | C | ✅ PASS | WAL压测: checkpoint后WAL=0 |
| D01 | 审计规则完整性 | D | ✅ PASS | 存在: evidence_auditor_v3.py |
| D02 | 审计器容错守卫 | D | ✅ PASS | run_robustness 4类损坏覆盖 |
| D03 | 短路逻辑 | D | ✅ PASS | P1批CRITICAL短路验证PASS |
| D04 | 审计指纹追踪 | D | ✅ PASS | fingerprint/MD5清单存在 |
| D05 | 证据MD5校验 | D | ✅ PASS | 存在: MD5_CHECKSUM_LIST_prod_case_a01_real_run.md |
| D06 | 事件级审计 | D | ✅ PASS | 15事件含rule/DP/team字段 |
| D08 | 审计日志防篡改 | D | ✅ PASS | WAL只读校验 |
| E01 | 灰度门禁脚本 | E | ✅ PASS | gray_gate_decider 12/12 自检PASS |
| E02 | G0影子放行条件 | E | ✅ PASS | gray_gate_decider T01/T02 PASS |
| E03 | G1单品种准入 | E | ✅ PASS | T03 ADVANCE PASS |
| E04 | G2小范围准入 | E | ✅ PASS | 阈值: 非零率98%/p95 20ms |
| E05 | G3中范围准入 | E | ✅ PASS | 阈值: 非零率99%/p95 15ms |
| E08 | 观测期校验 | E | ✅ PASS | T10 OBSERVE PASS |
| F01 | F1链路级自动回滚 | F | ✅ PASS | S02 F1 0秒自动 ROLLBACK PASS |
| F02 | F1回滚超时0秒 | F | ✅ PASS | ROLLBACK_MATRIX F1 timeout=0秒 |
| F03 | F2审计级自动回滚 | F | ✅ PASS | S06 F2 30分钟确认 ROLLBACK PASS |
| F04 | F2回滚确认机制 | F | ✅ PASS | need_confirm=True 对齐 |
| F05 | F3 Gate级回滚 | F | ✅ PASS | S09 F3 8小时确认 ROLLBACK PASS |
| F06 | F4性能级回滚 | F | ✅ PASS | S05 F4 2小时确认 ROLLBACK PASS |
| F07 | F5稳定性级回滚 | F | ✅ PASS | S03 F5 1小时确认 ROLLBACK PASS |
| F08 | 回滚矩阵完整性 | F | ✅ PASS | F1~F5 5类全部定义 |
| G01 | DSHB规则引擎联动 | G | ✅ PASS | 存在: gate_pre_check_auto_v5.py |
| G02 | DSHE L2面板联动 | G | ✅ PASS | L2面板真实DEP数据源已接入 |
| G03 | 运维B联动 | G | ✅ PASS | V4三方评审闭环 18/18 |
| G04 | 跨团队台账一致 | G | ✅ PASS | 风险台账五类一致 |
| H01 | 面板可用性 | H | ✅ PASS | 端口124.221.113.37:8766 连通 |
| H02 | 告警端到端延迟 | H | ✅ PASS | E团队标定: ≤30s |
| H03 | 面板5xx率 | H | ✅ PASS | 实测0%, 阈值1% |
| H04 | CRITICAL告警监控 | H | ✅ PASS | F2判定接入CRITICAL>0 |
| I01 | 面板端口连通 | I | ✅ PASS | 端口124.221.113.37:8766 连通 |
| I02 | 知几API连通 | I | ✅ PASS | zhiji_api.py 本地调用 |
| I03 | GitHub远端连通 | I | ✅ PASS | 端口github.com:443 连通 |
| I04 | 数据库连通 | I | ✅ PASS | SQLite本地库正常 |
| I05 | DEP-001就绪N1a | I | ❌ FAIL | j25_tc HTTP 500 (DEP-001 BLOCKED) |
| J01 | git写入权限 | J | ✅ PASS | feature分支push成功 |
| J02 | ssh密钥 | J | ✅ PASS | 存在: id_ed25519_github |
| J03 | 知几API密钥 | J | ✅ PASS | 存在: zhiji_api.py |
| J04 | 文件写权限 | J | ✅ PASS | BASE目录写权限 |
| K01 | 审计日志落盘 | K | ❌ FAIL | 文件数=0 < 5 |
| K02 | WAL日志落盘 | K | ✅ PASS | WAL文件可写/可恢复 |
| L01 | 磁盘余量≥1GB | L | ✅ PASS | 磁盘余量=9.9GB >= 1.0GB |
| L02 | DB容量 | L | ✅ PASS | WAL压测35K事件 8MB |
| L03 | WAL文件增长 | L | ✅ PASS | checkpoint后WAL=0 |
| L04 | 备份存储 | L | ✅ PASS | 每日备份03:00 |
| M01 | 每日备份 | M | ✅ PASS | 03:00 cron备份 |
| M02 | 备份完整性 | M | ✅ PASS | 备份后MD5校验 |
| M03 | 恢复验证 | M | ✅ PASS | 崩溃恢复0丢失 |

## FAIL/UNKNOWN 阻塞项

- **G04** [P0/A] API调用日志完整性: 文件数=0 < 5
- **G05** [P0/A] 桥接表数据准确性: 真实取数率0% (DEP未就绪)
- **B06** [P0/B] 桥接率阈值: 真实取数率0% < 80% (DEP未就绪)
- **I05** [P0/I] DEP-001就绪N1a: j25_tc HTTP 500 (DEP-001 BLOCKED)
- **K01** [P0/K] 审计日志落盘: 文件数=0 < 5
