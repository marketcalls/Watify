---
id: TKT-0013
title: Backend should boot even if the wars wheel is missing
status: open
priority: P2
area: backend
created: 2026-05-18T17:29:25Z
updated: 2026-05-18T17:29:25Z
created_by: ticketing_agent
related_plan_item: B-05, I-04
filed_via: gap_analysis
---

## Summary
`backend/app/whatsapp.py` imports `from wars import WhatsApp, qr_to_data_url` at module top. If the wars wheel is missing or fails to build (Rust toolchain, maturin, platform mismatch), the entire FastAPI app fails to boot -- the operator gets a stack trace and no /api/health, no /api/groups, nothing.

openalgo handles this with a lazy `_import_wars()` helper raising a `WarsNotInstalled` sentinel; the rest of the Flask app boots and the /whatsapp UI surfaces a friendly install hint.

## Reference
`docs/.support/openalgo/services/whatsapp_bot_service.py` lines 224-239:
```python
class WarsNotInstalled(RuntimeError):
    def __init__(self) -> None:
        super().__init__(
            "wars package is not installed. Run `uv sync` or `uv pip install wars` "
            "to enable the WhatsApp integration."
        )

def _import_wars():
    try:
        import wars
        return wars
    except Exception as e:
        raise WarsNotInstalled() from e
```

## Expected
- `app/whatsapp.py` exposes the same `WarsNotInstalled` sentinel + `_import_wars()` helper.
- `WaSingleton._worker_loop` and `WaSingleton._build` call `_import_wars()` inside, not at module top.
- `app/routers/whatsapp.py` catches `WarsNotInstalled` and returns a clear 503 (`{"error":"wars_not_installed","detail":"..."}`).
- Frontend `/connect` page renders the install hint when state stays disconnected and `last_error == "wars_not_installed"`.

## Fix sketch
- Move `from wars import WhatsApp, qr_to_data_url` out of module scope into `_import_wars()`.
- Routers wrap calls to `WaSingleton.connect()` in `try/except WarsNotInstalled`.
- Add `last_error = "wars_not_installed: <pip install instructions>"` propagation.

## Resolution history
- 2026-05-18T17:29:25Z -- filed by Ticketing Agent (iter32).
