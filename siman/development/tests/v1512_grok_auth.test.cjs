'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const app=n=>fs.readFileSync(path.resolve(__dirname,'../app',n),'utf8');
const origin='https://grok.com';
async function scenario(httpStatus){
 const events=[],messages=[],requests=[];
 const ctx={URL,URLSearchParams,Headers,AbortController,Date,Map,Set,Object,Promise,JSON,Math,Number,String,Boolean,Error,RegExp,Array,console,
  location:{href:origin+'/',origin,hostname:'grok.com',pathname:'/'},
  setTimeout,clearTimeout,setInterval:()=>0,clearInterval:()=>{}};
 ctx.window=ctx;ctx.globalThis=ctx;
 ctx.addEventListener=(kind,cb)=>{if(kind==='message')events.push(cb)};
 ctx.postMessage=m=>{messages.push(m);if(m.kind==='BRIDGE'){
  queueMicrotask(()=>events.forEach(cb=>cb({source:vm.runInContext('window',ctx),origin,data:{kind:'BRIDGE_REPLY',tag:m.tag,seqId:m.seqId,ok:true,completeIds:[],storageReady:true}})))}
 };
 ctx.fetch=async (url,opts)=>{
  const u=new URL(url);assert.equal(u.origin,origin);
  requests.push({path:u.pathname,status:httpStatus});
  return {ok:httpStatus===200,status:httpStatus,headers:new Headers({'Content-Type':'application/json'}),
   json:async()=>({conversations:[],nextPageToken:''})};
 };
 vm.createContext(ctx);vm.runInContext('window=globalThis',ctx);
 for(const f of ['core.js','grok-web.js','page.js'])vm.runInContext(app(f),ctx);
 ctx.__SimanRunnerV155.start();
 for(let i=0;i<70&&!messages.some(m=>m.kind==='DONE'||m.kind==='ERROR');i++)await new Promise(resolve=>setTimeout(resolve,15));
 const done=messages.find(m=>m.kind==='DONE'),err=messages.find(m=>m.kind==='ERROR');
 assert(!err,'Grok 401/empty is handled without a misleading global crash');
 assert(done,'status must finish promptly');
 assert(requests.some(r=>r.path.includes('/rest/app-chat/conversations')));
 if(httpStatus===401){
  assert.equal(done.result.authRequired,true);
  assert.equal(done.result.complete,false);
  assert.equal(done.result.checked,false);
  assert(messages.some(m=>m.kind==='TRACE'&&m.stage==='GROK_AUTH'));
  assert(!messages.some(m=>m.kind==='BRIDGE'&&m.action==='CATALOG'),'401 must not create a fake empty account index');
 }else{
  assert.equal(done.result.found,0);
  assert.equal(done.result.complete,true);
  assert.equal(done.result.listComplete,true);
  assert(!done.result.authRequired);
 }
}
(async()=>{await scenario(401);await scenario(200);console.log('PASS Grok unauthenticated HTTP 401 is distinct from authenticated genuinely-empty 0-chat account');})().catch(e=>{console.error(e);process.exitCode=1});
