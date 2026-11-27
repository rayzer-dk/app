import {test,expect} from 'vitest';
import {readFileSync as read,readdirSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
const server='dist/server',local='dist/offline';
const json=p=>JSON.parse(read(p,'utf8'));
test('416 complete books, correct Russian catalogue, retired ids and both distributions',()=>{
 const catalog=json(join(server,'catalog.json'));
 expect(catalog).toHaveLength(416);expect(new Set(catalog.map(b=>b.id)).size).toBe(416);
 expect(catalog.every(b=>b.language==='ru'&&b.category!=='Басни')).toBe(true);
 const review=json(join(server,'CATALOG_REVIEW.json'));expect(Object.keys(review.removed)).toHaveLength(163);
 expect(readdirSync(join(server,'books'))).toHaveLength(416);expect(readdirSync(join(local,'books'))).toHaveLength(416);
 for(const book of catalog){
  const doc=json(join(server,'books',book.id+'.json'));expect(doc.id).toBe(book.id);expect(doc.blocks.length).toBeGreaterThan(0);
  let actual;vm.runInNewContext(read(join(local,'books',book.id+'.js'),'utf8'),{window:{LUKO_ACCEPT_BOOK:(id,d)=>{expect(id).toBe(book.id);actual=JSON.stringify(d);}}});
  expect(actual).toBe(JSON.stringify(doc));
 }
});
test('all precached files are present and their final bytes match SHA-256',()=>{
 const hashes=json('dist/integrity.json');
 expect(Object.keys(hashes).filter(n=>n.startsWith('books/'))).toHaveLength(416);
 for(const [name,digest] of Object.entries(hashes))expect('sha256-'+createHash('sha256').update(read(join(server,name))).digest('base64')).toBe(digest);
 expect(read(join(server,'offline-shell.txt'),'utf8')).toBe(read(join(server,'index.html'),'utf8'));
 expect(existsSync(join(server,'sw.js'))).toBe(true);
 expect(json(join(server,'version.json')).version).toBe('1.12.1');
 expect(read(join(local,'index.html'),'utf8')).not.toContain('type="module"');
});

test('curated collections, new books and verified editions',()=>{
 const catalog=json(join(server,'catalog.json')),report=json(join(server,'CONTENT_REVIEW.json'));
 expect(report.total).toBe(416);
 expect(report.new).toHaveLength(12);
 expect(report.annotations).toBeGreaterThan(65);
 expect(report.previews).toBeGreaterThan(100);
 const newBooks=catalog.filter(b=>b.collections.includes('Новинки'));
 expect(newBooks).toHaveLength(12);
 for(const name of ['Лучшее','О животных','Волшебные сказки','Перед сном','Смешное','Путешествия','Познавательное']){
  expect(catalog.some(b=>b.collections.includes(name))).toBe(true);
 }
 for(const entry of report.new){
  expect(createHash('sha256').update(read(join(server,'books',entry.id+'.json'))).digest('hex')).toBe(entry.sha256);
  expect(json(join(server,'books',entry.id+'.json')).words).toBe(entry.words);
 }
 expect(catalog.every(b=>!/доступен для загрузки из Викитеки|Полный текст загружается из старого издания/.test(b.description))).toBe(true);
});

test('historical artwork is local, attributed and identical in both distributions',()=>{
 const credits=json(join(server,'art/credits.json'));
 expect(credits).toHaveLength(4);
 for(const art of credits){
  expect(art.license).toBe('Public domain');
  const data=read(join(server,art.path));
  expect(data.length).toBeLessThan(200000);
  expect(createHash('sha256').update(data).digest('hex')).toBe(art.sha256);
  expect(read(join(local,art.path))).toEqual(data);
  expect(json('dist/integrity.json')[art.path]).toBeTruthy();
 }
});
