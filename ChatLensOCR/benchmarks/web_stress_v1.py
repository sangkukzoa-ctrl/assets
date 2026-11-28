# -*- coding: utf-8 -*-
"""Development-only perturbation of frozen public WebCorpus, not new live pages."""
import argparse, collections, hashlib, io, json, math, unicodedata
from pathlib import Path
from PIL import Image,ImageOps

MANIFEST_SHA='3e48fe81b693374a3fb76569d83214a8bc1be9600c207140301b3df9d7c6f8ad'
CONDITIONS=('small75','large125','jpeg50','inverted')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def norm(s):return ' '.join(unicodedata.normalize('NFC',s).split())
def dist(a,b):
    old=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        new=[i]
        for j,y in enumerate(b,1):new.append(min(old[j]+1,new[j-1]+1,old[j-1]+(x!=y)))
        old=new
    return old[-1]
def write(path,obj):Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def transform(img,condition):
    if condition in ('small75','large125'):
        factor=.75 if condition=='small75' else 1.25
        return img.resize(tuple(max(1,round(x*factor)) for x in img.size),Image.Resampling.LANCZOS)
    if condition=='jpeg50':
        buf=io.BytesIO();img.save(buf,format='JPEG',quality=50,subsampling=2);buf.seek(0)
        with Image.open(buf) as decoded:return decoded.convert('RGB')
    if condition=='inverted':return ImageOps.invert(img)
    raise ValueError(condition)

def prepare(corpus,out):
    corpus,out=Path(corpus),Path(out)
    assert sha(corpus/'manifest.json')==MANIFEST_SHA
    src=json.loads((corpus/'manifest.json').read_text(encoding='utf-8'))
    dev=[x for x in src['records'] if x['split']=='development']
    assert src['complete'] and len(src['records'])==30 and len(dev)==21
    (out/'images').mkdir(parents=True,exist_ok=False);rows=[]
    for r in dev:
        f=corpus/'images'/r['filename'];assert sha(f)==r['sha256']
        assert hashlib.sha256(r['raw_inner_text'].encode()).hexdigest()==r['text_sha256']
        assert norm(r['raw_inner_text'])==r['text']
        with Image.open(f) as image:
            img=image.convert('RGB')
            for c in CONDITIONS:
                name=f'{f.stem}_{c}.png';dest=out/'images'/name
                transform(img,c).save(dest)
                rows.append({'filename':name,'source':r['filename'],'source_sha256':r['sha256'],'source_url':r['source_url'],'condition':c,'text':r['text'],'sha256':sha(dest)})
    assert len(rows)==84 and len({r['filename'] for r in rows})==84
    write(out/'manifest.json',{'source_manifest_sha256':MANIFEST_SHA,'development_only':True,'records':rows})

def score(root,old,new,out):
    root=Path(root);m=json.loads((root/'manifest.json').read_text(encoding='utf-8'));r=m['records'];assert m['source_manifest_sha256']==MANIFEST_SHA and m['development_only'] and len(r)==84
    keys={x['filename'] for x in r}
    def load(path,version):
        a=[json.loads(x) for x in Path(path).read_text(encoding='utf-8-sig').splitlines() if x.strip()]
        assert len(a)==len(keys) and {x['filename'] for x in a}==keys
        assert all(not x['failed'] and x['settings']==['자동','한국어',True,'모그리',version] and math.isfinite(x['elapsed_seconds']) for x in a)
        return {x['filename']:x for x in a}
    a,b=load(old,'0.5.0'),load(new,'0.5.1-rc.1')
    rows=[]
    for g in r:
        n=g['filename'];x,y=a[n],b[n];assert sha(root/'images'/n)==g['sha256']==x['sha256']==y['sha256']
        rows.append({'filename':n,'condition':g['condition'],'chars':len(g['text']),'old_errors':dist(g['text'],norm(x['result'])),'new_errors':dist(g['text'],norm(y['result'])),'old_seconds':x['elapsed_seconds'],'new_seconds':y['elapsed_seconds'],'mode_changed':x['mode']!=y['mode'],'rescued':any(t.get('type')=='paragraph_pixel_rescue' for t in y['messages'])})
    def agg(rs):
        n=sum(x['chars'] for x in rs);a=sum(x['old_errors'] for x in rs);b=sum(x['new_errors'] for x in rs)
        return {'count':len(rs),'chars':n,'old_errors':a,'new_errors':b,'old_cer':a/n,'new_cer':b/n,'improved':sum(x['new_errors']<x['old_errors'] for x in rs),'equal':sum(x['new_errors']==x['old_errors'] for x in rs),'worse':sum(x['new_errors']>x['old_errors'] for x in rs),'rescued':sum(x['rescued'] for x in rs),'old_seconds':sum(x['old_seconds'] for x in rs),'new_seconds':sum(x['new_seconds'] for x in rs)}
    s={'development_only':True,'all':agg(rows),'by_condition':{c:agg([x for x in rows if x['condition']==c]) for c in CONDITIONS},'rows':rows}
    write(out,s);print(json.dumps({k:v for k,v in s.items() if k!='rows'},ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
    a=s.add_parser('prepare');a.add_argument('corpus');a.add_argument('out')
    b=s.add_parser('score');b.add_argument('root');b.add_argument('old');b.add_argument('new');b.add_argument('out')
    v=p.parse_args()
    assert dist('가나다','가마')==2
    if v.cmd=='prepare':prepare(v.corpus,v.out)
    else:score(v.root,v.old,v.new,v.out)
