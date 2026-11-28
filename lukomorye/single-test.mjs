import {chromium} from 'playwright';
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const version=JSON.parse(await readFile('package.json','utf8')).version;
const html=await readFile(`dist/Lukomorye_v${version}.html`,'utf8');
const browser=await chromium.launch();
try{
 for(const width of [320,390,1440]){
  const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
  const page=await context.newPage(),errors=[],network=[];
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('request',r=>{if(/^(https?|file):/.test(r.url()))network.push(r.url())});
  await page.route('**/*',route=>route.abort());
  await page.setContent(html,{waitUntil:'domcontentloaded',timeout:60000});
  await context.setOffline(true);
  await page.waitForFunction(()=>document.body.dataset.libraryReady==='true');
  assert.equal(await page.locator('#stat-all').innerText(),'491');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
  assert(await page.locator('img').first().evaluate(i=>i.complete&&i.naturalWidth>0));
  await page.locator('#search').fill('Коза-дереза');
  await page.locator('#books [data-open="n16006"]').click();
  await page.waitForSelector('#reading-text [data-para]');
  assert((await page.locator('#reading-text').innerText()).includes('Кукареку'));
  await page.locator('#reader-back').click();
  await page.waitForSelector('#reader',{state:'hidden'});
  assert.deepEqual(errors,[]);assert.deepEqual(network,[]);
  await context.close();console.log('PASS embedded HTML',width);
 }
}finally{await browser.close()}
