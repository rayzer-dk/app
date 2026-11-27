import {chromium} from 'playwright';
import {createServer} from 'node:http';
import {readFile,stat} from 'node:fs/promises';
import {join,resolve,extname,sep} from 'node:path';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const root=resolve('dist/server'),local=resolve('dist/offline');
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.webmanifest':'application/manifest+json','.png':'image/png','.txt':'text/plain; charset=utf-8'};
const server=createServer(async(req,res)=>{
 try{
  const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  if(!pathname.startsWith('/library/')){res.writeHead(404);res.end();return;}
  let file=resolve(root,pathname.slice('/library/'.length));
  if(file!==root&&!file.startsWith(root+sep)){res.writeHead(403);res.end();return;}
  if((await stat(file)).isDirectory())file=join(file,'index.html');
  res.writeHead(200,{'Content-Type':types[extname(file)]||'application/octet-stream'});res.end(await readFile(file));
 }catch{res.writeHead(404);res.end();}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch();
try{
 for(const width of [390,1440]){
  for(const file of [false,true]){
   const ctx=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce',isMobile:width<500,hasTouch:width<500});
   try{
    await ctx.addInitScript(()=>{if(!localStorage.getItem('luko-progress'))localStorage.setItem('luko-progress',JSON.stringify({b038:{done:true,percent:100,updated:12},b059:{percent:25,updated:13},b052:{percent:0,updated:14}}));});
    const page=await ctx.newPage(),errors=[];page.on('pageerror',e=>errors.push(String(e)));
    await page.goto(file?pathToFileURL(join(local,'index.html')).href:'http://127.0.0.1:'+server.address().port+'/library/');
    await page.waitForFunction(()=>document.querySelector('#stat-all')?.textContent==='404');
    for(const [view,count] of [['done',1],['continue',1],['offline',404],['all',404]]){
     await page.locator('#search').fill('ненайденный текст');
     await page.locator('[data-stat-view="'+view+'"]').click();
     await page.waitForFunction(n=>document.querySelector('#result-count').textContent.startsWith(n+' '),count);
     assert.equal(await page.locator('#search').inputValue(),'');
    }
    assert(await page.locator('[data-icon] svg').count()>0,'Lucide icons not rendered');
    await page.locator('[data-stat-view="continue"]').click();
    await page.locator('#books [data-open]').first().click();
    await page.waitForSelector('#reading-text [data-para]');
    assert.equal(await page.locator('#reader-title').innerText(),'Царевна-лягушка');
    await page.locator('#reader-back').click();
    await page.waitForSelector('#reader',{state:'hidden'});
    if(!file){
     await page.waitForFunction(()=>navigator.serviceWorker.controller!==null,{},{timeout:180000});
     await ctx.setOffline(true);await page.reload();
     await page.waitForFunction(()=>document.querySelector('#stat-all').textContent==='404');
    }
    await page.locator('[data-stat-view="all"]').click();
    await page.locator('#search').fill('Сивка-бурка');
    await page.locator('#books [data-open]').first().click();
    await page.waitForSelector('#reading-text [data-para]');
    assert((await page.locator('#reader-title').innerText()).length);
    assert.deepEqual(errors,[]);
    console.log('PASS',width,file?'file://':'PWA offline');
   }finally{await ctx.close();}
  }
 }
}finally{await browser.close();await new Promise(r=>server.close(r));}
