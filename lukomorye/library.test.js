import {test,expect} from 'vitest';
import {readFileSync as read,readdirSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
const server='dist/server',local='dist/offline';
const json=p=>JSON.parse(read(p,'utf8'));
const bookCount=json(join(server,'catalog.json')).length;
test('library contains 478 works',()=>expect(bookCount).toBe(478));
test('Complete books, correct Russian catalogue, retired ids and both distributions',()=>{
 const catalog=json(join(server,'catalog.json'));
 expect(catalog).toHaveLength(bookCount);expect(new Set(catalog.map(b=>b.id)).size).toBe(bookCount);
 expect(catalog.every(b=>b.language==='ru'&&b.category!=='Басни')).toBe(true);
 const review=json(join(server,'CATALOG_REVIEW.json'));expect(Object.keys(review.removed)).toHaveLength(163);
 expect(readdirSync(join(server,'books'))).toHaveLength(bookCount);expect(readdirSync(join(local,'books'))).toHaveLength(bookCount);
 for(const book of catalog){
  const doc=json(join(server,'books',book.id+'.json'));expect(doc.id).toBe(book.id);expect(doc.blocks.length).toBeGreaterThan(0);
  let actual;vm.runInNewContext(read(join(local,'books',book.id+'.js'),'utf8'),{window:{LUKO_ACCEPT_BOOK:(id,d)=>{expect(id).toBe(book.id);actual=JSON.stringify(d);}}});
  expect(actual).toBe(JSON.stringify(doc));
 }
});
test('all precached files are present and their final bytes match SHA-256',()=>{
 const hashes=json('dist/integrity.json');
 expect(Object.keys(hashes).filter(n=>n.startsWith('books/'))).toHaveLength(bookCount);
 for(const [name,digest] of Object.entries(hashes))expect('sha256-'+createHash('sha256').update(read(join(server,name))).digest('base64')).toBe(digest);
 expect(read(join(server,'offline-shell.txt'),'utf8')).toBe(read(join(server,'index.html'),'utf8'));
 expect(existsSync(join(server,'sw.js'))).toBe(true);
 expect(json(join(server,'version.json')).version).toBe('1.16.6');
 expect(read(join(local,'index.html'),'utf8')).not.toContain('type="module"');
});

test('curated collections, new books and verified editions',()=>{
 const catalog=json(join(server,'catalog.json')),report=json(join(server,'CONTENT_REVIEW.json'));
 expect(report.total).toBe(bookCount);
 expect(report.new).toHaveLength(bookCount-404);
 expect(report.annotations).toBeGreaterThan(65);
 expect(report.previews).toBeGreaterThan(100);
 const newBooks=catalog.filter(b=>b.collections.includes('Новинки'));
 expect(newBooks).toHaveLength(bookCount-404);
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
 expect(credits).toHaveLength(11);
 for(const art of credits){
  expect(art.license).toBe('Public domain');
  const data=read(join(server,art.path));
  expect(data.length).toBeLessThan(200000);
  expect(createHash('sha256').update(data).digest('hex')).toBe(art.sha256);
  expect(read(join(local,art.path))).toEqual(data);
  expect(json('dist/integrity.json')[art.path]).toBeTruthy();
 }
});

test('seventeen additional fairy tales, complete bilingual-free Russian texts and annotations',()=>{
 const catalog=json(join(server,'catalog.json'));const added=catalog.filter(b=>b.id.startsWith('n130'));
 expect(added).toHaveLength(17);
 for(const b of added){expect(b.category).toBe('Сказки писателей');expect(b.descriptionType).toBe('annotation');expect(b.description.length).toBeGreaterThan(45);expect(b.collections.includes('Новинки')).toBe(true);const d=json(join(server,'books',b.id+'.json'));expect(d.words).toBeGreaterThan(350);expect(d.blocks.length).toBeGreaterThan(9);expect(d.sourceUrl).toBe('https://ru.wikisource.org/w/index.php?oldid='+b.revision);}
});

test('curated expansion: no missing files, transparent exclusions, new annotations',()=>{const r=json(join(server,'CONTENT_REVIEW.json'));expect(r.expansion.accepted).toBe(24);expect(r.expansion.accepted+r.expansion.rejected.length).toBe(40);expect(r.total).toBe(433+r.expansion.accepted+21);expect(r.annotations).toBeGreaterThan(150);});

test('childhood shelf, Russian retellings and existing aliases',()=>{const catalog=json(join(server,'catalog.json')),report=json(join(server,'CONTENT_REVIEW.json'));const shelf=catalog.filter(b=>b.collections?.includes('Сказки из нашего детства'));expect(shelf).toHaveLength(90);expect(report.childhood.added).toBe(21);for(const b of shelf.filter(b=>b.sourceType==='retelling')){expect(b.language).toBe('ru');expect(b.reference).toContain('Самостоятельный русский пересказ');expect(json(join(server,'books',b.id+'.json')).words).toBeGreaterThanOrEqual(180);}expect(catalog.find(b=>b.id==='af031').aliases).toContain('Жихарка');});

test('source-attributed translations and transparent structural audit',()=>{const a=json(join(server,'TEXT_AUDIT.json')),c=json(join(server,'catalog.json'));expect(a.total).toBe(478);expect(a.fullTranslations).toBe(17);expect(a.retellingsPending).toBe(4);expect(a.exactDuplicates).toEqual([]);for(const b of c.filter(b=>b.sourceType==='translation')){expect(b.textRevision).toBe(2);expect(b.sourceUrl).toBe('https://uk.wikisource.org/w/index.php?oldid='+b.sourceRevision);expect(json(join(server,'books',b.id+'.json')).sourceUrl).toBe(b.sourceUrl);}});

test('four further source translations preserve distinctive original episodes and endings',()=>{const book=id=>json(join(server,'books',id+'.json'));const plain=id=>book(id).blocks.map(b=>b.text).join('\n');expect(book('n16002').sourceRevision).toBe(668411);expect(plain('n16002')).toContain('пока и растаял');expect(book('n16011').sourceRevision).toBe(488020);expect(plain('n16011')).toContain('гречневые галушки');expect(book('n16015').sourceRevision).toBe(94883);expect(plain('n16015')).toContain('двенадцать');expect(book('n16016').sourceRevision).toBe(94904);expect(plain('n16016')).toContain('я притихну');expect(book('n16016').words).toBeLessThan(250);});

test('heroic tales: long source translation and distinct traditional variant',()=>{const book=id=>json(join(server,'books',id+'.json'));const k=book('n16004');expect(k.words).toBeGreaterThan(2000);expect(k.sourceRevision).toBe(705292);expect(k.blocks.map(b=>b.text).join(' ')).toContain('целебной воды');expect(k.blocks.at(-1).text).toContain('женился');expect(book('n16018').sourceRevision).toBe(94742);expect(book('n16018').words).toBeGreaterThan(500);expect(json(join(server,'catalog.json')).find(b=>b.id==='b034').revision).toBe(5832700);});

test('Egg tale uses full source rather than short plot summary',()=>{const d=json(join(server,'books','n16014.json')),t=d.blocks.map(b=>b.text).join(' ');expect(d.sourceRevision).toBe(236758);expect(d.words).toBeGreaterThan(1700);for(const phrase of ['царица-мышь','в двух саженях','золотого зайца','монастырём','Забыл, забыл!'])expect(t).toContain(phrase);expect(d.blocks.at(-1).text).toContain('женился');});

test('three new Ukrainian folk records and familiar hero aliases',()=>{const book=id=>json(join(server,'books',id+'.json'));const c=json(join(server,'catalog.json'));for(const [id,rev,end,min] of [['n16019',94718,'так только его и видели',600],['n16020',94738,'двенадцать возов',350],['n16021',94707,'заячье сало',200]]){const d=book(id);expect(d.sourceRevision).toBe(rev);expect(d.words).toBeGreaterThan(min);expect(d.blocks.at(-1).text).toContain(end);}expect(c.find(b=>b.id==='af103').aliases).toContain('Илья Муромец и Соловей-разбойник');expect(c.find(b=>b.id==='b062').aliases).toContain('Василиса Премудрая');});
