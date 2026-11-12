/* Siman Grok official web archive. Read-only REST endpoints as used by grok.com.
   Fetches only on grok.com with the browser's existing login. No passwords or tokens stored. */
(function(G){'use strict';
if(location.hostname!=='grok.com')return;
const UUID=/^[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}$/i;
const isId=s=>UUID.test(String(s||''));
function validList(raw){
 if(!Array.isArray(raw?.conversations))throw Error('Grok 대화 목록 응답 형식 변경');
 const rows=[];
 for(const item of raw.conversations){
  if(!isId(item?.conversationId))continue;
  rows.push({id:item.conversationId.toLowerCase(),title:String(item.title||'Grok 대화').slice(0,240),
   updated:item.modifyTime||item.createTime||'',projectName:''});
 }
 return {rows,nextPageToken:String(raw.nextPageToken||'')};
}
function activeMessages(meta,nodes,rawResponses,{responseId=''}={}){
 if(!isId(meta?.conversation?.conversationId)||!Array.isArray(nodes?.responseNodes)||!Array.isArray(rawResponses?.responses))
  throw Error('Grok 원문 구조 변경');
 const id=meta.conversation.conversationId.toLowerCase(),title=String(meta.conversation.title||'Grok 대화');
 const responseMap=new Map(rawResponses.responses.filter(x=>isId(x?.responseId)).map(x=>[x.responseId.toLowerCase(),x]));
 const known=nodes.responseNodes.filter(x=>isId(x?.responseId)&&responseMap.has(x.responseId.toLowerCase()));
 if(known.length!==nodes.responseNodes.filter(x=>isId(x?.responseId)).length)
  throw Error('Grok 응답 일부가 누락돼 완결로 저장할 수 없습니다');
 const parents=new Map(),children=new Map(),order=new Map();
 for(const [i,n] of known.entries()){
  const nId=n.responseId.toLowerCase(),parent=isId(n.parentResponseId)?n.parentResponseId.toLowerCase():null;
  parents.set(nId,parent);order.set(nId,i);
  const c=children.get(parent)||[];c.push(nId);children.set(parent,c);
 }
 const newer=(a,b)=>{
  const ta=String(responseMap.get(a)?.createTime||''),tb=String(responseMap.get(b)?.createTime||'');
  return ta===tb?(order.get(a)||0)-(order.get(b)||0):ta.localeCompare(tb)
 };
 const preferred=isId(responseId)?responseId.toLowerCase():null;
 function lineage(end){let path=[],seen=new Set();for(let at=end;at&&!seen.has(at);at=parents.get(at)||null){seen.add(at);path.unshift(at)}return path}
 let leaf;
 if(preferred&&responseMap.has(preferred))leaf=preferred;
 else{
  const leaves=known.map(x=>x.responseId.toLowerCase()).filter(x=>!(children.get(x)?.length));
  leaf=leaves.sort(newer).at(-1);
 }
 if(!leaf)throw Error('Grok 원문 메시지가 없습니다');
 let selected=lineage(leaf);
 if(preferred&&responseMap.has(preferred)){
  const seen=new Set(selected);
  for(let next=[...(children.get(selected.at(-1))||[])].sort(newer).at(-1);next&&!seen.has(next);){
   seen.add(next);selected.push(next);
   next=[...(children.get(next)||[])].sort(newer).at(-1);
  }
 }
 const messages=[];
 for(const responseId of selected){
  const r=responseMap.get(responseId);
  const role=r.sender==='human'||r.sender==='user'?'user':r.sender==='assistant'?'assistant':'unknown';
  // Search the visible answer, not private chain-of-thought or discarded regenerate branches.
  const content=String(r.message||'').replace(/<grok:render\b[^>]*>[\s\S]*?<\/grok:render>/g,'').trim();
  if(content)messages.push({index:messages.length,role,text:content,uid:responseId});
 }
 if(!messages.length)throw Error('Grok 대화에서 검색 가능한 메시지를 찾지 못했습니다');
 const projectName=(meta.conversation.workspaces||[]).map(x=>x?.name).find(x=>typeof x==='string'&&x.trim())||'';
 return G.SimanCore.record('grok',id,title,messages,{
  url:'https://grok.com/c/'+id,updated:meta.conversation.modifyTime||'',
  projectName,complete:true,expected:messages.length,source:'grok-web-rest'});
}
async function getJson(path,{method='GET',body}={}){
 const url=new URL(path,location.origin);
 if(url.origin!==location.origin||!url.pathname.startsWith('/rest/'))
  throw Error('Grok 공식 웹 외 요청 차단');
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),45000);
 try{
  const res=await fetch(url.href,{credentials:'include',cache:'no-store',redirect:'error',method,
   headers:{Accept:'application/json',...(method==='POST'?{'Content-Type':'application/json'}:{}),
    // Grok's web app expects an opaque per-request identifier for some REST paths.
    ...(globalThis.crypto?.randomUUID?{'x-xai-request-id':globalThis.crypto.randomUUID()}:{})},
   ...(body!==undefined?{body:JSON.stringify(body)}:{}),signal:controller.signal});
  if(!res.ok){const err=Error(res.status===401||res.status===403?'Grok 웹 계정 인증 필요 (HTTP '+res.status+')':'Grok HTTP '+res.status);err.status=res.status;err.authRequired=res.status===401||res.status===403;
   const header=res.headers?.get?.('Retry-After'),retry=Number(header);
   err.retryAfterMs=Number.isFinite(retry)&&retry>0?retry*1000:0;throw err}
  const ct=res.headers?.get?.('content-type')||'';
  if(ct.includes('text/html'))throw Error('Grok 로그인 화면 또는 HTML 응답');
  return await res.json();
 }finally{clearTimeout(timer)}
}
async function getDetail(id,{responseId=''}={}){
 if(!isId(id))throw Error('Grok ID 형식이 올바르지 않습니다');
 const base='/rest/app-chat/conversations';
 // Fetch exact relations and all response bodies; no message submission.
 const [meta,nodes]=await Promise.all([
  getJson(base+'_v2/'+encodeURIComponent(id)+'?includeWorkspaces=true&includeTaskResult=true'),
  getJson(base+'/'+encodeURIComponent(id)+'/response-node')]);
 if(!Array.isArray(nodes?.responseNodes))throw Error('Grok 메시지 관계 목록 확인 실패');
 const ids=[...new Set(nodes.responseNodes.map(x=>x.responseId).filter(isId))],responses=[];
 for(let i=0;i<ids.length;i+=100){
  const result=await getJson(base+'/'+encodeURIComponent(id)+'/load-responses',
   {method:'POST',body:{responseIds:ids.slice(i,i+100)}});
  if(!Array.isArray(result?.responses))throw Error('Grok 원문 응답 형식 변경');
  responses.push(...result.responses);
 }
 return activeMessages(meta,nodes,{responses},{responseId});
}
G.SimanGrokWeb={getJson,validList,activeMessages,getDetail,isId};
})(globalThis);
