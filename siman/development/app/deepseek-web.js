/* Siman: independent official DeepSeek WEB (chat.deepseek.com) archive reader.
 * Read-only same-origin calls. Never exports, logs or persists userToken.
 * Completely separate from Abacus/ChatLLM's DeepSeek model.
 */
(function(G){'use strict';
if(location.hostname!=='chat.deepseek.com')return;
function unwrap(payload){
 if(payload?.code!==undefined&&Number(payload.code)!==0)
  throw Error('DeepSeek 웹 응답 오류 코드 '+String(payload.code));
 return payload?.data?.biz_data||payload?.data||payload?.result||payload||{};
}
function readToken(){
 let raw='';try{raw=localStorage.getItem('userToken')||'';}catch{}
 if(!raw)return '';
 try{const parsed=JSON.parse(raw);if(typeof parsed==='string')return parsed;
  return String(parsed?.value||parsed?.token||parsed?.access_token||'');
 }catch{return raw.replace(/^"(.*)"$/,'$1')}
}
function list(payload){
 const biz=unwrap(payload),raw=biz.chat_sessions||biz.sessions||biz.items||[];
 if(!Array.isArray(raw))throw Error('DeepSeek 웹 목록 응답에 chat_sessions 배열 없음');
 const seen=new Set(),rows=[];
 for(const s of raw){
  const id=String(s?.id||s?.chat_session_id||'');
  if(!/^[\w-]{8,100}$/.test(id)||seen.has(id))continue;
  seen.add(id);rows.push({id,title:String(s.title||s.name||'DeepSeek 대화 '+id.slice(0,8)).slice(0,220),updated:s.updated_at||''});
 }
 const cursor=biz.next_cursor||biz.nextCursor||biz.cursor||'';
 return {rows,hasMore:biz.has_more===true||biz.hasMore===true,cursor:String(cursor||''),sourceCount:raw.length};
}
function branch(raw,session){
 const m=Array.isArray(raw)?raw:[];
 const current=session?.current_message_id;
 if(current==null||current==='')return m;
 const byId=new Map(m.filter(x=>x?.message_id!=null).map(x=>[String(x.message_id),x]));
 let node=byId.get(String(current));if(!node)return m;
 const result=[],seen=new Set();
 while(node&&!seen.has(String(node.message_id))){
  seen.add(String(node.message_id));result.push(node);
  node=node.parent_id==null?null:byId.get(String(node.parent_id));
 }
 return result.reverse();
}
function body(m){
 let parts=[];
 if(Array.isArray(m?.fragments)){
  for(const f of m.fragments){
   if(!['REQUEST','RESPONSE'].includes(String(f?.type||'').toUpperCase()))continue;
   const t=typeof f.content==='string'?f.content:typeof f.content?.text==='string'?f.content.text:'';
   if(t.trim())parts.push(t);
  }
 }
 if(parts.length)return parts.join('\n\n').trim();
 const c=m?.content;
 if(typeof c==='string')return c.trim();
 if(typeof c?.text==='string')return c.text.trim();
 if(typeof m?.text==='string')return m.text.trim();
 return '';
}
function history(payload,id,title){
 const biz=unwrap(payload),rows=biz.chat_messages||biz.messages;
 if(!Array.isArray(rows))throw Error('DeepSeek 웹 원문 응답에 chat_messages 배열 없음');
 const current=branch(rows,biz.chat_session||{});
 const messages=[];
 for(const m of current){
  let role=String(m?.role||'').toUpperCase();
  if(role!=='USER'&&role!=='ASSISTANT')continue;
  const text=body(m);if(!text)continue;
  messages.push({index:messages.length,role:role==='USER'?'user':'assistant',text,
   uid:String(m.message_id||'')});
 }
 return G.SimanCore.record('deepseek',id,title,messages,{
  url:'https://chat.deepseek.com/a/chat/s/'+encodeURIComponent(id),
  expected:messages.length,
  complete:messages.length>0&&!biz.has_more&&!biz.next_cursor,
  source:'deepseek-web-api'
 });
}
G.SimanDeepSeekWeb={readToken,list,history,branch,body};
})(globalThis);
