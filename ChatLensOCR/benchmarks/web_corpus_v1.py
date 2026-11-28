# -*- coding: utf-8 -*-
"""Live public-domain web captures and frozen OCR comparison, no private data."""
import argparse, hashlib, json, os, random, re, time, unicodedata
from pathlib import Path
from urllib.parse import quote, urlsplit

SEED=20261128
TITLES='''대한민국헌법 (제10호)|헌법재판소법|국회사무처법|국회도서관법|국회예산정책처법|민법|정부조직법|민사소송법|상법|형법|형사소송법|저작권법|특허법|상표법|국어기본법|교육기본법|소비자기본법|전기통신기본법|출입국관리법|고용정책 기본법|국회법|제조물책임법|주민소환에 관한 법률|법학전문대학원 설치·운영에 관한 법률|사립학교법|초·중등교육법|소 및 쇠고기 이력추적에 관한 법률|남녀고용평등과 일·가정 양립 지원에 관한 법률|기상법|실용신안법|디자인보호법|한국도로공사법|생명윤리법|문화재보호법|먹는물관리법|약관의 규제에 관한 법률|국민의 형사재판 참여에 관한 법률|정보통신망 이용촉진 및 정보보호등에 관한 법률|국정감사 및 조사에 관한 법률|근로기준법|항공보안법|국가재정법|행정절차법|지방자치법|국가공무원법|지방공무원법|전자정부법|개인정보 보호법|농지법|농업·농촌 및 식품산업 기본법|건축법|도로법|도로교통법|환경정책기본법|산림기본법|도서관법|박물관 및 미술관 진흥법|재난 및 안전관리 기본법|식품위생법|공공기관의 정보공개에 관한 법률|공공기관의 운영에 관한 법률|국가통계법|통계법'''.split('|')
SELECTOR='#mw-content-text .mw-parser-output p, #mw-content-text .mw-parser-output li, #mw-content-text .mw-parser-output dd'
ELIGIBLE=r'''els => els.flatMap((e,i)=>{
  if(e.closest('table,.navbox,.metadata,.ambox,.hatnote,.mw-references-wrap,.references,.toc') || e.querySelector('p,li,dd,ul,ol,dl,table,img,svg,math,button,input,.reference,.mw-editsection')) return [];
  const s=getComputedStyle(e), r=e.getBoundingClientRect(), t=e.innerText||'';
  if(s.display==='none'||s.visibility!=='visible'||s.opacity!=='1'||s.textTransform!=='none'||s.listStylePosition==='inside'||r.width<220||r.height<12||r.height>450||e.scrollWidth>e.clientWidth+2)return [];
  if(['::before','::after'].some(p=>!['normal','none','""'].includes(getComputedStyle(e,p).content)))return [];
  const txt=t.replace(/\s+/g,' ').trim();
  if(txt.length<65||txt.length>330||(txt.match(/[가-힣]/g)||[]).length<35||!(/^(제\s*\d+\s*조|[①-⑳]|\d+\.)/.test(txt)))return [];
  const range=document.createRange();range.selectNodeContents(e);
  if([...range.getClientRects()].some(b=>b.width>0&&(b.left<r.left-1||b.right>r.right+1||b.top<r.top-1||b.bottom>r.bottom+1)))return [];
  return [{i,text:t,width:r.width,height:r.height}];
})'''

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s): return ' '.join(unicodedata.normalize('NFC',s).split())
def nospace(s): return ''.join(norm(s).split())
def distance(a,b):
    if len(a)<len(b): a,b=b,a
    row=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        nxt=[i]
        for j,y in enumerate(b,1): nxt.append(min(row[j]+1,nxt[-1]+1,row[j-1]+(x!=y)))
        row=nxt
    return row[-1]
def dump(path,obj): Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def browser(p):
    args={'headless':True,'args':['--no-sandbox']}
    if os.environ.get('CHROMLENS_CHROMIUM'):args['executable_path']=os.environ['CHROMLENS_CHROMIUM']
    return p.chromium.launch(**args)
def candidates(page): return page.locator(SELECTOR).evaluate_all(ELIGIBLE)
def snap(page,entry,path):
    el=page.locator(SELECTOR).nth(entry['i']);el.scroll_into_view_if_needed(timeout=10000)
    page.evaluate('document.fonts.ready')
    if el.inner_text()!=entry['text']:raise ValueError('DOM text changed before capture')
    el.screenshot(path=str(path),animations='disabled',scale='css',timeout=15000)
    if el.inner_text()!=entry['text']:raise ValueError('DOM text changed after capture')

def capture(out,seed=SEED):
    from playwright.sync_api import sync_playwright
    out=Path(out);(out/'images').mkdir(parents=True,exist_ok=False)
    rng=random.Random(seed);titles=list(dict.fromkeys(TITLES));rng.shuffle(titles)
    records=[];failures=[];seen=set();texts=set()
    with sync_playwright() as p, browser(p) as b:
        for title in titles:
            if len(records)==30:break
            index=len(records);width=rng.choice([1024,1280,1440]);height=900
            context=b.new_context(viewport={'width':width,'height':height},locale='ko-KR',user_agent='ChatLensOCR-PublicDomainBenchmark/1.0 (educational OCR research; sequential one-page captures)')
            page=context.new_page();url='https://ko.wikisource.org/wiki/'+quote(('대한민국_'+title if not title.startswith('대한민국헌법') else title).replace(' ','_'))
            path=out/'images'/f'web_{index+1:02d}.png'
            try:
                response=page.goto(url,wait_until='domcontentloaded',timeout=30000)
                if not response or response.status!=200 or urlsplit(page.url).hostname!='ko.wikisource.org':raise ValueError('not an eligible live page')
                page.evaluate('document.fonts.ready')
                content=page.locator('#mw-content-text').inner_text(timeout=10000)
                if '퍼블릭 도메인' not in content or '제7조' not in content:raise ValueError('public-domain notice absent')
                revision=page.evaluate("() => window.mw?.config?.get('wgRevisionId') || null")
                canonical=page.url.split('#')[0];title_actual=page.locator('#firstHeading').inner_text(timeout=10000)
                if canonical in seen:raise ValueError('duplicate page')
                options=[q for q in candidates(page) if norm(q['text']) not in texts]
                if not options:raise ValueError('no eligible visible legal body block')
                entry=rng.choice(options);snap(page,entry,path)
                records.append({'filename':path.name,'source_url':canonical,'title':title_actual,'revision':revision,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'viewport':[width,height],'browser_version':b.version,'dom_index':entry['i'],'raw_inner_text':entry['text'],'text':norm(entry['text']),'sha256':sha(path),'text_sha256':hashlib.sha256(entry['text'].encode()).hexdigest(),'license':'Korean law text, public-domain notice (Copyright Act art. 7); source attribution retained','capture_kind':'live_dom_element_screenshot','split':'pending'})
                seen.add(canonical);texts.add(norm(entry['text']));print('Captured',index+1,title_actual,flush=True)
            except Exception as e:
                path.unlink(missing_ok=True);failures.append({'title':title,'url':url,'error':str(e)[:400]});print('Skip',title,str(e)[:120],flush=True)
            finally:context.close();time.sleep(1.1)
    # Randomize document groups independently of capture order; each source is unique.
    order=list(range(len(records)));random.Random(seed+1).shuffle(order)
    hold=set(order[:9])
    for i,row in enumerate(records):row['split']='holdout' if i in hold else 'development'
    dump(out/'manifest.json',{'version':1,'seed':seed,'expected':30,'records':records,'failures':failures,'complete':len(records)==30})
    if len(records)!=30:raise RuntimeError(f'Only {len(records)}/30 live captures; do not substitute synthetic samples')

def score(corpus,audit,output,version):
    corpus=Path(corpus);manifest=json.loads((corpus/'manifest.json').read_text(encoding='utf-8'));records=manifest['records']
    if not manifest['complete'] or len(records)!=30:raise ValueError('incomplete corpus')
    byname={r['filename']:r for r in records}
    if len(byname)!=30 or len({r['source_url'] for r in records})!=30:raise ValueError('duplicate capture')
    if sorted(r['split'] for r in records)!=['development']*21+['holdout']*9:raise ValueError('split')
    rows={}
    for line in Path(audit).read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():continue
        r=json.loads(line);name=r['filename']
        if name in rows or name not in byname:raise ValueError('duplicate or unexpected record')
        gt=byname[name];expected=gt['sha256']
        if r['failed'] or not isinstance(r['result'],str) or r['sha256'].lower()!=expected or sha(corpus/'images'/name)!=expected:raise ValueError('failed or mismatched record: '+name)
        if r['settings'][-1]!=version:raise ValueError('wrong executable version')
        if hashlib.sha256(gt['raw_inner_text'].encode()).hexdigest()!=gt['text_sha256'] or norm(gt['raw_inner_text'])!=gt['text']:raise ValueError('GT mismatch')
        a,b=gt['text'],norm(r['result']);rows[name]={'filename':name,'split':gt['split'],'literal_chars':len(a),'literal_errors':distance(a,b),'nonspace_chars':len(nospace(a)),'nonspace_errors':distance(nospace(a),nospace(b)),'exact':a==b,'mode':r['mode'],'seconds':r['elapsed_seconds'],'output':r['result']}
    if len(rows)!=30:raise ValueError('missing audit rows')
    def aggregate(group):
        return {'count':len(group),'exact':sum(x['exact'] for x in group),'literal_cer':sum(x['literal_errors'] for x in group)/sum(x['literal_chars'] for x in group),'nonspace_cer':sum(x['nonspace_errors'] for x in group)/sum(x['nonspace_chars'] for x in group),'literal_errors':sum(x['literal_errors'] for x in group),'literal_chars':sum(x['literal_chars'] for x in group),'seconds_sum':sum(x['seconds'] for x in group)}
    allrows=list(rows.values());report={'version':version,'manifest_sha256':sha(corpus/'manifest.json'),'all':aggregate(allrows),'development':aggregate([x for x in allrows if x['split']=='development']),'holdout':aggregate([x for x in allrows if x['split']=='holdout']),'development_rows':[x for x in allrows if x['split']=='development']}
    dump(output,report);print(json.dumps({k:report[k] for k in ['all','development','holdout']},ensure_ascii=False),flush=True)

def selftest():
    from playwright.sync_api import sync_playwright
    import tempfile
    assert distance('abc','adc')==1 and distance('','한글')==2 and norm('가\n  나')=='가 나'
    with tempfile.TemporaryDirectory() as d, sync_playwright() as p, browser(p) as b:
        page=b.new_page(viewport={'width':1000,'height':700})
        text='제1조(시험) '+('검증용으로 새로 작성한 문장을 화면에서 캡처하고 원문과 비교한다. '*3).strip()
        page.set_content('<div id="mw-content-text"><div class="mw-parser-output"><p>'+text+'</p><p>짧은 글</p><ul><li>'+text+'<ul><li>하위 항목</li></ul></li></ul><table><tr><td><p>'+text+'</p></td></tr></table></div></div>')
        page.evaluate('document.fonts.ready');q=candidates(page);assert len(q)==1,q
        path=Path(d)/'fixture.png';snap(page,q[0],path);assert path.stat().st_size>500 and norm(q[0]['text'])==text
    print('Synthetic DOM capture and edit-distance selftest PASS (not live corpus)')
if __name__=='__main__':
    a=argparse.ArgumentParser();sub=a.add_subparsers(dest='cmd',required=True)
    c=sub.add_parser('capture');c.add_argument('out');c.add_argument('--seed',type=int,default=SEED)
    s=sub.add_parser('score');s.add_argument('corpus');s.add_argument('audit');s.add_argument('output');s.add_argument('--version',required=True)
    sub.add_parser('selftest');v=a.parse_args()
    if v.cmd=='capture':capture(v.out,v.seed)
    elif v.cmd=='score':score(v.corpus,v.audit,v.output,v.version)
    else:selftest()
