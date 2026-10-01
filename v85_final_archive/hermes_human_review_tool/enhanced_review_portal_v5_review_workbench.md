# V85 评审门户 v5 · 人工评审工作台增强版

> 工单: `HERMES_V85_HUMAN_REVIEW_TOOL_ENHANCE_AND_BATCH_DATA_PREP`
> 生成时间: 2026-10-01
> 分支: `feature/v85-chart-template` @ `d324c76`
> 状态: 测试环境评审材料，未上线
> 增强内容: 在门户v5基础上新增人工评审工作台模块，联动DSHB风险处置工作表

> 上一版: `enhanced_review_portal_v5_full.md`

---

## 12. 人工评审工作台（v5增强新增）

### 12.1 工作台概览

工作台是人工评审的核心操作面板，集成以下功能：
- 按RISK-ID筛选P0阻塞风险
- 批量勾选处置结论（修复/白名单/观察）
- 填写评审备注
- 查看关联回放结果
- 快速跳转对应模板series

### 12.2 P0风险工作表

联动 `v85_p0_risk_human_workbook.csv`（34条P0风险）：

| RISK-ID | 模板 | 品种 | 错误指标 | 错误匹配 | 黑名单 | 冲突类型 | 结果 | Gate阻塞 | 人工处置 |
|---------|------|------|---------|---------|--------|---------|------|---------|---------|
| RISK-001 | TPL-AL-013 | AL | LME主要仓库场内库存 | LME：非仓单库存：欧洲 | BL-005 | 口径冲突 | BLOCKED | YES | (待填) |
| RISK-002 | TPL-LC-054 | LC | 碳酸锂 三元523需求 | SMM: 碳酸锂现金生产利润 | BL-009 | 口径冲突 | NOT_BLOCKED | NO | (待填) |
| RISK-003 | TPL-LC-084 | LC | 其他电池(磷酸铁锂) 销量 | SMM: 境内其他电池产量 | BL-003 | 口径冲突 | BLOCKED | YES | (待填) |
| RISK-005 | TPL-LC-087 | LC | 磷酸铁锂 电池 国内销量 | (空) | BL-015 | 无匹配 | CONDITIONAL | NO | (白名单) |
| RISK-006 | TPL-LC-091 | LC | 新能源乘用车 产量 | SMM: 国产乘用车销量-新能源汽车 | BL-002 | 口径冲突 | BLOCKED | YES | (待填) |
| RISK-010 | TPL-NI-008 | NI | 中国电解镍净进口量 | (空) | BL-022 | 跨品种 | NOT_BLOCKED | NO | (待填) |
| RISK-011 | TPL-SI-014 | SI | 工业硅样本工厂库存(SMM) | (空) | BL-020 | 跨品种 | NOT_BLOCKED | NO | (待填) |
| RISK-013 | TPL-SI-019 | SI | 工业硅供需平衡 | (空) | BL-021 | 跨品种 | NOT_BLOCKED | NO | (待填) |
| RISK-014 | THS-NI-2.3 | NI | COMEX镍持仓量（手） | COMEX：铜：主力合约：持仓量 | BL-022 | 跨品种 | ALREADY_BLOCKED | YES | (待填) |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

> 完整34条: `v85_p0_risk_human_workbook.csv`

### 12.3 风险统计

| 统计项 | 值 |
|--------|-----|
| P0风险总数 | 34条 |
| ALREADY_BLOCKED | 8条（旧规则已拦截） |
| NEW_BLOCKED | 22条（新规则拦截） |
| NOT_BLOCKED | 4条（未拦截，需分析） |
| CONDITIONAL_PASS | 1条（RISK-005白名单放行） |
| Gate阻塞 | 30/34 (88%) |

### 12.4 按品种分布

| 品种 | P0风险数 | 已阻塞 | 未阻塞 |
|------|---------|--------|--------|
| NI | 10 | 8 | 2 |
| LC | 7 | 4 | 3 |
| SI | 5 | 3 | 2 |
| AL | 3 | 2 | 1 |
| SN | 3 | 3 | 0 |
| AO | 3 | 5 | 0 |
| ZN | 2 | 2 | 0 |
| CU | 1 | 1 | 0 |

### 12.5 批量处置操作

#### 操作流程

```
1. 筛选: 按RISK-ID / 品种 / Gate阻塞状态 筛选P0风险
2. 勾选: 批量勾选处置结论（修复/白名单/观察）
3. 备注: 填写评审备注（处置理由）
4. 跳转: 点击模板ID跳转对应series详情
5. 回放: 查看DSHB 488模板回放结果
6. 提交: 导出处置结果，回写manifest
```

#### 操作命令

```bash
# 筛选P0阻塞风险
python3 batch_export_import_v2.py --filter-risk blocked --out p0_blocked.csv

# 按品种筛选
python3 batch_export_import_v2.py --filter-risk variety=NI --out ni_p0.csv

# 批量导入处置结果
python3 batch_export_import_v2.py --import disposal_filled.csv --apply

# 回写manifest
python3 batch_export_import_v2.py --apply --manifest ths_render_task_manifest_fixed.json
```

### 12.6 关联回放结果

每条P0风险可查看DSHB 488模板回放结果（2721条series）：

| 字段 | 说明 |
|------|------|
| template_id | 模板ID |
| series_name | series名称 |
| matched_name | zhiji匹配名 |
| verify_status | 校验状态 |
| old_bl_hits | 旧黑名单命中 |
| new_bl_hits | 新黑名单命中 |

```bash
# 查看模板回放结果
python3 -c "
import csv
with open('dshb_full_integrate/full_488_template_playback_result.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        if row['template_id'] == 'TPL-LC-091':
            print(row['series_name'], '→', row['matched_name'], '|', row['new_bl_hits'])
"
```

### 12.7 快速跳转

| 操作 | 命令 |
|------|------|
| 跳转模板series | `grep "TPL-LC-091" review_batches_v6/batch_C_review_v6.csv` |
| 查看风险详情 | `grep "RISK-006" v85_p0_risk_human_workbook.csv` |
| 查看别名推荐 | `grep "新能源乘用车" indicator_alias_library.csv` |
| 查看混淆对 | `grep "TPL-LC-091" high_risk_confusion_pairs.csv` |
| 查看回放 | `grep "TPL-LC-091" dshb_full_integrate/full_488_template_playback_result.csv` |

---

## 13. Gate阻塞进度看板（v5增强新增）

### 13.1 DSHB侧Gate自检（5项）

| Gate ID | 名称 | DSHB状态 | 阻塞项 | 结论 |
|---------|------|---------|--------|------|
| G-01 | P0模板全部处置 | ⚠ PARTIAL | 33条BLOCKED | 依赖HERMES落地 |
| G-02 | 风险库完整落地 | ✅ PASS | 无 | 已就绪 |
| G-03 | 风险库与回放对齐 | ✅ PASS | 5条需人工分析 | 80%命中 |
| G-04 | 黑名单规则完整 | ✅ PASS | BL-026待确认 | 已就绪 |
| G-05 | 488模板回放完成 | ✅ PASS | 无 | 已就绪 |

### 13.2 HERMES侧硬阻塞（5项）

| Gate ID | 名称 | 当前 | 目标 | 进度 | 预估 |
|---------|------|------|------|------|------|
| H1 | THS匹配率≥80% | 0% | ≥80% | 0% | 待人工回写 |
| H2 | P0全部处置 | 232阻塞 | 全部处置 | 2% | 待Batch-C |
| H3 | 渲染就绪率≥50% | 19.9% | ≥50% | 20% | 依赖H1+H4 |
| H4 | 评审完成率≥90% | 0% | ≥90% | 0% | 3-5天 |
| H5 | DSHB风险库落地 | 已提交 | 最终版 | 100% | ✅ 已完成 |

> **H5 已解除！** DSHB `6fded66` 已提交最终风险库（41条独立+31规则）。

### 13.3 进度可视化

```
DSHB Gate:
G-01 P0处置    [██░░░░░░░░] 3%  ⚠ PARTIAL
G-02 风险库    [██████████] 100% ✅ PASS
G-03 回放对齐  [████████░░] 80%  ✅ PASS
G-04 黑名单    [█████████░] 97%  ✅ PASS
G-05 全量回放  [██████████] 100% ✅ PASS

HERMES Gate:
H1 THS匹配    [░░░░░░░░░░] 0%   ❌ BLOCKED
H2 P0处置     [░░░░░░░░░░] 2%   ❌ BLOCKED
H3 就绪率     [██░░░░░░░░] 20%  ❌ BLOCKED
H4 评审完成   [░░░░░░░░░░] 0%   ❌ BLOCKED
H5 风险库     [██████████] 100% ✅ PASS
```

### 13.4 Gate阻塞解除路径

```
H1 (THS匹配) ──┐
               ├── H3 (就绪率>50%) ──┐
H4 (人工评审) ──┘                     ├── Gate全绿 ── 上线
H2 (P0处置)    ── 人工Batch-C ───────┘
H5 (风险库)    ── ✅ 已解除 ──────────┘
G-01 (P0处置)  ── 依赖H2 ────────────┘
```
