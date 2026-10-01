# Gate 阻塞进度看板设计文档

> 工单: `HERMES_V85_HUMAN_REVIEW_TOOL_ENHANCE_AND_BATCH_DATA_PREP`
> 数据源: `gate_block_tracker.csv` + DSHB `dsh_gate_self_check.md`

---

## 1. 看板定义

Gate阻塞进度看板展示 V85 上线 Gate 的10项检查（5项DSHB侧+5项HERMES侧）的实时进度，帮助跟踪阻塞解除路径。

---

## 2. 字段定义

| 字段 | 类型 | 说明 |
|------|------|------|
| gate_id | string | Gate唯一标识 (G-01~G-05 / H1~H5) |
| gate_name | string | Gate名称 |
| current | string | 当前状态描述 |
| target | string | 目标值 |
| blocked_count | int | 阻塞条目数 |
| resolved_count | int | 已解除条目数 |
| progress | string | 进度百分比 |
| eta | string | 预估解除时间 |
| status | enum | PASS / PARTIAL / BLOCKED |
| dshb_status | enum | DSHB侧状态 (PASS/PARTIAL/N/A) |

---

## 3. 统计逻辑

### 3.1 进度计算

```
progress = resolved_count / (blocked_count + resolved_count) * 100%
```

### 3.2 状态判定

| 条件 | 状态 |
|------|------|
| blocked_count == 0 | PASS |
| resolved_count > 0 && blocked_count > 0 | PARTIAL |
| resolved_count == 0 && blocked_count > 0 | BLOCKED |

### 3.3 Gate通过判定

```
Gate全绿 = 所有10项 status == PASS
```

---

## 4. 看板布局

### 4.1 DSHB侧（5项）

```
┌─────────────────────────────────────────────────┐
│ DSHB Gate自检                                    │
├─────────────────────────────────────────────────┤
│ G-01 P0模板全部处置     [██░░░░░░░░] 3%  ⚠     │
│ G-02 风险库完整落地     [██████████] 100% ✅    │
│ G-03 风险库与回放对齐   [████████░░] 80%  ✅    │
│ G-04 黑名单规则完整     [█████████░] 97%  ✅    │
│ G-05 488模板全量回放    [██████████] 100% ✅    │
├─────────────────────────────────────────────────┤
│ DSHB总结: 4/5 PASS, 1 PARTIAL                   │
└─────────────────────────────────────────────────┘
```

### 4.2 HERMES侧（5项硬阻塞）

```
┌─────────────────────────────────────────────────┐
│ HERMES 硬阻塞                                    │
├─────────────────────────────────────────────────┤
│ H1 THS匹配率≥80%       [░░░░░░░░░░] 0%   ❌    │
│ H2 P0全部处置           [░░░░░░░░░░] 2%   ❌    │
│ H3 渲染就绪率≥50%      [██░░░░░░░░] 20%  ❌    │
│ H4 评审完成率≥90%      [░░░░░░░░░░] 0%   ❌    │
│ H5 DSHB风险库落地      [██████████] 100% ✅    │
├─────────────────────────────────────────────────┤
│ HERMES总结: 1/5 PASS, 4 BLOCKED                 │
│ 上线判定: ❌ 禁止上线                            │
└─────────────────────────────────────────────────┘
```

### 4.3 阻塞解除路径

```
H1 (THS匹配) ──┐
               ├── H3 (就绪率>50%) ──┐
H4 (人工评审) ──┘                     ├── Gate全绿 ── 上线
H2 (P0处置)    ── 人工Batch-C ───────┤
H5 (风险库)    ── ✅ 已解除 ──────────┘
G-01 (P0处置)  ── 依赖H2 ────────────┘
```

---

## 5. 数据源

| 数据源 | 文件 | 用途 |
|--------|------|------|
| Gate跟踪表 | `gate_block_tracker.csv` | 10项Gate进度 |
| DSHB自检 | `dshb_full_integrate/dsh_gate_self_check.md` | DSHB侧5项 |
| HERMES自检 | `v85_gate_rerun_check_result.md` | HERMES侧46项 |
| P0风险 | `v85_p0_risk_human_workbook.csv` | 34条P0风险 |
| 回放结果 | `dshb_full_integrate/full_488_template_playback_result.csv` | 2721条series回放 |

---

## 6. 更新频率

| 触发条件 | 更新动作 |
|---------|---------|
| 人工评审完成1条 | 更新H4进度 |
| THS回填1条 | 更新H1进度 |
| P0风险处置1条 | 更新H2/G-01进度 |
| Gate预校验 | 全量重算10项 |
