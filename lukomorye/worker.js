import {registerRoute} from 'workbox-routing';
const scope=self.registration.scope;
const prefix='lukomorye-shell:'+scope+':';
const releaseVersion=__LUKO_VERSION__;
const cacheName=prefix+releaseVersion+'-'+__LUKO_FINGERPRINT__;
const assets=new Map(Object.entries(__LUKO_ASSETS__).map(([path,integrity])=>[new URL(path,scope).href,integrity]));
const entry=new URL('./',scope).href;
const entryFile=new URL('index.html',scope).href;
const offlineShell=new URL('offline-shell.txt',scope).href;
self.addEventListener('install',event=>{
 event.waitUntil((async()=>{
  try{
   const cache=await caches.open(cacheName);
   const requests=Array.from(assets,([url,integrity])=>new Request(url,{cache:'reload',integrity}));
   for(let i=0;i<requests.length;i+=24)await cache.addAll(requests.slice(i,i+24));
   const shell=await cache.match(offlineShell);
   if(!shell)throw new Error('Missing verified shell');
   await cache.put(entry,new Response(await shell.text(),{headers:{'Content-Type':'text/html; charset=utf-8'}}));
   await self.skipWaiting();
  }catch(error){await caches.delete(cacheName);throw error;}
 })());
});
self.addEventListener('activate',event=>{
 event.waitUntil((async()=>{
  const keys=await caches.keys();
  await Promise.all(keys.filter(key=>key.startsWith(prefix)&&key!==cacheName).map(key=>caches.delete(key)));
  await self.clients.claim();
 })());
});
self.addEventListener('message',event=>{
 if(event.data?.type==='ACTIVATE_UPDATE')event.waitUntil(self.skipWaiting());
 if(event.data?.type==='LUKO_VERSION')event.ports[0]?.postMessage({type:'LUKO_VERSION',version:releaseVersion});
});
function cacheKey(request){
 const url=new URL(request.url);url.search='';
 if(request.mode==='navigate'&&(url.href===entry||url.href===entryFile))return entry;
 return assets.has(url.href)?url.href:null;
}
registerRoute(({request})=>Boolean(cacheKey(request)),async({request})=>{
 const cache=await caches.open(cacheName);
 return await cache.match(cacheKey(request))||Response.error();
},'GET');
