from pathlib import Path
HERE=Path(__file__).resolve().parent
def add_shelves(out):
    p=out/'index.html';s=p.read_text(encoding='utf-8')
    anchor='<nav class="category-tabs" id="category-tabs"'
    assert anchor in s
    section='<section id="illustrated-shelves" class="illustrated-shelves" aria-label="Тематические подборки"><div class="shelves-heading"><h3>Выберите мир историй</h3><a href="art/credits.json" target="_blank" rel="noopener">Об иллюстрациях</a></div><div id="shelves-items" class="shelves-items"></div></section>'
    p.write_text(s.replace(anchor,section+anchor,1),encoding='utf-8')
    p=out/'app.js';s=p.read_text(encoding='utf-8')
    anchor='fillCountryFilter();renderCategoryTabs();'
    assert anchor in s
    s=s.replace(anchor,anchor+'renderIllustratedShelves();',1)
    anchor='function renderCategoryTabs(){'
    assert anchor in s
    source="""function renderIllustratedShelves(){
 const section=$('#illustrated-shelves');
 const show=view==='all'&&!hasFilters();
 section.classList.toggle('hidden',!show);
 if(!show)return;
 const groups=[['Сказки из нашего детства','Василиса Прекрасная'],['Приключения','Дети капитана Гранта'],['Сказки мира','Алиса в Стране чудес'],['Волшебные сказки','Снежная королева']];
 const items=$('#shelves-items');
 items.innerHTML=groups.map(([category,title])=>'<button type="button" class="shelf-card" data-shelf="'+esc(category)+'"><span class="shelf-art">'+coverArt({id:'shelf-'+category,title,category})+'</span><span class="shelf-copy"><strong>'+esc(category)+'</strong><small>'+esc(workCount(books.filter(b=>inCollection(b,category)).length))+'</small></span></button>').join('');
}
"""
    s=s.replace(anchor,source+anchor,1)
    anchor="$('#category-tabs').addEventListener('click',"
    assert anchor in s
    s=s.replace(anchor,"$('#shelves-items').addEventListener('click',e=>{const n=e.target.closest('[data-shelf]');if(n)navTo(n.dataset.shelf)});"+anchor,1)
    p.write_text(s,encoding='utf-8')
