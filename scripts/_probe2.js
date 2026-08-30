
const fs=require('fs'),path=require('path');
const {JSDOM}=require('/tmp/node_modules/jsdom');
const ROOT=path.resolve(__dirname,'..');
function load(f){const html=fs.readFileSync(path.join(ROOT,f),'utf-8');const store={};
 const dom=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,beforeParse(win){
  win.echarts={init:(el)=>{const i={setOption(o){store[el&&el.id]=o;},resize(){},dispose(){}};return i;},
   getInstanceByDom:()=>null};}});return dom;}
const files=fs.readdirSync(ROOT).filter(f=>/^(cu|al)_[2-7][0-9_]*\.html$/.test(f)&&!f.endsWith('overview.html')).sort();
const out=[];
for(const f of files){
 const dom=load(f),w=dom.window,d=w.document;
 const nChart=d.querySelectorAll('div.chart').length;
 for(const k of Object.keys(w)){
  const m=k.match(/^__opts_(echart_[a-z0-9_]+)$/); if(!m)continue;
  const cid=m[1];
  if(!d.getElementById(cid)) continue;
  const mode=w['__mode_'+cid];
  if(mode===undefined) continue;
  const o=w['__opts_'+cid];
  const seSeries=o&&o.se&&o.se.series?o.se.series.length:0;
  const data=w['__data_'+cid]; const nPts=Array.isArray(data)?data.length:0;
  const btn=!!d.querySelector('button[onclick*="'+cid+'"]');
  out.push({f,cid,mode,nPts,seSeries,btn,okToggle:btn&&seSeries>=3});
 }}
console.log(JSON.stringify(out));
