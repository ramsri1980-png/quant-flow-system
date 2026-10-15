# 040 Thesis and AnalysisSnapshotBuilder
Epic: E4 | Depends: 035, 037 | Blockers: RQ-005
Use: /opsx-propose @openspec/prompts/040-thesis-snapshot-builder.md
Capabilities: thesis, analysis-snapshot
Sources: SPEC V1 §1.3; SPEC V3; ARCH V4
Requirements:
1. One thesis → one immutable analysis snapshot → one market map.
2. Builder is pure: no fetch_*, get_current_*, read_pointer_* (AST lint).
3. as_of-seeded; byte-identical rebuild.
4. Evidence references immutable observation IDs.
Seed scenarios: rebuild identical; forbidden call detected; late data excluded
Open questions (do not invent): BLOCKING RQ-005
Out of scope: workflows
