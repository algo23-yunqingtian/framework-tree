# 人工评审一致性校验脚本使用文档

> 工单: `DSH-B_V85_HUMAN_REVIEW_SIMULATION_AND_PRECHECK`
> 生成时间: 2026-10-01 15:38:08
> 脚本: `review_consistency_check.py`

---

## 一、功能概述

`review_consistency_check.py` 是一个独立运行的校验脚本，用于检查人工填写完成的 P0 工作表的一致性。

**校验内容**:

| 校验项 | 描述 | 严重级别 |
|--------|------|---------|
| 白名单 vs 黑名单 | 白名单条目不应被黑名单规则拦截 | ⚠ WARNING |
| 修复 vs 规则捕获 | 修复P0风险应可被新版规则捕获 | ⚠ WARNING |
| Gate同步 | Gate跟踪表状态与工作表处置标记保持一致 | ❌ ERROR |
| 数据缺失 | 数据缺失条目应有明确处置方案 | ⚠ WARNING |

---

## 二、使用方法

### 2.1 基本用法

```bash
# 使用默认路径（位于 analysis/e2e_output/v85/ 下）
python3 review_consistency_check.py

# 指定工作表和Gate跟踪表
python3 review_consistency_check.py \
  --workbook /path/to/v85_p0_risk_human_workbook.csv \
  --gate /path/to/gate_block_tracker.csv
```

### 2.2 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--workbook` | P0工作表CSV路径 | `../dshb_human_review_prep/v85_p0_risk_human_workbook.csv` |
| `--gate` | Gate跟踪表CSV路径 | `../dshb_human_review_prep/gate_block_tracker.csv` |
| `--blacklist` | 黑名单JSON路径 | `../dshb_full_integrate/semantic_blacklist_v85_final.json` |
| `--boundary` | 边界测试集JSON路径 | `../miss_risk_mining/blacklist_boundary_testset.json` |

### 2.3 输出

- 控制台输出校验日志
- 自动在输入文件同目录生成 `_consistency_report.md` 报告文件
- 返回码: 0=通过, 1=存在错误

---

## 三、校验详细说明

### 3.1 白名单一致性校验

**目标**: 确保人工标记为白名单/放行的条目不会被黑名单规则误拦截。

**逻辑**:
1. 提取工作表中 recommended_action 包含'白名单'或'放行'的条目
2. 检查每条目的 series_name 是否匹配任何黑名单规则的 left_patterns
3. 若匹配则发出警告（可能存在规则冲突）

**示例**:

```
⚠ RISK-005(TPL-LC-087): 白名单放行但可能被规则拦截: BL-008, BL-015
```

**说明**: 这是预期行为 — RISK-005 因'国内销量'与'出口'互斥而被BL-008/015覆盖，但人工确认口径正确后放行是合理决策。校验脚本提示冲突供人工复核。

### 3.2 修复规则捕获校验

**目标**: 确保标记为'规则修复'的P0风险确实有对应的规则可以捕获。

**逻辑**:
1. 提取工作表中 recommended_action 包含'修复'或'BL-'的条目
2. 提取推荐的规则ID
3. 检查规则是否在主黑名单或扩展候选中

**示例**:

```
✓ RISK-002: 推荐规则 BL-009a 为扩展候选（classification=confirmed_new），需确认是否已纳入
⚠ RISK-010: 推荐规则 NOT_FIXABLE_BL-022 未在任何规则集中找到
```

### 3.3 Gate同步校验

**目标**: 确保Gate跟踪表中的阻塞状态与工作表中的实际处置进度一致。

**逻辑**:
1. 统计工作表中P0条目的处置状态（已阻塞/白名单/未处置）
2. 检查Gate跟踪表中H2的状态是否与实际P0处置率匹配
3. 检查G-03/G-05/G-06的状态是否与实际命中情况匹配

**示例**:

```
✓ H2阻塞状态正确（4条P0未处置）
⚠ G-03标记为部分完成但工作表中无未处置P0 — 请确认
```

### 3.4 数据缺失校验

**目标**: 确保数据缺失类P0风险有明确的处置方案。

**逻辑**:
1. 提取工作表中 root_cause_category 包含'数据缺失'或 notes 包含'matched_name'的条目
2. 检查每条目的 recommended_action 是否包含'白名单'、'放行'或'修复'

---

## 四、常见异常处理

### 4.1 文件路径错误

**现象**: `文件不存在: ...`
**解决**: 检查文件路径是否正确，确认CSV/JSON文件存在且编码为UTF-8

### 4.2 CSV编码问题

**现象**: `UnicodeDecodeError`
**解决**: 脚本默认使用 `utf-8-sig` 编码读取CSV。若文件为其他编码，请先转换为UTF-8

### 4.3 工作表为空

**现象**: `工作表为空或加载失败`
**解决**: 确认CSV文件非空，且包含有效的表头行

### 4.4 Gate跟踪表与P0工作表不同步

**现象**: `H2标记为完成但仍有N条P0未处置`
**解决**:
1. 检查Gate跟踪表中H2的 current_status 是否与实际处置进度匹配
2. 若工作表中所有P0已处置，更新Gate跟踪表中H2的 status 为 `DONE`
3. 若仍有未处置P0，确认Gate跟踪表H2的 blocked_count 正确

---

## 五、与Gate预校验的关系

| 脚本 | 功能 | 使用时机 |
|------|------|---------|
| `gate_pre_check.py` | 重算5项硬阻塞指标，重跑46项Gate | 人工评审完成后 |
| `review_consistency_check.py` | 校验人工填写的一致性 | 人工评审过程中随时运行 |

**推荐工作流**:
1. 人工评审填写P0工作表
2. 运行 `review_consistency_check.py` 检查一致性
3. 修复警告和错误
4. 运行 `gate_pre_check.py` 进行Gate预校验
5. 确认Gate全绿后提交

---

## 六、技术细节

### 6.1 校验类结构

```python
class ReviewConsistencyChecker:
    def check_workbook_integrity(self)    # 基本完整性
    def check_whitelist_consistency(self)  # 白名单 vs 黑名单
    def check_fix_capturable(self)         # 修复 vs 规则
    def check_gate_sync(self)              # Gate同步
    def check_data_missing_risks(self)     # 数据缺失
    def run(self)                          # 执行全部校验
```

### 6.2 严重级别定义

| 级别 | 含义 | 是否阻断提交 |
|------|------|-------------|
| ERROR | 数据不一致或逻辑矛盾 | ✅ 必须修复 |
| WARNING | 潜在风险或需关注 | ⚠ 建议修复 |
| INFO | 正常信息记录 | — |

### 6.3 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 校验通过（无ERROR） |
| 1 | 存在ERROR |
