# TASKS — 2026-11-26

## Approved active tasks
**NONE.** The user explicitly requested **handoff only**. No new implementation, bug fix, CI run, app store registration, new tag, or release has been assigned.

## Completed handoff (documentation, not app development)
- [x] Verified latest public release v1.3.1 and its signed APK, signed AAB, source ZIP, and GitHub Actions success.
- [x] Preserved product identity "Just PDF to Image" and developer "2bornot", KO+EN.
- [x] Created isolated handoff branch without changing assets/main.
- [x] Downloaded official v1.3.1 source ZIP in GitHub Actions, SHA-256 verified and restored original Java/Gradle source under project/.
- [x] Added nonpublishing handoff CI workflow for future approved development.
- [x] Wrote handoff documents and ready-to-paste starter prompt for ordinary ChatLLM/DeepSeek Flash 4.1.
- [ ] Optional step pending no user action: successor model verifies actual GitHub connector permissions inside their own Chat LLM conversation (cannot be preverified here).

## Session startup acceptance
The next model should confirm repo/branch and project source are readable, compare current version to v1.3.1, and report **ready with no work pending**. It should not silently initiate any tasks.

## Future work request record template (fill ONLY after user instruction)
Task ID:
Requested by user:
Scope:
Constraints:
Approved acceptance criteria:
Affected files:
Branch:
Last confirmed commit:
Build/run URL:
Tests performed:
Release permission (YES/NO):
Results:
Remaining/blocked:
Next exact action:

## Prohibited premature to-dos
- No exhaustive new feature roadmap unless user requests it.
- No store resubmission plan or payments.
- No rebuilding just because the handoff occurred.
- No production signing key upload to source control, ChatLLM attachments, logs, or artifact.
- No APK publication based only on compile success.
