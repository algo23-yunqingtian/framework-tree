# V85 归档目录结构与打包指引

> 工单: `HERMES_V85_FINAL_DELIVERY_PACKAGE_BUILD_AND_ACCEPTANCE_PORTAL`
> 规范来源: `human_review_archive_spec.md`

---

## 1. 归档目录结构

```
v85_final_archive/
├── hermes_v85_final_delivery/              # 最终交付包
│   ├── enhanced_review_portal_v6_final.md
│   ├── portal_operation_manual_v7.md
│   ├── v85_full_delivery_manifest_v2.md
│   ├── v85_delivery_readme.md
│   ├── delivery_package_check.py
│   ├── delivery_check_result.md
│   ├── v85_gate_final_acceptance_report.md
│   ├── v85_archive_folder_tree.md
│   └── v85_demo_overview.md
│
├── hermes_human_review_tool/               # 人工评审工具
│   ├── enhanced_review_portal_v5_review_workbench.md
│   ├── portal_operation_manual_v6.md
│   ├── batch_export_import_v2.py
│   ├── batch_tool_manual.md
│   ├── gate_dashboard_spec.md
│   ├── human_review_archive_spec.md
│   ├── gate_pre_check.py
│   ├── v85_p0_risk_human_workbook.csv
│   ├── gate_block_tracker.csv
│   └── review_batches_v6/
│       ├── batch_A_review_v6.csv
│       ├── batch_B_review_v6.csv
│       ├── batch_C_review_v6.csv
│       └── review_checklist_v6.md
│
├── hermes_portal_gate_final/               # 门户v5+Gate
│   ├── enhanced_review_portal_v5_full.md
│   ├── portal_operation_manual_v5.md
│   ├── v85_gate_rerun_check_result.md
│   ├── mapping_fill_helper_v2.py
│   ├── batch_export_import.py
│   ├── indicator_alias_library.csv
│   ├── high_risk_confusion_pairs.csv
│   └── review_batches_v5/
│
├── dshb_full_integrate/                    # DSHB全链路整合
│   ├── semantic_blacklist_v85_final.json
│   ├── full_488_template_playback_result.csv
│   ├── cross_variety_p0_validation.csv
│   ├── inconsistent_risk_items.csv
│   └── dsh_gate_self_check.md
│
├── miss_risk_mining/                       # DSHB漏检风险挖掘
│   ├── unified_indicator_risk_db_v2.csv
│   ├── dsh_gate_self_check_v2.md
│   ├── p0_miss_4_case_analysis.md
│   ├── p0_unhit_5_items_report.md
│   ├── blacklist_extend_candidate_v2.json
│   └── rule_defect_summary.md
│
├── v85_render_fix_review_package/          # 渲染脚本+评审包
│   ├── ths_render_task_manifest_fixed.json
│   ├── ths_render_prep_fixed.py
│   └── review_batches/
│
├── v85_ths_mapping_gap_prep/               # THS映射+缺口计划
│   ├── ths_candidate_mapping.csv
│   ├── ths_match_highconf.csv
│   └── gap_exec_plan.md
│
├── review_archive/                         # 人工评审结果(待填充)
│   ├── batch_A_completed_YYYYMMDD.csv
│   ├── batch_B_completed_YYYYMMDD.csv
│   ├── batch_C_completed_YYYYMMDD.csv
│   ├── p0_risk_disposal_YYYYMMDD.csv
│   ├── ths_zhiji_fill_YYYYMMDD.csv
│   └── archive_checksums.md5
│
└── JOB_READY.flag                          # 版本标记
```

---

## 2. 打包压缩指引

### 2.1 完整打包

```bash
cd /home/ubuntu/framework-tree

# 打包全部V85产物
tar -czf v85_final_delivery_$(date +%Y%m%d).tar.gz \
  analysis/e2e_output/v85/hermes_v85_final_delivery/ \
  analysis/e2e_output/v85/hermes_human_review_tool/ \
  analysis/e2e_output/v85/hermes_portal_gate_final/ \
  analysis/e2e_output/v85/dshb_full_integrate/ \
  analysis/e2e_output/v85/miss_risk_mining/ \
  analysis/e2e_output/v85/v85_render_fix_review_package/ \
  analysis/e2e_output/v85/v85_ths_mapping_gap_prep/ \
  analysis/e2e_output/v85/JOB_READY.flag

# 验证打包
tar -tzf v85_final_delivery_$(date +%Y%m%d).tar.gz | wc -l
```

### 2.2 分模块打包

```bash
# 仅HERMES产物
tar -czf v85_hermes_only.tar.gz \
  analysis/e2e_output/v85/hermes_v85_final_delivery/ \
  analysis/e2e_output/v85/hermes_human_review_tool/ \
  analysis/e2e_output/v85/hermes_portal_gate_final/

# 仅DSHB产物
tar -czf v85_dshb_only.tar.gz \
  analysis/e2e_output/v85/dshb_full_integrate/ \
  analysis/e2e_output/v85/miss_risk_mining/
```

### 2.3 MD5校验

```bash
# 生成MD5
find v85_final_archive/ -type f -exec md5sum {} + > v85_archive_checksums.md5

# 验证MD5
md5sum -c v85_archive_checksums.md5
```

---

## 3. 异地备份指引

### 3.1 本地备份

```bash
# 备份到/home/ubuntu/backup
mkdir -p /home/ubuntu/backup/v85
cp -r analysis/e2e_output/v85/* /home/ubuntu/backup/v85/

# 生成备份MD5
cd /home/ubuntu/backup/v85
find . -type f -exec md5sum {} + > backup_checksums.md5
```

### 3.2 Git备份

```bash
# 推送到远程仓库
git push origin feature/v85-chart-template

# 打tag
git tag -a v85-final -m "V85 Final Delivery Package - 2026-10-01"
git push origin v85-final
```

---

## 4. Git Tag 打标指引

### 4.1 打tag

```bash
# 轻量tag
git tag v85-final

# 附注tag（推荐）
git tag -a v85-final -m "V85 Final Delivery Package

- 488模板风险管控系统
- 31条黑名单规则 + 50条风险库
- 864条别名库 + 13条混淆对
- 人工评审工具 + Gate预校验
- Gate状态: ❌ 4/5 BLOCKED (待人工评审5-7天)
- 分支: feature/v85-chart-template
- 日期: 2026-10-01"

# 推送tag到远程
git push origin v85-final
```

### 4.2 查看tag

```bash
# 列出所有tag
git tag -l

# 查看tag信息
git show v85-final
```

### 4.3 回退到tag

```bash
# 查看tag对应的commit
git rev-parse v85-final

# 创建分支从tag
git checkout -b v85-hotfix v85-final
```

---

## 5. 验收校验

### 5.1 运行自检脚本

```bash
python3 analysis/e2e_output/v85/hermes_v85_final_delivery/delivery_package_check.py
```

### 5.2 验收标准

| 校验项 | 标准 |
|--------|------|
| 文件存在性 | 所有声明文件存在 |
| MD5匹配 | MD5与清单一致 |
| 分支正确 | feature/v85-chart-template |
| 红线文件 | 未修改 |
| 约束合规 | 无zhiji API调用 |
