from pathlib import Path
import hashlib, io, json, time, urllib.request, urllib.parse
from PIL import Image, ImageOps
HERE=Path(__file__).resolve().parent
SPECS=json.loads((HERE/'art-sources.json').read_text(encoding='utf-8'))
def prepare_art(out):
    folder=out/'art';folder.mkdir(exist_ok=True)
    manifest=[]
    for item in SPECS:
        name=item['file'].replace(' ','_')
        md5=hashlib.md5(name.encode()).hexdigest()
        url='https://upload.wikimedia.org/wikipedia/commons/'+md5[0]+'/'+md5[:2]+'/'+urllib.parse.quote(name)
        for attempt in range(3):
            try:
                req=urllib.request.Request(url,headers={'User-Agent':'LukomoryeLibrary/1.12.1 (https://github.com/rayzer-dk/app; public-domain illustrations)'})
                with urllib.request.urlopen(req,timeout=35) as response: raw=response.read(5*1024*1024)
                assert hashlib.sha1(raw).hexdigest()==item['sha1'],'Source image changed: '+name
                break
            except Exception:
                if attempt==2:raise
                time.sleep(2*(attempt+1))
        with Image.open(io.BytesIO(raw)) as opened:
            image=ImageOps.exif_transpose(opened).convert('RGB')
            image.thumbnail((720,720),Image.Resampling.LANCZOS)
            path=folder/(item['key']+'.webp')
            image.save(path,'WEBP',quality=79,method=6)
        manifest.append({**item,'license':'Public domain','path':'art/'+path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        print('Artwork:',item['work'],path.stat().st_size,'bytes',flush=True)
    (folder/'credits.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
