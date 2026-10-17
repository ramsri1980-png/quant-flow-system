# Proposal

## Why

QuantFlow persists decision-critical state in SQLite `quant_state.db` and
analytical state in DuckDB `quant_flow.duckdb`, and its schema evolves through
forward-only, checksum-recorded migrations (constitution §9; SPEC V1 §19.6
invariant K). No migration engine exists yet: there is no manifest of authorized
migration files, no validated ledger, and no non-mutating way to prove that an
on-disk database matches the code. Without it, E1 Storage & Durability (and every
later feature) has no safe way to bring a fresh or existing store to a known
schema, and no fail-closed guard against editing an applied migration or
silently adopting a legacy database.

## What Changes

- Introduce a **forward-only, checksum-verified migration runner** for both
  stores, with a single `migrations/MANIFEST.json` describing each migration
  (`{id, store, path, sha256, applies_after, component, enabled}` plus a
  validated per-store `baseline_covered` metadata section).
- Add the SPEC-defined authoritative ledger (`schema_version_sqlite` /
  `schema_version_duckdb`, SPEC V2 §19) as the only record of applied
  migrations, bootstrapped before any migration and never altered.
- Add a manifest validator: required keys/types, path safety, SHA-256, ID
  uniqueness, reserved-slot (NEVER) and ADOPT-ONLY policy, unmanifested-file
  detection, dependency existence and acyclicity, and stable topological order
  (numeric tie-break, baseline first); never `MAX(migration_id)`.
- Add a `quantflow migrate apply|status|verify [--store sqlite|duckdb|both]`
  Typer command. `apply` is atomic per store, uses explicit transactions (never
  `executescript`), records `OK`/`FAILED` (no `IN_PROGRESS`), and blocks on a
  prior `FAILED` row; `status` and `verify` are strictly read-only with fixed
  exit codes.
- Consume the existing epoch-clock port for all ledger timestamps; obtain the
  application version solely from `importlib.metadata.version("quantflow")`.
- 010a uses **synthetic fixture migrations only** and does not author any real
  baseline SQL; real baselines and legacy adoption are 010b's scope.

## Capabilities

### New Capabilities

- `migration-runner`: A forward-only, checksum-verified schema migration
  capability for SQLite and DuckDB. It owns the authorized-migration manifest and
  its validation, the authoritative applied-migration ledger and its bootstrap,
  fresh vs already-baselined vs legacy store classification, per-migration atomic
  apply with explicit `OK`/`FAILED` outcomes and dependency closure, and a
  read-only `status`/`verify` contract with defined exit codes.

### Modified Capabilities

- None. The `epoch-clock` capability is consumed unchanged (no requirement in it
  changes); no other existing capability's requirements change.

## Impact

- New code: `src/quantflow/migrations/` (`manifest.py`, `runner.py`);
  `src/quantflow/cli/` gains a `migrate` Typer command; new data artifact
  `migrations/{sqlite,duckdb}/` and `migrations/MANIFEST.json`.
- Reused: `quantflow.ports.clock` (`Clock.now_ms`), `quantflow.adapters.clock`
  (`SystemClock`), `quantflow.domain.time` (`EpochMs`, `epoch_ms`).
- Databases: no change to `/data` in dev/tests (temporary paths only). Reads
  and (on `apply`) writes `schema_version_sqlite` / `schema_version_duckdb`.
- Tests: new `tests/migration/` suite using synthetic migrations and `tmp_path`.
- Docs: no `docs/reference/CURRENT` edits; any brief-vs-doc disagreement is
  logged in `openspec/conflicts-and-gaps.md`.
- Out of scope (brief): real 010b baselines and legacy adoption; DuckDB 051/052
  validity; cross-store dependency features; any change to anti-detection logic
  or ARCH V3 §F; any runtime DDL outside the runner; edits to source, archived
  005/005a–d, or `docs/reference/CURRENT`.

## Sources

- SPEC v2.0.5.1 Vol 2 §19.1–§19.2 (canonical DDL incl. the ledger tables);
  §19.8.3 (UTC epoch ms; SQLite INTEGER / DuckDB BIGINT; no DuckDB TIMESTAMP).
- ARCH v5.1.5.1 Vol 2 §C.1 (store pragmas, ledger DDL), §C.3 (migration order,
  baseline, runner contract, `pending = enabled − baseline_covered − applied`),
  §C.4 (schema-hash/parity test).
- ARCH v5.1.5.1 Vol 4 §AH.6.6 (schema and migration ownership; reserved IDs).
- SPEC v2.0.5.1 Vol 1 §19.6 invariant K (every applied migration recorded with
  checksum).
- SPEC v1 §19.8.3 / SPEC v2 §19.8.3 (epoch vs duration naming).
- `openspec/constitution.md` §§9, 11, 12; feature brief
  `openspec/prompts/010a-migration-runner-core.md`.
