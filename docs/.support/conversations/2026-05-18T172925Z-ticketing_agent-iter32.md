# Iteration 32 — Ticketing Agent (openalgo gap sweep)

- **Started**: 2026-05-18T17:29:25Z
- **Phase**: ticketing
- **Active agent**: ticketing_agent

## Trigger
Per iter30 conversation log, the user supplied a reference WhatsApp integration at `docs/.support/openalgo/` and asked for a gap analysis. Filing the findings as 9 tickets (TKT-0011..TKT-0019), priorities per impact and effort.

## Actions
Files written under `docs/.support/tickets/`:
- TKT-0011 (P1 backend): encrypt wars session at rest.
- TKT-0012 (P2 backend): RUST_LOG defaults to silence wars protocol noise.
- TKT-0013 (P2 backend): lazy wars import + WarsNotInstalled sentinel.
- TKT-0014 (P2 backend+frontend): pair-code mode alongside QR.
- TKT-0015 (P2 backend): real rate-limit middleware on send endpoints.
- TKT-0016 (P3 backend): pair state machine -- paired distinct from ready.
- TKT-0017 (P3 backend): JID helpers `phone_to_jid` / `jid_to_phone`.
- TKT-0018 (P3 frontend): SSE / SocketIO push of QR instead of polling.
- TKT-0019 (P2 backend): auto-cycle wars after N seconds without `on_qr` so the 5-minute pairing window doesn't silently die. Surfaced during iter31 verification.

## Decisions
- Order of resolution recommended after this sweep:
  1. TKT-0011 (encrypt-at-rest) -- highest security value.
  2. TKT-0012 (RUST_LOG) and TKT-0013 (lazy import) -- one-line wins, group them.
  3. TKT-0019 (auto-cycle) -- direct UX impact on pairing.
  4. TKT-0014, TKT-0015 (pair-code, rate limit) -- bigger features.
  5. TKT-0016, TKT-0017, TKT-0018 -- polish.
- PIPELINE advances to `resolving_agent` since multiple P1/P2 tickets are now open.

## Next iteration
**Resolving Agent** picks TKT-0011 (P1 encrypt wars session at rest).
