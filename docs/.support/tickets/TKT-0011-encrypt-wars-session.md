---
id: TKT-0011
title: Encrypt wars session at rest (Fernet blob in app.db, temp-DB pair flow)
status: verified
priority: P1
area: backend
created: 2026-05-18T17:29:25Z
updated: 2026-05-18T17:51:26Z
created_by: ticketing_agent
related_plan_item: B-05, S3
filed_via: gap_analysis
---

## Summary
`backend/whatsapp.db` is plaintext SQLite on disk containing the linked-device Signal keys and noise-handshake state. Anyone with read access to that file can impersonate the paired WhatsApp account. openalgo encrypts the session blob with Fernet and stores it as a column in the main app DB; the on-disk file used for pairing is short-lived.

## Reference
`docs/.support/openalgo/services/whatsapp_bot_service.py` `start_pair` -- temp-DB at 0600, exports session bytes via `wa.export_session()` per wars.md §3, encrypts via Fernet, stores in `database.whatsapp_db` table column, deletes the temp DB.

## Expected
1. Pair into a temp file (`tempfile.mkstemp(suffix='.db', prefix='watify_pair_')`, chmod 0600).
2. On `on_connected`, call `wa.export_session()` -> Fernet-encrypt with `settings.session_encryption_key` (loaded from env or auto-generated and stored alongside the SQLAlchemy session table).
3. Persist the ciphertext blob into `app.db` (new `WaSession` SQLModel row with `id=1` singleton).
4. Delete the temp DB.
5. On startup, decrypt and `WhatsApp.from_bytes(blob)` to resume.
6. `backend/whatsapp.db` no longer exists at rest -- only the encrypted blob in `app.db`.

## Risks
- Need a stable encryption key. Two options: (a) `WATIFY_SESSION_KEY` in `.env` (operator manages), (b) generate on first run and persist alongside the blob (operator transparent but file-leak still exposes both). (a) is the safer default; document the bootstrap step in README.
- `wa.export_session()` only works on a file-backed DB (see wars.md §3). Confirmed.

## Fix sketch
- `app/models.py`: new `WaSession(id: int pk, ciphertext: bytes, created_at)` table.
- `app/settings.py`: `session_encryption_key: str` (must be set; backend fails to boot with a clear error if missing).
- `app/whatsapp.py`: pair into temp DB, on_connected callback exports + encrypts + writes WaSession row + deletes temp DB; on backend startup, attempt to decrypt and `from_bytes` instead of pair-from-scratch.
- `app/scripts/pair.py`: same temp-DB flow with a CLI affordance.
- README: note the `WATIFY_SESSION_KEY` setup step.

## Resolution history
- 2026-05-18T17:29:25Z -- filed by Ticketing Agent (iter32, openalgo gap analysis).
- 2026-05-18T17:47:28Z -- Resolving Agent (iter36) set status to inprogress, split scope:
  - **TKT-0011 (this ticket)**: infrastructure -- model, settings, helpers, smoke. Ships now.
  - **TKT-0021** (filed iter36): wiring into WaSingleton boot + on_connected + auto-migration of an existing `whatsapp.db`. Ships in a separate iteration so the operator's live paired session isn't disrupted mid-refactor.
- 2026-05-18T17:49:00Z -- Resolving Agent (iter36) shipped 0011a infrastructure:
  - `uv add cryptography` (cryptography 48.0.0, cffi 2.0.0, pycparser 3.0).
  - `backend/app/models.py` adds `WaSession(id=1 singleton, ciphertext: bytes, created_at, updated_at)`.
  - `backend/app/settings.py` adds `session_encryption_key: str | None = None` (env `WATIFY_SESSION_ENCRYPTION_KEY`).
  - `backend/app/session_crypto.py`: `generate_key`, `encrypt_blob`, `decrypt_blob`, `has_session`, `load_session`, `save_session`, `clear_session`, `SessionCryptoError`. Fernet under the hood.
  - `backend/scripts/smoke_crypto.py`: 6 cases all pass on 2026-05-18T17:48Z run. Plaintext 300 KB -> ciphertext 400 KB; wrong key correctly raises `SessionCryptoError`; upsert + clear semantics confirmed.
  - `backend/.env.example` documents the key-generation snippet.
  Status set to `resolved`; awaiting Verification Agent. Live session **unaffected** -- no production code path consumes the new module yet (TKT-0021 will wire it in).
- 2026-05-18T17:51:26Z -- Verification Agent (iter37) PASSED all 6 acceptance points:
  1. `scripts/smoke_crypto.py` re-ran -- 6/6 cases green (round-trip 300 KB -> 400 KB, wrong-key SessionCryptoError, persist, upsert, clear).
  2. All 8 public symbols importable (`generate_key`, `encrypt_blob`, `decrypt_blob`, `has_session`, `load_session`, `save_session`, `clear_session`, `SessionCryptoError`).
  3. `app.db` tables now include `wa_session` (alongside `apscheduler_jobs`, `contact`, `friend_group`, `send_attempt`, `send_job`).
  4. `.env.example` lines 23, 25, 28 cover the docstring, the key-generation snippet, and the commented `WATIFY_SESSION_ENCRYPTION_KEY=` slot.
  5. Live `GET /api/wa/state` returns `state=ready, qr=null` -- paired session preserved, no production code consumes the new module.
  6. All 5 frontend routes still HTTP 200.
  Status set to `verified`. Committed `fix(TKT-0011): encrypt wars session infrastructure` and pushed.
