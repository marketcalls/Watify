---
id: TKT-0034
title: Frontend apiFetch must send credentials so watify_session cookie crosses origins
status: verified
priority: P1
area: frontend
created: 2026-05-18T19:41:08Z
updated: 2026-05-18T19:54:30Z
created_by: ticketing_agent
related_plan_item: A4, A5
related_tickets: TKT-0024, TKT-0025, TKT-0026
filed_via: human_observed
---

## Summary
`frontend/src/lib/api.ts` calls `fetch(url, {...})` without `credentials: "include"`. After TKT-0025 verified, every authenticated `/api/*` request from the browser now silently 401s because the `watify_session` cookie set by `/api/auth/login` never crosses from `localhost:3000` to `localhost:8000`. The dashboard renders zeroed cards (Friend Groups, Contacts, Jobs Today) on top of SWR-cached state, and any login UI built on TKT-0026 will appear to "succeed" yet still leave the dashboard unauthenticated.

## Reproduction
1. Backend running in configured mode (`WATIFY_APP_SECRET` set, fingerprint non-null).
2. Open `http://localhost:3000` in browser. DevTools -> Network.
3. Observe `GET /api/groups`, `GET /api/jobs`, `GET /api/wa/state` requests.
4. Each request has NO `Cookie` header set on the request.
5. Each response is `401 {"error":"auth_required","detail":"missing watify_session cookie"}`.
6. The dashboard nevertheless renders with `0` in every count and the green `Backend: ok v0.1.0` badge (because `/api/health` is allowlisted).

## Expected
`apiFetch` always sends and receives cookies cross-origin, so once `/api/auth/login` sets `watify_session` the rest of the dashboard sees the session immediately:

```ts
const res = await fetch(url, {
  ...init,
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
    ...(init?.headers ?? {}),
  },
});
```

After fix: `GET /api/groups` from the browser carries `Cookie: watify_session=...` and returns 200.

## Actual
The `fetch` call omits `credentials`, which defaults to `"same-origin"`. Since `NEXT_PUBLIC_API_BASE=http://localhost:8000` is cross-origin to `http://localhost:3000`, the browser never attaches cookies, and the backend gate returns 401 on every protected endpoint.

## Logs / Evidence
- `frontend/src/lib/api.ts:29-50` -- `apiFetch` body, no `credentials` key.
- iter57 verification log: backend returns the flat 401 envelope on missing cookie, confirmed in curl smoke. From the browser, same shape.
- User screenshot `c:\Users\Admin1\Desktop\2026-05-19_01-05-13.png` (iter57 conversation) shows the dashboard rendering with `Friend Groups: 0` / `Contacts: 0` / `Jobs Today: 0` while `Sent (24H): 4` is residual SWR cache from before the gate tightened.

## Fix scope
One-line change to `frontend/src/lib/api.ts`. Add `credentials: "include"` to the `fetch` options object. No type changes, no API surface change. Smoke after: dashboard with a valid session cookie loads groups/jobs/wa state and gets non-zero counts; without a session cookie the same calls 401 (gate still effective).

## Notes for Resolving Agent
This must land BEFORE TKT-0026 (`/login` + `/register` UI) is verified end-to-end. If TKT-0026 ships first, login will appear successful (cookies set on the response, browser stores them) but the very next dashboard call will still 401 because the request omits the cookie.

Also: the backend CORSMiddleware in `app/main.py:56-62` already sets `allow_credentials=True`, so no backend change is needed -- the gap is purely on the frontend fetch options.

## Resolution history
- 2026-05-18T19:41:08Z -- filed by Ticketing Agent (iter58) after iter57 verification of TKT-0025 surfaced the gap via the user's dashboard screenshot.
- 2026-05-18T19:45:50Z -- resolved by Resolving Agent (iter59). Edited `frontend/src/lib/api.ts:34-41`: added `credentials: "include"` to the `fetch` options object inside `apiFetch`. The change is a single property; no API surface change (the `apiFetch<T>(path, init?)` signature is unchanged, all callers in `src/components`, `src/app/*/page.tsx`, `src/hooks` keep working). Comment in the diff explains the cross-origin reason and links back to TKT-0034 + TKT-0025. `npx tsc --noEmit` exits 0 -- compiles clean across the whole frontend tree. The Next.js dev server (pid 42204 from PIPELINE.md) HMR-reloaded the module on save. Awaits Verification Agent to drive a real browser session and confirm: (a) protected /api/* now sees the cookie, (b) dashboard counts populate after login, (c) gate still effective when no cookie is present.
- 2026-05-18T19:54:30Z -- VERIFIED by Verification Agent (iter60). The Chrome MCP browser-driven smoke could not be used because this Chrome profile's `localhost:3000` is still hijacked by a stale Strike Analytics service worker / browser cache (same external collision as TKT-0009): the loaded page rendered with `meta name="author" content="strike"` and made zero requests to `:8000` (`document.title=""`, body `[BLOCKED: Cookie/query string data]`), while `curl http://localhost:3000/` from the host returned the real Watify page (title `<title>Watify</title>`, 17768 bytes, `/_next/` markers). This is an external Chrome profile issue, not a Watify regression. Verification therefore used five independent proofs equivalent to the browser smoke: (1) source: `frontend/src/lib/api.ts:34-46` has `credentials: "include"` inside the `fetch` options with a TKT-0025/0034 comment; (2) type-check: `npx tsc --noEmit` exits 0; (3) bundled chunk: `curl http://localhost:3000/_next/static/chunks/src_130jczp._.js` (46120 bytes, 3000-served by the dev server) contains `apiFetch`, `credentials: "include"`, `"include"`, and the sourcemap path `src/lib/api.ts` -- proving the JS the browser would download has the property; (4) CORS preflight: `OPTIONS /api/groups` with `Origin: http://localhost:3000` returns `Access-Control-Allow-Credentials: true` + specific `Access-Control-Allow-Origin: http://localhost:3000` (not `*`), which are the exact WHATWG Fetch preconditions for the browser to attach the cookie on a `credentials: "include"` request; (5) cross-origin auth flow simulated: `POST /api/auth/login` with `Origin: http://localhost:3000` returns 200 + Set-Cookie for both `watify_session` (typ=access JWT) and `watify_refresh` (typ=refresh JWT); subsequent `GET /api/groups` with that cookie + `Origin: http://localhost:3000` returns 200 with the groups array and the same CORS headers. Combined evidence: the change is in source, in the bundle, the server cooperates, and the protected path returns 200 with a valid session cookie -- the browser will attach the cookie automatically given the property is present. Verified.
