/* 心眼: passive, same-origin conversation discovery. Never stores credentials. */
(()=>{'use strict';
if(window.__SimanNetworkV155)return;
const provider=window.SimanCore?.providerFromUrl(location.href);
if(!['chatllm','claude'].includes(provider))return;
const nativeFetch=window.fetch.bind(window),oldOpen=XMLHttpRequest.prototype.open,oldSend=XMLHttpRequest.prototype.send,oldSet=XMLHttpRequest.prototype.setRequestHeader;
const requests=new Map(),lists=new Map(),projects=new Map(),organizations=new Map(),details=new Map();let replayedAt=0;
const normUrl=u=>{try{const url=new URL(typeof u==='string'?u:u?.url,location.href);if(url.protocol!=='https:')return null;const host=url.hostname.toLowerCase();return (provider==='chatllm'&&(host==='abacus.ai'||host.endsWith('.abacus.ai')))||(provider==='claude'&&(host==='claude.ai'||host.endsWith('.claude.ai')))?url:null}catch{return null}};
function kind(u){const p=u.pathname.toLowerCase();if(!p.includes('/api/')&&!/(chat_conversations|list.{0,30}conversations|list.{0,30}sessions|list.{0,30}chats|get.{0,30}conversation|projects|organizations)/.test(p))return '';
 if(/create|delete|remove|generate|send|rename|update|upload|feedback|chatcompletion|predict|clear/.test(p))return '';
 if(/chat_conversations|listdeploymentconversations|list.*conversations|list.*sessions|list.*chats|search.*conversations|conversationlist/.test(p))return 'list';
 if(/getdeploymentconversation|exportdeploymentconversation|chat_conversations\//.test(p))return 'detail';
 if(/listchatllmprojects|\/projects/.test(p))return 'projects';
 if(/organizations/.test(p)&&!p.includes('chat_conversations'))return 'organizations';
 return '';
}
function enumerate(obj,allowed,depth=0){if(!obj||depth>9||typeof obj!=='object')return [];if(Array.isArray(obj)){const f=obj.filter(x=>x&&typeof x==='object'&&allowed(x));if(f.length)return f;for(const v of obj){let a=enumerate(v,allowed,depth+1);if(a.length)return a}return []}
 for(const key of ['deploymentConversations','conversations','chat_conversations','chatConversations','chatSessions','sessions','records','items','nodes','edges','results','result','data','organizations','projects','chatllmProjects','pagination'])if(obj[key]!=null){const a=enumerate(obj[key],allowed,depth+1);if(a.length)return a}
 return []}
const cid=x=>String(x?.deploymentConversationId||x?.conversationId||x?.chatSessionId||x?.conversation_uuid||x?.uuid||x?.id||'');
const isConv=x=>{const id=cid(x);return id.length>=6 && Boolean(x.deploymentConversationId||x.conversationId||x.chatSessionId||x.chatSession||((x.uuid||x.id)&&(x.name||x.title||x.summary||x.updated_at||x.updatedAt)))};
function recordList(data,url){const kindOf=kind(url),arr=kindOf==='list'||kindOf==='detail'?enumerate(data,isConv):enumerate(data,x=>!!(x.deploymentConversationId||x.conversationId||x.chatSessionId));if(kindOf==='list'&&!arr.length){nonMatchingLists++;if(nonMatchingLists<=4){const root=data?.result||data?.data||data;const names=Object.keys(root||{}).slice(0,14);window.postMessage({tag:'siman-heart-v155',kind:'TRACE',provider,stage:'LIST_RESPONSE_SHAPE',text:'목록 응답 구조: '+names.join(', ')+' · 세션 항목 0건'},location.origin)}}
 if(kindOf==='list'||arr.length){for(const x of arr){const id=cid(x);if(!id)continue;const existing=lists.get(id)||{};lists.set(id,{...existing,id,title:String(x.deploymentConversationName||x.name||x.title||x.summary||existing.title||''),projectId:String(x.chatllmProjectId||x.project_uuid||x.projectId||existing.projectId||''),projectName:String(x.chatllmProjectName||x.project_name||existing.projectName||''),organizationId:String(x.organization_uuid||x.organizationId||url.pathname.match(/organizations\/([\w-]+)/)?.[1]||existing.organizationId||''),url:String(x.conversationUrl||x.url||existing.url||''),raw:x});}}
 if(kindOf==='projects')for(const x of enumerate(data,v=>!!(v.chatllmProjectId||v.uuid||v.id)&&!!(v.name||v.title))){const id=String(x.chatllmProjectId||x.uuid||x.id);projects.set(id,String(x.name||x.title||''))}
 if(kindOf==='organizations')for(const x of enumerate(data,v=>!!(v.uuid||v.id)&&(v.name||v.display_name||v.capabilities||v.privacy_settings))){organizations.set(String(x.uuid||x.id),x)}
 if(kindOf==='detail'){const id=(url.searchParams.get('deploymentConversationId')||url.pathname.match(/chat_conversations\/([\w-]+)/)?.[1]||cid(data?.result||data?.data||data));if(id)details.set(id,data)}
}
function observe(url,method,headers,body){const u=normUrl(url);if(!u)return null;const k=kind(u);if(!k)return null;
 const tpl={url:u.href,method:String(method||'GET').toUpperCase(),headers:new Headers(headers||{}),body:typeof body==='string'&&body.length<12000?body:null,kind:k};if(!['GET','POST'].includes(tpl.method))return null;
 const key=k+'|'+u.pathname+'|'+tpl.method; if(!requests.has(key))requests.set(key,tpl);return {url:u,kind:k}
}
const safePath=u=>u.pathname.replace(/[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}/ig,'[ID]');
let networkTraceCount=0,nonMatchingLists=0;
function traceNet(obs,status){if(!obs)return;if(++networkTraceCount>30&&networkTraceCount%25!==0&&status===200)return;window.postMessage({tag:'siman-heart-v155',kind:'TRACE',provider,stage:'WEB_REQUEST',text:obs.kind+' '+safePath(obs.url)+' HTTP '+status},location.origin)}
function receive(data,url){try{if(data&&typeof data==='object')recordList(data,url)}catch{}}
window.fetch=function(input,init){const args=init||{};const url=normUrl(input);let observed=null;try{observed=observe(input,args.method||input?.method||'GET',args.headers||input?.headers,args.body)}catch{}
 const promise=nativeFetch(input,init);if(observed)Promise.resolve(promise).then(r=>{traceNet(observed,r.status);if(r.ok&&(r.headers.get('content-type')||'').includes('json'))return r.clone().json().then(d=>receive(d,observed.url))}).catch(()=>{});
 return promise};
XMLHttpRequest.prototype.open=function(method,url,...rest){this.__simanNet={method,url,headers:{}};return oldOpen.call(this,method,url,...rest)};
XMLHttpRequest.prototype.setRequestHeader=function(k,v){if(this.__simanNet)this.__simanNet.headers[k]=v;return oldSet.call(this,k,v)};
XMLHttpRequest.prototype.send=function(body){let obs;try{const d=this.__simanNet||{};obs=observe(d.url,d.method,d.headers,body)}catch{}if(obs)this.addEventListener('load',()=>{try{traceNet(obs,this.status);if(this.status<200||this.status>=300)return;const data=this.responseType==='json'?this.response:(!this.responseType||this.responseType==='text')?JSON.parse(this.responseText):null;receive(data,obs.url)}catch{}},{once:true});return oldSend.call(this,body)};
function templates(k){return [...requests.values()].filter(x=>x.kind===k)};
function withId(template,id){let url=new URL(template.url),body=template.body,changed=false;
 const keys=provider==='claude'?['chat_conversation_uuid','conversation_uuid','conversationId','chatId']:['deploymentConversationId','conversationId','chatSessionId','sessionId'];
 for(const key of keys)if(url.searchParams.has(key)){url.searchParams.set(key,id);changed=true}
 if(provider==='claude'){const m=url.pathname.match(/(\/chat_conversations\/)[\w-]+/);if(m){url.pathname=url.pathname.replace(/(\/chat_conversations\/)[\w-]+/,'$1'+encodeURIComponent(id));changed=true}}
 if(body){try{const params=new URLSearchParams(body);for(const key of keys)if(params.has(key)){params.set(key,id);changed=true}if(changed)body=params.toString()}catch{}try{const obj=JSON.parse(body);for(const key of keys)if(obj[key]){obj[key]=id;changed=true}if(changed)body=JSON.stringify(obj)}catch{}}
 return changed?{url:url.href,body}:null;
}
async function replay(template,{id}={}){const gap=Date.now()-replayedAt;if(replayedAt&&gap<1450)await new Promise(r=>setTimeout(r,1450-gap));replayedAt=Date.now();const arg=id?withId(template,String(id)):null;if(id&&!arg)throw Error('원문 요청 ID 치환 실패');const opts={method:template.method,credentials:'include',cache:'no-store',headers:new Headers(template.headers)};if(template.method==='POST'&&template.body!=null)opts.body=arg?.body??template.body;
 const u=arg?.url||template.url;if(!normUrl(u))throw Error('다른 사이트 요청 차단');const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),provider==='chatllm'?20000:45000);opts.signal=ctrl.signal;let r;try{r=await nativeFetch(u,opts);if(!r.ok){const e=Error('HTTP '+r.status+' '+new URL(u).pathname);e.status=r.status;e.retryAfterMs=Math.max(0,Number(r.headers.get('Retry-After')||0)*1000);if(r.status===429){e.ratePaused=true;e.retryAt=Date.now()+Math.max(90000,e.retryAfterMs)}throw e}const d=await r.json();receive(d,new URL(u));return d}finally{clearTimeout(timer)}
}
function domList(){const records=[];if(provider!=='chatllm')return records;const seen=new Set();for(const a of document.querySelectorAll('a[href], [data-conversation-id], [data-deployment-conversation-id], [data-chat-session-id]')){
 let u=normUrl(a.href||location.href),id=a.getAttribute('data-conversation-id')||a.getAttribute('data-deployment-conversation-id')||a.getAttribute('data-chat-session-id')||'';
 if(u){for(const k of ['deploymentConversationId','conversationId','chatSessionId','sessionId'])id ||=u.searchParams.get(k)||'';if(!id){const match=u.pathname.match(/(?:conversation|chat|session)\/([\da-f-]{9,})/i);if(match)id=match[1]}}
 if(id.length<7||seen.has(id))continue;seen.add(id);records.push({id,title:(a.getAttribute('title')||a.textContent||'').trim().slice(0,200),projectId:'',projectName:'',url:u?.href||''})
 }return records}
async function scrollLists(){const regions=[...document.querySelectorAll('nav, aside, [role="navigation"], main, section, div')].filter(e=>{try{const s=getComputedStyle(e);return ['scroll','auto'].includes(s.overflowY)&&e.scrollHeight>e.clientHeight+100&&e.clientWidth>120}catch{return false}}).sort((a,b)=>a.clientWidth-b.clientWidth).slice(0,9);
 for(const el of regions){let start=el.scrollTop,prev=-1;el.scrollTop=0;for(let i=0;i<85;i++){if(el.scrollTop===prev)break;prev=el.scrollTop;el.scrollTop+=Math.max(200,el.clientHeight*.8);await new Promise(r=>setTimeout(r,45))}el.scrollTop=start}return domList()}
async function replayListPages(template,{projectIds=[]}={}){
 const requestsToTry=[template],totalMax=12,recognized=new Set(),deadline=Date.now()+48000;
 // Reuse a project selector only if the site itself sent one in the observed request.
 if(projectIds.length){for(const id of projectIds.slice(0,300)){
  let u=new URL(template.url),body=template.body,changed=false;
  for(const k of ['chatllmProjectId','projectId','project_id'])if(u.searchParams.has(k)){u.searchParams.set(k,id);changed=true}
  if(body){try{const p=new URLSearchParams(body);for(const k of ['chatllmProjectId','projectId','project_id'])if(p.has(k)){p.set(k,id);changed=true}if(changed)body=p.toString()}catch{}
   try{const b=JSON.parse(body);for(const k of ['chatllmProjectId','projectId','project_id'])if(b[k]){b[k]=id;changed=true}if(changed)body=JSON.stringify(b)}catch{}}
  if(changed)requestsToTry.push({...template,url:u.href,body});
 }}
 let count=0,errors=[],all=true;
 for(const base of requestsToTry){if(Date.now()>deadline){all=false;break}let current=base,lastSignature='',pages=0,rows=0;
  while(pages++<totalMax){if(Date.now()>deadline){all=false;break}const response=await replay(current);count++;
   const list=enumerate(response,isConv);rows+=list.length;
   const signature=list.slice(0,6).map(cid).join('|');if(signature===lastSignature)break;lastSignature=signature;
   const root=response?.result||response?.data||response;
   const nextCursor=root?.nextCursor||root?.next_cursor||root?.nextPageToken||root?.next_page_token||root?.pageInfo?.endCursor||'';
   let candidate=null;
   if(nextCursor){const u=new URL(current.url);const key=u.searchParams.has('nextPageToken')?'nextPageToken':u.searchParams.has('pageToken')?'pageToken':u.searchParams.has('cursor')?'cursor':root?.nextPageToken||root?.next_page_token?'pageToken':'cursor';u.searchParams.set(key,String(nextCursor));candidate={...current,url:u.href}}
   else{const u=new URL(current.url);const offset=u.searchParams.get('offset');const page=u.searchParams.get('page');const limit=Number(u.searchParams.get('limit')||0);const total=Number(root?.totalCount||root?.total||root?.count||0);
    if(offset!=null&&list.length){u.searchParams.set('offset',String(Number(offset)+list.length));candidate={...current,url:u.href}}
    else if(page!=null&&list.length&&(root.has_more===true||root.hasMore===true||list.length>=limit)){u.searchParams.set('page',String(Number(page)+1));candidate={...current,url:u.href}}
    else if(limit>0&&limit<5000&&(root.has_more===true||root.hasMore===true||total>list.length||list.length>=limit)){u.searchParams.set('limit',String(Math.min(5000,Math.max(200,limit*3))));candidate={...current,url:u.href}}
   }
   if(!candidate)break;
   if(pages===totalMax)all=false;
   current=candidate;
  }
 }
 return {requests:count,complete:all,conversations:lists.size,errors};
}
window.__SimanNetworkV155={provider,snapshot:()=>({conversations:[...lists.values()],projects:[...projects].map(([id,name])=>({id,name})),organizations:[...organizations.values()],templates:templates('list').map(x=>x.url),details:[...details.keys()]}),templates, replay,replayListPages,domList,scrollLists,observedDetail:id=>details.get(String(id))||null};
})();
