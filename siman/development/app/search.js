/* 心眼 v1.5.6: local archive with explicit crawl counters. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const PROVIDERS=SimanCore.PROVIDERS;
const BASE={chatllm:'https://apps.abacus.ai/chatllm/',chatgpt:'https://chatgpt.com/',claude:'https://claude.ai/'};
let cache=new Map(),hits=[],selected=null,record=null,lastQ='',searchId=0,lastStatus='',refreshTimer=0;
let batchRunning=false,batchStop=false,batchCurrent='',batchCompleted=[];
const BULK=['chatllm','claude','chatgpt'];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const debug=(stage,message,level='INFO',provider='system')=>SimanStore.appendDebug({stage,message,level,provider}).catch(()=>{});

const toast=s=>{const el=$('toast');el.textContent=String(s);el.classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.classList.remove('show'),5500)};
const label=role=>role==='user'?'사용자':role==='assistant'?'AI':role==='제목'?'제목':'메시지';
function highlight(node,value,term){const s=String(value??'');node.replaceChildren();if(!term){node.textContent=s;return}
 // Literal search is deliberately not a regexp; preserves special characters such as [, (, +.
 const n=s.normalize('NFKC').toLocaleLowerCase(),q=term.normalize('NFKC').toLocaleLowerCase();let from=0,at,count=0;
 while((at=n.indexOf(q,from))>=0&&count++<200){node.append(document.createTextNode(s.slice(from,at)));const mark=document.createElement('mark');mark.textContent=s.slice(at,at+term.length);node.append(mark);from=at+term.length;if(from>=s.length)break}
 node.append(document.createTextNode(s.slice(from)))}
async function renderStats(){const catalog=await SimanStore.getCatalogs(),by={},all=[...cache.values()];let grand={found:0,complete:0,partial:0,pending:0,retry:0,failed:0};
 for(const p of Object.keys(PROVIDERS)){
  const index=catalog[p]||{},map=new Map(all.filter(r=>r.provider===p).map(r=>[String(r.id),r]));const ids=new Set([...Object.keys(index),...map.keys()]);let x={found:ids.size,complete:0,partial:0,pending:0,retry:0,failed:0};
  for(const id of ids){const c=map.get(id),status=index[id]?.status;if(c?.complete&&c.messages?.length)x.complete++;
   else if(status==='retry')x.retry++;
   else if(status==='failed')x.failed++;
   else if(c?.messages?.length)x.partial++;
   else x.pending++}
  by[p]=x;for(const k of Object.keys(grand))grand[k]+=x[k]
 }
 const root=$('stats');root.replaceChildren();
 function row(label,value,cls=''){const e=document.createElement('div');e.className='stat '+cls;const name=document.createElement('span');name.textContent=label;const v=document.createElement('b');v.textContent=value+'건';e.append(name,v);return e}
 root.append(row('검색 가능한 대화',grand.complete+grand.partial,'good'),row('발견된 세션',grand.found,'strong'),row('원문 수집 완료',grand.complete,'good'),row('원문 일부·완결 미확인',grand.partial),row('아직 미수집',grand.pending),row('재시도 대기',grand.retry,'warn'),row('수집 실패',grand.failed,'bad'));
 const head=document.createElement('p');head.className='sub statGuide';head.textContent='검색 가능 = 완료 및 일부 확보. 상세 원문 확보와 전체 계정 목록 발견 완료는 다른 상태입니다. 발견은 현재 확인된 대화 수이며, 계정 전체 총량을 뜻하지 않습니다.';root.append(head);
 for(const p of Object.keys(PROVIDERS)){
  const x=by[p],section=document.createElement('section');section.className='sourceStats';const heading=document.createElement('strong');heading.textContent=PROVIDERS[p];section.append(heading);
  const desc=document.createElement('div');desc.className='miniStats';desc.textContent=`발견 ${x.found} · 완료 ${x.complete} · 일부/미확인 ${x.partial} · 미수집 ${x.pending} · 재시도 ${x.retry} · 실패 ${x.failed}`;section.append(desc);root.append(section)
 }
}
async function loadRecords(){const arr=await SimanStore.all();cache=new Map(arr.map(r=>[r.key,r]));await renderStats();if($('query').value.trim())doSearch()}
function timeLabel(ms){if(!ms)return '';const diff=Number(ms)-Date.now();if(diff<=0)return '재시도 가능';const sec=Math.ceil(diff/1000);return '재시도까지 '+(sec>=3600?Math.floor(sec/3600)+'시간 ':'')+(sec>=60?Math.floor(sec%3600/60)+'분 ':'')+(sec%60)+'초'}
async function renderStatus(){try{const state=await SimanStore.getStatus(),lines=[];
 for(const [p,s] of Object.entries(state.active)){lines.push(`${PROVIDERS[p]||p} · ${s.stage||'수집 중'}`);lines.push(`처리 ${s.done||0}건 · 발견 ${s.total||0}건 · 신규 완료 ${s.read||0}건 · 기존 완료 ${s.skipped||0}건 · 실패 ${s.failed||0}건`);if(s.retryAt)lines.push(timeLabel(s.retryAt));if(s.details)lines.push(s.details)}
 for(const [p,s] of Object.entries(state.last)){if(s.error){lines.push(`${PROVIDERS[p]||p}: ${s.error}`);continue}lines.push(`${PROVIDERS[p]||p} 마지막 수집: 발견 ${s.found||0}건 · 이번 원문 저장 ${s.read||0}건 · 기존 완료 ${s.skipped||0}건 · 실패 ${s.errors||0}건 · 남음 ${s.remaining||0}건${s.complete?' · 목록·원문 완료':' · 전체 목록 확인 중'}`);if(p==='chatllm'&&s.detailVerified!=null)lines.push(`ChatLLM 상세 응답: 완결 ${s.detailVerified}건 · 추가 페이지 필요 ${s.detailPartial||0}건 · 전체 계정 목록 완결은 별도 미확인`);if(s.retryAt)lines.push(timeLabel(s.retryAt));if(s.paused)lines.push('HTTP 429 제한으로 추가 요청을 중단했습니다. 재시도 가능 시각 이후 수집·재개를 실행하세요.')}
 const text=lines.join('\n');if(text!==lastStatus){$('progress').textContent=text;lastStatus=text}
 $('diagnostic').textContent=(state.warnings||[]).slice(-3).join('\n');}catch(e){$('diagnostic').textContent='수집 상태 읽기 실패: '+e.message}}
function doSearch(){const q=$('query').value.trim();lastQ=q;const h=$('hits');const id=++searchId;
 if(!q){h.innerHTML='<div class="placeholder">검색어를 입력하면 저장된 모든 대화 원문에서 찾습니다.</div>';$('hitCount').textContent='';return}
 // In-memory cache lets every keystroke search without a worker or repeated disk reads.
 const r=SimanCore.find([...cache.values()],q,{provider:$('provider').value,role:$('role').value},1500);if(id!==searchId)return;
 hits=r;h.replaceChildren();$('hitCount').textContent=r.length+'개 일치'+(r.length>=1500?' (표시 제한)':'');
 if(!r.length){const div=document.createElement('div');div.className='placeholder small';div.textContent=cache.size?'일치하는 문장이 없습니다. 수집 상태와 서비스 필터를 확인하세요.':'저장된 원문이 없습니다. 왼쪽 서비스 전체 수집을 먼저 실행하세요.';h.append(div);return}
 const fragment=document.createDocumentFragment();for(const [i,x] of r.entries()){const div=document.createElement('div');div.className='hit';div.setAttribute('role','button');div.tabIndex=0;const heading=document.createElement('div');heading.className='heading';const t=document.createElement('span');t.textContent=x.title;const meta=document.createElement('small');meta.textContent=(PROVIDERS[x.provider]||x.provider)+' · '+(x.projectName?x.projectName+' · ':'')+label(x.role);heading.append(t,meta);const summary=document.createElement('div');summary.className='excerpt';highlight(summary,x.snippet,q);div.append(heading,summary);div.onclick=()=>select(i);div.onkeydown=e=>{if(e.key==='Enter')select(i)};fragment.append(div)}h.append(fragment)}
async function select(i){selected=hits[i];record=cache.get(selected.key);if(!record){record=await SimanStore.one(selected.key);if(!record){toast('저장된 원문을 찾을 수 없습니다.');return}}
 $('readerTitle').textContent=record.title;$('readerSource').textContent=(PROVIDERS[record.provider]||record.provider)+(record.projectName?' / '+record.projectName:'')+' · 메시지 '+record.messages.length+'개';const view=$('readerContent');view.replaceChildren();let idx=record.messages.findIndex(m=>m.index===selected.index);if(idx<0)idx=0;const excerpt=selected.index===-1?record.messages.slice(0,5):record.messages.slice(Math.max(0,idx-2),Math.min(record.messages.length,idx+3));
 for(const m of excerpt){const div=document.createElement('div');div.className='turn'+(m.index===selected.index?' focus':'');const who=document.createElement('div');who.className='who';who.textContent=label(m.role)+' · 메시지 '+(Number(m.index)+1);const body=document.createElement('div');body.className='body';highlight(body,m.text,lastQ);div.append(who,body);view.append(div)}
 for(const id of ['copyMessage','copyChat','openOriginal'])$(id).disabled=false;
 [...$('hits').children].forEach((div,n)=>div.classList.toggle('selected',n===i));}
async function copy(value){try{await navigator.clipboard.writeText(value);toast('복사했습니다.')}catch(e){toast('클립보드 복사 실패: '+e.message)}}
const formatted=m=>`${label(m.role)} (#${Number(m.index)+1})\n${m.text||''}`;
$('copyDiagnostics').onclick=async()=>{
 try{const s=await SimanStore.getStatus(),cats=await SimanStore.getCatalogs();const out=[];
 out.push('심안 v1.5.6 · 수집 진단 (원문 및 로그인 정보 미포함)',new Date().toISOString());
 for(const p of Object.keys(PROVIDERS)){const c=cats[p]||{};const statuses={};for(const x of Object.values(c))statuses[x.status||'pending']=(statuses[x.status||'pending']||0)+1;
 out.push(`${PROVIDERS[p]}: 발견 ${Object.keys(c).length}, ${JSON.stringify(statuses)}`);}
 for(const [p,v] of Object.entries(s.active||{}))out.push(`${p} 진행: ${v.stage||''} · 처리 ${v.done||0}/${v.total||0} · 429 재개 ${v.retryAt?new Date(v.retryAt).toISOString():'-'}`);
 for(const [p,v] of Object.entries(s.last||{}))out.push(`${p} 마지막 수집: 완료=${v.read||0}, 기존=${v.skipped||0}, 실패=${v.errors||0}, 남음=${v.remaining||0}, 미완료=${!v.complete}`);
 for(const w of (s.warnings||[]).slice(-12))out.push(String(w).replace(/[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}/ig,'[세션ID]'));
 await copy(out.join('\n'));}catch(e){toast('진단 복사 실패: '+e.message)};
};
$('saveDebug').onclick=async()=>{
 const button=$('saveDebug');button.disabled=true;
 try{
  const state=await SimanStore.getStatus(),cats=await SimanStore.getCatalogs(),logs=await SimanStore.getDebug();
  const lines=['심안(心眼) v1.5.6 상세 디버그 로그',
    '생성: '+new Date().toISOString(),
    '브라우저: '+navigator.userAgent.replace(/\d{3,}/g,'[숫자]'),
    '확장 컨텍스트 정상: '+Boolean(chrome.runtime?.id),
    '안내: 로그인 정보, 메시지 원문, 실제 검색어, 요청 쿼리, 전체 세션 ID를 포함하지 않습니다.',
    '', '=== 서비스별 발견·수집 현황 ==='];
  for(const p of Object.keys(PROVIDERS)){
   const values=Object.values(cats[p]||{}),counts={};
   for(const x of values){const v=x.status||'pending';counts[v]=(counts[v]||0)+1}
   lines.push(PROVIDERS[p]+': 발견 '+values.length+' · '+JSON.stringify(counts));
   const a=state.active?.[p],last=state.last?.[p];
   if(a)lines.push('  실행: '+SimanStore.scrub(a.stage)+' ('+(a.done||0)+'/'+(a.total||'미확인')+')');
   if(last)lines.push('  마지막 결과: '+SimanStore.scrub(JSON.stringify(last)));
  }
  lines.push('', '=== 대상 탭 및 수집기 연결 ===');
  for(const p of BULK){
   try{
    const tabs=await chrome.tabs.query({}),tab=tabs.find(x=>tabMatches(p,x.url));
    if(!tab){lines.push(PROVIDERS[p]+': 열린 탭 없음');continue}
    const out=await chrome.scripting.executeScript({target:{tabId:tab.id},world:'MAIN',func:()=>({runner:window.__SimanRunnerV155?.ping()||null,observer:window.__SimanNetworkV155?.snapshot?{count:window.__SimanNetworkV155.snapshot().conversations.length,templates:window.__SimanNetworkV155.snapshot().templates.map(x=>{try{return new URL(x).pathname}catch{return '(오류)'}})}:null})});
    lines.push(PROVIDERS[p]+': '+SimanStore.scrub(JSON.stringify(out[0]?.result||{})));
    const check=await chrome.scripting.executeScript({target:{tabId:tab.id},world:'MAIN',func:async()=>{try{return await window.__SimanRunnerV155?.pingStorage?.()||{ok:false,error:'수집기 미설치'}}catch(e){return {ok:false,error:String(e.message||e)}}}});
    lines.push('  로컬 저장소 통신: '+SimanStore.scrub(JSON.stringify(check[0]?.result||{})));
    if(!check[0]?.result?.ok)lines.push('  복구 안내: 「연결 복구」 버튼 또는 해당 서비스 탭 새로고침 후 다시 검사');
   }catch(e){lines.push(PROVIDERS[p]+': '+SimanStore.scrub(e.message))}
  }
  lines.push('', '=== 방문 저장 서비스 진단 ===');
  for(const p of ['gemini','deepseek','grok']){
   try{
    const tabs=await chrome.tabs.query({}),tab=tabs.find(x=>tabMatches(p,x.url));
    if(!tab){lines.push(PROVIDERS[p]+': 열린 탭 없음');continue}
    const result=await chrome.scripting.executeScript({target:{tabId:tab.id},world:'ISOLATED',func:()=>globalThis.__SimanVisitHealthV155?.()||{ok:false,stage:'방문 저장 스크립트 미연결'}});
    const v=result?.[0]?.result||{ok:false,stage:'응답 없음'};
    lines.push(PROVIDERS[p]+': '+SimanStore.scrub(JSON.stringify(v)));
   }catch(e){lines.push(PROVIDERS[p]+': 검사 실패 · '+SimanStore.scrub(e.message))}
  }
  lines.push('', '=== 최근 오류 ===',...(state.warnings||[]).slice(-80).map(x=>SimanStore.scrub(x)), '', '=== 시간순 수집 기록 (최근 600개) ===');
  for(const e of logs)lines.push([e.at,e.provider,e.level,e.stage,e.message].map(x=>SimanStore.scrub(x)).join(' | '));
  const text=lines.join('\n');
  const blob=new Blob([text],{type:'text/plain;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');
  const now=new Date(),stamp=now.getFullYear()+String(now.getMonth()+1).padStart(2,'0')+String(now.getDate()).padStart(2,'0')+'_'+String(now.getHours()).padStart(2,'0')+String(now.getMinutes()).padStart(2,'0')+String(now.getSeconds()).padStart(2,'0');
  a.href=url;a.download='Siman_v1.5.6_Debug_'+stamp+'.txt';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);
  toast('진단 TXT를 저장했습니다.');
 }catch(e){toast('진단 로그 저장 실패: '+e.message);await debug('EXPORT_ERROR',e.message,'ERROR')}
 finally{button.disabled=false}
};
$('copyMessage').onclick=()=>{const m=record?.messages?.find(m=>m.index===selected?.index);copy(m?formatted(m):record?.title||'')};
$('copyChat').onclick=()=>{if(record)copy('# '+record.title+'\n\n'+record.messages.map(formatted).join('\n\n-----\n\n'))};
function tabMatches(provider,url=''){try{const u=new URL(url);if(SimanCore.providerFromUrl(url)!==provider)return false;return provider!=='chatllm'||u.pathname.startsWith('/chatllm')}catch{return false}}
async function waitTab(id){let t=await chrome.tabs.get(id);if(t.status==='complete')return;
 await new Promise((resolve,reject)=>{const timer=setTimeout(()=>{chrome.tabs.onUpdated.removeListener(cb);reject(Error('사이트 로딩 시간 초과'))},30000);function cb(tabId,info){if(tabId===id&&info.status==='complete'){clearTimeout(timer);chrome.tabs.onUpdated.removeListener(cb);resolve()}}chrome.tabs.onUpdated.addListener(cb)})}
async function tabFor(p){const all=await chrome.tabs.query({});let t=all.find(x=>tabMatches(p,x.url));if(!t){t=await chrome.tabs.create({url:BASE[p],active:true});await waitTab(t.id)}else if(t.status!=='complete')await waitTab(t.id);return t}
async function installBridge(tabId){const target={tabId};
 // Inject into BOTH isolated and page worlds, and verify that the version matches.
 await chrome.scripting.executeScript({target,world:'ISOLATED',files:['core.js','store.js','content.js']});
 await chrome.scripting.executeScript({target,world:'MAIN',files:['core.js','network.js','page.js']});
 let isolated;
 for(let attempt=0;attempt<8;attempt++){
  isolated=await chrome.scripting.executeScript({target,world:'ISOLATED',func:()=>({ready:!!globalThis.__simanContentV155,storage:!!chrome.storage?.local})});
  if(isolated[0]?.result?.ready&&isolated[0]?.result?.storage)break;
  await sleep(300);
 }
 if(!isolated?.[0]?.result?.ready||!isolated?.[0]?.result?.storage)throw Error('로컬 저장용 스크립트 초기화 실패 · 저장소 의존성 또는 확장 프로그램 재로드 상태 확인');
 const main=await chrome.scripting.executeScript({target,world:'MAIN',func:()=>window.__SimanRunnerV155?.ping()||{ok:false,error:'runner missing'}});
 const ping=main[0]?.result;
 if(!ping?.ok||ping.version!=='1.5.6')throw Error('수집기 버전 연결 실패: '+(ping?.error||'다른 버전 실행 중'));
 // A marker means nothing unless main-world collector can exchange a message with isolated storage.
 const echo=await chrome.scripting.executeScript({target,world:'MAIN',func:async()=>{try{return await window.__SimanRunnerV155.pingStorage()}catch(e){return {ok:false,error:String(e.message||e)}}}});
 const bridge=echo[0]?.result;
 if(!bridge?.ok)throw Error('실제 저장소 왕복 통신 실패: '+(bridge?.error||'응답 없음'));
 await debug('BRIDGE_OK','페이지 수집기 ↔ 로컬 저장소 왕복 확인 · '+bridge.latencyMs+'ms','INFO');
 return ping;
}
async function probeVersion(tabId){try{const r=await chrome.scripting.executeScript({target:{tabId},world:'MAIN',func:()=>window.__SimanRunnerV155?.ping()||null});return r[0]?.result||null}catch{return null}}
async function prepareConnection(p){
 let tab=await tabFor(p);let ping=await probeVersion(tab.id),reloaded=false;
 // Old extension contexts retain stale message handlers. Reload ONCE if a mismatched/no runner exists.
 if(ping?.version!=='1.5.6'){
  await debug('REFRESH',PROVIDERS[p]+' 이전 버전 또는 수집기 없음 — 서비스 탭 자동 새로고침');
  await chrome.tabs.reload(tab.id);await waitTab(tab.id);reloaded=true;
 }
 try{ping=await installBridge(tab.id)}
 catch(e){
  if(reloaded)throw e;
  await debug('RECOVER',PROVIDERS[p]+' 연결 재시도: '+e.message,'WARN',p);
  await chrome.tabs.reload(tab.id);await waitTab(tab.id);ping=await installBridge(tab.id);reloaded=true;
 }
 if((p==='chatllm'||p==='claude')&&!reloaded){
  const snap=await chrome.scripting.executeScript({target:{tabId:tab.id},world:'MAIN',func:()=>window.__SimanNetworkV155?.snapshot()?.templates?.length||0});
  if(!snap[0]?.result){
   await debug('REFRESH',PROVIDERS[p]+' 목록 요청 수집을 위해 탭 새로고침', 'INFO',p);
   await chrome.tabs.reload(tab.id);await waitTab(tab.id);ping=await installBridge(tab.id);
  }
 }
 const live=await probeVersion(tab.id);
 if(!live?.ok)throw Error('수집기 자동 재연결 실패');
 return {tab,ping:live};
}
async function runSync(p){
 if(!BASE[p]){toast('지원하지 않는 서비스입니다.');return {ok:false,error:'unsupported provider'}}
 const startedAt=Date.now();
 await debug('INIT',PROVIDERS[p]+' 수집 준비','INFO',p);
 try{
  const {tab,ping}=await prepareConnection(p);
  if(ping.running){await debug('SKIP',PROVIDERS[p]+' 이미 실행 중','INFO',p);return {ok:false,already:true}}
  const previous=await SimanStore.getStatus();
  if(previous.last[p]?.retryAt>Date.now()){
   const reason='서버 요청 제한: '+timeLabel(previous.last[p].retryAt);toast(PROVIDERS[p]+' '+reason);
   await debug('RATE_LIMIT',reason,'WARN',p);return {ok:false,error:reason}
  }
  // Reset an orphaned active flag, without clearing the archive.
  await SimanStore.begin(p);
  const r=await chrome.scripting.executeScript({target:{tabId:tab.id},world:'MAIN',func:()=>window.__SimanRunnerV155?.start()||{ok:false}});
  if(!r[0]?.result?.ok)throw Error('수집기 시작 명령에 응답 없음');
  await debug('START',PROVIDERS[p]+' 수집기 시작: tabId='+tab.id,'INFO',p);
  toast(PROVIDERS[p]+' 수집을 시작했습니다.');
  return {ok:true,startedAt};
 }catch(e){
  const error='수집 시작 실패: '+e.message;
  await debug('ERROR',error,'ERROR',p);
  await SimanStore.updateEvent({provider:p,kind:'ERROR',text:error});toast(PROVIDERS[p]+': '+e.message);
  return {ok:false,error};
 }finally{await renderStatus()}
}
for(const b of document.querySelectorAll('.sync'))b.onclick=async()=>{if(batchRunning){toast('일괄수집이 진행 중입니다.');return}b.disabled=true;try{await runSync(b.dataset.p)}finally{b.disabled=false}};
for(const b of document.querySelectorAll('.stopSync'))b.onclick=async()=>{const p=b.dataset.p;try{const all=await chrome.tabs.query({}),t=all.find(x=>tabMatches(p,x.url));if(!t){toast('열린 '+PROVIDERS[p]+' 탭이 없습니다.');return}const result=await chrome.scripting.executeScript({target:{tabId:t.id},world:'MAIN',func:()=>window.__SimanRunnerV155?.stop()||{ok:false}});toast(result[0]?.result?.ok?'수집 중지 요청을 전달했습니다. 완료된 원문은 유지됩니다.':'실행 중인 수집을 찾지 못했습니다.')}catch(e){toast('수집 중지 실패: '+e.message)}};
async function stopRunner(p){
 try{const all=await chrome.tabs.query({}),tab=all.find(x=>tabMatches(p,x.url));if(!tab)return false;
  const r=await chrome.scripting.executeScript({target:{tabId:tab.id},world:'MAIN',func:()=>window.__SimanRunnerV155?.stop()||{ok:false}});
  return !!r[0]?.result?.ok;
 }catch(e){await debug('STOP_ERROR',e.message,'WARN',p);return false}
}
function batchLabel(text){$('batchProgress').textContent=text}
async function awaitSyncResult(p,startedAt){
 const t0=Date.now();let lastUpdate=Date.now();
 while(!batchStop){
  const state=await SimanStore.getStatus();
  const done=state.last[p];
  if(!state.active[p]&&Number(done?.finishedAt||0)>=startedAt)return {ok:!!done.complete,summary:done};
  if(Date.now()-lastUpdate>5000){
    const s=state.active[p];batchLabel('진행 중: '+PROVIDERS[p]+'\n'+(s?.stage||'서버 응답 대기')+' · '+(s?.done||0)+' / '+(s?.total||'조회 중')+'건\n완료한 서비스: '+(batchCompleted.join(', ')||'없음'));
    lastUpdate=Date.now();
  }
  // If a refreshed/closed tab loses its runner, avoid an eternal 'connecting' state.
  const active=state.active?.[p];const heartbeatAge=Date.now()-Date.parse(active?.updatedAt||0);
  if(heartbeatAge>95000 && !(active?.retryAt>Date.now())){
   const tabs=await chrome.tabs.query({}),tab=tabs.find(x=>tabMatches(p,x.url));
   const live=tab?await probeVersion(tab.id):null;
   if(!live?.running){
    const error='진행 상태가 95초 이상 갱신되지 않고 수집기가 중지되었습니다.';
    await debug('DISCONNECT',error,'ERROR',p);
    await SimanStore.updateEvent({provider:p,kind:'ERROR',text:error});return {ok:false,error,disconnected:true};
   }
  }
  await sleep(750);
 }
 return {ok:false,stopped:true};
}
async function runBatch(){
 if(batchRunning)return;
 batchRunning=true;batchStop=false;batchCompleted=[];
 $('bulkStart').disabled=true;$('bulkStop').disabled=false;
 await debug('BULK_START','전체 일괄수집 시작 (ChatLLM → Claude → ChatGPT)');
 let failures=[];
 try{for(const p of BULK){
  if(batchStop)break;
  batchCurrent=p;batchLabel('일괄수집 중 · '+PROVIDERS[p]+' 준비 중...\n이전 완료: '+(batchCompleted.join(', ')||'없음'));
  let done=null,startError='';
  // One bounded recovery on an orphaned page; completed IDs stay in chrome.storage.local.
  for(let attempt=0;attempt<2&&!batchStop;attempt++){
   const r=await runSync(p);
   if(!r.ok){startError=r.error||'이미 실행 중';break}
   done=await awaitSyncResult(p,r.startedAt);
   if(!done.disconnected||attempt!==0)break;
   await debug('AUTO_RECOVER',PROVIDERS[p]+' 수집 페이지 연결 상실 · 기존 저장 기록 유지 · 자동 재연결 1회','WARN',p);
   batchLabel(PROVIDERS[p]+' 수집기 연결 복구 중 · 이미 저장된 원문 유지');
   await sleep(1800);
  }
  if(batchStop)break;
  if(startError)failures.push(PROVIDERS[p]+': '+startError);
  else if(done?.ok)batchCompleted.push(PROVIDERS[p]);
  else failures.push(PROVIDERS[p]+': '+(done?.summary?.error||done?.error||(done?.summary?.paused?'서버 제한 대기':'미완료')));
 }
 const message=(batchStop?'사용자 중지':'일괄수집 단계 종료')+'\n완료: '+(batchCompleted.join(', ')||'없음')+'\n미완료: '+(failures.join(' / ')||'없음')+'\n자세한 내용은 「진단 로그 TXT 저장」에서 확인할 수 있습니다.';
 batchLabel(message);await debug('BULK_END',message,batchStop?'WARN':'INFO');
 }catch(e){batchLabel('일괄수집 중단: '+e.message);await debug('BULK_EXCEPTION',e.message,'ERROR')}
 finally{batchRunning=false;batchCurrent='';$('bulkStart').disabled=false;$('bulkStop').disabled=true;await loadRecords();await renderStatus()}
}
$('bulkStart').onclick=runBatch;
$('bulkStop').onclick=async()=>{if(!batchRunning)return;batchStop=true;await debug('BULK_STOP','일괄수집 중지 요청');if(batchCurrent)await stopRunner(batchCurrent);batchLabel('중지 요청 완료 · 이미 저장된 원문은 유지됩니다.')};
$('repair').onclick=async()=>{
 let ok=[],failed=[];
 for(const p of Object.keys(BASE)){
  const list=await chrome.tabs.query({}),existing=list.find(t=>tabMatches(p,t.url));
  if(!existing)continue;
  try{await installBridge(existing.id);ok.push(PROVIDERS[p])}
  catch(e){
   try{await chrome.tabs.reload(existing.id);await waitTab(existing.id);await installBridge(existing.id);ok.push(PROVIDERS[p]+'(재연결)')}
   catch(err){failed.push(PROVIDERS[p]+': '+err.message)}
  }
 }
 // Previously the repair button ignored all visit-only providers.
 for(const p of ['gemini','deepseek','grok']){
  const list=await chrome.tabs.query({}),existing=list.find(t=>tabMatches(p,t.url));
  if(!existing)continue;
  try{
   await chrome.tabs.reload(existing.id);await waitTab(existing.id);
   let result=await chrome.scripting.executeScript({target:{tabId:existing.id},world:'ISOLATED',func:()=>!!globalThis.__simanContentV155});
   if(!result?.[0]?.result){
    await chrome.scripting.executeScript({target:{tabId:existing.id},world:'ISOLATED',files:['core.js','store.js','content.js']});
    await sleep(450);
    result=await chrome.scripting.executeScript({target:{tabId:existing.id},world:'ISOLATED',func:()=>!!globalThis.__simanContentV155});
   }
   if(!result?.[0]?.result)throw Error('방문 수집 스크립트 초기화 실패');
   ok.push(PROVIDERS[p]);
  }catch(e){failed.push(PROVIDERS[p]+': '+e.message)}
 }
 await debug('REPAIR','연결 복구 성공 '+ok.length+'개 · 실패 '+failed.length+'개',failed.length?'WARN':'INFO');
 toast('다시 연결: '+(ok.join(', ')||'열린 지원 사이트 없음')+(failed.length?' · 오류 '+failed.join('; '):''));
};
async function gotoOriginal(){if(!record)return;let url=SimanCore.sourceUrl(record.provider,record.id,record.url);
 if(url){try{let t=await chrome.tabs.create({url,active:true});if(lastQ){try{await waitTab(t.id);await chrome.scripting.executeScript({target:{tabId:t.id},func:(q)=>{const els=[...document.querySelectorAll('main [data-message-author-role],main [data-testid*="message"],main p,main article')];let e=els.find(x=>x.textContent?.toLocaleLowerCase().includes(q.toLocaleLowerCase()));if(e){e.scrollIntoView({block:'center'});e.style.outline='3px solid #658bff'}},args:[lastQ]})}catch{}}return}catch(e){toast('원본 주소 열기 실패: '+e.message);return}}
 if(record.provider==='chatllm'){
  try{const t=await tabFor('chatllm');await chrome.tabs.update(t.id,{active:true});const results=await chrome.scripting.executeScript({target:{tabId:t.id},func:async(targetId,title,project)=>{
   function candidates(){return [...document.querySelectorAll('a[href],button,[role="button"],[data-conversation-id],[data-deployment-conversation-id]')].filter(el=>!el.closest('main article,[role="dialog"]'))}
   function locate(){const entries=candidates();const idmatches=entries.filter(el=>[el.dataset.conversationId,el.dataset.deploymentConversationId].includes(targetId));if(idmatches.length)return idmatches[0];const matches=entries.filter(el=>(el.getAttribute('title')||el.innerText||el.textContent||'').trim()===title);return matches.length===1?matches[0]:null}
   async function explore(){let e=locate();if(e)return e;const scrollables=[...document.querySelectorAll('aside,nav,[role="navigation"],div')].filter(el=>{let css=getComputedStyle(el);return ['auto','scroll'].includes(css.overflowY)&&el.scrollHeight>el.clientHeight+70&&el.clientWidth>120}).slice(0,12);
    for(const s of scrollables){let old=s.scrollTop;s.scrollTop=0;for(let i=0;i<100;i++){e=locate();if(e)return e;const before=s.scrollTop;s.scrollTop+=Math.max(s.clientHeight*.9,200);await new Promise(r=>setTimeout(r,75));if(s.scrollTop<=before+2)break}s.scrollTop=old}return null}
   let found=await explore();if(!found&&project){const ps=candidates().filter(el=>(el.innerText||el.textContent||'').trim()===project);if(ps.length===1){ps[0].click();await new Promise(r=>setTimeout(r,550));found=await explore()}}
   if(found){found.scrollIntoView({block:'center'});found.click();return true}return false
  },args:[record.id,record.title,record.projectName||'']});if(results[0]?.result){toast('ChatLLM 원본 대화를 열었습니다.');return}toast('원본 세션을 현재 목록에서 찾지 못했습니다. 심안에서 원문 복사는 가능합니다.');return
  }catch(e){toast('원본 탐색 실패: '+e.message);return}
 }
 toast('이 대화의 검증된 원본 이동 주소가 없습니다.');}
$('openOriginal').onclick=gotoOriginal;
$('query').addEventListener('input',()=>{clearTimeout(refreshTimer);refreshTimer=setTimeout(doSearch,90)});
$('search').onclick=doSearch;$('provider').onchange=doSearch;$('role').onchange=doSearch;
async function importRecords(records){let n=0;for(const r of records){if(!SimanStore.valid(r))continue;n++;await SimanStore.save(r)}return n}
$('importFile').onchange=async e=>{let count=0,errors=[];for(const f of e.target.files){try{let arr=[];if(/\.zip$/i.test(f.name)){const zip=await JSZip.loadAsync(f);for(const z of Object.values(zip.files)){if(z.dir||!/(?:conversation|chat|history|siman).*\.json$/i.test(z.name)||/node_modules|__MACOSX/i.test(z.name))continue;let raw=JSON.parse(await z.async('string'));arr.push(...(Array.isArray(raw?.simanRecords)?raw.simanRecords:SimanCore.parseImport(raw,z.name)))}}
 else{const raw=JSON.parse(await f.text());arr=Array.isArray(raw?.simanRecords)?raw.simanRecords:SimanCore.parseImport(raw,f.name)}count+=await importRecords(arr)}catch(err){errors.push(f.name+': '+err.message)}}await loadRecords();toast('원문 가져오기: '+count+'개'+(errors.length?' / 오류 '+errors.slice(0,2).join('; '):''));e.target.value=''};
$('export').onclick=async()=>{try{const data=JSON.stringify({format:'siman-archive-1',exportedAt:new Date().toISOString(),simanRecords:[...cache.values()]});const u=URL.createObjectURL(new Blob([data],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download='Siman_Archive_'+new Date().toISOString().slice(0,10)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),30000);toast('로컬 원문 백업 완료')}catch(e){toast('백업 실패: '+e.message)}};
$('clear').onclick=async()=>{if(!confirm('심안에 저장된 로컬 색인을 삭제할까요? 원래 채팅은 삭제되지 않습니다.'))return;await SimanStore.clear();await loadRecords();toast('로컬 색인 삭제 완료')};
chrome.storage.onChanged.addListener((changes,area)=>{if(area!=='local')return;let changed=false;for(const [k,v] of Object.entries(changes))if(k.startsWith(SimanStore.PREFIX)){const r=v.newValue;if(r)cache.set(r.key,r);else cache.delete(k.slice(SimanStore.PREFIX.length));changed=true}
 if(changed){renderStats().catch(()=>{});if($('query').value.trim()){clearTimeout(window.__simanReloadTimer);window.__simanReloadTimer=setTimeout(doSearch,250)}}if(Object.keys(changes).some(k=>k.startsWith(SimanStore.CATALOG)))renderStats().catch(()=>{});if(changes[SimanStore.META])renderStatus()});
window.addEventListener('error',e=>{debug('UI_ERROR',String(e.message||'알 수 없는 UI 오류'),'ERROR')});
window.addEventListener('unhandledrejection',e=>{debug('UNHANDLED_PROMISE',String(e.reason?.message||e.reason||'비동기 오류'),'ERROR')});
debug('UI_BOOT','심안 v1.5.6 검색 화면 시작');
setInterval(()=>{if(!chrome.runtime?.id){batchLabel('확장프로그램이 갱신되었습니다. 연결을 복구하기 위해 검색 화면을 다시 엽니다.');location.reload();return}renderStatus()},3000);(async()=>{try{await SimanStore.migrate();await loadRecords();await renderStatus()}catch(e){toast('초기 기록 읽기 실패: '+e.message);$('progress').textContent=e.message}})();
})();
