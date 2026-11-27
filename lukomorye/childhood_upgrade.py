"""Source-attributed complete translations and explicitly labelled retellings of folk plots."""
from pathlib import Path
import json,hashlib,re,math
from content_upgrade import words,compact
HERE=Path(__file__).resolve().parent
SHELF='Сказки из нашего детства'
SPECS=json.loads((HERE/'childhood-tales.json').read_text(encoding='utf-8'))
PICKS=json.loads((HERE/'childhood-picks.json').read_text(encoding='utf-8'))
def key(s):return re.sub(r'[\W_]+','',s.casefold().replace('ё','е'))
def add_childhood(out):
    catalog=json.loads((out/'catalog.json').read_text(encoding='utf-8'))
    assert len(catalog)==457
    report=json.loads((out/'CONTENT_REVIEW.json').read_text(encoding='utf-8'))
    index=json.loads((out/'book-index.js').read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))
    retired=(out/'catalog.js').read_text(encoding='utf-8').split('window.LUKO_RETIRED_IDS = ',1)[1]
    ids={b['id'] for b in catalog}
    assert set(PICKS)<=ids
    extra_aliases={'af031':['Жихарка','Жихарь'],'b018':['Вершки и корешки','Мужик и медведь'],'b006':['Заюшкина избушка','Лубяная и ледяная избушки'],'b104':['Золотая рыбка Пушкина'],'b007':['Котик и петушок','Котик и петушок и лисичка'],'b058':['Иван-царевич и Серый волк'],'b028':['Теремок (вариант Терем мухи)']}
    for b in catalog:
        if b['id'] in PICKS:
            b['collections']=list(dict.fromkeys([*b.get('collections',[]),SHELF]))
        if b['id'] in extra_aliases:
            b['aliases']=list(dict.fromkeys([*b.get('aliases',[]),*extra_aliases[b['id']]]))
    seen={key(b['title']) for b in catalog}
    new=[]
    for spec in SPECS:
        assert spec['id'] not in ids and key(spec['title']) not in seen
        blocks=[{'tag':'p','text':p.strip()} for p in spec['body'].split('\n\n') if p.strip()]
        count=words(' '.join(p['text'] for p in blocks))
        assert count>=(80 if spec.get('translation') else 180) and len(blocks)>=(5 if spec.get('translation') else 7),(spec['title'],count,len(blocks))
        nation={'Украинские':'Украинская','Белорусские':'Белорусская','Русские':'Русская'}[spec['country']]
        edition=nation+' народная сказка. Самостоятельный русский пересказ традиционного сюжета для «Лукоморья», 2026. Не текст мультфильма и не воспроизведение конкретного печатного перевода.'
        translation=spec.get('translation')
        if translation:
            edition=translation['edition']+' Полный перевод указанной украинской записи на русский язык, 2026. '+translation['license']+'.'
        b={k:v for k,v in spec.items() if k not in ('body','translation')}
        b.update(category='Русские народные' if b['country']=='Русские' else 'Сказки мира',author=nation+' народная сказка',language='ru',minutes=max(1,math.ceil(count/120)),reference=edition,descriptionType='annotation',sourceType='retelling',collections=list(dict.fromkeys(['Новинки',SHELF,*spec['collections']])),textRevision=1,page='')
        doc={'id':b['id'],'page':'','edition':edition,'blocks':blocks,'words':count,'bundled':True,'sourceType':'retelling'}
        if translation:
            b.update(sourceType='translation',sourceUrl=translation['sourceUrl'],sourceLanguage='uk',sourceRevision=translation['revision'],textRevision=2,reference=edition)
            doc.update(sourceType='translation',sourceUrl=translation['sourceUrl'],sourceLanguage='uk',sourceRevision=translation['revision'],license=translation['license'],edition=edition)
        path=out/'books'/f"{b['id']}.json";path.write_text(compact(doc),encoding='utf-8')
        index[b['id']]={'words':count}
        ids.add(b['id']);seen.add(key(b['title']));new.append(b)
        report['new'].append({'id':b['id'],'title':b['title'],'words':count,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'edition':edition,'sourceType':b['sourceType'],**({'sourceUrl':translation['sourceUrl'],'sourceRevision':translation['revision']} if translation else {})})
        print('Childhood text',b['title'],count,'words',flush=True)
    catalog=catalog[:20]+new+catalog[20:]
    report.update(version='1.16.3',total=len(catalog),childhood={'added':len(new),'existing':len(PICKS),'total':len(PICKS)+len(new),'edition':'Source-attributed full translations where available; remaining retellings explicitly labelled.','completeTranslations':sum(b['sourceType']=='translation' for b in new),'retellingsPending':sum(b['sourceType']=='retelling' for b in new)},annotations=sum(b.get('descriptionType')=='annotation' for b in catalog))
    assert len(catalog)==len(index)==457+len(SPECS)
    (out/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'catalog.js').write_text('window.LUKO_CATALOG = '+compact(catalog)+';\nwindow.LUKO_RETIRED_IDS = '+retired,encoding='utf-8')
    (out/'book-index.js').write_text('window.LUKO_BOOK_INDEX='+compact(index)+';\n',encoding='utf-8')
    (out/'CONTENT_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    p=out/'app.js';s=p.read_text(encoding='utf-8')
    old="const categories=['Лучшее','Новинки','Русские народные'"
    assert old in s
    s=s.replace(old,"const categories=['Лучшее','Сказки из нашего детства','Новинки','Русские народные'",1)
    old="Object.assign(categoryIcon,{'Лучшее':'sparkles'"
    assert old in s
    s=s.replace(old,"Object.assign(categoryIcon,{'Сказки из нашего детства':'book-open','Лучшее':'sparkles'",1)
    old="return book.sourceType==='local'?'':Number.isSafeInteger(book.revision)"
    assert old in s
    s=s.replace(old,"return book.sourceType==='translation'&&Number.isSafeInteger(book.sourceRevision)?'https://uk.wikisource.org/w/index.php?oldid='+book.sourceRevision:['local','retelling'].includes(book.sourceType)?'':Number.isSafeInteger(book.revision)",1)
    p.write_text(s,encoding='utf-8')
