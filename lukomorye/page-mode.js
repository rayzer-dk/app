// Screen-sized pages preserve the original DOM, paragraph IDs, selection and bookmarks.
let pageTurnFrame=0;
function pageMetrics(){
 const sc=$('#reader-scroll'),text=$('#reading-text'),r=sc.getBoundingClientRect(),t=text.getBoundingClientRect();
 const head=$('.reader-header'),sticky=head?Math.min(head.getBoundingClientRect().height,110):0;
 const usable=Math.max(100,sc.clientHeight-sticky-32);
 const start=Math.max(0,sc.scrollTop+t.top-r.top-sticky-12);
 const end=Math.max(start,sc.scrollTop+t.bottom-r.bottom+12);
 const step=Math.max(80,usable-28),count=Math.max(1,Math.ceil((end-start)/step)+1);
 return {sc,start,end,step,count,page:Math.max(1,Math.min(count,Math.floor((sc.scrollTop-start+step*.45)/step)+1))};
}
function refreshPages(){
 const bar=$('#page-navigation'),enabled=!!(currentDoc&&settings.pageMode);
 bar.classList.toggle('hidden',!enabled);
 if(!enabled)return;
 const m=pageMetrics();
 $('#page-number').textContent='Экран '+m.page+' из '+m.count;
 $('#page-prev').disabled=m.sc.scrollTop<=1;
 $('#page-next').disabled=m.sc.scrollTop>=m.sc.scrollHeight-m.sc.clientHeight-2;
}
function schedulePages(){if(!pageTurnFrame)pageTurnFrame=requestAnimationFrame(()=>{pageTurnFrame=0;refreshPages();});}
function turnPage(direction){
 if(!currentDoc||!settings.pageMode)return;
 stopAutoScroll();
 const m=pageMetrics(),top=Math.max(0,Math.min(m.sc.scrollHeight-m.sc.clientHeight,m.sc.scrollTop+direction*m.step));
 m.sc.scrollTo({top,behavior:motionAllowed()?'smooth':'auto'});
 schedulePages();
}
function wirePages(){
 $('#reader-page-mode').addEventListener('change',e=>{keepReaderAnchor(()=>{settings.pageMode=e.target.checked;saveSettings();});refreshPages();});
 $('#page-prev').addEventListener('click',()=>turnPage(-1));
 $('#page-next').addEventListener('click',()=>turnPage(1));
 $('#reader-scroll').addEventListener('scroll',schedulePages,{passive:true});
 window.addEventListener('resize',schedulePages,{passive:true});
 document.addEventListener('keydown',e=>{
  if(!settings.pageMode||!currentDoc||$('#reader').classList.contains('hidden')||document.querySelector('dialog[open]')||e.altKey||e.ctrlKey||e.metaKey||e.shiftKey||e.target.closest('input,textarea,select,button,[contenteditable]')||window.getSelection()?.toString())return;
  if(['ArrowRight','PageDown','ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();turnPage(e.key==='ArrowRight'||e.key==='PageDown'?1:-1);}
 });
}
