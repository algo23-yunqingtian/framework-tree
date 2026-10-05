# V86-RC2 CASE-A01 正向 E2E 真实环境用例规范（T3.1）

> **工单**: 工单-HERMES / T3.1 CASE-A01 正向 E2E 真实环境用例设计
> **分支**: `feature/v85-chart-template` @ `1b3c6f2`
> **编制方**: HERMES (L3 审计方)
> **日期**: 2026-10-15
> **状态**: 📋 **用例设计完成 — 待 DEP-001 就绪后执行**
>
> **约束**: NO_ZHIJI_API_CALL=FALSE（仅设计，不执行实测）/ NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE

---

## 0. CASE-A01 定义

CASE-A01 是 V86-RC2 投产验收的**唯一正向全链路 E2E 用例**。它验证从证据包提交到告警面板展示的完整数据流，确认所有组件在真实环境下协同工作。

**全链路**: L1 证据包 → Gate 准入 → HERMES 审计 → 事件存储 → DSHE 告警面板

### 0.1 当前状态

- DEP-001 短ID 解析服务: **BLOCKED**（服务器侧问题）
- 本用例已完成设计，**待 DEP-001 RECOVERED 后执行**
- dryrun 仿真已通过（上一轮 `gray_stair_sim.py` G0~G5 全阶梯 PASS）

---

## 1. 全链路数据流定义

```
┌─────────────┐     ┌──────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ DSHB/DSHE   │     │ Gate     │     │ HERMES      │     │ Event Store  │     │ DSHE 告警   │
│ 证据包提交  │────▶│ 准入检查 │────▶│ v3 审计     │────▶│ SQLite WAL   │────▶│ 面板渲染   │
│ (L1 payload)│     │ G01~G10  │     │ 短路+增量   │     │ audit_events │     │ (端口 8766) │
└─────────────┘     └──────────┘     └─────────────┘     └──────────────┘     └─────────────┘
     │                  │                  │                    │                    │
  Step 1              Step 2             Step 3              Step 4              Step 5
     │                  │                  │                    │                    │
  观测点 O1~O3        观测点 O4~O6        观测点 O7~O10        观测点 O11~O13      观测点 O14~O16
```

### 1.1 链路组件清单

| # | 组件 | 版本 | 部署位置 | 端口 | 依赖 |
|---|------|------|----------|------|------|
| C1 | DSHB 规则引擎 | V86-RC2 | 数据平台 | — | DEP-001 短ID 服务 |
| C2 | DSHE 别名引擎 | V86-RC2 | 数据平台 | — | C1 桥接映射 |
| C3 | Gate 准入检查 | v4 (gate_pre_check_auto_v4.py) | HERMES | — | C1/C2 证据包 |
| C4 | HERMES 审计器 | v3 (evidence_auditor_v3.py) | HERMES | — | C3 准入通过 |
| C5 | 事件存储 | v2 (event_store_wal_v2.py) | HERMES | — | C4 审计事件 |
| C6 | 告警面板 | V86-RC2 | 124.221.113.37:8766 | 8766 | C5 事件查询 |

---

## 2. 执行前置条件

### 2.1 硬性前置（缺一不可）

| # | 条件 | 验证方式 | 当前状态 |
|---|------|----------|----------|
| P1 | DEP-001 短ID 解析服务 RECOVERED | `curl zhiji 短ID 测试` → HTTP 200 + 非空数据 | 🔴 BLOCKED |
| P2 | DSHB 证据包生成器就绪 | DSHB 能产出含真实 API payload 的证据包 | 🔴 待确认 |
| P3 | DSHE 别名映射表已加载 | 桥接表有效映射率 ≥ 80% | 🟡 需验证 |
| P4 | HERMES 审计器 v3 部署完成 | `evidence_auditor_v3.py --self-test` → PASS | 🟢 已就绪 |
| P5 | 事件存储 WAL 模式生效 | `PRAGMA journal_mode` → `wal` | 🟢 已就绪 |
| P6 | 告警面板服务运行中 | `curl :8766/nickel-gh/` → HTTP 200 | 🟢 已就绪 |
| P7 | 网络连通性: HERMES → 数据平台 | `ping` + 端口扫描 | 🟢 已验证 |
| P8 | 三方证书/权限已配置 | Gate 检查 `G-01 权限验证` | 🟡 需确认 |

### 2.2 环境准备步骤

```bash
# 1. 确认 DEP-001 状态
python3 ~/.hermes/scripts/zhiji_api.py search "铅精矿 加工费 TC"
# 期望: HTTP 200, score>=12, data 非空

# 2. 确认审计器就绪
cd analysis/e2e_output/v86/hermes_e2e_test
python3 evidence_auditor_v3.py --self-test
# 期望: 54/54 PASS, exit 0

# 3. 确认事件存储就绪
python3 event_store_wal_v2.py --self-test
# 期望: 9/9 PASS, exit 0

# 4. 确认面板服务
curl -s -o /dev/null -w "%{http_code}" http://124.221.113.37:8766/nickel-gh/
# 期望: 200
```

---

## 3. 执行步骤（Step-by-Step）

### Step 1: DSHB/DSHE 证据包生成（L1 提交）

```bash
# DSHB 生成标准证据包 (256 call 基准包)
python3 dshb_gate_prod_fix/l1_evidence_pre_check_v2.py \
  --mode prod \
  --output /tmp/case_a01_evidence.json \
  --call-count 256 \
  --include-real-payload

# 验证产出
python3 -c "
import json
pkg = json.load(open('/tmp/case_a01_evidence.json'))
print('contract_version:', pkg.get('contract_version'))
print('calls:', len(pkg.get('calls', [])))
print('fingerprint:', pkg.get('fingerprint', '')[:32])
print('real_fetchable_rate:', pkg.get('real_fetchable_rate'))
"
```

**断言 A1**: 证据包契约完整（`contract_version=EVIDENCE_CONTRACT_V1`，`calls` 为非空 list）
**断言 A2**: 真实可取数率 ≥ 80%（DEP-001 就绪后预期 100%）
**断言 A3**: fingerprint 非空（8 字段 MD5 指纹）

### Step 2: Gate 准入检查（G01~G10）

```bash
python3 dshb_gate_prod_fix/gate_pre_check_auto_v4.py \
  --evidence /tmp/case_a01_evidence.json \
  --mode full \
  --output /tmp/case_a01_gate_result.json
```

**断言 A4**: G01~G08 全部 PASS
**断言 A5**: G09（脚本审计）PASS — 入参真实性核验通过
**断言 A6**: G10（真实取数校验）PASS — 短ID 实测返回非空数据
**断言 A7**: 整体判定 = `READY`（非 `CONDITIONAL` / `NOT_READY`）

### Step 3: HERMES 审计器 v3 审计

```bash
python3 evidence_auditor_v3.py \
  --evidence /tmp/case_a01_evidence.json \
  --mode full \
  --output /tmp/case_a01_audit_result.json \
  --store /tmp/case_a01_events.db
```

**断言 A8**: verdict = `PASS`（非 `CONDITIONAL_PASS` / `FAIL`）
**断言 A9**: 无 CRITICAL 级事件
**断言 A10**: 短路批次 = 0（正向链路不应触发短路）
**断言 A11**: 审计耗时 ≤ 15ms（256 call 基准，参考 v3 实测 7.168ms）

### Step 4: 事件存储写入与查询

```bash
python3 -c "
from event_store_wal_v2 import WALStore
import json

store = WALStore('/tmp/case_a01_events.db')
events = json.load(open('/tmp/case_a01_audit_result.json'))['events']
store.append_events(events)

# 验证写入
stats = store.stats()
print('total_events:', stats['total_events'])
print('by_level:', stats['by_level'])
print('journal_mode:', store.connection.execute('PRAGMA journal_mode').fetchone()[0])
"
```

**断言 A12**: 事件全部写入成功（`total_events` = 审计产出的事件数）
**断言 A13**: 存储模式 = `wal`
**断言 A14**: 去重生效（无重复 event_id）

### Step 5: 告警面板渲染验证

```bash
# 验证面板 API
curl -s http://124.221.113.37:8766/nickel-gh/api/events \
  -H "Content-Type: application/json" \
  -d '{"query": "case_a01", "limit": 10}' | python3 -m json.tool

# 验证面板页面加载
curl -s -o /dev/null -w "%{http_code}" \
  http://124.221.113.37:8766/nickel-gh/
```

**断言 A15**: 面板 API 返回 CASE-A01 相关事件
**断言 A16**: 面板 HTTP 200，页面正常渲染
**断言 A17**: 告警端到端延迟 ≤ 30s（Step 1 到 Step 5 的时间差）

---

## 4. 指标观测点定义

### 4.1 观测点清单

| # | 观测点 | 所属步骤 | 指标 | 采集方式 | 存储位置 |
|---|--------|----------|------|----------|----------|
| O1 | 证据包生成耗时 | Step 1 | ms | `time` 命令 | 执行日志 |
| O2 | 证据包大小 | Step 1 | KB | `stat -c%s` | 执行日志 |
| O3 | 真实可取数率 | Step 1 | % | JSON 字段 | 证据包 |
| O4 | Gate 检查耗时 | Step 2 | ms | `time` 命令 | 执行日志 |
| O5 | Gate 判定结果 | Step 2 | READY/NOT_READY | JSON 字段 | Gate 结果 |
| O6 | G09/G10 状态 | Step 2 | PASS/FAIL | JSON 字段 | Gate 结果 |
| O7 | 审计器耗时 | Step 3 | ms | `time` 命令 | 执行日志 |
| O8 | 审计 verdict | Step 3 | PASS/FAIL | JSON 字段 | 审计结果 |
| O9 | 短路触发数 | Step 3 | count | JSON 字段 | 审计结果 |
| O10 | 审计事件数 | Step 3 | count | JSON 字段 | 审计结果 |
| O11 | WAL 写入耗时 | Step 4 | ms | `time` 命令 | 执行日志 |
| O12 | WAL 模式状态 | Step 4 | wal/other | PRAGMA | SQLite |
| O13 | 事件去重数 | Step 4 | count | stats API | SQLite |
| O14 | 面板 API 延迟 | Step 5 | ms | `time` 命令 | 执行日志 |
| O15 | 面板事件命中 | Step 5 | count | API 返回 | 执行日志 |
| O16 | 端到端总延迟 | 全链路 | s | Step1→Step5 | 执行日志 |

### 4.2 指标基线（预期值）

基于上一轮仿真实测数据，制定真实环境预期基线：

| 指标 | 仿真基线 | 真实环境预期 | 容差 | 来源 |
|------|----------|-------------|------|------|
| 审计器耗时（256call） | 7.168 ms | ≤ 15 ms | ≤ 2x | v3 perf bench |
| 事件写入延迟（单批） | ~915 ms/千条 | ≤ 1000 ms | ≤ 1.1x | WAL v2 bench |
| Gate 检查耗时 | — | ≤ 5 s | — | 首次执行 |
| 面板 API 延迟 | — | ≤ 200 ms | — | 面板服务 |
| 端到端总延迟 | — | ≤ 30 s | — | 全链路 |
| 数据非零率 | 100% (DEP就绪) | ≥ 95% | ≤ 5% | 灰度 G1 阈值 |
| 审计 verdict | PASS | PASS | 0 | 正向链路 |
| CRITICAL 事件数 | 0 | 0 | 0 | 正向链路 |

---

## 5. 数据样本

### 5.1 正向证据包样本结构

```json
{
  "contract_version": "EVIDENCE_CONTRACT_V1",
  "fingerprint": "<8-field-md5>",
  "run_id": "CASE-A01-20261015-001",
  "source_team": "DSHB",
  "calls": [
    {
      "call_type": "series",
      "indicator_id": "ID02226332",
      "short_id": "j25_tc",
      "date_range": ["2026-08-01", "2026-08-31"],
      "status": 200,
      "data_points": 20,
      "real_fetchable": true
    }
  ],
  "real_fetchable_rate": 1.0,
  "metadata_mapping_complete": true,
  "dep_registry": [
    {"dep_id": "DEP-001", "status": "RECOVERED", "affected_indicators": ["j25_tc"]}
  ],
  "timestamps": {
    "created_at": "2026-10-15T10:00:00Z",
    "submitted_at": "2026-10-15T10:00:01Z"
  }
}
```

### 5.2 对照组样本

| 短ID | 长ID | 预期状态 | 用途 |
|------|------|----------|------|
| `j25_tc` | `ID02226332` | 200 / 20 points | 主链路验证 |
| `a10018143` | `ID02226332` | 200 / 20 points | 对照组（历史已验证可用） |
| `i1` | — | 200 / 非空 | DEP-001 就绪性验证 |

---

## 6. 执行后清理与回滚

### 6.1 正常清理（Step 5 全 PASS）

```bash
# 1. 清理临时文件
rm -f /tmp/case_a01_evidence.json \
      /tmp/case_a01_gate_result.json \
      /tmp/case_a01_audit_result.json \
      /tmp/case_a01_events.db

# 2. 标记执行完成
echo "CASE_A01_REAL_ENV_EXECUTED=TRUE" >> /tmp/case_a01_status.txt
echo "EXECUTION_TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /tmp/case_a01_status.txt
echo "RESULT=PASS" >> /tmp/case_a01_status.txt
```

### 6.2 异常回滚（任一步骤 FAIL）

| 失败步骤 | 回滚动作 | 回滚范围 | 人工确认 |
|----------|----------|----------|----------|
| Step 1 (证据包) | 无（尚未写入任何持久状态） | — | 否 |
| Step 2 (Gate) | 无（Gate 为只读检查） | — | 否 |
| Step 3 (审计) | 标记事件包为 `retired`，从面板移除 | 当前批次 | 否 |
| Step 4 (存储) | 删除本次写入的事件，执行 WAL checkpoint | 当前批次 | 否 |
| Step 5 (面板) | 无需回滚（面板为只读渲染） | — | 否 |

**回滚命令**:
```bash
# 存储层回滚: 删除本次执行的事件
python3 -c "
from event_store_wal_v2 import WALStore
store = WALStore('/tmp/case_a01_events.db')
store.execute(\"DELETE FROM audit_events WHERE run_id = 'CASE-A01-20261015-001'\")
store.commit()
store.connection.execute('PRAGMA wal_checkpoint(TRUNCATE)')
print('rollback complete')
"
```

### 6.3 致命故障回滚（F1 链路级）

如果 CASE-A01 执行中检测到链路级故障（短ID 500 / 对照组失败），执行灰度仿真已验证的 F1 回滚矩阵：

1. **立即自动回滚全部品种**
2. DEP 状态回退: RECOVERED → ROLLED_BACK
3. 所有证据包标记 `retired=true`
4. 事件存储标记 `retired=true`
5. 面板触发告警 `GATE_REVIEW_PAUSED`
6. FLAG 更新: `GATE_DECISION=NOT_READY, JOB_READY=FALSE`
7. 人工记录: DEP_ROLLBACK_COMPLETE 事件

---

## 7. 执行记录模板

执行完成后，填写以下记录并提交到 STATUS.md:

```markdown
## CASE-A01 真实环境执行记录

**执行时间**: YYYY-MM-DD HH:MM UTC
**执行者**: HERMES
**DEP-001 状态**: RECOVERED / BLOCKED
**整体判定**: PASS / FAIL

| 步骤 | 耗时 | 结果 | 断言数 | PASS | FAIL |
|------|------|------|--------|------|------|
| Step 1 证据包 | X.X ms | PASS/FAIL | 3 | X | X |
| Step 2 Gate | X.X s | PASS/FAIL | 4 | X | X |
| Step 3 审计 | X.X ms | PASS/FAIL | 4 | X | X |
| Step 4 存储 | X.X ms | PASS/FAIL | 3 | X | X |
| Step 5 面板 | X.X s | PASS/FAIL | 3 | X | X |

**端到端延迟**: X.X s
**事件写入数**: X
**去重数**: X
**CRITICAL 事件**: 0

**指标对比（仿真 vs 真实）**:
| 指标 | 仿真基线 | 真实值 | 偏差 |
|------|----------|--------|------|
| 审计耗时 | 7.2ms | X.Xms | X% |
| 写入延迟 | 915ms | X.Xms | X% |
| 端到端 | — | X.Xs | — |

**异常记录**: (如有)
**清理状态**: 已清理 / 保留供审计
```

---

## 8. 风险与注意事项

| # | 风险 | 影响 | 缓解措施 |
|---|------|------|----------|
| R1 | DEP-001 就绪后短ID 仍有部分失败 | Step 1/2 部分断言 FAIL | 对照组验证 + 逐 ID 排查 |
| R2 | 真实环境网络延迟高于仿真 | 端到端延迟超标 | 基线已设 30s 容差，监控 p95 |
| R3 | WAL 文件增长导致磁盘压力 | Step 4 写入失败 | 每 100 页自动 checkpoint + 磁盘监控 |
| R4 | 面板服务版本不匹配 | Step 5 渲染失败 | 执行前确认面板版本号 |
| R5 | 三方权限/证书过期 | Step 2 Gate FAIL | 执行前预检查 P8 |

---

## 9. 与 DSHB/DSHE 的三方对齐

### 9.1 指标预期对齐

| 指标 | HERMES 预期 | DSHB 确认 | DSHE 确认 |
|------|------------|-----------|-----------|
| 审计耗时 ≤ 15ms | ✅ | ⏳ 待确认 | N/A |
| 真实可取数率 ≥ 95% | ✅ | ⏳ 待确认 | ⏳ 待确认 |
| 端到端 ≤ 30s | ✅ | N/A | ⏳ 待确认 |
| CRITICAL = 0 | ✅ | ⏳ 待确认 | ⏳ 待确认 |

### 9.2 跨团队对齐检查点

- **DSHB**: 确认证据包结构符合 `EVIDENCE_CONTRACT_V1`，真实可取数率计算口径与 HERMES 一致
- **DSHE**: 确认别名映射表已加载，桥接率 ≥ 80%
- **HERMES**: 确认审计器 v3 短路逻辑不改变正向链路判定语义

---

*本文档为 CASE-A01 正向 E2E 真实环境用例规范。DEP-001 就绪后，按 Step 1~5 顺序执行，全部 17 项断言 PASS 即判定 CASE-A01 通过。*
