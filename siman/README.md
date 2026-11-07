# 심안 (心眼) — AI 대화 통합 검색

**개발자:** 2bornot  
**버전:** v1.3.0  
**대상:** Chrome / Edge (Manifest V3)

ChatGPT, Claude, ChatLLM의 대화 목록과 원문을 로컬에 색인하고 키워드 검색합니다. Gemini·DeepSeek·Grok은 방문 대화 저장을 지원합니다.

- 검색은 브라우저 로컬 저장소에서 수행되며 별도 AI 모델 토큰과 API 키를 사용하지 않습니다.
- ChatGPT, Claude, ChatLLM의 원문 조회는 각 서비스의 로그인 상태와 서버 허용 범위에 따라 달라집니다.
- HTTP 429가 발생하면 요청을 멈추고 재시도 간격을 준수하며 수집 상태를 유지합니다.
- 기존 ZIP 개발자모드 설치에서 v1.3.0으로 업데이트할 수 있는 자동 위치 탐지 도우미가 포함되어 있습니다.

## 릴리스 다운로드

[GitHub Releases — 심안 v1.3.0](https://github.com/sangkukzoa-ctrl/assets/releases/tag/siman-v1.3.0)

## 설치 및 서명

**일반 사용자에게 정식 설치를 제공하려면 Chrome Web Store / Edge Add-ons의 스토어 게시 및 심사가 필요합니다.** 현재 ZIP 파일은 기존 설치 이용자의 업데이트 및 검증용입니다. GitHub Actions의 서명된 빌드 출처 증명(attestation)은 Windows 코드 서명이나 웹스토어 게시자 서명과 서로 다릅니다.

[개인정보 처리 안내](PRIVACY.md)

## 개발·검증

릴리스 첨부파일: INSTALL (기존 사용자 업데이트), WEBSTORE (스토어 제출용), SOURCE (소스 및 테스트), SHA256SUMS (검증값).
