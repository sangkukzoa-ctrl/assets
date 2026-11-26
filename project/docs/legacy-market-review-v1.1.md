# PDF → Image: 2026-11-05 Google Play 경쟁조사·출시 전략

## 선언

PDF 한 개를 이미지 한 장으로 바꾸려는 사람과 PDF 수십 개를 한꺼번에 처리해야 하는 사람에게 **동일한 무료 기능**을 제공한다.

- 유료 결제, 보상형 광고, 워터마크, 파일/페이지 수 제한 없음
- 사용자 계정과 로그인, 업로드, 인터넷 의존성 없음
- 이미지 변환 전후의 최소 동작 외에 스캔, 편집, OCR, AI 기능을 추가하지 않음
- 대량 작업에서도 처리 진행·실패 항목·취소·저장 위치를 명확히 보여줌
- 휴대전화 파일 선택기를 사용하고 권한을 최소화함

## 실제 스토어 경쟁 사례

| 앱 | 관찰 가능한 사실 | 출처 |
|---|---|---|
| DLM Infosoft PDF to Image | 100만+ 다운로드, 약 3.3점, 광고 및 인앱 구매. 2024-10-27 후기에서 결과 폴더 경로가 번거롭다는 경험 확인 | https://play.google.com/store/apps/details?id=com.dlminfosoft.pdftoimage |
| NICEJJ PDF Converter | 오프라인이지만 광고 있음. 페이지 수, 고해상도, 배치 처리 제한을 보상형 광고로 임시 해제한다고 설명 | https://play.google.com/store/apps/details?id=com.hsh.docscan |
| Mini Developing BD PDF To Image | 여러 PDF 처리, 암호 PDF 지원, 광고·인앱 구매 | https://play.google.com/store/apps/details?id=com.minidevbd.pdftojpg |
| Flash Software Solution PDF to Image | 앱 설명에는 'No ads interrupting' 표현이 있으나, Play 표시는 'Contains ads'. 오프라인·페이지 선택·고해상도 제공 | https://play.google.com/store/apps/details?id=reze.pdf.toimage |
| PDF Tools Pro | PDF 병합, 분할, 압축 등 다기능; 광고 제거와 무제한 처리를 인앱 구매에 연결 | https://play.google.com/store/apps/details?id=com.brekele.pdftools |

앱 설명과 Play 표시, 공개 후기 일부에 기반한 **표본 조사**다. 전체 앱 순위나 모든 후기의 통계적 대표성을 주장하지 않는다.

## 시장에서 배운 핵심

1. 일괄 변환 자체는 이미 많은 앱이 지원한다. 차이는 **비과금·무중단·안정성**에서 만들어야 한다.
2. 저장 위치 찾기 어려움은 별도 사용자 후기에서 드러난 실질적인 불편이다. 결과 폴더 바로 열기와 저장 규칙 투명성에 우선 투자한다.
3. 편집·스캔·OCR 등을 추가할수록 제품 철학에서 멀어진다.
4. 'lossless'는 PNG 압축 방법에 관한 설명이다. PDF 벡터 원본을 이미지로 변환하면 해상도의 제약이 생긴다.

## Google Play 필수 등록사항 (2026-11 기준)

- 25 USD 1회 개발자 등록비: https://support.google.com/googleplay/android-developer/answer/6112435
- 2026-08-31 이후 신규 앱 및 업데이트 target API 36+: https://developer.android.com/google/play/requirements/target-sdk
- 신규 앱 AAB 제출: https://support.google.com/googleplay/android-developer/answer/9844279
- 2023-11-13 이후 생성 개인 계정은 12명 14일 연속 비공개 테스트 후 출시 접근 신청: https://support.google.com/googleplay/android-developer/answer/14151465
- 개인정보처리방침: https://support.google.com/googleplay/android-developer/answer/10144311
- 데이터를 수집하지 않아도 Data safety 양식 제출: https://support.google.com/googleplay/android-developer/answer/10787469
- 앱 아이콘·대표 그래픽·최소 2개 스크린샷과 규격: https://support.google.com/googleplay/android-developer/answer/9866151
- 파일 접근 권한 최소화: https://support.google.com/googleplay/android-developer/answer/16558241
- 2026년 개발자/패키지 등록: https://support.google.com/googleplay/android-developer/answer/16984799
- 간단한 앱이라도 실제 효용/안정성 필요: https://support.google.com/googleplay/android-developer/answer/9898783

## 출시에 필요한 테스트

| 상황 | 합격 기준 |
|---|---|
| 1페이지 PDF | 1개 이미지, 원본 이름 유지 |
| 다중 페이지 PDF | 순서가 보존된 개별 이미지 |
| 여러 PDF 동시 선택 | 모든 문서 처리, 충돌 없는 이름 |
| 대량 이미지(100+ 페이지) | 메모리/반응성 확인, 실질적 취소 가능 |
| 한글·공백·긴 파일명 | 정상 저장, 이름 충돌 없음 |
| 페이지 범위 잘못 입력 | 사용자에게 명확한 오류 |
| 앱에서 다른 앱으로 전환 | 작업 중단 동작/상태가 정확함 (장기 작업 개선 필요) |
| 150/200/300 DPI | 출력 해상도 및 화질, 메모리 제한에 의한 실효 DPI 확인 |
| 암호 PDF·손상 PDF | 전체 앱 비정상 종료 없이 문제 문서 보고 |
| 파일 공급자(내장 저장소/드라이브) | 읽기/쓰기 오류 표시, 기존 파일 보호 |
| Android 8, 13, 15, 16 | 화면 잘림·메모리/권한 문제 없음 |

## 우선순위

- P0: GitHub에서 APK 빌드 성공, 실제 기기 테스트, 여러 PDF 대량 변환 시 UI/메모리/취소 안정화
- P0: Android API 36 엣지 투 엣지 화면, 문서 제공자 호환성, 저장 결과 확인 UI
- P1: 결과 폴더 바로 열기, 이전 설정 유지, PDF 공유 메뉴에서 바로 받기
- P1: 영어 UI 및 접근성, 진짜 파일 손상 방지/에러 메시지
- P2: 암호 PDF 지원과 대용량/초고해상도 렌더러 고도화 (기본 동작을 흐리지 않도록 옵션화)

출시 전 우선 구현할 기능은 P0/P1 안에서 **PDF → PNG/JPG 변환에 직접 영향을 주는 것만** 선택한다.
