# 041 Ledger and outcomes (T+1)
Epic: E4 | Depends: 011, 012 | Blockers: C5
Use: /opsx-propose @openspec/prompts/041-ledger-outcomes-t1.md
Capabilities: signal-ledger, outcomes
Sources: SPEC V2 §19.3; SPEC V3 §17.5 (conflicts)
Requirements:
1. Outcome uniqueness via PK including outcome_scope_id (DDL wins over §17.5 partial indexes).
2. Outcomes append-only; no future leakage.
3. Idempotent recompute.
Seed scenarios: duplicate outcome; scope variation; restart
Open questions (do not invent): C5 resolution recorded; T+1 definition details
Out of scope: ML labels
