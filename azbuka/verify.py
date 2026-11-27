from pathlib import Path
import zipfile,hashlib,base64,json,re,subprocess,sys
p=Path(sys.argv[1]);r=json.loads((p/'release.json').read_text()); assert r['version']=='0.7.0';m=json.loads((p/'manifest.webmanifest').read_text());assert m['scope']=='./' and m['display']=='standalone' and m['start_url']=='./index.html'
for f in m['icons']:assert (p/f['src']).is_file()
sw=(p/'sw.js').read_text(); entries=json.loads(re.search(r'const manifest=(\[.*?\]);',sw)[1]);urls={e['url'] for e in entries};assert 'css/adventure.css' in urls
for e in entries:
 f=p/('index.html' if e['url']=='./' else e['url']);h=hashlib.sha256(f.read_bytes());assert e['revision']==h.hexdigest()[:24],f
 if 'integrity' in e:assert e['integrity']=='sha256-'+base64.b64encode(h.digest()).decode(),f
idx=json.loads((p/'audio/files.json').read_text());i=0
for n,sizes in enumerate(idx['packs']):
 b=(p/f'audio/pack-{n}.bin').read_bytes();offset=0
 for size in sizes:
  f=p/'audio'/idx['files'][i];assert f.read_bytes()==b[offset:offset+size],f;offset+=size;i+=1
 assert offset==len(b)
assert i==len(idx['files'])==r['audioClips']==1679
for f in list((p/'js').glob('*.js'))+[p/'sw.js']:subprocess.run(['node','--check',str(f)],check=True)
if len(sys.argv)>2:
 with zipfile.ZipFile(sys.argv[2]) as z:
  original={n for n in z.namelist() if n.startswith(('audio/','assets/')) and not n.endswith('/')};assert all(z.read(n)==(p/n).read_bytes() for n in original)
  for name in ['js/writing-course.js','js/reading-course.js','js/math-course.js','js/content.js','js/voice.js','js/study-store.js','js/offline-audio.js','js/game-extras.js','js/guided-start.js','vendor/workbox-7.4.0.js']:assert z.read(name)==(p/name).read_bytes(),name
print(f'PASS: {len(entries)} cached resources, {i} audio clips, {len(idx["packs"])} packs; JS syntax; PWA manifest; unchanged curriculum and audio when source provided.')
