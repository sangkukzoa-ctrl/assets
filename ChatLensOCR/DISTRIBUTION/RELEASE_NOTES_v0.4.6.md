# ChatLens OCR v0.4.6 — 무료 공개 테스트판 (Beta)

> **현재 개발 중인 공개 테스트판입니다.** OCR 인식 성능이 아직 불안정해 글자 오인식, 메시지 누락, 상품 정보·표 항목의 혼동이 발생할 수 있습니다. 정확도와 안정성을 계속 개선하고 있습니다. 중요한 내용은 반드시 원본 이미지와 비교하세요.

**개발자:** 2bornot · **Windows x64** · **오프라인 스탠드얼론 EXE** · **무료** · **현재 Authenticode 미서명**

## 다운로드

- `ChatLensOCR_v0.4.6.exe` — 단독 실행파일. Python 설치나 별도 OCR 서버가 필요하지 않습니다.
- `ChatLensOCR_v0.4.6_Windows_x64.zip` — EXE·라이선스·고지문이 들어 있는 압축 배포본.
- `SHA256SUMS.txt` — 배포 파일 해시 검증.
- `ChatLensOCR_v0.4.6_네이버블로그_게시글.txt` — 네이버 블로그 게시용 원고.
- `ChatLensOCR_v0.4.6_사용안내.txt` — 간단 사용법과 알려진 한계.
- `ChatLensOCR_v0.4.6_SOURCE.zip` — 원본 애플리케이션 소스와 라이선스.

## 주요 기능

- 이미지 파일 열기·클립보드 스크린샷 붙여넣기, 선택 영역 분석, 여러 장 일괄 분석.
- 한국어·영어·일본어 OCR.
- **자동 / 범용 / 쇼핑몰 목록 / 카카오톡 / 파이널판타지14 / 파일 탐색기** 모드.
- 결과 복사, TXT·JSON 저장, 테스트 결과 내보내기, 진단 로그 복사·저장.
- 카카오톡 미인식 표시 찾기(`Ctrl+G`), 결과 텍스트 수동 수정 및 저장.

## 검증 현황 및 알려진 한계

- 기준 이미지 34장으로 8차에 걸쳐 유형 분류, 구조 인식 및 OCR 회귀 검사를 진행했습니다.
- 직접 확인한 카카오톡 정답 문장 16개 중 **14개 정확히 일치(87.5%)**. 이는 전체 34장의 문자 정답률을 뜻하지 않습니다.
- 예: `오잉`을 `으잉`으로 읽거나, `퉤`처럼 짧은 글자를 읽지 못하는 문제가 남았습니다.
- 복잡한 쇼핑몰 카드, 파판14 직업 아이콘 및 특수기호, 파일 탐색기 셀에서도 오류가 발생할 수 있습니다.
- Windows GitHub Actions에서 1~8차 회귀 검사, 오프라인 EXE 자체검사, ZIP 무결성 검증을 통과했습니다.

## 개인정보 및 보안

OCR 분석은 사용자 PC 내부에서 이루어지며, 이미지나 채팅 내용을 외부 OCR 서비스로 자동 전송하지 않습니다. 수동 학습 샘플과 디버그 기록은 로컬에 저장됩니다. 자세한 내용은 `PRIVACY.md`를 참조하세요.

**이 EXE는 Windows Authenticode 코드서명 인증서를 아직 사용하지 않습니다.** '알 수 없는 게시자'나 SmartScreen 경고가 나타날 수 있습니다. GitHub Actions 출처 증명은 Windows 게시자 서명과 다른 검증입니다. 공식 다운로드 주소와 `SHA256SUMS.txt`를 확인하세요.

**저작권:** © 2026 2bornot · 원본 애플리케이션 소스 MIT License. 타사 라이브러리·상표·게임 아이콘은 각 권리자의 조건을 따릅니다.

**검증된 8차 빌드:** https://github.com/sangkukzoa-ctrl/assets/actions/runs/42464851957

---

**English:** Free offline Windows x64 screenshot OCR beta. Korean/English/Japanese; general, shopping, KakaoTalk, FFXIV and Explorer modes. Recognition accuracy is still being improved and mistakes or omissions are possible. EXE is unsigned; verify the official GitHub SHA256 checksum.
