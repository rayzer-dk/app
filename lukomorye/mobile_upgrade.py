from pathlib import Path
def refine_mobile(out):
    p=out/'index.html';s=p.read_text(encoding='utf-8')
    anchor='<select id="country-filter"'
    # The source uses explicit ARIA and title attributes before/after the ID.
    import re
    match=re.search(r'<select\b[^>]*\bid="country-filter"',s)
    assert match, 'Missing country filter'
    button='<button id="mobile-filter-toggle" type="button" class="mobile-filter-toggle" aria-expanded="false" aria-label="Дополнительные фильтры"><span data-icon="sliders"></span><span id="mobile-filter-count">Фильтры</span></button>'
    s=s[:match.start()]+button+s[match.start():]
    p.write_text(s,encoding='utf-8')
    p=out/'app.js';s=p.read_text(encoding='utf-8')
    anchor="function render(){"
    assert anchor in s
    s=s.replace(anchor, """function updateMobileFilters(){
 const count=Number(countryFilter!=='all')+Number(timeFilter!=='all')+Number(ageFilter!=='all')+Number(sortBy!=='popular');
 $('#mobile-filter-count').textContent=count?'Фильтры ('+count+')':'Фильтры';
 $('#mobile-filter-toggle').classList.toggle('has-active-filters',count>0);
}
function render(){""",1)
    anchor="updateOfflineStatus();}"
    # Only the catalog render contains the active-filter markup.
    start=s.index("$('#active-filters').innerHTML=")
    end=s.index(anchor,start)
    s=s[:end]+"updateMobileFilters();"+s[end:]
    anchor="function wire(){"
    assert anchor in s
    s=s.replace(anchor,"""function wire(){
 $('#mobile-filter-toggle').addEventListener('click',()=>{
  const expanded=$('.filters').classList.toggle('filters-expanded');
  $('#mobile-filter-toggle').setAttribute('aria-expanded',String(expanded));
 });""",1)
    anchor="const errors=failedBooks(lastVisible);"
    assert anchor in s
    s=s.replace(anchor,anchor+"\\n $('#offline-quick').classList.toggle('all-saved',lastVisible.length>0&&saved===lastVisible.length&&!bulkDownloading&&!errors.length);".replace('\\n','\n'),1)
    p.write_text(s,encoding='utf-8')
