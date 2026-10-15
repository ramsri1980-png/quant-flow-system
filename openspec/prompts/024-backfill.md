# 024 Backfill (thin spec)
Epic: E2 | Depends: 020–022 | Blockers: sparse source text
Use: /opsx-propose @openspec/prompts/024-backfill.md
Capabilities: backfill-job
Sources: runbook E2 task 024; SPEC V1 ingestion. Locate any further sections; do not invent.
Requirements:
1. Backfill uses the same ingestion path and authorization gate as live; no bypass.
2. Idempotent, resumable, rate-budgeted (014).
3. No future leakage: backfilled data stamped with true observation time.
Seed scenarios: rerun; interrupted run; overlap with live data.
Open questions: BLOCKING scope and sources — docs thin; ask operator before design.
Out of scope: ML training sets.
