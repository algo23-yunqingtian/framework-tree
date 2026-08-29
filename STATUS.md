# framework-tree 项目全局状态

> 唯一真源。任何参与 agent 先读此文件再开工。
> 更新规则：写完立即 `git commit + push`，前缀 `[DOC]`。

---

## 🔔 机制公告（2026-08-26 生效）

**两条线隔离机制已上线。** 所有参与 agent 请注意：

- **线A**（架构/前端/GitHub）→ 只写 `/home/ubuntu/framework-tree/`
- **线B**（指标录入/数据）→ 只写 `/home/ubuntu/analysis/iwencai/` 等 analysis 目录
- 文件锁白名单已强制隔离，违规写入会被拒
- **协作唯一真源 = `STATUS.md`**：你完成一个品种 → 在 "B→A 待办" 加一行 → 通知线A
- **不要往 framework-tree/ 里写数据产物**，你的数据只放 analysis/ 下

协作细节见 `COLLABORATION.md`，线B交接见 `docs/handover_b.md`。

---

## 总体进度

| 阶段 | 状态 | 负责人 |
|---|---|---|
| 目录树前端复刻 | ✅ 完成 (7大类×33指标×258 chip) | 线A |
| GitHub Pages 上线 | ✅ 完成 | 线A |
| 实时 API (Zhiji+3天缓存) | ✅ 骨架完成 | 线A |
| 铅库存 v2 完整版 (19图:5真+14骨架) | ✅ 完成 pb_stock_v2.html | 线A |
| 铅库存 v2 完整版 (24图:16真+8骨架) | ✅ 完成 (C08五地/C12b电池/C18b平衡 3新真图) | 线A |
| 铅库存 v2 聚焦版 (20图:12真+8骨架) | ✅ 完成 (移走矿端供给C15/C12/C17/C18, 验证指标加标注) | 线A |
| 铅库存 v2 方向A落地 (22图:14真+8骨架) | ✅ 完成 (新增C01b沪铅期货库存/C05b LME注销占比, C07/C11/C01b/C05b默认季节图) | 线A |
| **旧版产物归档** | ✅ 完成 → `legacy/20260826_pb_stock_v1/` (pb_stock.html / pb_stock_demo.html / build_pb_stock.py) | 线A |
| 铅 4.1 交易所库存子页 (2图全真) | ✅ 完成 pb_41_stock.html | 线A |
| 主站 chip 点击跳转品类看板 | ✅ 完成 index.html PAGE_MAP | 线A |
| 板块1 价格信号 6 节点全做 (2.1-2.6, 18图全真) | ✅ 完成 (pb_21~26 + 总览页, 73指标) | 线A |
| ECharts 四图接入 (其余品种) | ❌ 待做 | 线A |
| 同花顺 Prompt v5 定稿 | ✅ 完成 | 线B |
| 铅库存实测 | ✅ v5 发散版 19 图方案已落盘 | 线B |
| 铅库存 zhiji_id 验证 | ✅ 完成 (5个: i1~i5) | 线B |
| 铅库存灌库 (三表) | ❌ 待做 | 线B |
| 其余 7 品种 | ❌ 待做 | 线B |

---

## B→A 待办（线B完成 → 线A接手）

| 品种 | 线B完成项 | 线A需做 | 状态 |
|---|---|---|---|
| 铅(PB) | v5 发散版 19 图方案 + 5 zhiji_id 验证 + i1~i5 缓存数据 | 19图骨架看板(pb_stock_v2.html) + 4.1子页(pb_41_stock.html) + 主站chip跳转 | ✅ 完成 |

---

## A→B 待办（线A完成 → 线B接手）

| 项 | 线A完成项 | 线B需做 | 状态 |
|---|---|---|---|
| — | — | — | 🟡 暂无 |

---

## 近期变更记录

| 日期 | 内容 |
|---|---|
| 2026-08-26 | 项目启动。两条线隔离方案定稿，协作机制上线。 |
| 2026-08-27 | 方向A落地：i28(沪铅期货库存 a10026547)入库；新增C01b/C05b；4张图默认季节视图(切换按钮可切回)；22图=14真+8骨。i29(中国精炼铅进口量)查无序列，按预案跳过进口图。 |
| 2026-08-28 | 6.2 子页 ECharts 修复三连:①双重花括号转义(chart_line_t/chart_dual 输出 {{}})→②JS 变量赋值顺序(__d 引用必须晚于数据赋值行)→③主页跳转验证通过;build_pb_62_demo.py 沉淀为通用 build 模板 | 线B |
| 2026-08-28 | [T4-DEMO] 铅 6.2 精炼金属进出口子页上线(pb_62_import_export.html,2图全真数据);build_pb_62_demo.py 生成脚本;修复 Pages build 连续失败(加 .nojekyll 禁用 Jekyll,因 SOP 内 {占位符} 被 Liquid 当模板变量解析崩溃) | 线B |
| 2026-08-28 | [T5-P1试点] 铅 6.4 海外对华发运子页扩到 3 图(LME 新加坡出发仓/发运-到港节奏/分地区结构);indicators_v1.json v1.5;i40 从 trade_overseas_shipping 调回 trade_raw_import(6.1 正主);64_group 指标组定义;无需新增 zhiji_id;Step1.5 AI 自检报告 64_diversify_20260828.md | 线B |
| 2026-08-28 | [T5-P2.1+P2.2] 铅 6.1 原料进口 + 6.2 精炼金属进出口子页扩到 3 图;indicators_v1.json v1.7;6.1 修正 i40 归属为 6.1 正主(剔除旧 i17);6.2 采用方案A复用缓存(无需新增 zhiji_id),i7 作全球发运背景;Step1.5 自检报告 61/62_diversify_20260828.md | 线B |
| 2026-08-28 | [T5-P2.3] 铅 6.3 制品出口子页扩到 3 图(铅蓄电池出口总量/启动型/启动型vs其他类型结构);indicators_v1.json v1.8;复用 i37/i38 现有缓存;i39 累计作备用;剔除出口目的地分布/HS 7806 铅材;标注海合会反倾销 25.8-74% 2026.1.13 生效;Step1.5 自检报告 63_diversify_20260828.md。**6.1-6.4 四节点全部完成，指标树补全任务 P1+P2 闭环** | 线B |
| 2026-08-28 | [T5-图备注增强] 用户反馈"客户看每张图不知道指标间什么关系"，4 页全部图表加 `chart-note` 备注块(3图×4页=12 处)：每图两行——「什么时候看」=买方视角观测用途，「指标关系」=图内各指标如何配合。同轮重构 6.2 图2：原"进口+全球注销仓单"(关联牵强)→"进口(i17)+出口(i41)"双向(对齐同花顺图5 净买净卖判断)，新增 i41 海关铅锭出口 a10017091，i7 移出 6.2；图3 改净进口=i17-i41 计算图；indicators_v1.json v1.9；4 页标注 v3+图备注 | 线B |
| 2026-08-28 | [P1+P2] build 脚本公共模块重构 + 自动验证门禁。P1: 新增 `scripts/chart_kits.py`(269 行)，把 4 个 build 脚本重复的 `load_metric/pairs/latest/chart_line_t/chart_dual/chart_triple/CSS/ANTI/__seasonalize/__tgl/resize` 全部抽公共；4 个 build 脚本从 220+ 行降到 82-90 行(-60%)，只写"读哪个指标+画哪张图+什么备注"。P2: 新增 `scripts/check_html.py`(185 行,7 项校验×4 页) + `scripts/verify_render.js`(jsdom+ECharts mock 真实渲染验证,62 项检查)。**顺手修掉 3 个隐性 bug**:①6.2/6.3 季节按钮假数据(`data:[null×12]`)→统一真数据 `window.__seasonalize(__d)`;②6.4 缺 button CSS 样式 + 无公共 JS 封装→补齐;③`__tgl` 按钮文字语义错配(nxt==='ts' 时误显示「⏱ 时序」,与初始按钮文字语义对撞导致点击后文字看似不变)→统一为「按钮=点击后的视图」语义。三道验证全绿:check_html 4/4、Node 语法 4/4、jsdom 渲染 4/4(62 项)。备份: `/home/ubuntu/backups/framework-tree-t5-20260828/`(bundle+tar.gz+git tag `T5_P1P2_BEFORE_20260828`)，3 天观察期后删除 | 线A |
| 2026-08-29 | **[T6b] 季节图改造上线 v1.1**：季节视图由「12 月均值线」改为「历年各一条线+图例标年份」(默认近 5 年 2022-2026)。修复 chart_kits.py itemStyle 括号顺序 bug(`}}}]}]`→`}}]}}]`,与 v3 逐字节一致)；新增 `__seasonalizeByYear`；verify_render.js 的 setOption 检查改为兼容默认 ts/se 两种 mode(修复 62/63 误 FAIL)。三道验证全绿 4/4。已推 main `767221e`，线上 4 页 curl 验证 `__seasonalizeByYear` 均 ≥1。回退点:git tag `T6b_SEASONAL_V3_BEFORE_20260828` + 备份 `/home/ubuntu/backups/framework-tree-t6b-online-before-20260828/` | 线A |
| 2026-08-29 | **[T7-2.1] 铅价格信号·2.1盘面结构子页上线 v1**（指标树填充板块1第1子节点，全流程：同花顺v18发散→自检→知几验证→入库→build→push）。新增 `pb_21_price_structure.html` 3图全真：图1 沪铅主力量价仓三联动(chart_pv 新公共函数,价左轴+量仓右轴)、图2 月末收盘价季节图(近5年历年线)、图3 成交持仓比(量/仓日频计算)。数据源=zhiji 观 kline PB D 3751交易日全量(2011-03至2026-08-28)，灌 api_cache.db j21_close/j21_volume/j21_oi。indicators_v1.json v1.9→v2.0(+3指标)。待外部源：前20会员多空/集中度(知几无,需上期所会员持仓排名)。三道验证 5/5 ALL PASS，已推 `1b0b59b`，线上 curl 验证通过 | 线A |
| 2026-08-29 | **[T7-2.2] 铅价格信号·2.2现货与升贴水子页上线 v1**（板块1第2子节点）。新增 `pb_22_spot_premium.html` 3图全真：图1 1#铅现货价vs沪铅主力基差、图2 现货价季节图(近5年历年线)、图3 原生铅vs再生铅价差。数据源=SMM 1#铅现货均价+区域价+升贴水，灌 api_cache.db j22_spot/j22_sh/j22_gd/j22_hn/j22_tj/j22_premium/j22_regen/j22_shfe_ratio。indicators_v1.json v2.0→v2.1。已推 `01b6a63`，线上 curl 565KB 验证通过 | 线A |
| 2026-08-29 | **[T7-2.3] 铅价格信号·2.3海外价格子页上线 v1**（板块1第3子节点）。新增 `pb_23_overseas_price.html` 3图全真：图1 LME期限结构(Cash/3M/升贴水)、图2 LME现货价季节图、图3 现货升贴水vs SMM进口盈亏。数据源=LME现货+3M+升贴水+SMM进口盈亏，灌 j23_lme_cash/j23_lme_3m/j23_lme_0to3/j23_lme_sp3/j23_imp_profit。indicators_v1.json v2.1→v2.2。已推 `61612f5`，线上 curl 503KB 验证通过 | 线A |
| 2026-08-29 | **[T7-2.4] 铅价格信号·2.4价差体系子页上线 v1**（板块1第4子节点）。新增 `pb_24_spread_system.html` 3图全真：图1 期现价差(主力月差/近远月)、图2 再生铅利润vs精废价差、图3 铅锌比价。数据源=期现价差+再生利润+精废价差，灌 j24_spread_m/j24_spread_s/j24_regen_profit/j24_refine_spread。indicators_v1.json v2.2→v2.3。已推 `212fb8d`，线上 curl 711KB 验证通过 | 线A |
| 2026-08-29 | **[T7-2.5] 铅价格信号·2.5估值与利润子页上线 v1**（板块1第5子节点）。新增 `pb_25_valuation_profit.html` 3图全真：图1 原生vs再生铅冶炼利润、图2 废蓄电池价格vs再生精铅成本、图3 铅精矿TC矿端议价。数据源=加工成本+白银副产品收益+TC+废蓄电池，灌 j25_smelt_cost/j25_ag_revenue/j25_tc/j25_battery。indicators_v1.json v2.3→v2.4(+4指标, 累计73指标)。已推 `db4d7af`，线上 curl 589KB 验证通过 | 线A |
| 2026-08-29 | **[T7-2.6] 铅价格信号·2.6持仓席位观察子页上线 v1 + 板块1收官**（板块1第6子节点）。新增 `pb_26_position_holder.html` 3图全真：图1 沪铅持仓量vs成交量(量仓结构双轴)、图2 持仓量季节图(近5年历年线)、图3 持仓vs收盘价(量价背离双轴)。落地决策：前20会员多空排名/集中度在知几【无数据】(仅LME/SHFE总持仓量)，前20席位体系在NOTE标注「待上期所会员持仓排名外部源」，用观 kline 已有 j21_oi/j21_volume/j21_close 做3图。三道验证 10/10 ALL PASS。已推 `5b0903e`，线上 curl 848KB 验证通过。**板块1【价格信号】6子节点/18图全部上线，indicators_v1.json v2.4 共73指标** | 线A |
| 2026-08-29 | **[T7-板块1] 铅价格信号总览页 + 主站接入闭环**。新增 `pb_2_overview.html` 静态导航页(2.1-2.6 六卡片：每页3图摘要+指标组+数据量, 移动端自适应) + `scripts/build_pb_2_overview.py`。同时补齐主站 `index.html` 两处缺口：①`PAGE_MAP` 新增 `PB_p1~PB_p6` 六条映射(此前价格板块点击PB chip 只落到占位面板，无法跳转看板)；②分类卡片标题加数据驱动「📈 总览」入口(`OVERVIEW_MAP` 以 cat.id 为键, 后续板块可复用) + `.ov-link` 样式(margin-left:auto 右对齐, 不干扰 caret 折叠)。index.html JS 语法 node --check 通过。已推 `41982bb` + 本提交，线上 7 页 curl 全 200 验证 | 线A |

---

## 当前卡点

| # | 卡点 | 谁在等 |
|---|---|---|
| 1 | 铅库存8骨架仅剩5张待补：C03(浙江/江苏仓单地区无数据,HHI算不全)、C04交割品牌、C06质押、C10贸易商、C14b再生-原生价差、C15b进口盈亏(⚠️i12数据实为价格非盈亏,需用SMM进口成本+1#铅均价重算)、C17b亚洲可交仓、C19检修 | 需问财发散或外部数据源 |
| 2 | 移走的矿端供给4图(C15沪伦比值/C12再生产量/C17精矿进口/C18精矿产量)数据在缓存,待供给/价差目录建页时接入 | 线A(其他目录页) |
| 3 | 三表灌库(indicator_meta/indicator_series)按spec/db_design.md 仍待做 | 线B |
| 4 | C01b/C05b 数据源备忘：i28=SHFE库存周报(SMM名义,周度,2018起435点)；C05b=i7/(i6+i7)计算,2019-05起1832点。i29中国精炼铅进口总量在知几无序列(仅美/新/泰海关分国别)——若需进口图需换外部源(海关总署) | 线B |