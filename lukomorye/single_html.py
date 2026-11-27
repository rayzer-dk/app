"""Build one HTML with all resources embedded; no neighboring files or network needed."""
import argparse, base64, json, mimetypes, re, zipfile
from pathlib import Path
def single_html(archive,output):
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        html=z.read('index.html').decode();css=z.read('styles.css').decode();app=z.read('app.js').decode()
        catalog=json.loads(z.read('catalog.json'))
        def data_uri(name):return 'data:'+mimetypes.guess_type(name)[0]+';base64,'+base64.b64encode(z.read(name)).decode('ascii')
        def safe_json(value):return json.dumps(value,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
        art={Path(n).stem:data_uri(n) for n in z.namelist() if n.startswith('art/') and n.endswith('.webp')}
        html=re.sub(r'(href|src)="(icons/[^"<>]+)"',lambda m:f'{m[1]}="{data_uri(m[2])}"',html)
        html=html.replace('href="art/credits.json"','href="'+data_uri('art/credits.json')+'" download="credits.json"')
        assert html.count('<link rel="stylesheet" href="styles.css">')==1
        html=html.replace('<link rel="stylesheet" href="styles.css">','<style>'+css+'</style>')
        assert html.count('<script src="app.js" defer></script>')==1
        html=html.replace('<script src="app.js" defer></script>','')
        pattern=r'\x60<img class="historic-art" src="art/\x60\+([\w$]+)\+\x60\.webp"'
        tick=chr(96)
        app,n=re.subn(pattern,lambda m:tick+'<img class="historic-art" src="'+tick+'+(window.LUKO_EMBEDDED_ART['+m[1]+']||'+tick+tick+')+'+tick+'"',app)
        assert n==1,'Historic artwork anchor changed'
        assert not re.search(r'</script',app,re.I)
        entries=[]
        for book in catalog:
            id=book['id'];assert re.fullmatch(r'[A-Za-z0-9-]+',id)
            raw=z.read('books/'+id+'.js').decode().strip();prefix='window.LUKO_ACCEPT_BOOK('+json.dumps(id)+','
            assert raw.startswith(prefix) and raw.endswith(');')
            doc=json.loads(raw[len(prefix):-2]);assert doc['id']==id and doc['blocks']
            entries.append('<script type="application/json" id="embedded-book-'+id+'">'+safe_json(doc)+'</script>')
        intro="""<script>window.LUKO_STANDALONE=true;
window.LUKO_EMBEDDED_ART="""+safe_json(art)+""";
const embeddedStore=Object.freeze({async load(id){const node=document.getElementById('embedded-book-'+id);if(!node)throw Error('Книга отсутствует во встроенной библиотеке');const doc=JSON.parse(node.textContent);if(doc.id!==id||!Array.isArray(doc.blocks))throw Error('Повреждён текст книги');return doc;}});
Object.defineProperty(window,'LUKO_BOOK_STORE',{configurable:false,get:()=>embeddedStore,set:()=>{}});</script>"""
        assert html.count('</body>')==1
        html=html.replace('</body>','\n'+intro+'\n'+'\n'.join(entries)+'\n<script>'+app+'</script>\n</body>')
        Path(output).write_text(html,encoding='utf-8')
        print('Standalone:',len(entries),'books',Path(output).stat().st_size,'bytes')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('output');a=p.parse_args();single_html(a.archive,a.output)
