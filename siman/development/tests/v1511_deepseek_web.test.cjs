/* Official DeepSeek WEB regression: independent of Abacus ChatLLM.
   Synthetic authenticated API fixture. No real login tokens or chats. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const folder=path.resolve(__dirname,'../app');
const source=name=>fs.readFileSync(path.join(folder,name),'utf8');
const id='2bd193c3-216f-4120-b9ac-190f0abe1977';
const secret='test-only-not-a-real-token';
function apiResponse(data){return {code:0,data:{biz_data:data}}}
const listing=apiResponse({chat_sessions:[{id,title:'테스트 DeepSeek 웹 세션',updated_at:11}],has_more:false});
const history=apiResponse({chat_session:{current_message_id:4},chat_messages:[
 {message_id:1,parent_id:null,role:'USER',fragments:[{type:'REQUEST',content:'별도 사이트 맞지?'}]},
 {message_id:2,parent_id:1,role:'ASSISTANT',fragments:[{type:'THINK',content:'비공개 추론 생략'},{type:'RESPONSE',content:'독립된 공식 웹입니다.'}]},
 {message_id:3,parent_id:1,role:'ASSISTANT',fragments:[{type:'RESPONSE',content:'재생성된 별도 분기'}]},
 {message_id:4,parent_id:2,role:'USER',fragments:[{type:'REQUEST',content:'ChatLLM과 분리할 것'}]}
]});
const events=new Map(),outputs=[],calls=[],saved=[];
const root='https://chat.deepseek.com/',origin=new URL(root).origin;
const main={URL,URLSearchParams,Headers,AbortController,Map,Set,Object,Promise,JSON,Error,RegExp,Array,Math,Number,String,Boolean,console,Date,
 location:{href:root,origin,hostname:'chat.deepseek.com',pathname:'/'},
 localStorage:{getItem:k=>k==='userToken'?JSON.stringify({value:secret}):null}};
main.window=main;main.globalThis=main;
main.setTimeout=setTimeout;main.clearTimeout=clearTimeout;main.setInterval=setInterval;main.clearInterval=clearInterval;
main.addEventListener=(name,cb)=>{const list=events.get(name)||[];list.push(cb);events.set(name,list)};
main.postMessage=d=>{
 outputs.push(d);
 if(d.kind!=='BRIDGE')return;
 if(d.action==='SAVE')saved.push(d.record);
 queueMicrotask(()=>{
  const reply={tag:d.tag,kind:'BRIDGE_REPLY',seqId:d.seqId,ok:true,storageReady:true,completeIds:[]};
  for(const cb of events.get('message')||[])cb({source:vm.runInContext('window',main),origin,data:reply});
 });
};
main.fetch=async (url,opt)=>{
 const u=new URL(url);assert.equal(u.hostname,'chat.deepseek.com');
 assert.equal(opt?.headers?.Authorization,'Bearer '+secret,'same-origin auth only');
 calls.push(u.pathname);
 const payload=u.pathname.includes('fetch_page')?listing:history;
 return {ok:true,status:200,headers:new Headers({'content-type':'application/json'}),json:async()=>payload};
};
vm.createContext(main);vm.runInContext('window=globalThis',main);vm.runInContext(source('core.js'),main);vm.runInContext(source('deepseek-web.js'),main);
const ds=main.SimanDeepSeekWeb;
assert(ds,'official web parser missing');
assert.equal(main.SimanCore.providerFromUrl(root),'deepseek');
assert.equal(main.SimanCore.providerFromUrl('https://apps.abacus.ai/chatllm/'),'chatllm');
assert.equal(ds.list(listing).rows.length,1);
const c=ds.history(history,id,'테스트');
assert.equal(c.provider,'deepseek');assert.equal(c.id,id);assert.equal(c.messages.length,3);
assert.equal(c.messages[1].role,'assistant');
assert(!JSON.stringify(c).includes('재생성된 별도 분기'),'inactive branch must be excluded');
assert(!JSON.stringify(c).includes('비공개 추론 생략'),'reasoning fragments must not replace visible response');
assert(c.url.startsWith('https://chat.deepseek.com/a/chat/s/'));
vm.runInContext(source('page.js'),main);
assert.equal(main.__SimanRunnerV155.ping().version,'1.5.11');
assert.equal(main.__SimanRunnerV155.start().ok,true);
(async()=>{
 for(let attempts=0;attempts<300&&!outputs.some(x=>x.kind==='DONE');attempts++)
  await new Promise(resolve=>setTimeout(resolve,20));
 const done=outputs.find(x=>x.kind==='DONE');
 if(!done)console.error('DeepSeek test trace:',outputs.filter(x=>x.kind!=='BRIDGE').map(x=>({kind:x.kind,stage:x.stage,text:x.text,result:x.result})).slice(-20), 'calls',calls);
 assert(done,'DeepSeek standalone history must complete');
 assert.equal(done.result.found,1);assert.equal(done.result.read,1);
 assert.equal(done.result.complete,true);
 assert.deepEqual(calls,['/api/v0/chat_session/fetch_page','/api/v0/chat/history_messages']);
 assert.equal(saved.length,1);assert.equal(saved[0].provider,'deepseek');
 assert(!JSON.stringify(outputs).includes(secret),'authentication token must never leave main world');
 console.log('PASS: DeepSeek WEB /fetch_page and /history_messages, Bearer kept on origin, active message branch, local bridge, one-click bulk, no ChatLLM mixing');
})().catch(e=>{console.error(e);process.exitCode=1});
