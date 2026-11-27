import {test,expect} from 'vitest';
import {normalizeBookmarks,chapterAt,relatedBooks,sleepMinutes,sleepRemaining} from './reader-tools.js';
test('bookmarks normalize, deduplicate and reject malformed values',()=>{
 expect(normalizeBookmarks([{index:4,revision:1,label:'a'},{index:4,revision:1,label:'b'},{index:2,revision:1,label:'c'},{index:-1,revision:1},{index:1,revision:'1'}]).map(x=>x.index)).toEqual([2,4]);
 expect(normalizeBookmarks(Array.from({length:130},(_,i)=>({index:i,revision:0}))).length).toBe(100);
});
test('chapter selection and sleep deadlines',()=>{
 expect(chapterAt([0,4,20],18)).toBe(1);
 expect(chapterAt([0,4,20],20)).toBe(2);
 expect(chapterAt([],0)).toBe(-1);
 expect(sleepMinutes('15')).toBe(15);expect(sleepMinutes('17')).toBe(0);
 expect(sleepRemaining(5000,3501)).toBe(2);expect(sleepRemaining(5000,6000)).toBe(0);
});
test('related suggestions exclude current and unavailable, prioritize unread',()=>{
 const b={id:'a',title:'А',author:'Автор',category:'Приключения',collections:['О животных']};
 const pool=[b,{...b,id:'b',title:'Б'},{...b,id:'c',title:'В'},{...b,id:'d',title:'Г'}];
 expect(relatedBooks(b,pool,new Set(['a','b','c']),x=>x.id==='b').map(x=>x.id)).toEqual(['c','b']);
});
