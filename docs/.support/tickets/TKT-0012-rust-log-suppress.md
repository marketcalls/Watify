---
id: TKT-0012
title: Suppress noisy wars / whatsapp-rust / wacore log output via RUST_LOG defaults
status: open
priority: P2
area: backend
created: 2026-05-18T17:29:25Z
updated: 2026-05-18T17:29:25Z
created_by: ticketing_agent
related_plan_item: B-05, B-08
filed_via: gap_analysis
---

## Summary
`docs/.support/logs/backend.log` interleaves Watify INFO lines with wars/whatsapp-rust protocol noise. Three categories spam normal operation:

| Source | Example | Why it fires |
|---|---|---|
| `wacore::send` | `WARN Failed to encrypt for device: <stale-LID>: session not found. Skipping.` | Stale linked-device entries in a contact's device list; wars silently routes around them. |
| `whatsapp_rust::message` | `WARN Decryption still failed after PN->LID migration: SessionNotFound` | Incoming message from a device wars has no Signal session for; wars dispatches `UndecryptableMessage` and keeps running. |
| `wacore_libsignal::protocol::session_cipher` | `ERROR Message from <LID> failed to decrypt; ... No current session` | Lower-level libsignal log already handled by `whatsapp_rust::message`. |

None are actionable for the operator. LIDs are privacy-preserving identifiers, not phone numbers -- redaction is not the concern; sheer noise is.

## Reference
`docs/.support/openalgo/services/whatsapp_bot_service.py` top-of-file sets a `RUST_LOG` default via `os.environ.setdefault(...)` before importing wars, leaving each operator free to override for diagnostics.

## Expected
- `os.environ.setdefault("RUST_LOG", "error,wacore::send=off,whatsapp_rust::message=off,wacore_libsignal::protocol::session_cipher=off")` near the top of `app/whatsapp.py` BEFORE `from wars import ...`.
- Documented in README troubleshooting that `RUST_LOG=debug` (or any value the operator wants) is honored.

## Fix sketch
1. Edit `backend/app/whatsapp.py` -- the `setdefault` call must precede `from wars import ...`.
2. Note in README that the default suppresses three protocol-noise loggers and how to re-enable.

## Resolution history
- 2026-05-18T17:29:25Z -- filed by Ticketing Agent (iter32).
