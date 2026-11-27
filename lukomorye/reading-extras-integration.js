// Auto-scroll, optional cover, daily story and local reading-time history.
let autoFrame=0,autoLast=0,autoRemainder=0,readingInterval=0,readingTickAt=0,readingActivityAt=0;
function persistCatalogLayout(mode){
 settings.catalogLayout=mode;settings.catalogLayoutUpdated=Math.max(Date.now(),Number(settings.catalogLayoutUpdated||0)+1);
 saveSettings();
 try{history.replaceState({...history.state,lukoLayout:{mode,updated:settings.catalogLayoutUpdated}},'');}catch{}
}
function updateStoryOfDay(){
 const b=storyOfDay(books,cachedIds,getMinutes),el=$('#daily-story');
 el.hidden=!b;el.classList.toggle('hidden',!b);el.disabled=!b;
 if(b){el.dataset.dailyId=b.id;$('#daily-story-title').textContent=b.title;el.title='Сказка дня: '+b.title;}
 else{delete el.dataset.dailyId;}
}
function renderReaderIllustration(){
 const el=$('#reader-illustration'),enabled=!!(settings.readerIllustration&&current&&currentDoc);
 el.classList.toggle('hidden',!enabled);
 if(!enabled){el.replaceChildren();delete el.dataset.bookId;return;}
 if(el.dataset.bookId===current.id)return;
 el.innerHTML=coverArt(current);
 el.dataset.bookId=current.id;
}
function stopAutoScroll(){
 if(autoFrame)cancelAnimationFrame(autoFrame);
 autoFrame=0;autoLast=0;autoRemainder=0;
 $('#auto-scroll-stop').classList.add('hidden');
 $('#auto-scroll-toggle').textContent='Начать прокрутку';
}
function autoScrollStep(now){
 if(!currentDoc||document.hidden||$('#reader').classList.contains('hidden')||$('#reader-tools-dialog').open||$('#settings-dialog').open||ttsActive){stopAutoScroll();return;}
 const sc=$('#reader-scroll'),text=$('#reading-text');
 const bottom=text.getBoundingClientRect().bottom-sc.getBoundingClientRect().bottom;
 if(bottom<=1){stopAutoScroll();return;}
 const delta=autoLast?Math.min(50,Math.max(0,now-autoLast)):0;autoLast=now;
 autoRemainder+=scrollSpeed(settings.autoScrollSpeed)*delta/1000;
 const step=Math.min(Math.floor(autoRemainder),Math.ceil(bottom));
 if(step>0){autoRemainder-=step;sc.scrollTop+=step;readingActivityAt=Date.now();}
 autoFrame=requestAnimationFrame(autoScrollStep);
}
function startAutoScroll(){
 if(!currentDoc||document.hidden)return;
 if(ttsActive)stopSpeech();
 stopAutoScroll();
 $('#auto-scroll-stop').classList.remove('hidden');
 $('#auto-scroll-toggle').textContent='Остановить прокрутку';
 readingActivityAt=Date.now();
 autoFrame=requestAnimationFrame(autoScrollStep);
}
function collectReadingTime(){
 const now=Date.now(),elapsed=Math.floor((now-readingTickAt)/1000);
 if(!readingTickAt){readingTickAt=now;return;}
 if(elapsed<=0)return;
 readingTickAt+=elapsed*1000;
 if(!current||!currentDoc||document.hidden||$('#reader').classList.contains('hidden')||$('#reader-tools-dialog').open||$('#settings-dialog').open)return;
 if(!ttsActive&&!autoFrame&&now-readingActivityAt>90000)return;
 const old=getInfo(current);
 progress[current.id]={...old,readingDays:addSeconds(old.readingDays,localDay(),elapsed)};
 saveProgress();
}
function startReadingClock(){
 stopReadingClock(false);readingTickAt=Date.now();readingActivityAt=readingTickAt;
 readingInterval=setInterval(collectReadingTime,10000);
}
function stopReadingClock(flush=true){
 if(flush)collectReadingTime();
 if(readingInterval)clearInterval(readingInterval);
 readingInterval=0;readingTickAt=0;
}
function renderReadingWeek(){
 const days=readingWeek(progress),total=days.reduce((sum,d)=>sum+d.seconds,0),max=Math.max(60,...days.map(d=>d.seconds));
 const label=total>=60?formatDuration(Math.floor(total/60)):total?'< 1 мин':'0 мин';
 $('#reading-week-total').textContent=label+' за 7 дней';
 const list=$('#reading-week-days');list.replaceChildren();
 for(const item of days){
  const row=document.createElement('div');row.className='reading-day';
  const day=document.createElement('span');day.textContent=item.day.slice(8)+'.'+item.day.slice(5,7);
  const bar=document.createElement('span');bar.className='reading-day-track';
  const fill=document.createElement('i');fill.style.width=(item.seconds/max*100)+'%';bar.append(fill);
  const time=document.createElement('span');time.textContent=item.seconds>=60?formatDuration(Math.floor(item.seconds/60)):item.seconds?'< 1 мин':'—';
  row.append(day,bar,time);list.append(row);
 }
}
function wireReadingExtras(){
 $('#daily-story').addEventListener('click',e=>{const id=e.currentTarget.dataset.dailyId;if(id)openBook(id);});
 $('#reader-show-art').addEventListener('change',e=>{keepReaderAnchor(()=>{settings.readerIllustration=e.target.checked;saveSettings();});});
 $('#auto-scroll-speed').addEventListener('change',e=>{settings.autoScrollSpeed=scrollSpeed(e.target.value);saveSettings();});
 $('#auto-scroll-toggle').addEventListener('click',()=>{
  if(autoFrame){stopAutoScroll();return;}
  $('#reader-tools-dialog').close();startAutoScroll();
 });
 $('#auto-scroll-stop').addEventListener('click',stopAutoScroll);
 const sc=$('#reader-scroll');
 for(const event of ['wheel','touchstart','pointerdown','keydown'])sc.addEventListener(event,()=>{readingActivityAt=Date.now();if(autoFrame)stopAutoScroll();},{passive:true});
 sc.addEventListener('scroll',()=>{readingActivityAt=Date.now();},{passive:true});
 $('#reader').addEventListener('pointerdown',e=>{if(e.target.closest('#reader-scroll,#reader-quick-panel,#reader-aside,#reader-tools-dialog'))readingActivityAt=Date.now();},{passive:true});
 document.addEventListener('visibilitychange',()=>{if(document.hidden){stopAutoScroll();stopReadingClock(false);}else{updateStoryOfDay();if(currentDoc)startReadingClock();}});
 window.addEventListener('pagehide',()=>{collectReadingTime();stopAutoScroll();stopReadingClock(false);});
 $('#settings-dialog').addEventListener('close',()=>{if(currentDoc)readingActivityAt=Date.now();});
 const settingsDialog=$('#settings-dialog');
 if(typeof MutationObserver!=='undefined')new MutationObserver(()=>{if(settingsDialog.open)renderReadingWeek();}).observe(settingsDialog,{attributes:true,attributeFilter:['open']});
}
