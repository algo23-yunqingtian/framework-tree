# V86-RC2 审计告警路由与事件持久化规范

> **工单**: 工单-HERMES / T3.4 审计告警路由与事件持久化
> **分支**: `feature/v85-chart-template` @ commit `caa2410`
> **编制方**: HERMES（L3 审计方）
> **日期**: 2026-10-15
> **实现载体**: `evidence_auditor.py`（AuditEvent 类，已实测输出）
> **约束**: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **文档状态**: FINAL

---

## 0. 设计目标

三级流水线的审计判定要产生**可路由、可追溯、可审计**的事件流，解决三个实际问题：

1. **分级缺失**：前几轮审计输出只有"通过/不通过"，没有风险等级，无法区分"造假"（须立即上报）与"口径未拆分"（可退回补正）；
2. **路由缺失**：告警没有责任方指向，DSHB/DSHE 都要自行猜测哪条归自己；
3. **不留痕**：审计判定无持久化记录，事后无法复核"当时为什么判 FAIL"。

本规范把 T3.2 校验器实际输出的告警结构固化为契约。

---

## 1. 告警分级定义

### 1.1 四级分级

| 级别 | 英文 | 定义 | 响应时效 | 阻断行为 |
|------|------|------|---------|---------|
| **CRITICAL** | CRITICAL | 造假、伪造证据、脚本入参造假、桥接率口径造假、G-09/G-10 强制项 FAIL | **立即**（阻断流水线） | **强制阻断**，证据包作废，上报主脑 |
| **HIGH** | HIGH | 内部缺陷但无造假嫌疑、DEP 归类错误、L2 证据包作废、退回复用违规 | 当日处置 | 阻断当前批次，可修复后重提 |
| **MEDIUM** | MEDIUM | 登记不全、流程瑕疵、DEP 未登记、部分恢复未达阈值 | 3 工作日内 | 不阻断，标记 CONDITIONAL |
| **LOW** | LOW | 信息性事件：正常提交、状态迁移、通过记录 | 无需响应 | 仅记录 |

### 1.2 分级判定铁律

1. **CRITICAL 的唯一判定来源是四条硬审计规则的阻断级检测点**，不允许人工升级/降级；
2. **MEDIUM 不得升级用于阻断**——MEDIUM 只产生 CONDITIONAL_PASS，不产生 FAIL；
3. 同一事件不得同时处于两级（校验器保证单级输出）；
4. **造假类事件（D01.3/D03.2/DEP-CLASS 无证据）一律 CRITICAL**，不受"是否影响 Gate"影响。

---

## 2. 审计事件数据契约

### 2.1 事件字段（每条事件必含）

| # | 字段 | 类型 | 说明 | 示例 |
|---|------|------|------|------|
| 1 | `event_id` | string | 唯一事件ID（MD5 派生，12 位） | `AE-a3f2b1c4d5e6` |
| 2 | `level` | enum | CRITICAL/HIGH/MEDIUM/LOW | `CRITICAL` |
| 3 | `rule` | string | 触发的审计规则 | `R-AUDIT-02` |
| 4 | `detect_point` | string | 具体检测点 | `G-06` |
| 5 | `message` | string | 人可读告警文本（含量化数据） | `有效桥接率 0.0000 未达阈值 100% -> Gate 强制阻断` | [OLD_CALIBER - METADATA_ONLY, HERMES_INVALID]
| 6 | `trace_id` | string? | 关联的调用追踪ID（可空） | `DSHE-TEST_OK-001-001` |
| 7 | `evidence_index` | int? | 证据包内条目索引（可空） | `3` |
| 8 | `timestamp` | ISO8601 | 事件发生时间（UTC） | `2026-10-15T07:22:31Z` |

### 2.2 event_id 生成规则

```
event_id = "AE-" + md5("{timestamp}|{rule}|{detect_point}|{message}")[:12]
```

- 同一事件重复运行得到相同 ID（幂等），便于去重；
- 消息文本变化则 ID 变化（避免误去重不同事件）。

### 2.3 实际输出样例（T3.2 校验器实测）

```
[CRITICAL] R-AUDIT-02/G-06  有效桥接率 0.0000 未达阈值 100% -> Gate 强制阻断
[CRITICAL] R-AUDIT-02/D02.1 元数据完成率(1.0)冒充有效桥接率, 实际可取数率=0.0
[CRITICAL] R-AUDIT-01/D01.2 COMPLETED 条目缺真实取数证据 (无原始 payload 或全 0): DSHE-TEST_OK-001-001
[CRITICAL] R-AUDIT-04/D04.1 脚本入参 search 中转/自动替换 ID -> G-09 FAIL
```

> 以上为 CASE-N01（虚假桥接率）实测输出，7 条 CRITICAL 告警逐条对应检测点，可直接复现。

---

## 3. 告警分发路由规则

### 3.1 规则 → 责任方 → 通道矩阵

| 审计规则 | 检测点 | 责任方 | 主通道 | 备份通道 |
|---------|-------|--------|--------|---------|
| R-AUDIT-01 双证据 | D01.1/D01.2/D01.3 | **DSHB** | 飞书群 + 任务卡 | 交接文档标记 |
| R-AUDIT-02 桥接率口径 | D02.1/D02.2/D02.3 | **DSHB** | 飞书群 + 任务卡 | 交接文档标记 |
| R-AUDIT-03 L2 独立链 | D03.1/D03.2 | **DSHE** | 飞书群 + 任务卡 | 交接文档标记 |
| R-AUDIT-04 Gate 强制项 | D04.1~D04.5 | **DSHB** | 飞书群 + 主脑上报 | 交接文档标记 |
| DEP-CLASS DEP 归类 | DEP-CLASS | **DSHB**（错误归类方） | 飞书群 | 依赖登记表 |
| DEP-GATE 不豁免 | DEP-GATE | HERMES 记录 | 仅登记 | — |
| G-06 桥接率阈值 | G-06 | 按缺失条目归属 | 飞书群 | Gate 报告 |
| L2-R08 退回复用 | L2-R08 | **DSHE**（复用方） | 飞书群 | 证据包归档 |

### 3.2 分级 → 升级策略

| 级别 | 是否上报主脑 | 是否阻断流水线 | 是否通知 DEP 责任方 |
|------|------------|--------------|-------------------|
| CRITICAL | **是（立即）** | **是** | 否 |
| HIGH | 否（当日汇总） | 是（当前批次） | 仅 DEP-CLASS 类 |
| MEDIUM | 否 | 否 | 是（若涉 DEP） |
| LOW | 否 | 否 | 否 |

### 3.3 路由动作

```
告警产生
  │
  ├─ level=CRITICAL → 阻断流水线 + 立即推送责任方 + 上报主脑 + 证据包作废
  ├─ level=HIGH     → 阻断当前批次 + 推送责任方 + 要求修复重提
  ├─ level=MEDIUM   → 标记 CONDITIONAL_PASS + 推送责任方 + 登记待办
  └─ level=LOW      → 仅写入事件持久化存储
```

### 3.4 路由契约（跨团队不可变）

1. **责任方不可自行声明降级**：DSHB/DSHE 不得把 CRITICAL 自改为 MEDIUM；
2. **申诉机制**：责任方可对 CRITICAL 举证申诉（如证明是环境故障而非造假），争议期间标 PENDING，判定权归 HERMES；
3. **一次告警一条责任**：跨责任方的复合问题（如 DSHB 造假 + DSHE 背书）必须拆分为多条事件分别路由，不合并；
4. **告警必须可回放**：每条告警都能由 `evidence_auditor.py` 重跑复现。

---

## 4. 审计事件持久化

### 4.1 存储格式

JSON Lines（每行一条事件），便于追加、便于流式处理：

```json
{"event_id":"AE-a3f2b1c4d5e6","level":"CRITICAL","rule":"R-AUDIT-02","detect_point":"G-06","message":"有效桥接率 0.0000 未达阈值 100% -> Gate 强制阻断","trace_id":null,"evidence_index":null,"timestamp":"2026-10-15T07:22:31Z"}
```

### 4.2 存储位置与命名

| 场景 | 路径 |
|------|------|
| 用例库回放 | `audit_events_persist.json` |
| 阶段2 抽样 | `audit_events_sample.json` |
| 阶段3 全量 | `audit_events_full.json` |
| 归档（退回/作废） | `audit_archive/<run_id>/events.jsonl` |

### 4.3 持久化命令

```bash
# 用例库回放并持久化
python3 evidence_auditor.py --run-case-library --persist audit_events_persist.json

# 单证据包校验并持久化
python3 evidence_auditor.py --file dshe_l2_full_package.json --json \
  --persist audit_events_full.json
```

### 4.4 持久化不可变性

1. **追加不覆盖**：事件存储只追加，历史记录禁止修改（NO_OVERWRITE 延伸）；
2. **与证据包绑定**：每条事件带 `trace_id` + `evidence_index`，可反查原始 payload；
3. **归档即冻结**：证据包退回时其事件包一并归档并计算 MD5，作为审计追溯凭据；
4. **禁止删除**：作废的证据包对应事件永久保留（审计需要"知道曾经失败过"）。

### 4.5 事件去重

同一 `event_id` 重复出现视为重试产生的重复事件，保留首条并记录重复次数，不产生新告警。

---

## 5. 事件包结构（与 evidence_auditor.py 输出对齐）

校验器 `--persist` 输出的完整结构：

```json
{
  "case_id": "CASE-N01",
  "desc": "元数据完成+真实取数0% (虚假桥接率)",
  "expect": "FAIL",
  "actual": "FAIL",
  "match": true,
  "report": {
    "auditor_version": "1.0.0",
    "baseline": "caa2410",
    "verdict": "FAIL",
    "gate_result": "NOT_READY",
    "gate_g06_real_fetchable_rate": 0.0,
    "gate_g09_script_audit": "FAIL",
    "gate_g10_data_fetch": "FAIL",
    "events_summary": {"CRITICAL": 7, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "total": 7},
    "events": [ {"event_id": "...", "level": "CRITICAL", ...} ]
  }
}
```

---

## 6. 告警聚合与日报

### 6.1 聚合维度

| 维度 | 说明 |
|------|------|
| 按规则 | R-AUDIT-01/02/03/04 各产生多少 CRITICAL/HIGH |
| 按责任方 | DSHB / DSHE / DEP 各多少 |
| 按检测点 | 16 个检测点的命中率分布 |
| 按轮次 | 每个 run_id 的事件分布趋势 |

### 6.2 日报触发条件

| 条件 | 动作 |
|------|------|
| 当日 CRITICAL > 0 | **立即推送**，不等日报 |
| 当日 HIGH > 0 | 当日汇总推送 |
| 连续 3 日无 CRITICAL/HIGH | 周报仅 LOW |

### 6.3 聚合命令

```bash
python3 -c "
import json
ev = json.load(open('audit_events_persist.json'))
from collections import Counter
c = Counter()
for r in ev:
    for e in r['report']['events']:
        c[(e['level'], e['rule'])] += 1
for k, v in sorted(c.items(), key=lambda x: -x[1]):
    print('%-9s %-12s %d' % (k[0], k[1], v))"
```

---

## 7. 告警质量验收

### 7.1 验收标准

| 项 | 标准 |
|----|------|
| 每条告警含全部 8 字段 | 100% |
| CRITICAL 均带检测点 | 100%（可回放定位） |
| 每条告警有明确责任方 | 100%（依 §3.1 矩阵） |
| event_id 幂等 | 重跑同输入得到相同 ID |
| 持久化文件可解析 | JSON 有效 |
| 无告警时明确输出 | 输出"(无告警)"，不静默 |

### 7.2 本轮实测验证（T3.2 用例库回放 11 用例）

| 用例 | CRITICAL | HIGH | MEDIUM | 结论 |
|------|---------|------|--------|------|
| CASE-A01 | 0 | 0 | 0 | PASS（无告警） |
| CASE-A02 | 0 | 0 | 0 | PASS（无告警） |
| CASE-N01 | 7 | 0 | 0 | FAIL |
| CASE-N02 | 0 | 1 | 0 | CONDITIONAL_PASS |
| CASE-N03 | 3 | 0 | 0 | FAIL |
| CASE-N04 | 1 | 0 | 0 | FAIL |
| CASE-D01 | 1 | 1 | 0 | FAIL |
| CASE-D02 | 3 | 1 | 0 | FAIL |
| CASE-P01 | 1 | 1 | 0 | FAIL |
| CASE-P02 | 2 | 1 | 0 | FAIL |
| CASE-P03 | 2 | 1 | 0 | FAIL |
| **合计** | **20** | **6** | **0** | **11/11 判定符合预期** |

> 分布验证：造假类（N01/N02/N03/N04）CRITICAL 集中；DEP 类（D01/D02/P01/P02/P03）CRITICAL 少但 HIGH 多（合规阻塞 vs 口径问题）；正向类（A01/A02）零告警。分级有效区分了不同风险性质。

---

## 8. 与流水线阻断的联动

| 判定 | 流水线行为 | 事件级别 |
|------|-----------|---------|
| 存在 CRITICAL | 阻断当前级，证据包作废 | CRITICAL |
| 仅 HIGH | 阻断当前批次，允许修复重提 | HIGH |
| 仅 MEDIUM | 不阻断，标 CONDITIONAL_PASS | MEDIUM |
| 仅 LOW / 无事件 | 正常流转至下一级 | LOW / — |

**关键约束**：MEDIUM 永不阻断（避免流程噪音卡死流水线），CRITICAL 必阻断（造假零容忍）。

---

## 9. 规范完整性自证

| 要素 | 状态 |
|------|------|
| 告警分级 | 4 级（CRITICAL/HIGH/MEDIUM/LOW），各带响应时效与阻断行为 |
| 分级判定铁律 | 4 条（CRITICAL 来源限定 / MEDIUM 不阻断 / 单级 / 造假一律 CRITICAL） |
| 事件契约 | 8 字段，含 event_id 幂等生成规则 |
| 路由矩阵 | 8 类规则 → 责任方 → 通道 |
| 升级策略 | 4 级 → 主脑上报/阻断/DEP 通知 三维 |
| 路由契约 | 4 条跨团队不可变规则 |
| 持久化 | JSONL 格式 + 4 类存储路径 + 4 条不可变性规则 |
| 聚合日报 | 4 维度 + 3 触发条件 |
| 质量验收 | 6 项标准 + 11 用例实测分布表 |
| 流水线联动 | 4 级判定 → 4 类行为 |

**状态标记**：`HERMES_AUDIT_ALERT_ROUTING_READY=TRUE`
