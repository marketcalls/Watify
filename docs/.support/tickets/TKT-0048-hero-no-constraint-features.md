---
id: TKT-0048
title: Hero must not advertise constraints as features (20 cap, 3-30s delay)
status: verified
priority: P2
area: frontend
related_tickets: TKT-0044
created: 2026-05-19T03:05:00Z
updated: 2026-05-19T03:05:00Z
created_by: resolving_agent
filed_via: user_direct_request
---

## Summary
Operator: "never say this as feature: 20 contacts per group, 3-30s random per-recipient delay, Friend groups, capped at 20." These are internal constraints, not selling points.

## Fix
In `frontend/src/app/page.tsx`:
- Removed the 3-stat row (Stat component still exported but unused -- can be tree-shaken).
- Subhead paragraph: removed "capped at 20" and "random per-recipient delay" copy; replaced with neutral "Pair once with WhatsApp, organize contacts into watchlists, and send messages now or on a schedule."
- FeatureCard #2 renamed "Friend groups, capped at 20" -> "Organize contacts into watchlists" with body about manual + CSV bulk add and dedup.
- FeatureCard #3 body trimmed "One message at a time" to keep it product-focused.
- Built-with strip (formerly "Integrates with") kept; rephrased to "Built with" since these aren't external integrations but Watify's own stack.

## Resolution history
- 2026-05-19T03:05:00Z -- filed and resolved + verified inline as a P2 hotfix per operator directive.
