# V85 版本快照监控基线配置

> **任务ID**: B_V85_ARTIFACT_PERSIST_AND_SNAPSHOT_VERIFY  
> **生成时间**: 2026-10-01  
> **分支**: feature/v85-chart-template  
> **快照Tag**: v85-final-persist  

---

## 1. 快照标识

| 属性 | 值 |
|------|-----|
| 快照Tag | `v85-final-persist` |
| 关联分支 | `feature/v85-chart-template` |
| 核心Commit | `a2815c4`, `6771406`, `f313570` |
| 归档目录 | `v85_final_archive/` |
| V85输出目录 | `analysis/e2e_output/v85/` |
| 校验脚本 | `analysis/e2e_output/v85/b_storage_persist/artifact_ingest_check.py` |
| 快照时间 | 2026-10-01T20:25:19 |
| 文件总数 | 453 |
| 总大小 | 32.38 MB |

---

## 2. 变更告警规则

### 2.1 文件变更检测

**目标**: 检测V85核心交付物文件是否被意外修改

| 监控对象 | 告警条件 | 严重级别 | 响应动作 |
|----------|----------|----------|----------|
| `semantic_blacklist_v85_final.json` | MD5变更 | 🔴 P0-严重 | 立即告警, 回滚 |
| `indicator_alias_library.csv` (HERMES) | MD5变更 | 🔴 P0-严重 | 立即告警, 回滚 |
| `indicator_alias_library.csv` (审计) | MD5变更 | 🔴 P0-严重 | 立即告警, 回滚 |
| `unified_indicator_risk_db.csv` | MD5变更 | 🟡 P1-警告 | 通知负责人, 人工确认 |
| `unified_indicator_risk_db_v2.csv` | MD5变更 | 🟡 P1-警告 | 通知负责人, 人工确认 |
| `unified_indicator_risk_db_final.csv` | MD5变更 | 🟡 P1-警告 | 通知负责人, 人工确认 |
| `sim_sceneA_result.csv` | MD5变更 | 🟡 P1-警告 | 通知负责人, 人工确认 |
| `sim_sceneB_result.csv` | MD5变更 | 🟡 P1-警告 | 通知负责人, 人工确认 |
| `alias_test_case_set.json` | MD5变更 | 🟡 P1-警告 | 通知负责人, 人工确认 |
| `blacklist_boundary_testset.json` | MD5变更 | 🟡 P1-警告 | 通知负责人, 人工确认 |
| `dsh_final_gate_acceptance.md` | MD5变更 | 🔵 P2-提示 | 日志记录 |
| `v85_rule_full_summary.md` | MD5变更 | 🔵 P2-提示 | 日志记录 |
| `JOB_READY.flag` | 内容变更 | 🔵 P2-提示 | 日志记录 |

### 2.2 目录结构变更检测

**目标**: 检测核心目录是否被删除或新增

| 监控对象 | 告警条件 | 严重级别 |
|----------|----------|----------|
| `analysis/e2e_output/v85/` | 目录删除 | 🔴 P0-严重 |
| `v85_final_archive/` | 目录删除 | 🔴 P0-严重 |
| `analysis/e2e_output/v85/` | 新增未预期子目录 | 🔵 P2-提示 |
| `v85_final_archive/` | 文件数减少 | 🔴 P0-严重 |

### 2.3 文件数量监控

**目标**: 检测文件数量异常波动

| 监控对象 | 基线值 | 告警阈值 | 严重级别 |
|----------|--------|----------|----------|
| V85输出目录文件数 | 387 | ±5% (368-407) | 🟡 P1-警告 |
| 归档目录文件数 | 66 | ±10% (59-73) | 🟡 P1-警告 |
| 总文件数 | 453 | ±5% (430-476) | 🟡 P1-警告 |
| 核心只读文件数 | 21 | <21 | 🔴 P0-严重 |

---

## 3. MD5篡改检测

### 3.1 检测频率

| 检测类型 | 频率 | 工具 |
|----------|------|------|
| 全量MD5校验 | 每日1次 | `artifact_ingest_check.py --md5-only` |
| 核心文件快速校验 | 每4小时 | `artifact_ingest_check.py --readonly-only` |
| 增量变更检测 | 每次git push后 | CI/CD钩子 |

### 3.2 基线MD5清单

#### 核心文件基线 (21项)

```
# 黑名单
semantic_blacklist_v85_final.json|1e1bdf48a7734bce50df263ce4c3ef1a
blacklist_extend_candidate_v2.json|1489cda7f7d6fc8c78cb5611653832cd

# 别名库
indicator_alias_library.csv(HERMES)|8743cedbe614c4da6ffcaadee43eb6fd
indicator_alias_library.csv(审计)|e9989c2938b1707739f85e6085e91414

# 风险库
unified_indicator_risk_db.csv|1c56f59ad5329655753c23e6968e42f6
unified_indicator_risk_db_v2.csv|fbde5245b225876445fc0af72e926ef7
unified_indicator_risk_db_final.csv|178f993b09af4895769ecbfb41e61b5d

# 模板
pdf_web_chart_template_draft.json|24d08d002af09023026fcca9f15208b4
ths_chart_template_list.json|65125c53506299e85d1a89fe9436c610
tonghuashun_chart_template.json|a4da3d760e240b0fa8d41082112407dc

# 场景回放
sim_sceneA_result.csv|f981388a614692bc146924ac0bc6c4de
sim_sceneB_result.csv|148bca5f0562fa7f644c718131f21e3b

# 测试集
alias_test_case_set.json|271c374bed5c59faac34f47b4c7376b0
blacklist_boundary_testset.json|bba79ab946b4d0d584406216e6d81455

# 交付报告
dsh_final_gate_acceptance.md|9ef297bf85c756d3c0979c6a2d1c1dec
v85_rule_full_summary.md|0355ced9934c1227a8031ceb795d0c8a
v85_risk_final_conclusion.md|ce7b5a14fec7ccefafc9f1424815d5b6
v86_rule_milestone_ticket.md|610f442f3ec26d01596c10d3ba241c63
dshb_data_readme_for_hermes.md|88d37b42faf73f6ea4463f342933141d

# 系统文件
JOB_READY.flag|8164c4d65fae85e0011fe9e3e0f46128
MD5_CHECKSUM_LIST.md|59fc393f0fc7c516b3a4be1988d33383
```

### 3.3 篡改检测响应流程

```
┌─────────────────────┐
│  检测到MD5变更       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  判断文件所属级别     │
│  P0(严重)→立即回滚   │
│  P1(警告)→人工确认   │
│  P2(提示)→日志记录   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  记录变更日志       │
│  标记快照版本       │
└─────────────────────┘
```

---

## 4. 快照可用性探测规则

### 4.1 探测频率

| 探测项 | 频率 | 方法 |
|--------|------|------|
| Git tag存在性 | 每日 | `git tag -l "v85*"` |
| 归档目录完整性 | 每日 | `artifact_ingest_check.py --snapshot-only` |
| MD5清单存在性 | 每日 | 检查`MD5_MANIFEST.md` |
| 归档子目录结构 | 每周 | 检查8个子目录 |

### 4.2 快照完整性检查

```
检查项                          期望状态    失败响应
─────────────────────────────────────────────────────
git tag v85-final-persist       EXISTS      重新创建tag
v85_final_archive/MD5_MANIFEST  EXISTS      重建清单
v85_final_archive/GIT_TAG_NOTE  EXISTS      重新生成
v85_final_archive/ARCHIVE_BUILD EXISTS      报告异常
归档文件数(66)                   >=60        检查缺失
归档总大小(1.2MB)                >=0.8MB     检查截断
```

### 4.3 快照恢复流程

当快照不可用时, 执行以下步骤恢复:

1. **定位最新Git tag**: `git tag -l "v85*" --sort=-version:refname`
2. **检出快照**: `git checkout v85-final-persist -- v85_final_archive/`
3. **重建MD5清单**: 运行 `python analysis/e2e_output/v85/b_storage_persist/artifact_ingest_check.py --md5-only --output result.json`
4. **验证恢复**: 重新运行全量校验
5. **记录恢复日志**: 更新 `JOB_READY.flag`

---

## 5. CI/CD集成配置

### 5.1 Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
# 检查V85核心文件是否被修改

CORE_FILES="
analysis/e2e_output/v85/dshb_full_integrate/semantic_blacklist_v85_final.json
analysis/e2e_output/v85/hermes_portal_gate_final/indicator_alias_library.csv
analysis/e2e_output/v85/unified_risk_db/unified_indicator_risk_db.csv
analysis/e2e_output/v85/dshb_review_simulation/sim_sceneA_result.csv
analysis/e2e_output/v85/dshb_review_simulation/sim_sceneB_result.csv
analysis/e2e_output/v85/dshb_final_gate_summary/dsh_final_gate_acceptance.md
analysis/e2e_output/v85/JOB_READY.flag
"

for f in $CORE_FILES; do
    if git diff --cached --name-only | grep -q "$f"; then
        echo "⚠️  警告: 核心只读文件被修改: $f"
        echo "如需修改, 请确认并记录原因"
    fi
done
```

### 5.2 CI Pipeline 集成

```yaml
# .github/workflows/v85_snapshot_check.yml
name: V85 Snapshot Integrity Check

on:
  push:
    branches: [feature/v85-chart-template]
  schedule:
    - cron: '0 8 * * *'  # 每日8:00

jobs:
  snapshot-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      - name: Run artifact ingest check
        run: python analysis/e2e_output/v85/b_storage_persist/artifact_ingest_check.py
      - name: Check git tag
        run: git tag -l "v85*"
```

### 5.3 告警通知配置

| 告警级别 | 通知渠道 | 响应时限 |
|----------|----------|----------|
| P0-严重 | 即时通讯群 + 邮件 | 30分钟内响应 |
| P1-警告 | 邮件 + 日志 | 4小时内响应 |
| P2-提示 | 日志记录 | 下次维护处理 |

---

## 6. 快照版本管理

### 6.1 版本命名规范

```
v{major}.{minor}.{patch}-{stage}

示例:
  v85.0.0-final        — V85正式发布版本
  v85.0.0-persist      — V85持久化快照
  v85.0.1-fix          — V85小版本修复
  v86.0.0-alpha        — V86 Alpha版本
```

### 6.2 版本升级流程

| 升级类型 | 触发条件 | 操作 |
|----------|----------|------|
| 快照更新 | 修复CSV列数偏差 | 重新打tag |
| 快照重建 | 新增交付物 | 更新归档包+重新校验 |
| 版本迁移 | V86迭代 | 新建v86_final_archive/ |

### 6.3 快照保留策略

| 快照版本 | 保留周期 | 存储位置 |
|----------|----------|----------|
| 当前版本 | 无限期 | Git + 本地归档 |
| 历史版本 | 1年 | Git tag |
| 归档版本 | 永久 | 归档目录 |

---

## 7. 监控仪表盘指标

### 7.1 关键指标 (KPI)

| 指标 | 目标值 | 当前值 | 状态 |
|------|--------|--------|------|
| MD5通过率 | 100% | 100% | ✅ |
| 目录结构完整率 | 100% | 100% | ✅ |
| 文件解析通过率 | ≥98% | 99.1% | ✅ |
| 核心文件只读率 | 100% | 100% | ✅ |
| 快照可用性 | 100% | 100% | ✅ |
| Git tag存在性 | 100% | 100% | ✅ |

### 7.2 趋势指标

| 指标 | 当前基线 | 预期趋势 |
|------|----------|----------|
| 文件总数 | 453 | 稳定 |
| 总大小 | 32.38 MB | 稳定 |
| 核心文件数 | 21 | 稳定 |
| MD5通过率 | 100% | 保持 |
| 解析通过率 | 99.1% | 修复至100% |

---

## 8. 故障恢复手册

### 8.1 常见故障与处置

| 故障现象 | 可能原因 | 处置方案 | 预计耗时 |
|----------|----------|----------|----------|
| Git tag丢失 | 远程tag被删除 | `git push origin v85-final-persist` | 5分钟 |
| 归档文件缺失 | 文件被误删 | 从Git恢复: `git checkout <commit> -- v85_final_archive/` | 10分钟 |
| MD5批量不匹配 | 磁盘损坏/文件系统错误 | 从远程仓库重新clone | 15分钟 |
| CSV解析异常 | 编码/格式问题 | 检查文件编码, 必要时重新生成 | 30分钟 |
| 核心文件MD5变更 | 人工修改 | 确认修改意图, 更新基线 | 15分钟 |
| 归档目录为空 | 目录被清空 | 从Git恢复 | 10分钟 |
| 快照校验脚本异常 | Python环境/依赖 | 检查Python版本, 安装依赖 | 10分钟 |

### 8.2 快速恢复命令

```bash
# 1. 恢复快照tag
git fetch origin --tags
git checkout v85-final-persist

# 2. 恢复归档文件
git checkout v85-final-persist -- v85_final_archive/

# 3. 重新运行校验
python analysis/e2e_output/v85/b_storage_persist/artifact_ingest_check.py

# 4. 更新MD5基线
# 根据校验结果更新本文件第3.2节基线清单
```

---

## 9. 约束遵守

| 约束 | 遵守 |
|------|------|
| NO_ZHIJI_API_CALL=TRUE | ✅ 监控配置中不包含任何API调用 |
| READ_ONLY=TRUE | ✅ 仅读取文件校验, 不修改源文件 |
| NO_MODIFY_SOURCE_TEMPLATE=TRUE | ✅ 不修改原始GT/模板/黑名单 |
| 分支锁定 feature/v85-chart-template | ✅ |

---

## 10. 附录: 校验脚本使用指南

```bash
# 全量校验 (推荐每日执行)
python analysis/e2e_output/v85/b_storage_persist/artifact_ingest_check.py

# 仅MD5校验
python analysis/e2e_output/v85/b_storage_persist/artifact_ingest_check.py --md5-only

# 仅目录结构校验
python analysis/e2e_output/v85/b_storage_persist/artifact_ingest_check.py --structure-only

# 仅文件解析校验
python analysis/e2e_output/v85/b_storage_persist/artifact_ingest_check.py --parse-only

# 仅快照探测
python analysis/e2e_output/v85/b_storage_persist/artifact_ingest_check.py --snapshot-only

# 输出JSON结果
python analysis/e2e_output/v85/b_storage_persist/artifact_ingest_check.py --output result.json

# 详细输出
python analysis/e2e_output/v85/b_storage_persist/artifact_ingest_check.py --verbose
```
