# 심안(心眼) Windows 간편 설치 관리자 R2

이 버전은 심안 확장프로그램 **v1.5.1**을 제공하는 새 Windows 설치 도구입니다. 수집 엔진의 버전·기능은 변경하지 않았습니다.

## 변경 사항

- 기존 `INSTALL.cmd` / `setup.ps1` 대신 GUI `SimanSetup.exe` 제공
- 표준 설치 경로 `%LOCALAPPDATA%\2bornot\Siman\app`만 사용
- 기존 코드 폴더를 재사용하지 않고 신규 파일로 교체; 설치 실패 시 롤백
- Chrome / Edge 확장관리 화면 열기, 폴더 주소 자동 복사, 단계별 화면 안내
- 드래그 앤 드롭 불필요. 브라우저의 '압축해제된 확장프로그램 로드'에서 폴더 선택
- 삭제 전 JSON 백업 및 새 설치 후 기록 복원 안내
- 관리자 권한 불필요, 설치 로그 `%LOCALAPPDATA%\2bornot\Siman\setup.log`

## 검증 및 한계

- Windows GitHub Actions에서 GUI 실행파일 빌드, 페이로드 버전 확인, 신규 파일 설치, 구버전 파일 제거·새 버전 재설치 테스트 수행
- Chrome / Edge의 보안 정책상 웹스토어 미등록 확장프로그램의 최초 등록은 사용자가 직접 승인해야 합니다.
- 서명되지 않은 Windows 실행파일에는 SmartScreen 경고가 발생할 수 있습니다. GitHub 출처증명은 코드서명과 다릅니다.
- 실제 계정 ChatLLM/Claude 전수수집 검증은 별개입니다. 이번 릴리스는 **배포·설치 UX 개선판**입니다.
