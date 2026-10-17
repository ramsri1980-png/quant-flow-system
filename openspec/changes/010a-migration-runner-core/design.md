# Design

## Context

See proposal.md — Why. Constraints that shape the approach:

- Authoritative ledger DDL is SPEC V2 §19 (mirrored ARCH V2 §C.1):
  `schema_version_sqlite(migration_id TEXT PRIMARY KEY, checksum TEXT NOT NULL,
  applied_at INTEGER NOT NULL, app_version TEXT NOT NULL, result TEXT NOT NULL
  CHECK(result IN ('OK','FAILED')))`, DuckDB identical with `applied_at BIGINT`.
  `migration_id` is a PRIMARY KEY, so per-migration state is one row and failure
  handling is an UPDATE/upsert, not another row for the same ID.
- Migration order/runner contract: ARCH V2 §C.3 (baseline through SQLite 069 /
  DuckDB 041; `pending = enabled − baseline_covered − applied`; stable topo order,
  numeric tie-break; never `MAX(migration_id)`). Ownership: ARCH V4 §AH.6.6.
- Gates: only `quantd` writes the DBs (constitution §6); forward-only, reserved
  IDs never auto-applied, baseline not generated from patched final DDL
  (constitution §9). Clock via the existing epoch-clock port (constitution §5).
- 010a is synthetic-fixture only; no real baseline SQL is authored here.

## Goals / Non-Goals

**Goals:**
- Manifest authoring + validation, ledger bootstrap, fresh/already-baselined/legacy
  classification, per-migration atomic apply with `OK`/`FAILED`, dependency
  closure, and read-only `status`/`verify` with fixed exit codes.
- Provable rollback (no partial DDL) and no `executescript`.

**Non-Goals:**
- Real baselines, legacy adoption reconciliation, and DB-level schema parity
  testing (010b).
- DuckDB 051/052 validity; cross-store dependency features; AE/AF/AG adoption.
- Any change to anti-detection logic or ARCH V3 §F.

## Decisions

### D1–D4 Layout / API
- Flat `migrations/{sqlite,duckdb}/NNN_<slug>.sql`; code
  `src/quantflow/migrations/{runner,manifest}.py`; one `migrations/MANIFEST.json`;
  Typer CLI added under the existing `src/quantflow/cli`. No down migrations.
- Manifest entry `{id, store, path, sha256, applies_after, component, enabled}`;
  a per-store `baseline_covered` metadata section is added and validated when 010b
  introduces real baselines.
- `applies_after` is ALWAYS an array of IDs (`[]` = root); dependencies are
  store-local. *Alternative:* scalar dependency — rejected (ambiguity, silent
  omission of parallel deps). *Alternative:* cross-store deps — rejected (no
  approved cross-store feature; would create unmodeled coupling).

### D5 Slot policy
- NEVER: SQLite 072–079, DuckDB 046–049 — a manifest entry there is an error.
  DuckDB 046 is reserved for a future phase, not prohibited forever; changing the
  policy needs a later reviewed change.
- ADOPT-ONLY (no auto-apply until operator-approved enablement): DuckDB 043–045
  and 050, SQLite 071.
- Every other entry must be explicitly classified (`component`, `enabled`);
  unmanifested `.sql` files are an error. 051/052 are 010b's concern.
- *Alternative:* tiered "core vs research" auto-enable like ARCH §C.3 prose —
  deferred to 010b/operator because ARCH (§C.3) calls 050 "PROPOSED CORE" while
  the brief lists it ADOPT-ONLY (see OQ-3).

### D6 State machine
- `schema_version_<store>` is the ledger name, confirmed by SPEC V2 §19.2.
- fresh = no application schema and no OK baseline row; already-baselined = an OK
  baseline row exists; legacy = application tables with no OK baseline row → abort
  pending an explicit 010b adoption plan (never overwrite/silently adopt).
- An existing empty ledger is baseline-eligible only if inspection confirms no
  pre-existing application table, excluding the ledger itself.
- *Alternative:* infer freshness from ledger emptiness alone — rejected (a legacy
  store with no ledger would be wrongly baselined).

### D7 Ledger bootstrap and atomicity
- Bootstrap the ledger in its own committed transaction before any migration; the
  baseline's transactional payload excludes ledger creation.
- On migration failure: roll back DDL + its OK insert; in a NEW transaction
  upsert a single `FAILED` row for that `migration_id`, then abort. Bootstrap
  failure is a hard error, never a `FAILED` migration row.
- *Alternative:* one transaction wrapping ledger + baseline — rejected (bootstrap
  must survive to record the baseline attempt outcome).

### D8 Application version
- Sole source: `importlib.metadata.version("quantflow")`. Unavailable → actionable
  packaging error; never `unknown`, never hard-coded `v2.0.5.1`, never a fallback.
- 010b baseline rows use the same source at adoption time; later rows use the
  version at their own application time.

### D9 Dual-store
- `--store both` runs SQLite then DuckDB, reports each result independently, offers
  no cross-store atomicity. DuckDB failure does not roll back a committed SQLite
  migration. Success is never claimed for a failed store.

### D10 Baseline ledger identity
- Reserve `000_baseline` (store-local), an ordinary manifest entry with `path` and
  SHA-256. Ledger row: `migration_id = '000_baseline'`, `checksum` = lowercase
  SHA-256 of the exact file bytes, `app_version` from D8, `result='OK'` only on a
  successful baseline commit, `applied_at` from the Clock port (`EpochMs`). No
  checksum sentinel. Confirmed against SPEC V2 §19.2 — fits (no extra column, no
  DDL change).

### D11 Baseline dependency closure
- `000_baseline` is a real successful ledger row, not virtual/ignored. A
  migration with `applies_after:["000_baseline"]` passes closure only when the
  same store's OK baseline row exists. `baseline_covered` is informational
  history only, never a fabricated OK row. Prefer direct dependency on the
  baseline for freshly introduced post-baseline migrations.

### D12 FAILED handling
- A `FAILED` row blocks `apply` by default; `status` reports it and `verify`
  fails. Recovery requires operator investigation and an explicit, audited retry
  workflow; retry only after proving no partial schema changes and a checksum
  match with the failed attempt; success leaves a single OK row for the
  `migration_id`. No automatic retry-once. *Open question OQ-1 (BLOCKING)* covers
  the audit representation, since the ledger PK cannot hold per-attempt history.

### D13 SQL execution
- Forbidden: `sqlite3.Connection.executescript()`. Use `isolation_level=None` with
  explicit `BEGIN`/`COMMIT` and a statement-splitting strategy that respects
  triggers/quoted text (never naive `;`). DuckDB uses explicit per-migration
  transactions. Reject statements that cannot run transactionally. Apply required
  connection settings outside transactions. Rollback proven by fault injection.

### D14 Connection policy
- Embedded (quantd) mode reuses the quantd-owned SQLite connection and its
  established PRAGMAs, checking required settings without mutating them inside a
  transaction. Standalone CLI opens a separate connection only when quantd is
  stopped and sets `journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=ON`,
  `busy_timeout=5000` (ARCH V2 §C.1) before `BEGIN`, verifies them, and refuses
  incompatible state. No competing writer. DuckDB `temp_directory` is set before
  the write connection, using the documented path policy; tests never invent a
  `/data` path. No repo-specific difference found.

### D15 Verify contract
- `migrate verify` is strictly read-only and checks manifest schema/fields,
  uniqueness and store-local dependency existence, acyclicity, unmanifested
  files, slot policy, on-disk SHA-256 vs manifest, OK-ledger↔manifest agreement
  and checksum identity, baseline identity/presence, dependency closure, no
  `FAILED` rows, and no unexpected DB-newer-than-code rows. Pending enabled
  migrations are `PENDING` (exit 0 if otherwise consistent). Exit 0 = consistent,
  1 = validation/drift/failure, 2 = CLI/usage/config error. `verify`/`status`
  never write a ledger, set mutating PRAGMAs, or create a DB; missing stores are
  reported explicitly. 010b's schema-parity test is separate and not replaced.

## Reuse

- `quantflow.ports.clock.Clock` (`now_ms() -> EpochMs`) — reused unchanged for all
  ledger timestamps (constitution §5/§9; brief "consume the existing epoch-clock
  port; do not modify it").
- `quantflow.adapters.clock.SystemClock` — reused as the concrete clock at the CLI
  edge.
- `quantflow.domain.time` (`EpochMs`, `epoch_ms`) — reused for `applied_at`.
- `quantflow.domain.errors` — extend the existing error hierarchy for
  manifest/ledger/validation failures rather than adding a parallel one.
- Existing `src/quantflow/cli` package — extend with the `migrate` Typer command.
- New module `src/quantflow/migrations/` is justified: no manifest, ledger, or
  migration-execution code exists (openspec/modules.md lists none); the runner is
  a distinct concern from the pure domain layer and is not kernel/domain code.

## Migrations touched

- **None authored or applied by 010a.** No SQLite or DuckDB migration ID is
  created, changed, or applied here; all tests use synthetic fixture migrations
  under `tmp_path`. Confirmed: no applied migration is edited.
- 010b owns real migrations: baseline `000_baseline` (SQLite through 069 / DuckDB
  through 041) and post-baseline IDs (SQLite 070/071; DuckDB 042/050/051/052),
  with `baseline_covered` reconciliation.

## Testing strategy (10 classes)

1. Golden: stable topological apply order for a closed synthetic manifest.
2. Boundary/units: ID parsing, slot boundaries (071/072, 045/046), path safety.
3. Missing/stale/malformed: malformed manifest, missing file, missing store.
4. Duplicate/idempotency/restart: duplicate IDs; re-running a closed manifest is a
   no-op; restart mid-suite.
5. Port contract: Clock injection; no wall-clock reads.
6. Migration fresh+upgrade: fresh baseline vs upgrade equivalence for a closed
   manifest subset (schema equivalence via canonical `sqlite_master` / DuckDB
   table-column introspection, not byte-identical files).
7. Replay: repeat-apply determinism.
8. Property: manifest validator invariants (acyclicity, uniqueness, closure).
9. No-future-leakage: no runtime DDL, no `executescript` (AST scan), DB-newer
   handling.
10. Temp-paths-only: all test DBs under `tmp_path`; nothing touches `/data`.

Additional required checks: checksum mismatch, FAILED rollback with exactly one
FAILED row, FAILED default abort, read-only `verify` + exit codes, PRAGMA modes,
dual-store partial failure, baseline dependency closure, fresh/empty-ledger/legacy
distinctions. Integration suite target < 10 s.

## Risks / Trade-offs

- [RETRY_AUDIT] The ledger PK cannot hold per-attempt history → OQ-1; until
  resolved, retry is a single-row state transition and audit lives outside the
  ledger. → Mitigation: operator decision before implementing retry.
- [MANIFEST_FORMAT] ARCH V2 §C.3 says `MANIFEST.md`; brief mandates
  `MANIFEST.json` → OQ-2. → Mitigation: implement per brief, log doc drift,
  confirm before apply.
- [STATEMENT_SPLIT] Correct SQL splitting without a parser is subtle (triggers,
  quoted `;`) → Mitigation: reviewed strategy + fault-injection rollback tests;
  reject non-transactional statements.
- [ALTER_IN_TXN] Some engines restrict DDL inside explicit transactions →
  Mitigation: per-store capability check; reject statements that cannot run
  transactionally.
- [COVERAGE] New `migrations/**` must reach ≥95% → Mitigation: tests-first per the
  10 classes above.

## Migration Plan

- Not applicable to `/data`: 010a ships code + manifest mechanism only and applies
  nothing to real stores. Deployment is code + CLI; rollback is reverting the
  code. Real store migration rollout belongs to 010b.

## Open Questions

- **OQ-1 — Retry/audit representation (BLOCKING).** D12 requires an explicit,
  audited retry workflow, but the SPEC ledger PK `migration_id` cannot store
  per-attempt history without a constraint change. Proposed SPEC-compatible
  resolution: keep one row per `migration_id` (retry = UPDATE FAILED→OK), record
  the audited attempt trail outside the ledger (structured log and/or the
  existing operator-control audit path), and gate retry behind an explicit
  `--retry-failed` that re-verifies no partial schema and checksum match. Needs
  operator confirmation; if a per-attempt ledger trail is required, block 010b and
  propose a contract amendment (do not change the SPEC DDL silently). Stated in
  the brief's stop conditions.
- **OQ-2 — Manifest file format (BLOCKING confirmation).** ARCH V2 §C.3 names
  `MANIFEST.md`; brief D1 mandates a single `migrations/MANIFEST.json`. Per
  constitution §12 the doc wins and the disagreement must be logged. Proposed: make
  `MANIFEST.json` canonical, log the drift in `openspec/conflicts-and-gaps.md`, and
  queue an ARCH V2 §C.3 wording amendment. Operator confirmation requested before
  apply.
- **OQ-3 — DuckDB 050 classification (NON-BLOCKING).** ARCH V2 §C.3 calls 050
  "PROPOSED CORE REPAIR"; brief D5 lists 050 ADOPT-ONLY. 010a implements the brief
  (policy only, synthetic fixtures); 010b/operator reconcile the component label.
- **OQ-4 — Baseline filename (NON-BLOCKING).** ARCH §C.3 shows
  `000_baseline_v2.0.5.1.sql`; brief D1 uses `NNN_<slug>.sql` with ID
  `000_baseline`. 010a authors no baseline; 010b picks the on-disk name and aligns
  ARCH §C.3.
- **OQ-5 — CLI write-path vs quantd-only rule (NON-BLOCKING).** Constitution §6
  restricts operator mutations to `quantctl → quantd`. D14 resolves this by
  allowing the standalone CLI only when quantd is stopped; confirm the CLI command
  name/home (`quantflow migrate` vs `quantctl`) during apply.
- **OQ-6 — Python version drift (NON-BLOCKING).** `pyproject.toml` declares
  `requires-python = ">=3.14"` while the project context says Python 3.12.
  Documentation drift only; no migration-runner behavior depends on it.

## Operator Resolutions (2026-10-17)

Both blocking OQs from the propose run are RESOLVED. Proposed
resolutions match the pre-resolved answers in
`openspec/conflicts-and-gaps.md` section "010a Open Questions
(pre-resolved 2026-10-17)".

### OQ-1 (was BLOCKING) — RESOLVED

Retry/audit representation. Adopt the proposed resolution:
- `schema_version_<store>` remains a single-row-per-`migration_id`
  state machine (PK on `migration_id`). No additional per-attempt
  history rows in the ledger.
- Retry path: `apply` sees a FAILED row -> blocks. Operator invokes
  `quantflow migrate retry-failed --store <s> --id <id> --reason "<text>"`.
  The runner DELETEs the FAILED row, re-applies the migration in a
  normal transaction, and writes an `operator_control_audit` row
  (`channel='QUANTCTL'`, `action='migration_retry_failed'`,
  `target_ref=<migration_id>`, `reason=<operator-supplied>`).
- No SPEC §19 DDL change required. D12 is implementable as written.
- `--reason` is required; missing -> exit 2.
- Consequently tasks 5.4 is IN scope (`--retry-failed` is built,
  not deferred).

Matches: C14 in `openspec/conflicts-and-gaps.md`.

### OQ-2 (was BLOCKING) — RESOLVED

Manifest file format. Adopt the proposed resolution:
- `migrations/MANIFEST.json` is canonical for 010a. ARCH V2 §C.3's
  `MANIFEST.md` reference is recorded as drift.
- No ARCH V2 §C.3 edit during 010a apply (frozen docs untouched).
- An ARCH §C.3 amendment is queued for 010b as a governance task,
  not 010a.

Matches: C13 in `openspec/conflicts-and-gaps.md`.

### OQ-3 through OQ-6 — NON-BLOCKING, accepted as written

- OQ-3 DuckDB 050 classification: ADOPT-ONLY per D5.
- OQ-4 baseline filename: `000_baseline_v2.0.5.1.sql` for the file,
  `000_baseline` for the logical ID. Both correct, no conflict.
- OQ-5 CLI write path vs quantd-only: D14 already addresses both
  embedded and standalone modes.
- OQ-6 Python version drift: pyproject is ground truth, no action.

Apply is unblocked.
