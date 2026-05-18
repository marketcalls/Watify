# Iteration 67 -- Ticketing Agent

- **Started**: 2026-05-18T20:26:01Z
- **Phase**: ticketing
- **Active agent**: ticketing_agent

## Plan
Re-triage after TKT-0030 verified. The v1.1 P1 milestone (TKT-0024 endpoints, TKT-0025 middleware, TKT-0026 login/register UI, TKT-0030 install scripts, TKT-0031 per-install identity, TKT-0034 credentials include) is fully shipped. Remaining queue is P2/P3 polish.

1. Security spot pass focused on the install.sh / update.sh diff: any inline secrets, third-party `curl | bash` lines, missing chmod on sensitive files, missing systemd hardening, Nginx vhost gaps.
2. Re-confirm ticket counts.
3. Queue TKT-0027 (public hero + `/dashboard` move) -- the user's iter57 screenshot issue is the most user-visible open item.

## Actions

1. **Install-script security spot pass**:
   - Inline hex secrets (`[a-f0-9]{32,}`) in `install/install.sh` + `install/update.sh` -- empty. Secrets are generated at runtime via `openssl rand -hex 32` and the tmp-venv `Fernet.generate_key()`, never baked into the script.
   - Third-party `curl | bash` lines: TWO occurrences at install.sh:127 (`deb.nodesource.com/setup_20.x`) and install.sh:134 (`astral.sh/uv/install.sh`). Both are first-party setup scripts from the upstream maintainers (NodeSource + Astral). Acceptable per the spec; the alternative would be vendoring binaries, which is worse for security drift. Documented decision -- no ticket needed.
   - `chmod 600`: lines 262-264 cover backend/.env, app.db, and whatsapp.db.
   - Systemd hardening: 5 directives per unit (NoNewPrivileges, PrivateTmp, ProtectSystem=strict, ProtectHome=true, ReadWritePaths) -- both watify.service and watify-frontend.service.
   - Nginx denies dotfiles + leakage paths at lines 413-414: `\.(env|git|htaccess)` + `\.(ini|log|sh|sql|conf)$`.
   - Security headers at lines 402-405 (X-Frame-Options SAMEORIGIN, X-Content-Type-Options nosniff, X-XSS-Protection 1; mode=block, Referrer-Policy strict-origin-when-cross-origin) + HSTS via ssl-security.conf line 492.
   - Result: install-script surface area clean. No new tickets.
2. **Ticket recount**: open=12, inprogress=0, resolved=0, verified=22. Matches PIPELINE.md.
3. **TKT-0027 queued** with explicit deliverables in PIPELINE Next Action: rename current `app/page.tsx` -> `app/dashboard/page.tsx`, write new `app/page.tsx` hero with two CTAs + feature triplet + footer wars note, redirect login/register `router.push("/")` -> `router.push("/dashboard")`. Out of scope this iteration: TopNav nav links (TKT-0028), route guards (TKT-0029).
4. Updated PIPELINE.md: iteration=67, phase=resolving, agent=resolving_agent.

## Outcome
Security spot pass clean over the iter65/66 install-script diff. No new tickets filed. Next iteration: Resolving Agent picks TKT-0027.

