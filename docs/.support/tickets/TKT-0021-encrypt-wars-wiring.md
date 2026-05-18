---
id: TKT-0021
title: Wire encrypted wars session into WaSingleton boot + on_connected + auto-migration
status: verified
priority: P1
area: backend
created: 2026-05-18T17:48:00Z
updated: 2026-05-18T18:01:04Z
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
- 2026-05-18T17:56:44Z -- Resolving Agent (iter38) set status to inprogress.
- 2026-05-18T17:58:30Z -- Resolving Agent (iter38) shipped the wiring in `backend/app/whatsapp.py`:
  - **`_build_wa()` classmethod** chooses the wars constructor based on `settings.session_encryption_key`:
    - key unset -> `WhatsApp(str(DB_PATH))` (legacy file mode, no behavior change).
    - key set + WaSession row present -> `WhatsApp.from_bytes(decrypt(...))` (in-memory, no disk file).
    - key set + no row + `whatsapp.db` exists -> `WhatsApp(str(DB_PATH))` and `migrate_state["pending"] = True` (bridge -- migrate on first ready).
    - key set + neither -> `WhatsApp()` (fresh in-memory, awaits pair).
  - **`_persist_session()` closure** lives inside `_worker_loop`, captures `wa` + `migrate_state`. On every state -> ready transition:
    1. `wa.export_session()` -> bytes (try/except; swallow + log on failure so the worker keeps running).
    2. `session_crypto.save_session(db, blob, key)` -> upsert WaSession (try/except, will retry on next ready).
    3. If `migrate_state["pending"]`: `unlink` `whatsapp.db`, `.db-wal`, `.db-shm`, `.db-journal` and clear the flag. Logs `wars: legacy whatsapp.db removed -- encrypted mode is now the only at-rest store`.
  - Hooked into both transition paths: `@wa.on_connected` callback and the TKT-0020 `_check_connected` fallback poll.

  `uv run python -m py_compile app/whatsapp.py` succeeds. **Backend NOT restarted** (live paired session preserved); Verification Agent will respawn with `WATIFY_SESSION_ENCRYPTION_KEY` set to drive the migration end-to-end.

  Status set to `resolved`.
- 2026-05-18T18:01:04Z -- Verification Agent (iter39) PASSED end-to-end after fixing one cross-thread bug found in the field:

  **Bug surfaced during first migration attempt:** `_persist_session` was called directly from inside the `@wa.on_connected` callback. That callback fires on the wars Tokio thread (ThreadId 4), not the worker thread that constructed `wa` (ThreadId 3). `wa.export_session()` inside the callback hit PyO3 `!Send` and panicked -- same root cause as iter8 / TKT-0019. Fix: callback now queues a `persist` command; the worker handles it. `_check_connected` (already on the worker thread) calls `_persist_session` directly -- still safe.

  **Second bug surfaced after first fix succeeded:** on Windows, wars holds open file handles on `whatsapp.db` + sidecars while the in-process wa instance is alive. The in-iteration `unlink()` calls in `_persist_session` silently failed. Fix: a `_delete_legacy_wa_db_files` static method runs in `_build_wa` *before* any wa instance is constructed -- the second backend boot does the cleanup.

  **End-to-end run trace (first boot post-key-set):**
  ```
  wars: encrypted mode -- WaSession empty, whatsapp.db exists; will migrate on first ready
  wars on_connected: state=ready
  wars: persisted encrypted session (plaintext=499712B)
  wars: legacy whatsapp.db still held by wars (Windows file lock); next boot's stale-file sweep will remove it
  ```
  **Second boot:**
  ```
  wars: encrypted mode -- booting from WaSession row (499712B plaintext, in-memory)
  wars: removed 3 stale legacy whatsapp.db file(s) at boot
  wars on_connected: state=ready
  wars: persisted encrypted session (plaintext=499712B)
  ```

  Final disk state: `ls backend/whatsapp.db*` -> no such file or directory. `WaSession` row has the 499712B blob. `state == "ready"` on a poll. The operator's WhatsApp pair survived the migration.

  Status set to `verified`. About to commit `fix(TKT-0021): wire encrypted wars session into WaSingleton` and push.
