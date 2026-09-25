# HERMES 预检报告 · 工单 HERMES_PRECHECK_20260924

- **预检时间**：2026-09-24
- **模式**：全程只读（未 checkout、未改任何仓库文件/分支/指标库/task_queue 回执）
- **前置工单**：`HERMES_AUDIT_HIST_IND_20260924` → ⛔ BLOCK 驳回
- **审计基线**：`origin/main @ 404f7ee`（2026-09-13 16:47）
- **被审分支**：`origin/indicator-correction-win @ 5e4efe8`（2026-09-14 09:28）
- **预检结论**：驳回主干结论 **维持成立**；但发现 **2 项需修正的事实性错误 + 1 项风险降级 + 4 项新增风险**

---

## 一、回执检索复核结论（任务 1）

### 1.1 🔴 上一轮检索存在范围遗漏（已修正）

上一轮只在**本地 main checkout** 执行了 `grep`：
```
grep -rl "自检回执\|交接自检\|新DSH-B" ~/framework-tree/task_queue/ docs/ output/
```
**遗漏了 win 分支内的文件**（`git ls-tree` 可查，未 checkout 故 grep 扫不到）。补扫 win 分支 `task_queue/` 全量 15 个文件后，发现 **2 份 Dsharnes-B 正式回执**是上一轮未见的：

| 回执 | 分支归属 | 内容性质 |
|---|---|---|
| `RECEIPT-ROLE-DEF-FIX-20260913.md` | **win 独有** | 任务回执：DSHARNES_B_ROLE_DEF v1.0→v1.1（R1/R2/G1/G2 四项对齐） |
| `RECEIPT-PB-EXEC-20260913.md` | **win 独有** | 任务回执：PB_EXEC_TASK 执行完成（27 份 correction → 62 条 A 级入库，v3.48→v3.49，check_html 223/223 + verify_render 224/224 ALL PASS） |

另 win 独有 1 份中文回执 `TASK_RECEIPT_角色设定_20260913.md` 及 3 份复审报告（`REVIEW_SECONDARY_FIX_PENDING`、`REVIEW_267614D_F1F3_U1U4`、`REVIEW_5CD6DA3_F3U2U4`）。

### 1.2 但：回执类型不等于「交接自检回执」

逐一读取 win 上全部 11 份 feedback 文件正文后确认——

> **没有一份文件包含"交接自检""自检回执""新DSH-B"这三个关键词之一。**

| 关键词 | win 分支命中 | main/本地命中 |
|---|---|---|
| 交接自检 | **0** | 0 |
| 自检回执 | **0** | 0 |
| 新DSH-B | **0** | 0 |

win 上的 2 份回执是**单任务执行回执**（角色定义修订回执、PB 执行任务回执），均不含工单要求的三项内容：**① 新旧 DSH-B 节点切换范围 ② 原始素材清单 ③ 业务清洗规则清单**。

### 1.3 结论

**工单目标 1 的前置条件仍未达成。** 上一轮"回执完全不存在"的表述**不准确**（win 上存在 2 份 DSH-B 回执），但"工单所需的【交接自检回执】不存在"**准确**。

**判定**：暂停理由从"回执缺失"修正为"回执类型不匹配 + 无节点切换声明"——两者都支持暂停，但性质不同：前者是失联，后者是**交付物不合规**。

---

## 二、i* / pb_ 两套 ID 体系差异清单（任务 2）

### 2.1 🔴 上一轮"口径风险"描述错误，需更正

上一轮表述：
> "win 的 61 条 PB 新 A 级指标用的是 `i*` 旧编号，与 main 的 `pb_` 前缀是**两套命名体系**——不是假阳性匹配，而是新旧命名体系并存且未做主键交集核验。"

**该描述方向错误。** 实测核查结果：

| 核验项 | 结果 |
|---|---|
| main `pb_` 前缀条目 | **70 条**，zhiji_id 70 个 distinct |
| win `i*` 纯数字编号条目 | **41 条**，zhiji_id 40 个 distinct |
| **两套 zhiji_id 交集** | **0** |
| 名称精确匹配 `i*` ↔ `pb_` | **0** |
| win 内是否存在 `pb_` 作为指标 key | **0** |

**实际关系不是"同一批数据的两套命名"，而是"两个完全不相交的新增序列集合"。** win 的 `i*` 序列在 main 上**根本不存在**（不是被重命名，而是从未入库）。

### 2.2 i* → pb_ 待映射清单

**映射需求 = 0 条。** 41 条 `i*` 全部需要**新建** `pb_` 前缀 key，无法通过重命名完成。按 41 条 `i*` 的实际品种分布，其中属于铅（PB）的条目为 `i1–i41` 全量（name 全部含"铅"，见下表节选）：

| i* | 指标名（节选） | 建议归属节点 |
|---|---|---|
| i1 | LME铅库存 | 4.1 |
| i2 | SHFE铅仓单 | 4.1 |
| i3 | SMM铅锭五地社库 | 4.3 |
| i17 | 中国海关铅锭进口量 | 6.2 |
| i19–i25 | LME铅新加坡注册/注销/出入库 | 6.4 |
| i29 | LME铅库存_仁川 | 6.4 |
| i30 | LME铅非注册仓单_迪拜 | 6.4 |
| i32–i36 | SMM五地社库分省（广东/江苏/浙江/天津/上海） | 4.3 |
| i37–i39 | 中国海关铅蓄电池出口（总量/起动型/累计） | 6.3 |
| i40 | 中国海关铅精矿进口量 | 6.1 |
| i41 | 中国海关铅锭出口量 | 6.2 |

⚠️ **注意**：main 上 70 条 `pb_` 已有大量同类指标（如 `pb_62_plate_import`、`pb_63_battery_import`、`pb_63_plate_export`、`pb_72_waste_battery`）。虽 zhiji_id 不重叠，但**语义高度邻近**——`i17`（海关铅锭进口）vs main `pb_62_plate_import`（铅锭进口）属不同 zhiji 序列还是同序列不同口径，**必须由 DSH-B 在交接回执中给出映射判定**，无法仅凭 ID 判定。

### 2.3 别名字段隐藏 `pb_` 前缀检查

全量扫描 win JSON 所有字符串字段中的 `pb_` 子串，命中 **5 处**，**全部位于 `_meta.change` 元数据文本**，非指标 key、非别名字段：

```
第 27 行 "change": "看板统一：旧版产物(pb_stock.html/demo/build_pb_stock.py)归档至
legacy/20260826_pb_stock_v1/；当前唯一最新版 = pb_stock_v2.html (22图) + pb_..."
```

命中值：`pb_stock`、`pb_stock_v1`、`pb_stock_v2`、`pb_41_stock`。
→ **无隐藏 `pb_` 指标 ID。**

⚠️ **但发现遗留缺陷复现**：`pb_stock_v2` 出现在该文本中，与既有 skill 记录的遗留缺陷 `pb_stock_v2` 一致——win 分支仍保有 `legacy/20260826_pb_stock_v1/` 归档说明，说明**旧版 PB 产物迁移链路在 win 侧是活跃的**。

### 2.4 🔴 新增风险：win 指标 key 命名规范严重失控

win 的 1025 条指标 key 中：

| 类别 | 数量 | 示例 |
|---|---|---|
| 标准 ASCII 小写下划线 | 956 | `zn_21_close_front` |
| 含中文的 key | **68** | `zn_3_1_1_全球锌矿产量_年`、`zn_6_2_沪伦比与精锌进口盈亏`、`sn_2_3_lme锡现货现金价时序图` |
| 纯中文裸 key | **7** | `主连`、`LME库存`、`SHFE库存`、`社库`、`TC`、`精炼产量`、`表观消费`、`开工率` |

**7 个纯中文裸 key 是数据污染**：`主连`、`社库`、`开工率`、`TC` 这类通用词作为全局字典 key，任何后续查询/注册都会产生不可预测冲突，且无法承载品种维度（"铅开工率"和"锌开工率"会撞名）。

**3 条 `ids` 缺失条目**：win 有 23 条带 `zhiji_id` 字段、1002 条带 `ids`，即 **23 条指标无有效知几 ID**（无法拉数）。

**62 条 key 含 `图表`/`时序图` 字样**：如 `sn_2_3_lme锡现货现金价时序图`、`sn_2_3_lme锡期货收盘价时序图`、`sn_7_3_锡精矿价格时序图`——**图表名混入指标 key**（同花顺质量问题在指标注册层未被清洗）。

⚠️ 其中一条已确认**真错配**：
```
sn_2_3_lme锡现货现金价时序图 → name: IMEA：大豆：现货价：锡诺普（日）
sn_7_3_锡矿进口到岸价 → name: USGS：锡矿：含锡：产量：全球（年）
al_2__上期所仓单 → name: USGS：粗铝：进口数量：美国（年）
al_7_3_煤_电传导 → name: USGS：混杂低含量铜颗粒的铝：均价：美国（月）
ni_4_4_电解镍厂库存 → name: 电解镍：Ni≥99.96%，大板：出厂价：金昌：金川集团（日）
```
key 声明的品种/指标 与 `name` 字段实际序列**完全无关**。这是工单点名的"同名指标、不同口径造成假阳性匹配"的**真实实例**——但发生在 **win 分支既有存量**中，非本次 62 条新增。

---

## 三、main 附属指标业务属性判定（任务 3）

### 3.1 main 顶层结构

| 层级 | 条目 | 类型 |
|---|---|---|
| `_main_metric` | dict，120 条 | 系统配置元数据 |
| `_meta` | dict | 系统配置元数据 |
| `version` / `change` / `changelog` / `updated` | 4 条纯标量 | 系统配置元数据 |
| **业务指标条目** | **1580 条** | 业务指标 |
| 　├ `wr*` | 276 条 | 业务指标（周报系列） |
| 　└ 其他 | 1304 条 | 业务指标 |

### 3.2 `_main_metric`（120 条）判定

| 项 | 判定 |
|---|---|
| 业务属性 | **系统配置元数据**——非指标数据，是"页面主图选择"的映射表（页面节点 → 指标 key） |
| 是否可迁移 | **不可迁移，必须保留** |
| 合并风险 | win 分支**无此字段** → 合并后 120 条主图映射整体丢失 |
| 后果 | 所有依赖 `_main_metric` 的页面将回退兜底逻辑（取字典序第一个日频指标） |

⚠️ 这是**已知反复出问题的防线**。历史已多次因此串台：改 JSON `_main_metric` 但 `build_5m_batch.py` 硬编码块静默覆盖（根因 F）；`_main_metric` 指向无缓存指标被过滤后兜底取收盘价当主图（幽灵正主陷阱）。**该字段是串台防线的最后一道闸，丢失即全线失守。**

### 3.3 `wr*`（276 条）判定

| 项 | 判定 |
|---|---|
| 业务属性 | **业务指标**——真实周报指标序列，276 条 |
| verified 分布 | verified=True **86 条**（31.2%）/ verified=False **190 条** |
| 190 条未验证根因 | 全部为 SMM 上游凭据失效（182 条）或数据陈旧（7 条），非未清洗 |
| 是否可迁移 | **必须保留** |
| 合并风险 | win 分支**无 wr*** → 合并后 276 条 + 已上线 24 个周报页面数据源整体丢失 |

**判定：`_main_metric`(120) + `wr*`(276) = 396 条** 属"合并即丢失"类别，其中 120 条是系统配置、276 条是已上线业务的真实数据源。

### 3.4 main 1580 条业务指标分类统计

| 维度 | 结果 |
|---|---|
| **软删除/废弃/封存标记** | **0 条**（扫描 delete/archive/legacy/deprecated/disabled/removed/废弃/封存/软删/归档 共 10 个关键词） |
| verified=True | 1267 条（80.2%） |
| verified=False | 313 条（19.8%）—— `wr*` 占 190、非 `wr*` 占 123 |
| 含中文的 key | 7 条（`主连`/`LME库存`/`SHFE库存`/`社库`/`精炼产量`/`表观消费`/`开工率`） |
| 状态类字段 | `_nodes` 1205 条 / `_origin` 1182 条 / `_tier` 1042 条 / `_verified_by` 424 条 / `note` 30 条 / `_derived` 3 条 |

**结论：main 1580 条业务指标中无软删除/废弃封存条目。** 313 条 verified=False 属"上游凭据失效"而非"废弃"，属可激活资产（SMM 凭据修复后可补跑）。

⚠️ **上一轮表述修正**：上一轮称"main 1584 条"，实测**业务指标 1580 条** + 2 条 `_` 元数据 + 4 条纯标量元数据 = **1586 条顶层键**。"1584"是排除 `_` 前缀后的数字，**非业务指标数**。精确口径：**1580 条业务指标**。

⚠️ **main 也有 7 条中文裸 key 污染**（与 win 相同 7 条）——此污染源自更早期，非本次引入，但说明**命名规范从未执行**。

---

## 四、分支分叉校验结果 + 双分支文件哈希快照（任务 4）

### 4.1 merge-base 关系复核

| 项 | 值 |
|---|---|
| `origin/main` HEAD | `404f7ee963f279becbee60119ba8aeadafdb5f58` |
| `origin/indicator-correction-win` HEAD | `5e4efe8d6ce046159fd42f7c09c7f2a863c9bd3d` |
| **merge-base（分叉起始 commit）** | **`f73bccbc59b8aa24448c9468815c6d86be658e7b`** |
| 分叉时间 | **2026-09-02 12:59:56 +0800** |
| 分叉起始 commit 主题 | `[Txx] P1 v3: CU价格信号v4(9A) SN成本利润v3(5A) CU供给fix(21A) + 注册4指标 v3.48` |
| `git merge-base --is-ancestor win main` | **exit=1**（win 不是 main 祖先）✅ 上一轮结论正确 |

### 4.2 分叉提交计数复核

| 方向 | 计数 | 上一轮记录 | 是否准确 |
|---|---|---|---|
| main 有、win 无 | **145** | 145 | ✅ 准确 |
| win 有、main 无 | **16** | 16 | ✅ 准确 |

### 4.3 双分支 `indicators_v1.json` 文件哈希快照

```
origin/main  @ 404f7ee  data/indicators_v1.json
  sha256 = 960e15292c13dfe01df597df2ece8f3671bb08b70d5e6c9e536bfc765b93f2c8
  业务指标 1580 条 / flat-dict 结构 / version=v3.83

origin/indicator-correction-win @ 5e4efe8  data/indicators_v1.json
  sha256 = 2aeda1ea28316d34cb2776fdb20d5b3677191e29f13e18ade1b55cf00e9ede8a
  业务指标 1025 条 / 包装结构(含 indicators 子字典) / version=v3.50
```

### 4.4 🔴 新增风险：分叉方向性错误

win 的 16 个提交中，**最新的 2 个（`fb49d34` PB 修正注册、`5e4efe8` merge 解决）恰好是 PB 指标写入提交**，且这两提交都建立在 `f73bccb`（09-02 v3.48）这个**旧包装结构基线**上。

main 侧 145 个提交中，关键结构演进节点：
- `42401e2`（09-08）：新增氧化铝 AO 独立品种节点 → tree_config 加 ao + 13 子节点
- `e770ce8`：外部源补充数据协作任务卡（agent-B 跨服务器提交指南）
- `d79010e`（09-09）：周报指标框架树导入，518→205 键，v3.75→v3.76
- `f312cb8`（09-09）：周报指标清洗入库，205→276 条，1585 键，v3.77
- `bd2aa2a`（09-09）：**合并 task/p0_verify + task/wr_unit_backfill → v3.83**，85 冲突块取我方 freq 实测值
- `2c26719`：wr 周报图拼接到常规页
- `69033ba`：wr* 指标缺口审计，verified 87 条 / 未 verified 189 条

**结论**：main 侧已历经**结构重构 + 276 条 wr 导入 + 多轮合并冲突解决**，而 win 停在重构前的 v3.48 包装结构。win 的 PB 修正在**已被 main 抛弃的结构**上完成，重做（而非合并）是唯一可行路径。

---

## 五、预生成审计核验模板（任务 5）

以下三类校验规则已固化，供 DSH-B 完成 rebase 后重新提交时直接复算。

### 5.1 zhji_id 主键唯一性校验规则

```python
# 规则 R-ZHIJI-1：全库 zhiji_id 唯一性
# 采集范围：所有指标条目的 ids 字段（dict→扁平化 + list→展开）+ zhiji_id 字段
def collect_ids(indicators: dict) -> dict[str, list[str]]:
    """返回 {zhiji_id: [key1, key2, ...]}，len>1 即冲突"""
    m = {}
    for k, v in indicators.items():
        if not isinstance(v, dict): continue
        ids = set()
        x = v.get('ids')
        if isinstance(x, dict):
            for a, b in x.items():
                if isinstance(b, (list, tuple)): ids.update(str(t) for t in b)
                elif b: ids.add(str(b))
        elif isinstance(x, list):
            ids.update(str(t) for t in x)
        elif x: ids.add(str(x))
        if v.get('zhiji_id'): ids.add(str(v['zhiji_id']))
        for i in ids: m.setdefault(i, []).append(k)
    return m

# 验收式：conflicts = {z: ks for z, ks in collect_ids(ind).items() if len(ks) > 1}
# 通过标准：len(conflicts) == 0
# 已知：main pb_ ↔ win i* zhiji_id 交集 = 0（本次预检实测）
```

**⚠️ 当前基线缺陷**：win 上有 23 条指标无有效 zhiji_id（`ids` 缺失），这 23 条会被上述规则静默放过（无 ID 无法参与唯一性校验），**必须单独统计**——见 R-ZHIJI-2。

```python
# 规则 R-ZHIJI-2：无 ID 条目清点（不可静默放过）
def no_id_entries(indicators: dict) -> list[str]:
    return [k for k, v in indicators.items()
            if isinstance(v, dict)
            and not v.get('ids') and not v.get('zhiji_id')]
# 验收式：len(no_id_entries(ind)) == 0
# 已知：win = 23 条（阻断项）；main 需重新核定
```

### 5.2 JSON 结构合规校验项

```python
# 规则 R-STRUCT-1：顶层结构必须是 flat-dict（main 现行规范）
# 通过标准：指标条目直接为顶层 key，不存在顶层 'indicators' 子字典
assert 'indicators' not in d, '旧包装结构，必须 rebase 到 flat-dict'

# 规则 R-STRUCT-2：必备元数据字段
REQUIRED_TOP = ['version', 'updated', '_main_metric']
# 验收式：all(k in d for k in REQUIRED_TOP)
# 已知：win 缺失 _main_metric（120 条主图映射），属阻断项

# 规则 R-STRUCT-3：指标条目必备字段
REQUIRED_ENTRY = ['name', 'unit', 'freq', 'ids']
# 验收式：每条业务指标条目必须含以上 4 字段，缺失即不合格

# 规则 R-STRUCT-4：key 命名规范
import re
KEY_PATTERN = re.compile(r'^[a-z]{2,3}_[0-9]{2,4}_[a-z0-9_]+$')
# 说明：{品种2-3字母}_{节点号2-4位}_{语义下划线}
# 验收式：每条 key 必须匹配 KEY_PATTERN
# 已知违规：win 68 条含中文 key + 7 条纯中文裸 key = 75 条违规（5.37%）

# 规则 R-STRUCT-5：key 禁止包含图表形态词
CHART_WORDS = ['时序图', '图表', '季节图', '柱状图', '折线图', '趋势图']
# 验收式：key 不得含任一 CHART_WORDS 子串
# 已知违规：win 62 条（如 sn_2_3_lme锡现货现金价时序图）

# 规则 R-STRUCT-6：key 声明品种必须与 name 实际序列一致
VARIETY_WORDS = {'cu':'铜','al':'铝','zn':'锌','ni':'镍','sn':'锡','si':'硅','li':'锂','pb':'铅','ao':'氧化铝'}
# 验收式：key 前缀品种词 ∈ name，或 name ∈ key 声明的品种范围
# 已知违规：win 至少 5 条真错配（sn_2_3_lme锡现货现金价时序图→IMEA大豆；
#          al_2__上期所仓单→USGS粗铝美国；ni_4_4_电解镍厂库存→电解镍出厂价；
#          al_7_3_煤_电传导→USGS混杂铜颗粒铝；sn_7_3_锡矿进口到岸价→USGS锡矿产量）
```

### 5.3 ID 前缀规范校验规则

```python
# 规则 R-PREFIX-1：品种前缀白名单（9 品种）
ALLOWED_PREFIX = {'cu','al','zn','ni','sn','si','li','pb','ao'}
# 验收式：key.split('_')[0] ∈ ALLOWED_PREFIX
# 违规即需人工判定：是否新种类（如 co=钴）应补入白名单，还是错误前缀

# 规则 R-PREFIX-2：禁止多命名体系并存
# 同一品种禁止同时存在 {品种}_前缀 和 {字母}{数字} 编号体系
# 已知：main pb_(70) 与 win i*(41) 无 zhiji_id 交集 → 非重命名，是新增
#      → 合并前必须全部转为 pb_ 前缀，不得保留 i* 编号

# 规则 R-PREFIX-3：i*/j* 编号仅允许存量遗留
# 说明：main 现有 j*(50) 为铅历史编号（j21/j22/j24 等），属遗留资产
#      新增指标必须使用 {品种}_{节点}_{语义} 格式
# 验收式：新增条目的 key 必须匹配 KEY_PATTERN（R-STRUCT-4）

# 规则 R-PREFIX-4：pb_ 语义邻近条目必须人工判定
# 说明：zhiji_id 不重叠 ≠ 语义不重叠
# 已知：main pb_62_plate_import ↔ win i17 中国海关铅锭进口量
#      必须人工判定"是否同一序列的不同口径"（假阳性高风险区）
# 验收式：DSH-B 提交映射表时，语义邻近对必须逐条给出判定理由

# 规则 R-PREFIX-5：跨品种序列误归类扫描
# 验收式：对每条 key，若 VARIETY_WORDS[key_prefix] 不在 name 中，
#         且 name 含其他品种词 → 标记为误归类嫌疑，需人工复核
# 已知：win sn_2_3_lme锡现货现金价时序图 → IMEA大豆（跨到大豆）
```

---

## 六、预检汇总：与上一轮驳回结论的差异

### 6.1 上一轮结论维持成立的项

| # | 结论 | 复核结果 |
|---|---|---|
| R1 | win 非 main 祖先，双向分叉 145↔16 | ✅ 精确复核：145 / 16，exit=1 |
| R2 | win 旧包装结构 vs main flat-dict，合并将丢失数据 | ✅ 复核成立 |
| R3 | `_main_metric`(120) + `wr*`(276) 合并即丢失 | ✅ 复核成立，共 396 条 |
| R4 | 分叉起始 commit = `f73bccb`（2026-09-02 v3.48） | ✅ 已定位 |
| R5 | 交接自检回执未送达，工单前置条件未达成 | ✅ 成立（但需修正表述，见下） |

### 6.2 🔴 上一轮错误，需更正的项

| # | 上一轮表述 | 实测修正 | 影响 |
|---|---|---|---|
| E1 | "交接自检回执**完全不存在**" | **不准确**。win 分支存在 2 份 DSH-B 正式回执（`RECEIPT-ROLE-DEF-FIX`、`RECEIPT-PB-EXEC`），但均**不是工单要求的交接自检回执类型** | 暂停理由修正为"回执类型不匹配"，性质从"失联"改为"交付物不合规" |
| E2 | "win 61 条 PB 新指标用 `i*` 旧编号，与 main `pb_` 是**两套命名体系**——非假阳性匹配，而是新旧命名体系并存" | **方向错误**。实测 pb_ ↔ i* zhiji_id 交集 = **0**，名称精确匹配 = **0**。两者是**无重叠的不同序列集合**，`i*` 序列在 main 上从未存在，非"被重命名"而是"从未入库" | 任务从"命名统一"变为"全量新建 key"，映射需求 = 0 条 |
| E3 | "main 1584 条" | **口径不精确**。1584 = 排除 `_` 前缀的顶层键数；**业务指标实际 1580 条**（1586 顶层 − 2 条 `_` 元数据 − 4 条纯标量） | 后续核验必须以 1580 为业务指标基线 |

### 6.3 🟡 风险降级项

| # | 上一轮定级 | 预检后修正 | 依据 |
|---|---|---|---|
| R5（口径一致性） | 🟡 待核 | 🟢 **降级** | zhiji_id 交集 = 0，不存在假阳性匹配；但语义邻近对（`pb_62_plate_import` ↔ `i17`）仍需人工判定，保留 🟡 子项 |

### 6.4 🔴 预检新增风险项

| # | 新增风险 | 严重度 | 类型 |
|---|---|---|---|
| N1 | win 68 条含中文 key + 7 条纯中文裸 key（`主连`/`社库`/`开工率`/`TC`）→ 全局字典污染，无法承载品种维度 | 🔴 阻断 | 命名规范 |
| N2 | win 62 条 key 含"时序图/图表"字样（图表名混入指标 key，同花顺质量问题未清洗） | 🟡 待核 | 命名规范 |
| N3 | win 至少 5 条 key-name **真错配**（`sn_2_3_lme锡现货现金价时序图`→IMEA大豆；`al_2__上期所仓单`→USGS粗铝美国等） | 🔴 阻断 | 数据错配 |
| N4 | win 23 条指标无有效 zhiji_id（`ids` 缺失）→ 无法拉数，会被唯一性校验静默放过 | 🟡 待核 | 数据完整性 |
| N5 | win `_meta.change` 文本显示 `legacy/20260826_pb_stock_v1/` 归档链路活跃，`pb_stock_v2` 遗留缺陷仍在 | 🟡 待核 | 遗留缺陷 |
| N6 | main 与 win 共享同 7 条中文裸 key 污染 → **命名规范从未执行**，非本次引入 | 🟡 流程 | 规范缺失 |

### 6.5 驳回结论

**⛔ 维持驳回（BLOCK）。** 三项硬阻断（结构冲突、分支断流、无变更清单）全部复核成立。

**新增阻断项 2 项**（N1 命名污染、N3 真错配），**新增待核项 3 项**（N2/N4/N5）。

---

## 七、退回 DSH-B / FT 主脑的修正要求（更新版）

在原 3 项基础上补充：

4. **命名规范整改**：68 条中文 key + 7 条纯中文裸 key + 62 条图表名 key，共 137 条违规 key 必须重命名为 `{品种}_{节点}_{语义}` 格式（R-STRUCT-4/5）。
5. **key-name 错配修复**：至少 5 条已确认真错配（N3）必须重新匹配知几序列，或标记 `verified=False` 隔离。
6. **zhiji_id 补全**：23 条无 ID 条目（N4）必须补全或明确剔除，不得静默入库。
7. **交接回执补正**（替换原要求 1）：win 上 2 份既有回执**类型不匹配**，需补交**独立的交接自检回执**，必须含：① 新旧 DSH-B 节点切换范围 ② 原始素材清单（27 份 correction 文件路径 + 行数）③ 业务清洗规则清单（含 Step2 改写清洗的 3 种表格格式解析规则、Step3 知几分层阈值、41 条 `i*` → `pb_` 全量映射表 + 语义邻近对判定理由）。

---

## 八、审计方法说明（可复算）

全程只读，未 checkout、未改任何仓库文件：

```bash
# 检索范围（修正版，含 win 分支）
git ls-tree -r --name-only origin/indicator-correction-win -- task_queue/
git show origin/indicator-correction-win:<file>   # 逐个只读

# 主键交集
git show origin/main:data/indicators_v1.json | python3 -c "..."
git show origin/indicator-correction-win:data/indicators_v1.json | python3 -c "..."
# 实测：pb_(70) ∩ i*(41) zhiji_id = 0

# 隐藏 pb_ 扫描
git show origin/indicator-correction-win:data/indicators_v1.json | grep -o ".\{80\}pb_[a-zA-Z0-9_]*.\{40\}"

# 分支哈希
git show origin/main:data/indicators_v1.json | sha256sum
git show origin/indicator-correction-win:data/indicators_v1.json | sha256sum

# 分叉
git merge-base origin/main origin/indicator-correction-win
git rev-list --count origin/indicator-correction-win..origin/main   # 145
git rev-list --count origin/main..origin/indicator-correction-win   # 16
git merge-base --is-ancestor origin/indicator-correction-win origin/main; echo $?   # 1
```
