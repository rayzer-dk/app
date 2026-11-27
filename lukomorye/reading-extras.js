// Local reading features. No network, account or analytics service.
export const SCROLL_SPEEDS=[12,18,28,42];
export function scrollSpeed(v){return SCROLL_SPEEDS.includes(Number(v))?Number(v):18;}
export function localDay(d=new Date()){
 return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
}
function validDay(key){
 if(!/^\d{4}-\d{2}-\d{2}$/.test(key))return false;
 const [y,m,d]=key.split('-').map(Number);
 if(y<2000||y>2200)return false;
 const date=new Date(y,m-1,d);
 return date.getFullYear()===y&&date.getMonth()===m-1&&date.getDate()===d;
}
export function normalizeReadingDays(value){
 if(!value||typeof value!=='object'||Array.isArray(value))return {};
 return Object.fromEntries(Object.entries(value).filter(([day,n])=>validDay(day)&&Number.isFinite(n)&&n>0).sort(([a],[b])=>a.localeCompare(b)).slice(-90).map(([day,n])=>[day,Math.min(86400,Math.floor(n))]).filter(([,n])=>n>0));
}
export function addSeconds(value,day,seconds){
 const result=normalizeReadingDays(value);
 if(validDay(day)&&Number.isFinite(seconds)&&seconds>0)result[day]=Math.min(86400,(result[day]||0)+Math.min(15,Math.floor(seconds)));
 return normalizeReadingDays(result);
}
export function readingWeek(progress,today=new Date()){
 const days=Array.from({length:7},(_,i)=>{const d=new Date(today.getFullYear(),today.getMonth(),today.getDate()-6+i);return {day:localDay(d),seconds:0}});
 const byDay=new Map(days.map(d=>[d.day,d]));
 for(const record of Object.values(progress||{})){
  for(const [day,n] of Object.entries(normalizeReadingDays(record?.readingDays))){
   const item=byDay.get(day);if(item)item.seconds=Math.min(86400,item.seconds+n);
  }
 }
 return days;
}
export function storyOfDay(books,available,minutes,day=localDay()){
 const safe=books.filter(b=>available.has(b.id)&&!b.intense&&b.sourceType!=='local'&&b.language==='ru'&&/сказки/i.test(b.category||'')&&minutes(b)>=3&&minutes(b)<=25);
 const selected=safe.filter(b=>b.collections?.includes('Лучшее'));
 const pool=(selected.length>=7?selected:safe).sort((a,b)=>a.id.localeCompare(b.id));
 if(!pool.length)return null;
 // The choice stays the same throughout a local calendar day.
 let seed=2166136261;for(const c of day)seed=Math.imul(seed^c.charCodeAt(0),16777619);
 return pool[(seed>>>0)%pool.length];
}
export function restoredLayout(saved,history){
 const valid=x=>x&&(x.mode==='grid'||x.mode==='compact')&&Number.isFinite(x.updated)&&x.updated>=0;
 const a={mode:saved?.catalogLayout,updated:Number(saved?.catalogLayoutUpdated)||0};
 const h=valid(history)?history:null;
 if(h&&(!valid(a)||h.updated>a.updated))return h;
 return valid(a)?a:{mode:'grid',updated:0};
}
