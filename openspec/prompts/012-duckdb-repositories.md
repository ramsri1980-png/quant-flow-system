# 012 DuckDB repositories
Epic: E1 | Depends: 010 | Blockers: C8, C9
Use: /opsx-propose @openspec/prompts/012-duckdb-repositories.md
Capabilities: duckdb-ports, duckdb-adapters, analytical-writes
Sources: SPEC V2 §19 (DuckDB DDL), §19.8.3 Rule 1; ARCH V2; constitution §4, §6.
Requirements:
1. DuckDB writes only via quantd db_pool_executor.
2. Epoch columns BIGINT; no TIMESTAMP; dates as DATE.
3. No partial indexes (unsupported); uniqueness via PK incl. outcome_scope_id.
4. Analytical outage must not block SQLite decision path; writes queue/outbox (see 013).
5. Evidence columns reference immutable observation IDs, never package_quote_current.package_quote_id.
Seed scenarios: DuckDB unavailable; type mismatch on epoch col; duplicate key; restart replay.
Open questions: C9 baseline column types; C8 INTEGER vs BIGINT for _cents/_mills.
Out of scope: SQLite repos, kernels.
