# 模板字段适配文档：DSHB 交付格式 ↔ chart_template_schema.json

> 工单: `HERMES_V85_ARTIFICIAL_REVIEW_PREP`  
> 生成时间: 2026-09-30 13:52:59  
> 适配实现: `t22_render_online.py::adapt_template()`  
> ⚠️ **本文档为模板输出对齐规范，后续 DSHB 模板输出应直接对齐本文档 §4「目标规范」，避免再次出现字段不匹配。**

## 1. 问题背景

DSHB 交付的 `pdf_web_chart_template_hermes_ready.json` 与本仓库前置框架开发的 `chart_template_schema.json` **字段命名体系完全不同**，无法直接渲染。首次接入时因此阻塞，需编写适配层。本文档固化映射规则，使后续模板可直接对齐。

## 2. 顶层结构映射

| 语义 | DSHB 交付字段 | schema 目标字段 | 备注 |
|---|---|---|---|
| 模板唯一ID | `template_id` | `chart_id` | 命名不同，语义等价 |
| 模板版本 | `version` | `version` | 一致 (v85) |
| 图表标题 | `source.chart_title` | `title` | **DSHB 嵌套在 source 下** |
| 品种代码 | `variety` | `meta.variety` | **DSHB 顶层平铺，schema 在 meta 下** |
| 图表类型 | `chart_type` | `meta.chart_type` | DSHB 中文枚举 |
| 模板状态 | `metadata.verify_status` | `meta.status` | **枚举值完全不同** |
| 时间戳 | `metadata.verify_timestamp` | `meta.timestamp` | ISO8601 |

## 3. 逐字段映射明细

| # | DSHB 实际字段 | schema 字段 | 转换规则 | 陷阱说明 |
|---|---|---|---|---|
| 1 | `template_id` | `chart_id` | 直接映射 | 如 `TPL-AO-001` |
| 2 | `metadata.verify_status` | `meta.status` | `FULL_OK`→`released`, `PART_OK`→`warning` | **`metadata.status` 恒为 `draft`，不可用！** |
| 3 | `source.chart_title` | `title` | 直接映射 | 为空时降级为「未命名图表」 |
| 4 | `source.file` | `meta.source_file` | 直接映射 | PDF 文件名，用于页脚标注 |
| 5 | `source.page` | `meta.source_page` | 直接映射 | PDF 页码 |
| 6 | `source.chart_local_id` | `meta.chart_local_id` | 直接映射 | 如 `chart_01` |
| 7 | `variety` | `meta.variety` | 直接映射 + 查表取中文名/颜色 | AO/CU/AL/PB/ZN/NI/SN/SI/LC |
| 8 | `chart_type` | `meta.chart_type` | 中文枚举 → 渲染策略映射 | 单折线/多折线/堆叠柱状/复合混合(折线+柱状) |
| 9 | `axis.left.unit` | `y_axis.left.unit` | 直接映射 | 坐标轴单位 |
| 10 | `axis.right.unit` | `y_axis.right.unit` | 直接映射 | 可为 null |
| 11 | `series[].name` | `series[].name` | 直接映射 | 图例名称 |
| 12 | `series[].indicator_key` | `series[].indicator_key` | 直接映射 | 如 `wr34`，INVALID项常保留 |
| 13 | `series[].zhiji_id` | `series[].zhiji_id` | 直接映射 | **INVALID/MISSING 项此字段为 null（原 ID 已被清空）** |
| 14 | `series[].unit` | `series[].unit` | 直接映射，缺失时回退 `axis.left.unit` | 三级回退 |
| 15 | `series[].axis` | `series[].y_axis` | `left`/`right` 同义 | **字段名不同: DSHB `axis` vs schema `y_axis`** |
| 16 | `series[].line_type` | `series[].style.line_type` | solid/dashed/dotted/dash_dot → ECharts lineStyle.type | dash_dot 需转数组 `[8,4,2,4]` |
| 17 | `series[].color` | `series[].style.color` | 直接映射 | 缺失时回退品种主题色 |
| 18 | `series[].symbol` | `series[].style.symbol` | 直接映射 | circle/rect/diamond/triangle/none |
| 19 | `series[].verify_status` | `series[].status` | VALID/FILLED/INVALID/MISSING 四态 | **INVALID/MISSING 必须跳过渲染并告警** |
| 20 | `series[].verify_note` | `series[].note` | 直接映射 | **承载原始错误原因**（如 `API错误: HTTP 500`、`未找到候选ID`） |
| 21 | `layout.legend.position` | `legend.position` | 直接映射 | top/bottom/left/right |
| 22 | `metadata.notes` | `meta.notes` | 直接映射 | 恒为 draft 提示，无信息量 |

### 3.1 推导字段（DSHB 无对应字段，需运行时计算）

| schema 字段 | 推导规则 |
|---|---|
| `series[].plot_type` | 由 `chart_type` 决定: 堆叠柱状→全 `bar`; 复合混合→首个 `line` 其余 `bar`; 其余→`line` |
| `use_dual_axis` | `any(series.axis=='right')` OR `chart_type in (复合混合, 双Y轴)` |
| `series[].stack` | `chart_type=='堆叠柱状'` AND 该 series 有数据 |
| `node_code` | 按标题关键词推断业务节点: 价/升贴水/溢价→价格; 库存→库存; 产量/开工率→供给; 利润→成本利润; 消费→需求; 出口/进口→进出口; 持仓→资金 |

## 4. 目标规范（后续 DSHB 模板输出应对齐）

```json
{
  "chart_id": "TPL-AO-001",            // ← 原 template_id
  "title": "三网均价-内蒙古",           // ← 原 source.chart_title (提至顶层)
  "meta": {                              // ← 原品种/类型/状态集中到 meta
    "variety": "AO",
    "chart_type": "单折线",
    "status": "released",              // ← 原 metadata.verify_status, 枚举转换
    "source_file": "氧化铝周报20260830.pdf",
    "source_page": 6,
    "chart_local_id": "chart_01",
    "timestamp": "2026-09-30T11:13:50+08:00"
  },
  "y_axis": {                            // ← 原 axis 改名
    "left":  {"unit": "元/吨"},
    "right": null
  },
  "legend": {"position": "top"},      // ← 原 layout.legend.position 提平
  "series": [{
    "name": "三网均价-内蒙古",
    "indicator_key": "wr34",
    "zhiji_id": "ID01721686",
    "y_axis": "left",                  // ← 原 axis 改名
    "unit": "元/吨",
    "plot_type": "line",               // ← 新增，明确渲染类型
    "style": {"color": "#5470c6", "line_type": "solid", "symbol": "circle"},
    "status": "valid",                 // ← 原 verify_status 小写化
    "note": "氧化铝：长单均价：内蒙古（月）"
  }]
}
```

## 5. 状态枚举转换表

| 层级 | DSHB 枚举 | schema 枚举 | 渲染行为 |
|---|---|---|---|
| 模板 | `FULL_OK` | `released` | 全量渲染 |
| 模板 | `PART_OK` | `warning` | 渲染 + 红色告警条 + 禁止投产标记 |
| 模板 | `metadata.status='draft'` | — | **忽略（DSHB 恒为 draft，无信息量）** |
| series | `VALID` | `valid` | 正常渲染 |
| series | `FILLED` | `filled` | 正常渲染（但需抽检口径） |
| series | `INVALID` | `invalid` | 跳过渲染 + 红色虚线占位 + 明细告警 |
| series | `MISSING` | `missing` | 跳过渲染 + 红色虚线占位 + 明细告警 |

## 6. 关键陷阱（必读）

1. **`metadata.status` ≠ `metadata.verify_status`**: DSHB 模板的 `metadata.status` **恒为 `"draft"`**（硬编码提示语），真正的校验状态在 `metadata.verify_status`。首次接入误用前者导致全部模板被判为草稿。

2. **INVALID/MISSING series 的 `zhiji_id` 是 `null`**: 原 zhiji_id 已被 DSHB 清空，**无法从 JSON 直接获取原 ID**（原 ID 仅记录在 `hermes_readme.md §6` 表格中）。错误原因保留在 `verify_note`。

3. **唯一可拉取 ID 为 248 而非 252**: 362 series 去重后 VALID+FILLED 唯一 ID 248 个；5 INVALID + 2 MISSING 均为 null，不占 ID 计数。

4. **`chart_type` 为中文枚举**: 必须经映射表转渲染策略，不可直接传 ECharts。

5. **单位三级回退**: `series.unit` → `axis.left.unit` → `"数值"`，部分 series 无 unit 字段。

6. **品种仅 6 个**: DSHB 实际交付 LC/AO/SI/AL/SN/NI，**无 CU（铜）/PB（铅）**，与 9 品种配置有差异，节点索引按实际 6 品种生成。

## 7. 适配实现与验证

| 项 | 值 |
|---|---|
| 适配函数 | `t22_render_online.py::adapt_template()` |
| 拉取脚本 | `t21_fetch_zhiji.py`（1s 限速 + 断点续跑） |
| 模板包 MD5 | `92371c0a` (pdf_web_chart_template_hermes_ready.json) |
| 校验统计 MD5 | `dba27ff4` (zhiji_verify_stat.csv) |
| 模板数 | 333（FULL_OK 327 / PART_OK 6） |
| series 数 | 362（VALID 231 / FILLED 124 / INVALID 5 / MISSING 2） |
| 渲染成功 | 328/333 |

## 8. 后续模板输出对齐要求

1. **字段命名**: 直接采用 §4 目标规范的字段名，不再使用 `template_id`/`axis`/`layout.legend`
2. **状态集中**: 品种、图表类型、状态、来源统一放入 `meta` 对象
3. **状态枚举**: 使用 `released`/`warning` 与 `valid`/`filled`/`invalid`/`missing`
4. **保留原 ID**: INVALID/MISSING series **必须保留 `original_zhiji_id` 字段**，供人工查找备选指标（本次交付因清空原 ID 增加排查成本）
5. **记录匹配分数**: FILLED 系列应保留 `match_score` 与 `match_source` 字段
6. **plot_type 显式声明**: 不再依赖 `chart_type` 推断单系列类型
