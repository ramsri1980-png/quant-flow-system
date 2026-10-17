# migration-runner

## Purpose

A forward-only, checksum-verified schema migration capability for SQLite
`quant_state.db` and DuckDB `quant_flow.duckdb` that authorizes which migration
files may run, records applied migrations in the SPEC-defined ledger, applies
each migration atomically, and lets the operator verify consistency read-only.

## Requirements
### Requirement: Authorized migration manifest

The system SHALL maintain a single machine-readable migration manifest declaring,
for every authorized migration, the fields `id`, `store`, `path`, `sha256`,
`applies_after`, `component`, and `enabled`. `applies_after` MUST be an array of
migration IDs (`[]` for a root entry).
Source: brief D1/D4; ARCH V2 §C.3 ("Manifest entries record store, migration_id,
SHA-256, dependencies, component ... and explicit enabled/adopted state").

#### Scenario: Valid manifest entry is accepted
- **WHEN** an entry provides every required field, an array `applies_after`, and a
  path under `migrations/<store>/NNN_<slug>.sql`
- **THEN** validation accepts the entry

#### Scenario: Missing required field fails
- **WHEN** an entry omits any of `id`, `store`, `path`, `sha256`, `applies_after`,
  `component`, or `enabled`
- **THEN** validation fails closed naming the field

#### Scenario: Scalar dependency is rejected
- **WHEN** an entry declares `applies_after` as a scalar ID instead of an array
- **THEN** validation fails closed

### Requirement: Store-local dependencies

Migration dependencies SHALL be store-local: a dependency MAY name only an ID in
the same store's manifest (or validated baseline coverage). A cross-store
`applies_after` reference SHALL fail validation, since no cross-store dependency
feature is approved.
Source: brief D1/D4; ARCH V2 §C.3 (per-store manifest provenance).

#### Scenario: Cross-store dependency is rejected
- **WHEN** an entry's `applies_after` names an ID in the other store
- **THEN** validation fails closed

### Requirement: Manifest path safety and ID uniqueness

Every manifest entry path SHALL resolve inside `migrations/<store>/` and use the
form `NNN_<slug>.sql`; path traversal, absolute paths, and duplicate `id` values
within a store SHALL fail validation.
Source: brief D1/D5; ARCH V2 §C.3 (flat `migrations/sqlite|duckdb` layout).

#### Scenario: Traversal path is rejected
- **WHEN** a `path` escapes `migrations/<store>/` (for example `../other/x.sql`)
- **THEN** validation fails closed

#### Scenario: Duplicate ID fails
- **WHEN** two entries in the same store share an `id`
- **THEN** validation fails closed

### Requirement: Reserved and ADOPT-ONLY slot policy

For v2.0.5.1 the manifest SHALL reject any entry whose numeric ID is in SQLite
072–079 or DuckDB 046–049 as an error, and SHALL NOT auto-apply ADOPT-ONLY entries
(DuckDB 043–045 and 050; SQLite 071) until an explicit operator-approved
enablement. Every other entry MUST carry an explicit `component` and `enabled`
state.
Source: ARCH V2 §C.3 ("072..079 RESERVED", "046..049 RESERVED", "043 ... ADOPTION
REQUIRED"); ARCH V4 §AH.6.6; constitution §9; brief D5.

#### Scenario: Reserved ID is an error
- **WHEN** a manifest entry uses SQLite 075 or DuckDB 047
- **THEN** validation fails closed

#### Scenario: ADOPT-ONLY is not auto-applied
- **WHEN** an ADOPT-ONLY entry (for example DuckDB 043) is not operator-enabled
- **THEN** it is reported but SHALL NOT be applied by `apply`

#### Scenario: Unclassified entry fails
- **WHEN** an entry outside the reserved and ADOPT-ONLY sets omits its explicit
  classification
- **THEN** validation fails closed

### Requirement: Unmanifested migration files are an error

Every `*.sql` file present under `migrations/<store>/` SHALL have a manifest entry;
any unmanifested SQL file SHALL fail validation.
Source: brief D5; constitution §9 (forward-only, manifest-recorded migrations).

#### Scenario: Unmanifested file fails
- **WHEN** a `.sql` file exists on disk under `migrations/<store>/` with no
  manifest entry
- **THEN** validation fails closed naming the file

### Requirement: Dependency existence, acyclicity and stable order

The system SHALL reject a manifest whose dependencies reference an unknown
store-local ID or form a cycle, and SHALL apply enabled migrations in a stable
topological order using numeric ID as the only tie-break, with `000_baseline`
first. Ordering SHALL NOT rely on `MAX(migration_id)`.
Source: ARCH V2 §C.3 ("Validate dependency closure ... execute a stable
topological ordering (numeric ID breaks ties only). Never infer completeness from
MAX(migration_id)"); brief Implementation 1.

#### Scenario: Unknown dependency fails
- **WHEN** an entry's `applies_after` names an ID with no same-store manifest entry
  or validated baseline coverage
- **THEN** validation fails closed

#### Scenario: Cycle is rejected
- **WHEN** two entries depend on each other
- **THEN** validation fails closed

#### Scenario: Order is stable and reproducible
- **WHEN** two enabled migrations have no ordering constraint
- **THEN** they are ordered by numeric ID, identically on every run

### Requirement: Immutable, checksum-verified migration files

A migration file's lowercase SHA-256 of its exact bytes SHALL equal the manifest
`sha256`; applied migrations MUST be forward-only and never edited. Any
on-disk/manifest/ledger checksum mismatch SHALL fail closed before applying
anything.
Source: SPEC V1 §19.6 invariant K ("Every applied migration recorded with
checksum"); ARCH V2 §C.3 ("Forward-only. Never edit an applied migration");
brief D10.

#### Scenario: Checksum mismatch fails closed
- **WHEN** a file's bytes no longer hash to its manifest `sha256`
- **THEN** validation and `apply` fail closed without executing the file

#### Scenario: Verify detects an edited applied migration
- **WHEN** an already-applied file was modified so its hash differs from the
  recorded one
- **THEN** `verify` reports drift and exits non-zero

### Requirement: Authoritative ledger bootstrap

Before any migration, the system SHALL create the SPEC-defined ledger
`schema_version_sqlite` / `schema_version_duckdb` (the exact SPEC V2 §19 columns)
in its own committed transaction. Ledger creation MUST NOT be part of a
migration's transactional payload, and a bootstrap failure SHALL surface as a hard
error and MUST NOT be recorded as a migration FAILED row.
Source: SPEC V2 §19.2 (ledger DDL); ARCH V2 §C.1; brief D7.

#### Scenario: Ledger exists before first migration
- **WHEN** `apply` runs on a fresh store
- **THEN** the ledger table is committed before any migration SQL runs

#### Scenario: Bootstrap failure is a hard error
- **WHEN** the ledger cannot be created
- **THEN** the run aborts with a hard error and writes no migration outcome row

### Requirement: Store classification

The system SHALL classify each store as fresh (no application schema and no OK
baseline ledger row), already-baselined (an OK baseline ledger row exists), or
legacy (application schema present without an OK baseline row). A legacy store MUST
NOT be overwritten or silently adopted and SHALL abort pending an explicit 010b
adoption plan. An existing but empty ledger is baseline-eligible only when
inspection confirms no pre-existing application table (excluding the ledger
itself).
Source: brief D6.

#### Scenario: Fresh store is baselined
- **WHEN** a store has no application tables and no ledger row
- **THEN** it is classified fresh and eligible to baseline

#### Scenario: Already-baselined store is not re-baselined
- **WHEN** an OK `000_baseline` ledger row exists
- **THEN** the store is treated as already baselined, not fresh

#### Scenario: Legacy store aborts
- **WHEN** application tables exist with no OK baseline ledger row
- **THEN** `apply` aborts pending a 010b adoption plan and overwrites nothing

#### Scenario: Non-empty ledger is not silently adopted
- **WHEN** a ledger exists with rows but inspection cannot confirm the store is
  empty of application tables
- **THEN** the store is not treated as baseline-eligible

### Requirement: Ledger outcome states

The ledger `result` SHALL be only `'OK'` or `'FAILED'`; there SHALL be no
`IN_PROGRESS` or other value. A successful migration SHALL leave exactly one OK row
for its `migration_id`; a `FAILED` row SHALL block further `apply` by default and
SHALL make `verify` fail.
Source: SPEC V2 §19.2 (`result TEXT NOT NULL CHECK(result IN ('OK','FAILED'))`);
brief D12.

#### Scenario: No IN_PROGRESS state is written
- **WHEN** any migration starts, runs, or ends
- **THEN** no ledger row with a value other than `OK` or `FAILED` is ever written

#### Scenario: FAILED blocks apply
- **WHEN** a `FAILED` row exists for a migration
- **THEN** a subsequent `apply` aborts instead of retrying automatically

#### Scenario: Status and verify surface FAILED
- **WHEN** the ledger contains a `FAILED` row
- **THEN** `status` reports it and `verify` exits with a failure code

### Requirement: Atomic apply and rollback

Each migration SHALL execute in an explicit transaction (`BEGIN`/`COMMIT`) using a
statement strategy that handles semicolons inside triggers and quoted text;
`executescript()` and naive `;` splitting MUST NOT be used. On failure the migration
DDL and its OK row SHALL be rolled back and a single `FAILED` record written in a
new transaction, leaving no partial DDL.
Source: brief D13/D7; ARCH V2 §C.3.

#### Scenario: Failure leaves no partial DDL
- **WHEN** a migration fails partway through its statements
- **THEN** none of its DDL is committed and exactly one `FAILED` row exists

#### Scenario: executescript is not used
- **WHEN** a transactional migration is executed
- **THEN** it is run via explicit `BEGIN`/`COMMIT` with no implicit commit

#### Scenario: Semicolon in a trigger is handled
- **WHEN** a migration contains a trigger or quoted text with embedded semicolons
- **THEN** the statements are executed correctly without naive splitting

### Requirement: Baseline ledger identity

The reserved store-local migration ID `000_baseline` SHALL be an ordinary manifest
entry with a `path` and SHA-256. On success its ledger row SHALL carry
`migration_id` exactly `000_baseline`, the lowercase SHA-256 of the exact file
bytes, the application version, and a Clock-port `applied_at`; no checksum sentinel
SHALL be invented.
Source: brief D10/D11; SPEC V2 §19.2.

#### Scenario: Baseline row uses the real checksum
- **WHEN** `000_baseline` commits successfully
- **THEN** its ledger row records the actual file SHA-256, not a sentinel

#### Scenario: Baseline is a real ledger row
- **WHEN** the store is already baselined
- **THEN** `000_baseline` exists as an ordinary successful ledger row

### Requirement: Baseline dependency closure

A migration with `applies_after: ["000_baseline"]` SHALL pass closure only when the
same store's OK baseline ledger row exists. `baseline_covered` SHALL be
informational history only and MUST NOT be represented as a fabricated OK ledger
row; every applied dependency MUST be satisfied.
Source: brief D11; ARCH V2 §C.3.

#### Scenario: Baseline dependency unsatisfied fails closure
- **WHEN** a post-baseline migration depends on `000_baseline` but no OK baseline
  row exists in that store
- **THEN** closure fails and the migration is not applied

#### Scenario: baseline_covered is not an OK row
- **WHEN** covered historical IDs are recorded as manifest metadata
- **THEN** they are not written or read as OK ledger rows

### Requirement: Application version source

Ledger `app_version` SHALL come solely from
`importlib.metadata.version("quantflow")`. When package metadata is unavailable the
run SHALL fail with an actionable packaging error and MUST NOT write `unknown`, a
hard-coded version, or any fallback.
Source: brief D8.

#### Scenario: Version comes from metadata
- **WHEN** a ledger row is written
- **THEN** `app_version` equals the installed package version

#### Scenario: Missing metadata fails loudly
- **WHEN** the package version cannot be resolved
- **THEN** the run fails with a packaging error and writes no fallback value

### Requirement: Independent per-store results

`--store both` SHALL run SQLite then DuckDB and report each store's outcome
independently. There SHALL be no cross-store atomicity; a DuckDB failure MUST NOT
roll back a committed SQLite migration, and success SHALL NOT be reported for a
store that failed.
Source: brief D9.

#### Scenario: DuckDB failure keeps committed SQLite
- **WHEN** SQLite commits and DuckDB then fails
- **THEN** the SQLite migration stays applied and the DuckDB failure is reported
  separately

#### Scenario: Success is not overstated
- **WHEN** either store fails
- **THEN** the run does not report both stores as successful

### Requirement: Read-only status and verify

`migrate status` and `migrate verify` SHALL be strictly read-only: they MUST NOT
write a ledger, set mutating PRAGMAs, or create a database, and MUST report a
missing store explicitly rather than silently succeeding.
Source: brief D15.

#### Scenario: Verify does not mutate
- **WHEN** `verify` runs against a store
- **THEN** no ledger row is written, no mutating PRAGMA is set, and no database is
  created

#### Scenario: Missing store is explicit
- **WHEN** the target database does not exist
- **THEN** `status`/`verify` report it explicitly

### Requirement: Verify check set

`verify` SHALL check manifest schema and required fields; uniqueness and
store-local dependency existence; acyclicity; unmanifested files; slot policy;
on-disk SHA-256 against the manifest; ledger/manifest agreement (every OK row has
an entry and an identical checksum); baseline identity and presence; applied
dependency closure; absence of `FAILED` rows; and no unexpected DB-newer-than-code
rows.
Source: brief D15; ARCH V2 §C.4.

#### Scenario: Drift is reported
- **WHEN** a checksum mismatch, missing ledger entry, or unexpected newer row is
  found
- **THEN** `verify` reports the specific drift

#### Scenario: Pending is not corruption
- **WHEN** enabled migrations are pending
- **THEN** they are reported as `PENDING` and do not fail an otherwise consistent
  `verify`

#### Scenario: DB-newer is reported
- **WHEN** the database contains an applied migration absent from the code
- **THEN** `verify` reports the DB-newer drift and fails

### Requirement: Verify exit codes

`verify` SHALL exit 0 when the store is consistent, 1 on validation, drift, or
failure, and 2 on a CLI/usage/configuration error.
Source: brief D15.

#### Scenario: Consistent store exits 0
- **WHEN** everything is consistent
- **THEN** `verify` exits 0

#### Scenario: Drift exits 1
- **WHEN** a checksum mismatch, missing ledger entry, or unexpected newer row is
  found
- **THEN** `verify` exits 1

#### Scenario: Usage error exits 2
- **WHEN** the CLI is invoked with an unknown store or invalid usage
- **THEN** the command exits 2

### Requirement: Standalone connection PRAGMAs

Standalone CLI SHALL open its own SQLite connection only when quantd is stopped
and SHALL set `journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=ON`, and
`busy_timeout=5000` before `BEGIN`, verifying the values and refusing incompatible
state.
Source: ARCH V2 §C.1 (store pragmas); brief D14.

#### Scenario: Incompatible PRAGMAs are refused
- **WHEN** a standalone connection cannot obtain the required PRAGMA values before
  `BEGIN`
- **THEN** the run refuses to proceed

### Requirement: Embedded reuse and DuckDB temp_directory

Embedded (quantd) mode SHALL reuse the quantd-owned SQLite connection and MUST NOT
open a competing writer. DuckDB `temp_directory` SHALL be set before the write
connection, using the documented path policy; tests MUST NOT use a `/data` path.
Source: ARCH V2 §C.1 (WAL single writer); brief D14.

#### Scenario: No competing writer
- **WHEN** quantd holds the write connection
- **THEN** the runner does not open a second SQLite writer

#### Scenario: DuckDB temp_directory is set before writing
- **WHEN** a DuckDB migration connection is opened
- **THEN** `temp_directory` is set first using the documented path policy

### Requirement: Forward-only, DB-newer drift

The engine SHALL be forward-only with no down migrations; a store whose applied
migration set is newer than the code SHALL be reported as drift and MUST NOT be
silently downgraded or modified.
Source: ARCH V2 §C.3 ("Forward-only. Never edit an applied migration"); brief D15.

#### Scenario: No down migration exists
- **WHEN** the manifest and CLI are inspected
- **THEN** no down/rollback migration operation is offered

#### Scenario: Newer store is not modified
- **WHEN** the store has applied migrations the code does not know
- **THEN** the runner reports drift and modifies nothing
