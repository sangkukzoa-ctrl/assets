# -*- coding: utf-8 -*-
"""Pixel-backed OCR second opinions for Korean FFXIV dialogue.

Every candidate comes from the original image pixels. The existing speaker
and chat-channel header are never overwritten by semantic completion.
No user screenshot, private name, or original chat log is bundled.
"""
import difflib
import re
import numpy as np
from PIL import Image

_KOR=re.compile(r'[가-힣]')
_LATIN=re.compile(r'[A-Za-z]{2,}')
_UNLIKELY=re.compile(r'(?<=[가-힣])[\|©€¤@{}\d](?=[가-힣])')
_ENDINGS=('다는걸','다는게','습니다','했어','었어','이에요','했어요','는데','니까',
          '거든','잖아','네요','이에','한테','까지','으로','에서','에게','부터','더라')
_FAMILIAR=frozenset(('다시금','더구나','그러나','아무튼','그런데','따라서','게다가',
                    '대만판','일본판','한정판','중국판'))
_PARTICLES=('은','는','이','가','을','를','에','의','도','만','와','과','로')

def _quality(word):
    h=len(_KOR.findall(word))
    latin=len(_LATIN.findall(word))
    bad=len(_UNLIKELY.findall(word))
    noise=len(re.findall(r'[^가-힣ㄱ-ㅎㅏ-ㅣA-Za-z0-9\s.,!?~ㅋㅎㅠㅜ]',word))
    q=1.8*h - 3.5*latin - 5*bad - 1.5*noise
    if h>=2 and any(word.endswith(s) for s in _ENDINGS):q+=2.4
    if word in _FAMILIAR:q+=2.5
    return q

def _pick_word(old,alts):
    # Do not splice unrelated fragments merely because they share token index.
    alts=[x for x in alts if (len(_KOR.findall(old))<2
        or (min(len(x),len(old))/max(1,max(len(x),len(old)))>=.65
            and (difflib.SequenceMatcher(None,x,old).ratio()>=.45
                 or (x in _FAMILIAR and difflib.SequenceMatcher(None,x,old).ratio()>=.28))))]
    opts=[x for x in [old]+list(alts) if x]
    if not opts:return old
    for w in opts:
        if opts.count(w)>=2 and _quality(w)>=_quality(old)-1.5:
            return w
    # Grammatical endings may break ties only when another image read
    # physically contains the alternative character.
    for w in opts[1:]:
        if (len(w)==len(old) and len(w)>1 and w[:-1]==old[:-1]
            and w[-1] in _PARTICLES and old[-1] not in _PARTICLES):
            return w
    for word in opts[1:]:
        if (word in _FAMILIAR and len(word)>2
            and difflib.SequenceMatcher(None,word,old).ratio()>=.28
            and any(difflib.SequenceMatcher(None,word,v).ratio()>=.65
                    for v in opts[1:] if v!=word)):
            return word
    preferred=max(opts,key=_quality)
    if preferred!=old and _quality(preferred)>_quality(old)+1.7:
        ratio=difflib.SequenceMatcher(None,preferred,old).ratio()
        if ratio>=.45 or (preferred in _FAMILIAR and ratio>=.28) or len(_KOR.findall(old))<2:
            return preferred
    return old

def _body(value):
    pos=value.find('>')
    return value[pos+1:].strip() if pos>=0 else None

def merge_hypotheses(base,boost,overlay):
    """Merge image-derived text alternatives; keep uncertain raw spans."""
    old=_body(base) if '>' in base else base.strip()
    other=_body(boost) if boost else None
    warm=_body(overlay) if overlay else None
    if not old:return old
    if (len(_KOR.findall(old))==0 and warm and len(_KOR.findall(warm))>=2
        and (len(_LATIN.findall(old))<=1 or bool(re.search(r'\d',old)))):
        return warm
    candidates=[c for c in (other,warm) if c]
    if not candidates:return old
    # Only remove a detached scenery artefact if neither alternative sees it.
    trailing=re.search(r'\s{3,}([＊*~_^.,])$',old)
    if trailing and all(not c.rstrip().endswith(trailing.group(1)) for c in candidates):
        old=old[:trailing.start()].rstrip()
    pieces=old.split()
    if pieces and len(candidates)>=2:
        tail=pieces[-1]
        if len(tail)>=4:
            words=[c.split()[-1] for c in candidates if c.split()]
            for word in words:
                if (word!=tail and len(word)==len(tail)
                    and difflib.SequenceMatcher(None,word,tail).ratio()>=.75
                    and sum(word in c for c in candidates)>=2):
                    old=old[:-len(tail)]+word
                    break
    words=old.split()
    aligned=[c.split() for c in candidates]
    if words and any(len(seq)==len(words) for seq in aligned):
        revised=[]
        for i,w in enumerate(words):
            choices=[seq[i] for seq in aligned if len(seq)==len(words)]
            revised.append(_pick_word(w,choices))
        result=' '.join(revised)
        if result!=old:return result
    # Never generate a new word solely because it seems contextually likely.
    best=max(candidates,key=_quality)
    if (_quality(best)>_quality(old)+7 and
        difflib.SequenceMatcher(None,
            ''.join(_KOR.findall(best)),''.join(_KOR.findall(old))).ratio()>.42):
        return best
    return old

def isolate_warm_chat(crop):
    """Separate the warm green-yellow chat glyphs from the game background."""
    a=np.asarray(crop.convert('RGB')).astype(np.int16)
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    ink=(r>145)&(g>150)&((r-b)>32)
    if ink.sum()<max(35,crop.width//6) or ink.sum()>ink.size*.50:
        return None
    return Image.fromarray(np.where(ink,0,255).astype('uint8'),mode='L')

def refine_ffxiv_dialogue(crop,original,speaker,language):
    """Preserve the original speaker; verify the dialogue with two pixel reads."""
    if language!='한국어' or not speaker or '>' not in original:return original
    source=original.split('>',1)[-1]
    if not _KOR.search(source) and not re.search(r'\d[A-Za-z]|[A-Za-z]\d',source):
        return original # Don't rewrite legitimate English dialogue as Korean.
    ink=isolate_warm_chat(crop)
    if ink is None:return original
    from tess_backend import read
    def enlarge(im):
        return im.resize((im.width*4,im.height*4),Image.Resampling.LANCZOS)
    gray=np.asarray(crop.convert('L')).astype(np.float32)
    boosted=Image.fromarray(np.uint8(np.clip((gray-25)*1.7,0,255)))
    alt,_,_=read(enlarge(boosted),'파판14','한국어',psm=7)
    warm,_,_=read(enlarge(ink),'파판14','한국어',psm=7)
    def valid(text):
        if not text or '>' not in text:return ''
        header=text.split('>',1)[0]
        return text if re.sub(r'\s+','',speaker) in re.sub(r'\s+','',header) else ''
    alt=valid(alt)
    warm=valid(warm)
    if not alt and not warm:return original
    result=merge_hypotheses(original,alt,warm)
    body=source.strip()
    return original.split('>',1)[0]+'>'+' '+result if result and result!=body else original
