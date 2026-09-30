# V85 图表模板正式上线部署说明

> 工单: `HERMES_V85_CHART_TEMPLATE_INTEGRATION`  
> 生成时间: 2026-09-30T13:30:01

## 1. 当前状态

| 项 | 值 |
|---|---|
| 当前分支 | `feature/v85-chart-template` |
| 分支基线 | `4061dcf`（DSHB zhiji_verified_package 交付） |
| 渲染图表数 | 333 |
| 渲染成功率 | 98.5% |
| 视觉平均评分 | 9.63/10 |
| 上线状态 | **⛔ 未上线**（测试环境渲染验证中） |

## 2. 硬性约束（T4）— 当前遵守情况

| # | 约束 | 遵守 |
|---|---|---|
| 1 | 仅测试分支操作，**禁止合并 main** | ✅ 全部产物在 feature/v85-chart-template |
| 2 | 不修改 indicators_v1.json / tree_config.json | ✅ 零改动（只读消费） |
| 3 | PART_OK 强制告警，不与 FULL_OK 同等展示 | ✅ 红色告警条+失败明细表+🚫标记 |
| 4 | 渲染结果仅用于测试验收，人工评审后合并 | ✅ 见下节评审流程 |

## 3. 上线前人工评审流程

1. **视觉验收**: 打开 `rendered/*.html`，逐图对照 PDF 原图核对样式/坐标轴/图例/单位
2. **评分复核**: 查看 `visual_check_result.csv`，重点关注评分 < 7 的图表
3. **异常处理**: 按 `failed_chart_list.md` 处理
   - 5 项 INVALID series（HTTP 500 无效 zhiji_id）→ 人工在 zhiji 网页搜索补新 ID
   - 2 项 MISSING series（重检索失败）→ 人工补 zhiji_id
   - FETCH_FAIL = 0 项
4. **PART_OK 决策**: 6 套 PART_OK 模板**不纳入正式投产看板**，待补齐缺失 series 后升级为 FULL_OK
5. **节点验收**: 用 `node_mapping_index.csv` 核对 Framework Tree 节点映射完整性
6. **评审通过 → 合并上线**:
```bash
cd /home/ubuntu/framework-tree
git checkout main
git merge feature/v85-chart-template
git push origin main
python3 scripts/reclaim.py   # 门禁校验
```

## 4. 上线后节点访问路径

| 品种 | 页面路由 |
|---|---|
| LC 碳酸锂 (100图) | `/pages/lc/` |
| AO 氧化铝 (63图) | `/pages/ao/` |
| SI 工业硅 (48图) | `/pages/si/` |
| NI 镍 (47图) | `/pages/ni/` |
| AL 铝 (38图) | `/pages/al/` |
| SN 锡 (37图) | `/pages/sn/` |

## 5. 目录结构

```/home/ubuntu/framework-tree/analysis/e2e_output/v85/pdf_template_build/zhiji_verified_package/output/v85_chart_online_test/
├── rendered/                 333个图表HTML（FULL_OK + PART_OK告警版）
├── chart_online_render_result.md   全量渲染汇总报告
├── node_mapping_index.csv      节点-模板映射清单（前端路由用）
├── node_index.json             节点索引（结构化）
├── visual_check_result.csv     10项视觉校验+1-10星评分
├── failed_chart_list.md        渲染失败清单+原因归类
└── online_readme.md            本文档
```

## 6. 风险与遗留项

| 优先级 | 事项 | 说明 |
|---|---|---|
| P0 | 5项 INVALID zhiji_id | HTTP 500 无效ID，需人工补新ID |
| P0 | 2项 MISSING series | 重检索失败，需人工补ID |
| P1 | 6套 PART_OK 模板 | 不纳入正式投产，待补齐升级 |
| P2 | delivery_confirm.md 缺失 | DSHB交付commit未含此文件，以MD5实测替代 |
| P2 | 重检索FILLED的124项 | 模糊匹配score偏低(0.44-0.89)的映射建议人工抽检 |


---
*本文件由 HERMES V85 图表模板在线集成管线自动生成*
