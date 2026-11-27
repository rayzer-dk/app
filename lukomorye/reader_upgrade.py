from pathlib import Path
HERE=Path(__file__).resolve().parent
def upgrade_reader(out):
    def edit(name,changes):
        p=out/name;s=p.read_text(encoding='utf-8')
        for old,new in changes:
            assert old in s,(name,old[:100])
            s=s.replace(old,new,1)
        p.write_text(s,encoding='utf-8')
    (out/'reader-tools.js').write_bytes((HERE/'reader-tools.js').read_bytes())
    with (out/'styles.css').open('a',encoding='utf-8') as f:f.write('\n'+(HERE/'reader-tools.css').read_text(encoding='utf-8'))
    edit('index.html',[
      ('<button class="btn btn-small" id="save-position">Сохранить место</button>','<button class="btn btn-small" id="save-position" type="button" aria-label="Закладки и таймер сна"><span data-icon="bookmark"></span><span id="bookmark-label">Закладки</span></button>'),
      ('<div class="reading-bottom"><a id="reader-source"','<section class="reader-related hidden" id="reader-related" aria-labelledby="reader-related-heading"><h3 id="reader-related-heading">Что почитать дальше</h3><div class="reader-related-grid" id="reader-related-items"></div></section><div class="reading-bottom"><a id="reader-source"'),
      ('</footer>\n</div>\n<dialog id="settings-dialog"', '''</footer>
<dialog id="reader-tools-dialog" class="modal reader-tools-dialog" aria-labelledby="reader-tools-title"><form method="dialog"><div class="modal-header"><div><h2 id="reader-tools-title">Закладки и таймер</h2></div><button class="icon-btn" value="cancel" aria-label="Закрыть"><span data-icon="x"></span></button></div><section class="reader-tool-section"><h3>Закладки в этой книге</h3><p>Место чтения сохраняется автоматически. Закладки позволяют вернуться к любимым абзацам.</p><button type="button" class="btn btn-primary" id="bookmark-add"><span data-icon="bookmark"></span> Добавить закладку здесь</button><div id="bookmark-list" class="bookmark-list"></div></section><section class="reader-tool-section"><h3>Таймер сна</h3><p>Остановит озвучивание через выбранное время. Отсчёт начинается при запуске чтения вслух.</p><div class="reader-timer-row"><select id="reader-sleep" aria-label="Таймер сна"><option value="0">Выключен</option><option value="5">5 минут</option><option value="10">10 минут</option><option value="15">15 минут</option><option value="30">30 минут</option><option value="45">45 минут</option><option value="60">60 минут</option></select></div><p id="reader-sleep-status" role="status"></p></section></form></dialog>
</div>
<dialog id="settings-dialog"''')
    ])
    edit('app.js',[
      ("import {coverArt} from './cover-art.js';","import {coverArt} from './cover-art.js';\nimport {MAX_BOOKMARKS,normalizeBookmarks,chapterAt,relatedBooks,sleepMinutes,sleepRemaining} from './reader-tools.js';"),
      ("  textRevision:Number.isSafeInteger(p.textRevision)?p.textRevision:0,","  textRevision:Number.isSafeInteger(p.textRevision)?p.textRevision:0,\n  bookmarks:normalizeBookmarks(p.bookmarks),"),
      ("function closeReader(fromHistory=false){","function closeReader(fromHistory=false){\n if($('#reader-tools-dialog').open)$('#reader-tools-dialog').close();"),
      (" const b=books.find(x=>x.id===id);\n if(!b)return;"," const b=books.find(x=>x.id===id);\n if(!b)return;\n if($('#reader-tools-dialog').open)$('#reader-tools-dialog').close();\n $('#reader-related').classList.add('hidden');"),
      ("const position=changed?0:previous.index;","const position=changed?0:previous.index;"),
      ("$('#reading-finish').classList.remove('hidden');\n requestAnimationFrame","$('#reading-finish').classList.remove('hidden');renderReaderRelated();refreshBookmarkButton();\n requestAnimationFrame"),
      ("anchors.push({label:block.text.length>55?block.text.slice(0,52)+'…':block.text,index});","anchors.push({label:block.text,index});"),
      ("}else anchors.unshift({label:'Начало',index:visible[0]});","}else if(anchors[0].index!==visible[0])anchors.unshift({label:'Начало',index:visible[0]});"),
      ("function flushReadingPosition(){","function flushReadingPosition(){"),
      (" if(!currentDoc||getInfo(current).done)return;\n const sc=$('#reader-scroll'),max=sc.scrollHeight-sc.clientHeight;"," if(!currentDoc||!current)return;\n syncActiveChapter(visibleReaderIndex());\n if(getInfo(current).done)return;\n const sc=$('#reader-scroll'),max=sc.scrollHeight-sc.clientHeight;"),
      ("function stopSpeech(){ttsActive=false;","function stopSpeech(){clearSleepTimer();ttsActive=false;"),
      ("ttsActive=true;ttsParagraph=Math.min(currentDoc.blocks.length-1,getInfo(current).index||0);","ttsActive=true;armSleepTimer();ttsParagraph=Math.min(currentDoc.blocks.length-1,visibleReaderIndex());"),
      ("$('#save-position').addEventListener('click',()=>{if(!currentDoc){toast('Сначала загрузите книгу');return}readingScroll();flushReadingPosition();toast('Место чтения сохранено')});","$('#save-position').addEventListener('click',openReaderTools);wireReaderTools();"),
      ("function jumpPara(idx){","function jumpPara(idx){syncActiveChapter(idx);"),
      ("function updateProgressUI(){if(!current)return;","function updateProgressUI(){if(!current)return;refreshBookmarkButton();"),
    ])
    p=out/'app.js';s=p.read_text(encoding='utf-8')
    # Top-level initialization occurs before wire() runs.
    source=(HERE/'reader-integration.js').read_text(encoding='utf-8')
    anchor='function updateProgress(patch)'
    assert anchor in s
    s=s.replace(anchor,source+'\n'+anchor,1)
    p.write_text(s,encoding='utf-8')
