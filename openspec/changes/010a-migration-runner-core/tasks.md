# Tasks

## 1. Preconditions & scaffolding

- [x] 1.1 Resolve **OQ-1 (BLOCKING) retry/audit** with the operator and record the decision in `design.md` Open Questions plus `openspec/conflicts-and-gaps.md`; verify the decision states whether `--retry-failed` is in scope and where the audited trail lives (ledger single row vs external audit).
- [x] 1.2 Resolve **OQ-2 (BLOCKING) manifest format** (`MANIFEST.json` per brief vs `MANIFEST.md` per ARCH V2 §C.3) with the operator; log the resolution in `openspec/conflicts-and-gaps.md`; verify on-disk that the chosen filename is unambiguous.
- [x] 1.3 Create `src/quantflow/migrations/` package with empty `manifest.py` and `runner.py`, and a `migrate` Typer subcommand under `src/quantflow/cli`; verify `uv run python -c "import quantflow.migrations"` succeeds and `uv run quantflow migrate --help` prints usage.
- [x] 1.4 Define the new error types in `quantflow.domain.errors` (manifest/ledger/validation failures); verify each new type is importable and caught by `QuantFlowError`.

## 2. Manifest validator

- [x] 2.1 Red tests (property + missing/stale/malformed + duplicate classes): required fields, scalar `applies_after` rejected, cross-store dependency rejected, path traversal rejected, duplicate IDs, unmanifested `.sql` files, slot policy (NEVER 072–079 / 046–049; ADOPT-ONLY 043–045/050/071), unused classification, cycle detection, and stable numeric-tie-break order with `000_baseline` first; verify the tests fail against the empty module.
- [x] 2.2 Implement manifest loading and schema validation (`{id, store, path, sha256, applies_after, component, enabled}`) including path safety and `NNN_<slug>.sql` form; verify 2.1 schema/path/duplicate tests pass.
- [x] 2.3 Implement slot-policy and unmanifested-file validation; verify the NEVER/ADOPT-ONLY/unmanifested tests pass.
- [x] 2.4 Implement store-local dependency existence, cycle detection, and stable topological order (no `MAX(migration_id)`); verify closure/cycle/ordering tests pass and ordering is identical across runs.
- [ ] 2.5 Implement per-store `baseline_covered` metadata parsing/validation (informational only); verify a malformed coverage section fails closed.
- [ ] 2.6 Add on-disk SHA-256 verification against the manifest and forward-only/immutability assertions; verify the checksum-mismatch test fails closed.

## 3. Ledger, classification, and baseline identity

- [ ] 3.1 Red tests (missing/stale/malformed + duplicate/idempotency/restart + port-contract classes): ledger bootstrap before first migration, exact SPEC V2 §19.2 columns, bootstrap-failure hard error, fresh vs already-baselined vs legacy, empty-ledger eligibility with the ledger excluded from the emptiness check, `result` only `OK`/`FAILED`, and `applied_at` from an injected Clock; verify they fail first.
- [ ] 3.2 Implement the SPEC-defined ledger bootstrap in its own committed transaction (exact DDL, no invented columns); verify bootstrap tests pass and no migration payload contains ledger creation.
- [ ] 3.3 Implement store classification (fresh / already-baselined / legacy abort) using independent schema inspection; verify fresh/legacy/empty-ledger tests pass and a legacy store is never overwritten.
- [ ] 3.4 Implement `000_baseline` ledger identity: `migration_id='000_baseline'`, lowercase SHA-256 of exact file bytes, `app_version` from `importlib.metadata.version("quantflow")`, Clock-port `applied_at`, `result='OK'` only on success; verify no sentinel is ever written and a missing package version fails with a packaging error.
- [ ] 3.5 Implement baseline dependency closure (`applies_after:["000_baseline"]` requires the OK baseline row; `baseline_covered` is never an OK row); verify closure tests pass.

## 4. Atomic runner

- [ ] 4.1 Red tests (migration fresh+upgrade + replay + no-future-leakage + temp-paths-only classes): fault-injected mid-migration failure leaves no partial DDL and exactly one `FAILED` row; `FAILED` blocks apply; explicit BEGIN/COMMIT (no `executescript`); semicolon-in-trigger handling; per-store dual-run partial failure; idempotent re-apply of a closed manifest; restart mid-suite; all DBs under `tmp_path`; verify these fail first.
- [ ] 4.2 Implement the SQLite runner with `isolation_level=None`, explicit transactions, and a reviewed statement-splitting strategy (no naive `;`); verify rollback and trigger tests pass.
- [ ] 4.3 Implement the DuckDB runner with explicit per-migration transactions; verify DuckDB rollback/rollback-fault tests pass.
- [ ] 4.4 Implement failure handling: rollback DDL + OK insert, then upsert one `FAILED` row in a new transaction, then abort; verify exactly-one-FAILED and default-abort tests pass.
- [ ] 4.5 Implement connection policy (embedded reuse vs standalone PRAGMAs `WAL`/`NORMAL`/`foreign_keys=ON`/`busy_timeout=5000` verified before `BEGIN`, no competing writer; DuckDB `temp_directory` set first without a `/data` test path); verify PRAGMA-mode tests pass and refuse-on-incompatible-state is covered.
- [ ] 4.6 Add an AST/scan guard test rejecting `executescript` and any runtime DDL outside the runner; verify the guard fails on a planted violation.

## 5. CLI apply/status/verify

- [ ] 5.1 Red tests (golden + duplicate/idempotency/restart classes): `migrate apply|status|verify [--store sqlite|duckdb|both]`, read-only `verify`/`status` (no ledger write, no mutating PRAGMA, no DB creation), explicit missing-store reporting, `PENDING` not treated as corruption, DB-newer drift, and exit codes 0/1/2; verify they fail first.
- [ ] 5.2 Implement the `migrate` CLI (`apply`, `status`, `verify`, store selection) wiring the runner and clock adapter; verify apply/status golden tests pass.
- [ ] 5.3 Implement the `verify` check set and exit-code mapping (manifest/deps/acyclicity/unmanifested/slot/SHA-256/ledger agreement/baseline identity/closure/no-FAILED/no-DB-newer); verify exit-code tests pass and `verify` mutates nothing.
- [ ] 5.4 If OQ-1 selects `--retry-failed`, implement it with the agreed audit semantics; otherwise document why retry is deferred; verify the chosen behavior with a test.
- [ ] 5.5 Implement `status` reporting pending count and each store's last successful migration; verify the status test passes.

## 6. Equivalence & integration timing

- [ ] 6.1 Add the closed-manifest-subset fresh-vs-upgrade schema-equivalence test using canonical `sqlite_master` and DuckDB table/column introspection (not byte-identical files); verify it passes.
- [ ] 6.2 Wire the `tests/migration/` integration suite and verify it completes in < 10 s; verify no test path resolves under `/data`.

## 7. Final verification

- [ ] 7.1 Run `uv run pytest -q`, `uv run ruff check src tests`, `uv run ruff format --check src tests`, and `uv run mypy --strict src/quantflow`; verify all pass.
- [ ] 7.2 Verify coverage ≥ 95% for `migrations/**` (and `domain/**` unchanged) and run `python3 scripts/check_constants.py`; verify both succeed.
- [ ] 7.3 Verify the anti-detection SHA gate: `docs/reference/CURRENT/ARCH_v5.1.5.1_Vol3_Capture_AntiDetection.md` SHA-256 equals `2d7a90e533196af61745bc4efd3259b7b64b519b8ec78662392b50a911285e23`; abort on mismatch.
- [ ] 7.4 Verify `git status --short` is clean with no `.bak` files and that no file under `/data`, `docs/reference/CURRENT`, or archived 005/005a–d was modified; update `openspec/conflicts-and-gaps.md` for any resolved item.

## Workflow follow-up

- Tag `feature-010a-complete` only after merge and all checks above pass.
- Archive the change after the project's review requirements are satisfied; verify the archived result.
