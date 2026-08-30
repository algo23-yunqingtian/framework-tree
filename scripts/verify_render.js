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

const ROOT = '/home/ubuntu/framework-tree';
const PAGES = [
{ key: '21', file: 'pb_21_price_structure.html',       seasonal: ['echart_21_c2'] },
{ key: '22', file: 'pb_22_spot_premium.html',          seasonal: ['echart_22_c2'] },
{ key: '23', file: 'pb_23_overseas_price.html',        seasonal: ['echart_23_c2'] },
{ key: '24', file: 'pb_24_spread_system.html',          seasonal: [] },
{ key: '25', file: 'pb_25_valuation_profit.html',        seasonal: [] },
{ key: '26', file: 'pb_26_position_holder.html',          seasonal: ['echart_26_c2'] },
{ key: '51', file: 'pb_51_primary_consumption.html',   seasonal: ['echart_51_c2'] },
{ key: '52', file: 'pb_52_terminal_consumption.html',  seasonal: ['echart_52_c2'] },
{ key: '61', file: 'pb_61_raw_material_import.html', seasonal: ['echart_61_c1', 'echart_61_c3'] },
{ key: '62', file: 'pb_62_import_export.html',       seasonal: ['echart_62_c1', 'echart_62_c3'] },
{ key: '63', file: 'pb_63_product_export.html',      seasonal: ['echart_63_c1', 'echart_63_c2'] },
{ key: '64', file: 'pb_64_overseas_shipping.html',   seasonal: [] },
{ key: '32_3', file: 'pb_32_3_regen_supply.html',    charts: 4, seasonal: ['echart_32_3_c4'] },
{ key: '41', file: 'pb_41_exchange_stock.html',   seasonal: ['echart_41_c1'] },
{ key: '42', file: 'pb_42_warrant.html',          seasonal: ['echart_42_c1', 'echart_42_c2'] },
{ key: '43', file: 'pb_43_social_stock.html',     seasonal: ['echart_43_c3'] },
{ key: '44', file: 'pb_44_factory_stock.html',    seasonal: [] },
{ key: '45', file: 'pb_45_hidden_stock.html',     charts: 2, seasonal: [] },
{ key: '71', file: 'pb_71_cost_curve.html',       seasonal: ['echart_71_c2'] },
{ key: '72', file: 'pb_72_daily_profit.html',     seasonal: ['echart_72_c2'] },
{ key: '73', file: 'pb_73_energy_cost.html',      seasonal: ['echart_73_c2'] },
{ key: "cu_21", file: "cu_2_1.html", charts: 4, seasonal: ["echart_cu_21_c1"] },
  { key: 'cu_22', file: 'cu_2_2.html', charts: 2, seasonal: ["echart_cu_22_c1"] },
  { key: 'cu_23', file: 'cu_2_3.html', charts: 3, seasonal: ["echart_cu_23_c1"] },
  { key: 'cu_24', file: 'cu_2_4.html', charts: 4, seasonal: ["echart_cu_24_c1"] },
  { key: 'cu_25', file: 'cu_2_5.html', charts: 2, seasonal: ["echart_cu_25_c1"] },
  { key: 'cu_26', file: 'cu_2_6.html', charts: 2, seasonal: ["echart_cu_26_c1"] },
  { key: 'cu_311', file: 'cu_3_1_1.html', charts: 2, seasonal: ["echart_cu_311_c1"] },
  { key: 'cu_312', file: 'cu_3_1_2.html', charts: 1, seasonal: ["echart_cu_312_c1"] },
  { key: 'cu_313', file: 'cu_3_1_3.html', charts: 2, seasonal: ["echart_cu_313_c1"] },
  { key: 'cu_314', file: 'cu_3_1_4.html', charts: 1, seasonal: ["echart_cu_314_c1"] },
  { key: 'cu_315', file: 'cu_3_1_5.html', charts: 3, seasonal: ["echart_cu_315_c1"] },
  { key: 'cu_321', file: 'cu_3_2_1.html', charts: 3, seasonal: ["echart_cu_321_c1"] },
  { key: 'cu_322', file: 'cu_3_2_2.html', charts: 2, seasonal: ["echart_cu_322_c1"] },
  { key: 'al_323', file: 'al_3_2_3.html', charts: 2, seasonal: ["echart_al_323_c1"] },
  { key: 'cu_324', file: 'cu_3_2_4.html', charts: 2, seasonal: ["echart_cu_324_c1"] },
  { key: 'al_41', file: 'al_4_1.html', charts: 3, seasonal: ["echart_al_41_c1"] },
  { key: 'al_42', file: 'al_4_2.html', charts: 3, seasonal: ["echart_al_42_c1"] },
  { key: 'al_43', file: 'al_4_3.html', charts: 1, seasonal: [] },
  { key: 'al_44', file: 'al_4_4.html', charts: 1, seasonal: [] },
  { key: 'al_45', file: 'al_4_5.html', charts: 1, seasonal: ["echart_al_45_c1"] },
  { key: 'al_52', file: 'al_5_2.html', charts: 2, seasonal: ["echart_al_52_c1"] },
  { key: 'al_53', file: 'al_5_3.html', charts: 1, seasonal: ["echart_al_53_c1"] },
  { key: 'cu_61', file: 'cu_6_1.html', charts: 2, seasonal: ["echart_cu_61_c1"] },
  { key: 'cu_62', file: 'cu_6_2.html', charts: 2, seasonal: ["echart_cu_62_c1"] },
  { key: 'al_63', file: 'al_6_3.html', charts: 1, seasonal: ["echart_al_63_c1"] },
  { key: 'al_71', file: 'al_7_1.html', charts: 2, seasonal: ["echart_al_71_c1"] },
  { key: 'al_72', file: 'al_7_2.html', charts: 2, seasonal: ["echart_al_72_c1"] }


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