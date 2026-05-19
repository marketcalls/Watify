"""Smoke test for TKT-0023 (auth model + crypto + repo).

Tests hash/verify round-trip, register-once lock, refresh-secret
rotation, and timing-safe `verify_credentials` path. Cleans up the
created user row at the end so the next run starts fresh.

Run from `backend/`:
    uv run python scripts/smoke_auth.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session  # noqa: E402

from app.auth_crypto import (  # noqa: E402
    generate_refresh_secret,
    hash_password,
    verify_password,
)
from app.auth_repo import (  # noqa: E402
    RegistrationClosed,
    count_users,
    create_admin,
    get_singleton,
    get_user,
    rotate_refresh_secret,
    touch_last_login,
    update_credentials,
    verify_credentials,
)
from app.db import engine, init_db  # noqa: E402
from app.models import User  # noqa: E402


def main() -> int:
    init_db()

    # --- hash + verify round-trip ---
    h = hash_password("correct horse battery staple")
    assert h.startswith("$argon2id$"), "expected argon2id hash"
    assert verify_password("correct horse battery staple", h) is True
    assert verify_password("wrong password", h) is False
    print("hash/verify round-trip ok")

    # --- refresh secret randomness ---
    s1 = generate_refresh_secret()
    s2 = generate_refresh_secret()
    assert s1 != s2 and len(s1) >= 40
    print("refresh secret entropy ok")

    with Session(engine) as db:
        # --- start clean ---
        existing = get_singleton(db)
        if existing is not None:
            db.delete(existing)
            db.commit()
        assert count_users(db) == 0, "table not empty after cleanup"

        # --- create once ---
        user = create_admin(db, "admin", "correct horse battery staple")
        db.commit()
        db.refresh(user)
        assert user.id == 1
        assert user.username == "admin"
        assert user.password_hash.startswith("$argon2id$")
        assert user.refresh_secret
        print(f"create_admin ok (id={user.id}, hash_len={len(user.password_hash)})")
        assert count_users(db) == 1

        # --- register-once lock ---
        raised = False
        try:
            create_admin(db, "second", "another password")
        except RegistrationClosed:
            raised = True
        assert raised, "second create_admin did not raise RegistrationClosed"
        print("register-once lock ok")

        # --- verify_credentials happy path ---
        u = verify_credentials(db, "admin", "correct horse battery staple")
        assert u is not None and u.id == 1
        print("verify_credentials(good) -> user")

        # --- verify_credentials wrong password ---
        u = verify_credentials(db, "admin", "wrong")
        assert u is None
        print("verify_credentials(bad password) -> None")

        # --- verify_credentials unknown username ---
        u = verify_credentials(db, "nobody", "anything")
        assert u is None
        print("verify_credentials(unknown user) -> None (timing-padded)")

        # --- rotate refresh secret ---
        old = user.refresh_secret
        rotate_refresh_secret(db, user)
        db.commit()
        db.refresh(user)
        assert user.refresh_secret != old
        print("rotate_refresh_secret changed the value")

        # --- touch last_login ---
        touch_last_login(db, user)
        db.commit()
        db.refresh(user)
        assert user.last_login_at is not None
        print("touch_last_login set timestamp")

        # --- update_credentials: username only ---
        old_hash = user.password_hash
        old_secret = user.refresh_secret
        update_credentials(db, user, new_username="admin2", new_password=None)
        db.commit()
        db.refresh(user)
        assert user.username == "admin2"
        assert user.password_hash == old_hash, "password_hash should not change"
        assert user.refresh_secret != old_secret, "refresh_secret should rotate"
        print("update_credentials(username only) ok")

        # --- update_credentials: password only ---
        old_hash = user.password_hash
        old_secret = user.refresh_secret
        update_credentials(db, user, new_username=None, new_password="new fresh passphrase!")
        db.commit()
        db.refresh(user)
        assert user.username == "admin2", "username should not change"
        assert user.password_hash != old_hash, "password_hash should rotate"
        assert user.refresh_secret != old_secret, "refresh_secret should rotate"
        assert verify_credentials(db, "admin2", "new fresh passphrase!") is not None
        assert verify_credentials(db, "admin2", "correct horse battery staple") is None
        print("update_credentials(password only) ok")

        # --- update_credentials: both at once ---
        update_credentials(
            db, user, new_username="admin3", new_password="another fresh passphrase!"
        )
        db.commit()
        db.refresh(user)
        assert user.username == "admin3"
        assert verify_credentials(db, "admin3", "another fresh passphrase!") is not None
        print("update_credentials(both) ok")

        # --- cleanup so next run is reproducible ---
        db.delete(user)
        db.commit()
        assert count_users(db) == 0

    print("ALL AUTH SMOKE TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
