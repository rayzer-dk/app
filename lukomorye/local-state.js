export const STATE_KEYS=['luko-settings','luko-progress','luko-favorites'];
export const STATE_PREFIX='luko-mirror:';
export function stateRecord(raw,rev=0){
 if(typeof raw!=='string'||!Number.isSafeInteger(rev)||rev<0)return null;
 try{const value=JSON.parse(raw);if(!value||typeof value!=='object')return null;}catch{return null;}
 return {raw,rev};
}
export function normalizeRecord(value){return value&&stateRecord(value.raw,value.rev);}
export function newestRecord(...items){
 return items.map(normalizeRecord).filter(Boolean).reduce((best,r)=>!best||r.rev>best.rev?r:best,null);
}
