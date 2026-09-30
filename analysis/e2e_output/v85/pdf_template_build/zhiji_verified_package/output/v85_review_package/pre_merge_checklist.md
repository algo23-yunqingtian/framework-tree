# V85 图表模板分支合并上线检查清单与回滚方案

> 工单: `HERMES_V85_ARTIFICIAL_REVIEW_PREP`  
> 生成时间: 2026-09-30 13:52:59  
> 当前分支: `feature/v85-chart-template` @ `d67aebba0b5f`  
> ⛔ **本文档仅为准备材料，当前不发起任何生产部署**

## 1. 分支合并前检查项（Blocker 必须全部通过）

### 1.1 Blocker 项（不通过禁止合并）

| # | 检查项 | 当前状态 | 通过条件 |
|---|---|---|---|
| B1 | P0 口径冲突抽检 | ❌ **9 项待处理** | 全部判定结论为「✅通过」或已替换为新 zhiji_id |
| B2 | 异常指标补 ID | ❌ **7 条无有效数据** | 5 INVALID + 2 MISSING 全部补齐 zhiji_id 并重跑 |
| B3 | PART_OK 处置决策 | ❌ **6 张待定** | 逐张决策: 升级 FULL_OK 或永久剔除 |
| B4 | P1 匹配抽检 | ⚠️ **17 项待处理** | 全部人工确认 |
| B5 | 视觉验收 | ⚠️ 待评审 | 业务方逐图对照 PDF 原图签字 |
| B6 | 低分图表复核 | ⚠️ 62 张待复核 | 评分 <7 的必须处理 |
| B7 | 门禁校验 reclaim.py | ⏳ 未执行 | `python3 scripts/reclaim.py` 全部通过 |
| B8 | 节点映射核对 | ✅ 36 节点已生成 | 业务确认节点归属正确 |

### 1.2 约束合规检查（当前已全部通过 ✅）

| # | 约束 | 状态 | 证据 |
|---|---|---|---|
| C1 | 仅测试分支，禁止合并 main | ✅ | 当前 `feature/v85-chart-template` |
| C2 | 不修改 indicators_v1.json | ✅ | MD5 `7a864e10` 未变 |
| C3 | 不修改 tree_config.json | ✅ | MD5 `9b98c8af` 未变 |
| C4 | 不修改原始模板包 | ✅ | MD5 `92371c0a` 未变 |
| C5 | PART_OK 强制告警 | ✅ | 6 张全部红色告警，FULL_OK 零误标 |
| C6 | 不发起生产部署 | ✅ | 仅本地渲染，未部署任何服务 |

### 1.3 数据资产盘点

| 资产 | 数量 | 位置 |
|---|---|---|
| 渲染图表 HTML | 333 | `v85_chart_online_test/rendered/` |
| zhiji 时序缓存 | 248 | `zhiji_data_cache/` |
| 节点索引 | 36 节点 | `node_index.json` / `node_mapping_index.csv` |
| 视觉评分记录 | 333 行 | `visual_check_result.csv` |
| 渲染明细 | 6.5MB | `render_detail.json` |

## 2. 合并执行步骤（评审通过后方可执行）

```bash
# 前置: 确认所有 Blocker 已通过
cd /home/ubuntu/framework-tree

# 1. 确认当前分支与状态
git checkout feature/v85-chart-template
git status --short
git log --oneline -5

# 2. 更新 main 基线
git fetch origin
git checkout main
git pull origin main

# 3. 门禁校验（合并前必须全部通过）
python3 scripts/reclaim.py

# 4. 执行合并
git merge --no-ff feature/v85-chart-template \
  -m "feat(v85): 图表模板在线渲染 333图 + 36节点映射 (HERMES_V85_CHART_TEMPLATE_INTEGRATION)"

# 5. 推送
git push origin main

# 6. 清理测试分支（可选）
git push origin --delete feature/v85-chart-template
```

## 3. 生产环境部署步骤（需单独部署工单）

> ⚠️ 本文档仅描述步骤，**当前不执行**。部署需另开工单并确认资源。

### 3.1 部署前准备

| # | 步骤 | 说明 |
|---|---|---|
| D1 | 前端路由接入 | 按 `node_mapping_index.csv` 的 `node_path` 配置品种页面路由 |
| D2 | 静态资源发布 | `rendered/*.html` 部署至看板静态目录 |
| D3 | zhiji 拉取定时任务 | 按品种数据频率配置（日度/周度/月度）增量拉取 |
| D4 | ECharts CDN 缓存 | 本地化 `echarts@5.5.0`，避免 CDN 抖动 |
| D5 | 数据缓存策略 | zhiji 时序落本地，避免重复调用（当前已实现缓存） |
| D6 | 额度监控 | 配置 zhiji API 调用额度告警 |

### 3.2 部署执行

```bash
# 1. 构建前端产物
# (按项目构建流程执行)

# 2. 增量拉取数据（避免全量重跑 764s）
# python3 t21_fetch_zhiji.py   # 有缓存自动跳过，仅新增/失效 ID 会拉取

# 3. 重新渲染
python3 t22_render_online.py

# 4. 发布至看板服务
# (发布流程按现有部署规范执行)

# 5. 冒烟验证
# - 抽查 6 个品种各 3 张图表
# - 确认 PART_OK 告警展示正确
# - 确认 zhiji 数据为最新
```

## 4. 回滚方案

### 4.1 合并回滚（代码级）

```bash
# 场景: 合并后发现问题
# 方式A: revert 合并提交（推荐，保留历史）
git revert -m 1 <merge_commit_sha>
git push origin main

# 方式B: 强制回退（慎用，需确认无他人提交）
git log --oneline -5
git reset --hard <merge前commit>
git push --force-with-lease origin main
```

### 4.2 部署回滚（运行时）

| 层级 | 回滚动作 | 耗时 | 说明 |
|---|---|---|---|
| 图表层 | 删除 `rendered/*.html` 并恢复上一版本 | 5min | 不影响其他功能 |
| 路由层 | 移除品种页面路由配置 | 10min | 页面不可访问但不报错 |
| 数据层 | zhiji 缓存保留不删 | 0 | 缓存可复用，无需重建 |
| 全量 | revert 合并 + 清除静态资源 | 20min | 完全回到合并前状态 |

### 4.3 回滚触发条件

| 优先级 | 触发条件 | 建议动作 |
|---|---|---|
| P0 | 口径错误图表被业务方发现并投诉 | 立即图表层回滚 |
| P0 | 页面白屏/JS 报错 | 立即图表层回滚 |
| P1 | zhiji 额度耗尽导致大面积空图 | 暂停拉取任务，保留缓存 |
| P2 | 少量图表样式异常 | 定点修复，无需回滚 |

### 4.4 回滚验证清单

- [ ] `git log --oneline -3` 确认 revert 提交存在
- [ ] 抽查 6 个品种页面均可正常访问（或已下线）
- [ ] `scripts/reclaim.py` 门禁通过
- [ ] indicators_v1.json / tree_config.json MD5 未变
- [ ] STATUS.md 已记录回滚原因

## 5. 上线判定矩阵

| 条件组合 | 决策 |
|---|---|
| B1-B8 全部通过 | ✅ 合并并部署 |
| B1/B4 抽检发现口径错误 | ❌ 替换 ID 后重跑，重新评审 |
| 仅 B2/B3 未决（异常指标） | ⚠️ 可先合并，PART_OK 图表不挂载至看板 |
| 视觉验收未通过 | ❌ 不合并，修复后重新生成评审材料 |


## 6. 遗留项汇总

| 优先级 | 事项 | 数量 | 影响 |
|---|---|---|---|
| P0 | 口径冲突模糊匹配 | 9 项 | 图表数据误导，禁止投产 |
| P0 | INVALID zhiji_id (HTTP 500) | 5 条 | 图表空渲染 |
| P0 | MISSING series | 2 条 | 图表空渲染 |
| P1 | P1 匹配待复核 | 17 项 | 口径可能不一致 |
| P1 | PART_OK 模板处置 | 6 张 | 不纳入正式投产 |
| P2 | 低分图表 | 62 张 | 视觉细节 |
| P2 | delivery_confirm.md 缺失 | 1 项 | 已用 MD5 实测替代 |

