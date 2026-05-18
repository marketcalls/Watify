---
id: TKT-0011
title: Encrypt wars session at rest (Fernet blob in app.db, temp-DB pair flow)
status: open
priority: P1
area: backend
created: 2026-05-18T17:29:25Z
updated: 2026-05-18T17:29:25Z
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
