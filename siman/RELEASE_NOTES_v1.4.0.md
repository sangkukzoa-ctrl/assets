# 심안 (心眼) v1.4.0 — ChatLLM / Claude collector fix (Preview)

- Removed invalid ChatLLM `/api/listDeploymentConversations` requests without required deployment context.
- Added passive discovery of actual ChatLLM / Claude read-only list queries (no API key or model tokens).
- Added pagination based on observed offset/cursor, per-session detail reads, and resilient explicit error states.
- Fixed Claude zero-conversation reporting that previously looked successful.
- Preserved existing ChatGPT archive and 429 pacing behavior.

## Tests

- Node regression: ChatLLM observed list, two-page project data, details + full-text search.
- Node regression: Claude org/list/details and zero-record diagnostic.
- Windows CMD installation and update test through GitHub Actions (run status below).

**Preview limitations:** No authorized live account access for ChatLLM / Claude in our build environment. Passing regression tests does not prove exhaustive indexing of a real account. Chrome Web Store signing is not completed.
