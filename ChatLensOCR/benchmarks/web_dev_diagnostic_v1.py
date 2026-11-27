# -*- coding: utf-8 -*-
"""Development-only diagnostic: compare installed Windows source OCR variants.
No production edits, no private corpus, no holdout predictions or tuning.
"""
import hashlib,json,sys,time,unicodedata,subprocess
from pathlib import Path
from PIL import Image,ImageOps
import numpy as np
ROOT=Path.cwd()
sys.path.insert(0,str(ROOT/'baseline-src'/'ChatLensOCR'))
from app import recognize,merge_rows
from tess_backend import read,resolve_tesseract_paths

def norm(s):return ' '.join(unicodedata.normalize('NFC',s).split())
def distance(a,b):
    prev=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        row=[i]
        for j,y in enumerate(b,1):row.append(min(prev[j]+1,row[j-1]+1,prev[j-1]+(x!=y)))
        prev=row
    return prev[-1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run():
    corpus=ROOT/'corpus';manifest=json.loads((corpus/'manifest.json').read_text(encoding='utf-8-sig'))
    assert sha(corpus/'manifest.json')=='3e48fe81b693374a3fb76569d83214a8bc1be9600c207140301b3df9d7c6f8ad'
    dev=[r for r in manifest['records'] if r['split']=='development'];assert len(dev)==21
    report=json.loads((ROOT/'gate'/'final-report.json').read_text(encoding='utf-8-sig'))
    base={r['filename']:r['literal_errors'] for r in report['development_rows']}
    assert set(base)=={r['filename'] for r in dev} and sum(base.values())==803
    exe,data=resolve_tesseract_paths();assert exe and data
    provenance={'tesseract':subprocess.check_output([exe,'--version'],text=True,encoding='utf-8',errors='replace').splitlines()[0],
                'kor_sha':sha(Path(data)/'kor.traineddata'),'eng_sha':sha(Path(data)/'eng.traineddata')}
    results=[]
    for r in dev:
        path=corpus/'images'/r['filename'];assert sha(path)==r['sha256']
        img=Image.open(path).convert('RGB');gt=r['text']
        row={'filename':path.name,'reference_chars':len(gt),'baseline_errors':base[path.name],'variants':{}}
        def record(label,func):
            start=time.monotonic();text,boxes,conf=func()
            row['variants'][label]={'text':text,'errors':distance(gt,norm(text)),'seconds':time.monotonic()-start,
                                    'boxes':boxes,'confidence':conf}
        def rapid(im):
            items=recognize(im,'한국어',True)
            return '\n'.join(v['text'] for v in merge_rows(items)),items,None
        record('rapid_source',lambda:rapid(img))
        for scale in (1,2,3):
            variant=img if scale==1 else ImageOps.expand(img.resize((img.width*scale,img.height*scale),Image.Resampling.LANCZOS),border=10*scale,fill='white')
            def tess():
                text,boxes,conf=read(variant,'범용','한국어',psm=6,tess_lang='kor+eng')
                # Preserve native source coordinates; reject words outside the image.
                offset=0 if scale==1 else 10*scale
                valid=[]
                for x in boxes:
                    l,t,rr,bb=x['box'];a=max(0,(l-offset)/scale);b=max(0,(t-offset)/scale);c=min(img.width,(rr-offset)/scale);d=min(img.height,(bb-offset)/scale)
                    if a<c and b<d:valid.append(dict(x,box=[a,b,c,d]))
                return text,valid,conf
            record('tess_scale_'+str(scale),tess)
        results.append(row)
        print(path.name,{k:v['errors'] for k,v in row['variants'].items()},flush=True)
    summary={}
    for label in results[0]['variants']:
        summary[label]={'errors':sum(r['variants'][label]['errors'] for r in results),
                        'improved':sum(r['variants'][label]['errors']<r['baseline_errors'] for r in results),
                        'equal':sum(r['variants'][label]['errors']==r['baseline_errors'] for r in results),
                        'worse':sum(r['variants'][label]['errors']>r['baseline_errors'] for r in results),
                        'seconds_sum':sum(r['variants'][label]['seconds'] for r in results)}
    output={'development_only':True,'reference_chars':sum(r['reference_chars'] for r in results),'baseline_errors':803,
            'provenance':provenance,'summary':summary,'rows':results}
    (ROOT/'windows-dev-diagnostic.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':run()
