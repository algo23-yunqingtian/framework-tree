# V86 门户集成设计文档

> 工单: `HERMES_V86_PORTAL_INTEGRATE_AND_V85_FROZEN_DEMO_LOCK` · T2.3
> 生成时间: 2026-10-02 09:35
> 分支: `feature/v85-chart-template`
> 对接: E `v85_artifact_api.py`（9 端点）/ E `v86_task_api_design.md`（6 端点）
>       DSHB `v86_rule_task_adapter.md` + `v86_rule_test_suite.json`（48 用例）
>       DSHE `alias_task_adapter.py`（commit `168a073`）

---

## 1. 架构总览

```
┌──────────────────────────────────────────────────────────────────┐
│                    V85/V86 双版本评审门户                          │
├──────────────────────────────────────────────────────────────────┤
│  [🔒 V85.0 FROZEN]  [🧪 V86.0-alpha DEV]  ← 版本切换面板        │
├──────────────────────────┬───────────────────────────────────────┤
│  📊 指标大盘              │  📈 V85/V86 规则指标对比面板           │
│  🧪 测试样本面板          │  🚀 异步任务面板                      │
│  📄 制品目录              │  🔐 快照校验面板                      │
└────────────┬─────────────┴───────────────┬───────────────────────┘
             │                             │
             ▼                             ▼
   ┌────────────────────┐      ┌────────────────────────┐
   │ V85 只读 API       │      │ V86 任务 API            │
   │ GET only / 9 端点  │      │ GET+POST / 6 端点       │
   │ portal_read        │      │ task_submit/task_read   │
   │ 31 制品白名单      │      │ 6 task_type             │
   └────────┬───────────┘      └───────────┬────────────┘
            │                              │
            ▼                              ▼
   ┌──────────────────────────────────────────────┐
   │         V85 冻结快照 (da2a440)                │
   │   453 文件 / MD5 100% / tag v85-final-persist │
   └──────────────────────────────────────────────┘
```

**关键分离**（沿用 E 设计 §11）：V85 API 是"数据源"（只读）；V86 任务 API 是"计算层"（读 V85、写 V86）；V86 结果经只读 API 对外暴露（"输出层"）。

---

## 2. 版本切换面板

### 2.1 面板结构

```
┌──────────────────────────────────────────────────────────────┐
│ 版本:  ( ) V85.0 FROZEN    (●) V86.0-alpha DEV               │
│          readable ✅            readable ❌ (任务接口可用)    │
│                                                               │
│  对比模式:  [ ] 单栏  [✓] 双栏并排  [ ] 差异高亮             │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 版本元数据源

- V85：`GET /api/v1/versions` → `key=f313570, version_tag=v85.0, readable=true`
- V86：`GET /api/v1/versions?include_inactive=1` → `key=v86-dev, readable=false`

V86 制品**不在 V85 只读 API 白名单内**；门户通过 V86 任务接口提交 `dshb_rule_eval` 获取结果，结果写入 `analysis/e2e_output/v86/<task_id>/` 后注册到 V86 制品白名单，再经只读接口读取。

### 2.3 双栏并排渲染规则

| 项 | V85 栏 | V86 栏 |
|---|---|---|
| 数据来源 | 只读 API（`f313570`） | 任务 API 结果 |
| 刷新方式 | 页面加载即拉取 | 任务完成后轮询 `/result` |
| 版本标签 | 🔒 FROZEN | 🧪 DEV |
| 编辑能力 | 无 | 无（门户仍为只读消费方） |

---

## 3. 规则指标对比面板（T2.3.2）

### 3.1 指标定义与可视化

| 指标 | V85 | V86 | 可视化 |
|------|-----|-----|--------|
| P0 拦截率 | `p0_blocked / p0_total` | 同 | 双柱状图 + Δ 标注 |
| TP | 正确拦截数 | 同 | 横向条形图 |
| FP | 错误拦截数（目标 =0） | 同 | 数字卡片 + 红绿 |
| 回归差异 | — | `delta_blocked / delta_tp / delta_fp` | 瀑布图 |
| 边界通过率 | — | `boundary_pass / boundary_total` | 进度环 |

### 3.2 数据获取

```python
# V85 侧：只读 API 直接查询冻结回放结果
v85 = client.scenario_replay(filters={"scenario": "A"})
v85_stats = summarize_block_stats(v85["rows"])   # p0_rate / tp / fp

# V86 侧：提交任务 → 轮询 → 取结果
task = task_client.submit(
    task_type="dshb_rule_eval",
    version_tag="v86.0-alpha",
    priority=5,
    payload={
        "blacklist_version": "v86-p0-prototype",
        "case_set": "v86-rule-test-suite-v1",   # DSHB 48 用例
        "scenario": "A",
        "compare_baseline": {"kind": "scenario_replay",
                             "version": "f313570"}
    },
    idempotency_key=idem
)
for _ in range(60):                              # 最多 30 分钟
    st = task_client.get(task["task_id"])
    if st["status"] in ("succeeded", "failed", "cancelled", "timeout"):
        break
    time.sleep(st.get("poll_after_seconds", 30))
v86_result = task_client.get_result(task["task_id"])
v86_stats = summarize_block_stats(v86_result["result"]["rows"])
```

### 3.3 差异明细表

```
| risk_id   | risk_level | V85 状态  | V85 规则 | V86 状态  | V86 规则 | Δ TP | Δ FP |
|-----------|-----------|----------|---------|----------|---------|------|------|
| RISK-002  | P0        | BLOCKED  | BL-009a | BLOCKED  | BL-009a | 0    | 0    |
| …         |           |          |         |          |         |      |      |
```

排序：`REGRESSION` > `IMPROVEMENT` > `UNCHANGED`；分页 50 条/页。

---

## 4. 异步任务面板（T2.3.3）

### 4.1 任务类型映射

| 门户按钮 | task_type | 对接适配器 |
|---|---|---|
| 「🧪 规则回归」 | `dshb_rule_eval` | DSHB `v86_rule_task_adapter.md` |
| 「🔤 别名解析」 | `dshe_alias_resolve` | DSHE `alias_task_adapter.py` |
| 「🎯 规范键反查」 | `dshe_canonical_resolve` | DSHE `alias_task_adapter.py` |
| 「🛡️ Gate 全量回归」 | `gate_full_run` | DSHB + DSHE 联合 |
| «📦 迁移校验» | `migration_verify` | E `v85_to_v86_migration_verify_plan.md` |
| «🔁 场景回放» | `risk_db_replay` | DSHB |

### 4.2 任务生命周期 UI

```
[提交] ──> queued ──> running(进度环 % + progress_msg) ──> succeeded
                                                    └─> failed / cancelled / timeout
```

| 阶段 | 门户显示 |
|------|---------|
| 提交前 | 表单：task_type 下拉 + version_tag + priority(1-9) + payload JSON 编辑器 |
| `queued` | 队列序号 + 等待秒数 + 「取消」按钮 |
| `running` | 进度环 `progress` + `progress_msg` + `worker_id` |
| `succeeded` | 「加载结果」按钮 → `/result` → 注入对比面板 |
| `failed` | 红色错误块 + `error` + `retryable` + 「重试」（新 task_id） |
| `timeout` | 灰色 + 已耗时 + 「重试」 |

### 4.3 轮询策略

- 首轮立即拉取；此后按服务端 `poll_after_seconds` 拉取（默认 30s，临近完成缩短至 5s）
- 页面隐藏（`visibilitychange`）时暂停轮询，避免无谓请求
- 单任务轮询上限 60 次（约 30 分钟），超限提示人工查看
- 幂等：客户端计算 `X-Idempotency-Key = sha256(submitter|task_type|payload)[:32]`，重复提交返回原 `task_id`

### 4.4 结果回显

`succeeded` 后门户按 `result_format` 分流：

| result_format | 回显方式 |
|---|---|
| `json` | 注入对比面板 / 测试样本面板 |
| `csv` | 表格 + 前端分页（≤100 行/页） |
| `json_ref` | 仅显示 `result_ref` + 大小 + MD5，走只读接口拉取 |

---

## 5. V86 测试样本可视化面板（T2.4）

### 5.1 数据源

`v86_rule_test_suite.json`（DSHB 交付，`v86-rule-test-suite-v1`）：

| 组 | 规则 | 正向 | 负向 | 边界 | 小计 |
|---|---|---|---|---|---|
| BL-009a | 需求↔利润反向 | 4 | 4 | 4 | 12 |
| BL-026 | 库存口径 | 6 | 4 | 2 | 12 |
| BL-012_Plan_B | 方案 B | 4 | 2 | 2 | 8 |
| PDF_Fix | PDF 修复 | 4 | 4 | 4 | 12 |
| **合计** | | **18** | **14** | **12** | **48** |

### 5.2 面板结构

```
┌─────────────────────────────────────────────────────┐
│ 过滤: [规则 ▾ BL-009a/BL-026/BL-012B/PDF_Fix]      │
│       [类型 ▾ 正向/负向/边界]  [风险 ▾ P0/P1]       │
│ 搜索: [输入 case_id / indicator_name / matched_name]│
├─────────────────────────────────────────────────────┤
│ 用例列表（左侧，点击选中）   │  单条 case 预览（右侧）│
│  ☑ TC-BL009A-001 正向 P0    │  case_id: TC-BL009A-001│
│  ☑ TC-BL009A-002 正向 P0    │  类型: positive_trigger │
│  ⚠ TC-BL009A-NEG-001 负向   │  indicator_name:        │
│  ⚠ TC-BL009A-NEG-002 负向   │    碳酸锂 三元523需求   │
│  ▸ TC-BL009A-BND-001 边界   │  matched_name:          │
│  ▸ TC-BL009A-BND-002 边界   │    SMM:碳酸锂现金生产… │
│                            │  expected: BLOCKED      │
│                            │  expected_rule: BL-009a │
│                            │  source_risk: RISK-002  │
│                            │  ─────────────────      │
│                            │  [▶ 单条执行] [批量执行] │
└─────────────────────────────────────────────────────┘
```

### 5.3 用例类型视觉编码

| 类型 | 图标 | 颜色 | expected_result |
|------|------|------|----------------|
| 正向触发 `positive_trigger` | ☑ | 🔴 红 | `BLOCKED` |
| 安全负向 `negative_safety` | ⚠ | 🟢 绿 | `PASSED` |
| 边界 `boundary` | ▸ | 🟡 黄 | 视 case 而定 |

### 5.4 单条 case 执行

点击「▶ 单条执行」→ 构造最小任务：

```json
{
  "task_type": "dshb_rule_eval",
  "version_tag": "v86.0-alpha",
  "priority": 8,
  "payload": {
    "blacklist_version": "v86-p0-prototype",
    "case_set": "v86-rule-test-suite-v1",
    "single_case": "TC-BL009A-001",
    "compare_baseline": {"kind": "scenario_replay", "version": "f313570"}
  }
}
```

结果回显三态：

| 结果 | 显示 |
|------|------|
| `actual == expected` | ✅ PASS 绿 |
| `actual != expected` | ❌ FAIL 红 + 实际结果 + 命中规则 |
| 任务失败 | ⏸ 灰色 + 错误信息 |

### 5.5 批量执行

支持勾选多条（默认全选当前过滤结果）→ 单任务 `batch_cases: [case_id, ...]`；结果按 `actual/expected` 汇总为「通过 X / 失败 Y」+ 逐条展开。

---

## 6. 接口依赖与阻塞点

| 依赖 | 状态 | 门户影响 |
|------|------|---------|
| V85 只读 API（9 端点） | ✅ 已交付 `v85_artifact_api.py` | 冻结数据可拉取 |
| V86 任务 API（6 端点） | ⚠ 仅接口契约，无实现 | 任务面板降级为「仅设计预览」 |
| DSHB 规则任务适配器 | ✅ 已交付 `v86_rule_task_adapter.md` | 规则回归可对接 |
| DSHE 别名任务适配器 | ✅ 已交付 `alias_task_adapter.py` | 别名解析可对接 |
| V86 制品白名单 | ❌ 未建立 | V86 结果无法经只读 API 暴露 |
| `task_run` 表实现 | ❌ 仅 schema 设计 | 无 Worker 认领 |

**门户降级策略**：任务 API 未实现时，「🚀 异步任务面板」显示 `⏳ V86 任务 API 未上线（仅契约就绪）`，表单仍可填写并提交到本地队列文件（`task_queue/`），供后端实现后回放。
