const vm=require('vm'),fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const folder=path.resolve(__dirname,'..','app');
const read=n=>fs.readFileSync(path.join(folder,n),'utf8');
async function scenario({provider,siteResponses,observed=null,observedAfterStart=null,expectNoInvalid=false}){
 let now=1762550000000;const tick=observedAfterStart?120:2300;class FakeDate extends Date{static now(){now+=tick;return now}}
 let url=provider==='chatllm'?'https://apps.abacus.ai/chatllm/':'https://claude.ai/';const o=new URL(url);
 const outcomes=[];let siteCalls=[],events=new Map(),records=new Map(),catalog=[];
 const response=(payload,status=200)=>({ok:status===200,status,headers:new Headers({'content-type':'application/json'}),json:async()=>payload,clone(){return this}});
 function match(u){let path=new URL(u,url).pathname+new URL(u,url).search;siteCalls.push(path);let target=siteResponses.find(x=>(typeof x.test==='function'?x.test(path):path.includes(x.test)));return target?response(target.data,target.status||200):response({error:'unknown endpoint'},404)}
 const main={URL,URLSearchParams,Headers,AbortController,Map,Set,Object,Promise,JSON,Error,RegExp,Array,Math,Number,String,Boolean,console};
 main.location={href:url,origin:o.origin,hostname:o.hostname,pathname:o.pathname};main.document={querySelectorAll:()=>[]};main.getComputedStyle=()=>({overflowY:'hidden'});main.fetch=async(input,init)=>match(typeof input==='string'?input:input.url);
 main.XMLHttpRequest=class{open(){}send(){}setRequestHeader(){}addEventListener(){}};
 main.setTimeout=(fn)=>setTimeout(fn,1);main.clearTimeout=clearTimeout;main.setInterval=(fn)=>setInterval(fn,3000);main.clearInterval=clearInterval;main.Date=FakeDate;main.window=main;main.globalThis=main;
 main.addEventListener=(name,listener)=>{let arr=events.get(name)||[];arr.push(listener);events.set(name,arr)};
 const dispatch=data=>{for(const fn of events.get('message')||[])fn({source:main.window,origin:o.origin,data})};
 main.postMessage=(data)=>{
  if(data.kind==='BRIDGE')queueMicrotask(()=>{const action=data.action;let result={tag:data.tag,kind:'BRIDGE_REPLY',seqId:data.seqId,ok:true};
   if(action==='TEST'){result.storageReady=true;}
   if(action==='CATALOG')catalog.push(...data.entries);
   if(action==='LOOKUP')result.completeIds=[];
   if(action==='SAVE')records.set(data.record.key,data.record);
   dispatch(result);
  });
  else if(['DONE','ERROR','WARN','PROGRESS'].includes(data.kind))outcomes.push(data);
 };
 vm.createContext(main);vm.runInContext('window=globalThis',main);
 for(const name of ['core.js','network.js','page.js'])vm.runInContext(read(name),main,{filename:name});
 if(observed)await main.fetch(observed);
 assert(main.__SimanRunnerV155,'runner installed');const r=main.__SimanRunnerV155.start();assert(r.ok);
 if(observedAfterStart)setTimeout(()=>main.fetch(observedAfterStart).catch(e=>outcomes.push({kind:'WEB_LATE_FAILURE',text:String(e)})),3);
 let ended=false;for(let i=0;i<2000;i++){await new Promise(resolve=>setImmediate(resolve));if(outcomes.some(x=>x.kind==='DONE'||x.kind==='ERROR')){ended=true;break}}
 assert(ended,provider+' collector did not finish');
 if(expectNoInvalid)assert(!siteCalls.some(x=>x.includes('listDeploymentConversations')),'invalid API called');
 return {outcomes,records,catalog,siteCalls,completed:outcomes.find(x=>x.kind==='DONE'),error:outcomes.find(x=>x.kind==='ERROR')};
}
(async()=>{
 const chat=await scenario({provider:'chatllm',observed:'/api/chatllm/listConversations?limit=60',expectNoInvalid:true,siteResponses:[
 {test:'/api/chatllm/listConversations',data:{result:{deploymentConversations:[{deploymentConversationId:'aaaaaa111111',name:'중원무림맹 설정',chatllmProjectName:'무림맹'}]}}},
 {test:'/api/getDeploymentConversation',data:{result:{deploymentConversationId:'aaaaaa111111',history:[{role:'user',text:'마군 출현'},{role:'assistant',text:'호법이오'}]}}}
 ]});
 assert.equal(chat.catalog.length,1);assert.equal(chat.records.size,1);assert(chat.completed?.result.found===1);assert([...chat.records.values()][0].messages.some(m=>m.text.includes('마군')));console.log('PASS ChatLLM observed native list + direct details, no invalid API');
 const delayed=await scenario({provider:'chatllm',observedAfterStart:'/api/listDeploymentConversations',siteResponses:[
 {test:'/api/listDeploymentConversations',data:{result:{deploymentConversations:[{deploymentConversationId:'delayedid777',name:'늦게 도착한 마군 대화'}]}}},
 {test:'/api/getDeploymentConversation',data:{result:{deploymentConversationId:'delayedid777',history:[{role:'user',text:'마군은 어디 있느냐'},{role:'assistant',text:'여기 있소'}]}}}
 ]});
 assert.equal(delayed.catalog.length,1,'late ChatLLM list should not be lost');
 assert.equal(delayed.records.size,1,'late detail should be saved');
 assert(delayed.records.size&&[...delayed.records.values()][0].messages.some(m=>m.text.includes('마군')));
 console.log('PASS ChatLLM delayed list HTTP 200 arrives after sync START, then saved and searchable');
 const paged=await scenario({provider:'chatllm',observed:'/api/chatllm/listConversations?limit=1&offset=0',expectNoInvalid:true,siteResponses:[
 {test:p=>p.includes('/api/chatllm/listConversations')&&p.includes('offset=1'),data:{items:[{deploymentConversationId:'bbbbbb222222',name:'프로젝트 B'}],has_more:false}},
 {test:'/api/chatllm/listConversations',data:{items:[{deploymentConversationId:'aaaaaa111111',name:'프로젝트 A'}],has_more:true}},
 {test:p=>p.includes('/api/getDeploymentConversation')&&p.includes('bbbbbb222222'),data:{result:{deploymentConversationId:'bbbbbb222222',history:[{role:'user',text:'2번 프로젝트에도 마군'}]}}},
 {test:'/api/getDeploymentConversation',data:{result:{deploymentConversationId:'aaaaaa111111',history:[{role:'user',text:'1번 프로젝트의 마군'}]}}}
 ]});
 assert.equal(paged.records.size,2);assert.equal(paged.catalog.length,2);console.log('PASS ChatLLM multiple discovered pages, both searchable');
 const claude=await scenario({provider:'claude',siteResponses:[
 {test:'/api/organizations/org1/chat_conversations/',data:{uuid:'c12345678901',name:'프로젝트 대화',chat_messages:[{sender:'human',text:'마군'},{sender:'assistant',text:'알겠소'}]}},
 {test:'/api/organizations/org1/chat_conversations_v2',data:{chat_conversations:[{uuid:'c12345678901',name:'프로젝트 대화'}]}},
 {test:'/api/organizations/org1/projects',data:{projects:[]}},
 {test:'/api/organizations',data:[{uuid:'org1',name:'Personal'}]}
 ]});
 assert.equal(claude.records.size,1);assert(claude.completed?.result.found===1);console.log('PASS Claude org discovery, API list, detail, local store');
 const empty=await scenario({provider:'claude',siteResponses:[{test:'/api/organizations',data:[]},{test:'/api/account',data:{memberships:[]}}]});
 assert(empty.error?.text?.includes('조직을 발견하지 못했습니다'));assert(!empty.completed);console.log('PASS Claude zero discovered not a false success');
 const chat0=await scenario({provider:'chatllm',siteResponses:[],expectNoInvalid:true});assert(chat0.error);assert(!chat0.completed);console.log('PASS ChatLLM no data diagnosis, no fake success');
})().catch(e=>{console.error(e);process.exit(1)});
