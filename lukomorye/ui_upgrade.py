from pathlib import Path
import re
HERE=Path(__file__).resolve().parent
def upgrade_ui(out):
    def edit(name, changes):
        p=out/name; s=p.read_text(encoding='utf-8')
        for old,new in changes:
            if old not in s: raise RuntimeError('Missing UI anchor: '+name+' '+old[:100])
            s=s.replace(old,new,1)
        p.write_text(s,encoding='utf-8')
    (out/'cover-art.js').write_bytes((HERE/'cover-art.js').read_bytes())
    with (out/'styles.css').open('a',encoding='utf-8') as f:f.write('\n'+(HERE/'design.css').read_text(encoding='utf-8'))
    edit('index.html',[
      ('<div class="filter-pills" id="active-filters"></div>', '<div class="filter-pills" id="active-filters"></div><div class="catalog-tools"><div class="view-switch" role="group" aria-label="Вид каталога"><button type="button" id="view-grid" aria-pressed="true"><span data-icon="layers"></span> Карточки</button><button type="button" id="view-compact" aria-pressed="false"><span data-icon="list"></span> Список</button></div><button type="button" id="surprise-book" class="surprise-btn"><span data-icon="sparkles"></span> Случайная сказка</button></div>'),
      *[('<span class="stat-value" id="stat-'+name+'">','<span class="stat-symbol" data-icon="'+icon+'" aria-hidden="true"></span><span class="stat-value" id="stat-'+name+'">') for name,icon in [('all','library'),('read','check-circle'),('current','book-open'),('offline','download')]]
    ])
    edit('app.js',[
      ("import './catalog.js';","import {coverArt} from './cover-art.js';\nimport './catalog.js';"),
      ("animations:true};","animations:true,catalogLayout:'grid'};"),
      ("function setFav(id){favorites.has(id)?favorites.delete(id):favorites.add(id);safeSet('luko-favorites',JSON.stringify([...favorites]));render();if(current?.id===id){updateReaderFav();pulse($('#reader-favorite'));}else{pulse($$('[data-fav]').find(el=>el.dataset.fav===id));}}", """function setFav(id){
 const on=!favorites.has(id);on?favorites.add(id):favorites.delete(id);
 safeSet('luko-favorites',JSON.stringify([...favorites]));
 if(view==='favorites')render();
 else $$('[data-fav]').filter(el=>el.dataset.fav===id).forEach(el=>{
  el.classList.toggle('selected',on);el.setAttribute('aria-pressed',String(on));el.setAttribute('aria-label',on?'Убрать из избранного':'Добавить в избранное');pulse(el.querySelector('svg')||el);
 });
 if(current?.id===id){updateReaderFav();pulse($('#reader-favorite'));}
 toast(on?'Добавлено в избранное':'Удалено из избранного');
}"""),
      ("settings.wide=settings.wide===true;","settings.wide=settings.wide===true;\n settings.catalogLayout=settings.catalogLayout==='compact'?'compact':'grid';applyCatalogLayout();"),
      ("function card(b){","function applyCatalogLayout(){const compact=settings.catalogLayout==='compact';$('#books').classList.toggle('compact-mode',compact);$('#view-grid').setAttribute('aria-pressed',String(!compact));$('#view-compact').setAttribute('aria-pressed',String(compact));}\nfunction card(b,index=0){"),
      ('style="--card-bg:${bg};--card-fg:${fg}"','style="--card-bg:${bg};--card-fg:${fg};--entry-index:${Math.min(index,7)}"'),
      ('<div class="card-top"><div class="card-badges">','<div class="card-top">${coverArt(b)}<div class="card-badges">'),
      ("""<span class="book-emblem" aria-hidden="true">${icon(categoryIcon[b.category]||'book-open',32)}</span>""",''),
      ('data-fav="${esc(b.id)}" aria-label=', 'data-fav="${esc(b.id)}" aria-pressed="${favorites.has(b.id)}" aria-label='),
      ('data-fav="${id}" aria-label=', 'data-fav="${id}" aria-pressed="${selected}" aria-label='),
      ("const results=$('#books');","const results=$('#books');applyCatalogLayout();$('#surprise-book').disabled=!lastVisible.length;"),
      ("function wire(){","""function wire(){
 $('#view-grid').addEventListener('click',()=>{settings.catalogLayout='grid';saveSettings();});
 $('#view-compact').addEventListener('click',()=>{settings.catalogLayout='compact';saveSettings();});
 $('#surprise-book').addEventListener('click',()=>{
  const unread=lastVisible.filter(b=>!getInfo(b).done&&cachedIds.has(b.id));
  const pool=unread.length?unread:lastVisible.filter(b=>cachedIds.has(b.id));
  if(!pool.length){toast('В этой подборке нет доступных книг');return}
  openBook(pool[Math.floor(Math.random()*pool.length)].id);
 });"""),
      ("hydrateIcons();applySettings();updateInstallStatus();","hydrateIcons();$('.hero-art').innerHTML=coverArt({id:'hero-forest',title:'Лес',category:'Русские народные'});applySettings();updateInstallStatus();"),
      ("renderText(doc);$('#reader-duration')","renderText(doc);if(motionAllowed()&&$('#reading-text').animate)$('#reading-text').animate([{opacity:.45},{opacity:1}],{duration:180,easing:'ease-out'});$('#reader-duration')")
    ])
