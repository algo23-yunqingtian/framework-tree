# 人工评审产出归档规范

> 工单: `HERMES_V85_HUMAN_REVIEW_TOOL_ENHANCE_AND_BATCH_DATA_PREP`
> 目的: 规定人工评审完成后的文件命名、目录结构、MD5归档、git提交规范、验收校验逻辑

---

## 1. 目录结构

```
hermes_human_review_tool/
├── review_archive/                          # 人工评审归档目录
│   ├── batch_A_completed_YYYYMMDD.csv       # Batch-A已完成评审
│   ├── batch_B_completed_YYYYMMDD.csv       # Batch-B已完成评审
│   ├── batch_C_completed_YYYYMMDD.csv       # Batch-C已完成评审
│   ├── p0_risk_disposal_YYYYMMDD.csv        # P0风险处置结果
│   ├── ths_zhiji_fill_YYYYMMDD.csv          # THS zhiji_id回填结果
│   ├── archive_manifest.md                  # 归档清单
│   └── archive_checksums.md5                # MD5校验文件
├── v85_p0_risk_human_workbook.csv            # P0风险工作表(原始)
├── gate_block_tracker.csv                    # Gate进度跟踪
├── review_batches_v6/                        # v6批次(原始)
├── gate_pre_check.py                         # Gate预校验脚本
├── batch_export_import_v2.py                 # 批量工具v2
└── ...
```

---

## 2. 文件命名规范

### 2.1 评审结果文件

| 文件类型 | 命名格式 | 示例 |
|---------|---------|------|
| 批次评审结果 | `batch_{A/B/C}_completed_YYYYMMDD.csv` | `batch_A_completed_20261007.csv` |
| P0风险处置 | `p0_risk_disposal_YYYYMMDD.csv` | `p0_risk_disposal_20261007.csv` |
| THS回填结果 | `ths_zhiji_fill_YYYYMMDD.csv` | `ths_zhiji_fill_20261007.csv` |

### 2.2 日期格式

- `YYYYMMDD`：评审完成日期（如 `20261007`）
- 多次评审追加版本号：`_v2`, `_v3`

---

## 3. MD5归档

### 3.1 校验文件生成

```bash
# 生成归档MD5
cd hermes_human_review_tool/review_archive/
md5sum *.csv > archive_checksums.md5
```

### 3.2 校验文件格式

```
b3c2286053cb57c075c14afc7a32cd56  batch_A_completed_20261007.csv
bf4aeb5dfd7fd812c9874425d0453aa4  batch_B_completed_20261007.csv
a5abb21fd4647d037634688a48101921  batch_C_completed_20261007.csv
f9783f90ffa440bbdd51ca351be09924  p0_risk_disposal_20261007.csv
8743cedbe614c4da6ffcaadee43eb6fd  ths_zhiji_fill_20261007.csv
```

### 3.3 校验验证

```bash
md5sum -c archive_checksums.md5
```

---

## 4. Git提交规范

### 4.1 提交前缀

| 类型 | 前缀 | 示例 |
|------|------|------|
| 人工评审结果 | `[B]` | `[B] V85人工评审Batch-A完成(97/97)` |
| P0风险处置 | `[B]` | `[B] V85 P0风险处置完成(34/34)` |
| THS回填 | `[B]` | `[B] V85 THS zhiji_id回填完成(155/155)` |
| Gate预校验 | `[A]` | `[A] V85 Gate预校验通过(46/46)` |

### 4.2 提交内容

每次提交必须包含：
1. 评审结果CSV文件
2. 更新后的 `STATUS.md`
3. 归档清单 `archive_manifest.md`
4. MD5校验文件 `archive_checksums.md5`

### 4.3 提交命令

```bash
cd /home/ubuntu/framework-tree
git add analysis/e2e_output/v85/hermes_human_review_tool/review_archive/
git add STATUS.md
git commit -m "[B] V85人工评审Batch-A完成(97/97) — 评审人:XXX"
git push origin feature/v85-chart-template
```

---

## 5. 验收校验逻辑

### 5.1 评审完成验收

| 校验项 | 标准 | 校验命令 |
|--------|------|---------|
| Batch-A完成率 | 100% (97/97) | `wc -l batch_A_completed_*.csv` |
| Batch-B完成率 | 100% (155/155) | `wc -l batch_B_completed_*.csv` |
| Batch-C完成率 | 100% (236/236) | `wc -l batch_C_completed_*.csv` |
| P0风险处置 | 34/34 | `wc -l p0_risk_disposal_*.csv` |
| THS回填 | 155/155 | `wc -l ths_zhiji_fill_*.csv` |

### 5.2 Gate预校验

```bash
python3 gate_pre_check.py
```

输出新Gate报告，判定5项硬阻塞是否解除。

### 5.3 MD5一致性

```bash
md5sum -c archive_checksums.md5
```

### 5.4 验收通过标准

| 标准 | 要求 |
|------|------|
| 评审完成率 | ≥ 90% (≥440/488) |
| P0风险处置 | 34/34 全部处置 |
| THS匹配率 | ≥ 80% (≥124/155) |
| 渲染就绪率 | ≥ 50% (≥244/488) |
| Gate 46项 | 全部通过或可豁免 |
| MD5校验 | 全部一致 |
| Git提交 | 真实执行+push成功 |

---

## 6. 归档清单模板

```markdown
# 归档清单 — YYYY-MM-DD

## 评审结果

| 文件 | 条目数 | MD5 | 提交hash |
|------|--------|-----|---------|
| batch_A_completed_YYYYMMDD.csv | 97 | xxxxxx | xxxxxx |
| batch_B_completed_YYYYMMDD.csv | 155 | xxxxxx | xxxxxx |
| batch_C_completed_YYYYMMDD.csv | 236 | xxxxxx | xxxxxx |
| p0_risk_disposal_YYYYMMDD.csv | 34 | xxxxxx | xxxxxx |
| ths_zhiji_fill_YYYYMMDD.csv | 155 | xxxxxx | xxxxxx |

## Gate预校验

| Gate | 状态 | 变化 |
|------|------|------|
| H1 | PASS | 0%→100% |
| H2 | PASS | 2%→100% |
| H3 | PASS | 20%→55% |
| H4 | PASS | 0%→100% |
| H5 | PASS | 不变 |

## 验收结论

✅ V85 Gate全绿，允许合并 feature→main
```
