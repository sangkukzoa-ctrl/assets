# -*- coding: utf-8 -*-
"""ChatLens OCR - Windows offline standalone application.
Screenshots stay local. Supports FFXIV, KakaoTalk and general documents.
"""
import os, sys, re, json, socket, traceback, threading, queue, uuid
import debuglog_v0372 as debuglog
from pathlib import Path

BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ChatLensOCR"
DATA.mkdir(parents=True, exist_ok=True)
JOBS = {
"gladiator":"검술사","paladin":"나이트","marauder":"도끼술사","warrior":"전사",
"darkknight":"암흑기사","gunbreaker":"건브레이커","conjurer":"환술사",
"whitemage":"백마도사","scholar":"학자","astrologian":"점성술사","sage":"현자",
"pugilist":"격투사","monk":"몽크","lancer":"창술사","dragoon":"용기사",
"rogue":"쌍검사","ninja":"닌자","samurai":"사무라이","reaper":"리퍼",
"viper":"바이퍼","archer":"궁술사","bard":"음유시인",
"machinist":"기공사","dancer":"무도가","thaumaturge":"주술사",
"blackmage":"흑마도사","arcanist":"비술사","summoner":"소환사",
"redmage":"적마도사","pictomancer":"픽토맨서","bluemage":"청마도사",
"carpenter":"목수","blacksmith":"대장장이","armorer":"갑주제작사",
"goldsmith":"보석공예가","leatherworker":"가죽공예가",
"weaver":"재봉사","alchemist":"연금술사","culinarian":"요리사",
"miner":"광부","botanist":"원예가","fisher":"어부"
}
WORLD = re.compile(r"^(.+?)(?:\s*[@＠&＆]\s*([가-힣\w-]{2,24})|\s*\[([가-힣\w-]{2,24})\])$")
HEADER = re.compile(r"^\s*(?:(?:\[(?:파티|부대|자유부대|말하기|연합|링크셸|귓속말)\])\s*)?([^:：]{1,56})\s*[:：]\s*(.*)$")

_ENGINE_CACHE = {}
def engine(language="한국어"):
    if language in _ENGINE_CACHE:
        return _ENGINE_CACHE[language]
    from rapidocr import RapidOCR
    from rapidocr.utils.typings import ModelType, OCRVersion
    settings = {"Det.model_type":ModelType.SMALL, "Det.ocr_version":OCRVersion.PPOCRV6}
    if getattr(sys, "frozen", False):
        settings["Global.model_root_dir"] = str(BASE / "models")
    if language == "일본어":
        settings.update({"Rec.lang_type":"japan","Rec.model_type":ModelType.MOBILE,"Rec.ocr_version":OCRVersion.PPOCRV4})
    else:
        settings.update({"Rec.lang_type":"korean" if language == "한국어" else "en",
                         "Rec.model_type":ModelType.MOBILE,"Rec.ocr_version":OCRVersion.PPOCRV5})
    ocr = RapidOCR(params=settings)
    _ENGINE_CACHE[language] = ocr
    return ocr

def recognize(img, language="한국어", precise=True):
    """Run RapidOCR on safe nonzero pixel dimensions with accurate boxes.

    Long thin text regions are padded/split in ocr_guard_v0372, preventing
    RapidOCR's reduce_max_side from producing 0-pixel dimensions.
    """
    from PIL import Image, ImageEnhance
    from ocr_guard_v0372 import guarded_infer
    if img is None or img.width<=0 or img.height<=0:
        debuglog.warning("recognize_empty_image",size=getattr(img,"size",None))
        return []
    scale = (1.0 if img.height<140 and img.width>=1100
             else min(2.0,max(1.,850/max(1,img.height))) if img.height<850 else 1.)
    enlarged = img.resize(
        (max(1,round(img.width*scale)),max(1,round(img.height*scale))),
        Image.Resampling.LANCZOS) if scale>1 else img
    ocr=engine(language)
    def read_one(picture):
        result=[]
        for item in guarded_infer(ocr,picture):
            x0,y0,x1,y1=item["box"]
            left=max(0,int(x0/scale));top=max(0,int(y0/scale))
            right=min(img.width,int(round(x1/scale)))
            bottom=min(img.height,int(round(y1/scale)))
            if right>left and bottom>top:
                result.append({"text":item["text"],"score":item["score"],
                               "box":(left,top,right,bottom)})
        return result
    found=read_one(enlarged)
    if precise:
        found+=read_one(ImageEnhance.Contrast(enlarged).enhance(1.35))
    found.sort(key=lambda v:-v["score"])
    unique=[]
    for item in found:
        box=item["box"]
        area=max(1,(box[2]-box[0])*(box[3]-box[1]))
        duplicate=False
        for prev in unique:
            p=prev["box"]
            overlap=(max(0,min(box[2],p[2])-max(box[0],p[0]))*
                     max(0,min(box[3],p[3])-max(box[1],p[1])))
            other=max(1,(p[2]-p[0])*(p[3]-p[1]))
            if overlap>.73*min(area,other):
                duplicate=True
                break
        if not duplicate:unique.append(item)
    return sorted(unique,key=lambda v:(v["box"][1]//9,v["box"][0]))


def merge_rows(items):
    rows=[]
    for line in sorted(items,key=lambda q:(q["box"][1]+q["box"][3])/2):
        a=line["box"]; mid=(a[1]+a[3])/2; h=a[3]-a[1]
        row=next((r for r in rows if abs(mid-r[0])<=max(5,h*.48)),None)
        if row: row[1].append(line); row[0]=(row[0]+mid)/2
        else: rows.append([mid,[line]])
    joined=[]
    for _,group in rows:
        group.sort(key=lambda q:q["box"][0])
        sentence=""
        for i,item in enumerate(group):
            b=item["box"]
            if i and b[0]-group[i-1]["box"][2]>max(4,(b[3]-b[1])*.18) and not sentence.endswith((" ","[","(")):
                sentence+=" "
            sentence+=item["text"]
        joined.append({"text":sentence,"box":(min(v["box"][0] for v in group),
            min(v["box"][1] for v in group),max(v["box"][2] for v in group),
            max(v["box"][3] for v in group)),
            "score":sum(v["score"] for v in group)/len(group)})
    return sorted(joined,key=lambda z:z["box"][1])

class Icons:
    def __init__(self):
        import cv2, numpy as np
        self.icons=[]
        for directory in [BASE/"assets"/"jobs",DATA/"job_samples"]:
            if not directory.exists():continue
            for p in directory.glob("*.png"):
                job=JOBS.get(p.stem,p.stem.split("__")[0])
                if not job:continue
                raw=np.fromfile(str(p),np.uint8)
                img=cv2.imdecode(raw,cv2.IMREAD_UNCHANGED)
                if img is None:continue
                if img.ndim==3:img=cv2.cvtColor(img[:,:,:3],cv2.COLOR_BGR2GRAY)
                if min(img.shape)<8:continue
                self.icons.append((job,img))

    def match(self,image,box):
        import cv2, numpy as np
        if not self.icons:return ("",None,0.)
        h=max(12,box[3]-box[1]); center=(box[1]+box[3])/2
        sizes=sorted({min(40,max(12,int(h*x))) for x in (.85,1.05,1.25,1.45)})
        left=max(0,box[0]-int(2.8*max(sizes)))
        right=min(image.width,box[0]+int(.45*h))
        top=max(0,int(center-max(sizes)*1.15))
        bottom=min(image.height,int(center+max(sizes)*1.15))
        if right-left<15 or bottom-top<15:return ("",None,0.)
        patch=np.asarray(image.convert("L"))[top:bottom,left:right]
        patch=cv2.equalizeHist(patch)
        matches={}
        for job,raw in self.icons:
            for size in sizes:
                if size>=min(patch.shape):continue
                template=cv2.equalizeHist(cv2.resize(raw,(size,size)))
                if template.std()<5:continue
                _,score,_,xy=cv2.minMaxLoc(cv2.matchTemplate(patch,template,cv2.TM_CCOEFF_NORMED))
                x,y=xy; mid_y=top+y+size/2
                if abs(mid_y-center)>h*.68 or left+x+size/2>box[0]+.6*h:continue
                weighted=float(score)-.10*abs(mid_y-center)/h
                if job not in matches or weighted>matches[job][0]:
                    matches[job]=(weighted,(left+x,top+y,left+x+size,top+y+size))
        if not matches:return ("",None,0.)
        ranked=sorted(matches.items(),key=lambda a:-a[1][0])
        job,(score,rect)=ranked[0]
        runner=ranked[1][1][0] if len(ranked)>1 else 0.
        if score<.71 or score-runner<.025:return ("",None,score)
        return (job,rect,score)

def describe_sticker(image, rect):
    import numpy as np, cv2
    a=np.asarray(image.convert("RGB").crop(rect))
    if min(a.shape[:2])<4:return "작은 스티커"
    r,g,b=a[a.shape[0]//5:a.shape[0]*4//5,a.shape[1]//5:a.shape[1]*4//5].reshape(-1,3).mean(axis=0)
    palette={"흰색":(235,235,235),"검정색":(25,25,25),"노란색":(245,220,60),
             "빨간색":(230,60,65),"분홍색":(240,165,195),
             "파란색":(80,150,210),"초록색":(90,180,95),"보라색":(155,100,205),
             "회색":(145,145,145),"갈색":(145,95,55)}
    color=min(palette,key=lambda k:np.linalg.norm(np.array([r,g,b])-np.array(palette[k])))
    ratio=a.shape[1]/max(1,a.shape[0])
    shape="가로로 긴" if ratio>1.5 else "세로로 긴" if ratio<.7 else "둥글거나 정사각형에 가까운"
    return f"{color} 계열의 {shape} 이모티콘/스티커"

def format_chat(image,lines,mode,world,icons):
    rows=merge_rows(lines)
    if mode=="자동":
        s=" ".join(r["text"] for r in rows)
        mode="파판14" if any(v in s for v in ["모그리","초코보","[파티]","[부대]","&카벙클"]) else ("카카오톡" if "오전 " in s or "오후 " in s else "범용")
    formatted=[]; hits=[]; metadata=[]
    if mode=="파판14":
        for row in rows:
            m=HEADER.match(row["text"])
            if m:
                name=m.group(1).strip(); server=""
                sm=WORLD.match(name)
                if sm:
                    name=sm.group(1).strip()
                    server=(sm.group(2) or sm.group(3) or "").strip()
                job,icon,confidence=icons.match(image,row["box"])
                if icon:hits.append((icon,job))
                speaker=name+("&"+server if server and server!=world else "")
                formatted.append(f"({job or '직업미확인'}){speaker}: {m.group(2).strip()}")
                metadata.append({"speaker":name,"server":server,"job":job,"confidence":row["score"],"icon_score":confidence})
            elif formatted and not row["text"].startswith("["):
                formatted[-1]+=" "+row["text"]
    elif mode=="카카오톡":
        name=""
        for row in rows:
            s=row["text"].strip()
            if re.fullmatch(r"(오전|오후)\s+\d{1,2}:\d{2}",s):continue
            m=HEADER.match(s)
            if m:name=m.group(1).strip();s=m.group(2).strip()
            if len(s)>0:formatted.append(f"{name+': ' if name else ''}{s}")
            metadata.append({"confidence":row["score"]})
    else:
        for row in rows:formatted.append(row["text"]);metadata.append({"confidence":row["score"]})
    return mode,"\n".join(formatted),hits,metadata,rows

def selftest(outpath):
    info={"app":"ChatLens OCR","frozen":bool(getattr(sys,"frozen",False)),"checks":{},"ok":False}
    try:
        import cv2, numpy, onnxruntime, rapidocr
        from PIL import Image, ImageDraw, ImageFont
        icons=list((BASE/"assets"/"jobs").glob("*.png"))
        info["checks"]["job_icons"]=len(icons)
        from tess_backend import read as tess_read
        tesspath=BASE/"tesseract"/"tesseract.exe"
        info["checks"]["tesseract_binary"]=tesspath.is_file()
        if not tesspath.is_file():raise RuntimeError("Bundled Tesseract missing")
        from layout_v2 import _test_detection
        info["checks"]["pixel_layout"]=bool(_test_detection())
        from explorer_v1 import _synthetic as explorer_synthetic
        from colored_page import _synthetic as color_synthetic
        info["checks"]["file_explorer_rows"]=bool(explorer_synthetic())
        info["checks"]["colored_text_page"]=bool(color_synthetic())
        from shop_grid_v0374 import _synthetic as shop_synthetic
        info["checks"]["shop_card_grid"]=bool(shop_synthetic())
        from ocr_guard_v0372 import regression as guard_regression
        from batch_v0372 import regression as batch_regression
        info["checks"]["resize_guard"]=bool(guard_regression())
        info["checks"]["batch_error_isolation"]=bool(batch_regression())
        if len(icons)<40:raise RuntimeError("Job icon resources missing")
        img=Image.new("RGB",(800,160),"white")
        font_file=Path("C:/Windows/Fonts/arial.ttf")
        font=ImageFont.truetype(str(font_file),40) if font_file.exists() else ImageFont.load_default()
        ImageDraw.Draw(img).text((30,55),"CHATLENS OCR 12345",fill="black",font=font)
        tess_text,_,tess_conf=tess_read(img,"범용","한국어")
        info["checks"]["tesseract_text"]=tess_text
        if not tess_text:raise RuntimeError("Bundled Tesseract OCR failed")
        # Test actual Korean glyph recognition, not only English strings
        korean=Image.new("RGB",(1000,180),"white")
        kfont_file=Path("C:/Windows/Fonts/malgun.ttf")
        kfont=ImageFont.truetype(str(kfont_file),44) if kfont_file.exists() else font
        ImageDraw.Draw(korean).text((25,44),"안녕하세요 한글 인식 테스트 1234",fill="black",font=kfont)
        korean_text,_,_=tess_read(korean,"범용","한국어")
        korean_only,_,_=tess_read(korean,"범용","한국어",tess_lang="kor")
        info["checks"]["korean_only_model"]=korean_only
        if "안녕하세요" not in korean_only.replace(" ",""):
            raise RuntimeError("Bundled Korean-only OCR engine failed: "+repr(korean_only))
        info["checks"]["korean_sample"]=korean_text
        if "안녕하세요" not in korean_text.replace(" ",""):
            raise RuntimeError("Bundled Korean text recognition failed: "+repr(korean_text))
        line=Image.new("RGB",(800,120),"white")
        ImageDraw.Draw(line).text((20,28),"더럽게 꼬이는군",fill="black",font=kfont)
        space_text,_,_=tess_read(line,"파판14","한국어",psm=7)
        info["checks"]["korean_spacing"]=space_text
        if "꼬이는군" not in space_text.replace(" ",""):
            raise RuntimeError("Korean character recognition regression: "+repr(space_text))
        models=list((BASE/"models").rglob("*.onnx"))
        info["checks"]["onnx_model_count"]=len(models)
        if len(models)<4:raise RuntimeError("Packaged OCR ONNX models missing")
        old=socket.socket.connect
        oldex=socket.socket.connect_ex
        oldcreate=socket.create_connection
        def blocked(*a,**kw):raise RuntimeError("Offline test tried network access")
        socket.socket.connect=blocked
        socket.socket.connect_ex=blocked
        socket.create_connection=blocked
        try:
            for language in ["한국어","영어","일본어"]:
                records=recognize(img,language,False)
                info["checks"]["ocr_"+language]=len(records)
                if not records:raise RuntimeError("OCR failed to recognize test image: "+language)
            # Historically a very wide 2px-high crop caused RapidOCR
            # reduce_max_side to produce a zero-sized resize dimension.
            thin=Image.new("RGB",(2200,2),"white")
            info["checks"]["thin_crop_safe"]=isinstance(recognize(thin,"한국어",False),list)
            if not info["checks"]["thin_crop_safe"]:
                raise RuntimeError("Thin-crop OCR guard failed")
        finally:
            socket.socket.connect=old
            socket.socket.connect_ex=oldex
            socket.create_connection=oldcreate
        info["ok"]=info["frozen"]
        if not info["ok"]:raise RuntimeError("Not a bundled executable")
    except BaseException:
        info["error"]=traceback.format_exc()
    Path(outpath).write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding="utf-8")
    return 0 if info["ok"] else 1

def gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, simpledialog
    from PIL import Image, ImageGrab, ImageTk, ImageDraw
    root=tk.Tk();root.title("ChatLens OCR v0.4.3  |  이미지 문자 인식")
    root.geometry("1420x860");root.minsize(1060,680);root.configure(bg="#101722")
    debuglog.note("gui_started")
    def report_callback_exception(exc_type,exc,tb):
        debuglog.exception("gui_callback_failure",exc)
        status.set("UI 오류 발생 — [디버그 로그]에서 상세 확인")
        messagebox.showerror("ChatLens OCR 오류",
            "UI 오류가 발생했습니다. [디버그 로그] → [로그 복사]로 자세한 내용을 복사할 수 있습니다.")
    root.report_callback_exception=report_callback_exception
    style=ttk.Style(root);style.theme_use("clam")
    style.configure("TFrame",background="#101722")
    style.configure("Primary.TButton",padding=(14,8),font=("Malgun Gothic",10,"bold"))
    style.configure("TLabel",background="#101722",foreground="#d9e6f5",font=("Malgun Gothic",10))
    style.configure("TButton",padding=(8,6),font=("Malgun Gothic",10))
    style.configure("TCombobox",padding=(5,4))
    mode=tk.StringVar(value="자동"); language=tk.StringVar(value="한국어")
    precise=tk.BooleanVar(value=True); world=tk.StringVar(value="모그리")
    status=tk.StringVar(value="준비 완료  ·  이미지 열기 → 분석 → 결과 저장  |  검증 5/8")
    entries=[]; active=[None]; selection=[None]; last=[None]; photo=[None]; scale=[1.]
    origin=[0,0]; jobs=[None]; events=queue.Queue(); worker=[None]; generation=[0]
    def label(parent,s):ttk.Label(parent,text=s).pack(side="left",padx=(8,3))
    def button(parent,s,cb):ttk.Button(parent,text=s,command=cb).pack(side="left",padx=3)
    header=ttk.Frame(root,padding=(16,12,16,5));header.pack(fill="x")
    ttk.Label(header,text="ChatLens OCR",font=("Malgun Gothic",18,"bold"),
              foreground="#f1f6ff").pack(side="left")
    ttk.Label(header,text="v0.4.3  ·  검증 5/8  ·  오프라인 OCR",foreground="#95adc4").pack(side="left",padx=14)
    ttk.Label(header,text="by 2bornot  ·  © 2026",foreground="#b9c9dc").pack(side="right",padx=(10,3))
    tagline=ttk.Frame(root,padding=(16,0,16,10));tagline.pack(fill="x")
    ttk.Label(tagline,text="이미지와 스크린샷의 문자를 추출합니다. 자동 분석부터 시작하세요. 이미지는 외부로 전송되지 않습니다.",
              foreground="#aac0d5").pack(anchor="w")
    # Keep primary actions and OCR settings on separate lines.
    # The v0.4.1 single line overflowed the minimum window width.
    bar=ttk.Frame(root,padding=(12,4,12,6));bar.pack(fill="x")
    file_bar=ttk.Frame(bar);file_bar.pack(fill="x",pady=(0,5))
    options_bar=ttk.Frame(bar);options_bar.pack(fill="x")
    def show_about():
        messagebox.showinfo("ChatLens OCR 정보",
            "ChatLens OCR v0.4.3\n\n"
            "Developer: 2bornot\n"
            "Copyright © 2026 2bornot. All rights reserved under MIT License.\n"
            "License: MIT (application source code)\n\n"
            "오프라인 이미지 문자 인식 / Offline OCR\n"
            "공식 소스 및 배포: github.com/sangkukzoa-ctrl/assets\n"
            "타사 라이브러리·이미지 및 상표는 각각의 권리자에게 귀속됩니다.\n\n"
            "이번 버전은 품질 검증 5/8 시험판입니다. 정식 공개는 8차 검증 후 결정합니다.\n"
            "Windows 코드서명 여부는 파일 속성 및 배포 안내에서 확인하세요.",
            parent=root)
    ttk.Button(header,text="프로그램 정보 / About",command=show_about).pack(side="right",padx=9)
    def add_image(im,name):
        from ui_input_v042 import normalize_imported_image, unique_image_name
        im=normalize_imported_image(im)
        name=unique_image_name(name,entries)
        entries.append((name,im))
        lb.insert("end",name);lb.selection_clear(0,"end");lb.selection_set("end");lb.see("end")
        active[0]=im;selection[0]=None;last[0]=None
        generation[0]+=1
        # Do not leave the previous OCR output visible for a newly loaded image.
        for field in fields:field.delete("1.0","end")
        show();status.set(f"대상: {name} ({im.width}×{im.height}) · 이미지 {len(entries)}개")
    def open_file():
        for f in filedialog.askopenfilenames(filetypes=[("이미지 파일","*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"),("모든 파일","*.*")]):
            try:
                with Image.open(f) as picture:add_image(picture,Path(f).name)
            except Exception as e:
                debuglog.exception("image_open_failed",e,filename=str(f))
                messagebox.showerror("이미지 오류",str(e)+"\n상세 내용은 [디버그 로그]에서 확인할 수 있습니다.")
    def paste():
        try:
            a=ImageGrab.grabclipboard()
            if isinstance(a,Image.Image):add_image(a,"클립보드 이미지")
            elif isinstance(a,list) and a:
                for f in a:
                    with Image.open(f) as picture:add_image(picture,Path(f).name)
            else:messagebox.showinfo("클립보드","Win+Shift+S로 스크린샷을 복사하세요.")
        except Exception as e:messagebox.showerror("클립보드 오류",str(e))
    button(file_bar,"📂 이미지 열기",open_file);button(file_bar,"📋 화면 붙여넣기",paste)
    def get_selected():
        return active[0].crop(selection[0]) if selection[0] and active[0] is not None else active[0]
    def run(allfiles=False):
        if not entries:messagebox.showinfo("대상 없음","먼저 이미지를 열어 주세요.");return
        if worker[0] and worker[0].is_alive():return
        jobs[0]=None; stamp=generation[0]; settings=(mode.get(),language.get(),precise.get(),world.get())
        if allfiles:
            todo=entries[:]
        else:
            idx=lb.curselection()[0] if lb.curselection() else len(entries)-1
            name=entries[idx][0]
            todo=[(name + " [선택 영역]" if selection[0] else name,get_selected())]
        debuglog.note("analysis_requested",total=len(todo),mode=settings[0],
                      language=settings[1],precise=bool(settings[2]))
        def compute():
            try:
                from batch_v0372 import analyze_batch
                xicons=Icons()
                results=analyze_batch(todo,settings,xicons)
                events.put(("ok",stamp,results))
            except Exception as error:
                debuglog.exception("analysis_worker_crash",error,total=len(todo),
                                   mode=settings[0])
                events.put(("error",stamp,str(error)))
        worker[0]=threading.Thread(target=compute,daemon=True)
        worker[0].start();status.set("OCR 분석 중...")
    button(file_bar,"🔎 현재 이미지 분석",lambda:run(False));button(file_bar,"전체 이미지 일괄 분석",lambda:run(True))
    label(options_bar,"이미지 종류");mode_box=ttk.Combobox(options_bar,textvariable=mode,
        values=["자동","범용","쇼핑몰 목록","카카오톡","파판14","파일 탐색기"],
        width=13,state="readonly")
    mode_box.pack(side="left")
    label(options_bar,"인식 언어");ttk.Combobox(options_bar,textvariable=language,
        values=["한국어","영어","일본어"],width=8,state="readonly").pack(side="left")
    ttk.Checkbutton(options_bar,text="정밀 인식 (느리지만 상세하게)",variable=precise).pack(side="left",padx=9)
    advanced=ttk.Frame(root,padding=(12,0,12,5));advanced.pack(fill="x")
    ttk.Label(advanced,text="파판14 기준 서버").pack(side="left")
    world_entry=ttk.Entry(advanced,textvariable=world,width=11)
    world_entry.pack(side="left",padx=(6,12))
    ttk.Label(advanced,text="기준 서버와 동일한 채팅 발언자의 서버명은 생략합니다.",
              foreground="#91a8be").pack(side="left")
    def update_advanced(*_):
        if mode.get()=="파판14":advanced.pack(fill="x",after=bar)
        else:advanced.pack_forget()
    mode.trace_add("write",update_advanced)
    update_advanced()
    tools=ttk.Frame(root,padding=(12,0,12,8));tools.pack(fill="x")
    icon_tools=ttk.Frame(tools)
    sticker_tools=ttk.Frame(tools)
    button(tools,"영역 해제",lambda:(selection.__setitem__(0,None),show()))
    def teach_icon():
        if not selection[0] or active[0] is None:messagebox.showinfo("영역","아이콘을 드래그로 선택하세요.");return
        name=simpledialog.askstring("직업 학습","이 아이콘의 직업명을 입력하세요 (예: 현자):")
        if not name:return
        d=DATA/"job_samples";d.mkdir(parents=True,exist_ok=True)
        active[0].crop(selection[0]).save(d/(name+"__"+uuid.uuid4().hex[:8]+".png"))
        status.set("직업 아이콘 샘플 저장됨: "+name)
    button(icon_tools,"직업 아이콘 학습",teach_icon)
    def teach_sticker():
        if not selection[0] or active[0] is None:messagebox.showinfo("영역","스티커를 드래그로 선택하세요.");return
        detail=simpledialog.askstring("스티커 설명",describe_sticker(active[0],selection[0])+"\n설명을 수정해 저장:")
        if detail:
            d=DATA/"sticker_samples";d.mkdir(parents=True,exist_ok=True)
            img=active[0].crop(selection[0]);sample_file=uuid.uuid4().hex[:12]+".png";img.save(d/sample_file)
            with (d/"descriptions.jsonl").open("a",encoding="utf-8") as f:f.write(json.dumps({"filename":sample_file,"description":detail},ensure_ascii=False)+"\n")
            status.set("스티커 설명 등록: "+detail)
    button(sticker_tools,"이모티콘 설명 등록",teach_sticker)
    def update_special_tools(*_):
        icon_tools.pack_forget()
        sticker_tools.pack_forget()
        if mode.get()=="파판14":icon_tools.pack(side="left")
        elif mode.get()=="카카오톡":sticker_tools.pack(side="left")
    mode.trace_add("write",update_special_tools)
    update_special_tools()
    ttk.Label(tools,text="  단축키  Ctrl+O 열기 · Ctrl+V 붙여넣기 · Delete 언로드",
              foreground="#94aac0").pack(side="right",padx=8)
    box=ttk.Panedwindow(root,orient="horizontal");box.pack(fill="both",expand=True,padx=12,pady=(0,7))
    left=ttk.Frame(box);right=ttk.Frame(box);box.add(left,weight=6);box.add(right,weight=5)
    ttk.Label(left,text="이미지 미리보기  |  마우스로 드래그하면 해당 영역만 분석",
              font=("Malgun Gothic",10,"bold")).pack(anchor="w",pady=5)
    canvas=tk.Canvas(left,bg="#222c3a",highlightthickness=0,cursor="crosshair");canvas.pack(fill="both",expand=True)
    lb=tk.Listbox(left,height=4,background="#243143",foreground="#e2ebf4",exportselection=False)
    lb.pack(fill="x",pady=6)
    def change(event=None):
        sel=lb.curselection()
        if sel:active[0]=entries[sel[0]][1];selection[0]=None;show()
    lb.bind("<<ListboxSelect>>",change)
    def remove_selected():
        indices=sorted(lb.curselection(),reverse=True)
        if not indices:return
        for index in indices:
            if 0<=index<len(entries):
                entries.pop(index)
                lb.delete(index)
        generation[0]+=1
        selection[0]=None;last[0]=None
        if entries:
            idx=min(indices[-1],len(entries)-1)
            lb.selection_clear(0,"end");lb.selection_set(idx)
            active[0]=entries[idx][1]
        else:
            active[0]=None
        for widget in fields:widget.delete("1.0","end")
        show()
        status.set(f"이미지 언로드 완료 · 남은 이미지 {len(entries)}개")
    def remove_key(event):
        if isinstance(event.widget,(tk.Text,tk.Entry,ttk.Entry)):
            return
        remove_selected()
        return "break"
    root.bind("<Delete>",remove_key)
    root.bind("<KP_Delete>",remove_key)
    button(tools,"이미지 언로드 (Delete)",remove_selected)
    ttk.Label(right,text="추출한 텍스트  |  복사·저장",
              font=("Malgun Gothic",10,"bold")).pack(anchor="w",pady=5)
    actions=ttk.Frame(right);actions.pack(fill="x")
    tabs=ttk.Notebook(right);tabs.pack(fill="both",expand=True,pady=6)
    fields=[]
    for title in ["분석 결과","원문 OCR","인식 진단"]:
        frame=ttk.Frame(tabs);tabs.add(frame,text=title)
        item=tk.Text(frame,wrap="word",undo=True,bg="#202b39",fg="#eff6ff",insertbackground="white",relief="flat",font=("Malgun Gothic",11),padx=10,pady=10)
        scroll=ttk.Scrollbar(frame,command=item.yview);item.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right",fill="y");item.pack(fill="both",expand=True)
        fields.append(item)
    fields[0].insert("1.0","1. 이미지를 열거나 붙여넣으세요.\n2. [현재 이미지 분석]으로 읽거나, 여러 장이면 [전체 이미지 일괄 분석]을 누르세요.\n3. 특정 부분만 읽으려면 미리보기에서 드래그하여 선택하세요.\n\n[이미지 종류: 자동]을 권장합니다.\n본 프로그램은 로컬에서 동작하며, 외부로 이미지를 전송하지 않습니다.")
    def setfield(widget,value):widget.delete("1.0","end");widget.insert("1.0",value)
    def copy():
        if not last[0]:
            messagebox.showinfo("분석 결과 없음","먼저 이미지를 분석해 주세요.");return
        root.clipboard_clear();root.clipboard_append(fields[0].get("1.0","end-1c"))
        status.set("결과를 클립보드에 복사했습니다")
    def save(ext, suggested_name=None):
        if not last[0]:
            messagebox.showinfo("분석 결과 없음","먼저 이미지를 분석해 주세요.");return
        opts={"defaultextension":"."+ext,"filetypes":[("텍스트","*.txt")] if ext=="txt" else [("JSON","*.json")]}
        if suggested_name:opts["initialfile"]=suggested_name
        f=filedialog.asksaveasfilename(**opts)
        if f:
            if ext=="txt":content=fields[0].get("1.0","end-1c")
            else:
                raw=last[0] or []
                content=json.dumps(raw,ensure_ascii=False,indent=2,default=str)
            Path(f).write_text(content,encoding="utf-8")
            status.set("저장 완료: "+str(f))
    def show_debug_log():
        dialog=tk.Toplevel(root)
        dialog.title("ChatLens OCR v0.4.3 | 디버그 로그")
        dialog.geometry("960x650")
        dialog.minsize(600,360)
        dialog.transient(root)
        ttk.Label(dialog,text="오류 로그 — 파일명, 이미지 크기, 처리 단계, 전체 오류 내용",
                  padding=8).pack(anchor="w")
        actions_log=ttk.Frame(dialog,padding=(8,0,8,6))
        actions_log.pack(fill="x")
        text_frame=ttk.Frame(dialog,padding=(8,0,8,8))
        text_frame.pack(fill="both",expand=True)
        view=tk.Text(text_frame,wrap="none",font=("Consolas",10),
                     bg="#192433",fg="#ecf3fb",insertbackground="#ffffff")
        vscroll=ttk.Scrollbar(text_frame,orient="vertical",command=view.yview)
        hscroll=ttk.Scrollbar(text_frame,orient="horizontal",command=view.xview)
        view.configure(yscrollcommand=vscroll.set,xscrollcommand=hscroll.set)
        vscroll.pack(side="right",fill="y")
        hscroll.pack(side="bottom",fill="x")
        view.pack(fill="both",expand=True)
        def refresh():
            view.configure(state="normal")
            view.delete("1.0","end")
            view.insert("1.0",debuglog.recent_text())
            view.see("end")
            view.configure(state="disabled")
        def copy_log():
            content=debuglog.recent_text()
            root.clipboard_clear()
            root.clipboard_append(content)
            root.update()
            status.set("디버그 로그 전체를 클립보드에 복사했습니다")
        def save_log():
            filename=filedialog.asksaveasfilename(
                defaultextension=".txt",initialfile="ChatLensOCR_v0.4.3_debug.txt",
                filetypes=[("텍스트 파일","*.txt")],parent=dialog)
            if filename:
                Path(filename).write_text(debuglog.recent_text(),encoding="utf-8")
                status.set("디버그 로그 저장 완료: "+filename)
        button(actions_log,"로그 복사",copy_log)
        button(actions_log,"로그 새로고침",refresh)
        button(actions_log,"로그 TXT 저장",save_log)
        refresh()
    button(actions,"결과 복사",copy);button(actions,"TXT 저장",lambda:save("txt"));button(actions,"JSON 저장",lambda:save("json"))
    button(actions,"🐞 디버그 로그",show_debug_log)
    # Next to the debug button: identical TXT contents, automatic version/date name.
    from test_export_v0373 import default_test_result_filename
    button(actions,"📄 테스트결과 내보내기",
           lambda:save("txt",default_test_result_filename()))
    ttk.Label(root,textvariable=status,foreground="#95c9e6").pack(anchor="w",padx=14,pady=(0,9))
    def show():
        canvas.delete("all")
        im=active[0]
        if im is None:return
        w=max(1,canvas.winfo_width()-12);h=max(1,canvas.winfo_height()-12)
        z=min(w/im.width,h/im.height);scale[0]=z
        size=(max(1,round(im.width*z)),max(1,round(im.height*z)))
        drawing=im.copy()
        current_name = entries[lb.curselection()[0]][0] if lb.curselection() else ""
        overlay=next((r for r in (last[0] or []) if r.get("filename")==current_name), None)
        if overlay:
            draw=ImageDraw.Draw(drawing)
            for line in overlay.get("ocr_lines",[]):draw.rectangle(line["box"],outline="#3ea9ff",width=max(1,int(im.width/800)))
            for rect,job in overlay.get("icons",[]):draw.rectangle(rect,outline="#48ef9a",width=max(2,int(im.width/700)))
        photo[0]=ImageTk.PhotoImage(drawing.resize(size,Image.Resampling.LANCZOS))
        origin[0]=(canvas.winfo_width()-size[0])/2;origin[1]=(canvas.winfo_height()-size[1])/2
        canvas.create_image(origin[0],origin[1],image=photo[0],anchor="nw")
        if selection[0]:
            a,b,c,d=selection[0];canvas.create_rectangle(origin[0]+a*z,origin[1]+b*z,origin[0]+c*z,origin[1]+d*z,outline="orange",dash=(6,4),width=2,tag="select")
    def position(e):
        return (max(0,min(active[0].width,int((e.x-origin[0])/scale[0]))),
                max(0,min(active[0].height,int((e.y-origin[1])/scale[0]))))
    started=[None]
    def press(e):
        if active[0] is not None:started[0]=position(e)
    def drag(e):
        if started[0] is None:return
        a,b=started[0];c,d=position(e)
        selection[0]=(min(a,c),min(b,d),max(a,c),max(b,d));show()
    def release(e):
        if started[0] is None:return
        drag(e);started[0]=None
        if selection[0] and (selection[0][2]-selection[0][0]<8 or selection[0][3]-selection[0][1]<8):selection[0]=None
        show()
    canvas.bind("<Configure>",lambda e:show());canvas.bind("<ButtonPress-1>",press)
    canvas.bind("<B1-Motion>",drag);canvas.bind("<ButtonRelease-1>",release)
    def poll():
        try:
            kind,stamp,info=events.get_nowait()
            if stamp!=generation[0]:
                root.after(120,poll);return
            if kind=="error":
                messagebox.showerror("분석 오류",
                    "분석 중 오류가 발생했습니다. [디버그 로그]를 눌러 [로그 복사]로 내용을 복사하세요.\n"+str(info))
                status.set("분석 오류 — 디버그 로그에서 확인")
            else:
                last[0]=info
                setfield(fields[0],"\n\n".join("--- "+v["filename"]+" ["+v["mode"]+"] ---\n"+v["result"] for v in info))
                setfield(fields[1],"\n".join(f'{v["filename"]} {z["box"]} ({z["score"]:.2f}) {z["text"]}' for v in info for z in v["ocr_lines"]))
                setfield(fields[2],json.dumps([{"filename":v["filename"],"mode":v["mode"],"icons":v["icons"],"messages":v["messages"]} for v in info],ensure_ascii=False,indent=2))
                failed=sum(bool(v.get("failed")) for v in info)
                if failed:
                    status.set(f"분석 완료 {len(info)}개 중 오류 {failed}개 | [디버그 로그] → [로그 복사]")
                else:
                    status.set(f"분석 완료: {len(info)}개 이미지")
                show()
        except queue.Empty:pass
        root.after(120,poll)
    root.after(120,poll)
    root.bind("<Control-o>",lambda e:open_file())
    root.bind("<Control-v>",lambda e:paste())
    root.mainloop()

if __name__=="__main__":
    if len(sys.argv)>=3 and sys.argv[1]=="--self-test":sys.exit(selftest(sys.argv[2]))
    gui()
