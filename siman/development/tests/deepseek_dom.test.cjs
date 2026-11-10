const fs=require('fs'),vm=require('vm'),path=require('path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../app');
const id='0c77c49a-16f4-4016-bbdb-64229e722feb';
const href='https://chat.deepseek.com/a/chat/s/'+id;
const save=new Map(),traces=[],timers=[];
const row=(text,assistant=false)=>({
 innerText:text,textContent:text,className:assistant?'role-assistant':'role-user',parentElement:{closest:()=>null},
 getAttribute:()=>null,matches:()=>false,
 querySelector:(selector)=>assistant?{innerText:text,textContent:text}:null,
});
const list={children:[row('마군이란 무엇인가'),row('마군은 수행을 방해하는 존재다.',true)]};
let observer=null;
const link={getAttribute:(k)=>k==='href'?'/a/chat/s/'+id:'',innerText:'모의 딥시크 대화'};
const document={readyState:'complete',body:{},title:'DeepSeek',querySelector:(q)=>q.includes('ds-virtual-list')?list:null,
 querySelectorAll:(q)=>q.includes('a[href*="/a/chat/s/"]')?[link]:[],addEventListener:()=>{}};
const ctx=vm.createContext({URL,URLSearchParams,Object,Promise,Set,Map,Number,String,Boolean,Math,RegExp,Array,JSON,Date,Error,console,
 location:{href,origin:'https://chat.deepseek.com',pathname:'/a/chat/s/'+id},document,
 MutationObserver:class{constructor(fn){observer=fn}observe(){}},setTimeout:(fn)=>{const t=setTimeout(fn,5);timers.push(t);return t},clearTimeout,
 setInterval:()=>0,chrome:{runtime:{id:'test-extension',onMessage:{addListener(){}}}}});
ctx.window=ctx;ctx.globalThis=ctx;ctx.addEventListener=()=>{};ctx.postMessage=()=>{};
ctx.SimanStore={getStatus:async()=>({}),updateEvent:async()=>{},one:async(key)=>save.get(key),save:async(rec)=>{save.set(rec.key,rec)},appendDebug:async(obj)=>{traces.push(obj)}};
vm.runInContext(fs.readFileSync(path.join(root,'core.js'),'utf8'),ctx,{filename:'core.js'});
vm.runInContext(fs.readFileSync(path.join(root,'content.js'),'utf8'),ctx,{filename:'content.js'});
(async()=>{
 await new Promise(r=>setTimeout(r,25));
 let rec=save.get('deepseek:'+id);
 assert(rec,'DeepSeek visited conversation not saved');
 assert.equal(rec.id,id);assert.equal(rec.url,href);
 assert.equal(rec.messages.length,2);assert.equal(rec.messages.map(x=>x.role).join(','),'user,assistant');
 assert(rec.messages[0].text.includes('마군'));
 list.children=[row('추가 질문에 마군'),row('심안 검색을 수정했습니다.',true)];observer();
 await new Promise(r=>setTimeout(r,25));
 rec=save.get('deepseek:'+id);
 assert.equal(rec.messages.length,4,'new viewport replaced previous captured text');
 assert.equal(rec.messages.filter(x=>x.text.includes('마군')).length,3);
 assert.equal(traces.length,1,'debug trace repeated or omitted');
 assert(!JSON.stringify(traces).includes('마군'),'raw conversation text leaked into debug');
 console.log('PASS DeepSeek actual /a/chat/s/UUID, both message roles, visited scroll merge, original URL, privacy-safe debug');
})().catch(e=>{console.error(e);process.exitCode=1});
