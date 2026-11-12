/* Test-only Chrome target probe; never print update tokens or page message content. */
const http=require('node:http');
const port=Number(process.argv[2]);
if(!Number.isInteger(port)||port<1||port>65535)process.exit(2);
function getJson(path){return new Promise((resolve,reject)=>http.get({host:'127.0.0.1',port,path,timeout:5000},r=>{let s='';r.on('data',c=>s+=c);r.on('end',()=>{try{resolve(JSON.parse(s))}catch(e){reject(e)}})}).on('error',reject))}
(async()=>{
 let targets=await getJson('/json/list');
 const target=targets.find(t=>String(t.url||'').includes('siman-update-158.html'));
 if(!target){console.log('PROBE: no Siman extension-owned bootstrap page target');return}
 const ws=new WebSocket(target.webSocketDebuggerUrl);
 const timeout=setTimeout(()=>{console.log('PROBE: Chrome WebSocket timeout');process.exit(0)},4500);
 ws.onopen=()=>ws.send(JSON.stringify({id:1,method:'Runtime.evaluate',
   params:{expression:"JSON.stringify({title:document.title.split('?')[0],ready:document.readyState,body:(document.body&&document.body.innerText||'').slice(0,180),scripts:[...document.scripts].map(x=>x.getAttribute('src')||'inline').slice(0,6),hasRuntime:!!(globalThis.chrome&&chrome.runtime&&chrome.runtime.id),isError:!!document.querySelector('html[crashpage]')})",
      returnByValue:true}}));
 ws.onmessage=m=>{try{let r=JSON.parse(m.data);if(r.id===1){
   const text=r.result?.result?.value||r.error?.message||'(no result)';
   console.log('PROBE: extension tab document state '+text);clearTimeout(timeout);ws.close();}}catch(e){console.log('PROBE: '+e.message)}};
 ws.onerror=e=>{console.log('PROBE: websocket unavailable');clearTimeout(timeout)};
})().catch(e=>{console.log('PROBE: '+String(e.message||e))});
