'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const read=n=>fs.readFileSync(path.join(__dirname,'../app',n),'utf8');
let registered=0,unregistered=0,observer=null,bridgeListeners=[],removed=0,periodic=null,periodicCleared=0,timers=0;
const ctx={URL,URLSearchParams,Date,Map,Set,Object,Promise,JSON,Math,Number,String,Boolean,Error,RegExp,Array,console,
 location:{href:'https://grok.com/',origin:'https://grok.com',hostname:'grok.com',pathname:'/'},
 document:{readyState:'complete',body:{},title:'Grok',addEventListener(){},querySelectorAll:()=>[]},
 chrome:{runtime:{id:'ext-id',onMessage:{addListener(){registered++},removeListener(){unregistered++}}}},
 setTimeout:()=>++timers,clearTimeout:()=>{},
 setInterval:cb=>{periodic=cb;return 42},clearInterval:()=>{periodicCleared++},
 MutationObserver:class{constructor(fn){observer=this;this.cb=fn;this.disconnected=false}observe(){}disconnect(){this.disconnected=true}},
 addEventListener:(name,cb)=>{if(name==='message')bridgeListeners.push(cb)},
 removeEventListener:(name,cb)=>{if(name==='message'&&bridgeListeners.includes(cb))removed++},
 postMessage(){},getComputedStyle:()=>({overflowY:'hidden'})};
ctx.window=ctx;ctx.globalThis=ctx;
vm.createContext(ctx);
vm.runInContext(read('core.js'),ctx);
ctx.SimanStore={getStatus:async()=>({}),appendDebug:async()=>{},save:async()=>{},one:async()=>null};
vm.runInContext(read('content.js'),ctx);
assert.equal(registered,1);
assert(observer,'visited DOM observer attached');
assert(periodic,'health timer attached');
vm.runInContext(read('content.js'),ctx);
assert.equal(registered,1,'duplicate injection must not attach another listener');
ctx.chrome.runtime.id='';
assert.doesNotThrow(()=>observer.cb([]),'stale context should gracefully retire observers');
assert.equal(observer.disconnected,true);
assert.equal(unregistered,1);
assert.equal(removed,1);
assert(periodicCleared>=1);
assert.doesNotThrow(()=>periodic(),'stale timer callbacks should no-op');
console.log('PASS Chrome hot-extension-update disposes obsolete isolated-world listeners, observers and timers');
