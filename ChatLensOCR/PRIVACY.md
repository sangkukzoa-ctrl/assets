# ChatLens OCR privacy notice / 개인정보 안내

Developer: **2bornot** · © 2026 2bornot

ChatLens OCR runs its OCR engines **locally on the computer**. The application does not upload screenshots, extracted text, or examples used to teach icon/sticker descriptions to a hosted OCR or analytics service. There is no application account or telemetry requirement.

The application can store a local debug log and optional job-icon/sticker training samples under `%LOCALAPPDATA%\ChatLensOCR`. User-selected TXT and JSON exports are saved only to the destinations chosen by the user.

To remove the portable program, delete the EXE or extracted ZIP. To remove saved training data and logs, delete `%LOCALAPPDATA%\ChatLensOCR` after backing up anything you want to keep.

Source code and dependencies are available through the official GitHub repository. Download/build workflows retrieve publicly available upstream packages and OCR models; this network activity happens during *build*, not during runtime OCR.

---

**한국어 요약:** 이미지 분석·문자 인식은 PC에서 오프라인으로 이루어집니다. 스크린샷과 인식 결과를 자동 업로드하지 않습니다. 학습 데이터와 로그는 사용자 PC의 로컬 앱 데이터 영역에 저장되며 삭제할 수 있습니다.
