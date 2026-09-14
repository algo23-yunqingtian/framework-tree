# 回执：chart_registry 系统性修复完成

**日期**: 2026-09-13
**分支**: indicator-correction-win
**Commit**: 6167792

## 任务完成情况

| 任务 | 状态 | 说明 |
|------|------|------|
| A1: 修复 parse_node_code 正则 | ✅ | 正则改为 lookahead 兜底，chart 提取 652→1379 |
| A1: filename_to_info 识别聚合页/首页 | ✅ | 新增 sector_aggregate/home 页面类型分类 |
| B1: 327条串台核验 | ✅ | 12条规则误报 + 56条真实错放全部修复 |
| C1: chart_dual 消歧过滤 A vs A | ✅ | disambig_title 增加 mid_a==mid_b 过滤 + 兜底标签 |
| D1: 49条异常条目修复 | ✅ | 🔴=68→0，KEYWORD_RULES 精简重排 |
| E1/F1: PAGE_MAP 补全 52孤岛页 | ✅ | 34条板块聚合页+品种首页映射已录入 |

## 修复后数据

- **总图表**: 1379 张 (原 652)
- **✅ 归属正确**: 455
- **🟢 无关键词命中**: 102 (待人工确认)
- **🔴 异常**: 0 (原 68)
- **⚪ 设计意图**: 822 (聚合页/首页跨板块引用)
- **覆盖率**: 100% (1379/1379)

## 修改文件

1. `scripts/build_chart_registry.py` — v2.0 重写
   - 正则修复 + 页面类型分类 + 关键词精简 + judge_placement 优化
2. `scripts/chart_kits.py` — disambig_title 增强
   - mid_a==mid_b 过滤 + 三级兜底标签
3. `index.html` — PAGE_MAP 补全 34 条
4. `data/chart_registry.json` — 重新生成
5. `docs/CHART_REGISTRY.md` — 重新生成
6. `docs/Coverage_Report.md` — 新增覆盖率报告

## 关键修复点

1. **正则**: 原 primary 正则 `<div class="chart">(.*?)</div>\s*</div>\s*</div>` 仅捕获部分 chart 块 → 改为 `<div class="chart">(.*?)(?=<div class="chart">|<div class="note">|$)`
2. **关键词**: 移除过宽关键词("电解铝"/"多晶硅"/"电池级")，新增上下文限定规则
3. **judge_placement**: "主图"跨板块改为设计意图(⚪)，仅"正主"跨板块为异常(🔴)
4. **disambig_title**: 新增 mid_a==mid_b 返回 None 过滤自身对比

---

*等待爱马仕复审审计*
