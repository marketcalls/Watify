# Iteration 39 — Verification Agent (TKT-0021)

- **Started**: 2026-05-18T18:01:04Z
- **Phase entering**: verification
- **Active agent**: verification_agent
- **Ticket under test**: TKT-0021 -- wire encrypted wars session

## Plan
This verification touches the live paired session. Safety first:
1. Backup `whatsapp.db` family to `.support/logs/whatsapp.db.preverify.bak`. If the migration loses the pair we can restore.
2. Generate a Fernet key with `app.session_crypto.generate_key()`. Write `WATIFY_SESSION_ENCRYPTION_KEY=...` into `backend/.env`.
3. Kill backend; restart.
4. Watch for the 4 migration log lines in order:
   - `wars: encrypted mode -- WaSession empty, whatsapp.db exists; will migrate on first ready`
   - state -> ready via `on_connected` OR the TKT-0020 fallback
   - `wars: persisted encrypted session (plaintext=...B)`
   - `wars: legacy whatsapp.db removed -- encrypted mode is now the only at-rest store`
5. Confirm `backend/whatsapp.db*` is gone; `WaSession` row exists with non-empty ciphertext.
6. Restart a second time: expect `wars: encrypted mode -- booting from WaSession row (...B plaintext, in-memory)` and state flips to ready without touching the disk file.
7. On pass: commit + push. Leave the key in `.env` (gitignored) for the operator's future runs.
8. On fail: restore backup, remove the env line, restart, surface the failure mode in the ticket history.

## Actions
