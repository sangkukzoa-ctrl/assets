# Just PDF to Image v1.3.1 — by 2bornot (Android)

한 가지 일을 제대로 하는 안드로이드 PDF 이미지 변환기. 무료, 광고/분석 SDK/로그인/인터넷 권한/워터마크 없음.

## 두 가지 변환 방법

1. **페이지 렌더링 (PNG/JPG)**: 페이지에 보이는 글자·도형·이미지 전체를 150/200/300 DPI로 출력 (`android.graphics.pdf.PdfRenderer`). PNG 출력은 결과 픽셀의 무손실 압축이며 **원본 PDF 이미지의 픽셀을 직접 추출한다는 뜻이 아닙니다**.
2. **원본 JPEG 추출 (재압축 없음)**: PDF 페이지 리소스의 단일 `DCTDecode` 스트림을 원시 바이트 그대로 복사 (`PdfBox-Android`). 새로운 인코딩은 수행하지 않습니다. PDF에 해당 JPEG가 없는 경우 추출 0장, 비-JPEG 이미지·인라인 이미지·페이지 오버레이/글자/주석은 추출하지 않습니다. 원본 JPEG가 여러 개면 여러 파일로 저장합니다.

하나/여러 PDF 선택, 페이지 지정(전체/범위), SAF 저장 폴더, 원본명 사용, 중복명 회피, 진행률 및 취소를 지원합니다.

## GitHub Actions 자동 빌드

`.github/workflows/build.yml`로 `main` 또는 `pdfimage-ci/**` 브랜치에 푸시할 때 빌드됩니다. Java 17 / Android API 36 / Gradle 8.11.1 / AGP 8.10.1.

- `:app:assembleDebug` → 설치 가능한 `app-debug.apk`
- `:app:assembleRelease` → **서명되지 않은** `app-release-unsigned.apk`
- `:app:bundleRelease` → **서명되지 않은** `app-release.aab`

Play 배포 시에는 본인의 업로드 키로 AAB를 서명해야 합니다. 서명 키를 소스나 CI 아티팩트에 포함하지 마세요.

## 라이브러리

렌더링에는 Android 내장 PDF 엔진만 사용합니다. 원본 JPEG 추출에 한하여 Apache-2.0 라이선스 `com.tom-roush:pdfbox-android:2.0.27.0`을 사용합니다. 앱이 PDF 파일을 외부로 전송하지 않습니다.

## 프로젝트 목표

지속적인 대량 변환 안정성, 큰 파일 메모리 상한, 휴대폰 잠금·백그라운드 처리, 불량 문서 복구 등은 실기기 테스트 대상으로 남아 있습니다. PDF XObject JPEG 추출을 모든 PDF에 대해 동작하는 완전한 `pdfimages` 대체품으로 소개하지 마세요.

## Language / 언어
The app follows the device language: Korean (ko) or English (all other languages).
휴대전화의 언어가 한국어이면 한국어, 그 밖에는 영어로 표시됩니다.
