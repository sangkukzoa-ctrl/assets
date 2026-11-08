# ChatLens OCR v0.4.6 — QA 8/8 final review

**Developer:** 2bornot · **Copyright © 2026 2bornot** · [MIT License](ChatLensOCR/LICENSE)

**Source tested:** `84bf890b8dddf55bf417889b49675c1b9d5e3930`

**Verified Windows x64 build:** https://github.com/sangkukzoa-ctrl/assets/actions/runs/42464851957  
**Download:** from the run's Artifacts section → `ChatLensOCR-v0.4.6-Round8-Windows-x64`. This contains a ZIP with `ChatLensOCR_v0.4.6.exe` and SHA256 digest file.

## Evidence and interpretation

- **34/34** screenshots SHA256 matched previous QA. This confirms identical input, **not** perfect OCR.
- **11/11** shopping-catalog screenshot structures detected.
- **5/5** Windows Explorer grid screenshot structures detected.
- **57** KakaoTalk speech-bubble crops rechecked.
- **14/16 (87.5%)** manually confirmed KakaoTalk phrases matched independently reproduced localized Linux Tesseract results. This is **not** whole-corpus Windows EXE character accuracy.
- **2 unresolved phrases:** `오잉` is frequently read as `으잉`; `퉤` can be empty or another glyph. **60 additional image-preprocessing/language/segmentation combinations: zero exact results.** No forced dictionary substitutions.
- The existing correction of `12시라고잡아야1시에오켓지` → `12시라고잡아야1시에오겠지` remained correct with no regressions in the 57-bubble audit.
- Full hand-verified text ground truth for all 34 images is not yet available.

## Round 8 deliverables

- Locate unreadable `[글자 미인식]` results with the **미인식 찾기** button or **Ctrl+G**.
- Correct extracted TXT in the result editor before copying/saving.
- JSON export keeps original OCR evidence; if the user edits the visible TXT, it adds `user_edited_full_txt` and `user_edited_note` to the first record without changing the original output fields or list structure.
- Normal public-facing UI omits internal QA progress counters.
- Cumulative QA rounds 1–8, specialized OCR integration, frozen EXE offline self-test, Windows version metadata (`2bornot`), EXE/ZIP SHA256 and GitHub provenance attestation all passed.

### Verified checksum

```text
5c4f836cb02940931d112ead8ae33e595bf4e1cb3236a24b0ea0800a36f44331  ChatLensOCR_v0.4.6.exe
dc31d6643f0750226e838ed26286109ad6e46f8e7f50b3aa5642a7593cecb615  ChatLensOCR_v0.4.6_Windows_x64.zip
```

## Release decision

**v0.4.6 is approved as a usable quality-assurance release candidate; stable public release is deferred.**

Reasons: two remaining manually-confirmed OCR errors; no complete text gold corpus across 34 images; and **Authenticode code signing is not configured**. Build provenance attestation is **not** Authenticode signing. SignPath Foundation application and manual approval are still required. The earlier public v0.4.1 unsigned preview remains separate.

SignPath prep: [application material](CHATLENS_SIGNPATH_APPLICATION.md) · [signing policy](ChatLensOCR/CODE_SIGNING_POLICY.md).
