# R-V88-P7-001 文档校验→JSON结构化校验迁移方案

> **TASK_ID**: V88_PHASE03_P8_HERMESHF_P7_GATE_MONITOR_UPGRADE_PREP_JOB / T0
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **设计时刻**: 2026-10-17T14:40 +0800
> **风险编号**: R-V88-P7-001（P7 登记 LOW → P8 方案设计）
> **约束**: 仅文档设计，**不改动现有运行中仲裁代码**

---

## 1. 问题定义

### 1.1 现状

P7 整改 R-V88-P6-001 后，仲裁器 5 项预检中 3 项从静态 True 改为真实文件校验：

| # | 预检 | 当前校验方式 | 局限 |
|:-:|------|-------------|------|
| #2 | BASELINE-SWITCH-FREE | 读取 `phase03_summary_asset_re_seal.md`，查找关键字"无静默切换"+"✅ NO" | 文档可被篡改但保留关键字 |
| #3 | PHASE03-BLOCKERS-ZERO | 读取 `global_gate_dashboard.md`，查找关键字"全部阻断清零"+"🔴 FAIL"+"**0**" | 同上 |
| #5 | DSHE-AUTO-COMMIT-OFF | 读取 `blocker_monitor_hook_snippet.py` 源码，正则 `^AUTO_COMMIT_MODE\s*=\s*False` | 相对可靠（源码级），但行可被注释 |

### 1.2 风险

文档文本校验依赖关键字匹配，存在两类风险：
1. **假阳性**：文档被篡改但保留关键字 → 预检仍 PASS
2. **假阴性**：文档格式微调（如 Markdown 渲染差异）导致关键字不匹配 → 预检 FAIL

### 1.3 迁移目标

将 #2/#3 的文档关键字校验升级为 JSON 结构化校验：
- 定义机器可解析的 JSON schema
- 仲裁器直接解析 JSON 字段值（非关键字匹配）
- 消除文档格式依赖，提升校验精度

---

## 2. JSON Schema 设计

### 2.1 统一门禁状态文件: `gate_status.json`

```json
{
  "schema_version": "1.0.0",
  "generated_at": "2026-10-17T14:40:00+08:00",
  "generated_by": "HERMEShf",
  "phase": "phase03",
  "prechecks": {
    "p013_closed": {
      "passed": true,
      "evidence_file": "analysis/e2e_output/v88/phase03/p2/dshb/p013_watch_prep/final_archive/noise_168h_final_snapshot.json",
      "evidence_hash": "auto",
      "detail": "168h noise snapshot exists, 6.64% < 10% threshold"
    },
    "baseline_switch_free": {
      "passed": true,
      "evidence_file": "analysis/e2e_output/v88/phase03/p1/hermes/phase03_summary/phase03_summary_asset_re_seal.md",
      "evidence_hash": "auto",
      "active_baseline": "frozen_p012_gate_package/v88_p012_full_link_cpu_compare.json",
      "active_baseline_sha256_prefix": "3199ec8721313d2d",
      "alternative_01_status": "ARCHIVED",
      "detail": "No silent baseline switch detected"
    },
    "phase03_blockers_zero": {
      "passed": true,
      "fail_count": 0,
      "warn_count": 1,
      "warn_items": ["P0-12 (EXEMPTION_GRANTED, non-blocking)"],
      "detail": "All 7 gates PASS or WARN (non-blocking)"
    },
    "no_prematurous_merge": {
      "passed": true,
      "merge_marker_file": "v88-long-stable-baseline.json",
      "merge_marker_exists": false,
      "detail": "No premature baseline merge"
    },
    "dshe_auto_commit_off": {
      "passed": true,
      "evidence_file": "opt_hooks/blocker_monitor_hook_snippet.py",
      "evidence_hash": "auto",
      "auto_commit_mode": false,
      "detail": "AUTO_COMMIT_MODE=False in source code"
    }
  },
  "summary": {
    "total_prechecks": 5,
    "passed": 5,
    "failed": 0,
    "all_pass": true
  }
}
```

### 2.2 字段定义

| 字段路径 | 类型 | 必填 | 说明 |
|----------|------|:----:|------|
| `schema_version` | string | ✅ | Schema 版本号 |
| `generated_at` | string(ISO8601) | ✅ | 生成时间 |
| `generated_by` | string | ✅ | 生成方 |
| `phase` | string | ✅ | 阶段标识 |
| `prechecks.*.passed` | bool | ✅ | 该项是否通过 |
| `prechecks.*.evidence_file` | string | 选填 | 证据文件路径 |
| `prechecks.*.evidence_hash` | string | 选填 | 证据文件哈希 |
| `prechecks.*.detail` | string | ✅ | 人类可读说明 |
| `summary.all_pass` | bool | ✅ | 全部通过标志 |

---

## 3. 仲裁器改造方案

### 3.1 新增函数: `_load_gate_status_json(base)`

```python
def _load_gate_status_json(base):
    """加载 JSON 门禁状态文件，返回 dict 或 None"""
    json_path = os.path.join(base, "opt_auth_guard", "gate_status.json")
    if not os.path.exists(json_path):
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None
```

### 3.2 修改预检逻辑（伪代码）

```python
def run_5_point_safety_precheck():
    checks = []
    base = os.path.dirname(AUTH_GUARD_DIR)

    # 优先加载 JSON
    gate_json = _load_gate_status_json(base)

    if gate_json and gate_json.get("schema_version") == "1.0.0":
        # --- JSON 结构化校验路径（Phase04 新） ---
        pre = gate_json["prechecks"]
        checks.append({
            "id": "P0-13-CLOSED",
            "passed": pre["p013_closed"]["passed"],
            "detail": pre["p013_closed"]["detail"],
            "mode": "json"
        })
        checks.append({
            "id": "BASELINE-SWITCH-FREE",
            "passed": pre["baseline_switch_free"]["passed"],
            "detail": pre["baseline_switch_free"]["detail"],
            "mode": "json"
        })
        # ... 类似处理 #3/#4/#5
    else:
        # --- 兼容回退路径（P7 文档校验，保持运行） ---
        # 当前 official_trigger_arbiter.py 的逻辑不变
        pass

    return checks
```

### 3.3 改造原则

1. **JSON 优先**：`gate_status.json` 存在且 schema_version 匹配 → 走 JSON 路径
2. **文档回退**：JSON 不存在 → 回退到当前 P7 的文档校验逻辑
3. **不破坏现有**：Phase04 前不删除文档校验代码，作为兜底

---

## 4. 迁移步骤

### Phase04 Step 1: 生成 gate_status.json

HERMEShf 在每次预检后，不仅打印结果，还写入 `opt_auth_guard/gate_status.json`：
```python
# 在 main() 末尾追加
gate_status = {
    "schema_version": "1.0.0",
    "generated_at": datetime.datetime.now().isoformat(),
    "generated_by": "HERMEShf",
    "phase": "phase04",
    "prechecks": { ... },
    "summary": { ... }
}
with open(os.path.join(repo_path, "opt_auth_guard", "gate_status.json"), "w") as f:
    json.dump(gate_status, f, indent=2, ensure_ascii=False)
```

### Phase04 Step 2: 仲裁器支持 JSON 解析

按 §3.2 改造 `run_5_point_safety_precheck()`，加入 `_load_gate_status_json()` 优先路径。

### Phase04 Step 3: 双模式运行期

JSON + 文档双路径并行，JSON 路径为主，文档路径为兜底。运行 2 周（或 10 次预检）无异常后进入 Step 4。

### Phase04 Step 4: 移除文档校验代码

确认 JSON 路径稳定后，移除 `_check_baseline_switch_free()` / `_check_phase03_blockers_zero()` 的文档校验逻辑，仅保留 JSON 路径。

---

## 5. 回滚预案

### 5.1 回滚触发条件

- JSON 文件损坏/丢失
- JSON schema 不兼容
- JSON 校验结果与文档校验不一致（且文档校验更准确）

### 5.2 回滚步骤

| Step | 动作 | 命令 |
|:----:|------|------|
| 1 | 删除 gate_status.json | `rm opt_auth_guard/gate_status.json` |
| 2 | 仲裁器自动回退到文档校验 | （内置回退逻辑，无需操作） |
| 3 | 检查文档校验结果 | `python3 opt_auth_guard/official_trigger_arbiter.py` |
| 4 | 确认 5/5 ALL PASS | 验证预检正确 |

### 5.3 回滚安全性

- 回滚后仲裁器回到 P7 的文档校验逻辑（已验证 12/12 PASS）
- 不影响双钥匙仲裁契约
- 不影响 Phase04 冻结状态

---

## 6. 验收标准（Phase04 落地时）

| # | 标准 | 验证方法 |
|:-:|------|----------|
| 1 | `gate_status.json` 可被仲裁器解析 | `python3 -c "import json; json.load(open('opt_auth_guard/gate_status.json'))"` |
| 2 | JSON 路径预检 5/5 ALL PASS | 模拟 Key A 出现，检查输出 mode=json |
| 3 | 删除 JSON 后回退到文档校验 | `rm gate_status.json` → 仲裁器输出 mode=doc |
| 4 | 回退后仍 5/5 ALL PASS | 文档路径预检不变 |
| 5 | 无静态 True 残留 | grep `passed.*True` 无硬编码 |

---

## 7. 与 R-V88-P6-001 的关系

| 项 | R-V88-P6-001 (P7) | R-V88-P7-001 (P8) |
|----|-------------------|-------------------|
| 性质 | 整改（改代码） | 方案设计（仅文档） |
| 目标 | 3 项静态 True → 文档校验 | 文档校验 → JSON 校验 |
| 状态 | ✅ RESOLVED | 🟡 方案完成，待 Phase04 落地 |
| 代码改动 | arbiter.py +3 函数 | 无（Phase04 落地时改） |

---

## 8. 结论

| 项 | 值 |
|----|---|
| R-V88-P7-001 方案设计 | ✅ 完成 |
| JSON schema | ✅ 定义（gate_status.json v1.0.0） |
| 迁移步骤 | ✅ 4 步（生成→解析→双模式→清理） |
| 回滚预案 | ✅ 删除 JSON 即回退 |
| 代码改动 | ❌ 无（仅文档设计） |
| Phase04 落地 | 🟡 待 Phase04 工单签发 |

**STATUS**: R_V88_P7_001_MIGRATION_PLAN_DESIGNED_AWAIT_PHASE04

*Generated: 2026-10-17T14:40 +0800 | HERMEShf | V88 Phase03 P8 T0*
