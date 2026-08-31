# 交接文档：指标匹配机制修正 — 2026-08-31

## 一、核心发现

### 1. 当前分词机制存在根本缺陷

**问题代码位置**：本次对话中的匹配脚本（内联在 `execute_code` 中，未持久化到文件）

**缺陷清单**：
- 硬编码词典只有60个词，覆盖严重不足
- 单字品种名（锌/铜/铝/铅/镍/锡/硅）被 `len(t) >= 2` 过滤规则直接丢弃
- "冶炼""利润""开工"等常见产业词汇不在词典，被拆成单字后同样被丢弃
- 结果："电解锌冶炼利润" → 有效token = 空 → 匹配失败

**根本原因**：搜索策略是"在本地 `indicators_v1.json` 存量里文本匹配"，而非"调知几API实时搜索"。如果指标从未被注册过，分词再好也找不到。

### 2. 验证：正确的分词+API搜索能命中

用户指导后用分词拆解法搜"精炼锌 利润"：
```bash
~/.hermes/scripts/zhiji_api.py search "精炼锌企业利润" smm 20
```
→ 命中 `a10020636`: **SMM: 精炼锌企业生产利润（不含硫酸和小金属收益）: 日度**
→ 还有8省细分利润模型（j02871265 ~ j02871335）

---

## 二、当前各品种数据资产

### 2.1 divergence 文件（同花顺推荐）

| 品种 | 目录 | 文件数 | 状态 |
|------|------|--------|------|
| CU(铜) | `analysis/iwencai/CU/` | 30 | ✅完整 |
| AL(铝) | `analysis/iwencai/AL/` | 30 | ✅完整 |
| ZN(锌) | `analysis/iwencai/ZN/` | 30 | ✅完整 |
| NI(镍) | `analysis/iwencai/NI/` | 30 | ✅完整 |
| SN(锡) | `analysis/iwencai/SN/` | 30 | ✅完整 |
| SI(硅) | `analysis/iwencai/SI/` | 29 | ⚠️缺7.3 |
| LI(锂) | `analysis/iwencai/LI/` | 19 | ⚠️缺5.x-7.x |
| PB(铅) | `analysis/iwencai/PB/` | 0 | ❌旧diversify格式 |

每个品种30节点 × 8图表 = 240条记录，每图表含：图名称、指标列表(1-3个)、呈现形态、观测用途。

### 2.2 已注册指标（indicators_v1.json）

| 品种 | 前缀 | 已注册数 |
|------|------|----------|
| NI(镍) | ni_ | 156 |
| ZN(锌) | zn_ | ~590 (v3.43) |
| CU(铜) | cu_ | 待确认 |
| AL(铝) | al_ | 待确认 |
| PB(铅) | pb_ | 待确认 |
| SN(锡) | sn_ | 待确认 |

### 2.3 已生成的中间产物

| 文件 | 内容 | 位置 |
|------|------|------|
| 镍匹配看板HTML | 327概念指标 vs 156注册指标 | `/home/ubuntu/nickel_dashboard_gh/iwencai_full.html` |
| 镍匹配看板GitHub | 已推main分支 | `algo23-yunqingtian/nickel-dashboard` |
| 镍完整数据JSON | 240条enriched records | `/tmp/ni_divergence_enriched.json` |
| 镍匹配摘要txt | 文本版报告 | `/home/ubuntu/framework-tree/ni_match_summary.txt` |
| 镍匹配报告md | 详细匹配报告 | `/tmp/ni_match_report.md` |
| build_ni_batch.py | 镍批量重建引擎(v2, 有3个bug已修但未验证dry) | `/home/ubuntu/framework-tree/scripts/build_ni_batch.py` |

---

## 三、待办任务（按优先级）

### P0: 修正分词+搜索策略（必须先做）

**目标**：建一个通用的「同花顺概念名 → 知几API搜索 → 注册到本地」pipeline

**步骤**：
1. **分词升级**：安装jieba + 构建品种领域词典
   ```bash
   pip install jieba  # 在venv里
   ```
   词典内容：品种名(锌/铜/铝...)、交易所(SHFE/LME/COMEX)、产品(精炼锌/电解镍/不锈钢...)、指标类型(产量/开工率/利润/库存/仓单...)、地区(印尼/菲律宾/甘肃/云南...)

2. **搜索策略改**：
   - 输入：同花顺概念名（如"电解锌冶炼利润（元/吨）"）
   - 分词：精炼锌 / 冶炼 / 利润
   - **调知几API**：`zhiji_api.py search "精炼锌 冶炼 利润" smm 10`
   - 取top1结果，人工确认或自动置信度筛选
   - 注册到 `indicators_v1.json`

3. **批量跑**：对所有品种的所有概念指标执行上述流程

### P1: 逐品种重新匹配（P0完成后）

按品种优先级：
1. **ZN(锌)** — 用户当前关注
2. **NI(镍)** — 已有看板基础，需修正匹配
3. **CU/AL/SN** — 完整divergence待匹配
4. **PB(铅)** — divergence需先补生成
5. **SI/LI** — divergence不完整，需补生成

### P2: 镍看板重建（Phase 1-2-3）

见 `docs/NICKEL_SCHEMA_HANDOVER.md`，三个Phase：
1. 扩展 `indicators_v1.json` schema（5个新字段）
2. 逐节点重建30个HTML（对照divergence标准答案）
3. audit验证 + 推GitHub Pages

**注意**：P2依赖P1完成（匹配准确后再重建）

### P3: 其他品种看板

锌/铜/铝/铅/锡/硅/锂的看板重建，复用镍的pipeline。

---

## 四、关键技术细节

### 知几API调用约束
- 每轮对话最多5次API调用（缓存命中不算）
- 料服务search/series配额独立，429时用缓存兜底
- 中文查询需URL encode
- 缓存TTL: search 24h, series 1h

### 分词词典参考（需扩充）
```python
DICT_WORDS = [
    # 交易所
    "COMEX", "LME", "SHFE", "GFEX", "上期所", "广期所",
    # 产品
    "精炼锌", "电解锌", "电解镍", "精炼镍", "不锈钢", "硫酸镍",
    "高冰镍", "镍生铁", "NPI", "MHP", "镍豆", "镍铁",
    # 指标类型
    "冶炼利润", "生产利润", "开工率", "产能利用率", "加工费", "TC",
    "库存", "仓单", "注销仓单", "产量", "产能", "检修量",
    "进口量", "出口量", "进口盈亏", "持仓量", "成交量",
    # 地区
    "印尼", "菲律宾", "澳大利亚", "新喀里多尼亚",
    "甘肃", "四川", "云南", "湖南", "广西", "河南", "内蒙古", "陕西",
]
```

### build_ni_batch.py 已知状态
- v2版本，430行
- 3个bug已修复（full_years dict访问、chart_dual位置参数、latest/end字段）
- **dry run未验证**：需先运行 `python3 scripts/build_ni_batch.py --dry` 确认无误
- 归属分配逻辑：按ID前缀确定节点（ni_21_ → 2.1, ni_311_ → 3.1.1）
- 156指标已分配到28节点（2.3/3.1.5/4.2各只有1个指标，可能需要补注册）

---

## 五、用户关键指示

1. **分词必须用空格分词法**：把同花顺概念名拆成关键词，用空格分隔后去知几搜
2. **搜索必须调知几API**：不能在本地存量里文本匹配
3. **同花顺推荐的指标名称 ≠ 知几注册名**：需要建立映射关系
4. **每个品种的匹配结果要做成系统化表格**：之前承诺过但没交付
5. **PB(铅)的divergence需要补生成**：目前只有旧的diversify格式

---

## 六、文件路径速查

```
/home/ubuntu/framework-tree/
├── data/indicators_v1.json          # 指标元数据（所有品种）
├── scripts/
│   ├── build_ni_batch.py            # 镍批量重建引擎
│   ├── chart_kits.py                # 公共图表库
│   └── indicator_audit.py           # 审计工具
├── analysis/iwencai/                # 同花顺发散结果
│   ├── CU/divergence_*.md           # 铜30节点
│   ├── AL/divergence_*.md           # 铝30节点
│   ├── ZN/divergence_*.md           # 锌30节点
│   ├── NI/divergence_*.md           # 镍30节点
│   ├── SN/divergence_*.md           # 锡30节点
│   ├── SI/divergence_*.md           # 硅29节点(缺7.3)
│   ├── LI/divergence_*.md           # 锂19节点(缺5-7章)
│   └── PB/                          # 铅(旧格式，需补)
├── docs/
│   ├── NICKEL_SCHEMA_HANDOVER.md    # 镍看板重建交接文档
│   ├── NI_FULL_MATRIX.md            # 镍指标完整矩阵
│   └── HANDOVER_20260831_INDICATOR_MATCH.md  # 本文档
└── ni_match_dashboard.html          # 镍匹配看板(本地)

/home/ubuntu/nickel_dashboard_gh/
├── iwencai_full.html                # 镍匹配看板(GitHub Pages)
└── ...

/home/ubuntu/scripts/zhiji_api.py    # 知几API客户端(实际在~/.hermes/scripts/)
```

---

## 七、新对话启动指令

```
请读取交接文档 /home/ubuntu/framework-tree/docs/HANDOVER_20260831_INDICATOR_MATCH.md，
然后从P0开始：修正分词机制，用jieba+领域词典分词，
对锌(ZN)的所有divergence概念指标调知几API搜索，
建立完整的「同花顺概念名 → 知几ID → 注册名」映射表。
```
