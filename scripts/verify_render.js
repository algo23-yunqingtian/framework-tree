/**
 * verify_render.js — framework-tree 页面真实渲染验证（P1/P2 验收门禁，v1.1 历年 series）
 *
 * 做法：用 jsdom 加载真实 HTML，mock 掉 ECharts（jsdom 无 canvas），
 *       通过 echarts.init 捕获 window.__opts_*，直接调用页面内的
 *       __seasonalizeByYear / __tgl 函数，验证"季节按钮切换"是否产出历年 series。
 *
 * 校验点：
 *   1. __seasonalizeByYear 存在且可调用
 *   2. 对每个含季节模式的图，__seasonalizeByYear(data, years, pal) 产出 series：
 *      - series 数量 = 年份数量
 *      - 每个 series.data 长度=12
 *      - 每个 series.data 非空≥3（有 3 个月以上数据）
 *      - 每个 series.name 含"年"字
 *   3. __tgl 切换后 mode 翻转 + 按钮文字与 mode 对应关系正确
 *   4. 无季节模式的页（64）跳过 2/3
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('/tmp/node_modules/jsdom');

const ROOT = path.resolve(__dirname, '..');
const PAGES = [
  // ── 铅(PB) 30 页 ──
  { key: '21', file: 'pb_21_price_structure.html',       seasonal: ['echart_21_c2'] },
  { key: '22', file: 'pb_22_spot_premium.html',          seasonal: ['echart_22_c2'] },
  { key: '23', file: 'pb_23_overseas_price.html',        seasonal: ['echart_23_c2'] },
  { key: '24', file: 'pb_24_spread_system.html',          seasonal: [] },
  { key: '25', file: 'pb_25_valuation_profit.html',        seasonal: [] },
  { key: '26', file: 'pb_26_position_holder.html',          seasonal: ['echart_26_c2'] },
  { key: '51', file: 'pb_51_primary_consumption.html',   seasonal: ['echart_51_c2'] },
  { key: '52', file: 'pb_52_terminal_consumption.html',  seasonal: ['echart_52_c2'] },
  { key: '53', file: 'pb_53_demand_leading.html',       seasonal: ['echart_53_c2'] },
  { key: '61', file: 'pb_61_raw_material_import.html', seasonal: ['echart_61_c1', 'echart_61_c3'] },
  { key: '62', file: 'pb_62_import_export.html',       seasonal: ['echart_62_c1', 'echart_62_c3'] },
  { key: '63', file: 'pb_63_product_export.html',      seasonal: ['echart_63_c1', 'echart_63_c2'] },
  { key: '64', file: 'pb_64_overseas_shipping.html',   seasonal: [] },
  { key: '32_3', file: 'pb_32_3_regen_supply.html',    charts: 4, seasonal: ['echart_32_3_c4'] },
  { key: '311', file: 'pb_311_overseas_mine.html',     seasonal: ['echart_311_c1', 'echart_311_c2', 'echart_311_c3'] },
  { key: '312', file: 'pb_312_overseas_by_country.html', seasonal: ['echart_312_c2'] },
  { key: '313', file: 'pb_313_domestic_mine.html',     seasonal: ['echart_313_c1', 'echart_313_c2', 'echart_313_c3'] },
  { key: '314', file: 'pb_314_mine_import.html',       seasonal: ['echart_314_c1', 'echart_314_c2'] },
  { key: '315', file: 'pb_315_tc_fee.html',            seasonal: ['echart_315_c2', 'echart_315_c3'] },
  { key: '321', file: 'pb_321_refining_output.html',   seasonal: ['echart_321_c1', 'echart_321_c3'] },
  { key: '322', file: 'pb_322_operating_rate.html',    seasonal: ['echart_322_c1', 'echart_322_c3'] },
  { key: '324', file: 'pb_324_profit_elasticity.html', seasonal: ['echart_324_c1', 'echart_324_c3'] },
  { key: '41', file: 'pb_41_exchange_stock.html',   seasonal: ['echart_41_c1'] },
  { key: '42', file: 'pb_42_warrant.html',          seasonal: ['echart_42_c1', 'echart_42_c2'] },
  { key: '43', file: 'pb_43_social_stock.html',     seasonal: ['echart_43_c3'] },
  { key: '44', file: 'pb_44_factory_stock.html',    seasonal: [] },
  { key: '45', file: 'pb_45_hidden_stock.html',     charts: 2, seasonal: [] },
  { key: '71', file: 'pb_71_cost_curve.html',       seasonal: ['echart_71_c2'] },
  { key: '72', file: 'pb_72_daily_profit.html',     seasonal: ['echart_72_c2'] },
  { key: '73', file: 'pb_73_energy_cost.html',      seasonal: ['echart_73_c2'] },
  // ── 铜(CU)/铝(AL) 34 页：主脑 2026-08-31 jsdom 实测注册 ──
  // 铜铝页部分图无 season toggle 按钮（纯时序渲染），seasonal 留空；
  // 不要按「__opts.se 存在」就注册——那些图初始即渲染历史年份线但无切换按钮 ──
  { key: 'al_21', file: 'al_2_1.html', charts: 2, seasonal: ['echart_al_21_c1'] },
  { key: 'al_22', file: 'al_2_2.html', charts: 2, seasonal: ['echart_al_22_c1'] },
  { key: 'al_23', file: 'al_2_3.html', seasonal: ['echart_al_23_c1','echart_al_23_c3'] },
  { key: 'al_24', file: 'al_2_4.html', charts: 2, seasonal: ['echart_al_24_c1','echart_al_24_c2'] },
  { key: 'al_25', file: 'al_2_5.html', charts: 2, seasonal: ['echart_al_25_c1'] },
  { key: 'al_26', file: 'al_2_6.html', seasonal: [] },
  { key: 'al_323', file: 'al_3_2_3.html', charts: 2, seasonal: ['echart_al_323_c1'] },
  { key: 'al_41', file: 'al_4_1.html', seasonal: ['echart_al_41_c1'] },
  { key: 'al_42', file: 'al_4_2.html', seasonal: ['echart_al_42_c1','echart_al_42_c3'] },
  { key: 'al_43', file: 'al_4_3.html', charts: 1, seasonal: [] },
  { key: 'al_44', file: 'al_4_4.html', charts: 1, seasonal: [] },
  { key: 'al_45', file: 'al_4_5.html', charts: 1, seasonal: ['echart_al_45_c1'] },
  { key: 'al_51', file: 'al_5_1.html', charts: 2, seasonal: ['echart_al_51_c1'] },
  { key: 'al_52', file: 'al_5_2.html', charts: 2, seasonal: ['echart_al_52_c1'] },
  { key: 'al_53', file: 'al_5_3.html', charts: 1, seasonal: ['echart_al_53_c1'] },
  { key: 'al_63', file: 'al_6_3.html', charts: 1, seasonal: ['echart_al_63_c1'] },
  { key: 'al_71', file: 'al_7_1.html', charts: 2, seasonal: ['echart_al_71_c1'] },
  { key: 'al_72', file: 'al_7_2.html', charts: 2, seasonal: ['echart_al_72_c1','echart_al_72_c2'] },
  { key: 'al_312', file: 'al_3_1_2.html', charts: 3, seasonal: ['echart_al_312_c1'] },
  { key: 'al_314', file: 'al_3_1_4.html', charts: 3, seasonal: ['echart_al_314_c1'] },
  { key: 'al_61', file: 'al_6_1.html', charts: 2, seasonal: ['echart_al_61_c1'] },
  { key: 'al_64', file: 'al_6_4.html', charts: 3, seasonal: ['echart_al_64_c1'] },
  { key: 'al_73', file: 'al_7_3.html', charts: 3, seasonal: ['echart_al_73_c1'] },
  { key: 'cu_21', file: 'cu_2_1.html', charts: 4, seasonal: ['echart_cu_21_c1'] },
  { key: 'cu_22', file: 'cu_2_2.html', charts: 2, seasonal: ['echart_cu_22_c1','echart_cu_22_c2'] },
  { key: 'cu_23', file: 'cu_2_3.html', seasonal: ['echart_cu_23_c1','echart_cu_23_c3'] },
  { key: 'cu_24', file: 'cu_2_4.html', charts: 4, seasonal: ['echart_cu_24_c1','echart_cu_24_c4'] },
  { key: 'cu_25', file: 'cu_2_5.html', charts: 2, seasonal: [] },
  { key: 'cu_26', file: 'cu_2_6.html', charts: 2, seasonal: ['echart_cu_26_c2'] },
  { key: 'cu_311', file: 'cu_3_1_1.html', charts: 2, seasonal: ['echart_cu_311_c2'] },
  { key: 'cu_312', file: 'cu_3_1_2.html', charts: 1, seasonal: [] },
  { key: 'cu_313', file: 'cu_3_1_3.html', charts: 2, seasonal: ['echart_cu_313_c1','echart_cu_313_c2'] },
  { key: 'cu_314', file: 'cu_3_1_4.html', charts: 1, seasonal: ['echart_cu_314_c1'] },
  { key: 'cu_315', file: 'cu_3_1_5.html', seasonal: ['echart_cu_315_c3'] },
  { key: 'cu_321', file: 'cu_3_2_1.html', seasonal: ['echart_cu_321_c1'] },
  { key: 'cu_322', file: 'cu_3_2_2.html', charts: 2, seasonal: ['echart_cu_322_c1'] },
  { key: 'cu_324', file: 'cu_3_2_4.html', charts: 2, seasonal: [] },
  { key: 'cu_61', file: 'cu_6_1.html', charts: 2, seasonal: ['echart_cu_61_c1','echart_cu_61_c2'] },
  { key: 'cu_62', file: 'cu_6_2.html', charts: 2, seasonal: ['echart_cu_62_c1','echart_cu_62_c2'] },
  { key: 'cu_63', file: 'cu_6_3.html', charts: 3, seasonal: ['echart_cu_63_c1'] },
  { key: 'cu_64', file: 'cu_6_4.html', charts: 3, seasonal: ['echart_cu_64_c1'] },
  { key: 'cu_323', file: 'cu_3_2_3.html', charts: 1, seasonal: ['echart_cu_323_c1'] },
  { key: 'cu_41', file: 'cu_4_1.html', charts: 3, seasonal: ['echart_cu_41_c1'] },
  { key: 'cu_42', file: 'cu_4_2.html', charts: 2, seasonal: ['echart_cu_42_c1'] },
  { key: 'cu_43', file: 'cu_4_3.html', charts: 2, seasonal: [] },
  { key: 'cu_51', file: 'cu_5_1.html', charts: 2, seasonal: ['echart_cu_51_c1'] },
  { key: 'cu_52', file: 'cu_5_2.html', charts: 3, seasonal: ['echart_cu_52_c1'] },
  { key: 'cu_53', file: 'cu_5_3.html', charts: 3, seasonal: ['echart_cu_53_c1'] },
  { key: 'cu_44', file: 'cu_4_4.html', charts: 1, seasonal: [] },
  { key: 'cu_45', file: 'cu_4_5.html', charts: 2, seasonal: [] },
  { key: 'cu_71', file: 'cu_7_1.html', charts: 1, seasonal: [] },
  { key: 'cu_72', file: 'cu_7_2.html', charts: 2, seasonal: [] },
  { key: 'cu_73', file: 'cu_7_3.html', charts: 1, seasonal: [] },
  { key: 'al_311', file: 'al_3_1_1.html', charts: 2, seasonal: ['echart_al_311_c1'] },
  { key: 'al_313', file: 'al_3_1_3.html', charts: 1, seasonal: ['echart_al_313_c1'] },
  { key: 'al_315', file: 'al_3_1_5.html', charts: 2, seasonal: ['echart_al_315_c1'] },
  { key: 'al_321', file: 'al_3_2_1.html', charts: 1, seasonal: ['echart_al_321_c1'] },
  { key: 'al_322', file: 'al_3_2_2.html', charts: 1, seasonal: ['echart_al_322_c1'] },
  { key: 'al_324', file: 'al_3_2_4.html', charts: 1, seasonal: ['echart_al_324_c1'] },
  { key: 'al_62', file: 'al_6_2.html', charts: 1, seasonal: ['echart_al_62_c1'] },
  // === 五金属 ZN 锌 (2026-08-31) ===
  { key: 'zn_21', file: 'zn_2_1.html', charts: 4, seasonal: ['echart_zn_21_c1'] },
  { key: 'zn_22', file: 'zn_2_2.html', charts: 4, seasonal: ['echart_zn_22_c1'] },
  { key: 'zn_23', file: 'zn_2_3.html', charts: 4, seasonal: ['echart_zn_23_c1'] },
  { key: 'zn_24', file: 'zn_2_4.html', charts: 3, seasonal: ['echart_zn_24_c1'] },
  { key: 'zn_25', file: 'zn_2_5.html', charts: 4, seasonal: ['echart_zn_25_c1'] },
  { key: 'zn_26', file: 'zn_2_6.html', charts: 4, seasonal: ['echart_zn_26_c1'] },
  { key: 'zn_311', file: 'zn_3_1_1.html', charts: 4, seasonal: ['echart_zn_311_c1'] },
  { key: 'zn_312', file: 'zn_3_1_2.html', charts: 4, seasonal: [] },
  { key: 'zn_313', file: 'zn_3_1_3.html', charts: 2, seasonal: ['echart_zn_313_c1'] },
  { key: 'zn_314', file: 'zn_3_1_4.html', charts: 4, seasonal: ['echart_zn_314_c1'] },
  { key: 'zn_315', file: 'zn_3_1_5.html', charts: 4, seasonal: ['echart_zn_315_c1'] },
  { key: 'zn_321', file: 'zn_3_2_1.html', charts: 4, seasonal: ['echart_zn_321_c1'] },
  { key: 'zn_322', file: 'zn_3_2_2.html', charts: 3, seasonal: ['echart_zn_322_c1'] },
  { key: 'zn_323', file: 'zn_3_2_3.html', charts: 4, seasonal: ['echart_zn_323_c1'] },
  { key: 'zn_324', file: 'zn_3_2_4.html', charts: 4, seasonal: ['echart_zn_324_c1'] },
  { key: 'zn_41', file: 'zn_4_1.html', charts: 3, seasonal: ['echart_zn_41_c1'] },
  { key: 'zn_42', file: 'zn_4_2.html', charts: 2, seasonal: ['echart_zn_42_c1'] },
  { key: 'zn_43', file: 'zn_4_3.html', charts: 3, seasonal: ['echart_zn_43_c1'] },
  { key: 'zn_44', file: 'zn_4_4.html', charts: 3, seasonal: ['echart_zn_44_c1'] },
  { key: 'zn_45', file: 'zn_4_5.html', charts: 1, seasonal: ['echart_zn_45_c1'] },
  { key: 'zn_51', file: 'zn_5_1.html', charts: 2, seasonal: ['echart_zn_51_c1'] },
  { key: 'zn_52', file: 'zn_5_2.html', charts: 4, seasonal: ['echart_zn_52_c1'] },
  { key: 'zn_53', file: 'zn_5_3.html', charts: 4, seasonal: ['echart_zn_53_c1'] },
  { key: 'zn_61', file: 'zn_6_1.html', charts: 2, seasonal: ['echart_zn_61_c1'] },
  { key: 'zn_62', file: 'zn_6_2.html', charts: 2, seasonal: [] },
  { key: 'zn_63', file: 'zn_6_3.html', charts: 2, seasonal: ['echart_zn_63_c1'] },
  { key: 'zn_64', file: 'zn_6_4.html', charts: 1, seasonal: [] },
  { key: 'zn_71', file: 'zn_7_1.html', charts: 2, seasonal: ['echart_zn_71_c1'] },
  { key: 'zn_72', file: 'zn_7_2.html', charts: 2, seasonal: ['echart_zn_72_c1'] },
  { key: 'ni_21', file: 'ni_2_1.html', charts: 4, seasonal: ['echart_ni_21_c1'] },
  { key: 'ni_22', file: 'ni_2_2.html', charts: 4, seasonal: ['echart_ni_22_c1'] },
  { key: 'ni_23', file: 'ni_2_3.html', charts: 3, seasonal: ['echart_ni_23_c1'] },
  { key: 'ni_24', file: 'ni_2_4.html', charts: 4, seasonal: [] },
  { key: 'ni_25', file: 'ni_2_5.html', charts: 4, seasonal: ['echart_ni_25_c1'] },
  { key: 'ni_26', file: 'ni_2_6.html', charts: 2, seasonal: ['echart_ni_26_c1'] },
  { key: 'ni_311', file: 'ni_3_1_1.html', charts: 4, seasonal: [] },
  { key: 'ni_312', file: 'ni_3_1_2.html', charts: 4, seasonal: [] },
  { key: 'ni_313', file: 'ni_3_1_3.html', charts: 2, seasonal: ['echart_ni_313_c1'] },
  { key: 'ni_314', file: 'ni_3_1_4.html', charts: 4, seasonal: ['echart_ni_314_c1'] },
  { key: 'ni_315', file: 'ni_3_1_5.html', charts: 2, seasonal: ['echart_ni_315_c1'] },
  { key: 'ni_321', file: 'ni_3_2_1.html', charts: 4, seasonal: ['echart_ni_321_c1'] },
  { key: 'ni_322', file: 'ni_3_2_2.html', charts: 3, seasonal: ['echart_ni_322_c1'] },
  { key: 'ni_323', file: 'ni_3_2_3.html', charts: 3, seasonal: ['echart_ni_323_c1'] },
  { key: 'ni_324', file: 'ni_3_2_4.html', charts: 2, seasonal: ['echart_ni_324_c1'] },
  { key: 'ni_41', file: 'ni_4_1.html', charts: 3, seasonal: ['echart_ni_41_c1'] },
  { key: 'ni_42', file: 'ni_4_2.html', charts: 3, seasonal: ['echart_ni_42_c1'] },
  { key: 'ni_43', file: 'ni_4_3.html', charts: 4, seasonal: ['echart_ni_43_c1'] },
  { key: 'ni_44', file: 'ni_4_4.html', charts: 4, seasonal: ['echart_ni_44_c1'] },
  { key: 'ni_45', file: 'ni_4_5.html', charts: 4, seasonal: ['echart_ni_45_c1'] },
  { key: 'ni_51', file: 'ni_5_1.html', charts: 4, seasonal: ['echart_ni_51_c1'] },
  { key: 'ni_52', file: 'ni_5_2.html', charts: 2, seasonal: ['echart_ni_52_c1'] },
  { key: 'ni_53', file: 'ni_5_3.html', charts: 3, seasonal: ['echart_ni_53_c1'] },
  { key: 'ni_61', file: 'ni_6_1.html', charts: 4, seasonal: ['echart_ni_61_c1'] },
  { key: 'ni_62', file: 'ni_6_2.html', charts: 4, seasonal: ['echart_ni_62_c1'] },
  { key: 'ni_63', file: 'ni_6_3.html', charts: 3, seasonal: ['echart_ni_63_c1'] },
  { key: 'ni_64', file: 'ni_6_4.html', charts: 1, seasonal: ['echart_ni_64_c1'] },
  { key: 'ni_71', file: 'ni_7_1.html', charts: 4, seasonal: ['echart_ni_71_c1'] },
  { key: 'ni_72', file: 'ni_7_2.html', charts: 4, seasonal: ['echart_ni_72_c1'] },
  { key: 'ni_73', file: 'ni_7_3.html', charts: 4, seasonal: ['echart_ni_73_c1'] },
  { key: 'sn_21', file: 'sn_2_1.html', charts: 4, seasonal: ['echart_sn_21_c1'] },
  { key: 'sn_22', file: 'sn_2_2.html', charts: 4, seasonal: ['echart_sn_22_c1'] },
  { key: 'sn_23', file: 'sn_2_3.html', charts: 3, seasonal: ['echart_sn_23_c1'] },
  { key: 'sn_24', file: 'sn_2_4.html', charts: 2, seasonal: ['echart_sn_24_c1'] },
  { key: 'sn_25', file: 'sn_2_5.html', charts: 3, seasonal: ['echart_sn_25_c1'] },
  { key: 'sn_26', file: 'sn_2_6.html', charts: 4, seasonal: ['echart_sn_26_c1'] },
  { key: 'sn_311', file: 'sn_3_1_1.html', charts: 3, seasonal: [] },
  { key: 'sn_312', file: 'sn_3_1_2.html', charts: 4, seasonal: ['echart_sn_312_c1'] },
  { key: 'sn_313', file: 'sn_3_1_3.html', charts: 4, seasonal: [] },
  { key: 'sn_314', file: 'sn_3_1_4.html', charts: 4, seasonal: ['echart_sn_314_c1'] },
  { key: 'sn_315', file: 'sn_3_1_5.html', charts: 2, seasonal: ['echart_sn_315_c1'] },
  { key: 'sn_321', file: 'sn_3_2_1.html', charts: 4, seasonal: [] },
  { key: 'sn_322', file: 'sn_3_2_2.html', charts: 2, seasonal: ['echart_sn_322_c1'] },
  { key: 'sn_323', file: 'sn_3_2_3.html', charts: 4, seasonal: [] },
  { key: 'sn_41', file: 'sn_4_1.html', charts: 2, seasonal: ['echart_sn_41_c1'] },
  { key: 'sn_42', file: 'sn_4_2.html', charts: 3, seasonal: ['echart_sn_42_c1'] },
  { key: 'sn_43', file: 'sn_4_3.html', charts: 3, seasonal: ['echart_sn_43_c1'] },
  { key: 'sn_44', file: 'sn_4_4.html', charts: 2, seasonal: ['echart_sn_44_c1'] },
  { key: 'sn_45', file: 'sn_4_5.html', charts: 1, seasonal: ['echart_sn_45_c1'] },
  { key: 'sn_51', file: 'sn_5_1.html', charts: 3, seasonal: ['echart_sn_51_c1'] },
  { key: 'sn_52', file: 'sn_5_2.html', charts: 4, seasonal: ['echart_sn_52_c1'] },
  { key: 'sn_53', file: 'sn_5_3.html', charts: 1, seasonal: ['echart_sn_53_c1'] },
  { key: 'sn_61', file: 'sn_6_1.html', charts: 4, seasonal: [] },
  { key: 'sn_62', file: 'sn_6_2.html', charts: 4, seasonal: ['echart_sn_62_c1'] },
  { key: 'sn_63', file: 'sn_6_3.html', charts: 4, seasonal: ['echart_sn_63_c1'] },
  { key: 'sn_64', file: 'sn_6_4.html', charts: 2, seasonal: ['echart_sn_64_c1'] },
  { key: 'sn_71', file: 'sn_7_1.html', charts: 4, seasonal: ['echart_sn_71_c1'] },
  { key: 'sn_72', file: 'sn_7_2.html', charts: 4, seasonal: ['echart_sn_72_c1'] },
  { key: 'sn_73', file: 'sn_7_3.html', charts: 4, seasonal: ['echart_sn_73_c1'] },
  { key: 'si_21', file: 'si_2_1.html', charts: 4, seasonal: ['echart_si_21_c1'] },
  { key: 'si_22', file: 'si_2_2.html', charts: 3, seasonal: ['echart_si_22_c1'] },
  { key: 'si_23', file: 'si_2_3.html', charts: 2, seasonal: ['echart_si_23_c1'] },
  { key: 'si_24', file: 'si_2_4.html', charts: 4, seasonal: ['echart_si_24_c1'] },
  { key: 'si_25', file: 'si_2_5.html', charts: 4, seasonal: ['echart_si_25_c1'] },
  { key: 'si_26', file: 'si_2_6.html', charts: 4, seasonal: ['echart_si_26_c1'] },
  { key: 'si_311', file: 'si_3_1_1.html', charts: 3, seasonal: ['echart_si_311_c1'] },
  { key: 'si_312', file: 'si_3_1_2.html', charts: 4, seasonal: ['echart_si_312_c1'] },
  { key: 'si_314', file: 'si_3_1_4.html', charts: 2, seasonal: ['echart_si_314_c1'] },
  { key: 'si_315', file: 'si_3_1_5.html', charts: 3, seasonal: ['echart_si_315_c1'] },
  { key: 'si_321', file: 'si_3_2_1.html', charts: 3, seasonal: ['echart_si_321_c1'] },
  { key: 'si_322', file: 'si_3_2_2.html', charts: 4, seasonal: ['echart_si_322_c1'] },
  { key: 'si_323', file: 'si_3_2_3.html', charts: 3, seasonal: ['echart_si_323_c1'] },
  { key: 'si_324', file: 'si_3_2_4.html', charts: 4, seasonal: ['echart_si_324_c1'] },
  { key: 'si_41', file: 'si_4_1.html', charts: 3, seasonal: ['echart_si_41_c1'] },
  { key: 'si_42', file: 'si_4_2.html', charts: 4, seasonal: ['echart_si_42_c1'] },
  { key: 'si_43', file: 'si_4_3.html', charts: 2, seasonal: ['echart_si_43_c1'] },
  { key: 'si_44', file: 'si_4_4.html', charts: 2, seasonal: [] },
  { key: 'si_45', file: 'si_4_5.html', charts: 2, seasonal: [] },
  { key: 'si_51', file: 'si_5_1.html', charts: 3, seasonal: [] },
  { key: 'si_52', file: 'si_5_2.html', charts: 1, seasonal: ['echart_si_52_c1'] },
  { key: 'si_61', file: 'si_6_1.html', charts: 4, seasonal: ['echart_si_61_c1'] },
  { key: 'si_62', file: 'si_6_2.html', charts: 3, seasonal: ['echart_si_62_c1'] },
  { key: 'si_63', file: 'si_6_3.html', charts: 3, seasonal: ['echart_si_63_c1'] },
  { key: 'si_64', file: 'si_6_4.html', charts: 3, seasonal: ['echart_si_64_c1'] },
  { key: 'si_71', file: 'si_7_1.html', charts: 4, seasonal: ['echart_si_71_c1'] },
  { key: 'si_72', file: 'si_7_2.html', charts: 4, seasonal: ['echart_si_72_c1'] },
  { key: 'li_21', file: 'li_2_1.html', charts: 4, seasonal: [] },
  { key: 'li_22', file: 'li_2_2.html', charts: 4, seasonal: [] },
  { key: 'li_24', file: 'li_2_4.html', charts: 2, seasonal: [] },
  { key: 'li_25', file: 'li_2_5.html', charts: 3, seasonal: [] },
  { key: 'li_26', file: 'li_2_6.html', charts: 4, seasonal: [] },
  { key: 'li_311', file: 'li_3_1_1.html', charts: 2, seasonal: ['echart_li_311_c1'] },
  { key: 'li_312', file: 'li_3_1_2.html', charts: 1, seasonal: [] },
  { key: 'li_313', file: 'li_3_1_3.html', charts: 2, seasonal: [] },
  { key: 'li_321', file: 'li_3_2_1.html', charts: 4, seasonal: ['echart_li_321_c1'] },
  { key: 'li_323', file: 'li_3_2_3.html', charts: 3, seasonal: ['echart_li_323_c1'] },
  { key: 'li_324', file: 'li_3_2_4.html', charts: 3, seasonal: [] },
  { key: 'li_41', file: 'li_4_1.html', charts: 3, seasonal: [] },
  { key: 'li_42', file: 'li_4_2.html', charts: 4, seasonal: [] },
  { key: 'li_43', file: 'li_4_3.html', charts: 2, seasonal: [] },
  { key: 'li_44', file: 'li_4_4.html', charts: 4, seasonal: [] },
];

function expectedBtnText(mode) {
  return mode === 'ts' ? '☀ 季节' : '⏱ 时序';
}

function loadPage(file) {
  const html = fs.readFileSync(path.join(ROOT, file), 'utf-8');
  const dom = new JSDOM(html, {
    runScripts: 'dangerously',
    resources: undefined,
    pretendToBeVisual: true,
    beforeParse(win) {
      const store = {};
      win.echarts = {
        init: (el) => {
          const inst = {
            _el: el && el.id,
            _last: null,
            setOption(opt) { this._last = opt; store[el && el.id] = opt; },
            resize() {},
          };
          return inst;
        },
        getInstanceByDom: (el) => (el && el.id && store[el.id] !== undefined) ? { resize() {} } : null,
      };
    },
  });
  return dom;
}

let failures = 0;
const results = [];

for (const p of PAGES) {
  const dom = loadPage(p.file);
  const win = dom.window;
  const doc = win.document;
  const checks = [];

  // 1. __seasonalizeByYear 存在
  const hasByYear = typeof win.__seasonalizeByYear === 'function';
  checks.push(['__seasonalizeByYear 函数存在', hasByYear, hasByYear ? '' : '未定义']);

  // 图表容器数量（配置驱动，默认 3；4 图页需在 PAGES 显式声明 charts:4）
  const nChart = doc.querySelectorAll('div.chart').length;
  const expCharts = p.charts || 3;
  checks.push(['chart 容器数=' + expCharts, nChart === expCharts, '实际 ' + nChart]);

  for (const cid of p.seasonal) {
    const data = win['__data_' + cid];
    const nPts = Array.isArray(data) ? data.length : 0;
    checks.push([cid + ' 数据点数>20', nPts > 20, nPts + ' 点']);

    // 从 opts.se.series 直接读真实生成的 series
    const opts = win['__opts_' + cid];
    if (!opts || !opts.se || !opts.se.series) {
      checks.push([cid + ' opts.se.series 存在', false, 'opts 或 se 或 series 缺失']);
      continue;
    }
    const series = opts.se.series;
    const seriesLen = Array.isArray(series) ? series.length : 0;
    // series 数量 = 年份数（>=3，<=6 合理范围）
    checks.push([cid + ' 历年 series 数量≥3', seriesLen >= 3,
      '实际 ' + seriesLen + ' 条线']);

    if (seriesLen > 0) {
      // 每个 series 验证：长度按粒度 12(月度) 或 365(日度)
      const dayish = series.some(s => Array.isArray(s.data) && s.data.length === 365);
      const monthLenOk = series.every(s => Array.isArray(s.data)
        && (s.data.length === 12 || s.data.length === 365));
      checks.push([cid + ' 每条线长度=12或365', monthLenOk,
        monthLenOk ? '' : '某条线长度≠12/365']);

      const minNonNull = dayish ? 30 : 3;
      const allHaveData = series.every(s => (s.data || []).filter(v => v !== null).length >= minNonNull);
      checks.push([cid + ' 每条线非空' + (dayish ? '日' : '月') + '≥' + minNonNull, allHaveData,
        allHaveData ? '' : '某条线有效' + (dayish ? '日' : '月') + '<' + minNonNull]);

      const allNamesHaveYear = series.every(s => /年/.test(s.name || ''));
      checks.push([cid + ' 图例含年份名', allNamesHaveYear,
        allNamesHaveYear ? '' : '图例名缺"年"字']);

      // 打印实际 series 名称，便于人工核对
      const names = series.map(s => s.name).join(', ');
      console.log('    [INFO] ' + cid + ' 年份线: ' + names);
    }

    // __tgl：mode 翻转 + 按钮文字
    const hasInst = !!win['__inst_' + cid];
    const hasMode = win['__mode_' + cid] !== undefined;
    const initMode = win['__mode_' + cid];
    checks.push([cid + ' inst+mode 已初始化', hasInst && hasMode,
      'inst=' + hasInst + ' mode=' + (initMode || 'undefined')]);

    if (hasInst && hasMode && typeof win.__tgl === 'function') {
      const btn = doc.querySelector('button[onclick*="' + cid + '"]');
      if (!btn) {
        checks.push([cid + ' 季节按钮存在', false, '未找到按钮']);
      } else {
        const initTxt = btn.textContent.trim();
        const expInit = expectedBtnText(initMode);
        checks.push([cid + ' 初始按钮文字匹配 mode(' + initMode + ')',
          initTxt === expInit, '实际「' + initTxt + '」 期望「' + expInit + '」']);

        try {
          win.__tgl(cid, btn);
          const after = win['__mode_' + cid];
          const txtAfter = btn.textContent.trim();
          const expAfter = expectedBtnText(after);
          checks.push([cid + ' __tgl mode 翻转', initMode !== after, initMode + '→' + after]);
          checks.push([cid + ' 点击后按钮文字匹配 mode(' + after + ')',
            txtAfter === expAfter, '实际「' + txtAfter + '」 期望「' + expAfter + '」']);

          // 切换后 setOption 是否被调用：收到的 option 必须与切换后的 mode 一致
          // （se=历年多线≥3，ts=单条时序线<3；兼容默认 ts 与默认 se 两种页面）
          const lastOpt = win['__inst_' + cid]._last;
          const isSeasonOpt = after === 'se'
            ? !!(lastOpt && lastOpt.series && lastOpt.series.length >= 3)
            : !!(lastOpt && Array.isArray(lastOpt.series) && lastOpt.series.length < 3);
          checks.push([cid + ' __tgl 后 setOption 匹配 mode(' + after + ')', isSeasonOpt,
            isSeasonOpt ? '' : 'setOption 未收到当前 mode 的 series']);
        } catch (e) {
          checks.push([cid + ' __tgl 调用', false, '抛异常: ' + e.message]);
        }
      }
    }
  }

  // DOM 存在性检查：按本页实际图数循环（2 图页不会找 _c3）
  for (let i = 1; i <= expCharts; i++) {
    const cid = 'echart_' + p.key + '_c' + i;
    checks.push([cid + ' DOM 存在', !!doc.getElementById(cid), '']);
  }

  const ok = checks.every(c => c[1]);
  if (!ok) failures++;
  results.push({ key: p.key, file: p.file, ok, checks });
}

console.log('='.repeat(74));
console.log('framework-tree 渲染验证 v1.1 (jsdom + ECharts mock, 历年 series)');
console.log('='.repeat(74));
for (const r of results) {
  console.log('\n%s %s %s  (%s)', r.ok ? 'OK' : 'XX', r.key, r.ok ? 'PASS' : 'FAIL', r.file);
  for (const [name, good, detail] of r.checks) {
    console.log('    [%s] %-48s %s', good ? 'PASS' : 'FAIL', name, good ? '' : '← ' + detail);
  }
}
console.log('\n' + '='.repeat(74));
console.log('总结: %d/%d 页通过 → %s', PAGES.length - failures, PAGES.length,
  failures === 0 ? 'ALL PASS' : (failures + ' 页 FAIL'));
console.log('='.repeat(74));
process.exit(failures === 0 ? 0 : 1);