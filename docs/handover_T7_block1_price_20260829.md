# 交接文档 · framework-tree 铅指标树填充 T7 · 板块1 价格信号（2026-08-29）

## 任务背景
把镍方法论 + T5 flow v2 工作流迁移到铅(PB)，填充 tree_config.json 目录树。用户要求「先做板块1（价格信号）全流程看效果，然后 2.2-2.6 全做」。

## 已完成（本轮 2.1-2.5 已上线，2.6 待收尾）

| 子节点 | 页面 HTML | 3 图内容 | git commit | 线上 curl 验证 |
|---|---|---|---|---|
| 2.1 盘面结构 | pb_21_price_structure.html | 量价仓三联动 / 收盘价季节 / 成交持仓比 | 1b0b59b | ✅ 659KB |
| 2.2 现货与升贴水 | pb_22_spot_premium.html | 现货vs主力基差 / 现货季节 / 原生vs再生价差 | 01b6a63 | ✅ 565KB |
| 2.3 海外价格 | pb_23_overseas_price.html | LME期限结构 / LME现货季节 / 升贴水vs进口盈亏 | 61612f5 | ✅ 503KB |
| 2.4 价差体系 | pb_24_spread_system.html | 期现月差 / 再生利润vs精废价差 / 铅锌比价 | 212fb8d | ✅ 711KB |
| 2.5 估值与利润 | pb_25_valuation_profit.html | 原生vs再生利润 / 废电池vs再生精铅 / TC矿端 | db4d7af | ✅ 589KB |
| **2.6 持仓席位** | **pb_26_position_holder.html（待 build）** | 量仓结构 / 持仓季节 / 持仓-价格背离 | **待提交** | 待验证 |

**线上首页**：https://algo23-yunqingtian.github.io/framework-tree/
（GitHub Pages 构建延迟约 60-90s，push 后 sleep 75 再 curl 验证）

## 关键数据资产（indicators_v1.json v2.4，共 73 指标）
- **价格信号 j 系列**（本轮新增 21 个，全部日频全量灌入 api_cache.db）：
  - j21_*: close/volume/oi（观 kline PB D，3751 交易日 2011-03 起）
  - j22_*: spot/sh/gd/hn/tj/premium/regen/shfe_ratio（SMM 1#铅现货+区域+升贴水+沪伦比）
  - j23_*: lme_cash/lme_3m/lme_0to3/lme_sp3/imp_profit（LME现货+3M+升贴水+SMM进口盈亏）
  - j24_*: spread_m/s/regen_profit/refine_spread（期现价差+再生利润+精废价差）
  - j25_*: smelt_cost/ag_revenue/tc/battery（加工成本+白银收益+TC+废蓄电池）
- **复用已有**：i1/i2 库存系列、i17/i41 进出口系列（6.x 页）
- 观 kline 落盘：pb_main_daily_kline_raw.json、pb_zn_main_daily.json（ZN 4731 根 2007 起）

## 2.6 持仓席位观察 · 剩余步骤（同花顺已发散完，知几验证已确认）
- **同花顺返回**：8 图设计，核心 3 张 = ①前20多空vs价格 ②集中度+活跃度 ③多空比+净持仓分位
- **知几数据结论**：前20会员持仓排名【无数据】（只有 LME/SHFE 总持仓量）；akshare 未安装
- **落地决策（已定）**：用观 kline 已有数据做 3 图：
  1. 图1 沪铅持仓量+成交量（量仓结构，双轴）→ j21_oi + j21_volume
  2. 图2 沪铅持仓量季节图（近5年历年线）→ j21_oi（chart_line_t default_seasonal）
  3. 图3 持仓-价格背离（持仓 vs 收盘价，双轴）→ j21_oi + j21_close
  前20席位体系在 NOTE 标注「待上期所会员持仓排名外部源」
- **build 脚本**：scripts/build_pb_26.py（参考 build_pb_24.py 结构，3 图，无季节则 has_seasonal=False 但图2有季节 → 需要 seasonal）
- **验证门禁**：check_html.py PAGES 加 "26" 条目 + verify_render.js PAGES 加 {key:'26', seasonal:['echart_26_c2']} → 跑 10/10 ALL PASS
- **commit+push** + sleep 75 + curl 验证

## 验证门禁（当前完整流程，必须全绿）
1. `python3 scripts/check_html.py` → 10/10 PASS
2. node --check 每页 `<script>` 内容 → 语法 OK
3. `node scripts/verify_render.js` → 10/10 ALL PASS

## 坑速查
- **chart_kits.py 的 chart_pv/chart_dual 用双引号标题**，build 脚本里 `%s` 格式化，`%` 要写 `%%`
- **check_html.py 版本检查**已改为正则 `indicators_v1\.json v\d+\.\d+`（兼容 v1.x/v2.x），不要再写死版本号
- **STATUS.md 追加记录**：用 python 拆行（patch 的 `\n` 会变字面 `\n` 不换行！）→ 用脚本 `open().read().split('\n')` 处理
- 观 kline 返回**升序**（bars[0]=旧），不要反转
- 新对话入口：www.iwencai.com → 左侧「新对话」→ 底部 [contenteditable].ql-editor 注入 → .send-button 点击

## 下一步建议（板块1 完成后）
- STATUS.md 更新「板块1 价格信号 6 节点全部完成」
- 可选：建板块1 总览页串联 2.1-2.6
- 继续板块2 供给（3.x）、板块4 需求（5.x）、板块5 成本利润（7.x）、板块6 供需平衡（8.x）
- 库存 4.x（已做 4.1/4.2）、进出口 6.x（已做 6.1-6.4）

## 文件位置
- build 脚本：framework-tree/scripts/build_pb_2x.py
- 同花顺原始返回：analysis/iwencai/PB/2x_diversify_20260829.md
- 数据落盘：analysis/iwencai/PB/pb2x_*.json
- api_cache.db：framework-tree/scripts/api_cache.db（不推 GitHub，二进制）
- 指标库：framework-tree/data/indicators_v1.json（推 GitHub）
