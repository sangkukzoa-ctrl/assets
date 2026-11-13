const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const app=p=>fs.readFileSync(path.join(__dirname,'../app',p),'utf8');
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const TOKEN='0123456789abcdef0123456789abcdef';
const EXT_ID='abcdefabcdefabcdefabcdefabcdefab';
const U='chrome-extension://abcdefabcdefabcdefabcdefabcdefab/search.html?siman_auto_apply=1&version=1.5.13&port=30222&token='+TOKEN;
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
 assert.equal(changes.some(x=>x==='reload'),manifestVersion!=='1.5.13');
 assert.equal(changes.some(x=>x?.type==='SIMAN_APPLY_PENDING_UPDATE'),manifestVersion==='1.5.13');
}
async function testUncachedBootstrap(loadedVersion){
 const url='chrome-extension://abcdefabcdefabcdefabcdefabcdefab/siman-update-1513.html?version=1.5.13&port=30222&token='+TOKEN;
 const records={old:{messages:[{text:'preserved conversation'}]}},actions=[];
 const ctx={URL,Date,Number,String,RegExp,Promise,console,
  location:{href:url,pathname:'/siman-update-1513.html'},
  history:{replaceState(...args){actions.push(args)}},
  document:{getElementById:()=>null},
  chrome:{storage:{local:{set:async values=>{records.pending=values['siman:updater:pending']}}},
    runtime:{id:'test-extension',getManifest:()=>({version:loadedVersion}),
      reload:()=>actions.push('reload'),sendMessage:()=>actions.push('message'),lastError:null}}
 };
 vm.createContext(ctx);vm.runInContext(app('siman-update-1513.js'),ctx);
 await wait(20);
 assert.equal(records.old.messages[0].text,'preserved conversation');
 assert.equal(records.pending.token,TOKEN,'bootstrap must write updater token');
 assert.equal(actions[0][2],'/siman-update-1513.html');
 assert.equal(actions.includes('reload'),loadedVersion!=='1.5.13');
 assert.equal(actions.includes('message'),loadedVersion==='1.5.13');
}

async function testBackground(){
 const archive={messages:[{text:'never overwrite existing user archive'}]};
 const data=new Map([['siman:v11:record:chatgpt:keep',archive],
  ['siman:updater:pending',{port:30222,token:TOKEN,version:'1.5.13',at:Date.now()}]]);
 let ready,reply,created=[],reloaded=[],removed=[],pages=0;
 const chrome={runtime:{
  id:EXT_ID,getManifest:()=>({version:'1.5.13'}),
  getURL:(name)=>'chrome-extension://'+EXT_ID+'/'+name,
  onInstalled:{addListener(fn){ready=fn}},
  onStartup:{addListener(){}},
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
 assert(created[0].url.includes('&id='+EXT_ID),'ACK must be bound to the exact existing extension ID');
 assert.deepEqual(removed,[77]);
 // Replaying background load cannot trigger duplicate reload/ACK.
 ready({reason:'startup'});await wait(5);assert.equal(created.length,1);
}
async function testDirectBackgroundRequest(){
 // Reproduce the real user's ERR_BLOCKED_BY_CLIENT case: NO extension update page
 // is opened. The updated service worker fetches a local, extension-owned JSON
 // request embedded at the original unpacked path and confirms on localhost.
 const archive={messages:[{text:'user archive from earlier version'}]};
 const data=new Map([['siman:v11:record:chatgpt:existing',archive]]);
 const logs=[],urls=[],calls=[],directive={
  version:'1.5.13',extensionId:EXT_ID,port:30333,token:TOKEN,at:Date.now()
 };
 const chrome={runtime:{
  id:EXT_ID,getManifest:()=>({version:'1.5.13'}),
  getURL:filename=>'chrome-extension://'+EXT_ID+'/'+filename,
  onInstalled:{addListener(){}},onStartup:{addListener(){}},
  onMessage:{addListener(){}}},
  storage:{local:{
   get:async k=>({[k]:data.get(k)}),
   set:async values=>{for(const [k,v] of Object.entries(values))data.set(k,v)},
   remove:async k=>data.delete(k),
   getKeys:async()=>[...data.keys()]
  }},
  tabs:{
   query:async()=>[],reload:async()=>{},
   create:async options=>{urls.push(options.url);return {id:78}},
   remove:async()=>{}
  },scripting:{executeScript:async()=>[]}
 };
 const ctx={chrome,Date,Number,String,RegExp,Promise,encodeURIComponent,console,
  setTimeout:(fn)=>{fn();return 1;},
  fetch:async url=>{calls.push(url);return {ok:true,json:async()=>directive}}};
 vm.createContext(ctx);
 vm.runInContext(app('background.js'),ctx);
 await wait(40);
 assert.equal(calls.length,1,'background loads the one-time request from its own extension path');
 assert(calls[0].endsWith('/siman-updater-request.json'));
 assert.equal(urls.length,1,'new background must ACK once without blocked extension-page navigation');
 assert(urls[0].startsWith('http://127.0.0.1:30333/complete?'));
 assert(urls[0].includes('&records=1'),'installer receives count-only proof that archive still exists');
 assert.equal(data.get('siman:v11:record:chatgpt:existing'),archive,'archive untouched');
 assert.equal(data.has('siman:updater:pending'),false,'single-use request cleared');
}
async function testInstallerNoBlockedPage(){
 const cs=fs.readFileSync(path.join(__dirname,'../installer/SimanSetup.cs'),'utf8');
 const region=cs.split('public static BrowserUpdateResult ApplyBrowserUpdates()')[1].split('// Opening a chrome:// page')[0];
 assert(region.includes('PrepareBackgroundAck(profile, port, token)'));
 assert(region.includes('ReceiveBackgroundAck(listener, token, profile.Id'));
 assert(!region.includes('/siman-update-1513.html'),'installer must not navigate to a blocked chrome-extension URL');
 assert(region.includes('chrome://extensions/'),'installer uses Chrome’s native extension manager');
}
(async()=>{
 const manifest=JSON.parse(app('manifest.json'));
 assert.equal(manifest.background.service_worker,'background.js');
 assert.equal(manifest.version,'1.5.13');
 await testUncachedBootstrap('1.5.7');
 await testUncachedBootstrap('1.5.13');
 await testCommand('1.5.7');
 await testCommand('1.5.13');
 await testBackground();
 await testDirectBackgroundRequest();
 await testInstallerNoBlockedPage();
 console.log('PASS v1.5.13 direct background ACK without ERR_BLOCKED_BY_CLIENT, same ID, Chrome storage preservation, legacy bootstrap');
})().catch(e=>{console.error(e);process.exitCode=1});
