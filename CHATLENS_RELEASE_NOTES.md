# ChatLens OCR v0.4.1 — Field-test build

**Developer:** 2bornot · **Copyright © 2026 2bornot** · MIT License for original application source.

Updates from v0.4.0:
- Clear 2bornot developer attribution in the UI and Windows EXE version information.
- About panel with developer, copyright and MIT license.
- Dedicated LICENSE, privacy, third-party notices and code signing policy documentation.
- Additional synthetic regression tests and release metadata checks.
- Continues the existing OCR modes, batch features, exports and debug log workflow.

**Code signing policy:** https://github.com/sangkukzoa-ctrl/assets/blob/chatlens-v0410-field-test/ChatLensOCR/CODE_SIGNING_POLICY.md

**Signing:** Free signing by SignPath.io, certificate by SignPath Foundation has **not yet been approved or configured**. This field-test release remains explicitly unsigned unless a valid Authenticode signature is independently verified. GitHub provenance attestation is not a Windows publisher signature.

---

# ChatLens OCR v0.4.1 | Windows x64

무료 오프라인 스크린샷 OCR 프로그램입니다. Windows용 독립 EXE에 한국어·영어·일본어 인식 엔진을 포함합니다.

**변경사항**
- 범용 OCR 우선 UI: 이미지 열기/붙여넣기, 선택·일괄 분석, 유형/언어, TXT·JSON 내보내기.
- 파판14 서버 옵션을 해당 전용 모드로 분리. 기존 카카오톡/파판14 분석, 이미지 언로드, 직업·스티커 학습 유지.
- 상품 목록에서 2~7열·다중 행의 개별 상품카드를 찾아 독립적으로 OCR하여 상품정보 열 혼합 완화.
- 다중 이미지 분석 결과의 선택 이미지 오버레이 대응 및 선택 영역 OCR 수정.
- 테스트 결과 내보내기, 상세 디버그 로그 복사/저장, 이미지 단위 오류 격리 유지.
- GitHub Actions 윈도우 자체검사, SHA256, 빌드 출처 증명. 서명 여부는 릴리스 표시를 확인하세요.

**사용 방법:** ZIP을 풀고 `ChatLensOCR_v0.4.1.exe`를 실행한 다음 이미지를 불러와 **선택 분석** 또는 **전체 이미지 분석**을 선택하세요. 네트워크 연결이나 Python 설치는 필요하지 않습니다.

**Notes (English):** Offline screenshot OCR for Korean, English and Japanese. Modes: General, shopping catalog, KakaoTalk, Final Fantasy XIV and Explorer. Includes batch processing, crop selection, TXT/JSON export, and copyable debug logs. Windows x64; no Python installation needed.

**서명:** GitHub의 빌드 출처 증명(Sigstore attestation)은 Windows Authenticode 코드서명과 별개입니다. 게시된 릴리스에서 'unsigned preview'로 표시된 경우 실행파일은 코드서명되지 않았습니다.
