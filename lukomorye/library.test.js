import {test,expect} from 'vitest';
import {readFileSync as read,readdirSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
const server='dist/server',local='dist/offline';
const json=p=>JSON.parse(read(p,'utf8'));
test('412 complete books, correct Russian catalogue, retired ids and both distributions',()=>{
 const catalog=json(join(server,'catalog.json'));
 expect(catalog).toHaveLength(412);expect(new Set(catalog.map(b=>b.id)).size).toBe(412);
 expect(catalog.every(b=>b.language==='ru'&&b.category!=='Басни')).toBe(true);
 const review=json(join(server,'CATALOG_REVIEW.json'));expect(Object.keys(review.removed)).toHaveLength(163);
 expect(readdirSync(join(server,'books'))).toHaveLength(412);expect(readdirSync(join(local,'books'))).toHaveLength(412);
 for(const book of catalog){
  const doc=json(join(server,'books',book.id+'.json'));expect(doc.id).toBe(book.id);expect(doc.blocks.length).toBeGreaterThan(0);
  let actual;vm.runInNewContext(read(join(local,'books',book.id+'.js'),'utf8'),{window:{LUKO_ACCEPT_BOOK:(id,d)=>{expect(id).toBe(book.id);actual=JSON.stringify(d);}}});
  expect(actual).toBe(JSON.stringify(doc));
 }
});
test('all precached files are present and their final bytes match SHA-256',()=>{
 const hashes=json('dist/integrity.json');
 expect(Object.keys(hashes).filter(n=>n.startsWith('books/'))).toHaveLength(412);
 for(const [name,digest] of Object.entries(hashes))expect('sha256-'+createHash('sha256').update(read(join(server,name))).digest('base64')).toBe(digest);
 expect(read(join(server,'offline-shell.txt'),'utf8')).toBe(read(join(server,'index.html'),'utf8'));
 expect(existsSync(join(server,'sw.js'))).toBe(true);
 expect(json(join(server,'version.json')).version).toBe('1.11.0');
 expect(read(join(local,'index.html'),'utf8')).not.toContain('type="module"');
});

test('curated collections, new books and verified editions',()=>{
 const catalog=json(join(server,'catalog.json')),report=json(join(server,'CONTENT_REVIEW.json'));
 expect(report.total).toBe(412);
 expect(report.new).toHaveLength(8);
 expect(report.annotations).toBeGreaterThan(65);
 expect(report.previews).toBeGreaterThan(100);
 const newBooks=catalog.filter(b=>b.collections.includes('Новинки'));
 expect(newBooks).toHaveLength(8);
 for(const name of ['Лучшее','О животных','Волшебные сказки','Перед сном','Смешное','Путешествия','Познавательное']){
  expect(catalog.some(b=>b.collections.includes(name))).toBe(true);
 }
 for(const entry of report.new){
  expect(createHash('sha256').update(read(join(server,'books',entry.id+'.json'))).digest('hex')).toBe(entry.sha256);
  expect(json(join(server,'books',entry.id+'.json')).words).toBe(entry.words);
 }
 expect(catalog.every(b=>!/доступен для загрузки из Викитеки|Полный текст загружается из старого издания/.test(b.description))).toBe(true);
});
