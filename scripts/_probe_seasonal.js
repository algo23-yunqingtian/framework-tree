// 全量探测铜铝 34 页：确定 verify_render 注册所需的 key / charts / seasonal
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('/tmp/node_modules/jsdom');
const ROOT = path.resolve(__dirname, '..');

function loadPage(file) {
  const html = fs.readFileSync(path.join(ROOT, file), 'utf-8');
  const store = {};
  const dom = new JSDOM(html, { runScripts: 'dangerously', resources: undefined, pretendToBeVisual: true,
    beforeParse(win) {
      win.echarts = { init: (el) => {
        const inst = { _el: el && el.id, _last: null,
          setOption(opt) { this._last = opt; store[el && el.id] = opt; }, resize() {}, dispose() {} };
        return inst;
      }, getInstanceByDom: (el) => (el && el.id && store[el.id] !== undefined) ? { resize() {} } : null };
      win.__store = store;
    }});
  return dom;
}

const files = fs.readdirSync(ROOT)
  .filter(f => /^(cu|al)_[2-7][0-9_]*\.html$/.test(f) && !f.endsWith('overview.html')).sort();

const rows = [];
for (const f of files) {
  const dom = loadPage(f);
  const win = dom.window, doc = win.document;
  const nChart = doc.querySelectorAll('div.chart').length;
  // key 从 cid 推断：echart_cu_21_c1 -> cu_21
  const cids = Object.keys(win.__store || {}).filter(k => /^echart_/.test(k)).sort();
  const seasonal = [], ts = [], non = [];
  for (const cid of cids) {
    const m = cid.match(/^echart_([a-z]+_[0-9]+)_c(\d+)$/);
    if (!m) { non.push(cid); continue; }
    const mode = win['__mode_' + cid];
    const o = win['__opts_' + cid];
    const seOk = !!(o && o.se && o.se.series);
    if (mode !== undefined && seOk) seasonal.push(cid);
    else if (mode !== undefined) ts.push(cid + '(mode但无se)');
    else non.push(cid + '(无mode)');
  }
  // 按钮检查
  const btns = cids.filter(c => doc.querySelector('button[onclick*="' + c + '"]'));
  rows.push({ file: f, nChart, key: (cids[0]||'').match(/^echart_([a-z]+_[0-9]+)_/)[1] || '?',
              seasonal: seasonal.map(c => c.match(/^echart_([a-z]+_[0-9]+)_/)[1] + '_c' + c.match(/_c(\d+)$/)[1]),
              btns, non: non.length });
}
console.log('file\t\tkey\t\tcharts\tseasonal\tbtns\t无toggle图');
for (const r of rows) {
  console.log([r.file, r.key, r.nChart, '[' + r.seasonal.join(',') + ']', r.btns.length, r.non].join('\t'));
}
// 生成 JS 注册片段
console.log('\n=== 建议 PAGES 注册片段（铜铝） ===');
for (const r of rows) {
  const chartsOpt = r.nChart !== 3 ? ' charts: ' + r.nChart + ',' : '';
  console.log("  { key: '" + r.key + "', file: '" + r.file + "'," + chartsOpt + " seasonal: [" + r.seasonal.map(s => "'" + s + "'").join(', ') + '] },');
}
