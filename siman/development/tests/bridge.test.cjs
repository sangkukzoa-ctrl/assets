const fs=require('fs'),vm=require('vm'),path=require('path'),assert=require('node:assert/strict');
const folder=path.resolve(__dirname,'..','app');const read=n=>fs.readFileSync(path.join(folder,n),'utf8');
const url='https://apps.abacus.ai/chatllm/',origin=new URL(url).origin;
const store=new Map();
const local={async get(k){let keys=k==null?[...store.keys()]:Array.isArray(k)?k:[k];return Object.fromEntries(keys.filter(x=>store.has(x)).map(x=>[x,store.get(x)]))},async set(d){for(const [k,v] of Object.entries(d))store.set(k,v)},async remove(k){for(const x of Array.isArray(k)?k:[k])store.delete(x)},async getKeys(){return [...store.keys()]}};
const receivers={MAIN:[],ISOLATED:[]};let printed=0;
const make=(world)=>{
 let window={};
 const context={URL,URLSearchParams,Headers,AbortController,Map,Set,Object,Promise,JSON,Error,RegExp,Array,Math,Number,String,Boolean,console,Date, setTimeout,clearTimeout,setInterval,clearInterval};
 context.location={href:url,origin,hostname:'apps.abacus.ai',pathname:'/chatllm/'};
 context.window=context;context.globalThis=context;
 context.document={readyState:'loading',addEventListener(){},querySelectorAll(){return []}};
 context.getComputedStyle=()=>({overflowY:'hidden'});context.MutationObserver=class{observe(){}};
 context.addEventListener=(event,fn)=>{if(event==='message')receivers[world].push(fn)};
 context.postMessage=(data)=>queueMicrotask(()=>{
    if(printed++<12)console.log('BUS',data.kind,data.action,receivers.MAIN.length,receivers.ISOLATED.length);for(const w of Object.keys(receivers))for(const fn of receivers[w])fn({data,origin,source:w==='MAIN'?vm.runInContext('window',main):vm.runInContext('window',isolated)});
 });
 context.fetch=async(input)=>{
   const p=new URL(typeof input==='string'?input:input.url,url).pathname;
   let data={};if(p.includes('listConversations'))data={result:{deploymentConversations:[{deploymentConversationId:'aaaaaa111111',name:'중원무림맹'}]}};
   else if(p.includes('getDeploymentConversation'))data={result:{deploymentConversationId:'aaaaaa111111',history:[{role:'user',text:'마군 테스트'},{role:'assistant',text:'심안'}]}};
   else data={};
   return {ok:true,status:200,headers:new Headers({'content-type':'application/json'}),json:async()=>data,clone(){return this}};
 };
 context.XMLHttpRequest=class{open(){}send(){}setRequestHeader(){}addEventListener(){}};
 if(world==='ISOLATED')context.chrome={storage:{local},runtime:{id:'siman-test-extension',onMessage:{addListener(){}}}};
 return vm.createContext(context);
};
const main=make('MAIN'),isolated=make('ISOLATED');
function load(ctx,file){vm.runInContext(read(file),ctx,{filename:file})}
(async()=>{
 ['core.js','store.js','content.js'].forEach(f=>load(isolated,f));
 assert.equal(isolated.__simanContentV155,true,'isolated content script fully initialized');
 ['core.js','network.js','page.js'].forEach(f=>load(main,f));
 const test=await main.__SimanRunnerV155.pingStorage();assert(test.ok&&test.latencyMs>=0,'bidirectional storage ping');
 await main.fetch('/api/chatllm/listConversations?limit=10');await new Promise(r=>setTimeout(r,20));
 const before=main.__SimanNetworkV155.snapshot();assert.equal(before.conversations.length,1,'observed real page list');
 assert(main.__SimanRunnerV155.start().ok);
 let status;for(let i=0;i<800;i++){await new Promise(r=>setTimeout(r,10));status=await isolated.SimanStore.getStatus();if(status.last?.chatllm)break}
 assert(status?.last?.chatllm?.found===1,'discovered one conversation');
 assert(status?.last?.chatllm?.read===1,'wrote one conversation');
 const records=await isolated.SimanStore.all();assert.equal(records.length,1);assert(records[0].messages.some(m=>m.text.includes('마군')));
 const traces=await isolated.SimanStore.getDebug();assert(traces.some(e=>e.stage==='BRIDGE_OK'),'bridge OK recorded in diagnostics');
 console.log('PASS main/isolated postMessage -> chrome.storage -> local archive -> Korean search data');
 console.log('PASS observed ChatLLM list 1 -> detail GET -> saved 1 -> status DONE / trace');
})().catch(e=>{console.error(e);process.exitCode=1});
