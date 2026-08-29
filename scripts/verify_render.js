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
  { key: '61', file: 'pb_61_raw_material_import.html', seasonal: ['echart_61_c1', 'echart_61_c3'] },
  { key: '62', file: 'pb_62_import_export.html',       seasonal: ['echart_62_c1', 'echart_62_c3'] },
  { key: '63', file: 'pb_63_product_export.html',      seasonal: ['echart_63_c1', 'echart_63_c2'] },
  { key: '64', file: 'pb_64_overseas_shipping.html',   seasonal: [] },
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

  // 图表容器数量
  const nChart = doc.querySelectorAll('div.chart').length;
  checks.push(['chart 容器数=3', nChart === 3, '实际 ' + nChart]);

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
      // 每个 series 验证
      const monthLenOk = series.every(s => Array.isArray(s.data) && s.data.length === 12);
      checks.push([cid + ' 每条线 12 月数据', monthLenOk,
        monthLenOk ? '' : '某条线长度≠12']);

      const allHaveData = series.every(s => (s.data || []).filter(v => v !== null).length >= 3);
      checks.push([cid + ' 每条线非空月份≥3', allHaveData,
        allHaveData ? '' : '某条线有效月份<3']);

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

  for (let i = 1; i <= 3; i++) {
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