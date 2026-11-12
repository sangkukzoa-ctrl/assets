/* Isolation bridge: pass only parsed user-visible conversations to local extension storage. */
(()=>{'use strict';
const TAG='siman-heart-v155';
let bootAttempts=0;
function boot(){
 if(globalThis.__simanContentV155)return;
 // Some Chrome navigations execute the isolated script while its dependencies are
 // temporarily unavailable. Retrying is safer than a permanent uncaught error.
 if(!globalThis.SimanCore?.providerFromUrl){
  if(++bootAttempts<=20)setTimeout(boot,450);
  else console.warn('[Siman] Core script did not initialize. Use the connection repair action.');
  return;
 }
 const provider=globalThis.SimanCore.providerFromUrl(location.href);
 if(!provider)return;
 if(!globalThis.SimanStore?.getStatus||!globalThis.chrome?.runtime?.id){
  if(++bootAttempts<=20)setTimeout(boot,450);
  else console.warn('[Siman] The page archive bridge could not initialize. Open the extension and use connection repair.');
  return;
 }
 globalThis.__simanContentV155=true;

let statusQueue=Promise.resolve();const storeEvent=(kind,d)=>{statusQueue=statusQueue.catch(()=>{}).then(()=>kind==='TRACE'?SimanStore.appendDebug({provider:d.provider||provider,level:d.level||'TRACE',stage:d.stage||'',message:d.text||''}):SimanStore.updateEvent({kind,provider:d.provider||provider,stage:d.stage,done:d.done,total:d.total,read:d.read,skipped:d.skipped,failed:d.failed,remaining:d.remaining,retryAt:d.retryAt,details:d.details,text:d.text,result:d.result}));return statusQueue};
window.addEventListener('message',ev=>{void (async()=>{if(ev.source!==window||ev.origin!==location.origin||ev.data?.tag!==TAG)return;const d=ev.data;
 if(d.kind==='BRIDGE'){
  let out={tag:TAG,kind:'BRIDGE_REPLY',seqId:d.seqId,ok:false};
  try{const p=d.providerName||provider;
   if(d.action==='TEST'){await SimanStore.getStatus();await SimanStore.appendDebug({provider,level:'INFO',stage:'BRIDGE_TEST',message:'로컬 저장소 읽기·쓰기 검사 성공'});out.ok=true;out.storageReady=true}
   else if(d.action==='SAVE'){await SimanStore.save(d.record);out.ok=true}
   else if(d.action==='CATALOG'){await SimanStore.discover(p,d.entries||[]);out.ok=true}
   else if(d.action==='LOOKUP'){out.completeIds=await SimanStore.completeIds(p,d.ids||[]);out.ok=true}
   else if(d.action==='MARK'){await SimanStore.mark(p,d.id,d.status,d.reason);out.ok=true}
   else if(d.action==='MARK_MANY'){await SimanStore.markMany(p,d.ids||[],d.status);out.ok=true}
  }catch(e){out.error=e.message;await storeEvent('WARN',{provider,text:'저장소 작업 실패: '+e.message}).catch(()=>{})}
  window.postMessage(out,location.origin);
 }else if(['PROGRESS','DONE','WARN','ERROR','TRACE'].includes(d.kind))await storeEvent(d.kind,d);
 })().catch(e=>{
  // Chrome invalidates old content-script contexts after unpacked extension reload.
  // Expected late events must not become unhandled rejection cards in chrome://extensions.
  if(!globalThis.chrome?.runtime?.id)return;
  console.warn('[Siman isolated bridge] ignored stale page event:',String(e?.name||'Error'));
 });
});
const nodeSelectors={
 chatgpt:'[data-testid^="conversation-turn"]',
 claude:'[data-testid="user-message"], [data-testid="assistant-message"], .font-claude-response',
 chatllm:'[data-message-author-role], [data-testid*="message"], .chat-message',
 gemini:'[data-message-author-role], .conversation-container, .query-text, .response-container, [data-testid*="message"], .model-response-text',
 deepseek:'[class*="ds-virtual-list-visible-items"] > *, [data-message-id], [data-message-author-role], .ds-markdown, [class*="UserMessage"]',
 grok:'[data-message-id], [data-testid*="message"], [data-role], [data-message-author-role]'
};
function currentId(){try{let u=new URL(location.href);if(provider==='chatgpt')return (u.pathname.match(/\/c\/([\w-]+)/)||[])[1]||'';if(provider==='claude')return (u.pathname.match(/\/chat\/([\w-]+)/)||[])[1]||'';if(provider==='chatllm'){for(const k of ['deploymentConversationId','conversationId','chatSessionId']){const id=u.searchParams.get(k);if(id)return id}}if(provider==='gemini')return(u.pathname.match(/\/app\/([\w-]+)/)||[])[1]||'';if(provider==='deepseek')return(u.pathname.match(/^\/a\/[^/]+\/s\/([\w-]+)(?:\/|$)/)||[])[1]||'';if(provider==='grok'){const c=(u.pathname.match(/\/c\/([a-f0-9-]{36})(?:\/|$)/i)||[])[1];if(c)return c;return /^\/project\/[a-f0-9-]{36}(?:\/|$)/i.test(u.pathname)?u.searchParams.get('chat')||'':''}return u.pathname.split('/').filter(Boolean).pop()||''}catch{return ''}}
// DeepSeek uses /a/chat/s/<session-id> and renders only the viewport's mounted messages.
// Cache visited rows across scrolls so a subsequent viewport does not replace the archive.
function deepSeekRows(){
 const list=document.querySelector('[class*="ds-virtual-list--printable"] [class*="ds-virtual-list-visible-items"]')
   ||document.querySelector('[class*="ds-virtual-list-visible-items"]');
 if(list?.children?.length)return [...list.children];
 // Graceful fallback for product UI changes. Sidebars are excluded in capture().
 return [...document.querySelectorAll('[data-message-id], [data-message-author-role], [class*="UserMessage"], .user-message, .ds-markdown')];
}
function deepSeekRole(row){
 const explicit=row.getAttribute?.('data-message-author-role')||row.getAttribute?.('data-role')||'';
 if(explicit)return explicit;
 if(row.matches?.('.ds-markdown')||row.querySelector?.('.ds-markdown,[class*="AssistantMessage"]'))return 'assistant';
 return 'user';
}
function combineDeepSeek(previous,visible){
 const result=(previous||[]).map(m=>({...m}));
 for(const m of visible){
  const exact=result.findIndex(x=>x.role===m.role&&x.text===m.text);
  if(exact>=0)continue;
  // Avoid accumulating each intermediate token while the last assistant answer streams.
  const last=result[result.length-1];
  if(last?.role==='assistant'&&m.role==='assistant'&&last.text.length>20&&m.text.length>20 &&
      (m.text.startsWith(last.text)||last.text.startsWith(m.text))){
    if(m.text.length>=last.text.length)result[result.length-1]={...m};
    continue;
  }
  result.push({...m});
 }
 return result.map((m,index)=>({...m,index}));
}
let lastSig='',captureBusy=false;
let visitHealth={ok:true,provider,version:'1.5.11',stage:'초기화',count:0,at:0};
const visitLogged=new Set(),skipLogged=new Set();
async function noteSkip(stage){
 visitHealth={...visitHealth,stage,at:Date.now()};
 const fingerprint=location.pathname+'|'+stage;
 if(skipLogged.has(fingerprint))return;
 skipLogged.add(fingerprint);
 await SimanStore.appendDebug({provider,level:'INFO',stage:'VISIT_SKIP',message:stage});
}
async function capture(){
 if(captureBusy)return;
 captureBusy=true;
 try{await captureOnce()}
 catch(e){
  visitHealth={...visitHealth,ok:false,stage:'수집 오류',at:Date.now()};
  // Log only the error category, never a conversation title or message text.
  await SimanStore.appendDebug({provider,level:'ERROR',stage:'VISIT_ERROR',message:String(e?.name||'Error')+': '+String(e?.message||'').slice(0,180)}).catch(()=>{});
 }finally{captureBusy=false}
}
async function captureOnce(){
 let id=currentId();
 if(!id||id==='chatllm'||id==='chats'||id==='s'){
  if(['gemini','deepseek','grok'].includes(provider))await noteSkip('대화 URL이 아닌 화면');
  return;
 }
 let nodes=(provider==='deepseek'?deepSeekRows():[...document.querySelectorAll(nodeSelectors[provider]||'')])
  .filter(el=>!el.parentElement?.closest('nav,aside,[role=navigation]'));
 if(!nodes.length||nodes.length>3000){if(['gemini','deepseek','grok'].includes(provider))await noteSkip('메시지 요소 미발견');return;}
 let msgs=[];
 for(const n of nodes){
  if(provider!=='deepseek' && nodes.some(x=>x!==n&&x.contains(n)))continue;
  const role=provider==='deepseek'?deepSeekRole(n):n.getAttribute('data-message-author-role')||n.getAttribute('data-role')||(/user|human|query/.test(n.className?.toString()||'')?'user':'unknown');
  let target=provider==='deepseek'&&role==='assistant'?(n.matches?.('.ds-markdown')?n:n.querySelector?.('.ds-markdown')||n):n;
  const txt=(target?.innerText||target?.textContent||'').trim();if(!txt||txt.length<2)continue;
  msgs.push({index:msgs.length,role,text:txt.slice(0,1000000)});
 }
 if(!msgs.length){if(['gemini','deepseek','grok'].includes(provider))await noteSkip('화면 메시지 텍스트 없음');return;}
 const sig=location.href+'|'+msgs.map(m=>m.role+':'+m.text.length+'_'+m.text.slice(-30)).join('|');
 if(lastSig===sig)return;
 let title=(document.title||'').replace(/\s*[-|]\s*(ChatGPT|Claude|ChatLLM|Gemini|DeepSeek|Grok).*$/i,'').trim();
 if(provider==='deepseek'){
  const link=[...document.querySelectorAll('a[href*="/a/chat/s/"]')].find(a=>(a.getAttribute('href')||'').includes('/s/'+id));
  const proposed=(link?.getAttribute('title')||link?.innerText||'').trim();
  if(proposed)title=proposed.slice(0,200);
  if(!title||title==='DeepSeek')title='DeepSeek 대화 '+id.slice(0,8);
  const old=await SimanStore.one('deepseek:'+id);
  msgs=combineDeepSeek(old?.messages,msgs);
 }
 await SimanStore.save(SimanCore.record(provider,id,title,msgs,{url:location.href,complete:false,source:'visited-dom'}));
 // Commit the signature ONLY after a successful storage write; failed writes must retry.
 lastSig=sig;
 visitHealth={ok:true,provider,version:'1.5.11',stage:'저장 성공',count:msgs.length,at:Date.now()};
 if(['gemini','deepseek','grok'].includes(provider)&&!visitLogged.has(id)){
  visitLogged.add(id);
  await SimanStore.appendDebug({provider,level:'INFO',stage:'VISIT_CAPTURE',message:'방문 대화 원문을 저장했습니다. 화면 메시지 '+msgs.length+'건'});
 }

}
let timer,firstQueuedAt=0;
function schedule(force=false){
 if(force||!firstQueuedAt)firstQueuedAt=Date.now();
 clearTimeout(timer);
 if(force||Date.now()-firstQueuedAt>=4500){
  firstQueuedAt=0;timer=setTimeout(capture,80);
 }else timer=setTimeout(()=>{firstQueuedAt=0;capture()},900);
}
chrome.runtime.onMessage.addListener((d,s,reply)=>{
 if(!d||typeof d!=='object')return;
 if(d.type==='CAPTURE_HEALTH'){reply({...visitHealth,route:currentId()?'conversation':'other'});return}
 if(d.type==='CAPTURE_NOW'){capture().then(()=>reply({...visitHealth,route:currentId()?'conversation':'other'})).catch(e=>reply({ok:false,error:String(e?.name||'Error')}));return true}
 if(d.type==='BEGIN_SYNC'){window.postMessage({tag:TAG,kind:'COMMAND',action:'START'},location.origin);reply({ok:true});return}
 if(d.type==='STOP_SYNC'){window.postMessage({tag:TAG,kind:'COMMAND',action:'STOP'},location.origin);reply({ok:true});return}
 if(d.type==='FIND_TEXT'){let q=String(d.query||'').toLocaleLowerCase(),nodes=[...document.querySelectorAll(nodeSelectors[provider]||'')],t=nodes.find(n=>(n.textContent||'').toLocaleLowerCase().includes(q));if(t){t.scrollIntoView({block:'center',behavior:'smooth'});t.style.outline='3px solid #4c80ff';setTimeout(()=>{t.style.outline=''},6500)}reply({ok:!!t});return}
 if(d.type==='NAV_CHATLLM'){(async()=>{
  if(provider!=='chatllm'){reply({ok:false});return}
  let wanted=String(d.title||'').trim(),pid=String(d.id||'').trim(),project=String(d.projectName||'').trim();
  function nodes(){return [...document.querySelectorAll('a[href],button,[role="button"],[data-conversation-id],[data-deployment-conversation-id]')]
    .filter(el=>!el.closest('[role="dialog"],main article'))}
  function locate(){let entries=nodes();let exact=entries.filter(el=>[el.dataset.conversationId,el.dataset.deploymentConversationId].includes(pid));if(exact.length)return exact[0];
   let matching=entries.filter(el=>(el.getAttribute('title')||el.innerText||el.textContent||'').trim()===wanted);
   return matching.length===1?matching[0]:null}
  async function explore(){let t=locate();if(t)return t;let regions=[...document.querySelectorAll('aside,nav,[role="navigation"],div')]
   .filter(el=>{let st=getComputedStyle(el);return ['auto','scroll'].includes(st.overflowY)&&el.scrollHeight>el.clientHeight+60&&el.clientWidth>110}).slice(0,12);
   for(const el of regions){let previous=el.scrollTop;el.scrollTop=0;for(let i=0;i<140;i++){t=locate();if(t)return t;let prev=el.scrollTop;el.scrollTop+=Math.max(el.clientHeight*.9,240);await new Promise(r=>setTimeout(r,65));if(el.scrollTop<=prev+2)break}el.scrollTop=previous}return null}
  let found=await explore();if(!found&&project){let plist=nodes().filter(e=>(e.innerText||e.textContent||'').trim()===project);if(plist.length===1){plist[0].click();await new Promise(r=>setTimeout(r,700));found=await explore()}}
  if(found){found.scrollIntoView({block:'center'});found.click();reply({ok:true})}else reply({ok:false})
 })().catch(e=>reply({ok:false,error:e.message}));return true}

});
let lastUrl=location.href;
function init(){
 if(!document.body){setTimeout(init,250);return}
 schedule(true);
 new MutationObserver(()=>{
  if(location.href!==lastUrl){lastUrl=location.href;lastSig='';visitHealth={...visitHealth,stage:'대화 이동 감지',at:Date.now()};schedule(true)}
  else schedule();
 }).observe(document.body,{subtree:true,childList:true,characterData:true});
 // A permanently active SPA can mutate more often than the debounce interval.
 // Periodically capture independently so those chats are never starved.
 setInterval(()=>{if(location.href!==lastUrl){lastUrl=location.href;lastSig=''}schedule(true)},12000);
}
globalThis.__SimanVisitHealthV155=()=>({...visitHealth,route:currentId()?'conversation':'other'});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
}
boot();
})();
