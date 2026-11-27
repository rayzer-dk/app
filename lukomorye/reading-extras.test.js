import {test,expect} from 'vitest';
import {localDay,normalizeReadingDays,addSeconds,readingWeek,storyOfDay,restoredLayout,scrollSpeed} from './reading-extras.js';
test('reading days validate and cap elapsed time',()=>{
 expect(normalizeReadingDays({'2026-02-30':100,'2026-11-27':21,'2026-11-26':-1})).toEqual({'2026-11-27':21});
 expect(addSeconds({'2026-11-27':21},'2026-11-27',3600)).toEqual({'2026-11-27':36});
 expect(localDay(new Date(2026,10,27,12))).toBe('2026-11-27');
 const w=readingWeek({a:{readingDays:{'2026-11-27':35}},b:{readingDays:{'2026-11-27':25,'2026-11-26':20}}},new Date(2026,10,27));
 expect(w).toHaveLength(7);expect(w.at(-1).seconds).toBe(60);expect(w.at(-2).seconds).toBe(20);
});
test('catalog layout restores the newest valid choice',()=>{
 expect(restoredLayout({catalogLayout:'compact',catalogLayoutUpdated:20},{mode:'grid',updated:10}).mode).toBe('compact');
 expect(restoredLayout({catalogLayout:'grid',catalogLayoutUpdated:10},{mode:'compact',updated:20}).mode).toBe('compact');
 expect(restoredLayout({catalogLayout:'invalid'},null)).toEqual({mode:'grid',updated:0});
});
test('daily story is deterministic and excludes frightening, unavailable and long works',()=>{
 const books=Array.from({length:12},(_,i)=>({id:'a'+i,language:'ru',category:'Сказки писателей',intense:i===0,minutes:i===1?40:10,collections:['Лучшее']}));
 const available=new Set(books.slice(0,11).map(b=>b.id));
 const a=storyOfDay(books,available,b=>b.minutes,'2026-11-27');
 expect(a).toEqual(storyOfDay([...books].reverse(),available,b=>b.minutes,'2026-11-27'));
 expect(['a0','a1','a11']).not.toContain(a.id);expect(scrollSpeed(99)).toBe(18);
});
