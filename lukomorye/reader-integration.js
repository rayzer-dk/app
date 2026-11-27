let sleepChoice=0,sleepDeadline=0,sleepInterval=0;
function visibleReaderIndex(){
 const sc=$('#reader-scroll'),nodes=$$('[data-para]',$('#reading-text'));
 if(!nodes.length)return 0;
 const y=sc.getBoundingClientRect().top+85;
 let lo=0,hi=nodes.length-1;
 while(lo<hi){const mid=Math.ceil((lo+hi)/2);if(nodes[mid].getBoundingClientRect().top<=y)lo=mid;else hi=mid-1;}
 return Number(nodes[lo].dataset.para)||0;
}
function syncActiveChapter(index){
 const buttons=$$('[data-go]',$('#toc-items')),at=chapterAt(buttons.map(b=>Number(b.dataset.go)),index);
 buttons.forEach((b,i)=>{const active=i===at;b.classList.toggle('active',active);if(active)b.setAttribute('aria-current','true');else b.removeAttribute('aria-current');});
}
function bookBookmarks(){
 if(!current||!currentDoc)return [];
 return normalizeBookmarks(getInfo(current).bookmarks).filter(b=>b.revision===(current.textRevision||0)&&b.index<currentDoc.blocks.length&&currentDoc.blocks[b.index]?.text);
}
function refreshBookmarkButton(){
 const count=bookBookmarks().length;
 $('#bookmark-label').textContent=count?'Закладки ('+count+')':'Закладки';
 $('#save-position').dataset.hasBookmarks=String(count>0);
}
function renderBookmarkList(){
 const list=$('#bookmark-list');list.replaceChildren();
 const marks=bookBookmarks();
 if(!marks.length){const p=document.createElement('p');p.textContent='В этой книге пока нет закладок.';list.append(p);return;}
 for(const b of marks){
  const row=document.createElement('div');row.className='bookmark-entry';
  const open=document.createElement('button');open.type='button';open.dataset.jumpBookmark=String(b.index);
  const title=document.createElement('strong');title.textContent='Абзац '+(b.index+1);
  const preview=document.createElement('small');preview.textContent=b.label;
  open.append(title,preview);
  const del=document.createElement('button');del.type='button';del.dataset.deleteBookmark=String(b.index);del.setAttribute('aria-label','Удалить закладку на абзаце '+(b.index+1));del.innerHTML=icon('trash',18);
  row.append(open,del);list.append(row);
 }
}
function openReaderTools(){
 if(!currentDoc){toast('Сначала загрузите книгу');return;}
 readingScroll();flushReadingPosition();renderBookmarkList();updateSleepStatus();
 $('#reader-tools-dialog').showModal();
}
function addBookmark(){
 if(!current||!currentDoc)return;
 const index=visibleReaderIndex(),revision=current.textRevision||0,marks=bookBookmarks();
 if(marks.some(b=>b.index===index)){toast('Здесь уже есть закладка');return;}
 if(marks.length>=MAX_BOOKMARKS){toast('В одной книге можно сохранить до '+MAX_BOOKMARKS+' закладок');return;}
 const label=String(currentDoc.blocks[index]?.text||'').replace(/\s+/g,' ').trim().slice(0,145);
 if(!label)return;
 updateProgress({bookmarks:normalizeBookmarks([...marks,{index,revision,label,created:Date.now()}])});
 renderBookmarkList();toast('Закладка сохранена');
}
function updateSleepStatus(){
 const label=$('#reader-sleep-status'),listen=$('#listen-btn');
 if(sleepDeadline){
  const left=sleepRemaining(sleepDeadline,Date.now());
  const display=Math.floor(left/60)+':'+String(left%60).padStart(2,'0');
  label.textContent='До остановки озвучивания: '+display;listen.title='Озвучивание · таймер '+display;
 }else{
  label.textContent=sleepChoice?'Остановится через '+sleepChoice+' мин. после запуска озвучивания.':'Таймер выключен.';
  listen.title='Прочитать вслух';
 }
}
function clearSleepTimer(){
 if(sleepInterval)clearInterval(sleepInterval);
 sleepInterval=0;sleepDeadline=0;updateSleepStatus();
}
function checkSleepTimer(){
 if(sleepDeadline&&Date.now()>=sleepDeadline){stopSpeech();toast('Таймер сна: озвучивание остановлено');return;}
 updateSleepStatus();
}
function armSleepTimer(){
 clearSleepTimer();if(!sleepChoice)return;
 sleepDeadline=Date.now()+sleepChoice*60000;
 sleepInterval=setInterval(checkSleepTimer,1000);updateSleepStatus();
}
function renderReaderRelated(){
 const section=$('#reader-related'),list=$('#reader-related-items');list.replaceChildren();
 const picks=relatedBooks(current,books,cachedIds,b=>getInfo(b).done===true);
 for(const b of picks){
  const button=document.createElement('button');button.type='button';button.dataset.open=b.id;
  button.innerHTML='<span class="related-art">'+coverArt(b)+'</span><span class="related-copy"><strong>'+esc(b.title)+'</strong><small>'+esc(b.author||b.category)+' · '+esc(formatDuration(getMinutes(b)))+'</small></span>';
  list.append(button);
 }
 section.classList.toggle('hidden',!picks.length);
}
function wireReaderTools(){
 $('#bookmark-add').addEventListener('click',addBookmark);
 $('#bookmark-list').addEventListener('click',e=>{
  const jump=e.target.closest('[data-jump-bookmark]'),del=e.target.closest('[data-delete-bookmark]');
  if(jump){$('#reader-tools-dialog').close();jumpPara(Number(jump.dataset.jumpBookmark));return;}
  if(del){updateProgress({bookmarks:bookBookmarks().filter(b=>b.index!==Number(del.dataset.deleteBookmark))});renderBookmarkList();}
 });
 $('#reader-sleep').addEventListener('change',e=>{sleepChoice=sleepMinutes(e.target.value);if(ttsActive)armSleepTimer();else clearSleepTimer();});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden&&sleepDeadline)checkSleepTimer();});
}
