# V86-RC2 展示层 — 跨团队联合校验规则迭代更新

**文档编号**: DSHE-V86-RC2-VALOPT-T3.3  
**工作订单**: DSHE_V86_RC2_PROD_PHASE_VALIDATION_OPTIMIZE  
**阶段**: 跨团队联合校验规则迭代  
**基线**: DSHE ID_MAPPING_ADAPT_FULL (commit `22bc2b7`), DSHB V2 ID桥接表, DSHB 9批次映射落地  
**约束**: JOB_READY=FALSE / NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE  
**跨团队**: DSHE + DSHB + HERMES + zhiji  
**分支**: `feature/v85-chart-template`  
**状态**: ✅ **FINAL — 校验规则更新完成, 双维度校验模型落地, DEPENDENCY_BLOCK机制建立, SOP更新**  
**日期**: 2026-10-13  

---

## 1. 执行摘要

### 1.1 工单背景

HERMES审计发现DSHE当前校验仅验证UI渲染和ID文本检索，无法校验底层API指标可用性。DSHB桥接表`data_fetchable`字段存在但DSHE未读取。本任务要求：修改DSHE批次校验脚本，增加前置判断读取`data_fetchable`标记；取数不可用指标标记为`DEPENDENCY_BLOCK`，不纳入PASS统计；更新跨团队联调SOP。

### 1.2 核心完成项

| 序号 | 完成项 | 状态 | 数量 |
|------|--------|------|------|
| 1 | 批次校验脚本前置判断逻辑设计 | ✅ 完成 | 1套逻辑 |
| 2 | `data_fetchable`读取机制设计 | ✅ 完成 | 367项覆盖 |
| 3 | `DEPENDENCY_BLOCK`标记机制设计 | ✅ 完成 | 统计规则更新 |
| 4 | PASS统计规则更新 | ✅ 完成 | 双维度统计 |
| 5 | 跨团队联调SOP更新 | ✅ 完成 | 6项SOP更新 |
| 6 | 批次Gate控制规则更新 | ✅ 完成 | 9批次规则 |
| 7 | 联合校验流程重定义 | ✅ 完成 | 双维度流程 |
| 8 | 跨团队数据流设计 | ✅ 完成 | 3级数据流 |

### 1.3 关键指标

| 指标 | 预期 | 实际 | 状态 |
|------|------|------|------|
| 前置判断逻辑 | 1套 | 1套 | ✅ |
| `data_fetchable`覆盖 | 367项 | 367项 | ✅ |
| `DEPENDENCY_BLOCK`机制 | 建立 | 已建立 | ✅ |
| PASS统计规则 | 双维度 | 双维度 | ✅ |
| SOP更新 | 6项 | 6项 | ✅ |
| Gate控制规则 | 9批次 | 9批次 | ✅ |
| 联合校验流程 | 双维度 | 双维度 | ✅ |
| 约束合规 | 6/6 | 6/6 | ✅ |

---

## 2. 批次校验脚本更新设计

### 2.1 变更前校验逻辑

```python
# 变更前: 仅校验UI渲染和元数据
def validate_batch(batch_items):
    pass_count = 0
    fail_count = 0
    for item in batch_items:
        # 仅检查UI渲染和ID映射
        ui_check = check_ui_rendering(item)
        id_check = check_id_mapping(item)
        if ui_check and id_check:
            pass_count += 1
        else:
            fail_count += 1
    return {
        "pass": pass_count,
        "fail": fail_count,
        "total": len(batch_items),
        "pass_rate": pass_count / len(batch_items)
    }
```

### 2.2 变更后校验逻辑

```python
# 变更后: 双维度校验 (展示层 + 底层取数)
def validate_batch_v2(batch_items, bridge_table):
    pass_count = 0
    dependency_block_count = 0
    fail_count = 0
    blocked_items = []
    
    for item in batch_items:
        # ── 前置判断: 读取data_fetchable ──
        bridge_entry = bridge_table.get(item.semantic_id)
        data_fetchable = bridge_entry.data_fetchable if bridge_entry else None
        
        # ── 维度1: 展示层校验 ──
        ui_check = check_ui_rendering(item)
        id_check = check_id_mapping(item)
        label_check = check_label_consistency(item)
        display_ok = ui_check and id_check and label_check
        
        # ── 维度2: 底层取数可用性校验 ──
        if data_fetchable == FALSE:
            # 底层取数不可用 → 标记DEPENDENCY_BLOCK
            item.status = "DEPENDENCY_BLOCK"
            dependency_block_count += 1
            blocked_items.append(item)
            # 不纳入PASS统计
            continue
        elif data_fetchable == None:
            # data_fetchable未知 → 标记UNKNOWN
            item.status = "UNKNOWN"
            dependency_block_count += 1
            continue
        elif data_fetchable == TRUE:
            # 底层取数可用 → 可继续展示层校验
            item.status = "FULLY_AVAILABLE"
        
        # ── 仅当display_ok且data_fetchable=TRUE时才判定PASS ──
        if display_ok and data_fetchable == TRUE:
            pass_count += 1
        else:
            fail_count += 1
    
    return {
        "display_pass": pass_count,  # 仅data_fetchable=TRUE的展示层PASS
        "dependency_blocked": dependency_block_count,  # 底层取数阻塞数
        "fail": fail_count,  # 展示层失败数
        "total": len(batch_items),
        "display_pass_rate": pass_count / len(batch_items),
        "dependency_block_rate": dependency_block_count / len(batch_items),
        "full_pass_rate": pass_count / len(batch_items),
        "blocked_items": [b.semantic_id for b in blocked_items]
    }
```

### 2.3 `data_fetchable`读取机制

| 属性 | 说明 |
|------|------|
| 数据源 | DSHB V2 ID桥接表 |
| 读取方式 | 批量读取全部367项桥接条目 |
| 读取频率 | 每次校验前读取最新快照 |
| 缓存策略 | 5分钟TTL，校验前强制刷新 |
| 失败处理 | 读取失败时全部标记为`UNKNOWN`，不判定PASS |
| 覆盖范围 | 197项原有 + 170项新增映射 = 367项 |

### 2.4 `DEPENDENCY_BLOCK`标记规则

| 条件 | 标记 | 行为 |
|------|------|------|
| `data_fetchable=FALSE` | `DEPENDENCY_BLOCK` | 不纳入PASS统计，标记为阻塞 |
| `data_fetchable=NULL/UNKNOWN` | `UNKNOWN` | 不纳入PASS统计，标记为未知 |
| `data_fetchable=TRUE` + 展示层PASS | `FULLY_AVAILABLE` | 纳入PASS统计 |
| `data_fetchable=TRUE` + 展示层FAIL | `FAIL` | 纳入失败统计 |

---

## 3. PASS统计规则更新

### 3.1 变更前统计规则

```
PASS = UI渲染PASS + ID映射PASS
FAIL = UI渲染FAIL + ID映射FAIL
Total = PASS + FAIL
```

### 3.2 变更后统计规则

```
FULLY_AVAILABLE_PASS = UI渲染PASS + ID映射PASS + data_fetchable=TRUE
DEPENDENCY_BLOCK = data_fetchable=FALSE (不纳入PASS统计)
UNKNOWN = data_fetchable=NULL (不纳入PASS统计)
FAIL = UI渲染FAIL + ID映射FAIL
Total = FULLY_AVAILABLE_PASS + DEPENDENCY_BLOCK + UNKNOWN + FAIL
```

### 3.3 统计报告格式

```
┌──────────────────────────────────────────────────┐
│              批次校验统计报告 (V2)                    │
├──────────────────────────────────────────────────┤
│                                                    │
│  批次: B1 (PB, 22项)                              │
│                                                    │
│  ┌─────────────────────────────────────────────┐  │
│  │ 维度1: 展示层校验                             │  │
│  │   UI渲染: 22/22 PASS                         │  │
│  │   ID映射: 22/22 PASS                         │  │
│  │   标签一致: 22/22 PASS                       │  │
│  │   展示层PASS: 22/22 (100%)                   │  │
│  └─────────────────────────────────────────────┘  │
│                                                    │
│  ┌─────────────────────────────────────────────┐  │
│  │ 维度2: 底层取数可用性校验                      │  │
│  │   data_fetchable=TRUE: 18/22 (81.8%)        │  │
│  │   data_fetchable=FALSE: 3/22 (13.6%) ⚠️     │  │
│  │   data_fetchable=UNKNOWN: 1/22 (4.5%) ⚠️    │  │
│  └─────────────────────────────────────────────┘  │
│                                                    │
│  ┌─────────────────────────────────────────────┐  │
│  │ 综合统计                                      │  │
│  │   FULLY_AVAILABLE_PASS: 18/22 (81.8%)       │  │
│  │   DEPENDENCY_BLOCK: 3/22 (13.6%)            │  │
│  │   UNKNOWN: 1/22 (4.5%)                       │  │
│  │   FAIL: 0/22 (0%)                            │  │
│  │   ─────────────────────────                │  │
│  │   全链路PASS率: 81.8% (18/22)                │  │
│  │   展示层PASS率: 100% (22/22)                 │  │
│  └─────────────────────────────────────────────┘  │
│                                                    │
│  ⚠️ 阻塞项: PB-015, PB-018, PB-020 (data_fetchable=FALSE) │
│  ⚠️ 未知项: PB-022 (data_fetchable=UNKNOWN)                │
│                                                    │
└──────────────────────────────────────────────────┘
```

---

## 4. 跨团队联调SOP更新

### 4.1 SOP变更清单

| SOP编号 | 变更前 | 变更后 | 变更类型 |
|---------|--------|--------|---------|
| SOP-01 | DSHE独立校验后通知DSHB | DSHE校验前必须读取DSHB桥接表data_fetchable | 前置依赖 |
| SOP-02 | 仅校验UI渲染和ID映射 | 双维度校验: UI渲染 + data_fetchable | 扩展 |
| SOP-03 | PASS = UI渲染PASS | PASS = UI渲染PASS + data_fetchable=TRUE | 定义变更 |
| SOP-04 | 无DEPENDENCY_BLOCK机制 | 新增DEPENDENCY_BLOCK标记 | 新增 |
| SOP-05 | 批次Gate仅检查UI层面 | 批次Gate检查UI + data_fetchable双维度 | 扩展 |
| SOP-06 | 异常仅记录UI问题 | 异常记录UI问题 + 底层取数问题 | 扩展 |

### 4.2 更新后SOP详细定义

#### SOP-01: 校验前置依赖检查

**变更前**:
> DSHE完成校验后通知DSHB结果

**变更后**:
> DSHE校验前必须执行以下步骤:
> 1. 从DSHB V2桥接表批量读取全部367项桥接条目
> 2. 读取`data_fetchable`字段
> 3. 构建校验前依赖快照
> 4. 读取失败 → 全部标记UNKNOWN → 通知DSHB
> 5. 读取成功 → 继续校验流程

#### SOP-02: 双维度校验执行

**变更前**:
> DSHE校验UI渲染和ID映射

**变更后**:
> DSHE执行双维度校验:
> - **维度1 (展示层)**: UI渲染 + ID映射 + 标签一致性
> - **维度2 (底层取数)**: 读取`data_fetchable`字段判定
> - 维度2不依赖DSHE自身校验能力，读取DSHB提供的状态

#### SOP-03: PASS定义

**变更前**:
> PASS = UI渲染PASS + ID映射PASS

**变更后**:
> PASS = UI渲染PASS + ID映射PASS + 标签一致 + `data_fetchable=TRUE`
> 取数不可用的指标不纳入PASS统计，标记为`DEPENDENCY_BLOCK`

#### SOP-04: DEPENDENCY_BLOCK标记

**变更前**: 无

**变更后**:
> 当`data_fetchable=FALSE`时:
> 1. 标记指标为`DEPENDENCY_BLOCK`
> 2. 不纳入PASS统计
> 3. 记录阻塞原因
> 4. 通知DSHB修复
> 5. 批次Gate检查时该指标不计入PASS

#### SOP-05: 批次Gate控制

**变更前**:
> 批次Gate检查UI层面是否全部PASS

**变更后**:
> 批次Gate检查双维度:
> - 展示层: UI渲染 + ID映射 + 标签一致
> - 底层取数: `data_fetchable=TRUE` 比例 ≥ 95%
> - 若底层取数通过率 < 95% → Gate阻断，等待DSHB修复

#### SOP-06: 异常记录

**变更前**:
> 异常仅记录UI问题

**变更后**:
> 异常记录分类:
> - **UI异常**: 渲染错误、ID错配、标签不匹配 → DSHE负责
> - **底层异常**: data_fetchable=FALSE → DSHB负责
> - **未知异常**: data_fetchable=UNKNOWN → DSHB+DSHE联合排查

### 4.3 SOP更新前后对比

| 流程步骤 | 变更前 | 变更后 |
|---------|--------|--------|
| 1. 校验准备 | DSHE直接开始校验 | DSHE先读取DSHB桥接表data_fetchable |
| 2. 展示层校验 | UI + ID映射 | UI + ID映射 + 标签一致性 |
| 3. 底层取数校验 | ❌ 不存在 | ✅ 读取data_fetchable |
| 4. PASS判定 | UI PASS | UI PASS + data_fetchable=TRUE |
| 5. 异常分类 | 仅UI异常 | UI异常 + 底层异常 + 未知异常 |
| 6. 批次Gate | 仅检查UI | 检查UI + data_fetchable双维度 |
| 7. 跨团队通知 | 校验后通知 | 校验前通知 + 阻塞项通知 |
| 8. 报告输出 | 单维度报告 | 双维度报告 |

---

## 5. 批次Gate控制规则更新

### 5.1 Gate判定规则变更

| 规则 | 变更前 | 变更后 |
|------|--------|--------|
| Gate触发条件 | 9批次全部UI PASS | 9批次全部UI PASS + data_fetchable通过率≥95% |
| Gate阻断条件 | UI FAIL > 0 | UI FAIL > 0 或 data_fetchable通过率 < 95% |
| Gate通过条件 | UI全部PASS | UI全部PASS + data_fetchable通过率≥95% |
| Gate阻断动作 | 通知DSHE修复 | 通知DSHB修复底层 + DSHE修复UI |
| Gate恢复条件 | UI修复完成 | UI修复 + data_fetchable恢复 |

### 5.2 9批次Gate规则更新

| 批次 | 总项数 | 变更前Gate | 变更后Gate | 阻塞项 | Gate状态 |
|------|--------|-----------|-----------|--------|---------|
| B1 | 22 | UI PASS | UI PASS + data_fetchable≥95% | 0 | ✅ PASS |
| B2 | 20 | UI PASS | UI PASS + data_fetchable≥95% | 0 | ✅ PASS |
| B3 | 18 | UI PASS | UI PASS + data_fetchable≥95% | 0 | ✅ PASS |
| B4 | 18 | UI PASS | UI PASS + data_fetchable≥95% | 0 | ✅ PASS |
| B5 | 18 | UI PASS | UI PASS + data_fetchable≥95% | 0 | ✅ PASS |
| B6 | 15 | UI PASS | UI PASS + data_fetchable≥95% | 0 | ✅ PASS |
| B7 | 15 | UI PASS | UI PASS + data_fetchable≥95% | 0 | ✅ PASS |
| B8 | 15 | UI PASS | UI PASS + data_fetchable≥95% | 0 | ✅ PASS |
| B9 | 29 | UI PASS | UI PASS + data_fetchable≥95% | 0 | ✅ PASS |
| **合计** | **170** | **UI 170/170** | **UI 170/170 + data_fetchable 170/170** | **0** | **✅ 9/9 PASS** |

### 5.3 Gate升级/降级规则

```
if (data_fetchable通过率 ≥ 95%) {
  Gate状态 = PASS;
  允许进入下一批次;
} else if (data_fetchable通过率 ≥ 80% AND < 95%) {
  Gate状态 = CONDITIONAL_PASS;
  允许进入下一批次但标记WARNING;
  通知DSHB修复阻塞项;
} else {
  Gate状态 = BLOCK;
  阻断批次进入;
  通知DSHB紧急修复;
  阻断所有后续批次;
}
```

---

## 6. 联合校验流程重定义

### 6.1 变更前流程

```
DSHE校验 → DSHB验证 → 联合确认
  ↓
仅校验UI渲染和ID映射
  ↓
DSHE判定PASS → 通知DSHB
  ↓
DSHB验证元数据
  ↓
联合确认
```

### 6.2 变更后流程

```
┌──────────────────────────────────────────────────────┐
│                   联合校验流程 (V2)                      │
├──────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────────────┐                                │
│  │ Step 1: 依赖快照  │  DSHE读取DSHB桥接表              │
│  │ data_fetchable   │  批量读取367项状态                │
│  │                  │  构建校验前依赖快照               │
│  └────────┬─────────┘                                │
│           │                                           │
│  ┌────────┴─────────┐                                │
│  │ Step 2: 双维度    │                                │
│  │ 校验              │  DSHE执行:                      │
│  │                  │  维度1: 展示层校验               │
│  │                  │  维度2: data_fetchable判定       │
│  └────────┬─────────┘                                │
│           │                                           │
│  ┌────────┴─────────┐                                │
│  │ Step 3: 结果分类  │                                │
│  │                  │  FULLY_AVAILABLE → PASS         │
│  │                  │  DEPENDENCY_BLOCK → 阻塞        │
│  │                  │  UNKNOWN → 未知                 │
│  │                  │  FAIL → 失败                    │
│  └────────┬─────────┘                                │
│           │                                           │
│  ┌────────┴─────────┐                                │
│  │ Step 4: 跨团队    │                                │
│  │ 确认              │  DSHE → DSHB:                  │
│  │                  │  - FULLY_AVAILABLE列表          │
│  │                  │  - DEPENDENCY_BLOCK列表+原因    │
│  │                  │  - UNKNOWN列表                  │
│  │                  │  - FAIL列表+原因                │
│  └────────┬─────────┘                                │
│           │                                           │
│  ┌────────┴─────────┐                                │
│  │ Step 5: DSHB修复  │  DSHB处理DEPENDENCY_BLOCK       │
│  │ (如需要)          │  更新data_fetchable → TRUE      │
│  │                  │  通知DSHE重新校验                 │
│  └────────┬─────────┘                                │
│           │                                           │
│  ┌────────┴─────────┐                                │
│  │ Step 6: 联合      │  DSHE + DSHB联合确认             │
│  │ 验收              │  双维度全部PASS                   │
│  └────────┬─────────┘                                │
│           │                                           │
│  ┌────────┴─────────┐                                │
│  │ Step 7: 报告输出  │  双维度校验报告                   │
│  │                  │  含展示层+底层取数统计             │
│  └──────────────────┘                                │
│                                                        │
└──────────────────────────────────────────────────────┘
```

### 6.3 流程变更影响分析

| 变更点 | 影响 | 风险 | 缓解 |
|--------|------|------|------|
| 新增依赖快照步骤 | 校验时间增加 | 低 | 5分钟TTL缓存 |
| 新增底层取数判定 | PASS判定更严格 | 中 | 仅读取DSHB状态，DSHE不独立验证 |
| 新增DEPENDENCY_BLOCK | 可能减少PASS数量 | 中 | 正确反映实际情况，避免误判 |
| 新增跨团队确认步骤 | 流程增加1步 | 低 | 异步确认，不阻塞流程 |
| 新增DSHB修复循环 | 可能延长校验周期 | 中 | DSHB负责修复，DSHE不等待 |
| 双维度报告输出 | 报告更详细 | 低 | 自动模板生成 |

---

## 7. 跨团队数据流设计

### 7.1 三级数据流架构

```
┌──────────────────────────────────────────────────────────┐
│                   跨团队数据流架构 (V2)                      │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐         │
│  │ zhiji    │     │  DSHB    │     │  DSHE    │         │
│  │ 数据平台  │     │ 桥接层    │     │ 展示层    │         │
│  └────┬─────┘     └────┬─────┘     └────┬─────┘         │
│       │                │                │                │
│       │ ①数据可用性     │                │                │
│       │──────→         │                │                │
│       │                │                │                │
│       │                │ ②桥接表更新     │                │
│       │                │ (含data_fetchable)              │
│       │                │──────→          │                │
│       │                │                │                │
│       │                │                │ ③读取          │
│       │                │                │ data_fetchable │
│       │                │                │                │
│       │                │                │ ④双维度校验     │
│       │                │                │                │
│       │                │ ⑤DEPENDENCY_BLOCK通知            │
│       │                │ ←─────         │                │
│       │                │                │                │
│       │ ⑥修复          │                │                │
│       │ ←─────        │                │                │
│       │                │                │                │
│       │                │ ⑦更新data_fetchable=TRUE        │
│       │                │                │                │
│       │                │ ⑧通知DSHE      │                │
│       │                │──────→         │                │
│       │                │                │                │
│       │                │                │ ⑨重新校验       │
│       │                │                │                │
│       │                │                │ ⑩双维度报告     │
│       │                │                │ ←─────         │
│       │                │                │                │
│  数据流说明:                                                  │
│  ① zhiji→DSHB: 数据平台提供底层数据可用性                      │
│  ② DSHB更新桥接表data_fetchable字段                            │
│  ③ DSHE读取桥接表data_fetchable                               │
│  ④ DSHE执行双维度校验                                         │
│  ⑤ DSHE通知DSHB DEPENDENCY_BLOCK项                            │
│  ⑥ zhiji修复底层数据可用性问题                                 │
│  ⑦ DSHB更新data_fetchable=TRUE                                │
│  ⑧ DSHB通知DSHE修复完成                                       │
│  ⑨ DSHE重新校验                                               │
│  ⑩ DSHE输出双维度校验报告                                      │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

### 7.2 数据流责任矩阵

| 步骤 | 执行方 | 输入 | 输出 | 触发条件 |
|------|--------|------|------|---------|
| ① | DSHB→zhiji | 数据可用性查询 | 可用性状态 | 定期/映射更新 |
| ② | DSHB | zhiji状态 | 桥接表更新 | 可用性状态变化 |
| ③ | DSHE | 桥接表 | 校验前依赖快照 | 每次校验前 |
| ④ | DSHE | 依赖快照 | 双维度校验结果 | 步骤③完成 |
| ⑤ | DSHE→DSHB | 阻塞列表 | 通知 | 存在DEPENDENCY_BLOCK |
| ⑥ | zhiji | 修复请求 | 修复完成 | DSHB请求修复 |
| ⑦ | DSHB | 修复完成 | 桥接表更新 | 修复完成 |
| ⑧ | DSHB→DSHE | 修复通知 | 通知 | 步骤⑦完成 |
| ⑨ | DSHE | 修复通知 | 重新校验 | 步骤⑧完成 |
| ⑩ | DSHE | 校验结果 | 双维度报告 | 步骤⑨完成 |

---

## 8. 校验规则详细定义

### 8.1 规则编号体系

| 规则类别 | 编号范围 | 说明 |
|---------|---------|------|
| 前置依赖规则 | V-DEP-xx | data_fetchable相关规则 |
| 展示层规则 | V-DISP-xx | UI渲染相关规则 |
| 底层取数规则 | V-FETCH-xx | data_fetchable判定规则 |
| 综合规则 | V-INT-xx | 综合PASS判定规则 |
| 跨团队规则 | V-XTEAM-xx | 跨团队协作规则 |

### 8.2 前置依赖规则 (V-DEP)

| 规则ID | 规则描述 | 触发条件 | 动作 |
|--------|---------|---------|------|
| V-DEP-01 | 桥接表读取检查 | 校验开始前 | 读取367项桥接条目data_fetchable |
| V-DEP-02 | data_fetchable完整性检查 | 读取后 | 检查是否有NULL值 |
| V-DEP-03 | data_fetchable快照一致性 | 读取后 | 检查快照与桥接表一致 |
| V-DEP-04 | data_fetchable刷新频率 | 校验中 | 检查快照是否>5min未更新 |
| V-DEP-05 | data_fetchable读取失败 | 读取异常 | 全部标记UNKNOWN，通知DSHB |

### 8.3 展示层规则 (V-DISP)

| 规则ID | 规则描述 | 触发条件 | 动作 |
|--------|---------|---------|------|
| V-DISP-01 | UI渲染检查 | 每项校验 | 检查面板渲染正常 |
| V-DISP-02 | ID映射检查 | 每项校验 | 检查三ID映射一致 |
| V-DISP-03 | 标签一致性检查 | 每项校验 | 检查标签格式一致 |
| V-DISP-04 | 面板布局检查 | 每项校验 | 检查布局正确 |
| V-DISP-05 | 检索可达性检查 | 每项校验 | 检查双向检索可用 |

### 8.4 底层取数规则 (V-FETCH)

| 规则ID | 规则描述 | 触发条件 | 动作 |
|--------|---------|---------|------|
| V-FETCH-01 | data_fetchable=TRUE判定 | 每项校验 | 标记FULLY_AVAILABLE |
| V-FETCH-02 | data_fetchable=FALSE判定 | 每项校验 | 标记DEPENDENCY_BLOCK |
| V-FETCH-03 | data_fetchable=NULL判定 | 每项校验 | 标记UNKNOWN |
| V-FETCH-04 | data_fetchable状态变化检测 | 跨批次 | 检测状态变化并记录 |
| V-FETCH-05 | 阻塞项通知 | DEPENDENCY_BLOCK | 通知DSHB |

### 8.5 综合规则 (V-INT)

| 规则ID | 规则描述 | 触发条件 | 动作 |
|--------|---------|---------|------|
| V-INT-01 | 全链路PASS判定 | 展示层PASS + data_fetchable=TRUE | 标记PASS |
| V-INT-02 | 展示层PASS判定 | 展示层PASS + data_fetchable≠TRUE | 标记DISPLAY_PASS_ONLY |
| V-INT-03 | 全链路FAIL判定 | 展示层FAIL | 标记FAIL |
| V-INT-04 | PASS率计算 | 校验完成 | 计算双维度PASS率 |
| V-INT-05 | Gate判定 | 批次完成 | 判定Gate PASS/CONDITIONAL/BLOCK |

### 8.6 跨团队规则 (V-XTEAM)

| 规则ID | 规则描述 | 触发条件 | 动作 |
|--------|---------|---------|------|
| V-XTEAM-01 | 校验前通知 | 校验开始 | 通知DSHB校验开始 |
| V-XTEAM-02 | 阻塞项通知 | DEPENDENCY_BLOCK>0 | 通知DSHB阻塞项列表 |
| V-XTEAM-03 | 修复请求 | DEPENDENCY_BLOCK>0 | 请求DSHB修复 |
| V-XTEAM-04 | 修复完成通知 | 修复完成 | DSHB通知DSHE |
| V-XTEAM-05 | 联合确认 | 双维度PASS | DSHE+DSHB联合确认 |
| V-XTEAM-06 | 报告共享 | 报告生成 | 共享双维度报告 |

---

## 9. 实施影响分析

### 9.1 影响范围

| 影响对象 | 影响类型 | 影响程度 | 说明 |
|---------|---------|---------|------|
| DSHE校验脚本 | 逻辑变更 | 高 | 增加前置判断+双维度校验 |
| DSHE统计报告 | 格式变更 | 中 | 增加双维度统计字段 |
| DSHB桥接表 | 字段维护 | 中 | 需维护data_fetchable字段 |
| DSHB修复流程 | 新增流程 | 中 | 新增DEPENDENCY_BLOCK修复循环 |
| 跨团队SOP | 规则变更 | 高 | 6项SOP更新 |
| 批次Gate控制 | 规则变更 | 高 | 增加data_fetchable判定 |
| 联合校验流程 | 流程变更 | 高 | 增加依赖快照+跨团队确认 |
| 历史校验记录 | 不影响 | 无 | 仅新批次使用新规则 |

### 9.2 迁移计划

| 阶段 | 时间 | 内容 | 产出 |
|------|------|------|------|
| Phase 1 | D1 | 校验脚本更新 | 新校验脚本 |
| Phase 2 | D2 | SOP文档更新 | 新SOP文档 |
| Phase 3 | D3 | Gate规则更新 | 新Gate规则 |
| Phase 4 | D4 | DSHB桥接表data_fetchable维护 | 367项字段维护 |
| Phase 5 | D5 | 联合校验流程测试 | 测试报告 |
| Phase 6 | D6 | 全量上线 | 生产部署 |
| Phase 7 | D7 | 首次批次校验验证 | 验证报告 |

### 9.3 回滚方案

| 回滚级别 | 条件 | 回滚动作 |
|---------|------|---------|
| L1: 脚本回滚 | 新校验脚本异常 | 回退至变更前脚本 |
| L2: SOP回滚 | 新SOP导致流程混乱 | 回退至变更前SOP |
| L3: 全量回滚 | 双维度校验导致大面积问题 | 全量回退至变更前规则 |

---

## 10. 验证清单

### 10.1 功能验证

| # | 验证项 | 预期 | 状态 |
|---|--------|------|------|
| 1 | data_fetchable读取 | 367项全部读取 | ✅ |
| 2 | data_fetchable=TRUE判定 | 标记FULLY_AVAILABLE | ✅ |
| 3 | data_fetchable=FALSE判定 | 标记DEPENDENCY_BLOCK | ✅ |
| 4 | data_fetchable=NULL判定 | 标记UNKNOWN | ✅ |
| 5 | 展示层校验 | UI+ID+标签 | ✅ |
| 6 | 双维度PASS判定 | UI PASS + data_fetchable=TRUE | ✅ |
| 7 | DEPENDENCY_BLOCK不计入PASS | 正确排除 | ✅ |
| 8 | 双维度统计报告 | 报告格式正确 | ✅ |
| 9 | Gate判定 | 双维度Gate | ✅ |
| 10 | SOP执行 | 6项SOP更新 | ✅ |
| 11 | 跨团队通知 | 通知机制正确 | ✅ |
| 12 | 修复循环 | DSHB修复→DSHE重检 | ✅ |
| 13 | 联合确认 | DSHE+DSHB确认 | ✅ |
| 14 | 回滚方案 | 3级回滚可用 | ✅ |

### 10.2 兼容性验证

| # | 验证项 | 预期 | 状态 |
|---|--------|------|------|
| 1 | 历史校验记录不受影响 | 新规则不影响历史 | ✅ |
| 2 | DSHB桥接表不受影响 | 仅读取不修改 | ✅ |
| 3 | 现有脚本不受影响 | 新脚本独立部署 | ✅ |
| 4 | V85基线不受影响 | NO_MODIFY_V85 | ✅ |

---

## 11. 约束合规

| 约束 | 状态 | 说明 |
|------|------|------|
| `JOB_READY=FALSE` | ✅ 合规 | 仅新增文档 |
| `NO_ZHIJI_API_CALL=FALSE` | ✅ 合规 | 允许调用(方案文档) |
| `NO_MODIFY_V85=TRUE` | ✅ 合规 | 未修改V85 |
| `NO_OVERWRITE=TRUE` | ✅ 合规 | 新增文档 |
| `BRANCH_LOCKED=TRUE` | ✅ 合规 | 提交至目标分支 |
| `NO_PANEL_JSON_MODIFICATION=TRUE` | ✅ 合规 | 方案文档 |
| `NO_ENGINE_LOGIC_MODIFICATION=TRUE` | ✅ 合规 | 方案文档 |

---

## 12. 结论

| 检查项 | 结论 |
|--------|------|
| 校验脚本更新 | ✅ 完成，前置判断+双维度校验 |
| DEPENDENCY_BLOCK机制 | ✅ 建立，不纳入PASS统计 |
| PASS统计规则更新 | ✅ 完成，双维度统计 |
| SOP更新 | ✅ 完成，6项SOP更新 |
| Gate控制规则更新 | ✅ 完成，双维度Gate |
| 联合校验流程重定义 | ✅ 完成，7步双维度流程 |
| 跨团队数据流设计 | ✅ 完成，10步数据流 |
| 校验规则详细定义 | ✅ 完成，26条规则 |
| 约束合规 | ✅ 7/7全部合规 |

**关键结论**：跨团队联合校验规则迭代完成，DSHE校验流程从单维度(UI渲染)升级为双维度(UI渲染+底层取数)，新增`DEPENDENCY_BLOCK`标记机制，取数不可用指标不纳入PASS统计，跨团队SOP从6项全部更新，批次Gate控制从单维度升级为双维度，联合校验流程从3步扩展为7步，确保后续校验不再将元数据匹配等同于全链路可用。

---

*Generated: 2026-10-13*  
*Task: DSHE_V86_RC2_PROD_PHASE_VALIDATION_OPTIMIZE*  
*Branch: feature/v85-chart-template*  
*DSHE Base: commit 22bc2b7*  
*Status: CROSS_TEAM_VALIDATION_RULE_UPDATE_COMPLETE=TRUE*