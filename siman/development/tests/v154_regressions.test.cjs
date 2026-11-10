const assert=require('node:assert/strict'), fs=require('fs'),path=require('path'), vm=require('node:vm');
const folder=path.resolve(__dirname,'..','app');
const code=f=>fs.readFileSync(path.join(folder,f),'utf8');
function coreContext(){const c={console,Date,URL,URLSearchParams,Math,JSON,Set,Map};c.globalThis=c;vm.createContext(c);vm.runInContext(code('core.js'),c);return c;}
(async()=>{
 const ctx=coreContext(); const C=ctx.SimanCore;
 const fixture={result:{deploymentConversationId:'demo-123456',deploymentConversationName:'메시지 이벤트 차이',totalEvents:27,history:[{role:'user',text:'마군 등장'},{role:'assistant',text:'장문인이오'}]}};
 const complete=C.chatllm(fixture);
 assert.equal(complete.messages.length,2);
 assert.equal(complete.complete,true,'Unpaginated ChatLLM detail must not use totalEvents as visible message count');
 assert.equal(complete.expected,2);
 const partial=C.chatllm({result:{...fixture.result,hasMore:true,nextCursor:'cursor-example'}});
 assert.equal(partial.complete,false);
 assert(partial.expected>partial.messages.length);
 const storeContext={console,SimanCore:C,Date,JSON,Map,Set,chrome:{storage:{local:{get:async()=>({}),set:async()=>{},getKeys:async()=>[]}}}};
 storeContext.globalThis=storeContext;vm.createContext(storeContext);vm.runInContext(code('store.js'),storeContext);
 const legacy={...complete,complete:false,expected:27,source:'chatllm'};
 const upgraded=storeContext.SimanStore.merge(legacy,complete);
 assert.equal(upgraded.complete,true,'New unpaginated response must supersede old event-count heuristic');
 assert.equal(upgraded.expected,2);
 console.log('PASS ChatLLM event count vs displayable messages; explicit continuation remains partial; legacy stored partial can upgrade on re-collection');

 // Model a real 429 from the first ChatGPT API call and ensure no further
 // network request is made. Rate limits should be honored, not retried in a hot loop.
 const host='https://chatgpt.com/', origin=new URL(host).origin, events=new Map(),out=[],calls=[];
 const main={URL,URLSearchParams,Headers,AbortController,Map,Set,Object,Promise,JSON,Error,RegExp,Array,Math,Number,String,Boolean,console,Date,
   location:{href:host,origin,hostname:'chatgpt.com',pathname:'/'}};
 main.window=main;main.globalThis=main;
 main.setTimeout=setTimeout;main.clearTimeout=clearTimeout;main.setInterval=setInterval;main.clearInterval=clearInterval;
 main.addEventListener=(name,cb)=>{const handlers=events.get(name)||[];handlers.push(cb);events.set(name,handlers)};
 main.postMessage=d=>{
  if(d.kind==='BRIDGE')queueMicrotask(()=>{
   const reply={tag:d.tag,kind:'BRIDGE_REPLY',seqId:d.seqId,ok:true,storageReady:true,completeIds:[]};
   for(const f of events.get('message')||[])f({source:vm.runInContext('window',main),origin,data:reply});
  });
  else if(['DONE','ERROR','PROGRESS','TRACE'].includes(d.kind))out.push(d);
 };
 main.fetch=async url=>{
  calls.push(new URL(url).pathname);
  return {ok:false,status:429,headers:new Headers({'Retry-After':'60','Content-Type':'application/json'}),json:async()=>({})};
 };
 vm.createContext(main);vm.runInContext('window=globalThis',main);
 vm.runInContext(code('core.js'),main);vm.runInContext(code('page.js'),main);
 assert.equal(main.__SimanRunnerV155.start().ok,true);
 for(let tries=0;tries<200&&!out.some(x=>x.kind==='DONE');tries++)await new Promise(r=>setTimeout(r,1));
 const done=out.find(x=>x.kind==='DONE');
 assert(done,'429 must end the run with a resumable state');
 assert.equal(done.result.paused,true);
 assert.equal(calls.length,1,'429 cannot issue second request in the same run');
 assert(done.result.retryAt>=Date.now()+14*60*1000,'Must provide conservative retry time');
 console.log('PASS ChatGPT first HTTP 429 -> immediate pause, 15-minute minimum cooldown, 1 request only, resumable DONE state');
})();
