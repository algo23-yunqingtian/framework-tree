# V86 双任务（规则 + 别名）门户扩展页面

> 工单: `HERMES_V86_PORTAL_DEFECT_FIX_AND_FULL_E2E_INTEGRATION_TEST` · T2.2
> 生成时间: 2026-10-02 10:15
> 分支: `feature/v85-chart-template`
> 对接: DSHB `v86_rule_task_adapter.md` + DSHE `alias_task_adapter.py`（commit `168a073`）

---

## 1. 面板布局

```
┌────────────────────────────────────────────────────────────────────────┐
│ 🚀 V86 异步任务面板                       [⟳ 刷新] [⤓ 导出 JSON]          │
├────────────────────────────────────────────────────────────────────────┤
│ 任务类型:  (●) 🧪 DSHB 规则任务    ( ) 🔤 DSHE 别名任务                  │
│ 版本: v86.0-alpha    优先级: [5 ▾]    幂等键: auto                       │
├────────────────────────────────────────────────────────────────────────┤
│ ┌─ DSHB 规则任务 ─────────────────────────────────────────────────────┐ │
│ │ 规则集: [v86-p0-prototype(4规则) ▾]                                  │ │
│ │ 场景: [A ▾]    用例集: [v86-rule-test-suite-v1(48) ▾]                │ │
│ │ Payload: { "blacklist_version": "v86-p0-prototype",                  │ │
│ │            "case_set": "v86-rule-test-suite-v1", "scenario": "A" }   │ │
│ │ [▶ 提交规则任务]                                                      │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│ ┌─ DSHE 别名任务 ─────────────────────────────────────────────────────┐ │
│ │ 引擎变体: [F3+F4 ▾]    输入: [手动输入 ▾]                            │ │
│ │ 别名列表 (每行一个):                                                 │ │
│ │ ┌──────────────────────────────────────────────────────────────────┐│ │
│ │ │ COMEX:铜:主力合约:收盘价(日                                        ││ │
│ │ │ 沪铜主力收盘价                                                     ││ │
│ │ │ 碳酸锂 三元523需求                                                ││ │
│ │ └──────────────────────────────────────────────────────────────────┘│ │
│ │ [▶ 提交别名任务]                                                      │ │
│ └────────────────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────┤
│ ┌─ 任务列表 ──────────────────────────────────────────────────────────┐ │
│ │ task_id          类型        状态     进度    提交时间   操作        │ │
│ │ TASK-DH-...00001 dshb_rule   running  42.5%  10-02 10:15 [取消]      │ │
│ │ TASK-DH-...00002 dshe_alias  queued   0.0%   10-02 10:16 [取消]      │ │
│ └────────────────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────┤
│ ┌─ 结果面板（双栏并排）────────────────────────────────────────────────┐ │
│ │ 🧪 规则风险标签              │ 🔤 别名解析详情                      │ │
│ │ ┌──────────────────────────┐ │ ┌──────────────────────────────────┐│ │
│ │ │ risk_id  level rule  状态│ │ │ alias           canonical  conf  ││ │
│ │ │ RISK-002 P0   BL009a BLK │ │ │ COMEX:铜:主力…  cu_23_comex 0.92 ││ │
│ │ │ RISK-001 P0   BL005 BLK  │ │ │ 沪铜主力收盘价 cu_23_comex 0.95 ││ │
│ │ │ RISK-003 P0   BL003 BLK  │ │ │ 碳酸锂三元523… li_523_demand 0.88││ │
│ │ │ ...                      │ │ │ ...                              ││ │
│ │ └──────────────────────────┘ │ └──────────────────────────────────┘│ │
│ │ P0 拦截率: 75.0% TP:40 FP:0 │ 解析率: 100% 未解析: 0               │ │
│ └──────────────────────────────┴──────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. DSHB 规则任务面板

### 2.1 任务类型

| 项 | 值 |
|---|---|
| `task_type` | `dshb_rule_eval` |
| 对接适配器 | DSHB `v86_rule_task_adapter.md`（commit `128275a`） |
| 规则集选项 | `v86-p0-prototype`（4 规则）/ `v86-p1-prototype`（12 规则 BL-027~BL-038）/ `v86-full`（待实现） |
| 用例集 | `v86-rule-test-suite-v1`（48 用例，DSHB 交付） |

### 2.2 提交表单

```json
{
  "task_type": "dshb_rule_eval",
  "version_tag": "v86.0-alpha",
  "priority": 5,
  "payload": {
    "blacklist_version": "v86-p0-prototype",
    "case_set": "v86-rule-test-suite-v1",
    "scenario": "A",
    "compare_baseline": {
      "kind": "scenario_replay",
      "version": "f313570",
      "md5": "2c85f4025baf09ec55b47709cdc2168d"
    }
  }
}
```

### 2.3 结果回显

| 字段 | 说明 |
|---|---|
| `result.rows[]` | 每条 case 的 `risk_id` / `risk_level` / `v86_status` / `v86_rule` / `expected_result` |
| `result.summary` | `total / blocked / tp / fp / p0_interception_rate` |
| `result.changed_cases[]` | 与 V85 基线的差异列表 |
| 可视化 | 风险标签表（左侧红/绿/黄三色标记） |

---

## 3. DSHE 别名任务面板

### 3.1 任务类型

| 项 | 值 |
|---|---|
| `task_type` | `dshe_alias_resolve` |
| 对接适配器 | DSHE `alias_task_adapter.py`（commit `168a073`） |
| 引擎变体 | `F1` / `F2` / `F3` / `F4` / `F3+F4`（推荐） |
| 输入方式 | 手动输入 / 批量粘贴 / 文件上传（≤4MiB） |

### 3.2 提交表单

```json
{
  "task_type": "dshe_alias_resolve",
  "version_tag": "v86.0-alpha",
  "priority": 5,
  "payload": {
    "alias_names": [
      "COMEX:铜:主力合约:收盘价(日",
      "沪铜主力收盘价",
      "碳酸锂 三元523需求"
    ],
    "engine_variant": "f3+f4"
  }
}
```

### 3.3 结果回显

| 字段 | 说明 |
|---|---|
| `result.canonical[]` | `alias` / `canonical_key` / `confidence` |
| `result.unresolved[]` | 未解析的别名列表 |
| `result.summary` | `total / resolved / unresolved / resolution_rate` |
| 可视化 | 别名解析详情表（右侧，置信度条形图 + 颜色标记） |

### 3.4 DSHE 引擎实测数据

来源：DSHE `test_run_results.json` + `regression_results.json`（commit `168a073`）

| 指标 | 值 |
|---|---|
| 引擎 | `v86_alias_engine_prototype.py`（F1-F4 四层 Gate） |
| 165 样本 | 100% A→R diff（原文→规范化 100% 一致） |
| 扩展测试 | 37/40 PASS（92.5%） |
| 冒烟 | 17/17 PASS |
| 任务适配器 | 17/17 PASS |
| F3/F4 模式切换 | 支持 |
| 回归套件 | 41+200+893 三套 |

---

## 4. 双任务联合场景

### 4.1 联合工作流

```
1. 用户提交 dshe_alias_resolve → 解析一批别名
2. 解析结果 canonical_keys → 作为 dshb_rule_eval 的输入
3. 规则引擎对 canonical_keys 跑黑名单检查
4. 结果对比面板同时展示别名解析详情 + 规则风险标签
```

### 4.2 联合提交示例

```python
# 步骤 1：别名解析
alias_task = task_client.submit(
    task_type="dshe_alias_resolve",
    version_tag="v86.0-alpha",
    payload={"alias_names": [...], "engine_variant": "f3+f4"}
)
# 轮询 → succeeded
alias_result = task_client.get_result(alias_task["task_id"])
canonical_keys = [r["canonical_key"] for r in alias_result["result"]["canonical"]]

# 步骤 2：规则检查（引用步骤 1 结果）
rule_task = task_client.submit(
    task_type="dshb_rule_eval",
    version_tag="v86.0-alpha",
    payload={
        "blacklist_version": "v86-p0-prototype",
        "canonical_keys": canonical_keys,    # 联合！
        "compare_baseline": {"kind": "scenario_replay", "version": "f313570"}
    }
)
# 轮询 → succeeded
rule_result = task_client.get_result(rule_task["task_id"])
```

### 4.3 联合结果展示

```
┌─ 联合结果 ────────────────────────────────────────────────────────────┐
│ 别名 → 规范键 → 规则检查 三联表                                       │
│ ┌──────────────────────┬──────────────────┬─────────┬───────────────┐ │
│ │ alias                │ canonical_key    │ 规则状态│ 命中规则       │ │
│ │ COMEX:铜:主力合约…  │ cu_23_comex_close│ PASSED  │ —             │ │
│ │ 碳酸锂 三元523需求  │ li_523_demand    │ BLOCKED │ BL-009a       │ │
│ │ 沪铜主力收盘价       │ cu_23_comex_close│ PASSED  │ —             │ │
│ └──────────────────────┴──────────────────┴─────────┴───────────────┘ │
│ 汇总: 解析 3/3 (100%) | 拦截 1/3 (33.3%) | TP 1 | FP 0              │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 5. 降级策略

| 后端状态 | 门户展示 |
|---------|---------|
| V86 任务 API 已实现 | 完整双任务面板 |
| 仅 V86 任务 API 契约（当前） | `⏳ 任务 API 未上线` + 表单可填写 → 写入 `task_queue/` 本地文件 |
| DSHB 适配器未实现 | 规则任务 Tab 灰色 + `⏳ DSHB 适配器未上线` |
| DSHE 适配器已交付（`alias_task_adapter.py`） | 别名任务 Tab 可用（离线模式：直接调用 Python 适配器） |

### 5.1 离线模式（当前可用）

DSHE `alias_task_adapter.py` + `v86_alias_engine_prototype.py` 已交付，可直接进程内调用：

```python
import sys
sys.path.insert(0, "analysis/e2e_output/v86/dshe_alias_predev")
from v86_alias_engine_prototype import AliasEngine

engine = AliasEngine(variant="f3+f4")
result = engine.resolve_batch(["COMEX:铜:主力合约:收盘价(日", "沪铜主力收盘价"])
# → [{"alias": "...", "canonical_key": "cu_23_comex_close", "confidence": 0.92}, ...]
```

DSHB `v86_p0_rule_prototype.py` + `v86_p1_rule_prototype.py` 同样可进程内调用，无需等待后端。
