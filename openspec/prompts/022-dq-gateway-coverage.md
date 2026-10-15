# 022 DQ gateway and coverage
Epic: E2 | Depends: 021 | Blockers: none known
Use: /opsx-propose @openspec/prompts/022-dq-gateway-coverage.md
Capabilities: dq-gate, coverage-tracking
Sources: SPEC V1 data-quality sections; SPEC V3 §8.4 (DQ gate position).
Requirements:
1. DQ gate precedes signal_valid; failure → explicit unavailable/WATCH, never silent default.
2. Coverage metrics recorded per source/underlying.
3. Stale/missing/malformed inputs each produce a distinct reason code.
Seed scenarios: stale quote; missing leg; coverage below threshold; recovery.
Open questions: thresholds by named constant only; heading-only SPEC V1 §6.2/6.5 check lists (do not invent).
Out of scope: scoring.
