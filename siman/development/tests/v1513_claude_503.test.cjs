'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const read=n=>fs.readFileSync(path.resolve(__dirname,'../app',n),'utf8');
let now=1794577000000;class FakeDate extends Date{static now(){now+=3200;return now}}
const origin='https://claude.ai',url=origin+'/',calls=[],messages=[],callbacks=[],saved=[];
const ctx={URL,URLSearchParams,Headers,AbortController,Date:FakeDate,Map,Set,Object,Promise,JSON,Math,Number,String,Boolean,Error,RegExp,Array,console,
 location:{origin,href:url,pathname:'/',hostname:'claude.ai'},
 setTimeout:(fn)=>setTimeout(fn,1),clearTimeout,setInterval:()=>0,clearInterval:()=>{},
 document:{querySelectorAll:()=>[]},XMLHttpRequest:class{open(){}send(){}setRequestHeader(){}addEventListener(){}}
};
ctx.window=ctx;ctx.globalThis=ctx;
ctx.addEventListener=(name,fn)=>{if(name==='message')callbacks.push(fn)};
ctx.postMessage=m=>{
 messages.push(m);
 if(m.kind!=='BRIDGE')return;
 if(m.action==='SAVE')saved.push(m.record);
 queueMicrotask(()=>callbacks.forEach(fn=>fn({data:{tag:m.tag,kind:'BRIDGE_REPLY',seqId:m.seqId,ok:true,completeIds:[],storageReady:true},source:vm.runInContext('window',ctx),origin})));
};
let detailAttempts=0;
ctx.fetch=async input=>{
 const u=new URL(input,url),p=u.pathname;calls.push(p);
 const r=(data,status=200)=>({ok:status===200,status,headers:new Headers(),json:async()=>data});
 if(p==='/api/organizations')return r([{uuid:'org1',name:'Personal'}]);
 if(p.includes('/projects'))return r({projects:[]});
 if(p.includes('chat_conversations_v2'))return r({chat_conversations:[{uuid:'abcde12345',name:'503 임시 오류 테스트'}]});
 if(p.includes('chat_conversations/abcde12345')){
  detailAttempts++;
  if(detailAttempts<=2)return r({error:'temporary backend unavailable'},503);
  return r({uuid:'abcde12345',name:'503 임시 오류 테스트',chat_messages:[
   {sender:'human',text:'지난 클로드 질문 원문'},
   {sender:'assistant',text:'재시도 후 복구된 답변 원문'}
  ]});
 }
 return r({},404);
};
vm.createContext(ctx);vm.runInContext('window=globalThis',ctx);
for(const file of ['core.js','network.js','page.js'])vm.runInContext(read(file),ctx,{filename:file});
ctx.__SimanRunnerV155.start();
(async()=>{
 for(let i=0;i<400&&!messages.some(x=>x.kind==='DONE'||x.kind==='ERROR');i++)await new Promise(r=>setTimeout(r,5));
 const error=messages.find(x=>x.kind==='ERROR');if(error)console.error(error);
 assert(!error,'temporary HTTP 503 must not kill collection');
 const done=messages.find(x=>x.kind==='DONE');assert(done,'collector must finish');
 assert.equal(detailAttempts,3,'bounded retries should recover on third response');
 assert.equal(done.result.read,1);
 assert.equal(done.result.errors,0);
 assert.equal(saved.length,1);
 assert(saved[0].messages.some(m=>m.text.includes('복구된 답변')));
 assert(messages.some(m=>m.kind==='TRACE'&&m.stage==='CLAUDE_RETRY'));
 console.log('PASS Claude temporary 503 twice, bounded retry, third success, preserved searchable transcript');
})().catch(e=>{console.error(e);process.exitCode=1});
