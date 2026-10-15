# 053 Provider ingestion adapters
Epic: E5 | Depends: 051, 020 | Blockers: mapping tables need fixtures
Use: /opsx-propose @openspec/prompts/053-provider-ingestion-adapters.md
Capabilities: flow-alert-ingest
Sources: SPEC V1 ingestion; ARCH V1
Requirements:
1. Authorized sources only; output canonical raw events to 020.
2. Idempotent; schema drift detected and reported.
3. raw_color mapping via fixtures.
Seed scenarios: unknown field; duplicate; source revoked
Open questions (do not invent): provider schemas; mapping tables
Out of scope: capture mechanics
