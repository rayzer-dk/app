import {chromium} from 'playwright';
import {createServer} from 'node:http';
import {readFile,stat,mkdir} from 'node:fs/promises';
import {join,resolve,extname,sep} from 'node:path';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const root=resolve('dist/server'),local=resolve('dist/offline');
const count=JSON.parse(await readFile(join(root,'catalog.json'),'utf8')).length;
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.webmanifest':'application/manifest+json','.png':'image/png','.webp':'image/webp','.txt':'text/plain; charset=utf-8'};
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
await mkdir('dist/visual',{recursive:true});
try{
 for(const width of [320,390,768,1440]){
  for(const file of [false,true]){
   const ctx=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce',isMobile:width<500,hasTouch:width<500});
   try{
    await ctx.addInitScript(()=>{if(!localStorage.getItem('luko-progress'))localStorage.setItem('luko-progress',JSON.stringify({b038:{done:true,percent:100,updated:12},b059:{percent:25,updated:13},b052:{percent:0,updated:14}}));});
    const page=await ctx.newPage(),errors=[];page.on('pageerror',e=>errors.push(String(e)));
    await page.goto(file?pathToFileURL(join(local,'index.html')).href:'http://127.0.0.1:'+server.address().port+'/library/');
    await page.waitForFunction(()=>document.body.dataset.libraryReady==='true'&&Number(document.querySelector('#stat-all')?.textContent)>=456);
    for(const [view,count] of [['done',1],['continue',1],['offline',count],['all',count]]){
     await page.locator('#search').fill('ненайденный текст');
     await page.locator('[data-stat-view="'+view+'"]').click();
     await page.waitForFunction(n=>document.querySelector('#result-count').textContent.startsWith(n+' '),count);
     assert.equal(await page.locator('#search').inputValue(),'');
    }
    assert(await page.locator('[data-icon] svg').count()>0,'Lucide icons not rendered');
    assert(await page.locator('#books .cover-art').count()>0,'Missing illustrated covers');
    const daily=await page.locator('#daily-story').getAttribute('data-daily-id');assert(daily,'Missing daily story');
    assert.equal(await page.locator('#shelves-items [data-shelf]').count(),4);
    const shelf=page.locator('#shelves-items [data-shelf="Приключения"]');
    await shelf.scrollIntoViewIfNeeded();
    await page.waitForFunction(()=>[...document.querySelectorAll('#shelves-items img')].every(i=>i.complete&&i.naturalWidth>0));
    await shelf.click();
    await page.waitForFunction(()=>document.querySelector('[data-tab="Приключения"]')?.getAttribute('aria-pressed')==='true');
    await page.locator('[data-stat-view="all"]').click();
    if(!file){await page.screenshot({path:'dist/visual/catalog-'+width+'.png',animations:'disabled'});}
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2),'Horizontal overflow '+width);
    if(width<=670){
     const toggle=page.locator('#mobile-filter-toggle');
     assert.equal(await toggle.getAttribute('aria-expanded'),'false');
     assert.equal(await page.locator('#age-filter').isVisible(),false);
     await toggle.click();assert.equal(await page.locator('#age-filter').isVisible(),true);
     await page.locator('#age-filter').selectOption('10-plus');
     assert((await toggle.innerText()).includes('(1)'));
     await page.locator('#age-filter').selectOption('all');
     await toggle.click();assert.equal(await page.locator('#age-filter').isVisible(),false);
    }
    await page.locator('#view-compact').click();
    assert.equal(await page.locator('#view-compact').getAttribute('aria-pressed'),'true');
    assert(await page.locator('#books').evaluate(el=>el.classList.contains('compact-mode')));
    assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('luko-settings')||'{}').catalogLayout),'compact');
    if(file)await page.evaluate(()=>{localStorage.removeItem('luko-settings');localStorage.removeItem('luko-mirror:luko-settings');});
    await page.reload();
    await page.waitForFunction(()=>document.body.dataset.libraryReady==='true'&&Number(document.querySelector('#stat-all')?.textContent)>=456);
    await page.waitForFunction(()=>document.querySelector('#view-compact').getAttribute('aria-pressed')==='true');
    assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('luko-settings')||'{}').catalogLayout),'compact');
    assert.equal(await page.locator('#daily-story').getAttribute('data-daily-id'),daily);
    await page.locator('#view-grid').click();
    const favorite=page.locator('#books [data-fav]').first();
    const before=await favorite.getAttribute('aria-pressed');
    await favorite.click();
    assert.notEqual(await favorite.getAttribute('aria-pressed'),before);
    await favorite.click();
    assert.equal(await favorite.getAttribute('aria-pressed'),before);
    await page.locator('[data-stat-view="continue"]').click();
    await page.locator('#books [data-open]').first().click();
    await page.waitForSelector('#reading-text [data-para]');
    assert.equal(await page.locator('#reader-title').innerText(),'Царевна-лягушка');
    await page.locator('#reader-back').click();
    await page.waitForSelector('#reader',{state:'hidden'});
    if(!file){
     await page.waitForFunction(()=>navigator.serviceWorker.controller!==null,{},{timeout:180000});
     await ctx.setOffline(true);await page.reload();
     await page.waitForFunction(()=>Number(document.querySelector('#stat-all').textContent)>=456);
    }
    await page.locator('[data-stat-view="all"]').click();
    await page.locator('#search').fill('Сивка-бурка');
    await page.locator('#books [data-open]').first().click();
    await page.waitForSelector('#reading-text [data-para]');
    assert((await page.locator('#reader-title').innerText()).length);
    await page.locator('#reader-back').click();
    await page.waitForSelector('#reader',{state:'hidden'});
    await page.locator('[data-stat-view="all"]').click();
    await page.evaluate(()=>{window.__lukoTestRandom=Math.random;Math.random=()=>0;});
    await page.locator('#surprise-book').click();
    await page.evaluate(()=>{Math.random=window.__lukoTestRandom;delete window.__lukoTestRandom;});
    await page.waitForSelector('#reading-text [data-para]');
    await page.locator('#reader-back').click();
    await page.waitForSelector('#reader',{state:'hidden'});
    await page.locator('[data-tab="Новинки"]').click();
    await page.waitForFunction(n=>document.querySelector('#result-count').textContent.startsWith(n+' '),count-404);
    await page.locator('#books [data-open="n1003"]').click();
    await page.waitForSelector('#reading-text [data-para]');
    assert.equal(await page.locator('#reader-title').innerText(),'Карлик Нос');
    assert(await page.locator('#reader-related [data-open]').count()>0);
    await page.locator('#save-position').click();
    await page.locator('#bookmark-add').click();
    assert.equal(await page.locator('[data-jump-bookmark]').count(),1);
    await page.locator('#reader-sleep').selectOption('5');
    assert((await page.locator('#reader-sleep-status').innerText()).includes('5 мин.'));
    await page.locator('#reader-tools-dialog button[value="cancel"]').click();
    await page.locator('#reading-text [data-para]').nth(12).evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
    await page.locator('#save-position').click();
    await page.locator('#bookmark-add').click();
    assert.equal(await page.locator('[data-jump-bookmark]').count(),2);
    assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('luko-progress')).n1003.bookmarks.length),2);
    await page.locator('#reader-tools-dialog button[value="cancel"]').click();
    await page.locator('#reader-back').click();
    await page.waitForSelector('#reader',{state:'hidden'});
    await page.waitForFunction(()=>!history.state?.lukoReader);
    if(file)await page.evaluate(()=>{localStorage.removeItem('luko-progress');localStorage.removeItem('luko-mirror:luko-progress');});
    await page.reload();
    await page.waitForFunction(()=>JSON.parse(localStorage.getItem('luko-progress')||'{}').n1003?.bookmarks?.length===2);
    await page.waitForFunction(()=>document.body.dataset.libraryReady==='true'&&Number(document.querySelector('#stat-all')?.textContent)>=456);
    await page.locator('[data-tab="Новинки"]').click();
    await page.locator('#books [data-open="n1003"]').click();
    await page.waitForSelector('#reading-text [data-para]');
    await page.locator('#save-position').click();
    assert.equal(await page.locator('[data-jump-bookmark]').count(),2);
    await page.locator('[data-delete-bookmark]').first().click();
    assert.equal(await page.locator('[data-jump-bookmark]').count(),1);
    await page.locator('[data-jump-bookmark]').first().click();
    await page.waitForSelector('#reader-tools-dialog',{state:'hidden'});
    await page.locator('#reader-back').click();
    await page.waitForSelector('#reader',{state:'hidden'});
    await page.locator('[data-stat-view="all"]').click();
    await page.locator('#search').fill('Дети капитана Гранта');
    await page.locator('#books [data-open="n1201"]').click();
    await page.waitForSelector('#reading-text [data-para]');
    assert.equal(await page.locator('#reader-title').innerText(),'Дети капитана Гранта');
    assert(await page.locator('#reading-text [data-para]').count()>1000);
    if(!file){await page.screenshot({path:'dist/visual/reader-'+width+'.png',animations:'disabled'});}
    await page.locator('#reader-back').click();
    await page.waitForSelector('#reader',{state:'hidden'});
    await page.waitForFunction(()=>!history.state?.lukoReader);
    await page.locator('[data-stat-view="all"]').click();
    await page.locator('#search').fill('Маленький Мук');
    await page.locator('#books [data-open="n13001"]').click();
    await page.waitForSelector('#reading-text [data-para]');
    assert.equal(await page.locator('#reader-title').innerText(),'Маленький Мук');
    assert(await page.locator('#reading-text [data-para]').count()>35);
    await page.locator('#save-position').click();
    await page.locator('#reader-show-art').check();
    assert.equal(await page.locator('#reader-illustration').isVisible(),true);
    await page.locator('#reader-show-art').uncheck();
    await page.locator('#reader-page-mode').check();
    await page.locator('#reader-tools-dialog button[value="cancel"]').click();
    await page.waitForSelector('#page-navigation',{state:'visible'});
    const pageStart=await page.locator('#reader-scroll').evaluate(el=>el.scrollTop);
    await page.locator('#page-next').click();
    await page.waitForFunction(top=>document.querySelector('#reader-scroll').scrollTop>top+30,pageStart);
    await page.locator('#page-prev').click();
    await page.waitForFunction(top=>document.querySelector('#reader-scroll').scrollTop<=top+3,pageStart);
    await page.locator('#save-position').click();
    await page.locator('#reader-page-mode').uncheck();
    await page.locator('#auto-scroll-speed').selectOption('42');
    await page.locator('#auto-scroll-toggle').click();
    await page.waitForSelector('#auto-scroll-stop',{state:'visible'});
    const startTop=await page.locator('#reader-scroll').evaluate(el=>el.scrollTop);
    await page.waitForFunction(top=>document.querySelector('#reader-scroll').scrollTop>top+2,startTop);
    await page.locator('#auto-scroll-stop').click();
    await page.waitForSelector('#auto-scroll-stop',{state:'hidden'});
    await page.locator('#reader-back').click();
    await page.waitForSelector('#reader',{state:'hidden'});
    assert.deepEqual(errors,[]);
    console.log('PASS',width,file?'file://':'PWA offline');
   }finally{await ctx.close();}
  }
 }
}finally{await browser.close();await new Promise(r=>server.close(r));}
