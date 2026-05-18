"""Auth gate for every /api/* request (TKT-0025, REQUIREMENTS A4).

Order in main.py: registered AFTER CORS so this middleware is the
OUTERMOST layer -- it runs first on the request path. slowapi rate
limits are route decorators (not middleware), so they run INSIDE this
gate, which means 429 responses can never leak whether a token was
valid.

Bypass matrix (in order):
1. Non-`/api/*` paths (Next.js static, the public hero) -- not our
   concern.
2. `settings.app_secret` empty -- dev / unconfigured mode preserves
   the pre-auth behavior so legacy local setups keep working.
3. `OPTIONS` method -- CORS preflight; CORSMiddleware handles it.
4. Allowlist: `/api/health`, `/api/auth/register`,
   `/api/auth/login`, `/api/auth/refresh` -- needed before a session
   exists.

Anything else under `/api/*` must present a valid `watify_session`
cookie. Failures return 401 with the TKT-0001 flat envelope.
"""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.jwt_tokens import AuthConfigError, TokenInvalid, decode_access
from app.settings import settings

log = logging.getLogger(__name__)

_ALLOWLIST = frozenset({
    "/api/health",
    "/api/auth/register",
    "/api/auth/login",
    "/api/auth/refresh",
})


def _unauthorized(detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"error": "auth_required", "detail": detail},
    )


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 1. Bypass non-API paths entirely. Frontend static and the
        # public hero are not our concern.
        if not path.startswith("/api"):
            return await call_next(request)

        # 2. Dev / unconfigured mode -- preserve the pre-auth behavior
        # so local dev keeps working without any registration.
        if not settings.app_secret:
            return await call_next(request)

        # 3. CORS preflight.
        if request.method == "OPTIONS":
            return await call_next(request)

        # 4. Allowlist paths that can be hit pre-auth.
        if path in _ALLOWLIST:
            return await call_next(request)

        # Everything else -- require a valid session cookie.
        token = request.cookies.get("watify_session")
        if not token:
            return _unauthorized("missing watify_session cookie")
        try:
            decode_access(token)
        except AuthConfigError:
            # Defensive: app_secret was set when we checked above but
            # somehow lost between checks. Should never happen; let
            # the request through rather than 500.
            log.warning("AuthMiddleware: AuthConfigError despite settings.app_secret check")
            return await call_next(request)
        except TokenInvalid as e:
            log.info("AuthMiddleware: rejected token at %s (%s)", path, e)
            return _unauthorized("session token invalid or expired")

        return await call_next(request)
