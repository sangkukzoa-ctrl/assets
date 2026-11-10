const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const file=n=>fs.readFileSync(path.resolve(__dirname,'../app',n),'utf8');
const id='11aabb22-3344-5566-7788-990011223344';
const origin='https://chat.deepseek.com';
const href=origin+'/a/chat/s/'+id;
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let saved=[],logs=[],failSave=true,mutate,interval,now=10000;
const row=(text,assistant=false)=>({innerText:text,textContent:text,parentElement:{closest:()=>null},getAttribute:()=>null,matches:()=>false,querySelector:()=>assistant?{innerText:text,textContent:text}:null});
let rows=[row('수집 재시도 테스트 1'),row('수집 재시도 테스트 2',true)];
const doc={readyState:'complete',title:'DeepSeek',body:{},querySelector:q=>q.includes('ds-virtual-list')?{children:rows}:null,querySelectorAll:()=>[],addEventListener(){}};
const location={href,origin,pathname:new URL(href).pathname};
const DateProxy=class extends Date{static now(){return now}};
const ctx={Date:DateProxy,URL,URLSearchParams,Set,Map,Math,JSON,Number,String,Boolean,Object,Promise,RegExp,Array,Error,console,location,document:doc,clearTimeout,
  setTimeout:(fn,ms)=>setTimeout(fn,Math.min(10,ms)),setInterval:fn=>{interval=fn;return 42},
  chrome:{runtime:{id:'extension-stable',onMessage:{addListener(){}}}},
  MutationObserver:class{constructor(fn){mutate=fn}observe(){}}};
ctx.globalThis=ctx;ctx.window=ctx;ctx.addEventListener=()=>{};ctx.postMessage=()=>{};
vm.createContext(ctx);
vm.runInContext(file('core.js'),ctx);
// Test the exact Chrome error route: the isolated content executes before store.js.
assert.doesNotThrow(()=>vm.runInContext(file('content.js'),ctx), 'missing dependency must not crash Chrome extensions');
assert.equal(ctx.__simanContentV155,undefined,'must not mark initialized before store is ready');
ctx.SimanStore={getStatus:async()=>({}),appendDebug:async x=>{logs.push(x)},save:async x=>{if(failSave){failSave=false;throw Error('transient storage failure')}saved.push(x)},one:async()=>saved[0]};
(async()=>{
 await delay(50);
 assert.equal(ctx.__simanContentV155,true,'a delayed storage dependency must bootstrap automatically');
 assert.equal(saved.length,0,'first failed write should not be counted as saved');
 assert(logs.some(x=>x.stage==='VISIT_ERROR'),'failure must appear in diagnostic log');
 // Same exact DOM and URL: the old v1.5.4 code skipped this forever due to stale lastSig.
 interval();await delay(50);
 assert.equal(saved.length,1,'identical page should be saved on the next scheduled capture');
 assert(logs.some(x=>x.stage==='VISIT_CAPTURE'),'successful DeepSeek capture must appear in diagnostic log');
 assert(!JSON.stringify(logs).includes('수집 재시도 테스트'),'diagnostics must never contain message bodies');
 assert.equal(ctx.__SimanVisitHealthV155().count,2);
 // Continuous fast mutations should not indefinitely starve a debounce timer.
 rows=[row('새 메시지 세 번째'),row('새 답변 네 번째',true)];
 for(let i=0;i<8;i++){now+=900;mutate();await delay(2)}
 await delay(40);
 assert(saved.length>=2,'sustained DOM mutations must still capture new messages');
 console.log('PASS missing dependency recovery, retry after failed storage, continuous DOM activity, diagnostics privacy');
})().catch(e=>{console.error(e);process.exitCode=1});

// Also simulate core.js itself being late. Earlier v1.5.5 attempt returned before
// scheduling a retry when SimanCore was missing, leaving a silent dead script.
(async()=>{
 const c={URL,URLSearchParams,Map,Set,Math,JSON,Number,String,Boolean,Object,Promise,RegExp,Array,Error,Date,console,
  location,document:{readyState:'loading',addEventListener(){},body:{}},
  setTimeout:(fn)=>setTimeout(fn,5),clearTimeout,setInterval:()=>42,
  chrome:{runtime:{id:'test-extension',onMessage:{addListener(){}}}}};
 c.globalThis=c;c.window=c;c.addEventListener=()=>{};c.postMessage=()=>{};
 vm.createContext(c);
 assert.doesNotThrow(()=>vm.runInContext(file('content.js'),c));
 assert.equal(c.__simanContentV155,undefined);
 await delay(10);
 vm.runInContext(file('core.js'),c);
 c.SimanStore={getStatus:async()=>({}),appendDebug:async()=>{},save:async()=>{},one:async()=>null};
 await delay(50);
 assert.equal(c.__simanContentV155,true,'core.js delayed startup must self-recover');
 console.log('PASS late core.js dependency automatically recovers without uncaught Chrome script error');
})().catch(e=>{console.error(e);process.exitCode=1});
