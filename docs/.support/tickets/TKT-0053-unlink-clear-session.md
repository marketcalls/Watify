---
id: TKT-0053
title: Add Unlink action that wipes the encrypted wa_session row + legacy whatsapp.db files
status: open
priority: P2
area: backend+frontend
related_tickets: TKT-0011, TKT-0010
created: 2026-05-19T03:10:00Z
updated: 2026-05-19T03:10:00Z
created_by: resolving_agent
filed_via: user_request
---

## Summary
Operator: "it should delete the session right?" Currently Disconnect tears down wars's runtime state but the persisted session blob (encrypted `wa_session` row in `app.db` plus the legacy `whatsapp.db*` files when session encryption is unset) survives. Next connect re-imports from the blob and the device stays linked.

The operator expected Disconnect to be a full unlink. Splitting the affordance is the right move:
- Disconnect (current) -- runtime-only teardown; session blob preserved. Cheap; lets the operator re-pair without re-scanning.
- Unlink (new) -- full session wipe; next pair requires a fresh QR/pair-code scan.

## Approach
1. Backend `WaSingleton.unlink()` -- after disconnect, delete the WaSession row (or zero it) AND `_delete_legacy_wa_db_files()` so a subsequent connect goes fresh.
2. Backend route `POST /api/wa/unlink` -- auth-required, CSRF-required, calls `WaSingleton.unlink()`. Returns the post-unlink WaState.
3. Frontend ReadyPanel adds an "Unlink device" button next to Disconnect. Confirm dialog warns "Re-pairing will require scanning a fresh QR. Continue?"
4. After unlink: state -> disconnected, pair_code/qr cleared, owner_phone cleared.

## Acceptance
- POST /api/wa/unlink with cookies -> 200, returns disconnected state.
- `app.db` wa_session row gone (count == 0).
- Legacy `whatsapp.db` files gone (Windows may hold them open; sweep on next boot).
- After Unlink, clicking Start pairing fires a fresh QR/pair-code flow (no resume from blob).

## Resolution history
- 2026-05-19T03:10:00Z -- filed per operator question "it should delete the session right?".
