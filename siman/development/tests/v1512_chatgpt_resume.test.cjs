'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=n=>fs.readFileSync(path.join(__dirname,'../app',n),'utf8');
const origin='https://chatgpt.com',doneId='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',todoId='bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb';
const msgs=[],listeners=[],requests=[],saved=[];
const fixture={id:todoId,title:'ChatGPT 미수집 대화',mapping:{
 first:{message:{id:'user-1',create_time:1,author:{role:'user'},content:{parts:['미수집 기록 테스트']}}},
 second:{message:{id:'assistant-2',create_time:2,author:{role:'assistant'},content:{parts:['자동 재개 수집 성공']}}}
}};
let now=1794490000000;
class Clock extends Date{static now(){now+=10000;return now}}
const ctx={URL,URLSearchParams,Headers,AbortController,Map,Set,Object,Promise,JSON,Math,Number,String,Boolean,Error,RegExp,Array,console,Date:Clock,
 location:{href:origin+'/',origin,hostname:'chatgpt.com',pathname:'/'},setTimeout,clearTimeout,setInterval:()=>0,clearInterval:()=>{}};
ctx.window=ctx;ctx.globalThis=ctx;
ctx.addEventListener=(type,cb)=>{if(type==='message')listeners.push(cb)};
ctx.postMessage=m=>{
 msgs.push(m);if(m.kind!=='BRIDGE')return;
 const reply={tag:m.tag,kind:'BRIDGE_REPLY',seqId:m.seqId,ok:true,storageReady:true};
 if(m.action==='CATALOG_GET')reply.entries=[{id:doneId,title:'기존 완료'},{id:todoId,title:'미수집 대상'}];
 if(m.action==='LOOKUP')reply.completeIds=[doneId];
 if(m.action==='SAVE')saved.push(m.record);
 queueMicrotask(()=>{for(const cb of listeners)cb({source:vm.runInContext('window',ctx),origin,data:reply})});
};
ctx.fetch=async(url,options={})=>{
 const u=new URL(url);assert.equal(u.origin,origin);
 requests.push(u.pathname+u.search);
 if(u.pathname==='/api/auth/session')return {ok:true,status:200,headers:new Headers(),json:async()=>({accessToken:'private-token'})};
 if(u.pathname==='/backend-api/conversation/'+todoId){
  assert.equal(options.headers.Authorization,'Bearer private-token');
  return {ok:true,status:200,headers:new Headers(),json:async()=>fixture};
 }
 throw Error('Automatic resume must not refetch ChatGPT session listing or already-complete transcript: '+u.pathname);
};
vm.createContext(ctx);vm.runInContext('window=globalThis',ctx);
vm.runInContext(read('core.js'),ctx);vm.runInContext(read('page.js'),ctx);
ctx.__SimanRunnerV155.start({resumeOnly:true});
(async()=>{
 for(let i=0;i<100&&!msgs.some(x=>x.kind==='DONE'||x.kind==='ERROR');i++)await new Promise(r=>setTimeout(r,20));
 const error=msgs.find(x=>x.kind==='ERROR');if(error)console.error(error);
 assert(!error);
 const d=msgs.find(x=>x.kind==='DONE');assert(d,'ChatGPT resumed scan must finish');
 assert.equal(d.result.found,2);assert.equal(d.result.skipped,1);assert.equal(d.result.read,1);
 assert.equal(d.result.usedLocalCatalog,true);
 assert(!requests.some(x=>x.startsWith('/backend-api/conversations?')));
 assert(!requests.some(x=>x.includes(doneId)));
 assert.equal(saved.length,1);
 assert.equal(saved[0].messages.length,2);
 assert(!JSON.stringify(msgs).includes('private-token'));
 console.log('PASS ChatGPT 429 auto-resume uses local catalog and fetches only remaining original transcript, no repeat list calls');
})().catch(e=>{console.error(e);process.exitCode=1});
