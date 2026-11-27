"""Rebuild the curated Russian-language library from pinned, public-domain editions."""
from pathlib import Path
import json, math, re, time, urllib.request, urllib.parse, hashlib
from bs4 import BeautifulSoup
HERE=Path(__file__).resolve().parent
SPEC=json.loads((HERE/'new-classics.json').read_text(encoding='utf-8'))
CURATED=json.loads((HERE/'curated.json').read_text(encoding='utf-8'))
ANNOTATIONS=json.loads((HERE/'annotations.json').read_text(encoding='utf-8'))
TOTAL=404+len(SPEC)
def compact(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def words(text):return len(re.findall(r'[^\W_]+(?:[-’][^\W_]+)*',text))
def clean(text):return re.sub(r'\s+',' ',text).strip()
def normalize(text):return clean(text).casefold().replace('ё','е')
def fetch(spec):
    args=urllib.parse.urlencode({'action':'parse','oldid':spec['revision'],'prop':'text|revid','format':'json','formatversion':2,'disableeditsection':1})
    url='https://ru.wikisource.org/w/api.php?'+args
    for i in range(3):
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'LukomoryeLibrary/1.12 (https://github.com/rayzer-dk/app; public-domain offline reader)','Accept':'application/json'})
            with urllib.request.urlopen(request,timeout=35) as response:
                data=json.loads(response.read(15*1024*1024))
            parsed=data['parse']
            if int(parsed['revid'])!=spec['revision']:raise ValueError('Wrong revision')
            return parsed['text']
        except Exception as error:
            if i==2:raise RuntimeError('Failed to retrieve '+spec['title']) from error
            time.sleep(2*(i+1))
def extract(html,spec):
    soup=BeautifulSoup(html,'html.parser')
    root=soup.select_one('.mw-parser-output') or soup
    for n in root.select('script,style,sup,figure,img,form,nav,table,#headertemplate,.ws-header,.header-container,.ws-noexport,.mw-editsection,.metadata,.catlinks,.reference,.references,.reflist,.toc,.navbox,.infobox,.printfooter,.sistersitebox,.mw-empty-elt,.portal,.sisitemark,.noprint,.mw-collapsible,.ws-pagenum,.pagenum'):
        n.decompose()
    blocks=[]
    for n in root.select('h2,h3,h4,p,div,center,blockquote,pre'):
        if any(p.name in ('blockquote','pre','p') or 'poem' in (p.get('class') or []) for p in n.parents if getattr(p,'name',None)):continue
        tag='verse' if n.name=='pre' or 'poem' in (n.get('class') or []) else n.name
        text=clean(n.get_text(' ',strip=True))
        if not text:continue
        roman=spec['id']=='n1002' and len(text)<400 and re.match(r'^[IVXLCDM]+\.\s+\S',text)
        if n.name in ('div','center') and tag!='verse':
            if not roman or n.select_one('p,h2,h3,h4,div,center'):continue
        if roman:tag='h3'
        if re.match(r'^(Примечания|Примѣчанія|Примечание|Литература|Источники|Библиография)(\s|$)',text,re.I) and tag.startswith('h'):break
        if re.match(r'^(Содержание|Оглавление|Содержаніе|Оглавленіе|Эта страница|Это произведение|Источник:|Автор:|Перевод:|Текст доступен)',text,re.I):continue
        blocks.append({'tag':tag,'text':text})
    # Validate complete narrative ending, not merely a title or index.
    marker=normalize(spec['end'])
    match=[i for i,b in enumerate(blocks) if marker in normalize(b['text'])]
    if not match:raise ValueError('Missing verified final passage: '+spec['title'])
    # Remove the unrelated next-story framing in Hauff and end matter, retaining entire last paragraph.
    blocks=blocks[:match[-1]+1]
    # Retain the original chapter headings and text; only normalize whitespace.
    text=' '.join(b['text'] for b in blocks)
    count=words(text)
    if not spec['minWords']<=count<=spec['maxWords']:raise ValueError(f"{spec['title']}: unexpected word count {count}")
    letters=re.findall(r'[^\W\d_]',text)
    cyr=sum(bool(re.match(r'[А-Яа-яЁёѢѣІіѲѳѴѵ]',c)) for c in letters)
    if not letters or cyr/len(letters)<.90:raise ValueError('Non-Russian text '+spec['title'])
    if spec['id']=='n1201' and sum(b['tag'].startswith('h') and re.match(r'^Глава\s+[IVXLCDM]+',b['text'],re.I) is not None for b in blocks)<60:raise ValueError('Incomplete chapters in Captain Grant')
    if len(blocks)<10:raise ValueError('Incomplete prose '+spec['title'])
    if spec['id'] in ('n1001','n1002') and sum(b['tag'].startswith('h') for b in blocks)<30:raise ValueError('Missing chapters '+spec['title']+'; detected '+str(sum(b['tag'].startswith('h') for b in blocks)))
    return blocks,count
def upgrade_content(out):
    out=Path(out)
    catalog=json.loads((out/'catalog.json').read_text(encoding='utf-8'))
    assert len(catalog)==404
    index=json.loads((out/'book-index.js').read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))
    retired=(out/'catalog.js').read_text(encoding='utf-8').split('window.LUKO_RETIRED_IDS = ',1)[1]
    existing={b['id'] for b in catalog}
    for id in ANNOTATIONS:assert id in existing,id
    assert all(id in existing for ids in CURATED.values() for id in ids.split())
    generic=re.compile(r'^(Народная сказка из собрания|Традиционный народный текст|Полный текст из старого издания|Русскоязычный полный текст|Полный классический рассказ|Полные русскоязычные варианты)')
    counts={'annotations':0,'previews':0}
    for b in catalog:
        id=b['id']; doc=json.loads((out/'books'/f'{id}.json').read_text(encoding='utf-8'))
        b['collections']=list(dict.fromkeys([*b.get('collections',[]),*(name for name,ids in CURATED.items() if id in ids.split())]))
        if id in ANNOTATIONS:
            b['description']=ANNOTATIONS[id];b['descriptionType']='annotation';counts['annotations']+=1
        elif generic.match(b.get('description','')) or not b.get('description'):
            # A genuine opening excerpt, not an invented synopsis. Keep source edition separately.
            passage=next((clean(x['text']) for x in doc['blocks'] if x['tag']=='p' and len(clean(x['text']))>=85 and not re.match(r'^(Источник|Автор|Перевод|Примечани)',x['text'])), '')
            if not passage:
                passage=next((clean(x['text']) for x in doc['blocks'] if x['tag']=='p' and clean(x['text'])), '')
            if passage:
                short=passage if len(passage)<=145 else passage[:145].rsplit(' ',1)[0]+'…'
                b['description']='Начало: '+short;b['descriptionType']='excerpt';counts['previews']+=1
            else:b['description']='Классическое произведение. Полный текст доступен офлайн.'
    titlekey=lambda s:re.sub(r'[^\w]+','',s.casefold().replace('ё','е'))
    seen={titlekey(b['title']) for b in catalog}
    additions=[]
    report=[]
    for spec in SPEC:
        assert spec['id'] not in existing and titlekey(spec['title']) not in seen
        blocks,count=extract(fetch(spec),spec)
        doc={'id':spec['id'],'page':spec['page'],'edition':spec['edition'],'blocks':blocks,'words':count,'sourceUrl':f"https://ru.wikisource.org/w/index.php?oldid={spec['revision']}"}
        (out/'books'/f"{spec['id']}.json").write_text(compact(doc),encoding='utf-8')
        b={k:v for k,v in spec.items() if k not in ('minWords','maxWords','end','edition')}
        b.update(minutes=max(1,math.ceil(count/120)),reference=spec['edition'],descriptionType='annotation',collections=list(dict.fromkeys(['Новинки',*spec['collections']])),textRevision=1)
        if spec['id']=='n1002':b['aliases']=['Вокруг света в восемьдесят дней']
        if spec['id']=='n1004':b['aliases']=['Рассказ о калифе аисте']
        index[b['id']]={'words':count};additions.append(b);seen.add(titlekey(b['title']))
        report.append({'id':b['id'],'title':b['title'],'revision':spec['revision'],'words':count,'sha256':hashlib.sha256((out/'books'/f"{b['id']}.json").read_bytes()).hexdigest(),'sourceUrl':doc['sourceUrl'],'edition':doc['edition']})
        print('Imported',b['title'],count,'words',flush=True)
        time.sleep(.4)
    catalog=catalog[:20]+additions+catalog[20:]
    assert len(catalog)==len(index)==TOTAL
    (out/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'catalog.js').write_text('window.LUKO_CATALOG = '+compact(catalog)+';\nwindow.LUKO_RETIRED_IDS = '+retired,encoding='utf-8')
    (out/'book-index.js').write_text('window.LUKO_BOOK_INDEX='+compact(index)+';\n',encoding='utf-8')
    (out/'CONTENT_REVIEW.json').write_text(json.dumps({'version':'1.12.0','total':TOTAL,'new':report,**counts},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    p=out/'app.js';s=p.read_text(encoding='utf-8')
    old="const categories=['Русские народные','Сказки писателей','Приключения','Детские рассказы','Поучительные сказки','Сказки мира','Мои книги'];"
    new="const categories=['Лучшее','Новинки','Русские народные','Сказки писателей','Приключения','Детские рассказы','О животных','Волшебные сказки','Путешествия','Познавательное','Перед сном','Смешное','Поучительные сказки','Сказки мира','Мои книги'];\nObject.assign(categoryIcon,{'Лучшее':'sparkles','Новинки':'bookmark-check','О животных':'heart','Волшебные сказки':'sparkles','Путешествия':'compass','Познавательное':'book-text','Перед сном':'moon','Смешное':'book-open'});"
    assert old in s
    s=s.replace(old,new,1)
    old="return book.sourceType==='local'?'':trustedBookSource(doc?.sourceUrl)||sourceLink(doc?.page||book.page);"
    new="return book.sourceType==='local'?'':Number.isSafeInteger(book.revision)?'https://ru.wikisource.org/w/index.php?oldid='+book.revision:trustedBookSource(doc?.sourceUrl)||sourceLink(doc?.page||book.page);"
    assert old in s
    s=s.replace(old,new,1)
    p.write_text(s,encoding='utf-8')
    print('Content review:',counts,'total',TOTAL)
