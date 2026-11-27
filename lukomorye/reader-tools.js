// Reader enhancements: pure helpers, no storage or DOM side effects.
export const MAX_BOOKMARKS=100;
export function normalizeBookmarks(value){
 if(!Array.isArray(value))return [];
 const seen=new Set(),out=[];
 for(const b of value){
  if(!b||!Number.isSafeInteger(b.index)||b.index<0||!Number.isSafeInteger(b.revision)||b.revision<0)continue;
  const key=b.revision+':'+b.index;if(seen.has(key))continue;seen.add(key);
  out.push({index:b.index,revision:b.revision,label:typeof b.label==='string'?b.label.slice(0,180):'',created:Number.isFinite(b.created)?b.created:0});
  if(out.length>=MAX_BOOKMARKS)break;
 }
 return out.sort((a,b)=>a.index-b.index);
}
export function chapterAt(anchors,index){
 let active=-1;
 for(let i=0;i<anchors.length;i++){if(anchors[i]>index)break;active=i;}
 return active;
}
const shared=(a,b)=>a.filter(x=>b.includes(x)&&!['Лучшее','Новинки','Приключения'].includes(x)).length;
export function relatedBooks(current,books,available,done){
 const author=current.author||'';
 return books.filter(b=>b.id!==current.id&&available.has(b.id)&&b.sourceType!=='local').map(b=>{
  const sameAuthor=author.length>3&&author===b.author&&!/народ|неизвест/i.test(author);
  const common=shared(current.collections||[],b.collections||[]);
  const score=(sameAuthor?6:0)+(current.category===b.category?4:0)+common*2+(current.age&&current.age===b.age?1:0);
  return {b,score,done:done(b)};
 }).filter(x=>x.score>0).sort((a,b)=>Number(a.done)-Number(b.done)||b.score-a.score||a.b.title.localeCompare(b.b.title,'ru')).slice(0,4).map(x=>x.b);
}
export function sleepMinutes(value){const n=Number(value);return [0,5,10,15,30,45,60].includes(n)?n:0;}
export function sleepRemaining(deadline,now){return Math.max(0,Math.ceil((deadline-now)/1000));}
