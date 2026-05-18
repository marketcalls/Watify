"""Smoke test for app/session_crypto.py.

Generates a Fernet key, round-trips a fake "session blob" through
encrypt/decrypt, then persists+loads via SQLModel. No wars touched.

Run from `backend/`:
    uv run python scripts/smoke_crypto.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session  # noqa: E402

from app.db import engine, init_db  # noqa: E402
from app.session_crypto import (  # noqa: E402
    SessionCryptoError,
    clear_session,
    decrypt_blob,
    encrypt_blob,
    generate_key,
    has_session,
    load_session,
    save_session,
)


def main() -> int:
    init_db()
    key = generate_key()
    assert len(key) == 44, f"unexpected fernet key length: {len(key)}"
    print(f"generate_key() ok len={len(key)} (value redacted)")

    fake_blob = b"\x00\x01\x02\x03" * 75_000  # ~300 KB, the size of a real wars session
    ct = encrypt_blob(fake_blob, key)
    assert ct != fake_blob, "ciphertext == plaintext (encryption is a no-op)"
    pt = decrypt_blob(ct, key)
    assert pt == fake_blob, "decrypt round-trip mismatch"
    print(f"encrypt/decrypt round-trip ok plaintext={len(fake_blob)}B ciphertext={len(ct)}B")

    bad_key = generate_key()
    try:
        decrypt_blob(ct, bad_key)
    except SessionCryptoError:
        print("decrypt with wrong key correctly raised SessionCryptoError")
    else:
        print("ERROR: decrypt with wrong key did NOT raise")
        return 1

    with Session(engine) as db:
        clear_session(db)
        db.commit()
        assert not has_session(db), "clear_session left a row behind"

        save_session(db, fake_blob, key)
        db.commit()
        assert has_session(db), "save_session did not persist"

        loaded = load_session(db, key)
        assert loaded == fake_blob, "load_session round-trip mismatch"
        print(f"save/load round-trip ok ({len(loaded)}B)")

        # Overwrite with a different blob -> upsert semantics
        new_blob = b"\xff" * 1024
        save_session(db, new_blob, key)
        db.commit()
        loaded2 = load_session(db, key)
        assert loaded2 == new_blob, "upsert did not replace ciphertext"
        print("upsert ok")

        clear_session(db)
        db.commit()
        assert not has_session(db), "clear_session after upsert failed"
        print("clear ok")

    print("ALL CRYPTO SMOKE TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
