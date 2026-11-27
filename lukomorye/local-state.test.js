import {test,expect} from 'vitest';
import {stateRecord,normalizeRecord,newestRecord} from './local-state.js';
test('local file state accepts valid JSON and rejects malformed snapshots',()=>{
 expect(stateRecord('null',1)).toBeNull();
 expect(stateRecord('broken',1)).toBeNull();
 expect(stateRecord('{}',-1)).toBeNull();
 expect(normalizeRecord({raw:'{"catalogLayout":"compact"}',rev:10})).toEqual({raw:'{"catalogLayout":"compact"}',rev:10});
});
test('restore the newest persisted snapshot rather than an older initial value',()=>{
 const initial={raw:'{"catalogLayout":"grid"}',rev:0},newer={raw:'{"catalogLayout":"compact"}',rev:20};
 expect(newestRecord(initial,null,newer,{raw:'bad',rev:30})).toEqual(newer);
 expect(newestRecord(null)).toBeNull();
});
