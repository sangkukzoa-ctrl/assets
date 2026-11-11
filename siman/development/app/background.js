/* Siman v1.5.8 — one-shot self-update handshake. Never touches chat archives. */
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
async function applyPendingUpdate() {
 const state=(await chrome.storage.local.get(KEY))[KEY];
 if(!validRequest(state))return {ok:false,reason:'no-valid-pending-update'};
 // Remove the one-time updater marker before reporting. The conversation store is untouched.
 await chrome.storage.local.remove(KEY);
 const result=await refreshChatTabs();
 const url='http://127.0.0.1:'+state.port+'/complete?token='+
  encodeURIComponent(state.token)+'&v='+encodeURIComponent(state.version)+
  '&refreshed='+result.refreshed+'&drafts='+result.skippedDraft+'&failed='+result.failed;
 // A top-level navigation does not need local-network fetch host permissions.
 // Keep the receipt tab inactive and close it after the local installer receives the ACK.
 try{
  const tab=await chrome.tabs.create({url,active:false});
  if(tab?.id)setTimeout(()=>{chrome.tabs.remove(tab.id).catch(()=>{});},1700);
  return {ok:true,...result};
 }catch(e){return {ok:false,reason:'ack-open-failed'};}
}
chrome.runtime.onInstalled.addListener(details=>{
 if(details.reason==='update'||details.reason==='install')applyPendingUpdate().catch(()=>{});
});
chrome.runtime.onMessage.addListener((message,sender,reply)=>{
 if(message?.type!=='SIMAN_APPLY_PENDING_UPDATE')return;
 applyPendingUpdate().then(reply).catch(e=>reply({ok:false,reason:String(e?.message||e)}));
 return true;
});
