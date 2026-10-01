# 演示样例数据包说明

> 工单: `HERMES_V85_PORTAL_SIMULATION_DEMO_AND_GATE_DASHBOARD_TUNE`
> 生成时间: 2026-10-01
> 用途: 验收演示数据，非真实生产数据

---

## 1. 数据包内容

| # | 文件 | 说明 | MD5 |
|---|------|------|-----|
| 1 | sim_sceneA_result.csv | 场景A模拟结果(最小放行) | (见MD5清单) |
| 2 | sim_sceneB_result.csv | 场景B模拟结果(完整处置) | (见MD5清单) |
| 3 | p0_risk_sample.csv | P0风险样例(前5条) | (见MD5清单) |
| 4 | human_review_sample.csv | 人工填写样例行(3条) | (见MD5清单) |
| 5 | gate_tracker_sample.csv | Gate追踪样例 | (见MD5清单) |

---

## 2. 场景A模拟数据 (sim_sceneA_result.csv)

| 指标 | 基线 | 场景A | 变化 |
|------|------|-------|------|
| THS匹配率 | 0% | 80% | +80% |
| P0处置率 | 2% | 21% | +19% |
| 渲染就绪率 | 19.9% | 38.7% | +18.8% |
| 评审完成率 | 0% | 19.9% | +19.9% |
| Gate状态 | 4/5 BLOCKED | 2/5 BLOCKED | H1解除 |

### 场景A CSV样例

```csv
gate_id,gate_name,scene_a_value,scene_a_status,baseline_value,baseline_status,change
H1,THS匹配率,80%,PASS,0%,BLOCKED,+80%
H2,P0全部处置,21%,BLOCKED,2%,BLOCKED,+19%
H3,渲染就绪率,38.7%,BLOCKED,19.9%,BLOCKED,+18.8%
H4,评审完成率,19.9%,BLOCKED,0%,BLOCKED,+19.9%
H5,DSHB风险库,100%,PASS,100%,PASS,不变
```

---

## 3. 场景B模拟数据 (sim_sceneB_result.csv)

| 指标 | 基线 | 场景B | 变化 |
|------|------|-------|------|
| THS匹配率 | 0% | 100% | +100% |
| P0处置率 | 2% | 100% | +98% |
| 渲染就绪率 | 19.9% | 78.9% | +59% |
| 评审完成率 | 0% | 97.7% | +97.7% |
| Gate状态 | 4/5 BLOCKED | 0/5 BLOCKED | 全绿 |

### 场景B CSV样例

```csv
gate_id,gate_name,scene_b_value,scene_b_status,baseline_value,baseline_status,change
H1,THS匹配率,100%,PASS,0%,BLOCKED,+100%
H2,P0全部处置,100%,PASS,2%,BLOCKED,+98%
H3,渲染就绪率,78.9%,PASS,19.9%,BLOCKED,+59%
H4,评审完成率,97.7%,PASS,0%,BLOCKED,+97.7%
H5,DSHB风险库,100%,PASS,100%,PASS,不变
```

---

## 4. P0风险样例 (p0_risk_sample.csv)

| risk_id | template_id | variety | risk_level | current_status | recommended_action | gate_block_flag |
|---------|-------------|---------|------------|----------------|--------------------|-----------------|
| RISK-002 | TPL-LC-054 | LC | P0 | NOT_BLOCKED(漏拦截) | 规则修复: 新增BL-009a | YES |
| RISK-010 | TPL-NI-008 | NI | P0 | NOT_BLOCKED(漏拦截) | 上游数据修复或白名单 | YES |
| RISK-011 | TPL-NI-008 | NI | P0 | NOT_BLOCKED(漏拦截) | 上游数据修复或白名单 | YES |
| RISK-013 | TPL-NI-008 | NI | P0 | NOT_BLOCKED(漏拦截) | 上游数据修复或白名单 | YES |
| RISK-005 | TPL-AO-001 | AO | P0 | BLOCKED | 白名单放行 | YES |

---

## 5. 人工填写样例行 (human_review_sample.csv)

```csv
template_id,series_index,manual_zhiji_id,decision,remark,reviewer,review_time
THS-NI-2.3,0,ID01001761,通过,别名匹配正确,张三,2026-10-01 15:00:00
THS-NI-3.1,1,,驳回,跨品种风险(BL-022),李四,2026-10-01 15:05:00
TPL-LC-091,0,,修复,替换为产量指标,王五,2026-10-01 15:10:00
```

---

## 6. 加载到门户的操作步骤

### 6.1 场景A加载

1. 将 `sim_sceneA_result.csv` 放到门户数据目录
2. 打开门户，点击「场景A: 最小放行」
3. 门户自动读取CSV数据
4. Gate大盘刷新为场景A状态

### 6.2 场景B加载

1. 将 `sim_sceneB_result.csv` 放到门户数据目录
2. 打开门户，点击「场景B: 完整处置」
3. 门户自动读取CSV数据
4. Gate大盘刷新为场景B状态

### 6.3 运行Gate预校验

```bash
# 场景A
python3 gate_pre_check.py --scene A --output gate_sceneA_report.md

# 场景B
python3 gate_pre_check.py --scene B --output gate_sceneB_report.md
```

---

## 7. 数据加载验证

```bash
# 验证场景A数据
wc -l sim_sceneA_result.csv  # 应为5行(表头+5行Gate)

# 验证场景B数据
wc -l sim_sceneB_result.csv  # 应为5行

# 验证P0风险样例
wc -l p0_risk_sample.csv  # 应为5行(表头+5条风险)

# 验证人工填写样例
wc -l human_review_sample.csv  # 应为3行(表头+3条)
```
