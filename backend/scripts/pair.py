"""Headless / CLI pairing for Watify.

Use the web UI (visit /connect) for normal day-to-day pairing. This
script exists for headless boxes where a browser is not available.

Run from `backend/`:
    uv run python scripts/pair.py

It will render an ASCII QR in the terminal (per wars.md fallback) and
block up to 5 minutes waiting for you to scan with WhatsApp. The
paired session lands in backend/whatsapp.db, which is gitignored.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.settings import settings  # noqa: E402
from wars import WhatsApp  # noqa: E402


def main() -> int:
    db_path = settings.whatsapp_db
    print(f"Watify pair: using session db at {db_path}")
    wa = WhatsApp(db_path)
    print("Waiting for QR (up to 5 minutes). Open WhatsApp -> Linked devices.")
    try:
        wa.pair(timeout=300)
    except TimeoutError:
        print("Pair timed out. Re-run when ready.", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Pair cancelled.", file=sys.stderr)
        return 130
    print("Paired. The web UI at http://localhost:3000/connect will now show Connected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
