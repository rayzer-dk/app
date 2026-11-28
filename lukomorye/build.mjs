import {build} from 'vite';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {readFileSync as read,writeFileSync as write,mkdirSync,rmSync,cpSync,readdirSync,existsSync} from 'node:fs';
import {join,resolve,relative} from 'node:path';
import assert from 'node:assert/strict';
const root=fileURLToPath(new URL('.',import.meta.url));
const source=join(root,'src'), dist=join(root,'dist'), server=join(dist,'server'), local=join(dist,'offline');
const version=JSON.parse(read(join(source,'version.json'),'utf8')).version;
assert.equal(version,'1.16.8');
const bookCount=JSON.parse(read(join(source,'catalog.json'),'utf8')).length;assert.equal(bookCount,480);
const svgNames='book home heart settings search chevron-right chevron play pause stop volume edit bookmark plus check trash download upload sun moon x external copy info menu library layers clock book-open book-text globe feather compass check-circle panel-left list arrow-left arrow-right arrow-up-right type maximize sparkles check-check sliders bookmark-check share refresh minimize help-circle'.split(' ');
const aliases={home:['house','home'],chevron:['chevron-left'],stop:['square'],volume:['volume-2'],edit:['pencil'],trash:['trash-2'],external:['external-link'],'check-circle':['circle-check','check-circle'],sliders:['sliders-horizontal'],refresh:['refresh-cw'],'help-circle':['circle-question-mark','circle-help','help-circle']};
const iconRoot=join(root,'node_modules/lucide-static/icons');
const icons={};
for(const name of svgNames){
 const candidates=aliases[name]||[name];
 const icon=candidates.map(n=>join(iconRoot,n+'.svg')).find(existsSync);
 assert(icon,'Missing Lucide icon: '+name);
 const svg=read(icon,'utf8').match(/<svg\b[^>]*>([\s\S]*?)<\/svg>/);
 assert(svg,'Invalid SVG: '+name);icons[name]=svg[1].trim();
}
const appPath=join(source,'app.js');
let app=read(appPath,'utf8');
const start=app.indexOf('const ICON_PATHS='),end=app.indexOf('const icon=',start);
assert(start>=0&&end>start);
app=app.slice(0,start)+'const ICON_PATHS='+JSON.stringify(icons)+';\n'+app.slice(end);
write(appPath,app);
const updatePath=join(source,'update.html');
write(updatePath,read(updatePath,'utf8').replace('<script src="update.js" defer></script>','<script type="module" src="update.js"></script>'));
rmSync(dist,{recursive:true,force:true});
mkdirSync(server,{recursive:true});mkdirSync(local,{recursive:true});
const common={configFile:false,root:source,base:'./',publicDir:false,mode:'production',define:{'process.env.NODE_ENV':JSON.stringify('production')}};
const options={target:'es2022',sourcemap:false,assetsInlineLimit:0,reportCompressedSize:false};
await build({...common,build:{...options,outDir:server,emptyOutDir:false,rollupOptions:{input:{index:join(source,'index.html'),update:join(source,'update.html')}}}});
await build({...common,build:{...options,outDir:local,emptyOutDir:false,lib:{entry:appPath,name:'LukomoryeApp',formats:['iife'],fileName:()=> 'app.js'}}});
assert(existsSync(join(local,'app.js')),'Missing classic script bundle');
for(const dest of [server,local]){
 for(const file of ['icons','art','catalog.json','CATALOG_REVIEW.json','CONTENT_REVIEW.json','TEXT_AUDIT.json','README.txt','version.json']) cpSync(join(source,file),join(dest,file),{recursive:true});
 const licenses=join(dest,'licenses');mkdirSync(licenses,{recursive:true});
 for(const name of ['lucide-static','workbox-routing','workbox-core']){
  const dir=join(root,'node_modules',name);
  if(!existsSync(dir))continue;
  for(const file of readdirSync(dir).filter(n=>/^licen[cs]e(?:\.|$)/i.test(n)))cpSync(join(dir,file),join(licenses,name+'-'+file));
 }
}
cpSync(join(source,'books'),join(server,'books'),{recursive:true});
cpSync(join(source,'manifest.webmanifest'),join(server,'manifest.webmanifest'));
let shell=read(join(server,'index.html'),'utf8').replace(/(<link\b[^>]*rel=["']manifest["'][^>]*href=)["'][^"']*["']/i,'$1"./manifest.webmanifest"');
write(join(server,'index.html'),shell);write(join(server,'offline-shell.txt'),shell);
cpSync(join(source,'styles.css'),join(local,'styles.css'));
let localHtml=read(join(source,'index.html'),'utf8').replace(/<link rel="manifest"[^>]*>\s*/,'').replace('<script type="module" src="app.js"></script>','<script src="app.js" defer></script>');
assert(!localHtml.includes('type="module"'));
write(join(local,'index.html'),localHtml);
mkdirSync(join(local,'books'),{recursive:true});
for(const name of readdirSync(join(source,'books'))){
 const doc=JSON.parse(read(join(source,'books',name),'utf8'));
 write(join(local,'books',doc.id+'.js'),'window.LUKO_ACCEPT_BOOK('+JSON.stringify(doc.id)+','+JSON.stringify(doc)+');\n');
}
const sha=b=>createHash('sha256').update(b);
function walk(dir){return readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(join(dir,e.name)):[join(dir,e.name)]);}
const files=walk(server).map(f=>relative(server,f).replaceAll('\\','/')).filter(f=>f==='offline-shell.txt'||f==='manifest.webmanifest'||/^(assets|books|icons|art)\//.test(f)).sort();
const integrity=Object.fromEntries(files.map(f=>[f,'sha256-'+sha(read(join(server,f))).digest('base64')]));
assert.equal(files.filter(f=>f.startsWith('books/')).length,bookCount);
const fingerprint=sha(JSON.stringify(integrity)).digest('hex').slice(0,16);
const worker=read(join(root,'worker.js'),'utf8').replace('__LUKO_ASSETS__',JSON.stringify(integrity)).replace('__LUKO_VERSION__',JSON.stringify(version)).replace('__LUKO_FINGERPRINT__',JSON.stringify(fingerprint));
const entry=join(source,'sw-generated.js');write(entry,worker);
await build({...common,build:{...options,outDir:server,emptyOutDir:false,lib:{entry,name:'LukomoryeWorker',formats:['iife'],fileName:()=> 'sw.js'}}});
assert(existsSync(join(server,'sw.js')));
write(join(dist,'integrity.json'),JSON.stringify(integrity,null,2)+'\n');
console.log('Built '+version+': '+files.length+' verified PWA resources, '+bookCount+' books, local file edition');
