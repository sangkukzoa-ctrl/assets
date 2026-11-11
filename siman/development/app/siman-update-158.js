/* Newly named v1.5.8 bootstrap: previous Chrome cache has no such extension file. */
(()=>{'use strict';
const url=new URL(location.href);
const version=String(url.searchParams.get('version')||'');
const token=String(url.searchParams.get('token')||'');
const port=Number(url.searchParams.get('port')||0);
if(version!=='1.5.8'||!/^[a-f0-9]{32}$/i.test(token)||
 !Number.isInteger(port)||port<1024||port>65535)return;
if(!chrome.runtime?.id||!chrome.storage?.local)return;
const state={port,token,version,at:Date.now()};
chrome.storage.local.set({'siman:updater:pending':state})
 .then(()=>{
   history.replaceState(null,'',location.pathname);
   const loaded=chrome.runtime.getManifest().version;
   if(loaded===version)chrome.runtime.sendMessage({type:'SIMAN_APPLY_PENDING_UPDATE'},()=>void chrome.runtime.lastError);
   else chrome.runtime.reload(); // Full unpacked extension refresh including manifest.
 })
 .catch(e=>{
   const line=document.getElementById('status');
   if(line)line.textContent='심안 자동 적용 확인 실패: '+String(e?.message||e);
 });
})();
