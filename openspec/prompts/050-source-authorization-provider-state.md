# 050 Source authorization and provider state

Epic: E5 | Depends: 011 | Blockers: C11 (source-scope only)
Use: /qf-propose @openspec/prompts/050-source-authorization-provider-state.md
Capabilities: source-authorization, provider-state-machine
Sources: ARCH V3 §F.0, §F.N; SPEC V1 §4.1

Requirements:
1. Automation allowed only if `source_authorization` record has status=APPROVED, unexpired review, automation_allowed=1, and the specific ToS permitting provision recorded in `authorization_reference`. Absence of any of these fails closed.
2. Ambiguity in authorization → fail closed, do not proceed.
3. Provider state machine per ARCH V3 §F.N: HEALTHY, DEGRADED, CHALLENGED, MANUAL_REQUIRED, BLOCKED, COOLDOWN, AUTH_REQUIRED, SCHEMA_CHANGED, DISABLED. All transitions persisted with reason.
4. Persistent challenge or persistent 403 on an automation_allowed=1 source → suspend automated access, route to authorization review per §F.0.8. Never solve-and-continue.
5. ADR-001 resolves WHICH sources are authorized for automation. It does not reduce §E or §F requirements for sources that ARE authorized.

Seed scenarios: expired authorization; missing ToS provision; 403 loop; restart in suspended state; challenge → CHALLENGED; three-session escalation to MANUAL_REQUIRED; 429 → COOLDOWN until next day.

Open questions (do not invent): C11 ADR-001 source-scope decision.

Out of scope: any bypass technique, unauthorized source automation.
