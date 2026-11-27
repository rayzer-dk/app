"""Curated, fail-closed import of individual classical works, not automated bulk scraping."""
from pathlib import Path
import json,hashlib,re,math,time,urllib.parse,urllib.request
from bs4 import BeautifulSoup
from content_upgrade import fetch,words,clean,compact,extract
HERE=Path(__file__).resolve().parent
AS_OF='2026-11-27T00:00:00Z'
SPECS=json.loads((HERE/'fairy-expansion.json').read_text(encoding='utf-8'))
ANNOTATIONS=json.loads((HERE/'fairy-annotations.json').read_text(encoding='utf-8'))
AUTHOR={
 'a':('Ганс Христиан Андерсен, перевод А. В. Ганзен','Датские','Андерсен; Ганзен','Перевод Анны Ганзен (1869–1942), собрание сказок и рассказов.'),
 'h':('Вильгельм Гауф, перевод Н. А. Полевого','Немецкие','Гауф','Перевод Николая Полевого (1796–1846).'),
 'w':('Оскар Уайльд, перевод И. П. Сахарова','Английские','Уайльд; Сахаров','Замечательные рассказы и сказки, 1908, перевод И. П. Сахарова.'),
 'c':('Лидия Алексеевна Чарская','Русские','Чарская','Сказки голубой феи, 1912.')
}
def api(params):
    url='https://ru.wikisource.org/w/api.php?'+urllib.parse.urlencode({'format':'json','formatversion':2,**params})
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'LukomoryeLibrary/1.15 (https://github.com/rayzer-dk/app; curated public-domain reader)'})
            with urllib.request.urlopen(req,timeout=25) as f:return json.loads(f.read(10*1024*1024))
        except Exception:
            if attempt==2:raise
            time.sleep(2)
def key(s):
    return re.sub(r'[\W_]+','',s.casefold().replace('ё','е'))
def choose(spec):
    author,country,suffix,edition=AUTHOR[spec['k']]
    if spec.get('verifiedEdition'):
        ed=spec['verifiedEdition'];blocks,count=extract(fetch({'revision':ed['revision'],'title':spec['title']}),{**spec,**ed});return ed['page'],ed['revision'],blocks,count
    locked=spec['locked']
    rev=locked['revision']
    html=fetch({'revision':rev,'title':spec['title']})
    # The revision and accepted text length are fixed by the successful build.
    page={'title':spec['title']+' ('+suffix+')'}
    for _ in (0,):
        soup=BeautifulSoup(html,'html.parser')
        raw=clean(soup.get_text(' ',strip=True))
        if 'общественное достояние' not in raw.casefold() and 'общественном достоянии' not in raw.casefold():continue
        if spec['k']=='a' and 'ганзен' not in raw.casefold():continue
        if spec['k']=='h' and 'полевой' not in raw.casefold() and 'полевого' not in raw.casefold():continue
        if spec['k']=='w' and 'сахаров' not in raw.casefold():continue
        blocks=[]
        root=soup.select_one('.mw-parser-output') or soup
        for node in root.select('script,style,sup,figure,img,form,nav,table,#headertemplate,.ws-header,.header-container,.ws-noexport,.mw-editsection,.metadata,.catlinks,.reference,.references,.reflist,.toc,.navbox,.infobox,.printfooter,.sistersitebox,.mw-empty-elt,.portal,.sisitemark,.noprint,.ws-pagenum,.pagenum'):
            node.decompose()
        for node in root.select('h2,h3,h4,p,blockquote,pre'):
            if any(p.name in ('blockquote','pre','p') for p in node.parents):continue
            txt=clean(node.get_text(' ',strip=True))
            if not txt:continue
            if re.match(r'^(Примечания|Примечание|Литература|Источники|Библиография)(\s|$)',txt,re.I) and node.name.startswith('h'):break
            if re.match(r'^(Содержание|Оглавление|Источник:|Автор:|Перевод:|Текст доступен|Это произведение|Если произведение|Оригинал находится|Текст приведен|Текст приведён)',txt,re.I):continue
            blocks.append({'tag':'verse' if node.name=='pre' else node.name,'text':txt})
        if not blocks:continue
        # These are whole work pages, not chapters; reject source stubs, apparent redirects and unfinished excerpts.
        whole=' '.join(b['text'] for b in blocks)
        count=words(whole)
        if count<350 or count>35000 or sum(b['tag']=='p' for b in blocks)<5:continue
        if re.search(r'пока не (?:вычитан|написан)|текст (?:неполный|отсутствует)|продолжение следует|незаконченный фрагмент',whole,re.I):continue
        if not re.search(r'[.!?…»]["»”)\s]*$',blocks[-1]['text']):continue
        letters=re.findall(r'[^\W\d_]',whole)
        if not letters or sum(bool(re.match(r'[А-Яа-яЁёѢѣІіѲѳѴѵ]',c)) for c in letters)/len(letters)<.92:continue
        # Full source transcription. Preserve actual end and revision, do not generate missing text.
        assert count==locked['words'],f'Locked text length changed: {count}'
        return page['title'],rev,blocks,count
    raise ValueError('No qualifying complete Russian edition')
def expand_fairy_library(out):
    catalog=json.loads((out/'catalog.json').read_text(encoding='utf-8'))
    report=json.loads((out/'CONTENT_REVIEW.json').read_text(encoding='utf-8'))
    index=json.loads((out/'book-index.js').read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))
    retired=(out/'catalog.js').read_text(encoding='utf-8').split('window.LUKO_RETIRED_IDS = ',1)[1]
    seen={key(t) for b in catalog for t in [b['title'],*b.get('aliases',[])]}
    hashes=set()
    for b in catalog:
        d=json.loads((out/'books'/f"{b['id']}.json").read_text(encoding='utf-8'))
        hashes.add(hashlib.sha256(key(' '.join(x['text'] for x in d['blocks'])).encode()).hexdigest())
        if b['id'] in ANNOTATIONS and b.get('descriptionType')!='annotation':
            b['description']=ANNOTATIONS[b['id']];b['descriptionType']='annotation'
    added=[];rejected=[]
    for spec in SPECS:
        if not spec.get('locked'):
            rejected.append({'title':spec['title'],'reason':'Not accepted in final catalogue'})
            continue
        try:
            assert key(spec['title']) not in seen,'Existing title'
            page,revision,blocks,count=choose(spec)
            assert revision==spec['locked']['revision'] and count==spec['locked']['words'],'Locked edition mismatch'
            digest=hashlib.sha256(key(' '.join(b['text'] for b in blocks)).encode()).hexdigest()
            assert digest not in hashes,'Duplicate text'
            assert spec['id'] not in index,'Duplicate ID'
            author,country,_,edition=AUTHOR[spec['k']]
            source=f'https://ru.wikisource.org/w/index.php?oldid={revision}'
            b={k:v for k,v in spec.items() if k not in ('k','verifiedEdition','locked')}
            b.update(author=author,country=country,category='Сказки писателей',language='ru',revision=revision,page=page,minutes=max(1,math.ceil(count/120)),descriptionType='annotation',reference=edition+' Электронная редакция: Викитека (CC BY-SA, исходное произведение — общественное достояние).',collections=list(dict.fromkeys(['Новинки',*spec['collections']])),textRevision=1)
            doc={'id':b['id'],'page':page,'edition':b['reference'],'blocks':blocks,'words':count,'sourceUrl':source,'license':'Public domain original; Wikisource transcription CC BY-SA 4.0 where applicable'}
            path=out/'books'/f"{b['id']}.json";path.write_text(compact(doc),encoding='utf-8')
            index[b['id']]={'words':count};added.append(b);seen.add(key(b['title']));hashes.add(digest)
            report['new'].append({'id':b['id'],'title':b['title'],'revision':revision,'words':count,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'sourceUrl':source,'edition':doc['edition']})
            print('FAIRY ACCEPTED',b['title'],count,'words',revision,flush=True)
        except Exception as err:
            raise RuntimeError('Cannot restore final locked edition: '+spec['title']) from err
        time.sleep(.5)
    assert len(added)==24,f'Only {len(added)} locked additions'
    catalog=catalog[:20]+added+catalog[20:]
    report.update(version='1.15.0',total=len(catalog),expansion={'requested':len(SPECS),'accepted':len(added),'rejected':rejected,'cutoff':AS_OF,'review':'Whole source page and automated integrity checks; individual editorial proofreading pending.'},annotations=sum(b.get('descriptionType')=='annotation' for b in catalog),previews=sum(b.get('descriptionType')=='excerpt' for b in catalog))
    (out/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'catalog.js').write_text('window.LUKO_CATALOG = '+compact(catalog)+';\nwindow.LUKO_RETIRED_IDS = '+retired,encoding='utf-8')
    (out/'book-index.js').write_text('window.LUKO_BOOK_INDEX='+compact(index)+';\n',encoding='utf-8')
    (out/'CONTENT_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
