---
id: TKT-0023
title: Single-user auth model (User table + argon2 + register-once lock)
status: open
priority: P1
area: backend
created: 2026-05-18T18:41:55Z
updated: 2026-05-18T18:41:55Z
created_by: ticketing_agent
related_plan_item: B-09, A1, A2, A8
filed_via: human_manual_input
---

## Summary
Backend foundation for v1.1 auth. Adds the singleton `User` SQLModel, argon2 password hashing, and the register-once-lock helper that the auth endpoints will call.

## Expected
- `uv add argon2-cffi`.
- `app/models.py` adds:
  ```python
  class User(SQLModel, table=True):
      id: int | None = Field(default=1, primary_key=True)  # singleton: only id=1
      username: str = Field(unique=True, index=True, min_length=1, max_length=80)
      password_hash: str  # argon2 ($argon2id$...)
      refresh_secret: str  # bytes -> base64; rotated on logout
      created_at: datetime = Field(default_factory=_now)
      last_login_at: datetime | None = None
  ```
- `app/auth_crypto.py` (or extend `session_crypto.py`):
  - `hash_password(plain: str) -> str` -- argon2id, default time_cost/memory/parallelism.
  - `verify_password(plain: str, hashed: str) -> bool`.
  - `generate_refresh_secret() -> str` -- 32 random bytes -> base64.
- `app/auth_repo.py` thin DAO with:
  - `count_users(session) -> int`
  - `create_admin(session, username, password) -> User`
  - `get_user(session, username) -> User | None`
  - `rotate_refresh_secret(session, user) -> None`
  - `touch_last_login(session, user) -> None`
- Unit/smoke script `backend/scripts/smoke_auth.py` round-trips: hash + verify (good and bad), create_admin once, second create raises, count_users == 1.

Does NOT yet wire any endpoint -- that lands in TKT-0024.

## Resolution history
- 2026-05-18T18:41:55Z -- filed by Ticketing Agent (iter47, human input).
