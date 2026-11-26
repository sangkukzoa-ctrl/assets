# Instructions to the successor model — ordinary ABACUS.AI Chat LLM / DeepSeek Flash 4.1

## Environment and user expectations
- You are in an ordinary Chat LLM chat using **DeepSeek Flash 4.1**, NOT Abacus AI Agent, DeepAgent, or autonomous multi-stage agent mode.
- User expects completed concrete engineering work when a future task exists; avoid repeated re-planning, unsupported declarations and doing nothing. The current user expressly requests **HANDOFF ONLY, NO WORK TO START YET**.
- User speaks Korean, may use frank language; respond clearly in Korean with precise technical terminology.
- The user should not have to re-explain their product goals or the current state when moving sessions.
- "진행" means continue the last **already approved** development task with actual work, not rerun brainstorming. If TASKS has no active approved work (as now), state readiness, do not invent a task.
- Quality takes priority over artificially short responses; report what changed, what was actually run, and file/release URLs.
- Prefer complete source and reproducible ZIP/package or source branch rather than lone snippets. Avoid creating files that overwrite other projects.

## Startup in a fresh conversation — no questions unless absolutely required
1. Read HANDOFF/00_START_HERE.md and HANDOFF/STATE.json.
2. Read HANDOFF/TASKS.md and other handoff docs.
3. Fetch GitHub branch pdfimage-handoff/2026-11-26, inspect real project/app/build.gradle, manifest and Java source.
4. Verify the canonical v1.3.1 public release and its assets before assuming latest.
5. Check what code-edit/write, GitHub Actions and artifact retrieval tools are **actually available in the present normal Chat LLM environment**. Chat LLM may have GitHub connector in certain configurations but read-only access must not be confused with write/run permission. Do not use Abacus AI Agent as a workaround.
6. Initial response should state successful/failed source loading, release identity, known current state, and explicitly **no pending development task**. Do not modify product or create a new release now.

## When the user assigns a new task later
1. Identify exact scope, acceptance criteria and files; carry forward all unchanged constraints.
2. Start from verified source under project/, preferably a new isolated branch. Avoid unrelated assets/ branches.
3. Read code before proposing edits. Use smallest well-justified changes, preserve native UX and offline-only scope.
4. Add tests proportional to risk; validate actual Gradle build via CI when available, not Java-only test.
5. If issue cannot be reproduced, separate facts from hypotheses, but continue with concrete code/testable fix rather than endless theory.
6. Document existing baseline, changed files, tests and output. Capture actual CI run number, conclusion, commit SHA, app version, artifact links.
7. On explicit release request only, securely manage original production signing identity, verify signature and download links, update bilingual changelog.
8. Update HANDOFF/STATE.json and HANDOFF/TASKS.md and notes **after** action confirmation. Never falsely mark "done" or "released".
9. If Chat LLM tool cannot write or run CI: produce complete revised files and human-readable short instructions; ask user only for essential access/interaction, not a full explanation of project.

## Source-of-truth conventions
- REPO: https://github.com/sangkukzoa-ctrl/assets
- HANDOFF BRANCH: pdfimage-handoff/2026-11-26
- SOURCE ROOT: project/
- DOCUMENTS: HANDOFF/
- STATE: HANDOFF/STATE.json
- WORK BOARD: HANDOFF/TASKS.md
- TAGGED APP RELEASE: v1.3.1 (source/package linked in START_HERE)
- MIXED REPO WARNING: do not change unrelated project files, branches, assets/main or previously published tags.
- The root handoff CI is intentionally nonpublishing.

## State model and reporting discipline
Use JSON state for cross-session continuity. Fields should track:
- last confirmed release and commit;
- working branch/commit;
- task status: no_active_task / active / waiting_for_user / blocked / complete;
- last verified CI status, build artifacts, next action;
- user-approved vs suggested work.

Never treat a suggestion as an assigned task. Never silently broaden the scope from PDF-to-image converter into OCR, PDF-to-PDF, image editor, media player, scanning or cloud features.

## ABACUS.AI practical preparation
A GitHub connector can be useful, but connection and capabilities are account-specific. If GitHub connector is accessible, use it to inspect source; otherwise attach this repo's official source archive and handoff documents to normal Chat LLM. Confirm readable files first. Do not assume a GitHub connector automatically provides shell execution, signing credentials or GitHub Actions write permission. Do not ask the user to enable an agent.
