from pathlib import Path
import hashlib, io, json, time, urllib.request, urllib.parse
from PIL import Image, ImageOps
from urllib.error import HTTPError
HERE=Path(__file__).resolve().parent
SPECS=json.loads((HERE/'art-sources.json').read_text(encoding='utf-8'))
def request_bytes(url,limit):
    for attempt in range(6):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'LukomoryeLibrary/1.15 (https://github.com/rayzer-dk/app; historic illustration importer)'})
            with urllib.request.urlopen(req,timeout=45) as res:return res.read(limit)
        except Exception as error:
            if attempt==5:raise
            retry=error.headers.get('Retry-After','') if isinstance(error,HTTPError) else ''
            delay=max(5*(attempt+1),int(retry) if retry.isdigit() else 0)
            print('Artwork fetch retry',attempt+1,'after',delay,'seconds',flush=True)
            time.sleep(delay)
def prepare_art(out):
    folder=out/'art';folder.mkdir(exist_ok=True)
    manifest=[]
    for item in SPECS:
        name=item['file'].replace(' ','_')
        if not item.get('sha1'):
            query=urllib.parse.urlencode({'action':'query','titles':'File:'+name,'prop':'imageinfo','iiprop':'url|sha1|extmetadata','format':'json','formatversion':2})
            request=urllib.request.Request('https://commons.wikimedia.org/w/api.php?'+query,headers={'User-Agent':'LukomoryeLibrary/1.15 (https://github.com/rayzer-dk/app; historic illustration importer)'})
            data=json.loads(request_bytes(request.full_url,2*1024*1024))
            info=data['query']['pages'][0]['imageinfo'][0]
            license=info['extmetadata'].get('LicenseShortName',{}).get('value','').lower()
            assert 'public domain' in license or license.startswith('pd'),'Not public domain: '+name
            sha=info['sha1'];item['sha1']=sha if len(sha)==40 else format(int(sha,36),'040x')
        md5=hashlib.md5(name.encode()).hexdigest()
        url='https://upload.wikimedia.org/wikipedia/commons/'+md5[0]+'/'+md5[:2]+'/'+urllib.parse.quote(name)
        raw=request_bytes(url,5*1024*1024)
        assert hashlib.sha1(raw).hexdigest()==item['sha1'],'Source image changed: '+name
        with Image.open(io.BytesIO(raw)) as opened:
            image=ImageOps.exif_transpose(opened).convert('RGB')
            image.thumbnail((720,720),Image.Resampling.LANCZOS)
            path=folder/(item['key']+'.webp')
            image.save(path,'WEBP',quality=79,method=6)
        manifest.append({**item,'license':'Public domain','path':'art/'+path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        print('Artwork:',item['work'],path.stat().st_size,'bytes',flush=True)
    (folder/'credits.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
