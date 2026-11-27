from pathlib import Path
HERE=Path(__file__).resolve().parent
def upgrade_extras(out):
    def edit(name,changes):
        p=out/name;s=p.read_text(encoding='utf-8')
        for old,new in changes:
            assert old in s,(name,old[:120])
            s=s.replace(old,new,1)
        p.write_text(s,encoding='utf-8')
    (out/'reading-extras.js').write_bytes((HERE/'reading-extras.js').read_bytes())
    with (out/'styles.css').open('a',encoding='utf-8') as f:f.write('\n'+(HERE/'reading-extras.css').read_text(encoding='utf-8'))
    edit('index.html',[
        ('<button id="hero-all" class="btn btn-glass big">Выбрать сказку</button>','<button id="hero-all" class="btn btn-glass big">Выбрать сказку</button></div><button type="button" id="daily-story" class="daily-story hidden"><span data-icon="sparkles" aria-hidden="true"></span><span class="daily-story-copy"><small>Сказка дня</small><strong id="daily-story-title"></strong></span><span data-icon="chevron-right" aria-hidden="true"></span></button><div class="hidden" aria-hidden="true">'),
        ('<div class="reader-alert hidden" id="reader-alert"></div>','<div class="reader-alert hidden" id="reader-alert"></div><figure id="reader-illustration" class="reader-illustration hidden" aria-hidden="true"></figure>'),
        ('<footer class="reader-footer">','<button id="auto-scroll-stop" type="button" class="auto-scroll-stop hidden"><span data-icon="stop" aria-hidden="true"></span> Остановить прокрутку</button><footer class="reader-footer">'),
        ('<h3>Таймер сна</h3>','<h3>Автопрокрутка</h3><div class="reader-timer-row"><select id="auto-scroll-speed" aria-label="Скорость автопрокрутки"><option value="12">Очень медленно</option><option value="18">Медленно</option><option value="28">Средне</option><option value="42">Быстро</option></select><button type="button" class="btn btn-primary" id="auto-scroll-toggle">Начать прокрутку</button></div><p>Остановится в конце текста, при ручной прокрутке, касании или переходе в другое окно.</p><label class="illustration-setting"><input type="checkbox" id="reader-show-art"> Показывать иллюстрацию перед текстом</label></section><section class="reader-tool-section"><h3>Таймер сна</h3>'),
        ('<strong>Сохранение прогресса</strong>','<strong>Сохранение прогресса</strong>'),
        ('<div class="setting"><div><strong>Анимации интерфейса</strong>','<div class="setting reading-week-setting"><div><strong>Время чтения</strong><small>Приблизительное активное время в открытой книге. Хранится локально и входит в экспорт прогресса.</small></div><div class="reading-week"><strong id="reading-week-total">0 мин за 7 дней</strong><div id="reading-week-days"></div></div></div><div class="setting"><div><strong>Анимации интерфейса</strong>')
    ])
    edit('app.js',[
        ("import {coverArt} from './cover-art.js';","import {coverArt} from './cover-art.js';\nimport {scrollSpeed,localDay,normalizeReadingDays,addSeconds,readingWeek,storyOfDay,restoredLayout} from './reading-extras.js';"),
        ("animations:true,catalogLayout:'grid'};","animations:true,catalogLayout:'grid',catalogLayoutUpdated:0,readerIllustration:false,autoScrollSpeed:18};"),
        ("let settings=Object.assign({},defaultSettings,readLocal('luko-settings',{}));","let settings=Object.assign({},defaultSettings,readLocal('luko-settings',{}));\nconst layout=restoredLayout(settings,history.state?.lukoLayout);settings.catalogLayout=layout.mode;settings.catalogLayoutUpdated=layout.updated;"),
        ("  bookmarks:normalizeBookmarks(p.bookmarks),","  bookmarks:normalizeBookmarks(p.bookmarks),\n  readingDays:normalizeReadingDays(p.readingDays),"),
        ("const state={lukoView:v,lukoDepth:(history.state?.lukoDepth||0)+1};","const state={lukoView:v,lukoDepth:(history.state?.lukoDepth||0)+1,lukoLayout:{mode:settings.catalogLayout,updated:settings.catalogLayoutUpdated||0}};"),
        ("settings.catalogLayout=settings.catalogLayout==='compact'?'compact':'grid';applyCatalogLayout();","settings.catalogLayout=settings.catalogLayout==='compact'?'compact':'grid';applyCatalogLayout();\n settings.autoScrollSpeed=scrollSpeed(settings.autoScrollSpeed);settings.readerIllustration=settings.readerIllustration===true;\n $('#auto-scroll-speed').value=String(settings.autoScrollSpeed);$('#reader-show-art').checked=settings.readerIllustration;renderReaderIllustration();"),
        ("settings.catalogLayout='grid';saveSettings();","persistCatalogLayout('grid');"),
        ("settings.catalogLayout='compact';saveSettings();","persistCatalogLayout('compact');"),
        ("function render(){","function render(){updateStoryOfDay();"),
        ("function closeReader(fromHistory=false){","function closeReader(fromHistory=false){\n stopAutoScroll();stopReadingClock();"),
        (" const b=books.find(x=>x.id===id);\n if(!b)return;"," const b=books.find(x=>x.id===id);\n if(!b)return;\n stopAutoScroll();stopReadingClock();"),
        ("current=b;currentDoc=null;updateBookNavigation();","current=b;currentDoc=null;renderReaderIllustration();updateBookNavigation();"),
        ("renderReaderRelated();refreshBookmarkButton();","renderReaderRelated();renderReaderIllustration();refreshBookmarkButton();startReadingClock();"),
        ("function readingScroll(){\n if(!currentDoc)return;\n clearTimeout(scrollTimer);\n scrollTimer=setTimeout(flushReadingPosition,140);\n}","function readingScroll(){\n if(!currentDoc)return;\n if(!scrollTimer)scrollTimer=setTimeout(flushReadingPosition,180);\n}"),
        (" if(!scrollTimer)return;\n clearTimeout(scrollTimer);"," clearTimeout(scrollTimer);"),
        (" const sc=$('#reader-scroll'),max=sc.scrollHeight-sc.clientHeight;\n const percent=max>0?Math.min(100,Math.max(0,Math.round(sc.scrollTop/max*1000)/10)):0;\n const paragraphs=$$('[data-para]',$('#reading-text'));\n const y=sc.getBoundingClientRect().top+85;\n let index=0;\n for(const paragraph of paragraphs){\n  if(paragraph.getBoundingClientRect().top>y)break;\n  index=Number(paragraph.dataset.para);\n }"," const sc=$('#reader-scroll'),text=$('#reading-text'),box=sc.getBoundingClientRect(),rect=text.getBoundingClientRect();\n const start=sc.scrollTop+rect.top-box.top-85,end=Math.max(start,sc.scrollTop+rect.bottom-box.bottom);\n const percent=end>start?Math.min(100,Math.max(0,Math.round((sc.scrollTop-start)/(end-start)*1000)/10)):0;\n const index=visibleReaderIndex();"),
        ("function toggleSpeech(){","function toggleSpeech(){stopAutoScroll();"),
        ("wireReaderTools();","wireReaderTools();wireReadingExtras();"),
        ("!$('#settings-dialog').open&&!$('#import-dialog').open","!$('#settings-dialog').open&&!$('#import-dialog').open&&!$('#reader-tools-dialog').open"),
        (" prepareOfflineApp();"," document.body.dataset.libraryReady='true';\n prepareOfflineApp();")
    ])
    p=out/'app.js';s=p.read_text(encoding='utf-8')
    anchor='function updateProgress(patch)'
    assert anchor in s
    s=s.replace(anchor,(HERE/'reading-extras-integration.js').read_text(encoding='utf-8')+'\n'+anchor,1)
    p.write_text(s,encoding='utf-8')
