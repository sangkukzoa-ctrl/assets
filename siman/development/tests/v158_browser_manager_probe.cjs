/* QA only: inspect Chrome extension manager through CDP.
   No profile edits or buttons pressed; never expose unrelated extension names/tokens. */
'use strict';
const http=require('node:http');
const port=Number(process.argv[2]), extensionId=String(process.argv[3]||'');
if(!Number.isInteger(port)||port<1||port>65535||!/^[a-p]{32}$/.test(extensionId))process.exit(2);
const delay=ms=>new Promise(r=>setTimeout(r,ms));
function get(path){return new Promise((resolve,reject)=>{
 const req=http.get({hostname:'127.0.0.1',port,path,timeout:5000},res=>{
  let raw='';res.on('data',v=>raw+=v);res.on('end',()=>{try{resolve(JSON.parse(raw))}catch(e){reject(e)}});
 });req.on('error',reject);req.on('timeout',()=>req.destroy(Error('CDP timeout')));
});}
async function connect(url){
 const ws=new WebSocket(url);
 await new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>reject(Error('CDP socket timeout')),6000);
  ws.addEventListener('open',()=>{clearTimeout(timer);resolve()},{once:true});
  ws.addEventListener('error',()=>{clearTimeout(timer);reject(Error('CDP socket error'))},{once:true});
 });return ws;
}
let seq=0;
async function cdp(ws,method,params={}){
 const id=++seq;
 return new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>{ws.removeEventListener('message',receive);reject(Error('CDP '+method+' timeout'))},6500);
  function receive(ev){
   let m;try{m=JSON.parse(ev.data)}catch{return}
   if(m.id!==id)return;
   ws.removeEventListener('message',receive);clearTimeout(timer);
   if(m.error)reject(Error(m.error.message));else resolve(m.result||{});
  }
  ws.addEventListener('message',receive);
  ws.send(JSON.stringify({id,method,params}));
 });
}
function inspect(id){
 const manager=document.querySelector('extensions-manager');
 function all(root,selector){const out=[];const seen=new Set();
  function walk(node){if(!node||seen.has(node))return;seen.add(node);
   if(node.querySelectorAll){for(const el of node.querySelectorAll(selector))out.push(el);
    for(const el of node.querySelectorAll('*'))if(el.shadowRoot)walk(el.shadowRoot);}
  }walk(root);return out;
 }
 const items=all(document,'extensions-item');
 const item=items.find(el=>el.data?.id===id);
 const detail=all(document,'extensions-detail-view').find(el=>el.data?.id===id);
 const reload=item?.shadowRoot?.querySelector('#dev-reload-button');
 const dev=all(document,'#devMode, #dev-mode, cr-toggle').map(el=>({id:el.id,checked:el.checked,aria:el.getAttribute('aria-checked')}));
 return JSON.stringify({manager:!!manager,allCards:items.length,found:!!item,
  state:item?.data?.state??null,
  enabled:item?.data?.state==='ENABLED'||item?.data?.state===1,
  inDevMode:manager?.inDevMode??item?.inDevMode??null,
  reloadExists:!!reload,reloadVisible:!!reload&&reload.getClientRects().length>0,
  detailsFound:!!detail,devToggles:dev.slice(0,5)});
}
async function main(){
 const info=await get('/json/version');
 const browser=await connect(info.webSocketDebuggerUrl);
 try{
  await cdp(browser,'Target.createTarget',{url:'chrome://extensions/'});
  await delay(1200);
  const targets=await get('/json/list');
  const tab=targets.find(t=>t.type==='page'&&t.url.startsWith('chrome://extensions/'));
  if(!tab){console.log('MANAGER PROBE: browser did not expose extensions manager page');return}
  const page=await connect(tab.webSocketDebuggerUrl);
  try{
   await cdp(page,'Runtime.enable');
   if(process.argv.includes('--dev-mode')){
     const setter='(()=>{function seek(r){if(!r)return null;const el=r.querySelector?.("#devMode");if(el)return el;for(const n of r.querySelectorAll?.("*")||[]){if(n.shadowRoot){const found=seek(n.shadowRoot);if(found)return found}}return null}const toggle=seek(document);if(!toggle)return "missing";if(!toggle.checked){toggle.click();return "enabled"}return "already-enabled"})()';
     const applied=await cdp(page,'Runtime.evaluate',{expression:setter,returnByValue:true});
     console.log('MANAGER FIXTURE: developer mode '+String(applied.result?.value||'unknown'));
     await delay(700);
   }
   const expr='('+inspect.toString()+')('+JSON.stringify(extensionId)+')';
   const value=await cdp(page,'Runtime.evaluate',{expression:expr,returnByValue:true});
   console.log('MANAGER PROBE: '+String(value.result?.value||value.exceptionDetails?.text||'no page result'));
  }finally{page.close()}
 }finally{browser.close()}
}
main().catch(e=>{console.log('MANAGER PROBE: '+String(e.message||e));process.exitCode=0});
