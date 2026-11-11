const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const app=p=>fs.readFileSync(path.join(__dirname,'../app',p),'utf8');
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const TOKEN='0123456789abcdef0123456789abcdef';
const U='chrome-extension://abcdefabcdefabcdefabcdefabcdefab/search.html?siman_auto_apply=1&version=1.5.8&port=30222&token='+TOKEN;
async function testCommand(manifestVersion){
 const data=new Map([['siman:v11:record:chatgpt:keep',{messages:[{text:'keep original transcript'}]}]]);
 const changes=[],store={get:async k=>({[k]:data.get(k)}),set:async r=>{for(let [k,v] of Object.entries(r))data.set(k,v)},remove:async k=>data.delete(k)};
 const ctx={location:{search:new URL(U).search,pathname:'/search.html'},URLSearchParams,
  history:{replaceState(...args){changes.push(args)}},window:{},console,
  chrome:{storage:{local:store},runtime:{getManifest:()=>({version:manifestVersion}),
   reload:()=>changes.push('reload'),sendMessage:(msg,cb)=>{changes.push(msg);cb?.()},lastError:null}},
 };
 ctx.globalThis=ctx;ctx.window=ctx;vm.createContext(ctx);
 vm.runInContext(app('search.js'),ctx);
 await wait(10);
 assert.equal(data.get('siman:v11:record:chatgpt:keep').messages[0].text,'keep original transcript');
 assert.equal(data.get('siman:updater:pending').token,TOKEN);
 assert.equal(changes[0][2],'/search.html','one-shot URL must be cleared before reload');
 assert.equal(changes.some(x=>x==='reload'),manifestVersion!=='1.5.8');
 assert.equal(changes.some(x=>x?.type==='SIMAN_APPLY_PENDING_UPDATE'),manifestVersion==='1.5.8');
}
async function testBackground(){
 const archive={messages:[{text:'never overwrite existing user archive'}]};
 const data=new Map([['siman:v11:record:chatgpt:keep',archive],
  ['siman:updater:pending',{port:30222,token:TOKEN,version:'1.5.8',at:Date.now()}]]);
 let ready,reply,created=[],reloaded=[],removed=[],pages=0;
 const chrome={runtime:{
  getManifest:()=>({version:'1.5.8'}),
  onInstalled:{addListener(fn){ready=fn}},
  onMessage:{addListener(fn){reply=fn}}},
  storage:{local:{get:async k=>({[k]:data.get(k)}),remove:async k=>data.delete(k)}},
  scripting:{executeScript:async args=>[{result:args.target.tabId===9}]},
  tabs:{query:async()=>[{id:8,url:'https://chatgpt.com/c/test'},{id:9,url:'https://claude.ai/chat/test'}],
   reload:async id=>reloaded.push(id),
   create:async args=>{created.push(args);return {id:77}},
   remove:async id=>removed.push(id)}
 };
 const ctx={chrome,Date,Number,String,RegExp,Promise,encodeURIComponent,console, setTimeout:(fn)=>{fn();return 1;}};
 vm.createContext(ctx);vm.runInContext(app('background.js'),ctx);
 assert.equal(typeof ready,'function');assert.equal(typeof reply,'function');
 ready({reason:'update'});
 await wait(20);
 assert.equal(data.has('siman:updater:pending'),false);
 assert.equal(data.get('siman:v11:record:chatgpt:keep'),archive,'archive object reference is unchanged');
 assert.deepEqual(reloaded,[8], 'only tabs without a draft are refreshed');
 assert.equal(created.length,1,'only one local verification receipt');
 assert.equal(created[0].active,false);
 assert(created[0].url.includes('127.0.0.1:30222/complete?token='+TOKEN));
 assert(created[0].url.includes('drafts=1'));
 assert.deepEqual(removed,[77]);
 // Replaying background load cannot trigger duplicate reload/ACK.
 ready({reason:'startup'});await wait(5);assert.equal(created.length,1);
}
(async()=>{
 const manifest=JSON.parse(app('manifest.json'));
 assert.equal(manifest.background.service_worker,'background.js');
 assert.equal(manifest.version,'1.5.8');
 await testCommand('1.5.7');
 await testCommand('1.5.8');
 await testBackground();
 console.log('PASS v1.5.7 page one-shot trigger -> runtime.reload -> new MV3 background receipt -> AI tabs refreshed only if no draft; archive preserved');
})().catch(e=>{console.error(e);process.exitCode=1});
