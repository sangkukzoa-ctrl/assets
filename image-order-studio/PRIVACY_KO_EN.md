# Privacy / 개인정보 처리 안내

**Image Order Studio** (developer: 2bornot) operates locally on your Android device.

- Images are accessed only after the user picks them via Android's document picker or explicitly shares images with the app.
- Copies, original file names, image sequence identifiers, and temporary exports are stored locally on the device. The original external images are not changed.
- The app does not request internet access, run advertising or analytics SDKs, require accounts, or transmit images to any developer-controlled server.
- Export/share invokes Android's built-in Sharesheet or saves files into a folder that the user chooses. Any later data handling by the target app or website follows that destination's policies.
- Clearing the library removes the app's private imported copies and order history. Uninstalling the app removes its private app data. Exported files saved by the user in external folders remain there.

**한국어:** 앱은 사용자가 선택·공유한 이미지와 순서 정보를 기기 내부에 보관하며, 앱 자체적으로 인터넷 전송·광고·통계를 수행하지 않습니다. 사용자가 직접 선택한 외부 앱/사이트 또는 폴더로만 출력합니다. 앱 보관함 삭제는 원본 파일을 삭제하지 않습니다.

## External picker sessions / 외부 첨부 세션

외부 앱·사이트에서 호출하는 경우 별도의 앱 전용 디렉터리에 이미지 복사본을 보관하여 개인 보관함의 선택을 변경하지 않습니다. 첨부 결과는 해당 앱이 읽을 수 있도록 URI 접근 권한을 부여합니다. 오래된 세션은 7일 후 다음 실행 시 정리합니다. / A separate private session is created for each external image picking request. Selected results are returned as temporary read-granted content URIs. Sessions older than seven days are pruned on the next external session.
