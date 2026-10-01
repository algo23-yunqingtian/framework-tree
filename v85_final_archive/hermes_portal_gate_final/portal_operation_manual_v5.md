# V85 评审门户 v5 操作手册

> 工单: `HERMES_V85_PORTAL_FINAL_INTEGRATE_GATE_FULL_CHECK_AND_REVIEW_BATCH_PACKAGE`
> 适用门户: `enhanced_review_portal_v5_full.md`

---

## 1. 门户入口

```bash
# 门户文档
cat analysis/e2e_output/v85/hermes_portal_gate_final/enhanced_review_portal_v5_full.md

# 相关数据文件目录
ls analysis/e2e_output/v85/hermes_portal_gate_final/
```

---

## 2. 全局大盘查看

### 2.1 渲染队列占比

打开门户 §0.1，查看5个分组的数量分布。

### 2.2 品种分布

打开门户 §0.2，查看9个品种的P0/P1/CLEAN分布柱状图。

### 2.3 风险类型分布

打开门户 §0.3，查看P0/P1/CLEAN总量。

---

## 3. 黑名单规则查看（v5新增）

### 3.1 查看语义互斥黑名单

1. 打开门户 §3 黑名单规则详情面板
2. 查看10组语义互斥(G01-G10)
3. 每组含: 组ID/冲突类型/关键词/严重度/状态

### 3.2 BL-021 修复说明

1. 打开门户 §3.2 BL-021 修复说明
2. 了解 G08 组「价格↔均价」误报根因及修复方案

### 3.3 白名单规则

1. 打开门户 §3.3 白名单规则
2. 查看3条白名单放行规则

---

## 4. 别名库查看（v5新增）

### 4.1 查看别名库

```bash
# 查看全部别名
cat indicator_alias_library.csv | head -20

# 按品种筛选
grep ",NI," indicator_alias_library.csv

# 搜索特定指标
grep "沪铝主力" indicator_alias_library.csv
```

### 4.2 别名库字段说明

| 字段 | 说明 |
|------|------|
| alias_id | 别名唯一ID (ALIAS-0001) |
| ths_indicator_name | THS原始指标名 |
| zhiji_indicator_name | zhiji实际指标名 |
| zhiji_id | zhiji指标ID |
| variety | 品种代码 |
| similarity_score | 相似度分数(≥70为高置信) |
| alias_type | high_confidence / fuzzy_match |
| source | 数据来源 |
| created_date | 创建日期 |

### 4.3 别名库操作

```bash
# 按相似度排序
sort -t, -k6 -rn indicator_alias_library.csv | head -20

# 统计品种分布
cut -d, -f5 indicator_alias_library.csv | sort | uniq -c | sort -rn

# 导出特定品种别名
python3 batch_export_import.py --export-alias --variety NI
```

---

## 5. 高危混淆对查看（v5新增）

### 5.1 查看混淆对

```bash
# 查看全部混淆对
cat high_risk_confusion_pairs.csv

# 按严重度筛选
grep ",P0," high_risk_confusion_pairs.csv
grep ",P1," high_risk_confusion_pairs.csv
```

### 5.2 混淆对字段说明

| 字段 | 说明 |
|------|------|
| pair_id | 混淆对ID (CONF-001) |
| severity | P0(口径对立) / P1(语义近似) |
| chart_id | 所属图表模板ID |
| indicator_a | PDF/THS原始指标名 |
| indicator_b | zhiji实际指标名 |
| conflict_group | 冲突组ID (G01-G10) |
| reason | 冲突原因 |
| impact | 影响描述 |
| mitigation | 缓解措施 |

---

## 6. 风险库详情查看（v5新增）

### 6.1 查看单模板风险

```bash
python3 -c "
import json
bound = json.load(open('v85_final_integrate/chart_risk_bound_all.json'))
for t in bound['templates']:
    if t['template_id'] == 'TPL-LC-091':
        print(json.dumps(t, ensure_ascii=False, indent=2))
"
```

### 6.2 按品种/风险筛选

```bash
python3 batch_export_import.py --filter variety=NI,risk=P0 --export risk_detail.csv
```

---

## 7. 评审批次操作

### 7.1 查看批次

| 批次 | 范围 | 文件 |
|------|------|------|
| Batch-A | 可直接渲染+高置信 | `review_batches_v5/batch_A_review_v5.csv` |
| Batch-B | THS模糊待匹配 | `review_batches_v5/batch_B_review_v5.csv` |
| Batch-C | 阻塞/复核/降级 | `review_batches_v5/batch_C_review_v5.csv` |

### 7.2 评审流程

```bash
# 1. 导出待评审
python3 batch_export_import.py --export batch_A --out review_filled.csv

# 2. 人工填写(Excel/CSV编辑器)
# 填写: manual_zhiji_id, decision(通过/驳回/白名单), remark

# 3. 导入评审结果
python3 batch_export_import.py --import review_filled.csv

# 4. 回写manifest
python3 mapping_fill_helper_v2.py --apply

# 5. Gate复检
cat v85_gate_rerun_check_result.md
```

### 7.3 别名核验项（v5新增）

评审时需额外核对：

- [ ] **别名匹配**：该series是否有别名库匹配？匹配度多少？
- [ ] **混淆预警**：该series是否命中高危混淆对？
- [ ] **黑名单命中**：该series是否命中语义黑名单(G01-G10)？
- [ ] **白名单状态**：是否在白名单中？是否过期？

---

## 8. Gate准入查看

### 8.1 查看Gate报告

```bash
cat v85_gate_rerun_check_result.md
```

### 8.2 Gate状态说明

| 状态 | 说明 |
|------|------|
| ✅ 通过 | 检查项通过 |
| ❌ 未通过 | 检查项未通过(阻塞) |
| ⚠️ 可豁免 | 检查项未通过但可临时豁免 |

### 8.3 5项硬阻塞

打开门户 §7.2，查看5项硬阻塞条件当前状态。
