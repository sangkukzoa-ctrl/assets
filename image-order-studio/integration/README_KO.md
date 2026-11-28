# Image Order — 호스트 앱 선택 연동 (실험)
일반 앱이 다른 앱의 시스템 Photo Picker 호출을 변경하는 기능이 아니다. 첨부 기능을 가진 앱 개발자가 직접 지원할 때만 사용한다. 사용자에게 1회 설정에서 Image Order 사용 여부를 선택하게 하고, 이후 매 첨부에서 기존 버튼을 그대로 사용한다. 미설치/미지원/미동의/서명 불일치면 기존 요청 유지. Image Order v0.5.5 이상 기준. 공개 배포 아님.

호스트 manifest의 queries에 package com.twobornot.imageorder를 추가한다. integration/src/main/java의 OrderedAttachment.java를 호스트 소스에 포함한다. 기존 첨부 요청 Intent를 normalRequest로 전달하고 request(context,userOptedIn,"image/*",maxSelection,normalRequest)를 기존 ActivityResult launcher에서 실행한다. 원래의 요청이 반환한 결과라면 원래 앱 처리 규약을 사용한다. Image Order 요청을 사용한 경우 readResult는 ClipData 순서를 그대로 읽는다. 호스트는 순번을 보존해 준비/업로드하고 취소를 존중한다. 앱 제거 등 launch race가 발생하면 ActivityNotFoundException에서 기존 요청을 다시 실행할 수 있다. Helper는 fallback의 원본 이름/순서를 보장하지 않으며 임의로 변경하지 않는다. 테스트 전용 trust override는 외부 제품에서 사용하지 않는다.

주의: 이 방식은 GPT/Chat LLM/네이버 등 미수정 앱에 자동 적용되지 않는다. 기존 독립 갤러리 UI를 최초 첨부 동작으로 쓰는 협력 연동의 구현 예시다. 플랫폼 picker를 대체하거나 시스템 권한을 변경하지 않는다. 원본 파일명 보존은 Image Order에 정상 갤러리 접근 권한이 있고 원본 MediaStore 경로로 선택할 때의 목표다. 권한 거부 fallback은 시스템 picker의 파일명 제약을 그대로 받는다.
