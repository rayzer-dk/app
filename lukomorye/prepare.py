from pathlib import Path
import base64, hashlib, json, math, re, shutil, sys, zipfile, zlib

HERE = Path(__file__).resolve().parent
BASE = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / 'Lukomorye_Server_v1.8.2.zip'
OUT = HERE / 'src'
VERSION = '1.16.8'
raw = BASE.read_bytes()
assert hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest() == '08c36ed6618d110a483aee44582a445fc0f0bd8b', 'Wrong source archive'
patch = (HERE/'delta-1.8.4.b64').read_bytes().strip()
assert hashlib.sha256(patch).hexdigest() == 'c26254fee414012bb1889a86d996b585a5325204e4f13db7d34e671bda15fe70', 'Wrong patch'
delta = json.loads(zlib.decompress(base64.b64decode(patch)))
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()
compact=lambda x:json.dumps(x,ensure_ascii=False,separators=(',',':'))
with zipfile.ZipFile(BASE) as z:
    for name in ['app.js','index.html','styles.css','update.js','update.html','manifest.webmanifest','README.txt']:
        lines=z.read(name).decode().splitlines(keepends=True)
        for i,j,replacement in reversed(delta[name]):
            if isinstance(replacement,list):
                old=''.join(lines[i:j])
                for a,b,s in reversed(replacement): old=old[:a]+s+old[b:]
                replacement=old
            lines[i:j]=[replacement]
        content=''.join(lines)
        expected={'app.js':'63a84438fc051de6e144d40fc8ecea742cd98435d61c2a71a0e5db45448706e6','index.html':'e649c6529a9c7c282497116ac0b807e2f53206b2f1c29dd2cbb4312dcfece929','styles.css':'60dc6b1e19cb4b2ded7e25308f35a3433c8b71e55c9d95163266721ee18b15ed'}
        if name in expected: assert hashlib.sha256(content.encode()).hexdigest()==expected[name],name
        (OUT/name).write_text(content.replace('1.8.4',VERSION),encoding='utf-8')
    cat=json.loads(z.read('catalog.json')); by_id={b['id']:b for b in cat}
    docs=json.loads(z.read('offline_docs.js').decode().split('=',1)[1].strip().rstrip(';'))
    for name in z.namelist():
        if re.fullmatch(r'icons/[a-z0-9-]+\.png',name):
            (OUT/'icons').mkdir(exist_ok=True); (OUT/name).write_bytes(z.read(name))
ids=delta['ids'].split(); assert len(ids)==len(set(ids))==404
assert set(ids)|set(delta['removed'])==set(by_id) and not set(ids)&set(delta['removed'])
(OUT/'books').mkdir(); catalog=[]; index={}
for i in ids:
    b=by_id[i]; doc=docs[i]; assert re.fullmatch(r'[a-zA-Z0-9-]+',i) and doc['id']==i
    if i in delta['foreign']:
        groups=[]
        for block in doc['blocks']:
            if not groups or (block['tag'].startswith('h') and block['text'].strip().isdigit()): groups.append([])
            groups[-1].append(block)
        foreign=set(delta['foreign'][i]); assert foreign<={g[0]['text'].strip() for g in groups}
        doc['blocks']=[x for g in groups if g[0]['text'].strip() not in foreign for x in g]
        doc['words']=sum(len(re.findall(r'[^\W_]+(?:[-’][^\W_]+)*',x['text'])) for x in doc['blocks'])
        b['minutes']=max(1,math.ceil(doc['words']/120)); b['textRevision']=max(2,b.get('textRevision',0)+1)
        b['description']='Полные русскоязычные варианты народной сказки из собрания А. Н. Афанасьева.'
    b['language']='ru'; b['collections']=[c for c in b.get('collections',[]) if c!='Басни']
    if i=='t202':
        b['title']='Пальма (Attalea princeps)'; b['aliases']=list(dict.fromkeys([*b.get('aliases',[]),'Attalea princeps']))
    words=doc['words']; assert doc['blocks']
    if doc.get('page','').startswith('Народные русские сказки (Афанасьев)/'):
        words-=sum(len(re.findall(r'\w+',x['text'])) for x in doc['blocks'] if re.fullmatch(r'h[234]',x['tag']) and re.fullmatch(r'(?:№\s*)?\d+(?:\s*[-–—]\s*\d+)?\.?',x['text'].strip()))
    index[i]={'words':max(1,words)};catalog.append(b)
    (OUT/'books'/f'{i}.json').write_text(compact(doc),encoding='utf-8')
cat_js='window.LUKO_CATALOG = '+compact(catalog)+';\nwindow.LUKO_RETIRED_IDS = '+compact(sorted(delta['removed']))+';\n'
assert hashlib.sha256(cat_js.encode()).hexdigest()=='63250e76eca1efff582cd94e80d6c9934e309295f08b123cc88c79f9a7d12c80'
(OUT/'catalog.js').write_text(cat_js,encoding='utf-8')
(OUT/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
book_js='window.LUKO_BOOK_INDEX='+compact({b['id']:index[b['id']] for b in cat if b['id'] in index})+';\n'
assert hashlib.sha256(book_js.encode()).hexdigest()=='b572b93ec7ad9ab1ea9c9f079616f73eaee18354e39bc1292ad9f639a3cf5fe4'
(OUT/'book-index.js').write_text(book_js,encoding='utf-8')
(OUT/'book-store.js').write_text(delta['store'],encoding='utf-8')
review={'base':'1.8.2','version':'1.8.3','before':567,'after':404,'removed':{i:{'title':by_id[i]['title'],'reason':delta['reasons'][n]} for i,n in delta['removed'].items()},'revised_russian_variants':delta['foreign']}
(OUT/'CATALOG_REVIEW.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'version.json').write_text(json.dumps({'version':VERSION})+'\n',encoding='utf-8')
from ui_upgrade import upgrade_ui
upgrade_ui(OUT)
from content_upgrade import upgrade_content
upgrade_content(OUT)
from fairy_expansion import expand_fairy_library
expand_fairy_library(OUT)
from childhood_upgrade import add_childhood
add_childhood(OUT)
from text_audit import audit_texts
audit_texts(OUT)
from reader_upgrade import upgrade_reader
upgrade_reader(OUT)
from art_import import prepare_art
prepare_art(OUT)
from shelf_upgrade import add_shelves
add_shelves(OUT)
from mobile_upgrade import refine_mobile
refine_mobile(OUT)
from reading_extras_upgrade import upgrade_extras
upgrade_extras(OUT)
from file_state_upgrade import harden_file_state
harden_file_state(OUT)
from page_upgrade import add_page_mode
add_page_mode(OUT)
with (OUT/'styles.css').open('a',encoding='utf-8') as visual: visual.write('\n'+(HERE/'visual-finish.css').read_text(encoding='utf-8'))
print('Prepared',VERSION,len(json.loads((OUT/'catalog.json').read_text(encoding='utf-8'))),'books from verified source archive and patch')
