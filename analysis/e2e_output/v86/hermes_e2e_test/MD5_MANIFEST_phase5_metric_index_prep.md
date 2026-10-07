# MD5 校验清单 — V86-RC2 Phase5 指标适配与索引上线准备批次

> 生成时间: 2026-10-19 17:45
> 分支: `feature/v85-chart-template`（HEAD 含 DSHB `8b88ee8` + DSHE `2c23e13`）
> 工单: `HERMES_V86_RC2_HERMES_PHASE5_METRIC_ADAPT_AND_INDEX_PREP`
> 约束: BRANCH_LOCKED=TRUE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / **NO_ZHIJI_API_CALL=FALSE(0 次调用)**
> 状态标记: `HERMES_PHASE5_METRIC_INDEX_PREP_DONE=TRUE`

---

## 本轮新增/修改产物

| # | 文件 | 类型 | MD5 | 字节 | 行 | 核心内容 |
|---|------|------|-----|------|-----|----------|
| 1 | `phase4_gray_audit_wal_validator.py` | 更新 | `de4d2cbe9a25e754f7b20ad628b6e50f` | 58,002 | 1230 | 新增 DSHB 权威口径层（8 指标）+ caliber_v1_metrics 重写 + align_72h_window + 自检 12→18 项 |
| 2 | `phase5_index_baseline_validator.py` | 新增 | `574854559a3282da2f7527c5723ed9b1` | 9,033 | 214 | 索引沙箱基准验证器（250 万行分阶段 + 线性回归外推） |
| 3 | `phase5_index_deploy.py` | 新增 | `5c301792d7f6efd4d3bff8789db65244` | 15,700 | 387 | 复合索引上线脚本（check/create/verify/rollback/size 五模式） |
| 4 | `v86_rc2_hermes_phase5_metric_adapt_verify_report.md` | 新增 | `54420d1ea2fd80b4087617e9b54ed69f` | 16,338 | 309 | 指标适配对账报告（DSHB V1.0 对齐 + 环境差异归因 + 大样本复测 + 风险清单） |
| 5 | `v86_rc2_hermes_phase5_index_deploy_sop.md` | 新增 | `06816a3c77d4c41052eaf9046317409c` | 14,123 | 365 | 复合索引上线操作 SOP |
| 6 | `v86_rc2_hermes_prod_audit_trace_spec_update.md` | 更新 | `ebe5652690da39ca3587f7f672ffcd7e` | 15,555 | 410 | 追溯规范 v1.2→v1.3（§7 灰度场景 + §7.7 DSHB 统一口径） |
| 7 | `v86_rc2_hermes_gray_audit_ops_sop.md` | 更新 | `bdf79e98f5da35f9ed22c5e46d0f3421` | 15,515 | 459 | 运维 SOP v1.0→v1.1（§8 复合索引运维） |

## 本轮总计
- 新增: **4** 份（2 脚本 + 2 报告）
- 更新: **3** 份（1 验证器 + 2 文档规范）
- 合计: **7** 份, **144,266 字节**

## 关键验证结果

- 验证器自检: **18/18 PASS**（Phase4 为 12 项，新增 T13~T18 六项 DSHB 口径自检）
- 口径来源: **DSHB《G1 灰度三方指标口径规范 V1.0》**（`v86_rc2_dshb_g1_tripartite_metric_spec_v1.0.md`，1,289 行 / 44,162 字节，文档ID `DSHB-V86-RC2-G1-P5-METRIC-SPEC`，commit `8b88ee8`）
- **三方签收**: DSHB（`8b88ee8` 发布规范）+ **DSHE**（`2c23e13` 完成 16/16 指标适配、1,167,144 事件沙箱回放）+ HERMES（已实现）→ **三方全部签收**
- HERMES 原提案 METRIC-01~04 **已废弃**，按 DSHB 权威规范重写为 8 个指标标识
- 117 万基准样本新口径重算: 吞吐三层 648.437/648.437/648.413 ev/s · M-LOSS-RATE 0.0036%（分子42/分母1,167,144，≤0.01% normal）· M-P99-WAL-WRITE 1.485ms · M-P99-AUDIT-INGEST 5.93ms · M-TOTAL-72H 168,068,736 events（窗口对齐 UTC+8 08:00 8h 块）
- 三方对账: **统计逻辑差异 100% 消除**，COMPARABLE=6 / PARTIAL=1 / NOT_APPLICABLE=1；剩余偏差全部可归因数据环境差异（灰度 1800s vs 72h 全量）
- 告警抑制率 500 样本复测: **88.8%（95% CI [85.73, 91.27]）**，87% 基线统计成立，Phase4 PARTIAL→PASS
- 索引沙箱基准: 250 万行 **184 倍提速**（2288.355ms → 12.447ms）
- 500 万行外推: 无索引 4796.865ms（超时）/ 有索引 25.463ms
- 索引脚本: **5 模式全部实测通过**；check 模式 DB 不存在 exit 0（首次部署正常状态）
- 回滚实测: DROP 5 索引后 integrity=ok，行数 100,000 未变，完全恢复

## 风险清单变化

| ID | 名称 | Phase4 | Phase5 |
|----|------|--------|--------|
| B-01 | 检索线性扫描退化 | P1 | P1 → MITIGATED |
| B-02 | 索引空间膨胀 | P2 | **P1 ⬆️ 上调（76.26% 实测）** |
| B-03 | WAL 非线性增长 | P2 | P2（缓解，SOP §8.6） |
| B-04 | 告警样本不足 | P2 | **CLOSED** |
| B-05 | 跨团队指标口径差异 | P0 | **CLOSED** |
| B-06 | 丢失率阈值冲突 | P0 | **CLOSED** |
| B-07 | 延迟跨链路混比 | P1 | **CLOSED** |
| B-08 | 数据环境差异（新增） | — | P2 |
| B-09 | DSHE 签收 | — | **CLOSED**（DSHE `2c23e13`） |

**P0 由 2 项 → 0 项（全部关闭）**｜P1 由 2 项 → 1 项｜P2 由 3 项 → 2 项

## 状态标记

```
HERMES_PHASE5_METRIC_INDEX_PREP_DONE = TRUE
HERMES_PHASE5_CALIBER_DSHB_V1_ALIGNED = TRUE
HERMES_PHASE5_SELFTEST                = TRUE (18/18)
HERMES_PHASE5_ALERT_LARGE_SAMPLE      = TRUE
HERMES_PHASE5_INDEX_BENCH             = TRUE
HERMES_PHASE5_INDEX_SCRIPT_READY      = TRUE
HERMES_PHASE5_P0_CROSS_TEAM_CALIBER   = TRUE
HERMES_PHASE5_DSHB_SPEC_PUBLISHED     = TRUE
HERMES_PHASE5_DSHB_SIGNED             = TRUE
HERMES_PHASE5_DSHB_CONFIRM            = TRUE
HERMES_PHASE5_V85_ZERO_DRIFT          = TRUE
HERMES_PHASE5_ZHIJI_API_CALLED        = FALSE
JOB_READY                             = FALSE
GATE_DECISION                         = NOT_READY
DEP_001_STATUS                        = BLOCKED
```

## 性能数据 SHA256（可复现凭证）

```
phase5_run.json (seed=20261007)
sha256 = e12863dbd5145db77a616bba1bd3c0df5e6c53d29514f7d9c6a7d225f686b569
```

---

*本清单由 HERMES 生成于 Phase5 指标适配与索引上线准备批次完成后。*
