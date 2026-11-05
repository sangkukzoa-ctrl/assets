# -*- coding: utf-8 -*-
"""Fault-isolated analysis of multiple screenshots.

One exception must not discard all preceding results or stop subsequent files.
The full traceback is stored locally in the debug log, not pasted into the
primary OCR output.
"""
from debuglog_v0372 import note, exception, context, clear_context

def analyze_batch(items, settings, icons, analyzer=None):
    if analyzer is None:
        from layout_v2 import analyze as analyzer
    results=[]
    selected_mode,language,precise,world=settings
    for index,(name,img) in enumerate(items,1):
        width,height=img.size if img is not None else (0,0)
        context(filename=name,size=(width,height),index=index,mode=selected_mode,
                language=language,precise=bool(precise))
        note("image_analysis_start")
        try:
            if img is None or width<=0 or height<=0:
                raise ValueError("Empty or invalid input image")
            detected,output,hits,meta,rows,raw=analyzer(
                img,selected_mode,language,precise,world,icons)
            results.append({"filename":name,"mode":detected,"result":output,
                            "ocr_lines":raw,"messages":meta,"icons":hits,
                            "rows":rows,"failed":False})
            note("image_analysis_success",detected=detected,ocr_lines=len(raw))
        except Exception as error:
            exception("image_analysis_failure",error)
            results.append({"filename":name,"mode":"오류",
                            "result":"[이 이미지의 분석이 실패했습니다.]\n"
                                     "다른 이미지는 계속 분석합니다.\n"
                                     "상세 내역은 [디버그 로그] → [로그 복사]에서 확인하세요.",
                            "ocr_lines":[],"messages":[{"error":str(error),
                                                         "type":type(error).__name__}],
                            "icons":[],"rows":[],"failed":True})
        finally:
            clear_context()
    note("batch_analysis_complete",total=len(results),
         failed=sum(bool(v["failed"]) for v in results))
    return results

def regression():
    from PIL import Image
    class Icons:pass
    calls=[]
    def stub(img,mode,language,precise,world,icons):
        calls.append(img.size)
        if len(calls)==2:raise RuntimeError("synthetic per-image crash")
        return "범용","OK",[],[],[],[]
    images=[("one.png",Image.new("RGB",(100,50),"white")),
            ("two.png",Image.new("RGB",(80,60),"white")),
            ("three.png",Image.new("RGB",(90,40),"white"))]
    out=analyze_batch(images,("자동","한국어",True,"모그리"),Icons(),stub)
    assert len(out)==3 and [v["failed"] for v in out]==[False,True,False]
    assert [v["result"] for v in out][0]=="OK"
    return True
