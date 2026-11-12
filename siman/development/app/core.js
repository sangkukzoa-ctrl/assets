/* 心眼 (Siman): deterministic conversation extraction. No model calls. */
(function(G){'use strict';
const PROVIDERS={chatllm:'ChatLLM',chatgpt:'ChatGPT',claude:'Claude',gemini:'Gemini',deepseek:'DeepSeek',grok:'Grok'};
const clean=(x)=>String(x??'').normalize('NFKC').toLocaleLowerCase();
const val=(o,keys)=>{for(const k of keys){if(o&&o[k]!=null&&o[k]!=='')return o[k]}return null};
function providerFromUrl(s){try{const h=new URL(s).hostname;if(h==='chatgpt.com'||h==='chat.openai.com')return 'chatgpt';if(h==='claude.ai')return 'claude';if(h==='apps.abacus.ai'||h.endsWith('.abacus.ai'))return 'chatllm';if(h==='gemini.google.com')return 'gemini';if(h==='chat.deepseek.com')return 'deepseek';if(h==='grok.com'||h==='x.com')return 'grok';}catch{}return ''}
function sourceUrl(p,id,proposed=''){if(proposed){try{let u=new URL(proposed);if(u.protocol==='https:'&&providerFromUrl(u.href)===p && !/\/api\//.test(u.pathname)){
    if(p==='chatllm'){const params=['deploymentConversationId','conversationId','chatSessionId','chatId'].map(k=>u.searchParams.get(k));if(params.includes(String(id))||u.pathname.split('/').includes(String(id)))return u.href;}
    else if(u.href.includes(encodeURIComponent(String(id))))return u.href;
   }}catch{}}
 if(p==='chatgpt'&&/^[a-f0-9-]{8,80}$/i.test(id))return 'https://chatgpt.com/c/'+id;
 if(p==='claude'&&/^[a-f0-9-]{8,80}$/i.test(id))return 'https://claude.ai/chat/'+id;
 if(p==='deepseek'&&/^[a-z0-9-]{8,100}$/i.test(id))return 'https://chat.deepseek.com/a/chat/s/'+id;
 return '';
}
function textFrom(obj,d=0){if(d>12||obj==null)return '';if(typeof obj==='string')return obj;if(Array.isArray(obj))return obj.map(x=>textFrom(x,d+1)).filter(Boolean).join('\n');if(typeof obj!=='object')return '';
 for(const k of ['text','markdown','outputText','responseText','textContent','value'])if(typeof obj[k]==='string'&&obj[k].trim())return obj[k];
 for(const k of ['parts','segments','responseSegments','response_segments','content','message','data','response','textSegments','blocks'])if(obj[k]){let t=textFrom(obj[k],d+1);if(t)return t;}return ''}
function msg(m,i){if(!m)return null;let r=String(m.role||m.sender||m.author?.role||m.messageRole||(m.isUser===true?'user':m.isUser===false?'assistant':'unknown')).toLowerCase();if(r==='human')r='user';if(['bot','ai','model','agent'].includes(r))r='assistant';let text=textFrom(m),idx=Number(m.index??m.conversationSequenceNumber??i);return text.trim()?{index:Number.isFinite(idx)?idx:i,role:r||'unknown',text,uid:String(m.uuid||m.id||'')}:null}
function record(provider,id,title,messages,opts={}){const m=(messages||[]).map(msg).filter(Boolean);return {key:provider+':'+id,id:String(id),provider,title:String(title||'제목 없는 대화'),url:sourceUrl(provider,String(id),opts.url),projectId:String(opts.projectId||''),projectName:String(opts.projectName||''),updated:String(opts.updated||''),messages:m,complete:opts.complete===true,expected:Number(opts.expected||0),source:opts.source||'api',storedAt:new Date().toISOString()}}
function chatgpt(obj){let id=String(obj.id||obj.conversation_id||'');if(!id)return null;let m=[];if(obj.mapping&&typeof obj.mapping==='object'){
 let nodes=Object.values(obj.mapping).filter(n=>n?.message);
 nodes.sort((a,b)=>Number(a.message?.create_time||0)-Number(b.message?.create_time||0));
 m=nodes.map((n,i)=>{const a=n.message,content=a.content;return msg({index:i,role:a.author?.role,text:textFrom(content),uuid:a.id})}).filter(Boolean);
 }else if(Array.isArray(obj.messages))m=obj.messages.map(msg).filter(Boolean);
 return record('chatgpt',id,obj.title,m,{url:obj.url,projectId:obj.project_id||obj.project_id_str,projectName:obj.project_name,updated:obj.update_time||obj.updated_at,complete:m.length>0,expected:m.length,source:'chatgpt'});
}
function claude(obj){let id=String(obj.uuid||obj.conversation_uuid||obj.id||'');if(!id)return null;let a=obj.chat_messages||obj.messages||obj.conversation?.chat_messages||[];if(!Array.isArray(a))a=[];
 let messages=a.map((v,i)=>msg({...v,role:v.sender||v.role,index:i,text:textFrom(v.content)||v.text||''},i)).filter(Boolean);
 return record('claude',id,obj.name||obj.title||obj.summary,messages,{url:obj.url,projectId:obj.project_uuid||obj.project_id,projectName:obj.project_name,updated:obj.updated_at||obj.created_at,complete:messages.length>0,expected:messages.length,source:'claude'});
}
function pickArray(obj,depth=0){if(depth>8||!obj||typeof obj!=='object')return [];if(Array.isArray(obj)){if(obj.length&&obj.some(x=>x&&typeof x==='object'&&('role'in x||'isUser'in x||'sender'in x||'messageRole'in x||'conversationSequenceNumber'in x)))return obj;for(const v of obj){const r=pickArray(v,depth+1);if(r.length)return r}return []}
 for(const k of ['history','messages','events','conversationEvents','deploymentConversationEvents','chatHistory','chat_messages','items','result','data']){if(obj[k]){let a=pickArray(obj[k],depth+1);if(a.length)return a}}return []}
function chatllm(obj,idHint=''){const root=obj?.result||obj?.data||obj||{};let id=String(val(root,['deploymentConversationId','conversationId','chatSessionId','id'])||idHint);if(!id)return null;let a=pickArray(root),m=a.map(msg).filter(Boolean);
 // totalEvents can include internal/intermediate events and is NOT a user-visible turn count.
 // A detail response with no continuation marker is treated as a complete detail page;
 // explicit continuation indicators still mark the transcript as partial.
 const page=root.pagination||root.pageInfo||{};
 const hasMore=[root.hasMore,root.has_more,root.hasNextPage,root.has_next_page,page.hasMore,page.has_more,page.hasNextPage,page.has_next_page]
   .some(x=>x===true||x===1||x==='true');
 const nextCursor=root.nextCursor||root.next_cursor||root.nextPageToken||root.next_page_token||(page.hasNextPage===true?page.endCursor:'');
 const isPartial=hasMore||!!nextCursor;
 const expected=isPartial?Math.max(m.length+1,Number(root.totalEvents||root.total_events||0)):m.length;
 return record('chatllm',id,val(root,['deploymentConversationName','name','title'])||'ChatLLM 대화',m,{url:root.conversationUrl||root.url,projectId:root.chatllmProjectId,projectName:root.chatllmProjectName,updated:root.lastEventCreatedAt,expected,complete:m.length>0&&!isPartial,source:'chatllm'});
}
function htmlMessages(html){if(!html||typeof html!=='string'||typeof DOMParser==='undefined')return [];let d=new DOMParser().parseFromString(html,'text/html');d.querySelectorAll('script,style,noscript,svg,template').forEach(n=>n.remove());const out=[];
 for(const n of d.querySelectorAll('[data-message-author-role],[data-role],.chat-message,.message-item,.conversation-turn')){if(n.parentElement?.closest('[data-message-author-role],[data-role],.chat-message,.message-item,.conversation-turn'))continue;const text=(n.innerText||n.textContent||'').trim();if(text)out.push({index:out.length,role:n.getAttribute('data-message-author-role')||n.getAttribute('data-role')||'unknown',text})}
 if(!out.length){for(const n of d.querySelectorAll('pre')){let label=(n.previousElementSibling?.textContent||n.parentElement?.firstElementChild?.textContent||'').slice(0,60).toLowerCase();let text=n.textContent.trim();if(text)out.push({index:out.length,role:/user|human/.test(label)?'user':/assistant|bot|ai/.test(label)?'assistant':'unknown',text})}}
 if(!out.length){let text=(d.body?.textContent||'').trim();if(text)out.push({index:0,role:'unknown',text})}
 return out;
}
function parseImport(data,filename=''){let files=[];if(Array.isArray(data)){for(const x of data){let c=x?.mapping?chatgpt(x):x?.chat_messages?claude(x):x?.deploymentConversationId?chatllm(x):null;if(c&&c.messages.length)files.push(c)}}else if(typeof data==='object'&&data){let arr=data.conversations||data.chats||data.items||data.data;if(Array.isArray(arr))files=parseImport(arr,filename);else{const c=data.mapping?chatgpt(data):data.chat_messages?claude(data):data.deploymentConversationId?chatllm(data):null;if(c?.messages.length)files.push(c)}}return files}
function snippet(str,q,around=115){let norm=clean(str),at=norm.indexOf(clean(q));if(at<0)return str.slice(0,around*2);return (at>around?'…':'')+str.slice(Math.max(0,at-around),Math.min(str.length,at+q.length+around))+(at+q.length+around<str.length?'…':'')}
function find(records,query,filters={},limit=300){const q=clean(query.trim());if(!q)return [];let out=[];for(const r of records){if(filters.provider&&r.provider!==filters.provider)continue;const title=clean(r.title),titleAt=title.indexOf(q);if(titleAt>=0)out.push({key:r.key,provider:r.provider,title:r.title,projectName:r.projectName||'',index:-1,role:'제목',snippet:r.title,url:r.url});
 for(const m of r.messages||[]){if(filters.role&&filters.role!=='all'&&m.role!==filters.role)continue;let t=clean(m.text),at=t.indexOf(q);if(at<0)continue;out.push({key:r.key,provider:r.provider,title:r.title,projectName:r.projectName||'',index:m.index,role:m.role,snippet:snippet(m.text,q),url:r.url,uid:m.uid});if(out.length>=limit)return out}}
 return out}
G.SimanCore={PROVIDERS,clean,providerFromUrl,sourceUrl,textFrom,record,msg,chatgpt,claude,chatllm,htmlMessages,parseImport,find,pickArray};
})(globalThis);
