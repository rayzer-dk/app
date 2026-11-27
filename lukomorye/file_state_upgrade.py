from pathlib import Path
HERE=Path(__file__).resolve().parent
def harden_file_state(out):
    (out/'local-state.js').write_bytes((HERE/'local-state.js').read_bytes())
    p=out/'app.js';s=p.read_text(encoding='utf-8')
    def replace(old,new):
        nonlocal s
        assert old in s,old[:120]
        s=s.replace(old,new,1)
    replace("import {coverArt} from './cover-art.js';","import {coverArt} from './cover-art.js';\nimport {STATE_KEYS,STATE_PREFIX,stateRecord,normalizeRecord,newestRecord} from './local-state.js';")
    replace("const safeSet=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){console.warn('Local save unavailable:',e)}};","")
    replace("const readLocal=(k,fallback)=>{try{const v=localStorage.getItem(k);return v?JSON.parse(v):fallback}catch{return fallback}};",(HERE/'local-state-integration.js').read_text(encoding='utf-8'))
    replace("indexedDB.open('lukomorye-library',2)","indexedDB.open('lukomorye-library',3)")
    replace("['texts','custom'].forEach(name=>","['texts','custom','preferences'].forEach(name=>")
    replace(" try{\n for(const id of downloadFailures.keys())"," await restoreFileState();\n try{\n for(const id of downloadFailures.keys())")
    replace("window.addEventListener('pagehide',()=>{collectReadingTime();stopAutoScroll();stopReadingClock(false);});","window.addEventListener('pagehide',()=>{collectReadingTime();stopAutoScroll();stopReadingClock(false);snapshotFileState();flushFileState();});")
    replace("function saveProgress(){safeSet('luko-progress',JSON.stringify(progress))}","function saveProgress(){safeSet('luko-progress',JSON.stringify(progress))}")
    replace("renderBookmarkList();toast('Закладка сохранена');","snapshotFileState();flushFileState();renderBookmarkList();toast('Закладка сохранена');")
    replace("updateProgress({bookmarks:bookBookmarks().filter(b=>b.index!==Number(del.dataset.deleteBookmark))});renderBookmarkList();","updateProgress({bookmarks:bookBookmarks().filter(b=>b.index!==Number(del.dataset.deleteBookmark))});snapshotFileState();flushFileState();renderBookmarkList();")
    replace("current=null;currentDoc=null;readerOrder=[];render();","current=null;currentDoc=null;readerOrder=[];snapshotFileState();flushFileState();render();")
    p.write_text(s,encoding='utf-8')
