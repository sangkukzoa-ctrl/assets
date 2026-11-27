# 빌드/환경
Go 1.23.2, 표준 라이브러리만 사용(원본 go.mod에 외부 의존성 없음). Windows 전용 syscall/Win32, amd64 GUI 타깃. Gradle/Android SDK 불필요.

## 재현 명령 (Linux, Go 1.23.2)
```
cd project
CGO_ENABLED=0 GOOS=windows GOARCH=amd64 GOAMD64=v1 go build -trimpath -ldflags='-H=windowsgui -s -w' -o FF14KakaoBridge.exe .
sha256sum FF14KakaoBridge.exe
```
원본 및 재빌드 SHA256: `b7d732b9cea6fdc20ddeb96c78a1759e7e0fbc2cb4f7d1481a7373918517477f`
**링커 플래그 문자열의 순서와 표기까지 그대로 유지하면 이번 환경에서 완전 동일.** `-s -w -H=windowsgui`는 컴파일 성공했으나 Go build ID 차이로 해시 달랐음. 실제 최초 재빌드 결과를 verification/에 기록. 원본 소스 수정 없음.

Windows PowerShell에서 동일한 대상 빌드:
```
cd project
$env:CGO_ENABLED='0'; $env:GOOS='windows'; $env:GOARCH='amd64'; $env:GOAMD64='v1'
go build -trimpath '-ldflags=-H=windowsgui -s -w' -o FF14KakaoBridge.exe .
Get-FileHash FF14KakaoBridge.exe -Algorithm SHA256
```
다른 호스트/Go 버전에서는 결과가 달라질 수 있으므로 실제 SHA를 보고한다. 단순 빌드 실패를 제품 코드 문제로 단정하지 말 것.

## 검증
- `GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go vet ./...`는 기존 unsafe.Pointer 경고 9건으로 nonzero.
- `GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go vet -unsafeptr=false ./...` PASS. 이는 unsafe.Pointer 검사 제외이며 전체 vet PASS라고 표현하지 않는다.
- `GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go test -vet=off ./...`는 `[no test files]`. 테스트 케이스가 없으므로 기능 테스트 PASS 아님.
- Windows UI 실기기 테스트는 미실시. GitHub Actions Linux 러너는 Windows EXE 크로스 빌드만 가능.
- CI는 `.github/workflows/ff14kakaobridge-handoff-ci.yml` 준비본. 해당 브랜치 push만, workflow_dispatch도 정의하되 기본 브랜치에 workflow가 없으면 수동 실행 불가할 수 있다. 자동 출판 없음.
- 브랜치 초기화 후 Actions 권한/실제 run 결과를 확인하고 링크 기록. 현재 원격 CI 결과 없음.
