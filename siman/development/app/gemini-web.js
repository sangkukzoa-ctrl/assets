/* Siman official Gemini web history reader. Read-only same-origin RPC.
   The web protocol is private and may change; fail closed rather than mark missing chats complete. */
(function(G){'use strict';
if(location.hostname!=='gemini.google.com')return;
let requestNumber=100000;
function token(html,key){
 const match=String(html).match(new RegExp('"'+key+'"\\s*:\\s*"([^"]+)"'));
 return match?.[1]||'';
}
function credentials(html){
 const info={at:token(html,'SNlM0e'),bl:token(html,'cfb2h'),sid:token(html,'FdrFJe')};
 if(!info.at||!info.bl)throw Error('Gemini 로그인 페이지에서 웹 세션 토큰을 확인하지 못했습니다.');
 return info;
}
function unframe(text,rpcid){
 let s=String(text||'').replace(/^\)\]\}'\s*/,''),found=[];
 // Batchexecute commonly uses length-prefixed JSON frames.
 for(const line of s.split('\n')){
  const trimmed=line.trim();
  if(!trimmed.startsWith('['))continue;
  try{
   const v=JSON.parse(trimmed);
   function visit(x,depth=0){
    if(depth>8||!Array.isArray(x))return;
    if(x[0]==='wrb.fr' && x[1]===rpcid && typeof x[2]==='string'){found.push(JSON.parse(x[2]));return}
    if(x[0]===rpcid && typeof x[2]==='string'){found.push(JSON.parse(x[2]));return}
    for(const item of x)if(Array.isArray(item))visit(item,depth+1);
   }
   visit(v);
  }catch{}
 }
 if(!found.length){const err=Error('Gemini 웹 응답 프레임 누락: '+rpcid+' (응답 길이 '+s.length+')');err.code='GEMINI_EMPTY_FRAME';throw err;}
 return found[0];
}
function page(payload){
 if(!Array.isArray(payload)||!Array.isArray(payload[2]))throw Error('Gemini 대화 목록 API 응답 배열이 없습니다');
 const nextToken=typeof payload[1]==='string'&&payload[1].length?payload[1]:null;
 return {rows:list(payload),nextToken};
}
function list(payload){
 if(!Array.isArray(payload?.[2]))throw Error('Gemini 웹 세션 목록 배열이 없습니다.');
 const rows=payload[2];
 const seen=new Set(),out=[];
 for(const entry of rows){
  if(!Array.isArray(entry))continue;
  const full=String(entry[0]||'');
  if(!/^c_[\w-]{8,128}$/.test(full))continue;
  const id=full.slice(2);
  if(seen.has(id))continue;
  seen.add(id);
  out.push({id,title:String(entry[1]||'Gemini 대화 '+id.slice(0,8)).slice(0,220),updated:entry[5]?.[0]||''});
 }
 return out;
}
function history(payload,id,title){
 if(!Array.isArray(payload?.[0]))throw Error('Gemini 웹 원문 응답 구조를 확인할 수 없습니다.');
 const messages=[];
 // Gemini's read RPC returns newest turn first; search results are chronological.
 for(const turn of [...payload[0]].reverse()){
  if(!Array.isArray(turn))continue;
  const ask=turn[2]?.[0]?.[0];
  const response=turn[3],candidates=Array.isArray(response?.[0])?response[0]:[];
  const chosen=typeof response?.[3]==='string'?response[3]:'';
  const candidate=chosen?candidates.find(x=>x?.[0]===chosen):candidates[0];
  if(chosen&&!candidate)throw Error('Gemini 선택한 답변 분기 확인 실패');
  const answer=candidate?.[1]?.[0];
  if(typeof ask==='string'&&ask.trim())messages.push({index:messages.length,role:'user',text:ask.trim()});
  if(typeof answer==='string'&&answer.trim())messages.push({index:messages.length,role:'assistant',text:answer.trim()});
 }
 return G.SimanCore.record('gemini',id,title,messages,{
  url:'https://gemini.google.com/app/'+encodeURIComponent(id),
  complete:messages.length>0&&payload[0].length<10000,
  expected:messages.length,source:'gemini-web-rpc'});
}
async function webRequest(url,options={}){
 const control=new AbortController(),timer=setTimeout(()=>control.abort(),45000);
 try{
  const response=await fetch(url,{credentials:'include',redirect:'error',cache:'no-store',signal:control.signal,...options});
  if(!response.ok){const e=Error('Gemini 웹 HTTP '+response.status);e.status=response.status;
   const h=response.headers.get('Retry-After');e.retryAfterMs=h?Math.max(0,Number(h)*1000):0;
   throw e}
  return await response.text();
 }finally{clearTimeout(timer)}
}
async function start(){
 const html=await webRequest(location.origin+'/app');
 const info=credentials(html);return info;
}
async function rpc(info,rpcid,body){
 if(!['MaZiqc','hNvQHb'].includes(rpcid))throw Error('읽기 전용 Gemini 웹 함수만 허용');
 const query=new URLSearchParams({rpcids:rpcid,'source-path':'/app',bl:info.bl,rt:'c',_reqid:String(requestNumber+=100000)});
 if(info.sid)query.set('f.sid',info.sid);
 const params=new URLSearchParams({'f.req':JSON.stringify([[[rpcid,JSON.stringify(body),null,'generic']]]),at:info.at});
 const result=await webRequest(location.origin+'/_/BardChatUi/data/batchexecute?'+query,{
  method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'},body:params});
 return unframe(result,rpcid);
}
G.SimanGeminiWeb={start,rpc,list,page,history,unframe,credentials};
})(globalThis);
