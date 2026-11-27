"""Independent comparison of bundled Russian texts against their declared source.
Reports evidence, not a blanket claim of literary completeness. No books are modified.
"""
import argparse, collections, csv, hashlib, io, json, re, time, unicodedata, urllib.parse, urllib.request, urllib.error, zipfile
from pathlib import Path
from bs4 import BeautifulSoup

def norm(text):
    s=unicodedata.normalize('NFKD',text.casefold().replace('ё','е'))
    return ''.join(c for c in s if c.isalnum())
def body(doc):
    return ' '.join(x['text'] for x in doc['blocks'] if x.get('tag') not in ('h2','h3','h4') or not re.fullmatch(r'\s*(?:№\s*)?\d+[а-я]?\s*',x['text'],re.I))
def candidates(html):
    soup=BeautifulSoup(html,'html.parser')
    root=soup.select_one('.mw-parser-output') or soup
    for x in list(root.select('script,style,sup,figure,table,nav,.noprint,.metadata,.reflist,.references,.mw-editsection,.ws-noexport,.ws-header,.header-container,.navbox,.infobox,.ws-pagenum,.pagenum,.printfooter,.toc,.sistersitebox')):
        x.decompose()
    all_parts=[]; variants=[]; section=[]; numbered=False
    for node in root.select('h2,h3,h4,p,pre,blockquote,.poem'):
        if any(p.name in ('p','blockquote','pre') or 'poem' in (p.get('class') or []) for p in node.parents if p is not root):continue
        text=node.get_text(' ',strip=True)
        if not text:continue
        if node.name in ('h2','h3','h4'):
            if re.match(r'^(Примечания|Комментарии|Источники|Литература|Библиография|Ссылки)(?:\s|$)',text,re.I):break
            if re.fullmatch(r'(?:№\s*)?\d+[а-я]?',text,re.I):
                if numbered and section:variants.append(' '.join(section))
                section=[];numbered=True
                continue
        if re.match(r'^(?:Текст доступен|Это произведение|Источник —|Источник:|Эта работа находится|Данный текст находится|Общественное достояние)',text,re.I):continue
        all_parts.append(text)
        if numbered:section.append(text)
    if numbered and section:variants.append(' '.join(section))
    return [('page',' '.join(all_parts))]+[('numbered_variant',s) for s in variants]
def compare(local,source):
    needle=norm(local)
    if not needle:return {'status':'empty_local'}
    pairs=[(kind,norm(text)) for kind,text in source if norm(text)]
    if not pairs:return {'status':'source_parser_empty'}
    for kind,hay in pairs:
        if needle==hay:return {'status':'exact_normalized_'+kind,'localChars':len(needle),'sourceChars':len(hay)}
    # Do not label excerpts as complete. Compare whole page or explicitly numbered variants.
    for kind,hay in pairs:
        if len(needle)>=50 and needle in hay:
            return {'status':'contiguous_fragment_review','candidate':kind,'localChars':len(needle),'sourceChars':len(hay),'coverage':round(len(needle)/len(hay),4)}
    best=min(pairs,key=lambda k:abs(len(k[1])-len(needle)))
    kind,hay=best
    anchor=min(80,len(needle)//3)
    return {'status':'difference_requires_review','candidate':kind,'localChars':len(needle),'sourceChars':len(hay),'coverage':round(len(needle)/len(hay),4),'openingMatches':anchor>0 and hay.startswith(needle[:anchor]),'endingMatches':anchor>0 and hay.endswith(needle[-anchor:])}
def source_key(book,doc):
    if book.get('sourceType')=='translation':return None
    if book.get('sourceType')=='retelling':return None
    url=doc.get('sourceUrl') or book.get('sourceUrl') or ''
    rev=book.get('revision')
    if not isinstance(rev,int):
        parsed=urllib.parse.urlparse(url)
        if parsed.hostname=='ru.wikisource.org':
            value=urllib.parse.parse_qs(parsed.query).get('oldid',[''])[0]
            if value.isdigit():rev=int(value)
    if isinstance(rev,int) and rev>0:return ('oldid',str(rev))
    page=doc.get('page') or book.get('page')
    if page and isinstance(page,str):return ('page',page)
    return None
def fetch(key):
    params={'action':'parse','prop':'text|revid','format':'json','formatversion':2,key[0]:key[1]}
    url='https://ru.wikisource.org/w/api.php?'+urllib.parse.urlencode(params)
    for attempt in range(2):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'LukomoryeSourceCollation/1.0 (https://github.com/rayzer-dk/app; historical public-domain text verification)'})
            with urllib.request.urlopen(req,timeout=20) as r:data=json.loads(r.read(16*1024*1024))
            p=data.get('parse')
            if not p:raise ValueError(str(data.get('error','missing parse'))[:250])
            return candidates(p['text']),p.get('revid')
        except urllib.error.HTTPError as exc:
            if exc.code not in (429,503) or attempt:raise
            retry=exc.headers.get('Retry-After','')
            time.sleep(min(120,max(10,int(retry) if retry.isdigit() else 10)))
def main():
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('out');a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.archive) as z:
        catalog=json.loads(z.read('catalog.json'))
        version=json.loads(z.read('version.json'))['version']
        books=[(b,json.loads(z.read('books/'+b['id']+'.json'))) for b in catalog]
    books.sort(key=lambda pair:pair[1].get('words',0))
    rows=[];cache={};consecutive_errors=0
    for b,d in books:
        r={'id':b['id'],'title':b['title'],'words':d['words'],'sha256':hashlib.sha256(body(d).encode()).hexdigest()}
        key=source_key(b,d)
        if b.get('sourceType')=='translation':
            r.update(status='translation_needs_bilingual_collation',source=b.get('sourceUrl',''))
        elif b.get('sourceType')=='retelling':
            r.update(status='retelling_needs_replacement')
        elif not key:
            r.update(status='source_unidentified')
        else:
            r['sourceKey']=key
            if key not in cache:
                if consecutive_errors>=6:
                    cache[key]=(None,None,'paused after six consecutive fetch failures')
                else:
                    try:
                        s,rev=fetch(key);cache[key]=(s,rev,'');consecutive_errors=0
                    except Exception as e:
                        cache[key]=(None,None,str(e)[:300]);consecutive_errors+=1
                    time.sleep(1.3)
            s,rev,error=cache[key]
            if error:r.update(status='source_unavailable',error=error)
            else:r.update(sourceRevision=rev,**compare(body(d),s))
        rows.append(r)
        print(r['id'],r['status'],r['title'],flush=True)
        # Checkpoint: a stopped run still yields an explicit partial report.
        if len(rows)%10==0:save(out,rows,version,len(books))
    save(out,rows,version,len(books))
def save(out,rows,version,total):
    summary={'version':version,'catalogTotal':total,'processed':len(rows),'counts':dict(collections.Counter(r['status'] for r in rows)),'method':'Exact normalized whole page or explicitly numbered variant; all other outcomes require review. Translations need bilingual comparison. This is not independent comparison of every printed edition.'}
    (out/'source-collation.json').write_text(json.dumps({'summary':summary,'books':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fields=sorted(set().union(*(r.keys() for r in rows)))
    with (out/'source-collation.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
