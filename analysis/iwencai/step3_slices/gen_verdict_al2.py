#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对 slice_al2.json 的候选指标做语义判定，输出 verdict_al2.json。
纯读 json + 写 json，不调用任何 API。"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
src = json.load(open(os.path.join(BASE, 'slice_al2.json'), encoding='utf-8'))

# 判定表：指标名 -> (选中hit的下标或None, note)
V = {
 # ============ 真匹配 ============
 '中国铝精炼金属净进口量': (1, '命中"电解铝：净进口数量：中国（月）"，铝品种前缀+净进口口径完全一致；氧化铝净进口与指标所指精炼金属不符，原铝仅年度口径，月度更贴合6.2节点'),
 '中国铝终端消费量': (0, '命中"电解铝：消费量：中国（月）"，与"中国铝终端消费量"语义一致（精炼铝消费量即终端消费），万吨/月频率合理'),
 '中国铝铝制品出口金额': (0, '命中"铝制品：出口金额：安徽（月）"，虽仅省级分片但字段"铝制品出口金额"与指标名完全对应，为hits中唯一铝制品出口金额序列（另有北京/重庆同系列）'),
 '沪铝主力合约成交量': (0, '命中"SHFE：铝：主力合约：单边交易：成交量（日）"，交易所/品种/主力合约/字段四项全对'),
 '沪铝主力合约持仓量': (0, '命中"SHFE：铝：主力合约：单边交易：持仓量（日）"，为精确主序列；氧化铝/铁矿命中不相关'),
 '沪铝主力合约收盘价': (0, '命中"SHFE：铝：主力合约：收盘价（日）"，精确主序列'),
 '沪铝基差': (0, '命中"SHFE：铝：基差（日）"，铝品种基差序列；氧化铝基差与豆粕基差不相关'),
 '沪铝注销仓单': (0, '命中"LME：铝：注销仓单（日）"，为总量主序列；其余为分仓库地区子序列'),
 '电解铝（精炼）产量': (1, '命中"中国：工业产品：产量：电解铝（月）"，口径标准且为月度（覆盖日/月/年三口径时月度最通用），与指标名电解铝产量完全一致'),
 '铝冶炼端完全成本分位 / 现金成本分位': (0, '命中"SMM: 电解铝分地区成本: 全国加权平均: 现金成本: 季度"，电解铝现金成本为冶炼端成本正主口径，SMM官方源；工业硅与氢氧化锂命中不相关'),
 '铝冶炼端现金成本': (0, '命中"氧化铝：现金成本：中国（月）"，为三命中中唯一的全国加权口径；内蒙古/山东为分省口径，全国序列更贴合"铝冶炼端现金成本"上位概念'),
 '铝基差': (0, '命中"SHFE：铝：基差（日）"，铝基差主序列；氧化铝/铝合金铸造基差为下游品种'),
 '铝现货价': (0, '命中"MCX：铝：现货价：赖布尔（日）"，铝现货价序列；铝矿现货价与迷你型子序列非主口径'),
 '铝现货升贴水': (0, '命中"电解铝：现货升贴水：重庆—SHFE（日）"，电解铝对SHFE升贴水为铝现货升贴水标准口径（佛山/巩义为同系列分地域序列）'),
 '铝矿TC加工费进口盈亏': (0, '命中"氧化铝：进口盈亏：中国（日）"，氧化铝即铝矿加工端进口盈亏正主口径；镍铁/镍豆命中不相关'),

 # ============ 未匹配：铝相关候选但命中全不相关 ============
 '中国铝精炼厂开工天数': None,
 '中国铝精炼厂检修天数': None,
 '中国铝精炼厂检修量': None,
 '中国铝精炼金属出口量': None,
 '中国铝精炼金属进出口金额': None,
 '中国铝精炼金属进口分国别量': None,
 '中国铝精炼金属进口量': None,
 '中国铝终端产量': None,
 '中国铝终端消费分地区量': None,
 '中国铝终端消费占比': None,
 '中国铝能源成本占比': None,
 '中国铝表观消费占比': None,
 '中国铝表观消费量': None,
 '中国铝订单量': None,
 '中国铝订单量分地区量': None,
 '中国铝铝出口分国别量': None,
 '中国铝铝出口占比': None,
 '中国铝铝出口量': None,
 '中国铝铝制品出口关税税率': None,
 '中国铝铝制品出口分国别量': None,
 '中国铝铝制品出口占比': None,
 '中国铝铝制品出口发运量': None,
 '中国铝铝矿砂成本': None,
 '中国铝隐性库存': None,
 '中国铝隐性库存分位': None,
 '中国铝隐性库存占比': None,
 '中国铝隐性库存天数': None,
 '中国铝需求增速': None,
 '主要产铝国的月度/年度产量总量': None,
 '产量总量': None,
 '俄罗斯产量': None,
 '全球铝矿/电解铝总产量（月/年）': None,
 '分国别产量占全球比重': None,
 '前20大席位的持仓结构': None,
 '北非产量': None,
 '印度产量': None,
 '本节点按 IAI/LME 电解铝季度口径为准': None,
 '氧化铝矿（铝土矿）': None,
 '沪铝主力-次主力月差序列（跨月价差结构）': None,
 '沪铝主力合约估值分位': None,
 '沪铝主力合约前20大净多头持仓量': None,
 '沪铝主力合约前20大多头持仓量': None,
 '沪铝主力合约前20大空头持仓量': None,
 '沪铝主力合约多空持仓比': None,
 '沪铝交易所库存': None,
 '沪铝仓单': None,
 '沪铝在途仓单': None,
 '沪铝注销仓单占比': None,
 '沪铝现货月-主力月差': None,
 '沪铝近月-远月月差': None,
 '海外市场的铝价定价本身': None,
 '海外铝矿产能利用率': None,
 '海外铝矿产量（季度）': None,
 '海外铝矿端的财报/协会口径季度产量': None,
 '海外铝精炼产量（季度）': None,
 '海外铝精炼厂开工率': None,
 '海外铝精炼新增/关停产能（在建项目）': None,
 '现货价 与 期货价之间的价差体系': None,
 '铝冶炼端产能利用率': None,
 '铝冶炼端完全成本': None,
 '铝冶炼端开工率': None,
 '铝冶炼端日度利润': None,
 '铝冶炼端日度利润分位': None,
 '铝冶炼端检修量': None,
 '铝加工端加工费分位': None,
 '铝加工端日度利润': None,
 '铝矿TC加工费': None,
 '铝矿TC加工费分位': None,
 '铝精炼厂TC加工费': None,
 '铝精炼厂TC加工费分位': None,
 '主图归 7.1': None,
 '价格所处的历史估值位置': None,
 '分位（估值贵/便宜）归 2.5，成本与利润的绝对值测算归 7.x': None,
 '席位明细（前20大）归 2.6，全市场总持仓量/成交量归 2.1': None,
 '持仓量 / 成交量 / 多空持仓比 / 收盘价': None,
 '期货合约间的期限结构': None,
 '由此推导的冶炼/加工端利润弹性': None,
 '绝对值测算主图归 7.2': None,
}

# 未匹配的差异化 note 生成器（按指标名关键词归类，避免千篇一律）
def unmatched_note(name, hits):
    hm = ' / '.join(h.get('name', '') for h in hits)
    # 非铝前缀指标名：先说明命中与铝无关
    if not any(k in name for k in ['铝', 'IAI', 'LME', 'TC']):
        return '指标名不含铝，命中3项（%s）均为其他品种/泛口径序列，无任何铝语义对应 → unmatched' % hm
    # 指标名含铝，按命中内容说明
    if '中国铝精炼厂' in name or '中国铝铝' in name or '中国铝终端' in name or '中国铝表观' in name or '中国铝订单' in name:
        return '指标名含"铝"，但3项命中（%s）分别为沥青/豆粕/焦炭/冰箱空调/农机/氟化铝等非铝品种，无铝相关词 → unmatched' % hm
    if '中国铝精炼金属' in name:
        return '指标名指向精炼铝进出口，但命中为钢材/热轧钢带/冰箱空调/农机/证券资产/硫酸镍等，无电解铝或原铝口径 → unmatched' % hm
    if '隐性库存' in name:
        return '指标名含"隐性库存"，命中仅氧化铝库存/铝土矿库存/焦炭库存/大豆余粮占比等，无铝锭或铝产业链隐性库存口径 → unmatched' % hm
    if '中国铝需求增速' in name:
        return '命中3项均为硫酸镍需求量（东北分片），无铝需求口径 → unmatched' % hm
    if '产量' in name and ('俄罗斯' in name or '印度' in name or '北非' in name):
        return '命中3项分别为煤炭/褐煤/氨或印度煤炭部产量/冷轧板卷等，无电解铝或铝矿产量口径 → unmatched' % hm
    if '全球铝矿' in name or '分国别产量' in name or '主要产铝国' in name:
        return '指标名指向铝矿/电解铝全球产量，命中为高炉生铁/粗钢/玉米淀粉/氧化铝产量等，无电解铝产量全球序列 → unmatched' % hm
    if '海外铝' in name:
        return '指标名指向海外铝，命中为高炉/焦化产能利用率、黄金海外产冶炼厂产量、精炼镍产能等，无海外电解铝或铝矿序列 → unmatched' % hm
    if '沪铝' in name:
        if '持仓' in name or '席位' in name:
            return '沪铝CFTC持仓类指标，命中为USGS粗铝进出口/美国铝均价/大气污染物环保税，非持仓结构序列 → unmatched' % hm
        if '仓单' in name or '在途' in name:
            return '命中为USGS粗铝进出口与"混杂低含量铜颗粒的铝"均价，无SHFE仓单/在途仓单口径 → unmatched' % hm
        if '交易所库存' in name:
            return '命中为氧化铝库存/铝土矿库存/焦炭库存，无SHFE铝库存口径 → unmatched' % hm
        if '月差' in name or '估值分位' in name:
            return '命中为USGS粗铝进出口/美国铝均价等贸易数据，无合约价差或估值分位序列 → unmatched' % hm
        return '命中3项（%s）无沪铝对应口径 → unmatched' % hm
    if 'TC加工费' in name:
        return '铝矿TC加工费应匹配铝土矿或氧化铝TC，命中仅PTA/纯涤纱/冷轧不锈钢加工费等，无铝矿TC口径 → unmatched' % hm
    if '精炼厂TC' in name:
        return '铝精炼厂TC应匹配电解铝加工费/电解铝利润，命中为铝棒6063加工费（属铝加工端而非精炼端），口径不符 → unmatched' % hm
    if '冶炼端' in name or '加工端' in name or '能源成本' in name or '铝制品出口' in name or '出口关税' in name:
        return '命中3项（%s）为硅锰成本利润、白糖利润、大豆压榨、混凝土发运量、铝型材产量等非电解铝冶炼/加工口径 → unmatched' % hm
    if '铝现货升水' in name:
        return '命中为USGS粗铝进出口与"混杂低含量铜颗粒的铝"均价，无铝现货升水（premium）口径 → unmatched' % hm
    if '海外的铝价' in name:
        return '命中为USGS"混杂低含量铜颗粒的铝"均价（铜颗粒类杂料，非伦铝/铝价定价），另两项为粗铝进出口贸易量，均不构成铝价定价序列 → unmatched' % hm
    if '价差' in name or '价格所处的历史估值位置' in name or '分位' in name:
        return '命中为液化气二甲醚价差/生猪价差/汽油裂解价差或焦炭运输价格等，无铝价或铝估值分位口径 → unmatched' % hm
    if '持仓量 / 成交量' in name or '席位明细' in name or '前20大席位' in name or '期货合约间的期限结构' in name:
        return '期货持仓/期限结构指标，命中为DCE铁矿持仓量或豆油/建筑钢成交量等，无沪铝或LME铝持仓结构序列 → unmatched' % hm
    if '绝对值测算' in name or '由此推导的冶炼' in name or '主图归 7.1' in name or '分位（估值贵' in name or '本节点按 IAI' in name or '氧化铝矿（铝土矿）' in name or '产量总量' in name:
        return '指标名非具体指标口径，且命中3项（%s）与铝产业语义无关 → unmatched' % hm
    return '命中3项（%s）与指标名"%s"无铝语义对应 → unmatched' % (hm, name)


out = {}
matched = 0
for name, info in src.items():
    hits = info.get('hits', [])
    pick = V.get(name, 'MISSING')
    if pick == 'MISSING':
        raise SystemExit('V 表缺少指标名：%s' % name)
    if pick is None:
        out[name] = {'matched': False, 'chosen': None, 'note': unmatched_note(name, hits)}
    else:
        idx, note = pick
        h = hits[idx]
        out[name] = {
            'matched': True,
            'chosen': {'id': h.get('id'), 'name': h.get('name'), 'source': h.get('source'), 'unit': h.get('unit')},
            'note': note,
        }
        matched += 1

with open(os.path.join(BASE, 'verdict_al2.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print('总数: %d  匹配: %d  未匹配: %d' % (len(out), matched, len(out) - matched))
