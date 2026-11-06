#!/usr/bin/env python3
from pathlib import Path
import re
root=Path(".")
main_file=root/"app/src/main/java/com/hsiwan/pdfimage/MainActivity.java"
gradle_file=root/"app/build.gradle"
manifest_file=root/"app/src/main/AndroidManifest.xml"
main=main_file.read_text(encoding="utf-8")
main,n=re.subn(r'(?m)^(\s*TextView title = label\([^\n]*\);)$',r'\1\n        title.setText("Just PDF to Image");',main,count=1)
if n!=1: raise RuntimeError("MainActivity title not found")
if "body.addView(emblem);" not in main: raise RuntimeError("MainActivity header not found")
main=main.replace('body.addView(emblem);','emblem.setText("2bornot");\n        body.addView(emblem);',1)
main=main.replace("1.3.0","1.3.1")
main_file.write_text(main,encoding="utf-8")
gradle=gradle_file.read_text(encoding="utf-8")
gradle,n1=re.subn(r'versionCode\s+\d+','versionCode 5',gradle,count=1)
gradle,n2=re.subn(r"versionName\s+['\"][^'\"]+['\"]","versionName '1.3.1'",gradle,count=1)
if n1!=1 or n2!=1 or "com.hsiwan.pdfimage" not in gradle: raise RuntimeError("Unexpected Gradle version/applicationId")
gradle_file.write_text(gradle,encoding="utf-8")
manifest=manifest_file.read_text(encoding="utf-8")
manifest,n=re.subn(r'android:label="[^"]+"','android:label="@string/app_name"',manifest,count=1)
if n!=1:raise RuntimeError("Manifest label not found")
manifest_file.write_text(manifest,encoding="utf-8")
for dirname in ("values","values-ko"):
    d=root/"app/src/main/res"/dirname
    d.mkdir(exist_ok=True,parents=True)
    (d/"strings.xml").write_text('<?xml version="1.0" encoding="utf-8"?>\n<resources><string name="app_name">Just PDF to Image</string></resources>\n',encoding="utf-8")
l10n=root/"app/src/main/java/com/hsiwan/pdfimage/L10n.java"
if not l10n.exists():raise RuntimeError("Missing bilingual localization")
s=l10n.read_text(encoding="utf-8")
for old in ('PDF → 이미지','PDF → Image','PDF Image','PDF 이미지 변환기'):
    s=s.replace('"'+old+'"','"Just PDF to Image"')
s=s.replace("1.3.0","1.3.1")
l10n.write_text(s,encoding="utf-8")
(root/"RELEASE_NOTES.md").write_text("""# Just PDF to Image v1.3.1 — by 2bornot

## 한국어

**PDF를 이미지로. 그게 전부입니다.**

무료 · 광고 없음 · 인터넷 불필요 · 변환 횟수 제한 없음.

- PDF 여러 개를 PNG/JPG 이미지로 일괄 변환
- 150/200/300 DPI, JPG 품질 및 페이지 범위 지정
- PDF에 삽입된 JPEG 원본을 재압축 없이 추출
- 저장 폴더 선택, 진행률 확인 및 작업 취소
- 한국어·영어 지원(기기 언어 자동 적용)

**v1.3.1:** 설치 이름과 화면 제목을 **Just PDF to Image**로 통일하고 개발자명 **2bornot**을 표시했습니다. 기존 기능 및 앱 패키지명은 유지합니다.

**설치:** JustPDFtoImage-v1.3.1.apk를 내려받아 Android 8.0 이상에서 설치하세요. 정식 v1.3.0 사용자는 업데이트로 설치할 수 있습니다. v1.2.0 디버그 버전은 서명이 달라 삭제 후 설치해야 합니다.

버그와 개선 의견은 이 저장소의 Issues에 남겨주세요.

## English

**PDF to images. Nothing else.**

Free · No ads · Offline · No conversion limits.

- Batch convert multiple PDFs to PNG/JPG
- Set resolution (150/200/300 DPI), JPEG quality and page range
- Extract embedded JPEG originals without re-encoding
- Choose an output folder, view progress and cancel
- Korean and English interface (follows device language)

**v1.3.1:** Installed name and interface title updated to **Just PDF to Image**, with developer **2bornot**. Existing conversion features and application ID remain unchanged.

**Install:** Download JustPDFtoImage-v1.3.1.apk (Android 8.0+). Official v1.3.0 users can update without uninstalling. The older v1.2.0 debug build uses a different signature.

Report bugs and feature requests via Issues.

---
MIT (app source). PDFBox-Android is Apache 2.0 licensed.
""",encoding="utf-8")
(root/"STORE_LISTING_KO_EN.md").write_text("""# Just PDF to Image / 2bornot

## 한국어
앱 이름: Just PDF to Image
개발자: 2bornot
설명: PDF를 이미지로. 그게 전부입니다.

PDF를 PNG 또는 JPG로 간편하게 변환합니다. 여러 PDF 일괄 변환, 페이지 범위, 해상도, JPG 품질, 원본 JPEG 무손실 추출을 지원합니다. 무료 · 무광고 · 오프라인 · 무제한.

## English
App: Just PDF to Image
Developer: 2bornot
Tagline: PDF to images. Nothing else.

Convert PDFs to PNG or JPG. Batch conversion, page ranges, DPI, JPEG quality, and extraction of original embedded JPEGs. Free, no ads, offline, unlimited.
""",encoding="utf-8")
readme=root/"README.md"
if readme.exists():
    s=readme.read_text(encoding="utf-8")
    s=s.replace("# PDF → Image v1.3.0", "# Just PDF to Image v1.3.1 — by 2bornot")
    s=s.replace("PDF Image v1.3.0","Just PDF to Image v1.3.1")
    readme.write_text(s,encoding="utf-8")
print("Rebrand OK: Just PDF to Image v1.3.1 / 2bornot")
