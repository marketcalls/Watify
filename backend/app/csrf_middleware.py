"""CSRF defense for state-changing /api/* endpoints (TKT-0032).

`SameSite=Lax` on `watify_session` already blocks the common
cross-site POST CSRF. This is defense-in-depth on top of that:
require either a custom request header that simple HTML forms
cannot set (`X-Requested-With: XMLHttpRequest`) OR a same-origin
`Origin` header matching `settings.cors_origin`. Both signals are
trivially produced by fetch() from our own frontend and absent on
forged requests.

Order in `main.py`: registered AFTER `AuthMiddleware` so this is
the OUTERMOST middleware (FastAPI applies middleware in reverse
order of `add_middleware`). The CSRF check fires before auth on
state-changing requests, so a forged unauthenticated POST receives
403 csrf_required rather than 401 auth_required -- both reject the
request, the 403 is just stricter about what failed.

Bypass matrix:
1. Non-`/api/*` paths.
2. Safe methods (`GET`, `HEAD`, `OPTIONS`).
3. Allowlist (`/api/auth/login`, `/api/auth/register`) -- these fire
   before any session exists; they cannot rely on `X-Requested-With`
   for first-load UX, and the frontend wraps both through `apiFetch`
   which sets the header anyway.

Anything else: require the header OR a matching Origin.
"""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.settings import settings

log = logging.getLogger(__name__)

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_ALLOWLIST = frozenset({"/api/auth/login", "/api/auth/register"})


def _forbidden(detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={"error": "csrf_required", "detail": detail},
    )


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if not path.startswith("/api"):
            return await call_next(request)
        if request.method in _SAFE_METHODS:
            return await call_next(request)
        if path in _ALLOWLIST:
            return await call_next(request)

        xrw = request.headers.get("x-requested-with")
        origin = request.headers.get("origin")

        if xrw == "XMLHttpRequest":
            return await call_next(request)
        if origin and origin == settings.cors_origin:
            return await call_next(request)

        log.info("CSRFMiddleware: rejected %s %s (xrw=%r origin=%r)", request.method, path, xrw, origin)
        return _forbidden("missing X-Requested-With or invalid Origin")
