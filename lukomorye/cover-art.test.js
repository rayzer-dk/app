import {test,expect} from 'vitest';
import {coverArt} from './cover-art.js';
test('custom scenes are deterministic, local and safe',()=>{
 const titles=['Царевна-лягушка','Жар-птица','Иван-царевич и серый волк','Сивка-бурка','Вокруг света за 80 дней','Алиса в Стране чудес','Остров сокровищ','Приёмыш','Дети капитана Гранта','Аленький цветочек','Карлик Нос','Паровоз'];
 const svgs=titles.map((title,i)=>coverArt({title,id:String(i),category:'Приключения'}));
 expect(new Set(svgs.map(s=>s.match(/data-scene="([^"]+)"/)[1])).size).toBe(12);
 for(const s of svgs){expect(s).toContain('viewBox="0 0 320 160"');expect(s).not.toMatch(/https?:|<script|<image/);}
 expect(coverArt({id:'x',title:'<script>alert(1)</script>'})).not.toContain('<script>');
});
