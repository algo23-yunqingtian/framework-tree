# V86-RC2 审计告警路由与事件持久化规范 v2（持久化升级版）

> **工单**: 工单-HERMES / T3.5 审计事件持久化模块升级
> **分支**: `feature/v85-chart-template` @ commit `dcf7194`
> **编制方**: HERMES（L3 审计方）
> **日期**: 2026-10-15
> **实现载体**: `audit_event_store.py`（STORE v2.0.0，实测自检 11 类通过）
> **v1 文档**: `v86_rc2_hermes_alert_routing_spec.md`（MD5 `d94cbba2`，**保留不删**）
> **约束**: NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **状态**: FINAL — 本文件为新增迭代版本，v1 保留（NO_OVERWRITE）

---

## 0. v2 相对 v1 的升级

| 维度 | v1（d94cbba2） | **v2（本轮）** |
|------|----------------|----------------|
| 事件来源 | 仅审计器产出 | **三方上报**（DSHB/DSHE/HERMES 均可主动上报） |
| 存储 | 静态 JSON 导出（覆盖式） | **JSONL 追加式**，历史记录不可修改 |
| 去重 | 无 | **event_id 幂等去重** + `dedup_count` 计数 |
| DEP 关联 | 无 | **`dep_registry_id` 强关联** + 按 DEP 追溯 |
| 检索 | 无 | **6 维检索**（team/rule/dep/level/trace/fingerprint） |
| 统计 | 无 | **4 维分布** + DEP 最差等级推导 |
| 导入 | 无 | 审计器报告 / 批量报告自动导入 |
| 实现 | 无代码 | `audit_event_store.py`（23KB，实测通过） |

---

## 1. 事件契约 v2（8 字段基础 + 6 字段扩展）

### 1.1 基础字段（v1 沿用）

| # | 字段 | 类型 | 说明 |
|---|------|------|------|
| 1 | `event_id` | string | 唯一ID，`AE-` + MD5 前 12 位 |
| 2 | `level` | enum | CRITICAL / HIGH / MEDIUM / LOW |
| 3 | `rule` | string | 审计规则 |
| 4 | `detect_point` | string | 检测点 |
| 5 | `message` | string | 告警文本 |
| 6 | `timestamp` | ISO8601 | 事件发生时间 |
| 7 | `trace_id` | string? | 调用追踪ID |
| 8 | `evidence_index` | int? | 证据包内索引 |

### 1.2 v2 扩展字段

| # | 字段 | 类型 | 说明 |
|---|------|------|------|
| 9 | `source_team` | enum | 上报方：`DSHB` / `DSHE` / `HERMES` / 提交方 |
| 10 | `owner` | string | 责任方（按规则自动推导） |
| 11 | `dep_registry_id` | string? | **DEP 登记ID**（`DEP-REG-NNN`），跨团队关联核心 |
| 12 | `audit_fingerprint` | string? | 证据包审计指纹 |
| 13 | `evidence_file` | string? | 证据包文件名 |
| 14 | `run_id` | string? | 运行ID |
| 15 | `received_at` | ISO8601 | 存储接收时间 |
| 16 | `dedup_count` | int | 上报次数（去重折叠计数） |

### 1.3 event_id 幂等生成

```
event_id = "AE-" + md5(level|rule|detect_point|message|source_team
                       |dep_registry_id|evidence_index|trace_id)[:12]
```

**幂等性**：同一事件多次上报得到相同 ID，重复上报折叠为 `dedup_count` 累加，不新增记录。

### 1.4 source_team 前缀识别

三方 `caller` 常带版本后缀（如 `DSHE_V86_RC2_L2_AUDIT`、`DSHB_L1_SELF_TEST`），
存储按**前缀归一**为 `DSHB`/`DSHE`/`HERMES`：

| 上报 caller | 归一为 |
|------------|--------|
| `DSHB` / `DSHB_L1_SELF_TEST` | DSHB |
| `DSHE` / `DSHE_V86_RC2_L2_AUDIT` | DSHE |
| `HERMES` | HERMES |

> **设计理由**：实测发现若要求精确匹配，DSHE 的正常上报会被全部误拒
> （`source_team: DSHE_V86_RC2_L2_AUDIT` 不在枚举内）。前缀识别保证
> 三方上报不被格式细节误杀，同时仍拒绝真正未知的来源。

---

## 2. 事件校验规则（上报准入）

上报事件必须先通过校验，不合规即拒绝并报告原因：

| 校验 | 规则 | 失败处理 |
|------|------|---------|
| 类型 | 必须是 JSON 对象 | 拒绝 |
| `level` | 必属 CRITICAL/HIGH/MEDIUM/LOW | 拒绝 |
| `rule` | 必属合法规则集（7 条） | 拒绝 |
| `detect_point` | 必填 | 拒绝 |
| `message` | 必填 | 拒绝 |
| `source_team` | 可前缀归一，否则拒绝 | 拒绝 |
| `dep_registry_id` | 若非空，须匹配 `DEP-REG-NNN` | 拒绝 |

实测：非法 `level=SEVERE`、缺 `rule/detect_point/message`、
`dep_registry_id=DEP-123`（格式错）均被正确拒绝。

---

## 3. 存储模型

### 3.1 JSONL 追加式

```
{JSONL 路径}: audit_event_store.jsonl
每行一条事件 (json.dumps, ensure_ascii=False)
```

### 3.2 追加语义（只追加不删除）

1. **新增**：`event_id` 未见 → 追加到存储末尾；
2. **去重**：`event_id` 已见 → `dedup_count += 1`，更新 `last_seen`，不新增行；
3. **禁止修改**：历史事件的 `level`/`rule`/`message`/`timestamp` 等原始字段**不可变更**；
4. **禁止删除**：作废证据包的事件永久保留（审计需知道"曾失败"）。

### 3.3 去重语义验证（实测）

| 步骤 | 动作 | 新增 | 去重折叠 | 存储条数 |
|------|------|------|---------|---------|
| 1 | 上报事件 A | 1 | 0 | 1 |
| 2 | 上报 A + A（重复内容） | 0 | 2 | 1 |
| 3 | 校验 `dedup_count` | — | — | `= 3` |

实测：`dedup_count=3`，存储保持 1 条唯一记录 —— 去重正确。

---

## 4. 跨团队检索（6 维）

| 维度 | 参数 | 语义 |
|------|------|------|
| 团队 | `--team DSHB` | 按 `source_team` 或 `owner` 匹配 |
| 规则 | `--rule R-AUDIT-02` | 精确匹配规则 |
| DEP | `--dep DEP-REG-001` | 按 DEP 登记ID 追溯 |
| 等级 | `--level critical` | 大小写不敏感 |
| 调用 | `--trace T-001` | 精确匹配 trace_id |
| 指纹 | `--fingerprint FP-001` | 精确匹配审计指纹 |

维度可组合（AND 关系）。实测：按 `DEP-REG-001` 检索返回 10 条、
按 `DSHB` 检索返回 29 条（存储共 41 条）。

### 4.1 按 DEP 追溯的价值

`DEP-REG-001` 是三方共用的短ID 解析依赖。按 DEP 检索可一次拿到该依赖
的**全生命周期告警**——DSHB 的阻塞上报、DSHE 的台账不一致、
HERMES 的 G-06 阻断——跨团队串成一条完整时间线。

---

## 5. 统计与 DEP 索引

### 5.1 四维统计

| 维度 | 说明 |
|------|------|
| 按等级 | CRITICAL / HIGH / MEDIUM / LOW 计数 |
| 按规则 | 7 条审计规则分布 |
| 按责任方 | DSHB / DSHE / DSHB/DSHE / 提交方 |
| 按上报团队 | 谁在上报（区分责任方） |

### 5.2 DEP 最差等级推导

每个 `dep_registry_id` 推导其历史最严重等级：

```
DEP-REG-001 → 10 条事件，最差 = CRITICAL
```

**用途**：三方交叉比对时，一眼看出哪个 DEP 风险最高，优先处理。

### 5.3 实测统计输出

```
  唯一事件: 41  |  含去重总接收: 49  |  去重折叠: 8
  按等级: CRITICAL 31 | HIGH 7 | MEDIUM 3 | LOW 0
  按规则: R-AUDIT-01 2 | R-AUDIT-02 10 | R-AUDIT-03 5 | R-AUDIT-04 12
          R-CONTRACT-V1 3 | R-DEP-STATE 5 | R-LEGACY-CAL 4
  按责任方: DSHB 28 | DSHB/DSHE 5 | DSHE 5 | 提交方 3
  按 DEP: DEP-REG-001 10 (最差: CRITICAL)
```

---

## 6. 三方上报通道

### 6.1 上报方式

```bash
# DSHB 上报单条
python3 audit_event_store.py --store <store.jsonl> --event '{
  "level":"HIGH","rule":"R-DEP-STATE","detect_point":"DS-05",
  "message":"台账 last_change_timestamp 不一致",
  "source_team":"DSHB","dep_registry_id":"DEP-REG-001","trace_id":"EXT-DSHB-001"}'

# DSHE 上报单条
python3 audit_event_store.py --store <store.jsonl> --event '{
  "level":"MEDIUM","rule":"R-CONTRACT-V1","detect_point":"CV-05",
  "message":"证据包缺 md5_manifest",
  "source_team":"DSHE","dep_registry_id":"DEP-REG-001"}'

# 批量上报 (JSON 数组)
python3 audit_event_store.py --store <store.jsonl> --ingest-batch events.json

# 从审计器报告自动导入
python3 audit_event_store.py --store <store.jsonl> --audit-report batch_r.json
```

### 6.2 通道矩阵

| 通道 | 来源 | 触发方式 |
|------|------|---------|
| 审计器报告导入 | evidence_auditor_v2 / batch_runner | `--audit-report` |
| DSHB 主动上报 | DSHB 自测/触发器 | `--event` / `--ingest-batch` |
| DSHE 主动上报 | DSHE L2 校验/DEP 监听 | `--event` / `--ingest-batch` |
| HERMES 预审 | L3 流水线 | `--audit-report` |

### 6.3 上报契约要求

1. **必须提供 `level` + `rule` + `detect_point` + `message`**，缺一即拒绝；
2. **涉及 DEP 必须提供 `dep_registry_id`**（格式 `DEP-REG-NNN`）；
3. **`source_team` 必须为真实上报方**，禁止代报（责任归因依赖此字段）；
4. **重复上报安全**：同内容多次上报只累加 `dedup_count`，不产生重复记录。

---

## 7. 告警路由（v1 沿用 + v2 增强）

### 7.1 规则 → 责任方矩阵（v1 沿用）

| 规则 | 责任方 | 级别 |
|------|--------|------|
| R-AUDIT-01 双证据 | **DSHB** | CRITICAL |
| R-AUDIT-02 桥接率口径 | **DSHB** | CRITICAL |
| R-AUDIT-03 L2 独立链 | **DSHE** | CRITICAL |
| R-AUDIT-04 Gate 强制项 | **DSHB** | CRITICAL |
| R-DEP-STATE 状态机/台账 | **DSHB/DSHE** | CRITICAL（DS-02/03/05） |
| R-CONTRACT-V1 契约完整性 | 提交方 | HIGH/MEDIUM |
| R-LEGACY-CAL 存量旧口径 | **DSHB** | CRITICAL |

### 7.2 v2 增强：路由可追溯

v1 只定义"告警发给谁"，v2 增加**路由可追溯**：
每条事件持久化 `source_team`（谁报的）与 `owner`（谁负责），
可按责任方检索全部待处置告警：

```bash
python3 audit_event_store.py --store <store> --query --team DSHB
# 返回 29 条 DSHB 负责的告警，按时间线可逐条处置
```

### 7.3 分级阻断（v1 沿用）

| 级别 | 阻断 | 持久化要求 |
|------|------|-----------|
| CRITICAL | **强制阻断** | 必须持久化 + 立即上报 |
| HIGH | 阻断当前批次 | 必须持久化 |
| MEDIUM | 不阻断（CONDITIONAL） | 必须持久化 |
| LOW | 仅记录 | 可仅持久化 |

---

## 8. 与流水线的挂载

```
L1 DSHB 自测包 ─┐
L2 DSHE 证据包 ─┤→ batch_evidence_audit_runner.py → 审计报告 JSON
                │
                ├→ audit_event_store.py --audit-report  →  事件存储 (JSONL)
DSHB/DSHE 上报 ─┘
                │
                ├→ --query --team X  (派工检索)
                ├→ --query --dep X   (DEP 生命周期追溯)
                └→ --stats           (日报聚合)
```

---

## 9. 自检结果（实测）

`audit_event_store.py --self-test` **11 类检查全部通过**：

| # | 检查类 | 内容 |
|---|--------|------|
| 1 | 正常事件归一化 | 字段提取 + 责任方推导 |
| 2 | event_id 幂等 | 同内容多次生成相同 ID |
| 3 | 非法 level 拒绝 | `SEVERE` 被拒 |
| 4 | 缺必填拒绝 | rule/detect_point/message 缺项逐一检测 |
| 5 | 非法 DEP 格式拒绝 | `DEP-123` 被拒 |
| 6 | 存储追加 + 去重 | 新增/去重计数正确 |
| 7 | 6 维检索 | team/rule/dep/level/trace/fingerprint |
| 8 | 统计正确 | 唯一数/去重折叠/DEP 最差等级 |
| 9 | 审计器报告导入 | 单报告事件转换 |
| 10 | 批量报告导入 | SKIPPED 正确跳过 |
| 11 | 规则集合完整 | RULE_OWNER 与 RULES 一致 |

**结论**: `SELF-TEST PASSED / EXIT=0`

---

## 10. 端到端实测记录

| 步骤 | 命令 | 结果 |
|------|------|------|
| 1 | `batch_evidence_audit_runner.py --demo --json batch_r.json` | 23 包审计，39 事件 |
| 2 | `audit_event_store.py --audit-report batch_r.json` | 新增 39，去重 8，拒绝 0 |
| 3 | DSHB 外部上报 | 新增 1 |
| 4 | DSHE 外部上报 | 新增 1 |
| 5 | 重复上报 | 去重折叠 1（dedup_count 累加） |
| 6 | `--query --dep DEP-REG-001` | 返回 10 条 |
| 7 | `--query --team DSHB` | 返回 29 条 |
| 8 | `--stats` | 41 唯一 / 49 含去重 / DEP-REG-001 最差 CRITICAL |

---

## 11. 完整性自证

| 要素 | 状态 |
|------|------|
| 事件契约 v2 | 16 字段（8 基础 + 6 扩展 + 2 元数据） |
| event_id 幂等 | MD5 派生，重复上报折叠 |
| source_team 归一 | 前缀识别（防格式误杀） |
| 校验规则 | 7 条，实测拒绝非法输入 |
| 存储模型 | JSONL 追加，只增不删 |
| 去重语义 | dedup_count 累加，实测验证 |
| 检索维度 | 6 维可组合 |
| 统计维度 | 4 维 + DEP 最差等级 |
| 上报通道 | 4 种（2 自动导入 + 2 主动上报） |
| 路由可追溯 | source_team vs owner 分离 |
| 自检 | 11 类通过 |
| NO_OVERWRITE | v1 规范保留（MD5 `d94cbba2`） |

**状态标记**：`HERMES_AUDIT_EVENT_STORE_V2_READY=TRUE`
