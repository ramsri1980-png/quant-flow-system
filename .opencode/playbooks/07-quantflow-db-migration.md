# Playbook: QuantFlow DB migrations (load for any schema/migration/repository work)
- Forward-only. Never edit an applied migration (SHA-256 manifest mismatch = hard fail). Fix = new migration.
- pending = enabled − baseline_covered − applied. Never MAX(id). Baseline: SQLite 001–069, DuckDB 001–041, from the historical chain only, never from the patched final DDL.
- Reserved IDs never auto-applied: SQLite 072–079, DuckDB 046–049. AE/AF/AG = DuckDB 043–045 only when adopted. SQLite 071 / DuckDB 050 are proposed repairs → pending.
- Epoch ms: SQLite INTEGER, DuckDB BIGINT; no DuckDB TIMESTAMP. Dates: SQLite TEXT ISO, DuckDB DATE. Duration cols (*_latency_ms etc.) bounded INTEGER.
- Units: _cents/_micros/_mills BIGINT in decision path; DOUBLE analysis-only. (Open conflict C8/C9: check conflicts-and-gaps.md.)
- SQLite: WAL, single writer (quantd only), explicit transactions, `PRAGMA foreign_keys=ON`. DuckDB: no partial indexes; writes only via db_pool_executor.
- Append-only tables (analysis_snapshots, market_map_snapshots, dealer_level_maps, zero_dte_cluster_snapshots, position_exit_events): no UPDATE/DELETE; corrections via supersedes_id.
- Canonical DDL = SPEC V2 §19 (SPEC wins over ARCH V2). Add a parity hash test.
- Tests on temp paths only: fresh install, upgrade-from-baseline, edited-applied-file fails, crash mid-migration restart.
