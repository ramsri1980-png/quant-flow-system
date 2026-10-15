# 010 Migration runner
Epic: E1 | Depends: 005 | Blockers: C9, C10, C8
Use: /opsx-propose @openspec/prompts/010-migration-runner.md
Capabilities: migration-manifest, pending-calculation, baseline-coverage, reserved-ids
Sources: ARCH V2 §C.3; SPEC V2 §19 (DDL), §19.8.3; constitution §9.
Requirements:
1. Forward-only; SHA-256 manifest; applied migration never edited (hash mismatch → hard fail).
2. pending = enabled − baseline_covered − applied; never MAX(id).
3. Baseline: SQLite 001–069, DuckDB 001–041, generated only from the historical chain, never from patched final DDL.
4. Reserved IDs (SQLite 072–079, DuckDB 046–049) never auto-applied; AE/AF/AG = DuckDB 043–045 only when adoption flag set.
5. Proposed core repairs SQLite 071 / DuckDB 050 and 070/071, 042 tables apply as pending, not baseline.
6. Schema parity hash test ARCH V2 vs SPEC V2 (SPEC wins).
Seed scenarios: fresh install; upgrade from baseline; applied-file edited; gap in IDs; reserved ID present on disk; crash mid-migration restart.
Open questions: C10 historical migrations 001–064/001–037 may not exist — how to bootstrap baseline? C9 rearmed_at/cooldown_until type; adoption flag name.
Out of scope: repositories, data backfill.
