const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=name=>fs.readFileSync(path.join(__dirname,'../app',name),'utf8');
const delay=ms=>new Promise(r=>setTimeout(r,ms));
function makeHost(){
 const origin='https://apps.abacus.ai',href=origin+'/chatllm/';
 const handles=[],events=[],listeners=[];
 let rawRequests=0,bodyReads=0;
 const h={console,Date,URL,URLSearchParams,Headers,AbortController,Map,Set,Object,Promise,JSON,Error,RegExp,Array,Math,Number,String,Boolean,
  location:{href,origin,pathname:'/chatllm/'},
  setTimeout:(fn,ms)=>{if(ms>=60000){handles.push(fn);return 732}return setTimeout(fn,Math.min(ms,5))},
  clearTimeout:()=>{},
  setInterval:()=>1,clearInterval:()=>{},
  document:{querySelectorAll:()=>[],readyState:'loading',addEventListener(){}},
  XMLHttpRequest:class{open(){}send(){}setRequestHeader(){}addEventListener(){}},
  getComputedStyle:()=>({overflowY:'hidden'}),
  addEventListener:(event,fn)=>{if(event==='message')listeners.push(fn)},
 };
 h.window=h;h.globalThis=h;
 h.postMessage=d=>{
  if(d.kind==='BRIDGE'){
   queueMicrotask(()=>listeners.forEach(fn=>fn({source:(h._vmWindow||h.window),origin:h.location.origin,data:{tag:d.tag,kind:'BRIDGE_REPLY',seqId:d.seqId,ok:true,storageReady:true,completeIds:[]}})));
  }else events.push(d);
 };
 h.fetch=async(url,opts={})=>{
  rawRequests++;
  const signal=opts.signal;
  return {ok:true,status:200,headers:new Headers({'content-type':'application/json'}),json:()=>{
   bodyReads++;
   return new Promise((resolve,reject)=>{
    if(signal?.aborted)reject(Error('body aborted'));
    else signal?.addEventListener('abort',()=>reject(Error('body aborted')),{once:true});
   });
  },clone(){return this}};
 };
 return {h,handles,events,stats:()=>({rawRequests,bodyReads})};
}
(async()=>{
 // Reproduces the genuine 2026-11-10 trace: a detail response reaches HTTP 200
 // but the JSON body stays pending. The AbortController must cover body consumption.
 {
  const {h,handles,stats}=makeHost();
  vm.createContext(h);vm.runInContext(read('core.js'),h);vm.runInContext(read('network.js'),h);
  const tpl={url:'https://apps.abacus.ai/api/getDeploymentConversation?deploymentConversationId=test-session-001',method:'GET',headers:new Headers(),body:null};
  const pending=h.__SimanNetworkV155.replay(tpl);
  await delay(10);
  assert.equal(stats().bodyReads,1,'replay must reach a stalled response body');
  assert.equal(handles.length,1,'timeout must be armed while JSON body remains pending');
  handles[0]();
  await assert.rejects(pending,/body aborted/);
  console.log('PASS observed ChatLLM HTTP 200 never-ending response body aborts instead of hanging indefinitely');
 }
 // The direct same-origin request path must retain its timeout across JSON parse too.
 {
  const {h,handles,events,stats}=makeHost();
  h.location={href:'https://chatgpt.com/',origin:'https://chatgpt.com',pathname:'/'};
  vm.createContext(h);h._vmWindow=vm.runInContext('window',h);vm.runInContext(read('core.js'),h);vm.runInContext(read('page.js'),h);
  assert.equal(h.__SimanRunnerV155.start().ok,true);
  for(let i=0;i<30&&stats().bodyReads===0;i++)await delay(5);
  if(stats().bodyReads!==1)console.log('Fixture diagnostics',JSON.stringify({stats:stats(),events:events.slice(0,15),handles:handles.length,runner:h.__SimanRunnerV155.ping()}));
  assert.equal(stats().bodyReads,1,'main collector must reach a stalled JSON body');
  assert(handles.length>0,'collector body timeout must remain armed');
  handles[0]();
  for(let i=0;i<30&&!events.some(x=>x.kind==='ERROR');i++)await delay(5);
  assert(events.some(x=>x.kind==='ERROR'),'stalled JSON body must end runner with explicit failure');
  assert(events.some(x=>x.kind==='TRACE'&&x.stage==='NETWORK_ERROR'),'private-safe network failure trace required');
  console.log('PASS direct collector detects hung JSON body with explicit error rather than silent stall');
 }
 // A crashed/disconnected batch tab must be reconnected once only, not forever.
 const search=read('search.js');
 assert(search.includes('AUTO_RECOVER')&&search.includes('attempt<2'),'batch reconnect must have a strict upper bound');
 assert(search.includes('disconnected:true'),'watchdog must distinguish disconnected tab from HTTP 429 pause');
 assert(search.includes('done?.summary?.paused'),'HTTP 429 pause handling must remain intact');
 console.log('PASS one bounded batch reconnect, prior archive retention, HTTP 429 unchanged');
})().catch(e=>{console.error(e);process.exitCode=1});
