# Iteration 46 — Resolving Agent (TKT-0005)

- **Started**: 2026-05-18T18:37:10Z
- **Phase**: resolving
- **Active agent**: resolving_agent
- **Ticket**: TKT-0005 (P2 backend) -- surface owner_phone after wars pairing

## Plan
1. Mark TKT-0005 `inprogress`.
2. Discovery: dump the wars 0.1.3 `WhatsApp` instance API to find an owner / me / jid attribute. The ticket guessed wars exposes the data via the single-arg `wa.send(text)` -> "routes to owner" mechanism but no accessor.
3. If a direct accessor exists -> read it inside `_check_connected` / `_on_connected` (worker thread, PyO3-safe) and update `WaSingleton._state.owner_phone`.
4. If no accessor exists -> fall back to setting `owner_phone` from `wa.export_session()` parsing (last resort) OR from the user's `WATIFY_OWNER_PHONE` env (operator-set, defensive).
5. Update `/api/wa/state` DTO (already includes `owner_phone`) and the frontend Ready panel which falls back to "this device" today.
6. Mark TKT-0005 `resolved`.

## Actions
