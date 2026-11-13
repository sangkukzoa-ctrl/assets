/* Siman v1.5.13 — one-shot self-update handshake. Never touches chat archives. */
'use strict';
const KEY='siman:updater:pending';
const PROVIDERS=['https://apps.abacus.ai/*','https://*.abacus.ai/*',
  'https://chatgpt.com/*','https://chat.openai.com/*',
  'https://claude.ai/*','https://*.claude.ai/*',
  'https://gemini.google.com/*','https://chat.deepseek.com/*','https://grok.com/*'];

function validRequest(p) {
 return !!p && p.version===chrome.runtime.getManifest().version &&
  Number.isInteger(p.port) && p.port>=1024 && p.port<=65535 &&
  /^[a-f0-9]{32}$/i.test(String(p.token||'')) &&
  Date.now()-Number(p.at||0)<120000 && Date.now()>=Number(p.at||0)-10000;
}
async function refreshChatTabs() {
 let refreshed=0,skippedDraft=0,failed=0;
 let tabs=await chrome.tabs.query({url:PROVIDERS});
 for(const tab of tabs){
  if(!tab.id)continue;
  try{
   // Do not erase a message the user is still composing.
   let result=await chrome.scripting.executeScript({
    target:{tabId:tab.id},func:()=>{
     const nodes=[...document.querySelectorAll('textarea,[contenteditable="true"],[role="textbox"]')];
     return nodes.some(el=>{
      if(!(el.getClientRects().length))return false;
      const value=('value' in el?el.value:el.innerText)||'';
      return String(value).trim().length>0;
     });
    }
   });
   if(result[0]?.result){skippedDraft++;continue;}
   await chrome.tabs.reload(tab.id);
   refreshed++;
  }catch(e){failed++;}
 }
 return {refreshed,skippedDraft,failed};
}
// v1.5.13: the installer writes a one-time request into the SAME unpacked
// extension directory before invoking the Chrome extensions-manager Reload.
// Chrome itself loads this service worker after Reload; no external navigation
// to chrome-extension:// (blocked by Chrome in real user profile) is necessary.
const DIRECTIVE='siman-updater-request.json';
let updateFlight=null;
async function pendingFromDirectory(){
 const url=chrome.runtime.getURL(DIRECTIVE);
 let r;
 try {r=await fetch(url,{cache:'no-store'});}catch{return false}
 if(!r?.ok)return false;
 let candidate;
 try{candidate=await r.json()}catch{return false}
 if(!validRequest(candidate)||candidate.extensionId!==chrome.runtime.id)return false;
 await chrome.storage.local.set({[KEY]:{
  version:candidate.version,port:candidate.port,token:candidate.token,at:candidate.at
 }});
 return true;
}
async function applyPendingUpdate() {
 let state=(await chrome.storage.local.get(KEY))[KEY];
 if(!validRequest(state)){
  const accepted=await pendingFromDirectory();
  if(!accepted)return {ok:false,reason:'no-valid-pending-update'};
  state=(await chrome.storage.local.get(KEY))[KEY];
 }
 if(!validRequest(state))return {ok:false,reason:'expired-update-request'};
 // Remove the single-use marker before reporting. User conversations untouched.
 await chrome.storage.local.remove(KEY);
 const result=await refreshChatTabs();
 // Report COUNT only: never send any titles, content, keys or authentication.
 let recordCount=-1;
 try{
  const keys=await chrome.storage.local.getKeys();
  recordCount=keys.filter(k=>k.startsWith('siman:v11:record:')).length;
 }catch{}
 const url='http://127.0.0.1:'+state.port+'/complete?token='+
  encodeURIComponent(state.token)+'&v='+encodeURIComponent(state.version)+
  '&id='+encodeURIComponent(chrome.runtime.id)+
  '&refreshed='+result.refreshed+'&drafts='+result.skippedDraft+
  '&failed='+result.failed+'&records='+recordCount;
 // Local-only receipt uses an ordinary browser navigation. No extra permissions.
 try{
  const tab=await chrome.tabs.create({url,active:false});
  if(tab?.id)setTimeout(()=>{chrome.tabs.remove(tab.id).catch(()=>{});},3500);
  return {ok:true,...result,recordCount};
 }catch(e){return {ok:false,reason:'local-ack-tab-failed'};}
}
function completeOnce(){
 if(updateFlight)return updateFlight;
 updateFlight=applyPendingUpdate().catch(e=>({ok:false,reason:String(e?.name||'Error')}))
  .finally(()=>{updateFlight=null});
 return updateFlight;
}
chrome.runtime.onInstalled.addListener(details=>{
 if(details.reason==='update'||details.reason==='install')completeOnce().catch(()=>{});
});
chrome.runtime.onStartup.addListener(()=>{completeOnce().catch(()=>{});});
chrome.runtime.onMessage.addListener((message,sender,reply)=>{
 if(message?.type!=='SIMAN_APPLY_PENDING_UPDATE')return;
 completeOnce().then(reply).catch(e=>reply({ok:false,reason:String(e?.name||'Error')}));
 return true;
});
// Loading this worker immediately after pressing extension Reload must also ACK
// even when Chrome does not issue a manifest 'update' event for unpacked builds.
completeOnce().catch(()=>{});
