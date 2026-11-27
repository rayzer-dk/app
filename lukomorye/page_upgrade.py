from pathlib import Path
HERE=Path(__file__).resolve().parent
def add_page_mode(out):
    p=out/'index.html';s=p.read_text(encoding='utf-8')
    old='<footer class="reader-footer">'
    assert old in s
    s=s.replace(old,'<div id="page-navigation" class="page-navigation hidden" role="group" aria-label="Перелистывание текста"><button id="page-prev" type="button" aria-label="Предыдущий экран"><span data-icon="arrow-left"></span><span>Назад</span></button><span id="page-number" aria-live="off">Экран 1</span><button id="page-next" type="button" aria-label="Следующий экран"><span>Далее</span><span data-icon="arrow-right"></span></button></div>'+old,1)
    old='<label class="illustration-setting">'
    assert old in s
    s=s.replace(old,'<label class="illustration-setting"><input type="checkbox" id="reader-page-mode"> Читать по экранам (перелистывание)</label>'+old,1)
    p.write_text(s,encoding='utf-8')
    p=out/'app.js';s=p.read_text(encoding='utf-8')
    for old,new in [
      ("readerIllustration:false,autoScrollSpeed:18","readerIllustration:false,autoScrollSpeed:18,pageMode:false"),
      ("$('#reader-show-art').checked=settings.readerIllustration;renderReaderIllustration();","$('#reader-show-art').checked=settings.readerIllustration;settings.pageMode=settings.pageMode===true;$('#reader-page-mode').checked=settings.pageMode;renderReaderIllustration();schedulePages();"),
      ("renderReaderRelated();renderReaderIllustration();refreshBookmarkButton();startReadingClock();","renderReaderRelated();renderReaderIllustration();refreshBookmarkButton();startReadingClock();schedulePages();"),
      ("wireReaderTools();wireReadingExtras();","wireReaderTools();wireReadingExtras();wirePages();"),
      ("function updateProgress(patch)",(HERE/'page-mode.js').read_text(encoding='utf-8')+'\nfunction updateProgress(patch)')
    ]:
      assert old in s,old[:100]
      s=s.replace(old,new,1)
    p.write_text(s,encoding='utf-8')
    with (out/'styles.css').open('a',encoding='utf-8') as f:f.write('\n'+(HERE/'page-mode.css').read_text(encoding='utf-8'))
