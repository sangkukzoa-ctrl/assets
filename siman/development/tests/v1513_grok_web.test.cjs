'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const read=n=>fs.readFileSync(path.join(__dirname,'../app',n),'utf8');
const origin='https://grok.com',id='00000000-0000-4000-8000-000000000001';
const ask='00000000-0000-4000-8000-000000000002';
const old='00000000-0000-4000-8000-000000000004',newId='00000000-0000-4000-8000-000000000005';
const nodes={responseNodes:[{responseId:ask,sender:'human',parentResponseId:null},{responseId:old,sender:'assistant',parentResponseId:ask},{responseId:newId,sender:'assistant',parentResponseId:ask}]};
const meta={conversation:{conversationId:id,title:'Grok 과거 대화',modifyTime:'2026-11-12T18:00:00Z',workspaces:[{name:'프로젝트 테스트'}]}};
const responseList={responses:[
 {responseId:ask,sender:'human',message:'Grok 과거 질문',createTime:'2026-11-10T12:00:00Z'},
 {responseId:old,sender:'assistant',message:'버려진 답변',createTime:'2026-11-10T12:00:01Z'},
 {responseId:newId,sender:'assistant',message:'검색 대상 최종 답변',createTime:'2026-11-10T12:00:02Z'}
]};
const events=new Map(),out=[],saved=[],calls=[];
const main={URL,URLSearchParams,Headers,AbortController,Map,Set,Object,Promise,JSON,Error,RegExp,Array,Math,Number,String,Boolean,console,Date,
 location:{href:origin+'/',origin,hostname:'grok.com',pathname:'/'},
 setTimeout,clearTimeout,setInterval:()=>0,clearInterval:()=>{}};
main.window=main;main.globalThis=main;
main.addEventListener=(type,fn)=>{const handlers=events.get(type)||[];handlers.push(fn);events.set(type,handlers)};
main.postMessage=d=>{
 out.push(d);if(d.kind!=='BRIDGE')return;
 if(d.action==='SAVE')saved.push(d.record);
 queueMicrotask(()=>{for(const fn of events.get('message')||[])fn({source:vm.runInContext('window',main),origin,
 data:{kind:'BRIDGE_REPLY',seqId:d.seqId,tag:d.tag,ok:true,completeIds:[],storageReady:true}})});
};
main.fetch=async (url,options={})=>{
 const u=new URL(url);
 assert.equal(u.origin,origin);
 assert(u.pathname.startsWith('/rest/'));
 assert.equal(options.credentials,'include');
 calls.push({path:u.pathname,query:u.searchParams,method:options.method||'GET'});
 let data;
 if(u.pathname==='/rest/app-chat/conversations'&&u.searchParams.has('pageSize')){
  data=u.searchParams.has('pageToken')?{conversations:[],nextPageToken:''}:{conversations:[{conversationId:id,title:'Grok 과거 대화'}],nextPageToken:''};
 }else if(u.pathname.includes('conversations_v2/'))data=meta;
 else if(u.pathname.endsWith('/response-node'))data=nodes;
 else if(u.pathname.endsWith('/load-responses')){
  assert.equal(options.method,'POST');
  const body=JSON.parse(options.body);assert(body.responseIds.includes(ask));
  data=responseList;
 }else throw Error('Unexpected Grok request '+u.pathname);
 return {ok:true,status:200,headers:new Headers({'content-type':'application/json'}),
  json:async()=>data};
};
vm.createContext(main);vm.runInContext('window=globalThis',main);
vm.runInContext(read('core.js'),main);vm.runInContext(read('grok-web.js'),main);
const grok=main.SimanGrokWeb;assert(grok);
assert.equal(main.SimanCore.providerFromUrl(origin+'/c/'+id),'grok');
assert.equal(main.SimanCore.sourceUrl('grok',id),origin+'/c/'+id);
assert.equal(grok.validList({conversations:[{conversationId:id,title:'A'}],nextPageToken:'more'}).nextPageToken,'more');
assert.throws(()=>grok.validList({error:'not logged in'}),/응답 형식/);
const transcript=grok.activeMessages(meta,nodes,responseList);
assert.equal(transcript.messages.length,2);
assert.equal(transcript.messages[0].text,'Grok 과거 질문');
assert.equal(transcript.messages[1].text,'검색 대상 최종 답변');
assert.equal(transcript.complete,true);
assert.equal(transcript.projectName,'프로젝트 테스트');
assert(!JSON.stringify(transcript).includes('버려진 답변'));
const older=grok.activeMessages(meta,nodes,responseList,{responseId:old});
assert.equal(older.messages[1].text,'버려진 답변');
assert.throws(()=>grok.activeMessages(meta,nodes,{responses:responseList.responses.slice(0,2)}),/누락/);
vm.runInContext(read('page.js'),main);
const ping=main.__SimanRunnerV155.ping();assert.equal(ping.provider,'grok');
assert.equal(ping.version,'1.5.13');
assert.equal(main.__SimanRunnerV155.start().ok,true);
(async()=>{
 for(let i=0;i<100&&!out.some(x=>x.kind==='DONE'||x.kind==='ERROR');i++)
  await new Promise(resolve=>setTimeout(resolve,60));
 const errors=out.filter(x=>x.kind==='ERROR');if(errors.length)console.error('Grok fixture failures',errors);
 assert(!errors.length);
 const done=out.find(x=>x.kind==='DONE');assert(done,'Grok collection must terminate');
 assert.equal(done.result.found,1);
 assert.equal(done.result.read,1);
 assert.equal(done.result.complete,true);
 assert.equal(saved.length,1);assert.equal(saved[0].provider,'grok');
 assert(calls.some(x=>x.path.endsWith('/response-node')));
 assert(calls.some(x=>x.path.endsWith('/load-responses')&&x.method==='POST'));
 assert(!JSON.stringify(out).includes('버려진 답변'),'internal messages must not escape to debug log');
 console.log('PASS: Grok account list, authenticated read-only detail, active branch, no discarded answer, local archive, DONE and original URL');
})().catch(e=>{console.error(e);process.exitCode=1});
