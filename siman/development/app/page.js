/* 心眼 v1.5.10 — same-origin archive reader, conservative pacing and resumable index. */
(()=>{'use strict';
if(window.__simanPageV155)return;
window.__simanPageV155=true;
const TAG='siman-heart-v155',C=window.SimanCore,origin=location.origin,provider=C.providerFromUrl(location.href);
const PACE_MS=2700,MIN_RETRY_MS=15*60*1000;
const pending=new Map();let seq=0,running=false,cancelled=false,auth=null,lastRequestAt=0,activeController=null;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function emit(kind,data={}){window.postMessage({tag:TAG,kind,provider,...data},origin)}
let traceCount=0;
function trace(stage,text,level='TRACE'){emit('TRACE',{stage,text,level})}
function safePath(path){try{return new URL(path,origin).pathname.replace(/[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}/ig,'[ID]').replace(/\b[a-f0-9]{18,}\b/ig,'[ID]')}catch{return '(경로확인불가)'}}

function bridge(action,data={},timeout=30000){const seqId=++seq;return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{pending.delete(seqId);reject(Error('로컬 저장소 통신 시간 초과: '+action))},timeout);pending.set(seqId,result=>{clearTimeout(timer);if(result.ok)resolve(result);else reject(Error(result.error||'로컬 저장소 요청 실패: '+action))});window.postMessage({tag:TAG,kind:'BRIDGE',seqId,action,provider,...data},origin)})}
let lastProgress={stage:'연결 검증',done:0,total:0},lastProgressAt=Date.now();
function progress(stage,done,total,extra={}){lastProgress={stage,done,total,...extra};lastProgressAt=Date.now();emit('PROGRESS',lastProgress)}
function parseDelay(value){if(value==null||value==='')return 0;const raw=String(value).trim(),number=Number(raw);if(Number.isFinite(number)&&number>=0)return Math.round(number*1000);const unit=raw.match(/^(\d+(?:\.\d+)?)\s*(ms|s|sec|m|min|h)$/i);if(unit){let scale=/^ms$/i.test(unit[2])?1:/^h$/i.test(unit[2])?3600000:/^m(in)?$/i.test(unit[2])?60000:1000;return Math.round(Number(unit[1])*scale)}const ts=Date.parse(raw);return Number.isFinite(ts)?Math.max(0,ts-Date.now()):0}
async function request(path){const url=new URL(path,origin);if(url.origin!==origin)throw Error('교차 출처 요청 차단');const headers={Accept:'application/json'};if(auth&&provider==='chatgpt')headers.Authorization='Bearer '+auth;
 if(provider==='deepseek'){const token=window.SimanDeepSeekWeb?.readToken();if(!token)throw Error('DeepSeek 웹 로그인 토큰을 찾지 못했습니다. chat.deepseek.com에서 로그인한 후 다시 수집하세요.');headers.Authorization='Bearer '+token;}
 const controller=new AbortController();activeController=controller;
 // Covers BOTH the HTTP headers and the full JSON response body. Previously the
 // timer was cleared before response.json(), allowing an indefinite 200-response stall.
 const timer=setTimeout(()=>controller.abort(),60000);
 try{
  const response=await fetch(url.href,{credentials:'include',method:'GET',headers,cache:'no-store',redirect:'error',signal:controller.signal});
  if(!response.ok||++traceCount<=8||traceCount%20===0)trace('HTTP',safePath(path)+' status='+response.status,'HTTP');
  if(!response.ok){const err=Error('HTTP '+response.status+' '+url.pathname);err.status=response.status;err.path=url.pathname;err.retryAfterMs=Math.max(parseDelay(response.headers.get('Retry-After')),parseDelay(response.headers.get('x-oai-history-initial-retry-after')));throw err}
  const type=response.headers.get('content-type')||'';if(type.includes('text/html'))throw Error('인증 페이지 또는 HTML 응답: '+url.pathname);
  return await response.json();
 }catch(e){if(e.status==null)trace('NETWORK_ERROR',safePath(path)+' / '+String(e.message).slice(0,140),'ERROR');if(cancelled)e.cancelled=true;throw e}
 finally{clearTimeout(timer);if(activeController===controller)activeController=null}
}
async function cancellableWait(ms,stage,counts={}){const until=Date.now()+ms;while(Date.now()<until){if(cancelled)throw Object.assign(Error('수집 중지됨'),{cancelled:true});progress(stage,counts.done||0,counts.total||0,{...counts,...(stage.includes('429')?{retryAt:until}:{})});await sleep(Math.min(5000,Math.max(1,until-Date.now())))}}
// Respect server rate limiting: on the FIRST 429, stop detailed requests instead
// of automatically hammering the same endpoint repeatedly every ~2 minutes.
async function pacedRequest(path,counts={}){
 if(cancelled)throw Object.assign(Error('수집 중지됨'),{cancelled:true});
 const delta=Date.now()-lastRequestAt;
 if(lastRequestAt&&delta<PACE_MS)await cancellableWait(PACE_MS-delta,'요청 간격 조절',counts);
 lastRequestAt=Date.now();
 try{return await request(path)}catch(err){
  if(err.status!==429)throw err;
  const delay=Math.max(err.retryAfterMs||0,MIN_RETRY_MS);
  const retryAt=Date.now()+delay;
  trace('RATE_LIMIT',(provider==='deepseek'?'DeepSeek 웹':'ChatGPT')+' HTTP 429 · 요청 중단 · '+Math.ceil(delay/60000)+'분 뒤 재개 가능','WARN');
  progress('429 제한 · 요청 중단 · 재개 대기',counts.done||0,counts.total||0,{...counts,retryAt,details:'서버 제한이 발생해 추가 요청을 중단했습니다. 이전에 확보한 원문은 유지됩니다. 표시된 시간이 지난 후 수집·재개를 다시 실행하세요.'});
  const paused=Error((provider==='deepseek'?'DeepSeek 웹':'ChatGPT')+' 서버 요청 제한 · '+new Date(retryAt).toLocaleString()+' 이후 재개');
  paused.ratePaused=true;paused.retryAt=retryAt;throw paused;
 }
}
const MIN_OTHER_INTERVAL=provider==='claude'?1600:1100;let otherRequestAt=0;
async function serviceRequest(path,counts={}){
 if(provider==='chatgpt')return request(path);
 for(let attempt=0;attempt<2;attempt++){
  if(cancelled)throw Object.assign(Error('수집 중지됨'),{cancelled:true});
  let delta=Date.now()-otherRequestAt;
  if(otherRequestAt&&delta<MIN_OTHER_INTERVAL)await cancellableWait(MIN_OTHER_INTERVAL-delta,'요청 간격 조절',counts);
  otherRequestAt=Date.now();
  try{return await request(path)}catch(err){
   if(err.status!==429)throw err;
   const delay=Math.max(err.retryAfterMs||0,MIN_RETRY_MS*Math.pow(2,attempt));
   const retryAt=Date.now()+delay;
   if(attempt>0){const paused=Error((provider==='claude'?'Claude':'ChatLLM')+' 서버 요청 제한 · 다음 재시도 가능 시각 '+new Date(retryAt).toLocaleString());paused.ratePaused=true;paused.retryAt=retryAt;throw paused}
   await cancellableWait(delay,'429 제한 · 자동 재시도 대기',counts);
  }
 }
}
function arrays(payload,allowed,depth=0){if(depth>6||!payload||typeof payload!=='object')return [];if(Array.isArray(payload))return payload;for(const k of allowed)if(Array.isArray(payload[k]))return payload[k];for(const k of ['result','data','results','pagination'])if(payload[k]){const v=arrays(payload[k],allowed,depth+1);if(v.length)return v}return []}
async function register(providerName,records){if(!records.length)return;await bridge('CATALOG',{providerName,entries:records.map(r=>({id:String(r.id||''),title:String(r.title||''),projectName:String(r.projectName||'')})).filter(x=>x.id)},60000)}
async function completeIds(providerName,ids){if(!ids.length)return new Set();const done=new Set();for(let i=0;i<ids.length;i+=300){const result=await bridge('LOOKUP',{providerName,ids:ids.slice(i,i+300)},60000);for(const id of result.completeIds||[])done.add(String(id))}return done}
async function mark(providerName,id,status,reason=''){await bridge('MARK',{providerName,id:String(id),status,reason})}
async function markMany(providerName,ids,status){if(!ids.length)return;for(let i=0;i<ids.length;i+=250)await bridge('MARK_MANY',{providerName,ids:ids.slice(i,i+250),status},60000)}
async function saveRecord(c){if(!c?.id||!c.messages?.length)return false;const reply=await bridge('SAVE',{record:c},60000);return !!reply.ok}
function report(found,read,skipped,failed,processed,complete,extra={}){return {found,read,skipped,completed:read+skipped,errors:failed,processed,remaining:Math.max(0,found-processed),complete:!!complete,...extra}}
// Gemini official web history, separate from its previously visit-only DOM saving.
async function scanGemini(){
 const g=window.SimanGeminiWeb;
 if(!g||provider!=='gemini')throw Error('Gemini 웹 수집기 연결 실패');
 progress('Gemini 웹 로그인 확인',0,0);
 const session=await g.start(); // Token lives only in the site's MAIN world.
 const payload=await g.rpc(session,'MaZiqc',[1000]);
 const rows=g.list(payload);
 if(!rows.length)throw Error('Gemini 웹 목록이 비어 있습니다. gemini.google.com의 로그인 계정 및 이전 기록을 확인하세요.');
 await register('gemini',rows);
 const cached=await completeIds('gemini',rows.map(x=>x.id));
 await markMany('gemini',[...cached],'complete');
 let read=0,skipped=0,failed=0,processed=0,pausedError=null;
 const counts=()=>({read,skipped,failed,done:processed,total:rows.length});
 const listComplete=rows.length<1000;
 trace('GEMINI_LIST','공식 Gemini 웹 세션 '+rows.length+'건 · 한 번에 조회 가능한 목록 '+(listComplete?'확인':'상한에 도달'));
 for(const item of rows){
  if(cancelled)break;
  if(cached.has(item.id)){skipped++;processed++;continue}
  progress('Gemini 웹 원문 조회 중',processed,rows.length,counts());
  try{
   // Read-only history RPC; no chat creation, sending or mutation.
   const detail=await g.rpc(session,'hNvQHb',['c_'+item.id,1000,null,1,[0],[4],null,1]);
   const record=g.history(detail,item.id,item.title);
   if(record.messages.length){
    if(await saveRecord(record))read++;
    else{failed++;await mark('gemini',item.id,'failed','저장 실패')}
   }else{failed++;await mark('gemini',item.id,'failed','웹 원문 메시지 미발견')}
  }catch(e){
   if(e.status===429){
    const retryAt=Date.now()+Math.max(MIN_RETRY_MS,e.retryAfterMs||0);
    pausedError={retryAt};
    await mark('gemini',item.id,'retry','서버 요청 제한');
    trace('GEMINI_RATE_LIMIT','Gemini HTTP 429 · 추가 요청 중단 · '+new Date(retryAt).toLocaleString(),'WARN');
    break;
   }
   if(e.cancelled||cancelled)break;
   failed++;await mark('gemini',item.id,'failed',String(e.message||e).slice(0,110));
   trace('GEMINI_DETAIL_ERROR','Gemini 웹 원문 '+String(e.message||e).slice(0,110),'WARN');
   if(failed>=5){emit('WARN',{text:'Gemini 웹 원문 조회 오류 5건 — 추가 요청을 중단합니다.'});break;}
  }
  processed++;
  if(processed%10===0)progress('Gemini 웹 원문 저장 중',processed,rows.length,counts());
  if(!cancelled)await sleep(1800);
 }
 progress(pausedError?'429 제한 · 재개 대기':'Gemini 수집 종료',processed,rows.length,{...counts(),retryAt:pausedError?.retryAt||0});
 return report(rows.length,read,skipped,failed,processed,
  listComplete&&!pausedError&&!failed&&!cancelled&&processed===rows.length,
  {listComplete,paused:!!pausedError,retryAt:pausedError?.retryAt||0,cancelled});
}
// DeepSeek official web archive, NOT ChatLLM's DeepSeek model. Independent IDs and host.
// Fetches existing chats using the site's read-only authenticated REST endpoints.
async function scanDeepSeek(){
 const ds=window.SimanDeepSeekWeb;
 if(!ds||provider!=='deepseek')throw Error('DeepSeek 웹 수집기 초기화 실패');
 if(!ds.readToken())throw Error('DeepSeek 웹 로그인 정보가 없습니다. https://chat.deepseek.com/ 에 로그인하세요.');
 const sessions=new Map();let cursor='',listComplete=false,pausedError=null;
 const usedCursors=new Set();
 for(let page=0;page<80&&!cancelled;page++){
  let path='/api/v0/chat_session/fetch_page?count=100';
  if(cursor)path+='&cursor='+encodeURIComponent(cursor);
  let response;
  try{response=await pacedRequest(path,{done:sessions.size,total:0})}
  catch(e){if(e.ratePaused){pausedError=e;break}throw e}
  const parsed=ds.list(response);
  for(const item of parsed.rows)sessions.set(item.id,item);
  progress('DeepSeek 웹 대화 목록 확인',sessions.size,sessions.size,{
   details:'chat.deepseek.com 웹 세션 '+sessions.size+'건'});
  trace('DEEPSEEK_LIST','목록 페이지 '+(page+1)+' · 누적 '+sessions.size+'건'+(parsed.hasMore?' · 추가 페이지 존재':''));
  if(!parsed.hasMore){listComplete=true;break}
  if(!parsed.cursor||usedCursors.has(parsed.cursor)){
   emit('WARN',{text:'DeepSeek 웹에서 추가 목록은 있으나 페이지 커서를 제공하지 않았습니다. 확인된 대화를 우선 저장합니다.'});
   break;
  }
  usedCursors.add(parsed.cursor);cursor=parsed.cursor;
 }
 const rows=[...sessions.values()];
 if(!rows.length&&!pausedError)throw Error('DeepSeek 웹 대화 목록이 비어 있습니다. 로그인 상태 및 API 응답을 확인하세요.');
 await register('deepseek',rows);
 const cached=await completeIds('deepseek',rows.map(x=>x.id));
 await markMany('deepseek',[...cached],'complete');
 let read=0,skipped=0,failed=0,processed=0;
 const totals=()=>({read,skipped,failed,done:processed,total:rows.length});
 for(const x of rows){
  if(cancelled||pausedError)break;
  const id=x.id;
  if(cached.has(id)){skipped++;processed++;continue}
  progress('DeepSeek 웹 대화 원문 조회',processed,rows.length,{...totals(),details:'세션 '+(processed+1)+' / '+rows.length});
  try{
   // Zero cache parameters request the authoritative full transcript rather than
   // the site's incremental empty MERGE response.
   const payload=await pacedRequest('/api/v0/chat/history_messages?chat_session_id='+encodeURIComponent(id)+
      '&cache_version=0&cache_reset_at=0',totals());
   const record=ds.history(payload,id,x.title);
   if(record.messages?.length){
    if(await saveRecord(record))read++;
    else{failed++;await mark('deepseek',id,'failed','원문 저장 실패')}
   }else{failed++;await mark('deepseek',id,'failed','반환된 대화에 텍스트 없음')}
  }catch(e){
   if(e.ratePaused){pausedError=e;await mark('deepseek',id,'retry','429 제한');break}
   if(e.cancelled){cancelled=true;break}
   failed++;await mark('deepseek',id,'failed',String(e.message||e).slice(0,120));
   trace('DEEPSEEK_DETAIL_ERROR','원문 조회 실패 · '+String(e.message||e).slice(0,130),'WARN');
  }
  processed++;
  if(processed%10===0)progress('DeepSeek 웹 원문 누적',processed,rows.length,totals());
 }
 progress(pausedError?'429 제한 · 재개 대기':'수집 종료',processed,rows.length,{...totals(),retryAt:pausedError?.retryAt||0});
 return report(rows.length,read,skipped,failed,processed,
  listComplete&&!pausedError&&!cancelled&&!failed&&processed===rows.length,
  {listComplete,paused:!!pausedError,retryAt:pausedError?.retryAt||0,cancelled});
}
async function scanChatGPT(){let session=await pacedRequest('/api/auth/session');auth=session.accessToken||session.access_token||null;
 const items=new Map(),limit=100;let offset=0,lastSig='',listComplete=false,pausedError=null;
 for(let page=0;page<1000&&!cancelled;page++){
  let j;try{j=await pacedRequest('/backend-api/conversations?offset='+offset+'&limit='+limit+'&order=updated',{done:items.size,total:0})}catch(e){if(e.ratePaused){pausedError=e;break}throw e}
  const a=arrays(j,['items','conversations']),sig=a.slice(0,8).map(x=>x.id).join('|');if(!a.length){listComplete=true;break}
  if(sig===lastSig){emit('WARN',{text:'ChatGPT 목록이 반복되어 마지막 페이지를 확인할 수 없습니다.'});break}lastSig=sig;
  for(const x of a)if(x?.id)items.set(String(x.id),x);offset+=a.length;progress('전체 세션 목록 탐색',items.size,Number(j.total||0));
  if(j.has_more===false||Number(j.total)>0&&offset>=Number(j.total)||a.length<limit){listComplete=true;break}
 }
 const entries=[...items.values()];await register('chatgpt',entries.map(x=>({id:x.id,title:x.title,projectName:x.project_name||''})));
 const cached=await completeIds('chatgpt',entries.map(x=>String(x.id)));await markMany('chatgpt',[...cached],'complete');
 let read=0,skipped=0,failed=0,processed=0;
 const counts=()=>({done:processed,total:entries.length,read,skipped,failed,remaining:Math.max(0,entries.length-processed)});
 if(!pausedError)for(const x of entries){if(cancelled)break;const id=String(x.id);
   if(cached.has(id)){skipped++;processed++;if(processed%10===0)progress('원문 수집',processed,entries.length,counts());continue}
   try{const j=await pacedRequest('/backend-api/conversation/'+encodeURIComponent(id),counts());const c=C.chatgpt({...j,id,title:x.title||j.title,project_id:x.project_id||j.project_id});
      if(c?.messages.length){c.url=C.sourceUrl('chatgpt',id);if(await saveRecord(c))read++;else{failed++;await mark('chatgpt',id,'failed','원문 저장 실패')}}
      else{failed++;await mark('chatgpt',id,'failed','본문이 비어 있는 응답');emit('WARN',{text:'ChatGPT 원문 없음: '+id})}
   }catch(e){if(e.ratePaused){pausedError=e;await mark('chatgpt',id,'retry','429 서버 제한');break}if(e.cancelled)break;
     failed++;await mark('chatgpt',id,'failed',e.message);emit('WARN',{text:'ChatGPT 상세 실패 ('+id+'): '+e.message})}
   processed++;progress('원문 수집',processed,entries.length,counts());
 }
 const result=report(entries.length,read,skipped,failed,processed,listComplete&&failed===0&&!pausedError&&!cancelled&&processed===entries.length,{listComplete,paused:!!pausedError,cancelled, retryAt:pausedError?.retryAt||0});
 if(pausedError)emit('WARN',{text:'ChatGPT 429 제한으로 중단: 재시도 시점 '+new Date(pausedError.retryAt).toLocaleString()+' · 미수집 대화는 다음 수집에 유지'});
 progress(pausedError?'429 제한 · 재개 대기':cancelled?'사용자 중지':'수집 종료',processed,entries.length,{...counts(),retryAt:pausedError?.retryAt||0});return result}
// Claude is an account-scoped app. Organization discovery and conversation lists
// are separate; receiving zero organizations is NOT successful synchronization.
async function scanClaude(){
 const net=window.__SimanNetworkV155;
 const snapshot=()=>net?.snapshot()||{conversations:[],organizations:[],projects:[]};
 let orgs=[],orgError='';
 try{const j=await serviceRequest('/api/organizations');orgs=arrays(j,['organizations','items']);if(!orgs.length&&j&&typeof j==='object'&&(j.uuid||j.id))orgs=[j]}
 catch(e){if(e.ratePaused||e.cancelled)throw e;orgError=e.message}
 if(!orgs.length){try{const a=await serviceRequest('/api/account');orgs=a.memberships?.map(m=>m.organization).filter(Boolean)||arrays(a,['organizations','memberships'])}catch(e){if(e.ratePaused||e.cancelled)throw e;orgError+=(orgError?' / ':'')+e.message}}
 if(!orgs.length)orgs=snapshot().organizations;
 if(!orgs.length)throw Error('Claude 조직을 발견하지 못했습니다. 로그인된 Claude 탭을 새로고침한 뒤 다시 수집하세요.'+(orgError?' ('+orgError+')':''));
 const dedup=new Map();for(const o of orgs){const id=String(o?.uuid||o?.id||o?.organization_uuid||o?.organization?.uuid||'');if(id)dedup.set(id,o)}
 if(!dedup.size)throw Error('Claude 조직 응답에 유효한 조직 ID가 없습니다.');
 let found=0,read=0,skipped=0,failed=0,processed=0,allList=true,pausedError=null;const discovered=new Set();
 for(const [oid] of dedup){if(cancelled)break;const projectNames=new Map();let orgIssues=[];
  try{const p=await serviceRequest('/api/organizations/'+encodeURIComponent(oid)+'/projects?limit=500');for(const row of arrays(p,['projects','items']))projectNames.set(String(row.uuid||row.id),String(row.name||''))}
  catch(e){if(e.ratePaused||e.cancelled)throw e;orgIssues.push('프로젝트 조회: '+e.message)}
  let local=snapshot();for(const p of local.projects||[])projectNames.set(String(p.id),String(p.name));
  const conv=new Map();const observed=(local.conversations||[]).filter(x=>!x.organizationId||x.organizationId===oid);
  for(const x of observed)if(x.id)conv.set(String(x.id),{uuid:x.id,name:x.title,project_uuid:x.projectId});
  // Probe the real read-only list used by Claude.ai, not a developer-model API.
  const attempts=[
   '/api/organizations/'+encodeURIComponent(oid)+'/chat_conversations_v2?limit=1000&starred=false&consistency=eventual',
   '/api/organizations/'+encodeURIComponent(oid)+'/chat_conversations_v2?limit=1000&consistency=eventual',
   '/api/organizations/'+encodeURIComponent(oid)+'/chat_conversations?limit=1000&offset=0'
  ];
  let gotList=false,lastResponse=null;
  for(const path of attempts){if(cancelled)break;try{
   const j=await serviceRequest(path);const a=arrays(j,['chat_conversations','conversations','items','data']);lastResponse=j;
   if(!a.length){orgIssues.push('목록에 대화 없음: '+path.split('?')[0]);continue}
   for(const x of a){const id=String(x.uuid||x.id||'');if(id)conv.set(id,x)}gotList=true;
   if((j.has_more===true||j.hasMore===true||Number(j.total)>a.length)&&a.length>=1000){allList=false;orgIssues.push('Claude 목록이 단일 응답 제한에 도달: '+a.length+'건')}
   break;
  }catch(e){if(e.ratePaused||e.cancelled)throw e;orgIssues.push(e.message)}}
  if(!gotList){for(const t of net?.templates('list')||[]){if(!t.url.includes('/organizations/'+oid+'/'))continue;try{const j=await net.replay(t);for(const x of arrays(j,['chat_conversations','conversations','items','data'])){const id=String(x.uuid||x.id||'');if(id)conv.set(id,x)}if(conv.size){gotList=true;break}}catch(e){if(e.ratePaused||e.status===429)throw e;orgIssues.push('실제 요청 재조회: '+e.message)}}}
  // The app may already have populated a list before this run; save all observed records.
  for(const x of snapshot().conversations){if(x.id&&!conv.has(x.id)&&(x.raw?.organization_uuid===oid||x.raw?.organizationUuid===oid))conv.set(x.id,{uuid:x.id,name:x.title,project_uuid:x.projectId})}
  for(const id of conv.keys())discovered.add(id);
  found=discovered.size;
  if(!conv.size){allList=false;emit('WARN',{text:'Claude '+oid.slice(0,8)+' 대화 목록 0건: '+orgIssues.join(' / ').slice(0,300)});continue}
  await register('claude',[...conv].map(([id,x])=>({id,title:x.name||x.title||'',projectName:projectNames.get(String(x.project_uuid||x.project_id||''))||''})));
  const cached=await completeIds('claude',[...conv.keys()]);await markMany('claude',[...cached],'complete');
  for(const [id,x] of conv){if(cancelled||pausedError)break;if(cached.has(id)){skipped++;processed++;continue}
   try{let j;const path='/api/organizations/'+encodeURIComponent(oid)+'/chat_conversations/'+encodeURIComponent(id)+'?tree=true&rendering_mode=messages&render_all_tools=true';
    try{j=await serviceRequest(path)}catch(e){if(e.ratePaused||e.cancelled)throw e;j=await serviceRequest('/api/organizations/'+encodeURIComponent(oid)+'/chat_conversations/'+encodeURIComponent(id)+'?tree=True&rendering_mode=messages&render_all_tools=true&consistency=eventual')}
    const root=j?.result||j?.data||j;
    let c=C.claude({...root,uuid:id,name:x.name||root.name,project_uuid:x.project_uuid||root.project_uuid,project_name:projectNames.get(String(x.project_uuid||''))||''});
    if(c?.messages?.length){if(await saveRecord(c))read++;else{failed++;await mark('claude',id,'failed','저장 실패')}}
    else{failed++;await mark('claude',id,'failed','원문 비어 있음')}}
   catch(e){if(e.ratePaused){pausedError=e;await mark('claude',id,'retry','429 서버 제한');break}if(e.cancelled){cancelled=true;break}failed++;await mark('claude',id,'failed',e.message);emit('WARN',{text:'Claude 상세 실패 ('+id+'): '+e.message})}
   processed++;if(processed%5===0)progress('Claude 원문 수집',processed,found,{read,skipped,failed});
  }
  if(pausedError)break;
 }
 if(!found)throw Error('Claude에서 대화 목록을 수집하지 못했습니다. 조직 '+dedup.size+'개는 발견했으나 대화 목록은 비어 있거나 접근되지 않았습니다.');
 const completed=allList&&failed===0&&processed===found&&!cancelled&&!pausedError;
 progress(pausedError?'429 제한 · 재개 대기':'수집 종료',processed,found,{read,skipped,failed,retryAt:pausedError?.retryAt||0});
 return report(found,read,skipped,failed,processed,completed,{listComplete:allList,cancelled,paused:!!pausedError,retryAt:pausedError?.retryAt||0})
}
function findRecords(data,depth=0){if(depth>8||!data||typeof data!=='object')return [];if(Array.isArray(data)){const v=data.filter(x=>x&&typeof x==='object'&&(x.deploymentConversationId||x.conversationId||x.chatSessionId));if(v.length)return v;for(const item of data){const a=findRecords(item,depth+1);if(a.length)return a}return []}for(const k of ['deploymentConversations','deployment_conversations','conversations','chatSessions','items','records','results','data','result'])if(data[k]){const a=findRecords(data[k],depth+1);if(a.length)return a}return []}
async function exportChatLLM(id){const j=await serviceRequest('/api/exportDeploymentConversation?deploymentConversationId='+encodeURIComponent(id));const root=j?.result||j?.data||j;let html=root?.conversationExportHtml||root?.conversation_export_html||root?.html||root?.chat_session_export||root?.conversationExport?.html||'';return C.htmlMessages(typeof html==='string'?html:'')}
async function scanChatLLM(){
 const net=window.__SimanNetworkV155;
 if(!net)throw Error('ChatLLM 웹페이지 관찰기가 설치되지 않았습니다. 탭을 새로고침하세요.');
 let entries=new Map(),sources=new Set(),issues=[];
 function add(items){for(const x of items||[]){let id=String(x.id||x.deploymentConversationId||x.conversationId||x.chatSessionId||'');if(!id)continue;const previous=entries.get(id)||{};entries.set(id,{...previous,...x,id,title:String(x.title||x.name||x.deploymentConversationName||previous.title||''),projectName:String(x.projectName||x.chatllmProjectName||previous.projectName||''),url:String(x.url||x.conversationUrl||previous.url||'')})}}
 // In ChatLLM the first list requests can be issued several seconds AFTER page load.
 // Prior releases took a zero-item snapshot immediately and failed before those HTTP 200 responses arrived.
 const waitStarted=Date.now();let seenTemplates=0,lastNotice=0;
 while(!cancelled && Date.now()-waitStarted<16000){
   const snap=net.snapshot();add(snap.conversations);
   seenTemplates=net.templates('list').length;
   if(entries.size>0)break;
   // DOM fallback can discover entries before an API list is parsed.
   add(net.domList());if(entries.size>0)break;
   const elapsed=Date.now()-waitStarted;
   if(elapsed-lastNotice>1400){
      lastNotice=elapsed;
      progress('ChatLLM 목록 응답 대기',0,0,{details:'목록 조회 '+seenTemplates+'종 감지 · '+Math.ceil(elapsed/1000)+'초 경과'});
   }
   await sleep(350);
 }
 let snap=net.snapshot();add(snap.conversations);add(net.domList());
 if(entries.size)sources.add('웹페이지 대화 목록 응답');
 progress('ChatLLM 목록 확인 · 추가 페이지 검사',0,entries.size,{details:'목록 '+entries.size+'건 · 요청 형식 '+net.templates('list').length+'종'});
 trace('CATALOG_SNAPSHOT','대기 '+Math.max(0,Math.ceil((Date.now()-waitStarted)/1000))+'초 · 수집 후보 '+entries.size+'건 · 목록 요청 '+net.templates('list').length+'종');
 // Reuse only list requests observed on the actual authenticated page; never invent invalid API parameters.
 for(const t of net.templates('list')){if(cancelled)break;
   progress('ChatLLM 추가 목록 수집',0,entries.size,{details:'웹페이지에서 확인된 목록 요청 재사용'});
   try{const result=await net.replayListPages(t,{projectIds:snap.projects.map(p=>p.id)});add(net.snapshot().conversations);sources.add(new URL(t.url).pathname);trace('CATALOG_REPLAY','조회 '+result.requests+'회 · 누적 '+entries.size+'건')}
   catch(e){if(e.status===429||e.ratePaused)throw e;issues.push(new URL(t.url).pathname+': '+e.message);trace('CATALOG_REPLAY_ERROR',e.message,'WARN')}}
 snap=net.snapshot();add(snap.conversations);
 if(entries.size<10){progress('ChatLLM 사이드바 추가 탐색',0,entries.size);try{add(await net.scrollLists());add(net.snapshot().conversations)}catch(e){issues.push('사이드바 탐색: '+e.message)}}
 if(!entries.size){const observed=net.templates('list').length;
  throw Error(observed
    ?'ChatLLM 목록 API '+observed+'종을 관찰했지만 응답에서 세션 ID를 추출하지 못했습니다. 요청 응답 형식을 상세 진단에 기록했습니다.'+(issues.length?' · '+issues.slice(0,2).join('; '):'')
    :'ChatLLM 목록 요청을 16초 동안 감지하지 못했습니다. 웹페이지 대화 목록 로딩을 확인해 주세요.'+(issues.length?' · '+issues.slice(0,2).join('; '):''));}
 const projectNames=new Map(net.snapshot().projects.map(x=>[String(x.id),x.name]));
 for(const e of entries.values())if(!e.projectName&&e.projectId)e.projectName=projectNames.get(String(e.projectId))||'';
 const rows=[...entries.values()];await register('chatllm',rows.map(x=>({id:x.id,title:x.title,projectName:x.projectName})));
 const cached=await completeIds('chatllm',rows.map(x=>x.id));await markMany('chatllm',[...cached],'complete');
 let read=0,verified=0,partial=0,skipped=0,failed=0,processed=0,pausedError=null,consecutiveEmpty=0;
 const totals=()=>({read,skipped,failed,done:processed,total:rows.length});
 for(const x of rows){if(cancelled)break;const id=x.id;if(cached.has(id)){skipped++;processed++;if(processed%10===0)progress('ChatLLM 기존 완료 기록 확인',processed,rows.length,totals());continue}progress('ChatLLM 원문 조회 중',processed,rows.length,{...totals(),details:'현재 대화 '+(processed+1)+' / '+rows.length+' · 상세 응답 확인'});
  try{
   let c=null,raw=net.observedDetail(id);if(raw)c=C.chatllm({...raw,result:{...(raw.result||raw.data||raw),deploymentConversationId:id}},id);
   if(!c?.messages.length){for(const t of net.templates('detail')){progress('ChatLLM 관찰된 상세 요청 재사용',processed,rows.length,totals());try{const j=await net.replay(t,{id});c=C.chatllm({...j,result:{...(j.result||j.data||j),deploymentConversationId:id}},id);if(c?.messages.length)break}catch(e){if(e.status===429)throw e;issues.push('원문 재조회: '+e.message)}}}
   if(!c?.messages.length){progress('ChatLLM 직접 원문 조회',processed,rows.length,totals());try{raw=await serviceRequest('/api/getDeploymentConversation?deploymentConversationId='+encodeURIComponent(id)+'&filterIntermediateConversationEvents=false',totals());c=C.chatllm({...raw,result:{...(raw.result||raw.data||raw),deploymentConversationId:id}},id)}catch(e){if(e.ratePaused||e.cancelled)throw e;issues.push('원문 조회: '+e.message)}}
   if(!c?.messages.length){progress('ChatLLM HTML 내보내기 조회',processed,rows.length,totals());try{const m=await exportChatLLM(id);if(m.length)c=C.record('chatllm',id,x.title||'ChatLLM 대화',m,{url:x.url,projectName:x.projectName,expected:m.length,complete:true,source:'html-export'})}catch(e){if(e.ratePaused||e.cancelled)throw e;issues.push('HTML 원문: '+e.message)}}
   if(c?.messages.length){c.title=x.title||c.title;c.projectName=x.projectName||c.projectName;c.url=C.sourceUrl('chatllm',id,x.url||c.url);if(await saveRecord(c)){read++;if(c.complete)verified++;else partial++;consecutiveEmpty=0}else{failed++;await mark('chatllm',id,'failed','원문 저장 실패')}}
   else{failed++;consecutiveEmpty++;await mark('chatllm',id,'failed','ChatLLM 조회 응답에 메시지 없음')}
  }catch(e){if(e.ratePaused||e.status===429){pausedError=e;await mark('chatllm',id,'retry','서버 요청 제한');break}if(e.cancelled){cancelled=true;break}failed++;consecutiveEmpty++;await mark('chatllm',id,'failed',e.message);emit('WARN',{text:'ChatLLM 원문 실패 ('+id+'): '+e.message})}
  processed++;progress('ChatLLM 원문 수집',processed,rows.length,totals());
  if(consecutiveEmpty>=4){emit('WARN',{text:'ChatLLM 원문 조회 4회 연속 실패: 무의미한 추가 요청을 중단했습니다. 웹페이지의 실제 조회 경로 확인 필요.'});break}
 }
 if(issues.length)emit('WARN',{text:'ChatLLM 수집 경로 진단: '+issues.slice(0,5).join(' / ').slice(0,800)});
 progress(pausedError?'429 제한 · 재개 대기':'수집 종료',processed,rows.length,{...totals(),retryAt:pausedError?.retryAt||0});
 const listComplete=false; // Passive discovery alone cannot prove all projects/pages were enumerated.
 trace('CHATLLM_DETAIL_STATUS','원문 저장 성공 '+read+' · 상세 응답 완결 '+verified+' · 추가 페이지 필요 '+partial+' · 계정 목록 완결 미확인');
 return report(rows.length,read,skipped,failed,processed,false,{observedComplete:processed===rows.length&&!failed&&!pausedError&&!cancelled,listComplete,detailVerified:verified,detailPartial:partial,sourceCount:sources.size,paused:!!pausedError,cancelled,retryAt:pausedError?.retryAt||0});
}
async function run(){if(running)return;running=true;cancelled=false;auth=null;lastRequestAt=0;let heartbeat=null;
 try{await bridge('TEST',{},7000);trace('BRIDGE_OK','수집기↔로컬 저장소 왕복 통신 확인');progress('수집 시작',0,0);
 heartbeat=setInterval(()=>{if(running&&Date.now()-lastProgressAt>8000)emit('PROGRESS',{...lastProgress,details:'응답 대기 중 · 마지막 단계: '+lastProgress.stage})},10000);
 let result;
 if(provider==='chatgpt')result=await scanChatGPT();else if(provider==='claude')result=await scanClaude();else if(provider==='chatllm')result=await scanChatLLM();else if(provider==='deepseek')result=await scanDeepSeek();else if(provider==='gemini')result=await scanGemini();else throw Error('해당 서비스는 방문 대화 자동 저장만 지원합니다.');emit('DONE',{result});trace('DONE','발견 '+(result.found||0)+' / 저장 '+(result.read||0)+' / 계정 목록 확인 '+!!result.listComplete)}
 catch(e){if(e.cancelled)emit('DONE',{result:report(0,0,0,0,0,false,{cancelled:true})});else if(e.ratePaused){emit('DONE',{result:report(0,0,0,0,0,false,{paused:true,retryAt:e.retryAt||0})});emit('WARN',{text:'서버 429 요청 제한으로 수집 일시 중지'});}else {trace('FAIL',String(e?.message||e),'ERROR');emit('ERROR',{text:String(e?.message||e)})}}finally{clearInterval(heartbeat);running=false;auth=null}}
window.__SimanRunnerV155={start:()=>{if(running)return {ok:true,already:true};run();return {ok:true}},stop:()=>{cancelled=true;activeController?.abort();return {ok:true}},ping:()=>({ok:true,provider,version:'1.5.10',running,stage:lastProgress.stage,lastProgressAt}),pingStorage:async()=>{const started=Date.now();const r=await bridge('TEST',{},6500);return {ok:!!r.ok&&!!r.storageReady,latencyMs:Date.now()-started}}};
window.addEventListener('message',ev=>{if(ev.source!==window||ev.origin!==origin||ev.data?.tag!==TAG)return;const d=ev.data;if(d.kind==='BRIDGE_REPLY'){pending.get(d.seqId)?.(d);pending.delete(d.seqId)}if(d.kind==='COMMAND'){if(d.action==='START')run();if(d.action==='STOP')cancelled=true}});
})();
