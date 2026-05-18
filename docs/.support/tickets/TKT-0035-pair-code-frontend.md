---
id: TKT-0035
title: Pair-code frontend toggle + panel on /connect
status: open
priority: P3
area: frontend
created: 2026-05-18T21:48:00Z
updated: 2026-05-18T21:48:00Z
created_by: resolving_agent
related_plan_item: F-03, A1
related_tickets: TKT-0014
filed_via: split_from_TKT-0014
---

## Summary
TKT-0014 shipped the backend half of pair-code mode in iter83: `POST /api/wa/connect` now accepts an optional `{"phone":"+CCXXXXXXXXX"}` body and the `WaState` response includes a `pair_code: str | None` field. The frontend still only renders the QR card. This ticket covers the matching UI.

## Expected
- `frontend/src/app/connect/page.tsx`:
  - Add a small mode-switch above the pairing card: "Scan QR" (default) vs "Use pair code instead".
  - When "Use pair code" is active:
    - Render a phone-input field with helper "Enter the phone number you will type the code on (E.164: +CC followed by digits)".
    - "Get pair code" button calls `auth-routed` `apiFetch` to `POST /api/wa/connect` with `{phone}`. Validate client-side: trim, must start with `+`, total length 8-16.
    - On 200, poll `/api/wa/state` (already happens via `useWaState` SWR refresh) and render `<PairCodePanel code={waState.pair_code} />` with "Open WhatsApp on your phone -> Settings -> Linked devices -> Link with phone number -> type this code:" and a large monospace 4-3 chunked display of the 8-char code (e.g. `ABCD-EFG1`).
    - On 422 invalid_phone: inline error toast.
  - When the mode-switch flips back to "Scan QR", call `POST /api/wa/connect` with no body so wars resumes the QR flow.

- `frontend/src/components/connect/PairCodePanel.tsx` (new) -- pure presentational; takes `{ code: string | null }`. When `code` is null, shows "Waiting for pair code...".

- `useWaState` already polls; no hook changes required other than reading `waState.pair_code`.

## Acceptance
- `npx tsc --noEmit` exit 0.
- The /connect page has a working mode-switch.
- Submitting a valid phone surfaces an 8-character code in `<PairCodePanel>` once wars returns it.

## Resolution history
- 2026-05-18T21:48:00Z -- filed by Resolving Agent (iter83) as the frontend follow-on to TKT-0014. Backend (worker pair_code state + WaState schema + /api/wa/connect body extension) is verified-in-place; frontend remains.
