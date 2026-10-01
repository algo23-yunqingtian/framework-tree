# V85 评审门户 v7 操作手册

> 工单: `HERMES_V85_FINAL_DELIVERY_PACKAGE_BUILD_AND_ACCEPTANCE_PORTAL`
> 适用门户: `enhanced_review_portal_v6_final.md`
> v7新增: V6验收总览面板操作说明

---

## 1. 门户入口

```bash
# V6最终验收门户
cat analysis/e2e_output/v85/hermes_v85_final_delivery/enhanced_review_portal_v6_final.md
```

---

## 2. V6验收总览面板操作（v7新增）

### 2.1 版本总览

打开门户 §1，查看版本关键指标：
- 模板总数: 488
- 渲染就绪率: 19.9%
- 评审完成率: 0%
- Gate状态: ❌ 禁止上线

### 2.2 5项硬Gate状态大盘

打开门户 §2，查看5项硬阻塞状态：
- H1-H4: ❌ BLOCKED
- H5: ✅ PASS

### 2.3 风险库总览

打开门户 §3，查看DSHB风险库v2（50条）：
- 34条P0 (25独立+9重复)
- 黑名单规则: 31条最终版 + 1条候选(BL-009a)

### 2.4 别名库质量总览

打开门户 §4，查看别名库（864条）：
- 7品种，36.7%高置信覆盖率
- 13条高危混淆对

### 2.5 人工评审进度

打开门户 §6，查看评审进度：
- Batch-A: 0/97 (0%)
- Batch-B: 0/155 (0%)
- Batch-C: 0/236 (0%)
- P0风险处置: 0/34 (0%)

### 2.6 遗留风险清单

打开门户 §7，查看4项硬阻塞+4项可豁免+4项已知局限。

### 2.7 V86迭代入口

打开门户 §8，查看12项V86规划。

---

## 3. 交付包自检

### 3.1 运行自检脚本

```bash
python3 delivery_package_check.py
```

### 3.2 查看自检结果

```bash
cat delivery_check_result.md
```

### 3.3 自检校验项

| 校验项 | 说明 |
|--------|------|
| 文件存在性 | 所有声明文件是否存在 |
| MD5匹配 | MD5是否与清单一致 |
| 分支正确 | 是否在feature/v85-chart-template |
| 约束合规 | 无zhiji数据、未修改源模板 |

---

## 4. Gate最终验收

### 4.1 运行Gate预校验

```bash
python3 gate_pre_check.py
```

### 4.2 查看Gate报告

```bash
cat v85_gate_final_acceptance_report.md
```

### 4.3 Gate状态判定

| 状态 | 说明 | 动作 |
|------|------|------|
| ✅ PASS | 全部通过 | 允许合并+上线 |
| ⚠ PARTIAL | 部分通过 | 等待剩余解除 |
| ❌ BLOCKED | 阻塞 | 禁止上线 |

---

## 5. 归档打包

### 5.1 查看归档目录树

```bash
cat v85_archive_folder_tree.md
```

### 5.2 打包压缩

```bash
tar -czf v85_delivery_package.tar.gz \
  analysis/e2e_output/v85/hermes_v85_final_delivery/ \
  analysis/e2e_output/v85/hermes_human_review_tool/ \
  analysis/e2e_output/v85/hermes_portal_gate_final/
```

### 5.3 Git tag打标

```bash
git tag -a v85-final -m "V85 Final Delivery Package"
git push origin v85-final
```

---

## 6. 版本演示

### 6.1 查看演示文档

```bash
cat v85_demo_overview.md
```

### 6.2 演示要点

1. 核心能力（门户v6+人工评审工具+Gate看板）
2. 关键数据（488模板/328渲染/31规则/864别名/50风险）
3. Gate状态（❌4/5 BLOCKED — 禁止上线）
4. 上线路径（5-7天人工评审后）
