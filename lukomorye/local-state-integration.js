// Browser file origins can expose non-persistent localStorage. Keep backups in
// sessionStorage, IndexedDB and (for same-document reload) bounded history state.
const mirrorState=new Map(),mirrorPending=new Map();
let mirrorTimer=0,mirrorRevision=0;
function getStorage(which,key){try{return window[which].getItem(key);}catch{return null;}}
function putStorage(which,key,value){try{window[which].setItem(key,value);return true;}catch{return false;}}
function decodeMirror(value){try{return normalizeRecord(JSON.parse(value));}catch{return null;}}
function getLocalRecord(key){
 const raw=getStorage('localStorage',key);
 const stamp=Number(getStorage('localStorage',STATE_PREFIX+key)||0);
 return stateRecord(raw,Number.isSafeInteger(stamp)&&stamp>=0?stamp:0);
}
function getSyncRecord(key){
 let historical=null;
 try{historical=normalizeRecord(history.state?.lukoFileState?.[key]);}catch{}
 return newestRecord(mirrorState.get(key),getLocalRecord(key),decodeMirror(getStorage('sessionStorage',STATE_PREFIX+key)),historical);
}
function saveMirroredRecord(key,record){
 mirrorState.set(key,record);mirrorRevision=Math.max(mirrorRevision,record.rev);
 const ok=putStorage('localStorage',key,record.raw);
 if(ok)putStorage('localStorage',STATE_PREFIX+key,String(record.rev));
 putStorage('sessionStorage',STATE_PREFIX+key,JSON.stringify(record));
 mirrorPending.set(key,record);
 if(!mirrorTimer)mirrorTimer=setTimeout(flushFileState,300);
}
function snapshotFileState(){
 if(!fileEdition)return;
 const entries=Object.fromEntries([...mirrorState].filter(([key])=>STATE_KEYS.includes(key)));
 try{
  if(JSON.stringify(entries).length<=300000)history.replaceState({...history.state,lukoFileState:entries},'');
 }catch{/* Some browsers restrict history changes on file URLs. */}
}
function flushFileState(){
 if(mirrorTimer)clearTimeout(mirrorTimer);mirrorTimer=0;
 if(!fileEdition||!db||!db.objectStoreNames.contains('preferences')||!mirrorPending.size)return;
 try{
  const tx=db.transaction('preferences','readwrite');
  for(const [id,record] of mirrorPending)tx.objectStore('preferences').put({id,...record});
  const batch=new Map(mirrorPending);mirrorPending.clear();
  tx.onabort=()=>{for(const [id,r] of batch)if(!mirrorPending.has(id))mirrorPending.set(id,r);};
 }catch{}
}
function safeSet(k,v){
 if(!fileEdition||!STATE_KEYS.includes(k)){
  if(!putStorage('localStorage',k,v))console.warn('Local save unavailable:',k);
  return;
 }
 mirrorRevision=Math.max(mirrorRevision+1,Date.now()*1000);
 const record=stateRecord(v,mirrorRevision);
 if(!record)return;
 saveMirroredRecord(k,record);
 // Settings and favorites are infrequent and safe to mirror immediately.
 if(k!=='luko-progress')snapshotFileState();
}
function readLocal(k,fallback){
 try{
  const rec=fileEdition&&STATE_KEYS.includes(k)?getSyncRecord(k):null;
  const value=rec?.raw??getStorage('localStorage',k);
  if(rec){mirrorState.set(k,rec);mirrorRevision=Math.max(mirrorRevision,rec.rev);}
  return value?JSON.parse(value):fallback;
 }catch{return fallback;}
}
async function restoreFileState(){
 if(!fileEdition)return;
 let disk=[];
 try{if(db?.objectStoreNames.contains('preferences'))disk=await dbAll('preferences');}catch{}
 for(const key of STATE_KEYS){
  const record=newestRecord(getSyncRecord(key),disk.find(r=>r.id===key));
  if(!record)continue;
  try{
   const value=JSON.parse(record.raw);
   if(key==='luko-settings'&&value&&!Array.isArray(value)){
    settings={...defaultSettings,...Object.fromEntries(Object.keys(defaultSettings).filter(k=>Object.hasOwn(value,k)).map(k=>[k,value[k]]))};
   }else if(key==='luko-progress')progress=validProgress(value);
   else if(key==='luko-favorites')favorites=new Set(validFavorites(value));
   saveMirroredRecord(key,record);
  }catch{}
 }
 const layout=restoredLayout(settings,history.state?.lukoLayout);
 settings.catalogLayout=layout.mode;settings.catalogLayoutUpdated=layout.updated;
 // A history-only restored layout must be written back to the primary store.
 safeSet('luko-settings',JSON.stringify(settings));
 safeSet('luko-progress',JSON.stringify(progress));
 safeSet('luko-favorites',JSON.stringify([...favorites]));
 applySettings();flushFileState();snapshotFileState();
}
