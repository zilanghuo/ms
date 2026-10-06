
'use strict';
let loadTimer, toastTimer;
function notify(message) {
 const el=document.getElementById('toast'); if(!el)return;
 el.textContent=message; el.hidden=false; clearTimeout(toastTimer);
 toastTimer=setTimeout(()=>{el.hidden=true;},4000);
}

function bindRangeEditor(root) {
 const form=root.querySelector('.report-range');if(!form)return;
 const start=form.querySelector('[name=start]'),end=form.querySelector('[name=end]');
 const status=form.querySelector('.range-status'),submit=form.querySelector('[type=submit]');
 start.value=root.dataset.start;end.value=root.dataset.end;
 const update=()=>{
  const dirty=start.value!==root.dataset.start||end.value!==root.dataset.end;
  const invalid=!start.value||!end.value||start.value>end.value||end.value>'2026-09-23';
  status.textContent=invalid?'请选择有效日期，开始日期不能晚于结束日期，结束日期不能晚于业务今天。':dirty?'日期已修改，点击“重新分析”后更新报告。':'当前报告日期已生效。';
  status.classList.toggle('date-error',invalid);
  submit.disabled=invalid;
  root.querySelector('#download-toggle').disabled=dirty||invalid;
  root.querySelector('#download-menu').hidden=true;
 };
 form.addEventListener('input',update);
 form.querySelectorAll('[data-days]').forEach(button=>button.onclick=()=>{
  const endDate=new Date('2026-09-22T00:00:00Z'),startDate=new Date(endDate);
  startDate.setUTCDate(startDate.getUTCDate()-Number(button.dataset.days)+1);
  start.value=startDate.toISOString().slice(0,10);end.value='2026-09-22';update();
 });
 form.querySelector('[data-reset-range]').onclick=()=>{start.value=root.dataset.start;end.value=root.dataset.end;update();};
 form.onsubmit=e=>{
  e.preventDefault();update();if(submit.disabled)return;
  generate(root.dataset.scenario,{start:start.value,end:end.value});
 };
 update();
}
function applyReportRange(root,range) {
 root.dataset.start=range.start;root.dataset.end=range.end;
 const header=root.querySelector('.report-header .muted');
 header.textContent='美国TK-艾斯特尼-美区跨境1店:US · 2 个 PID · 报告区间 '+range.start+' — '+range.end;
 if(range.start!=='2026-09-01'||range.end!=='2026-09-23'){
  root.querySelector('.report-nav').hidden=true;root.querySelector('.title-line .chip.amber').textContent='日期切换预览';
  const container=root.querySelector('.report-body');container.replaceChildren();
  const section=document.createElement('section');section.className='panel date-empty';
  const label=document.createElement('span');label.className='chip purple';label.textContent='日期切换预览';
  const title=document.createElement('h2');title.textContent='分析区间已切换';
  const period=document.createElement('p');period.className='date-period';period.textContent=range.start+' — '+range.end;
  const text=document.createElement('p');text.className='muted';text.textContent='当前仍分析 AL-W0199、原店铺及 2 个 PID。正式接入后，将按新区间重新取数、比较历史并生成结论。';
  const note=document.createElement('div');note.className='note';note.textContent='本地预览未接真实数据与 DeepSeek，因此此区间不展示旧报告的数字。下载保留当前区间和这条说明。';
  const restore=document.createElement('button');restore.className='primary restore-example';restore.textContent='返回完整示例（09.01—09.23）';
  restore.onclick=()=>generate(root.dataset.scenario,{start:'2026-09-01',end:'2026-09-23'});
  section.append(label,title,period,text,note,restore);container.append(section);
  root.querySelector('.report-footer span').textContent='报告日期：'+range.start+' — '+range.end+' · 当前仅为日期切换预览';
 }
}

function bindReport(root) {
 const menu=root.querySelector('#download-menu'),toggle=root.querySelector('#download-toggle');
 toggle.onclick=()=>{menu.hidden=!menu.hidden;toggle.setAttribute('aria-expanded',String(!menu.hidden));};
 root.querySelectorAll('.close-report').forEach(b=>b.onclick=()=>document.getElementById('report-dialog')?.close());
 root.querySelectorAll('[data-jump]').forEach(b=>b.onclick=()=>{
  const target=root.querySelector('#'+b.dataset.jump);
  if(target.tagName==='DETAILS')target.open=true;
  target.scrollIntoView({behavior:'smooth',block:'start'});
 });
 root.querySelectorAll('.report-nav a').forEach(a=>a.onclick=e=>{
  e.preventDefault();root.querySelector(a.getAttribute('href')).scrollIntoView({behavior:'smooth',block:'start'});
 });
 root.querySelector('#download-html').onclick=()=>{
  menu.hidden=true;toggle.setAttribute('aria-expanded','false');downloadReport(root);
 };
 root.querySelector('#print-report').onclick=()=>{
  menu.hidden=true;toggle.setAttribute('aria-expanded','false');window.print();
 };
 let priorOpen=[];
 window.addEventListener('beforeprint',()=>{
  priorOpen=[...root.querySelectorAll('details')].map(el=>[el,el.open]);
  priorOpen.forEach(([el])=>el.open=true);
 });
 window.addEventListener('afterprint',()=>priorOpen.forEach(([el,open])=>el.open=open));
}
function downloadReport(root) {
 const clone=root.cloneNode(true);clone.removeAttribute('hidden');
 clone.querySelectorAll('.close-report,.report-range,.restore-example').forEach(el=>el.remove());
 clone.querySelector('#download-menu').hidden=true;
 const runtime="'use strict';let toastTimer;"+notify.toString()+bindReport.toString()+downloadReport.toString()+";bindReport(document.getElementById('report-content'));";
 const html='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><link rel="icon" href="data:,"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AL-W0199 分析报告 · 示例</title><style>'+document.querySelector('style').textContent+'</style></head><body class="standalone">'+clone.outerHTML+'<div id="toast" class="toast" role="status" hidden></div><script>'+runtime+'</scr'+'ipt></body></html>';
 const url=URL.createObjectURL(new Blob([html],{type:'text/html;charset=utf-8'}));
 const link=document.createElement('a');link.href=url;link.download='AL-W0199_'+root.dataset.start+'_'+root.dataset.end+'_AI分析报告_示例_'+(root.dataset.scenario==='missing'?'采购缺失':'标准')+'.html';
 document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
 notify('已发起 HTML 下载，请查看浏览器下载列表');
}
const dialog=document.getElementById('report-dialog');
const report=document.getElementById('report-content');
function generate(scenario,range={start:'2026-09-01',end:'2026-09-23'}) {
 clearTimeout(loadTimer);document.getElementById('loading-view').hidden=false;
 document.getElementById('error-view').hidden=true;report.hidden=true;
 if(!dialog.open)dialog.showModal();
 loadTimer=setTimeout(()=>{
  document.getElementById('loading-view').hidden=true;
  if(scenario==='error'){document.getElementById('error-view').hidden=false;document.getElementById('retry').focus();return;}
  report.innerHTML=document.getElementById('report-template').innerHTML;report.dataset.scenario=scenario;
  if(scenario==='missing'){
   report.querySelector('[data-stock-head]').textContent='热卖码断货，补货衔接待核实';
   report.querySelector('[data-stock-summary]').textContent='采购来源暂不可用。当前库存仍可查看，未交数量和接续时间保持未知。';
   report.querySelector('[data-stock-warning]').textContent='采购数据暂不可用：本报告保留销量、现有库存与素材分析，无法判断补货批次、未交量和可售衔接。请由供应链核实。';
   report.querySelectorAll('[data-procurement]').forEach(el=>el.textContent='未知 · 采购数据缺失');
   report.querySelectorAll('[data-arrival]').forEach(el=>{el.innerHTML='<span class="chip amber">补货衔接待核实</span>';});
   report.querySelector('[data-erp-source]').textContent='暂不可用 · 影响补货判断';
  }
  applyReportRange(report,range);report.hidden=false;bindReport(report);bindRangeEditor(report);report.querySelector('.report-scroll').scrollTop=0;
  report.querySelector('#download-toggle').focus();
 },650);
}
document.getElementById('open-report').onclick=()=>generate(document.getElementById('scenario').value);
document.getElementById('retry').onclick=()=>generate('normal');
document.getElementById('cancel-load').onclick=()=>dialog.close();
document.querySelector('#error-view .close-report').onclick=()=>dialog.close();
dialog.addEventListener('close',()=>{clearTimeout(loadTimer);document.getElementById('open-report').focus();});


