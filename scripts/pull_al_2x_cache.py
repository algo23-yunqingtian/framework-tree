#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AL 2.x 价格信号节点 · 新指标缓存拉取（Step3→Step4 桥接）

不复用 refresh_cache.py 的 i/j 前缀筛选，直接按 (code, metric, zhiji_id) 拉取。
写入 scripts/api_cache.db 的 indicator_cache 表（metric 字段必须与
indicators_v1.json 的 key 一致，因为 chart_kits.load_metric(mid, code) 按
(code, metric) 查表）。

新增指标（经 zhiji search→series 实测确认有数据，2026-08-31）：
  al_22_spot         ID00259727  电解铝A00现货价 上海华通（日）  ⚠ 断更：n=1913 但 latest=2022-10-13
  al_22_premium_cn   ID01319345  电解铝A00升贴水 中国（日）
  al_23_lme_settle   FU00014308  LME铝3M结算价（日）
  al_23_lme_oi       FU00014314  LME铝3M持仓量（日）
  al_23_lme_volume   FU00014307  LME铝3M成交量（日）
  al_24_lme_settle   FU00014308  LME铝3M结算价（日）·2.4期限结构锚(与2.3共用源，不重复注册)
  al_25_profit       ID01732414  电解铝利润（月）
  al_26_long_top20   FU00021993  SHFE铝08合约多单持仓合计 前20期货公司（日）
  al_26_short_top20  FU00021998  SHFE铝08合约空单持仓合计 前20期货公司（日）
  al_26_comex_nc_long  ID00303201 COMEX铝报告头寸非商业多头（周）
  al_26_comex_nc_short ID00303202 COMEX铝报告头寸非商业空头（周）
  al_00_settle_front FU00014630  SHFE铝主力合约结算价（日）·2.4月差衍生原料·近月端
  al_00_settle_cont  FU00014623  SHFE铝连续合约结算价（日）·2.4月差衍生原料·远月端

⚠ 已知通用层错标，禁止使用：
  FU00014812 在 indicators_v1.json 的通用条目 LME库存.ids.AL，但实测 series 返回的是
  「镍：3个月合约：收盘价」——通用条目层把镍误配给了铝，禁止拿它当 LME 铝库存用。

不在此脚本的三项（本地自算，见 analyze 阶段 / build_cu_al_batch.py 旁路）：
  al_24_shfe_spread     = al_00_settle_front - al_00_settle_cont（DERIVED:SPREAD）
  al_25_close_quantile  = al_00_close_front 滚动 730 天分位（DERIVED:QUANTILE）
  al_25_lme_quantile    = al_23_lme_settle 滚动 730 天分位（DERIVED:QUANTILE）
"""
import importlib.util, json, os, sqlite3, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "api_cache.db")

# 复用统一缓存脚本的写入逻辑（保持 payload 结构与全库一致）
spec = importlib.util.spec_from_file_location("rc", os.path.join(HERE, "refresh_cache.py"))
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)

TARGETS = [
    ("al_22_spot",        "ID00259727", "电解铝：A00：Al≥99.7%：现货价：上海华通（日）", "元/吨", "daily"),
    ("al_22_premium_cn",  "ID01319345", "电解铝：A00：Al≥99.7%：升贴水：中国（日）",      "元/吨", "daily"),
    ("al_23_lme_settle",  "FU00014308", "LME：铝：3个月合约：结算价（日）",              "美元/吨", "daily"),
    ("al_23_lme_oi",      "FU00014314", "LME：铝：3个月合约：持仓量（日）",              "手", "daily"),
    ("al_23_lme_volume",  "FU00014307", "LME：铝：3个月合约：成交量（日）",              "手", "daily"),
    ("al_24_lme_settle",  "FU00014308", "LME：铝：3个月合约：结算价（日）",              "美元/吨", "daily"),
    ("al_25_profit",      "ID01732414", "电解铝：利润（月）",                            "元/吨", "monthly"),
    ("al_26_long_top20",  "FU00021993", "SHFE：铝：08合约：多单持仓合计：前20期货公司（日）", "手", "daily"),
    ("al_26_short_top20", "FU00021998", "SHFE：铝：08合约：空单持仓合计：前20期货公司（日）", "手", "daily"),
    ("al_26_comex_nc_long",  "ID00303201", "COMEX：铝：报告头寸非商业多头持仓数量（周）", "手", "weekly"),
    ("al_26_comex_nc_short", "ID00303202", "COMEX：铝：报告头寸非商业空头持仓数量（周）", "手", "weekly"),
    ("al_00_settle_front", "FU00014630", "SHFE：铝：主力合约：结算价（日）",             "元/吨", "daily"),
    ("al_00_settle_cont",  "FU00014623", "SHFE：铝：连续合约：结算价（日）",             "元/吨", "daily"),
]

START, END = "2015-01-01", "2026-08-30"


def main():
    con = sqlite3.connect(DB)
    ok = 0
    print("=" * 76)
    print("AL 2.x 新指标拉取 → %s (%s→%s)" % (os.path.basename(DB), START, END))
    print("=" * 76)
    for mid, zid, name, unit, freq in TARGETS:
        entry = {"name": name, "unit": unit, "freq": freq, "ids": {"AL": zid}}
        r = rc.refresh_one(con, "AL", mid, entry, START, END)
        flag = "✗" if r[4] else "✓"
        print("%s %-22s %-11s n=%-6d latest=%-11s %s" % (flag, mid, zid, r[2], r[3], r[4] or name[:30]))
        if not r[4]:
            ok += 1
        time.sleep(1.2)
    con.commit()
    con.close()
    print("-" * 76)
    print("[OK] %d/%d 成功" % (ok, len(TARGETS)))


if __name__ == "__main__":
    main()
