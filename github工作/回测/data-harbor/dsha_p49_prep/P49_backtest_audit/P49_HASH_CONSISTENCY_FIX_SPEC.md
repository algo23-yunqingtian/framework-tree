# P49 哈希一致性修复方案 · Hash Consistency Fix Specification

> **文档ID**: DSHA-P54-P49-HASH-FIX-SPEC-001
> **生成时间**: 2026-10-16 GMT+8
> **Agent**: DSHA-P54
> **Branch**: feature/v88-g1
> **GATE**: CLOSED/HOLD
> **Wind API Calls**: 0
> **声明**: 纯离线分析文档，不直接修改任何原始checksum文件。

---

## 0. 问题描述

### 0.1 漂移现状

在 P49_factor_version_diff_report.md 第5节中检测到：
- **17 个被追踪文件中，13 个存在哈希漂移**（76.5% 不一致率）
- **仅 4 个文件一致**（G7_DSHA_DSHD_MONITORING_ROUND_001/002.md、DSHD_P67_EXPLORATION_RISK_OBSERVATION_BRIEF.md）

### 0.2 漂移根因分析

| 根因 | 说明 | 影响文件数 |
|---|---|---|
| 多时间源生成 | SHA256_CHECKSUMS.txt 和 MANIFEST 在不同时间点分别生成，中间文件内容被更新 | 13/17 |
| MANIFEST 使用原始文件 | MANIFEST 中的 sha256 值来自文件创建时的原始版本，SHA256_CHECKSUMS.txt 使用刷新后的版本 | 13/17 |
| P49_pre_gray_check.md 缺失 | 磁盘不存在，SHA256_CHECKSUMS.txt 标记 MISSING，MANIFEST 有完整引用记录 | 1/17 |
| 自身不追溯 | SHA256_CHECKSUMS.txt 不包含自身哈希（自引用排除），MANIFEST 包含 tracking_monitor_audit.jsonl 但 MANIFEST 不含自身 | 0 (设计如此) |

### 0.3 具体漂移对照

| 文件 | SHA256_CHECKSUMS.txt (当前) | MANIFEST (原始) | 文件大小差 |
|---|---|---|---|
| FL01_FL02_manual_review.md | `1AF9BB37C20FBEC5...` | `EB8689D71B29F582...` | +621B (25,027 vs 24,406) |
| poll39_main_audit_report.md | `8B8A08E1EC4C9EAA...` | `B328A408B889D6CB...` | +147B (8,439 vs 8,292) |
| poll39_factor_leakage_risk_appendix.md | `8982FE433CE258F9...` | `2E8377D02604C5DD...` | +179B (8,716 vs 8,537) |
| P66_KB_SECOND_REVIEW_REPORT.md | `A7FF6E8818257B75...` | `244371CA5E2177C2...` | +154B (4,359 vs 4,205) |
| WL006_WL014_whitelist_draft.md | `FD7FB054B5702CBA...` | — (MANIFEST 无此项) | 仅 SHA256_CHECKSUMS.txt |
| DRAFT_REVIEW_COMMENTS.md | `B32D7A4CCE4FC9D0...` | `5201F239D7C2F9FF...` | +304B (14,660 vs 14,356) |
| DRAFT_REVIEW_COMMENTS_RESPONSE.md | `4A9DB50197B01B6E...` | `131F99879E03E733...` | +74B (2,164 vs 2,090) |
| G7_FACTOR_ADJUDICATION_REPORT.md | `A87D1896DE6D121D...` | `EF98B5510B95833A...` | +236B (12,307 vs 12,071) |
| G7_ADJUDICATION_PACKAGE_MANIFEST.json | `8520C256001FA2FC...` | — (自引用排除) | — |
| G7_CONDITIONAL_RELEASE_PERMIT.md | `7D37ADDB83E9A08F...` | `E534B27ACD88442A...` | +82B (3,314 vs 3,232) |
| G7_CONDITIONAL_RELEASE_BROADCAST.md | `EDAC4071C2CE7E4D...` | `F138F6BFA75FDF26...` | +86B (2,749 vs 2,663) |
| G7_CONDITIONAL_BACKTEST_CHAIN_AUDIT_SUMMARY.md | `2CAC9B471FF38706...` | `762124DD55A95896...` | +449B (4,394 vs 3,945) |
| G7_CONDITIONAL_WIND_TEMP_CREDENTIAL.md | `466406FD1C5263F5...` | `0C8834AE0C32A144...` | +70B (3,492 vs 3,422) |
| G7_EXCEL_WIND_PLUGIN_ACCESS_GUIDE.md | `8BE852C3ED5BEE55...` | `B96B5A1FDB8C9897...` | +136B (4,905 vs 4,769) |
| G7_DSHA_DSHD_MONITORING_ROUND_001.md | `BF9742B48584EF99...` | `BF9742B48584EF99...` | 0B ✅ |
| G7_DSHA_DSHD_MONITORING_ROUND_002.md | `7B304A635DC76ECA...` | `7B304A635DC76ECA...` | 0B ✅ |
| DSHD_P67_EXPLORATION_RISK_OBSERVATION_BRIEF.md | `35E930F691AB1E25...` | `35E930F691AB1E25...` | 0B ✅ |

---

## 1. 修复方案定义

### 1.1 唯一可信哈希源（Canonical Hash Source）

**方案选定**: **SHA256_CHECKSUMS.txt** 作为唯一可信哈希源。

**理由**:

| 评判标准 | SHA256_CHECKSUMS.txt | MANIFEST (documents[].sha256) |
|---|---|---|
| 时间戳标注 | ✅ 有（2026-10-16 20:35 GMT+8） | ❌ 无逐文件时间戳 |
| 文件大小记录 | ✅ 有 | ✅ 有 |
| 更新后刷新 | ✅ 本轮已刷新 | ❌ 未刷新 |
| 自引用排除 | ✅ 明确排除 | ❌ 未明确排除 |
| 缺失文件标注 | ✅ MISSING 状态标注 | ❌ 部分引用已缺失文档 |
| 覆盖完整性 | ✅ 20 文件 (含 MISSING 标注) | ⚠️ 20 文件但部分哈希过时 |
| 可读性 | ✅ 表格格式 | ⚠️ JSON 嵌套 |

### 1.2 哈希源层级关系

```
┌──────────────────────────────────────────────────────────┐
│          LAYER 1: Canonical Source (唯一可信源)            │
│  SHA256_CHECKSUMS.txt                                    │
│  ─ 磁盘实际状态的权威快照                                    │
│  ─ 由 DSHC-P66 在 2026-10-16 20:35 重建                   │
│  ─ 任何哈希引用必须以此为准                                 │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│          LAYER 2: Reference Source (引用源)               │
│  G7_ADJUDICATION_PACKAGE_MANIFEST.json                   │
│  ─ documents[].sha256 值仅用于历史追溯                     │
│  ─ 不再作为当前哈希验证基准                                 │
│  ─ 后续引用时须交叉验证 SHA256_CHECKSUMS.txt                │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│          LAYER 3: Validation Target (验证对象)            │
│  G7_FACTOR_ADJUDICATION_REPORT.md                         │
│  P49_factor_version_diff_report.md                        │
│  ─ 所有文档中引用的哈希值必须溯源到 SHA256_CHECKSUMS.txt     │
│  ─ 不一致时以 SHA256_CHECKSUMS.txt 为准                    │
└──────────────────────────────────────────────────────────┘
```

### 1.3 修复步骤（建议性，不执行）

| 步骤 | 操作 | 执行者 | 前置条件 |
|---|---|---|---|
| 1 | 确认 SHA256_CHECKSUMS.txt 为唯一可信源 | DSHC 审核确认 | 本文档审核通过 |
| 2 | MANIFEST 中标记 `sha256_source`: `SHA256_CHECKSUMS.txt` | DSHC 授权后执行 | 步骤1完成 |
| 3 | MANIFEST 中 documents[].sha256 加注 `status`: `HISTORICAL_ONLY` | DSHC 授权后执行 | 步骤1完成 |
| 4 | 所有新文档引用哈希时统一标注 `source: SHA256_CHECKSUMS.txt` | DSHC 授权后执行 | 步骤1-2完成 |
| 5 | 后续每次文件更新，SHA256_CHECKSUMS.txt 同步刷新 | DSHC 授权后执行 | 步骤4完成 |

### 1.4 当前阶段声明

> **当前阶段执行方式**: 本文档仅定义修复方案，**不执行任何文件修改**。
> SHA256_CHECKSUMS.txt 和 MANIFEST 均保持原始状态。
> 修复需经 DSHC 审核确认后授权执行。

---

## 2. 漂移影响评估

### 2.1 治理影响

| 维度 | 影响 | 说明 |
|---|---|---|
| 治理不变量 | ❌ 无影响 | 13 个漂移文件均未涉及治理控制面文件 |
| 因子准入判断 | ❌ 无影响 | 哈希漂移不涉及因子定义或准入状态 |
| 审计一致性 | ⚠️ 低影响 | 审计事件记录与当前文件内容一致，仅哈希元数据漂移 |
| 文件完整性验证 | ⚠️ 中影响 | 13 个文件无法通过 MANIFEST 校验，需切换至 SHA256_CHECKSUMS.txt |
| 回滚/比对 | ⚠️ 中影响 | 历史版本追溯需参考 MANIFEST 中 sha256，但文件内容已变更 |

### 2.2 修复优先级

| 优先级 | 修复项 | 影响 |
|---|---|---|
| P0 | 确认唯一哈希源 | 消除13个文件的校验歧义 |
| P1 | MANIFEST 标注历史哈希 | 防止错误引用 |
| P2 | 补齐 P49_pre_gray_check.md | 消除 1 个 MISSING 文档 |
| P3 | 未来文件更新自动同步哈希 | 防止新漂移 |

---

## 3. 预防措施

### 3.1 哈希同步规则

```
RULE-1: SHA256_CHECKSUMS.txt 为唯一写入点
  → 任何文件修改后，仅更新 SHA256_CHECKSUMS.txt 对应行
  → MANIFEST 中的 sha256 不再更新，仅保留为历史记录

RULE-2: 新增文件必须同时写入 SHA256_CHECKSUMS.txt
  → 新建文件前，在 SHA256_CHECKSUMS.txt 中预留行位
  → 文件生成后立即计算并写入哈希

RULE-3: 引用哈希时须标注来源
  → 引用哈希格式: `sha256: <hash> (source: SHA256_CHECKSUMS.txt)`
  → 引用 MANIFEST 历史哈希格式: `sha256: <hash> (source: MANIFEST, historical)`

RULE-4: 定期完整性检查
  → 每次 DSHA 任务完成后，运行哈希验证脚本
  → 对比 SHA256_CHECKSUMS.txt 与磁盘实际值
```

### 3.2 哈希验证脚本（伪代码）

```python
# 哈希验证脚本（建议）
import hashlib

def verify_hash(filepath, expected_hash, source):
    """验证文件哈希与预期值是否一致"""
    actual_hash = hashlib.sha256(open(filepath, 'rb').read()).hexdigest().upper()
    return actual_hash == expected_hash.upper()

def verify_all(checksum_file="SHA256_CHECKSUMS.txt"):
    """验证所有文件哈希"""
    # 解析 SHA256_CHECKSUMS.txt
    # 逐个验证
    # 返回: 通过/失败 列表
    pass
```

---

## 4. 总结

| 项目 | 结果 |
|---|---|
| 漂移文件数 | 13/17 |
| 唯一可信源 | SHA256_CHECKSUMS.txt |
| 治理影响 | 无 |
| 修复方案 | 3层哈希源层级 + 4条同步规则 |
| 当前阶段 | 仅定义方案，不执行修改 |
| 授权需求 | 需 DSHC 审核确认后授权执行 |

> **DSHA-P54 声明**: 本文档为纯离线分析产物，未调用任何 Wind API。
> 所有治理不变量保持：wind_api_calls=0, backtest_started=false, gate=CLOSED/HOLD, release_permit=NOT_ISSUED。

---

_生成时间: 2026-10-16 GMT+8 | Agent: DSHA-P54 | Branch: feature/v88-g1_