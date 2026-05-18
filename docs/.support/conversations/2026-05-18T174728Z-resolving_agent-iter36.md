# Iteration 36 — Resolving Agent (TKT-0011a infrastructure)

- **Started**: 2026-05-18T17:47:28Z
- **Phase**: resolving
- **Active agent**: resolving_agent
- **Ticket**: TKT-0011 (P1 backend) — encrypt wars session at rest

## Scope decision: split TKT-0011 across two iterations
The full ticket spans: new DB table, Fernet crypto, settings key, WaSingleton boot/save refactor, auto-migration of an existing `whatsapp.db`, README. Trying to land all of that in one iteration while the operator has a live paired session is too risky — a mid-refactor regression would force a re-pair.

Splitting:

- **TKT-0011a (this iteration)**: infrastructure only — `WaSession` table, `WATIFY_SESSION_ENCRYPTION_KEY` setting, `app/session_crypto.py` helpers, smoke script. No production wiring; live session unaffected.
- **TKT-0011b (next iteration)**: wire into WaSingleton — boot prefers encrypted blob via `from_bytes`, `on_connected` persists, auto-migrate any existing `whatsapp.db`, delete the file.

This iteration ships 0011a. Filing TKT-0011b as a follow-up.

## Plan
1. Mark TKT-0011 `inprogress`.
2. `uv add cryptography`.
3. New SQLModel `WaSession(id pk=1, ciphertext: bytes, created_at, updated_at)` -- singleton row.
4. `app/settings.py` adds `session_encryption_key: str | None = None` and a `session_storage_mode` derived property.
5. `app/session_crypto.py` exposes:
   - `encrypt_blob(blob: bytes, key: str) -> bytes`
   - `decrypt_blob(ciphertext: bytes, key: str) -> bytes`
   - `save_session(session: Session, ciphertext: bytes) -> None`
   - `load_session(session: Session) -> Optional[bytes]` (returns plaintext, decrypts internally)
   - `has_session(session: Session) -> bool`
   - `generate_key() -> str` for the CLI bootstrap
6. `backend/scripts/smoke_crypto.py` round-trips a fake blob through encrypt/decrypt and persist/load. Independent verification, no wars touched.
7. `backend/.env.example` documents `WATIFY_SESSION_ENCRYPTION_KEY` + how to generate one.
8. File TKT-0011b for the wiring step.
9. Mark TKT-0011 (well, the 0011a sub-scope) resolved.

## Actions
