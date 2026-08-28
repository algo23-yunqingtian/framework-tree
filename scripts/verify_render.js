/**
 * verify_render.js — framework-tree 页面真实渲染验证（P1/P2 验收门禁）
 *
 * 做法：用 jsdom 加载真实 HTML，mock 掉 ECharts（jsdom 无 canvas），
 *       通过 echarts.init 捕获 window.__opts_*，直接调用页面内的
 *       __seasonalize / __tgl 函数，验证"季节按钮切换"是否产出真数据。
 *
 * 校验点：
 *   1. __seasonalize 存在且可调用
 *   2. 对每个含季节模式的图，__seasonalize(data) 产出 12 个月均值（非 null ≥ 6）
 *   3. __tgl 切换后 mode 翻转 + 按钮文字与 mode 对应关系正确
 *      （按钮文字 = 点击后将要切到的视图：ts 状态→"☀ 季节"，se 状态→"⏱ 时序"）
 *   4. 无季节模式的页（64）跳过 2/3
 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('/tmp/node_modules/jsdom');

const ROOT = '/home/ubuntu/framework-tree';
const PAGES = [
  { key: '61', file: 'pb_61_raw_material_import.html', seasonal: ['echart_61_c1', 'echart_61_c3'] },
  { key: '62', file: 'pb_62_import_export.html',       seasonal: ['echart_62_c1', 'echart_62_c3'] },
  { key: '63', file: 'pb_63_product_export.html',      seasonal: ['echart_63_c1', 'echart_63_c2'] },
  { key: '64', file: 'pb_64_overseas_shipping.html',   seasonal: [] },
];

// 按钮文字 ↔ mode 对应关系（按钮显示"点击后将切到的视图"）
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

  // 1. __seasonalize 存在
  const hasSzn = typeof win.__seasonalize === 'function';
  checks.push(['__seasonalize 函数存在', hasSzn, hasSzn ? '' : '未定义']);

  // 图表容器数量
  const nChart = doc.querySelectorAll('div.chart').length;
  checks.push(['chart 容器数=3', nChart === 3, '实际 ' + nChart]);

  for (const cid of p.seasonal) {
    const data = win['__data_' + cid];
    const nPts = Array.isArray(data) ? data.length : 0;
    checks.push([cid + ' 数据点数>20', nPts > 20, nPts + ' 点']);

    // 2. __seasonalize 产出 12 个月均值
    let seData = null, nonNull = 0;
    if (hasSzn && Array.isArray(data)) {
      try {
        seData = win.__seasonalize(data);
        nonNull = (seData || []).filter(v => v !== null).length;
      } catch (e) {
        checks.push([cid + ' __seasonalize 调用', false, '抛异常: ' + e.message]);
        continue;
      }
      const ok = seData.length === 12 && nonNull >= 6;
      checks.push([cid + ' 季节数据=12月且非空≥6', ok,
        'len=' + (seData ? seData.length : 'null') + ' 非空=' + nonNull]);
    }

    // 3. __tgl：mode 翻转 + 按钮文字与 mode 对应关系
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
        // 初始状态：按钮文字应 = 点击后要切到的视图
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
console.log('framework-tree 渲染验证 (jsdom + ECharts mock)');
console.log('='.repeat(74));
for (const r of results) {
  console.log('\n%s %s %s  (%s)', r.ok ? 'OK' : 'XX', r.key, r.ok ? 'PASS' : 'FAIL', r.file);
  for (const [name, good, detail] of r.checks) {
    console.log('    [%s] %-42s %s', good ? 'PASS' : 'FAIL', name, good ? '' : '← ' + detail);
  }
}
console.log('\n' + '='.repeat(74));
console.log('总结: %d/%d 页通过 → %s', PAGES.length - failures, PAGES.length,
  failures === 0 ? 'ALL PASS' : (failures + ' 页 FAIL'));
console.log('='.repeat(74));
process.exit(failures === 0 ? 0 : 1);