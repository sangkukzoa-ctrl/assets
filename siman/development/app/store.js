/* 心眼 v1.2 — extension-local archive, independent of the service worker. */
(function(G){'use strict';
const PREFIX='siman:v11:record:', META='siman:v11:status', MIG='siman:v11:migrated', CATALOG='siman:v11:catalog:';
const store=chrome.storage.local;
const DEBUG='siman:v15:debug';
let debugQueue=Promise.resolve();
function scrub(text){return String(text??'').replace(/(?:Bearer\s+)[\w.\-]+/gi,'Bearer [제외]').replace(/([?&](?:token|key|auth|session|conversationId|deploymentConversationId)\s*=)[^\s&]+/gi,'$1[제외]').replace(/[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}/gi,'[ID]').replace(/\b[a-f0-9]{24,}\b/gi,'[ID]').replace(/\b[A-Za-z0-9+/_-]{75,}={0,2}\b/g,'[값 제외]').slice(0,440)}
function appendDebug(e){debugQueue=debugQueue.catch(()=>{}).then(async()=>{const prev=(await store.get(DEBUG))[DEBUG]||[];const entry={at:new Date().toISOString(),provider:String(e?.provider||'system').slice(0,20),level:String(e?.level||'INFO').slice(0,12),stage:scrub(e?.stage||''),message:scrub(e?.message||'')};await store.set({[DEBUG]:[...prev,entry].slice(-600)})});return debugQueue}
async function getDebug(){await debugQueue.catch(()=>{});return (await store.get(DEBUG))[DEBUG]||[]}

function valid(r){return r&&SimanCore.PROVIDERS[r.provider]&&r.id&&Array.isArray(r.messages)}
function key(r){return PREFIX+r.provider+':'+r.id}
function merge(old={},next={}){
 const o={...old,...next};
 if(!next.messages?.length && old.messages?.length)o.messages=old.messages;
 else if(old.messages?.length && next.source==='deepseek-web-api' && next.complete && next.messages?.length) o.messages=next.messages;
 else if(old.messages?.length && (old.complete&&!next.complete || old.messages.length>next.messages.length))o.messages=old.messages;
 for(const x of ['url','projectName','projectId','title'])if(!next[x]&&old[x])o[x]=old[x];
 // A newly verified unpaginated transcript supersedes legacy totalEvents-based expectations.
 o.expected=next.complete===true&&next.messages?.length?Number(next.expected||next.messages.length):Math.max(Number(old.expected||0),Number(next.expected||0));
 o.complete=!!(o.messages?.length && (old.complete||next.complete) && (!o.expected||o.messages.length>=o.expected));
 o.key=o.provider+':'+o.id;
 return o;
}
async function save(record){if(!valid(record))throw Error('대화 원문 형식이 올바르지 않습니다.');const k=key(record);
 const previous=(await store.get(k))[k]; const combined=merge(previous||{},record);await store.set({[k]:combined});await mark(combined.provider,combined.id,combined.complete?'complete':'partial','',combined.title,combined.projectName);return combined;
}
async function saveMany(records){let done=0;for(const r of records){if(!valid(r))continue;await save(r);done++}return done}
async function all(){const keys=(await store.getKeys()).filter(k=>k.startsWith(PREFIX));if(!keys.length)return [];
 const out=[];for(let i=0;i<keys.length;i+=40){const data=await store.get(keys.slice(i,i+40));for(let k of keys.slice(i,i+40))if(valid(data[k]))out.push(data[k]);}return out;
}
async function one(id){return (await store.get(PREFIX+id))[PREFIX+id]||null}
async function clear(){const keys=(await store.getKeys()).filter(k=>k.startsWith(PREFIX)||k.startsWith(CATALOG)||k===META);for(let i=0;i<keys.length;i+=200)await store.remove(keys.slice(i,i+200))}
async function getCatalogs(){const ids=Object.keys(SimanCore.PROVIDERS),keys=ids.map(p=>CATALOG+p),data=await store.get(keys),result={};for(const p of ids)result[p]=data[CATALOG+p]||{};return result}
async function discover(provider,entries){if(!SimanCore.PROVIDERS[provider])return 0;const k=CATALOG+provider,dict=(await store.get(k))[k]||{};let n=0;for(const x of entries){if(!x||!x.id)continue;const id=String(x.id),old=dict[id]||{};dict[id]={...old,title:String(x.title||old.title||''),projectName:String(x.projectName||old.projectName||''),status:old.status||'pending',discoveredAt:old.discoveredAt||new Date().toISOString()};n++}await store.set({[k]:dict});return n}
async function mark(provider,id,status,reason='',title='',projectName=''){if(!SimanCore.PROVIDERS[provider]||!id)return;const k=CATALOG+provider,d=(await store.get(k))[k]||{},old=d[String(id)]||{};
 if(old.status==='complete'&&status!=='complete')return;d[String(id)]={...old,title:title||old.title||'',projectName:projectName||old.projectName||'',status,reason:String(reason||''),updatedAt:new Date().toISOString()};await store.set({[k]:d})}
async function markMany(provider,ids,status){if(!ids.length||!SimanCore.PROVIDERS[provider])return;const k=CATALOG+provider,d=(await store.get(k))[k]||{};for(const id of ids){const old=d[String(id)]||{};if(old.status==='complete'&&status!=='complete')continue;d[String(id)]={...old,status,reason:'',updatedAt:new Date().toISOString()}}await store.set({[k]:d})}
async function completeIds(provider,ids){const found=[];for(let i=0;i<ids.length;i+=100){const block=ids.slice(i,i+100),keys=block.map(id=>PREFIX+provider+':'+id),r=await store.get(keys);for(let j=0;j<block.length;j++)if(r[keys[j]]?.complete===true&&r[keys[j]]?.messages?.length)found.push(String(block[j]))}return found}
async function getStatus(){let s=(await store.get(META))[META];return s&&typeof s==='object'?s:{active:{},last:{},warnings:[]}}
async function setStatus(s){await store.set({[META]:{active:s.active||{},last:s.last||{},warnings:(s.warnings||[]).slice(-80),updatedAt:new Date().toISOString()}})}
async function updateEvent(e){let s=await getStatus(),p=e.provider;if(!p)return;
 if(e.kind==='PROGRESS')s.active[p]={stage:e.stage,done:e.done||0,total:e.total||0,read:e.read||0,skipped:e.skipped||0,failed:e.failed||0,remaining:e.remaining||0,retryAt:e.retryAt||0,details:e.details||'',updatedAt:new Date().toISOString()};
 else if(e.kind==='DONE'||e.kind==='ERROR'){s.last[p]={...(e.kind==='DONE'?e.result:{error:e.text}),finishedAt:Date.now()};delete s.active[p];if(e.kind==='ERROR')s.warnings.push(p+': '+e.text)}
 else if(e.kind==='WARN')s.warnings.push(p+': '+scrub(e.text));
 await setStatus(s);
 if(e.kind==='ERROR'||e.kind==='WARN'||e.kind==='DONE'||e.kind==='TRACE')await appendDebug({provider:p,level:e.kind,stage:e.stage||'',message:e.text||(e.result?('발견 '+(e.result.found||0)+'건 / 새 원문 '+(e.result.read||0)+'건 / 완료 '+!!e.result.complete):'')});
}
async function begin(provider){const s=await getStatus();s.active[provider]={stage:'연결',done:0,total:0,updatedAt:new Date().toISOString()};await setStatus(s)}
async function migrate(){const m=await store.get(MIG);if(m[MIG])return 0;
 let n=0,issues=[];
 // Old v1.0 unified IndexedDB, same extension origin. Run in search page, not content script.
 if(typeof SimanDB!=='undefined'){
  try{const old=await SimanDB.all();n+=await saveMany(old)}catch(e){issues.push('기존 기록 이전 실패: '+e.message)}
  try{await SimanDB.migrateLegacy();const old=await SimanDB.all();n+=await saveMany(old)}catch(e){issues.push('이전 세대 기록 변환 실패: '+e.message)}
 }
 if(issues.length){const state=await getStatus();state.warnings.push(...issues);await setStatus(state);return n}
 await store.set({[MIG]:true});return n;
}
G.SimanStore={PREFIX,META,CATALOG,DEBUG,appendDebug,getDebug,scrub,valid,merge,save,saveMany,all,one,clear,getCatalogs,discover,mark,markMany,completeIds,getStatus,setStatus,updateEvent,begin,migrate};
})(globalThis);
