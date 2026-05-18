# Iteration 38 — Resolving Agent (TKT-0021)

- **Started**: 2026-05-18T17:56:44Z
- **Phase**: resolving
- **Active agent**: resolving_agent
- **Ticket**: TKT-0021 (P1 backend) — wire encrypted wars session into WaSingleton

## Plan
1. Mark TKT-0021 `inprogress`.
2. Refactor `_worker_loop` in `app/whatsapp.py`:
   - New `_build_wa()` helper returns `(wa, migrated_from_file: bool)` and picks the constructor based on `settings.session_encryption_key`:
     - Unset -> `WhatsApp(str(DB_PATH))` (legacy file-backed mode).
     - Set + `WaSession` row exists -> `WhatsApp.from_bytes(decrypted_blob)` (in-memory, no disk file).
     - Set + no row but `whatsapp.db` exists -> `WhatsApp(str(DB_PATH))` with migration flag = True; the first successful pair / on_connected will export+save+delete-file.
     - Set + neither -> `WhatsApp()` (fresh in-memory, awaits pair).
   - New `_persist_session()` closure called on every state -> ready transition: `wa.export_session()` -> Fernet-encrypt -> upsert `WaSession`. If `migrated_from_file` is true, also delete `whatsapp.db` + sidecars and clear the flag.
   - Hook `_persist_session()` into both `_on_connected` (when wars fires it) AND the existing TKT-0020 `_check_connected` fallback (so post-restart re-handshake also re-persists).
3. Behavior matrix:
   - Operator with NO key set: zero change. Continues using `whatsapp.db` file.
   - Operator who sets the key today and restarts: legacy `whatsapp.db` migrated to encrypted blob on first ready; file deleted. Next restart boots from blob (no file).
4. `py_compile`. **Do NOT restart the backend** (would interrupt the live paired session); Verification Agent will respawn in a controlled way and toggle the key.
5. Mark TKT-0021 `resolved`.

## Risks + mitigations
- `wa.export_session()` may fail on a wars instance that isn't yet connected. Per wars docs it works on a paired session. The persist call is gated on `state == "ready"`, so wars has accepted the pair by then. `_persist_session` is wrapped in try/except so a failure doesn't crash the worker.
- The `from_bytes` path is in-memory. If the process dies without a re-persist, the wars state may have drifted from the blob (key rotations etc). For v1 we accept this: we re-persist on every ready transition, so the blob stays current across restarts.

## Actions
