# V86-RC2 DEP-001 就绪后 E2E 全链路实测预案

> **工单**: 工单-HERMES / T3.3 DEP就绪后E2E全链路实测预案编制
> **分支**: `feature/v85-chart-template` @ commit `caa2410`
> **编制方**: HERMES（L3 审计方）
> **日期**: 2026-10-15
> **前置依赖**: `DEP-001`（zhiji 短ID 前缀解析能力）状态 `OPEN → RESOLVED`
> **工具链**: `evidence_auditor.py`（T3.2，11/11 用例回放通过）+ `dep_recovery_auto_verify.py`
> **约束**: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **文档状态**: READY — DEP-001 一恢复即可按本预案启动

---

## 0. 为什么需要这份预案

上两轮（`fa4974f` 流水线仿真 / 本轮 T3.1-T3.2）已完成**全部审计规则的仿真验证**，但**唯一未实测跑通的场景是正向完整链路**（CASE-A01），因为 DEP-001 仍 OPEN：短ID 直连 `?id=j25_tc` 返回 HTTP 500「无法识别指标来源」。

本轮实证（2026-10-15）确认阻塞形态稳定：

```
对照组 ID02226332 (长ID):  HTTP 200, 8 点, value=30700/20875/26950...  ← 环境健康
实验组 j25_tc  (短ID):      HTTP 500, ValueError: 无法识别指标来源(id前缀) @ commodity_api.py:443
       s_001 / ID_FAKE001:  HTTP 500 (同左)
       i1:                  permission_state=-4, 0 点
```

对照组的存在把归因锁定为**服务器侧解析能力缺失**（非凭据失效、非数据源故障）。因此 DEP-001 一旦就绪，链路具备可实测条件——本预案定义"如何一键启动、看什么、什么算过、失败怎么办"。

### 0.1 启动前置条件（三条件全绿才启动）

| # | 条件 | 验证方式 | 责任方 |
|---|------|---------|--------|
| P1 | DEP-001 状态 = `RESOLVED`（数据平台已上线短ID 解析） | 依赖登记表更新 + 数据平台书面确认 | 数据平台 |
| P2 | 短ID 探测集全部 HTTP 200 | `python3 dep_recovery_auto_verify.py` 输出全 PASS | HERMES |
| P3 | 对照组仍正常（排除环境整体故障） | `ID02226332` 返回 ≥1 非零点 | HERMES |

> **P2+P3 缺一不可**：只有 P2 无 P3 = 对照组也挂了（环境故障，非恢复）；只有 P3 无 P2 = 短ID 仍未就绪。

---

## 1. 三阶段测试结构

采用**冒烟 → 小规模抽样 → 全量**三阶段递进，任一阶段失败即停止并回滚，禁止跳阶段。

```
阶段1 冒烟测试 (Smoke)      ≤30 分钟    10 条核心指标    目的: 验证链路通路
  │  ↓ 全 PASS
阶段2 小规模抽样 (Sample)    ≤4 小时     60 条分层抽样    目的: 验证口径与审计规则
  │  ↓ evidence_auditor PASS
阶段3 全量验证 (Full)        ≤1 工作日    178 条全量      目的: 验证 Gate 准入
  │  ↓ G01~G10 全 PASS
      Gate READY 评估
```

### 1.1 阶段间门禁

| 门禁 | 判定 | 未过动作 |
|------|------|---------|
| S1→S2 | 冒烟 10 条全 HTTP 200 且 value≠0 | 停止，回滚至 DEP 未就绪态，通知数据平台 |
| S2→S3 | `evidence_auditor.py --file l2_package.json` 输出 `verdict=PASS` | 停止，退回 DSHE 重做独立调用 |
| S3→Gate | G01~G10 全 PASS 且有效桥接率 = 100% | 停止，Gate 维持 NOT_READY | [OLD_CALIBER - METADATA_ONLY, HERMES_INVALID]

---

## 2. 阶段1：冒烟测试（Smoke）

### 2.1 采样范围

| 层 | 指标数 | 选取 |
|----|-------|------|
| 核心品种 TC | 3 | `j25_tc`（铅精矿TC）+ 铜/锌精矿TC 短ID |
| 库存类 | 3 | i1-i3（社库/交易所库存） |
| 价格类 | 2 | 主力合约收盘价 |
| 对照组 | 2 | `ID02226332` + 另一已知可用长ID |

### 2.2 执行命令

```bash
cd analysis/e2e_output/v86/hermes_e2e_test
# 探测短ID 恢复状态
python3 dep_recovery_auto_verify.py
# 生成冒烟证据包 (DSHB L1 + DSHE L2 各一份)
python3 -c "..." # 见 §2.3
```

### 2.3 冒烟证据包最小结构（DSHE L2 契约）

```json
{
  "fingerprint": "DSHE-<run_id>-<session_id>",
  "run_id": "<YYYYMMDD_HHMMSS>",
  "session_id": "<uuid8>",
  "total_calls": 10,
  "caller": "DSHE_V86_RC2_L2_AUDIT",
  "dshb_reuse": false,
  "metadata_rate": 1.0,
  "real_fetchable_rate": "<实测值>",
  "control_check": {"http_status": 200, "has_nonzero_value": true},
  "script_audit": {
    "uses_search_passthrough": false,
    "has_id_consistency_assert": true,
    "zero_value_counts_as_pass": false,
    "retains_raw_payload": true
  },
  "calls": [ { "trace_id": "...", "indicator_id": "j25_tc",
               "request_payload": {"requested_id": "j25_tc", "independent": true},
               "response_payload": {"resolved_id": "j25_tc", "points": [...]},
               "status": "INDEPENDENT_FETCH_OK",
               "call_type": "DSHE_INDEPENDENT_ZHIJI" } ]
}
```

### 2.4 观测指标与判定阈值

| 指标 | 采集 | 通过阈值 |
|------|------|---------|
| 短ID HTTP 状态码 | 每个 trace | **10/10 = 200** |
| 非零数据点率 | value≠0 计数 | **10/10** |
| `requested_id == resolved_id` | 逐条断言 | **10/10 一致** |
| 对照组健康 | `ID02226332` | 200 且 ≥1 非零点 |
| 原始 payload 留存 | 请求URL+响应体 | **10/10 完整** |

---

## 3. 阶段2：小规模抽样（Sample）

### 3.1 采样策略（P0/P1/P2 分层，60 条）

| 层 | 条数 | 品种覆盖 | 说明 |
|----|------|---------|------|
| P0 核心 | 24 | PB/CU/ZN 精矿TC + 社库 + 主连收盘 | 直接影响 Gate G-06 |
| P1 结构 | 20 | 7 品种库存/供需平衡/进出口 | 月差、表观消费 |
| P2 长尾 | 16 | 成本/利润/开工率 | 低优先级但不豁免 |

**分层原则**：每品种 ≥4 条，避免单品种污染整体结论。

### 3.2 执行与校验

```bash
python3 evidence_auditor.py --file dshe_l2_sample_package.json --json \
  --persist audit_events_sample.json
```

### 3.3 观测指标与判定阈值

| 指标 | 通过阈值 |
|------|---------|
| `verdict` | **PASS**（CONDITIONAL_PASS 需人工裁决） |
| `gate_g06_real_fetchable_rate` | **= 1.0** |
| `gate_g09_script_audit` | **PASS** |
| `gate_g10_data_fetch` | **PASS** |
| CRITICAL 事件数 | **= 0** |
| 双桥接率一致性 | `metadata_rate == real_fetchable_rate == 1.0` |
| `dshb_reuse` | **= false**（L2 独立调用） |

### 3.4 审计规则触发监控

抽样阶段同时验证四条审计规则**不应误触发**：

| 规则 | 预期 | 若触发说明 |
|------|------|-----------|
| R-AUDIT-01 | 0 告警 | 双证据仍有缺口 |
| R-AUDIT-02 | 0 告警 | 口径未拆分或虚增 |
| R-AUDIT-03 | 0 告警 | L2 调用链不独立 |
| R-AUDIT-04 | 0 告警 | 脚本或取数校验有缺陷 |

---

## 4. 阶段3：全量验证（Full）

### 4.1 范围

178 条全量映射条目（`v86_rc2_dshb_bridge_snapshot_for_dshe.json` 清单），L1 自测 + L2 独立抽样双包提交。

### 4.2 Gate G01~G10 逐条准入

| Gate | 判定项 | 阈值 | 失败处置 |
|------|-------|------|---------|
| G-01 | L1 自测包完整 | 全部字段齐全 | 退回 DSHB |
| G-02 | L2 独立调用链 | `dshb_reuse=false` + trace 唯一 | 退回 DSHE |
| G-03 | 双证据齐全 | 178/178 双证据 | 退回 |
| G-04 | 元数据完成率 | = 100% | 退回 |
| G-05 | 桥接率口径拆分 | 双栏齐全 | CONDITIONAL |
| **G-06** | **真实可取数率** | **= 100%** | **NOT_READY** |
| G-07 | DEP 登记完整 | 10 字段齐全 | 阻断 |
| G-08 | Mock→Real 切换 | 无残留 Mock | NOT_READY |
| **G-09** | **脚本源码审计** | 无 search 中转 + 一致性断言 | **NOT_READY** |
| **G-10** | **真实取数抽样** | 对照组 + 目标全通过 | **NOT_READY** |

> **G-06/G-09/G-10 为强制项**：任一 FAIL 即 Gate NOT_READY，无豁免路径。

### 4.3 全量执行

```bash
python3 evidence_auditor.py --file dshe_l2_full_package.json --json \
  --persist audit_events_full.json
python3 evidence_auditor.py --run-case-library   # 回归用例库, 确保无退化
```

### 4.4 观测指标与判定阈值

| 指标 | 通过阈值 |
|------|---------|
| 有效桥接率（唯一口径） | **178/178 = 100%** |
| 审计 CRITICAL 事件 | **= 0** |
| 用例库回归 | **11/11 OK**（防校验器退化） |
| Gate G01~G10 | **10/10 PASS** |

---

## 5. 失败分级与处置

### 5.1 失败分级

| 级别 | 定义 | 处置 |
|------|------|------|
| **F1 链路级** | 短ID 仍 HTTP 500 / 对照组也失败 | 判定 DEP 未真正就绪或环境故障，**立即回滚**，DEP-001 重开 |
| **F2 审计级** | 链路通但审计 CRITICAL > 0 | 退回对应责任方（R-AUDIT-01→DSHB，R-AUDIT-03→DSHE），旧证据包作废 |
| **F3 Gate级** | 审计 PASS 但 G-06 未达阈值 | Gate NOT_READY，登记部分恢复（CASE-P01），等待补齐 |

### 5.2 处置责任矩阵

| 失败规则 | 触发检测点 | 退回对象 | 处置动作 |
|---------|-----------|---------|---------|
| R-AUDIT-01 | D01.2/D01.3 | **DSHB** | 删除旧脚本产出，重跑取数 |
| R-AUDIT-02 | D02.1/D02.3 | **DSHB** | 拆分双栏桥接率 |
| R-AUDIT-03 | D03.1/D03.2 | **DSHE** | 重做独立调用链 |
| R-AUDIT-04 | D04.1~D04.5 | **DSHB** | 修复脚本入参/payload 留存 |
| G-06 | 桥接率 < 100% | 按缺失条目归属 | 补齐取数 |
| DEP-CLASS | 声称 DEP 无证据 | **DSHB** | 降级为内部缺陷 P0 |

---

## 6. 回滚方案

### 6.1 回滚触发条件

1. 阶段1 冒烟短ID 仍 HTTP 500（DEP 假就绪）；
2. 任一阶段出现 CRITICAL 且 24 小时内无法定位；
3. 对照组突然失效（环境整体故障）；
4. 发现伪造证据（R-AUDIT-01 模式）——**强制回滚**，不尝试修复。

### 6.2 回滚步骤

```
Step 1  冻结当前证据包 (标记 retired=true, 归档至 audit_archive/ 并记 MD5)
Step 2  DEP-001 状态回退 RESOLVED → IN_PROGRESS (更新登记表 + 提交)
Step 3  恢复 JOB_READY.flag: GATE_REVIEW_PAUSED=TRUE, 注明回滚原因与轮次
Step 4  作废本轮全部证据包 (L2-R08: 退回即作废, 禁止复用)
Step 5  通知数据平台复核短ID 解析 (附对照组证据)
Step 6  记录回滚事件至审计事件持久化 (level=CRITICAL, rule=ROLLBACK)
```

### 6.3 回滚后不可做的事

- ❌ 不得复用本轮任何证据包（L2-R08 作废铁律）；
- ❌ 不得以"DEP 已就绪"名义跳过冒烟阶段；
- ❌ 不得在 DEP-001 状态为 OPEN 时提交 COMPLETED 结论。

---

## 7. 一键启动脚本

```bash
#!/bin/bash
# dep_ready_launch.sh — DEP-001 就绪后一键启动全链路实测
set -e
cd analysis/e2e_output/v86/hermes_e2e_test

echo "=== [0/4] 前置条件检查 ==="
python3 dep_recovery_auto_verify.py || { echo "P2 未满足: 短ID 未恢复"; exit 1; }
python3 evidence_auditor.py --check-md5 evidence_auditor.py \
  --expect c173c0e964e864c35ec2c44350c236cd || { echo "校验器被篡改"; exit 1; }

echo "=== [1/4] 阶段1 冒烟 ==="
python3 evidence_auditor.py --file dshe_l2_smoke_package.json --json > smoke_result.json
python3 -c "import json;d=json.load(open('smoke_result.json'));exit(0 if d['verdict']=='PASS' else 1)" \
  || { echo "F1/F2: 冒烟失败, 回滚"; exit 2; }

echo "=== [2/4] 阶段2 抽样 ==="
python3 evidence_auditor.py --file dshe_l2_sample_package.json --json \
  --persist audit_events_sample.json > sample_result.json
python3 -c "import json;d=json.load(open('sample_result.json'));exit(0 if d['verdict']=='PASS' else 1)" \
  || { echo "F2: 抽样审计失败"; exit 3; }

echo "=== [3/4] 阶段3 全量 + 用例库回归 ==="
python3 evidence_auditor.py --file dshe_l2_full_package.json --json \
  --persist audit_events_full.json > full_result.json
python3 evidence_auditor.py --run-case-library || { echo "用例库退化"; exit 4; }

echo "=== [4/4] Gate 结论 ==="
python3 -c "
import json;d=json.load(open('full_result.json'))
print('Gate:',d['gate_result'],'| 桥接率:',d['gate_g06_real_fetchable_rate'])
print('G09:',d['gate_g09_script_audit'],'| G10:',d['gate_g10_data_fetch'])"
```

---

## 8. 预案完整性自证

| 要素 | 状态 |
|------|------|
| 启动前置条件 | 3 条（DEP RESOLVED + 短ID 全通 + 对照组健康） |
| 测试阶段 | 3 阶段（冒烟 10 条 → 抽样 60 条 → 全量 178 条） |
| 阶段间门禁 | 3 道，未过即停 |
| 观测指标 | 阶段1: 5 项 / 阶段2: 7 项 / 阶段3: 4 项 |
| 判定阈值 | 全部量化（含硬性 100% 桥接率） |
| 失败分级 | 3 级（链路/审计/Gate） |
| 处置责任矩阵 | 6 类规则 → 责任方映射 |
| 回滚方案 | 触发条件 4 条 + 步骤 6 步 + 禁止事项 3 条 |
| 一键启动 | `dep_ready_launch.sh`（含校验器 MD5 防篡改） |
| 可回放性 | `evidence_auditor.py --run-case-library` 11/11 回归 |

**状态标记**：`HERMES_DEP_READY_E2E_PLAN_READY=TRUE`（DEP-001 恢复后可直接启动）
