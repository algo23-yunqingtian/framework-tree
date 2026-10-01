# V85 上线部署与回滚操作手册

> 工单: `HERMES_V85_PRE_ARCHIVE_PACKAGE_PREP_AND_RELEASE_NOTE`
> 生成时间: 2026-10-01

---

## 1. 上线部署步骤

### 1.1 前置条件检查

```bash
# 1. Gate全绿检查
python3 analysis/e2e_output/v85/hermes_v85_final_delivery/delivery_package_check.py
# 确认: 文件存在性✅ 红线文件✅ 分支✅ 约束合规✅

# 2. Gate最终验收报告
cat analysis/e2e_output/v85/hermes_v85_final_delivery/v85_gate_final_acceptance_report.md
# 确认: H1-H5全部PASS

# 3. MD5校验
cd v85_final_archive && md5sum -c MD5_MANIFEST.md
# 确认: 全部OK
```

### 1.2 上线前检查清单

| # | 检查项 | 命令 | 预期 |
|---|--------|------|------|
| 1 | Gate全绿 | `cat v85_gate_final_acceptance_report.md` | 5/5 PASS |
| 2 | 自检通过 | `python3 delivery_package_check.py` | PASS |
| 3 | MD5校验 | `md5sum -c MD5_MANIFEST.md` | 全部OK |
| 4 | 分支正确 | `git branch` | feature/v85-chart-template |
| 5 | 红线文件 | `md5sum data/indicators_v1.json` | 7a864e10 |
| 6 | 无zhiji调用 | `grep -r "zhiji_api" analysis/e2e_output/v85/ --include="*.py"` | 仅注释引用 |

### 1.3 版本切换流程

```bash
# 1. 从feature分支合并到main
git checkout main
git merge feature/v85-chart-template --no-ff -m "V85 Final Delivery Merge"

# 2. 打tag
git tag -a v85-final -m "V85 Final Delivery - 2026-10-01"
git push origin main v85-final

# 3. 触发CI/CD (如适用)
# 或手动部署到目标环境
```

### 1.4 部署验证

| # | 验证项 | 方法 | 预期 |
|---|--------|------|------|
| 1 | 模板渲染 | 打开333个PDF模板HTML | 328个正常渲染 |
| 2 | 黑名单校验 | 运行488模板回放 | 31规则全部命中 |
| 3 | Gate状态 | `python3 gate_pre_check.py` | 全部PASS |
| 4 | 评审工具 | `python3 batch_export_import_v2.py --help` | 正常输出 |
| 5 | 门户文档 | `cat enhanced_review_portal_v6_final.md` | 内容完整 |

---

## 2. 一键回滚操作

### 2.1 回滚触发条件

| 条件 | 说明 | 紧急度 |
|------|------|--------|
| P0风险回归 | 已解除P0重新出现 | 🔴 紧急 |
| 渲染故障 | >10%模板无法加载 | 🔴 紧急 |
| 黑名单误拦 | 正常指标被拦截 | 🟡 重要 |
| Gate倒退 | 已解除Gate重新阻塞 | 🟡 重要 |
| 数据异常 | 模板数据错误 | 🟡 重要 |

### 2.2 快速回滚（5分钟）

```bash
# 方案A: git revert (推荐)
git checkout main
git revert <v85-merge-commit-hash>
git push origin main

# 方案B: 重置到tag
git checkout main
git reset --hard v85-final^
git push origin main --force

# 方案C: 切换分支
git checkout feature/v84-stable  # 上一稳定分支
git push origin feature/v84-stable
```

### 2.3 完整回滚流程

```bash
# 1. 确认回滚commit
git log --oneline -5

# 2. revert V85合并
git revert <merge-commit>

# 3. 恢复模板数据(如已修改)
git checkout v85-final^ -- data/indicators_v1.json
git checkout v85-final^ -- data/tree_config.json

# 4. 验证回滚
python3 analysis/e2e_output/v85/hermes_v85_final_delivery/delivery_package_check.py

# 5. 推送回滚
git push origin main

# 6. 通知
echo "V85已回滚至$(git log --oneline -1 | cat)" | mail -s "V85回滚通知" team@example.com
```

### 2.4 回滚时间线

| 步骤 | 耗时 | 说明 |
|------|------|------|
| 确认回滚 | 2分钟 | 判断是否需回滚 |
| git revert | 1分钟 | 执行回滚命令 |
| 验证 | 10分钟 | 运行自检脚本 |
| 推送 | 1分钟 | 推送到远程 |
| 通知 | 2分钟 | 通知相关方 |
| **总计** | **16分钟** | |

---

## 3. 版本切换操作

### 3.1 升级到V86

```bash
# V85保持main分支
# V86在feature/v86-xxx分支开发
# V86完成后合并到main
git checkout main
git merge feature/v86-xxx --no-ff
git tag -a v86-final -m "V86 Release"
git push origin main v86-final
```

### 3.2 降级到V84

```bash
git checkout main
git reset --hard v84-stable
git push origin main --force
```

---

## 4. 校验项清单

### 4.1 上线前校验

- [ ] Gate 52项全绿
- [ ] delivery_package_check.py PASS
- [ ] MD5校验通过
- [ ] 红线文件MD5匹配
- [ ] 无zhiji API真实调用
- [ ] 分支锁定feature/v85-chart-template
- [ ] 488模板HTML渲染正常
- [ ] 黑名单31规则验证通过
- [ ] 评审工具可运行
- [ ] 门户文档完整

### 4.2 上线后校验

- [ ] 模板加载成功率>95%
- [ ] 无P0风险回归
- [ ] 黑名单误拦率<1%
- [ ] Gate状态保持全绿
- [ ] 数据源正常
- [ ] 用户反馈无异常

### 4.3 回滚后校验

- [ ] 模板回到上一版本状态
- [ ] Gate恢复到回滚前状态
- [ ] MD5匹配回滚前版本
- [ ] 通知所有相关方
- [ ] 记录回滚原因和后续修复计划

---

## 5. 应急预案

### 5.1 模板批量渲染故障

```bash
# 1. 立即回滚
git revert <v85-merge-commit>

# 2. 检查渲染脚本
cat output/v85_chart_online_test/build_pb_*.py

# 3. 检查数据源
python3 ~/.hermes/scripts/zhiji_api.py search "锌 社会库存"
```

### 5.2 黑名单误拦截

```bash
# 1. 检查触发规则
cat analysis/e2e_output/v85/dshb_full_integrate/semantic_blacklist_v85_final.json

# 2. 定位误拦规则
python3 -c "
import json
d = json.load(open('analysis/e2e_output/v85/dshb_full_integrate/semantic_blacklist_v85_final.json'))
for r in d['rules']:
    print(r['id'], r['name'])
"

# 3. 临时白名单
# 编辑黑名单JSON添加白名单例外
```

### 5.3 Gate倒退

```bash
# 1. 运行Gate检查
python3 analysis/e2e_output/v85/hermes_human_review_tool/gate_pre_check.py

# 2. 对比基线
cat analysis/e2e_output/v85/hermes_v85_final_delivery/v85_gate_final_acceptance_report.md

# 3. 定位倒退项
diff <(cat report_new.md) <(cat report_old.md)
```
