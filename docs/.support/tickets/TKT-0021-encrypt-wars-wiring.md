---
id: TKT-0021
title: Wire encrypted wars session into WaSingleton boot + on_connected + auto-migration
status: open
priority: P1
area: backend
created: 2026-05-18T17:48:00Z
updated: 2026-05-18T17:48:00Z
created_by: resolving_agent
related_plan_item: B-05, S3
related_tickets: TKT-0011
---

## Summary
TKT-0011 split. iter36 (TKT-0011) landed the infrastructure: `WaSession` model, `WATIFY_SESSION_ENCRYPTION_KEY` setting, `app/session_crypto.py` (encrypt/decrypt/save/load/clear), 6-case smoke script green. This ticket wires that infrastructure into the running app.

## Expected
When `WATIFY_SESSION_ENCRYPTION_KEY` is set:
1. **Auto-migrate on startup**: if `backend/whatsapp.db` exists AND `WaSession` row is empty, open the file with wars, call `export_session()`, encrypt+`save_session(...)`, then delete the file plus its `-wal`/`-shm` siblings. Log a one-line `wars-session: migrated whatsapp.db -> encrypted blob` line. One-shot; subsequent boots skip this block.
2. **Boot from blob**: if `WaSession` row exists, `WhatsApp.from_bytes(load_session(db, key))` instead of `WhatsApp(db_path)`.
3. **Persist on connect**: in the worker's `_check_connected` (or on the first successful `on_connected`), call `wa.export_session()` -> `save_session(db, blob, key)`. This refreshes the stored ciphertext with any new device-list / key-rotation state that wars accumulated.
4. **Clear on user-initiated unpair**: extend `disconnect()` with an optional `unpair=True` parameter (default False) that, when true, calls `clear_session(db)` so the user can rebuild from scratch.

When `WATIFY_SESSION_ENCRYPTION_KEY` is unset, behavior is unchanged from today (file-backed `whatsapp.db`).

## Fix sketch
- `app/whatsapp.py` `_worker_loop`:
  - Top of the function: try the migration + boot-from-blob path; fall back to current `WhatsApp(str(DB_PATH))` if no key set.
  - `_check_connected` re-export-and-persist when state flips to `ready` for the first time.
- README troubleshooting + setup adds the key-generation snippet.

## Acceptance
- With key set and no existing `whatsapp.db`: pair, restart, no re-pair needed (boot reads encrypted blob).
- With key set and an existing `whatsapp.db`: backend boot auto-migrates; whatsapp.db is gone after first run; session resumes.
- With key unset: legacy mode -- unchanged.

## Resolution history
- 2026-05-18T17:48:00Z -- filed by Resolving Agent (iter36) as the wiring follow-up to TKT-0011a.
