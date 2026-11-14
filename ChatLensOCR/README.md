**Developer / 개발자:** 2bornot  ·  **Copyright © 2026 2bornot**  ·  **License:** [MIT](LICENSE)

**Code signing policy:** [SignPath Foundation application plan](CODE_SIGNING_POLICY.md). Current beta downloads are distributed from GitHub Releases at the stable link https://github.com/sangkukzoa-ctrl/assets/releases/tag/chatlens-beta. It is NOT Authenticode signed; Windows may warn about an unknown publisher. GitHub build attestation does not provide a Windows publisher signature. Windows certificate Publisher will say SignPath Foundation if signing is eventually approved. It is separate from the project developer attribution.

[Privacy](PRIVACY.md) · [Third-party notices](NOTICE.md)

## Development build v0.4.21 — local Windows EXE 166-image audit and human-reference CER

Latest public download: https://github.com/sangkukzoa-ctrl/assets/releases/tag/chatlens-beta

# ChatLens OCR v0.4.21 (무료 공개 테스트판 · Beta)

**개발 중이며 문자 인식 오류가 발생할 수 있습니다. 정확도 개선을 지속하고 있습니다.** 추출한 이름·금액·날짜 및 중요한 문장은 원본 이미지와 비교해 주세요.

**Windows x64 · 무료 오프라인 이미지 문자 인식 프로그램**

스크린샷을 분석하여 일반 문서와 웹페이지, 쇼핑몰 상품 목록, 카카오톡 대화, 파이널판타지14 채팅·전투 로그를 텍스트로 추출합니다.

## v0.4.21 표 판독 개선
- 선이 반복되는 밝은 다열 웹표를 픽셀 구조에 따라 열별로 분리해 판독합니다. 행·열을 섞거나 한 행의 날짜/금액을 다른 행으로 넘기는 오류를 줄이는 것이 목적입니다.
- 반복되는 사각형 아이콘은 글자가 아닌 그림으로 식별하고, 파란 버튼에 보이는 흰 글자만 별도로 판독합니다. 고정 문구 치환이나 구매내역별 예외 코드는 사용하지 않습니다.
- 화면 구조가 뚜렷하지 않으면 기존 OCR 방식으로 돌아갑니다. 원본 이미지와 사람이 직접 판독한 비공개 테스트 데이터는 공개 저장소에 넣지 않습니다.
- Windows 공개 베타 빌드 성공과 실제 이미지 전체 문자정확도 검증은 서로 다른 항목으로 관리합니다.

## v0.4.21 개선\n- 여러 줄의 노란 외곽선 자막이 픽셀로 감지되었으나 OCR이 공란을 반환하면, 추측한 문장 대신 `[글자 미인식]`을 표시하여 사용자의 검수를 돕습니다.\n- 단일 이미지 OCR 결과를 표시한 상태에서 다른 이미지로 전환하면 이전 이미지의 결과가 새 이미지 결과로 오해되지 않도록 비웁니다. 일괄 분석 결과는 유지됩니다.\n- 사용자 원본 166장, 판독 GT, 비공개 검수 데이터는 GitHub 공개 저장소에 업로드하지 않습니다.\n\n## v0.4.21 비공개 실제 화면 검증

- **Windows EXE 실제 엔진 검사**: `ChatLensOCR.exe --audit-folder "검증이미지폴더" "비공개결과.jsonl"`로 해당 폴더의 원본 이미지를 한 장씩 실제 OCR하고 비공개 JSONL로 기록합니다. 기존 결과파일이 있으면 덮어쓰지 않습니다.
- **재개**: `ChatLensOCR.exe --audit-resume "검증이미지폴더" "비공개결과.jsonl"`은 같은 버전·옵션에서 미완료 또는 변경된 이미지부터 진행합니다.
- **인간 정답 비교**: `ChatLensOCR.exe --audit-score "비공개결과.jsonl" "인간정답.csv" "비공개CER.json"`은 원문 그대로의 문자 오류율·완전 일치·텍스트 없는 사진의 환각 건수를 계산합니다. 원본/정답/결과는 모두 로컬에 남습니다.
- `--audit-folder` 또는 `--audit-score`는 별도 GUI 없이 실행되고, Windows 배포의 동일 엔진·자원을 사용합니다. JSONL 항목 하나에 실패해도 다음 원본을 계속 처리하며 진행 내역이 보존됩니다.
- `Windows CI PASS`는 실제 166장 CER 판정이 아닙니다. 실제 데이터 전수 결과는 비공개 로컬 검사로 별도 기록합니다.

## 사용 방법
1. [공식 GitHub Releases](https://github.com/sangkukzoa-ctrl/assets/releases/tag/chatlens-beta)에서 Windows x64 EXE 또는 ZIP 다운로드
2. ZIP이라면 압축 해제 후 EXE 실행 (Python 설치 불필요)
3. **이미지 열기** 또는 **붙여넣기**로 스크린샷 추가
4. **자동** 유형에서 **현재 이미지 분석** 또는 **전체 이미지 일괄 분석**
5. 오른쪽에서 **결과 복사**, **TXT/JSON 저장**, **테스트결과 내보내기**, **미인식 찾기**

## 분석 유형
- **자동**: 카카오톡·파판14·파일탐색기·상품목록 등 감지
- **범용**: 일반 문서, 웹페이지, 이미지 속 텍스트
- **쇼핑몰 목록**: 여러 열의 상품을 각각 분리하여 글자를 인식
- **카카오톡**: 발언자·말풍선·이모티콘 보존
- **파판14**: 채팅, 직업 아이콘 자동 인식·고신뢰 자동 학습, 서버명, 전투 메시지, PvP 스코어보드
- **파일 탐색기**: 행과 열 구조를 분리

## 오프라인·개인정보
OCR은 사용자 PC에서 실행됩니다. 이미지/대화는 앱의 외부 서비스로 업로드되지 않습니다. 직업/이모티콘 수동 학습 자료와 디버그 기록은 사용자 로컬 영역에 저장됩니다.

## 배포·서명
공개 빌드는 Windows용 GitHub Actions에서 생성하며, SHA256과 빌드 출처 증명(Sigstore)을 제공합니다. 이는 **Windows Authenticode 실행 파일 서명과 다릅니다**. 'unsigned preview' 릴리스는 서명되지 않은 빌드이며 Windows SmartScreen 경고가 표시될 수 있습니다. 유효한 코드서명 인증서가 제공되면 Actions에서 서명과 검증을 완료한 뒤 정식 릴리스로 표시합니다.

원본 사용자 테스트 이미지와 개인 대화는 저장소에 게시하지 않습니다. 직업 아이콘 자동 학습은 인식 확신도가 충분히 높을 때 아이콘 영역만 사용자 PC에 저장하며, 잘못된 학습을 막기 위한 제한을 적용합니다. 카카오톡 스티커 검출·설명 등록 기능은 유지됩니다.

---

**English:** Free, offline Windows x64 OCR for screenshots. Supports general documents, multi-column shopping catalogs, KakaoTalk and FFXIV, with batch processing, region selection, TXT/JSON export and logs. No Python install or network service required at runtime. Public build attestations do not substitute for Windows executable code signing.
