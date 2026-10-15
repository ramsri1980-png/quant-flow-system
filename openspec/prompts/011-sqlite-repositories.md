# 011 SQLite repositories
Epic: E1 | Depends: 010 | Blockers: C8
Use: /opsx-propose @openspec/prompts/011-sqlite-repositories.md
Capabilities: sqlite-ports, sqlite-adapters, single-writer
Sources: SPEC V2 §19 (SQLite DDL); ARCH V2 (storage); constitution §6, §9.
Requirements:
1. Repository ports in domain; SQLite adapters only in infrastructure.
2. Only quantd opens SQLite for write; others read-only connections.
3. Decision-critical state (SQLite first) survives DuckDB outage.
4. Append-only tables (analysis_snapshots, market_map_snapshots, dealer_level_maps, position_exit_events) reject UPDATE/DELETE; corrections use supersedes_id.
5. Idempotent upserts keyed per DDL; transactions atomic per unit of work.
Seed scenarios: duplicate insert; restart mid-transaction; update on append-only table rejected; read-only connection write rejected; temp path only.
Open questions: exact table list for this slice (derive from DDL, do not invent); WAL/pragma settings if unspecified.
Out of scope: DuckDB, queue, migrations.
