# 050 Source authorization and provider state
Epic: E5 | Depends: 011 | Blockers: C11
Use: /opsx-propose @openspec/prompts/050-source-authorization-provider-state.md
Capabilities: source-authorization, provider-state-machine
Sources: ARCH V3 §F.0, §F.N; SPEC V1 §4.1
Requirements:
1. Automation only if source_authorization APPROVED, unexpired, automation_allowed=1, specific ToS provision recorded.
2. Ambiguity → fail closed.
3. Provider state machine (F.N) with explicit transitions; persisted.
4. Persistent challenge/403 → suspend, route to authorization review (F.0.8).
Seed scenarios: expired authorization; missing provision; 403 loop; restart in suspended state
Open questions (do not invent): C11 ADR-001 scope
Out of scope: any bypass technique
