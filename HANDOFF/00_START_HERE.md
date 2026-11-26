# START HERE — Just PDF to Image / 2bornot

## This is the authoritative handoff for ABACUS.AI Chat LLM (normal chat), DeepSeek Flash 4.1
Handoff prepared 2026-11-26 (Asia/Seoul). **The user has NOT requested a new feature, bug fix, or release.** Your initial duty is to read, verify access, and acknowledge readiness. **Do not start coding, changing APKs, or publishing.**

**Mode:** Standard CHAT LLM conversation. **Do not invoke an Agent/DeepAgent workflow.** In case Chat LLM has no GitHub write/run permission, explain accurately and deliver complete, uploadable files or diffs rather than claiming changes.

### Project identity
- Product name (EN and KO): **Just PDF to Image**
- Developer / publisher identity: **2bornot**
- Slogan (KO): **PDF를 이미지로. 그게 전부입니다.**
- Slogan (EN): **PDF to images. Nothing else.**
- Platform: native Android Java app; Android 8.0+ (API >=26)
- GitHub linked account/repository: sangkukzoa-ctrl/assets. This is a **shared repository with unrelated projects**; avoid changing main or unrelated files.
- Official latest confirmed published release: **v1.3.1** (2026-11-06). Maintained as signed update from v1.3.0.
- Canonical release: https://github.com/sangkukzoa-ctrl/assets/releases/tag/v1.3.1
- Canonical source ZIP: https://github.com/sangkukzoa-ctrl/assets/releases/download/v1.3.1/JustPDFtoImage-v1.3.1-Source.zip
- SHA-256 file: https://github.com/sangkukzoa-ctrl/assets/releases/download/v1.3.1/SHA256SUMS.txt
- Official completed release workflow: https://github.com/sangkukzoa-ctrl/assets/actions/runs/42159936750
- This handoff's source-as-text: **project/** in branch **pdfimage-handoff/2026-11-26**
- Original release build tag commit: 8394fbb356a810243d3f4dc8d5259be4580648f8
- Official APK: https://github.com/sangkukzoa-ctrl/assets/releases/download/v1.3.1/JustPDFtoImage-v1.3.1.apk
- Official AAB: https://github.com/sangkukzoa-ctrl/assets/releases/download/v1.3.1/JustPDFtoImage-v1.3.1.aab

### First-run reading order
1. HANDOFF/STATE.json — current state, source of truth and pending work.
2. HANDOFF/TASKS.md — explicit absence of immediate tasks and future request discipline.
3. HANDOFF/01_PRODUCT_AND_ARCHITECTURE.md — requirements and real source layout.
4. HANDOFF/02_BUILD_AND_ENVIRONMENT.md — working GitHub Actions, exact versions.
5. HANDOFF/03_RELEASE_AND_SECURITY.md — signing/update and publishing controls.
6. HANDOFF/04_CHATLLM_WORKFLOW.md — ordinary ChatLLM operating protocol.
7. HANDOFF/05_VERIFICATION_AND_HISTORY.md — validated facts vs pending empirical evidence.
8. HANDOFF/INITIAL_PROMPT_KO.md — starter prompt the user can paste if needed.
9. Browse real Java/Gradle files in project/; **read the code, do not invent missing implementations**.

### Priority of evidence when things disagree
1. Published release v1.3.1 and its signed APK/source/checksum.
2. Actual contents of project/ (materialized unmodified official release source).
3. Successful historical GitHub Actions run logs.
4. HANDOFF/STATE.json and change records (these document intent/status, not override actual source).
5. Conversation summaries and external market assumptions.

### Current acceptance condition for this handoff
- project/ contains actual original v1.3.1 source, not screenshots or fake test PDFs.
- Handoff documentation exists and an ordinary-chat model can inspect the source.
- A safe, no-publishing GitHub Actions workflow is available in .github/workflows/pdfimage-handoff-ci.yml.
- No new release or functional modification is authorized.
- The future model can respond to "진행" by reading STATE/TASKS and continuing the last user-approved task **when one exists**; at this handoff there is intentionally no active task.

### Critical dos and don'ts
- Preserve free / no ads / no account / no web connection / no conversion limits / no broad file access / no unrelated utilities.
- Do not add analytics, advertisements, online PDF uploads, or MANAGE_EXTERNAL_STORAGE.
- Do not change applicationId or signing identity inadvertently; package remains **com.hsiwan.pdfimage**.
- Never upload or print production keystore (.p12/.jks), passwords, or backups to a public repo, ChatLLM upload, or workflow artifact.
- Unit tests/build success is not proof of full device coverage.
- State what's actually done; never call something shipped when only source or unsigned APK exists.
