# epoch-clock Specification

## Purpose
UTC epoch-millisecond time representation, the epoch-vs-duration naming rule,
ET-display-only rule, and the injectable Clock port that keeps wall-clock
reads out of domain and kernel code.

## Requirements

### Requirement: Timestamps are UTC epoch milliseconds
All timestamps SHALL be UTC epoch milliseconds carried as integers. Storage
correspondence: SQLite INTEGER (64-bit), DuckDB BIGINT; no DuckDB TIMESTAMP.
Source: SPEC V1 Sec 19.8.3 ("Timestamps UTC epoch ms. SQLite: INTEGER
(64-bit). DuckDB: BIGINT"); SPEC V2 Sec 19.6 invariant W; constitution Sec 4.

#### Scenario: Float timestamp is rejected
- **WHEN** a float is passed where an epoch-ms value is required
- **THEN** construction raises a type error

#### Scenario: Value outside signed 64-bit is rejected
- **WHEN** an epoch-ms value outside signed 64-bit range is constructed
- **THEN** construction fails explicitly (fail closed, no wrap)

### Requirement: Epoch vs duration naming rule
Field names matching `*_ts`, `*_at`, `*_epoch_ms`, `*_epoch_ns`, or `*epoch_*`
SHALL be epoch values. Field names matching `*latency_ms`, `*staleness_ms`,
`*age_ms`, `*duration_ms`, or `*response_ms` SHALL be bounded durations
carried as integers. A `*` in these patterns means an underscore-delimited
prefix: a name matches a duration suffix only if it equals the suffix or ends
with `_` plus the suffix. Names matching `_ms` without a duration or epoch
qualifier SHALL be rejected as ambiguous. A schema-style rule test SHALL
verify this for every typed field name this feature introduces.
Source: SPEC V1 Sec 19.8.3 Rule 1 and Rule 2 ("Ambiguous names (e.g., *_ms
without a duration qualifier) fail the test and require an explicit rename").

#### Scenario: Ambiguous `_ms` name fails
- **WHEN** a field named e.g. `elapsed_ms_wait` (no recognized qualifier) is
  introduced in a typed structure of this feature
- **THEN** the naming rule test fails and the field must be renamed

#### Scenario: Bare suffix lookalike is rejected
- **WHEN** a field named `message_ms` is classified (it ends with `age_ms`
  only across an underscore-delimited token boundary)
- **THEN** the naming rule raises a field-name error (rejected as ambiguous)

#### Scenario: Underscore-delimited duration suffix matches
- **WHEN** a field named `quote_age_ms` is classified
- **THEN** the naming rule returns `duration`

#### Scenario: Duration values are BIGINT-parity with a validated maximum
- **WHEN** a duration value is constructed that is negative or exceeds
  `DURATION_MS_MAX` (named structural constant, validated in code)
- **THEN** construction fails explicitly (fail closed, no wrap, no clamp);
  DurationMs keeps 64-bit BIGINT / SQLite INTEGER parity -- no int32 type
  bound; structural value bound 2**31-1 enforced at construction
  (operator ruling 2026-10-15; the SPEC V1 Sec 19.8.3 Rule 2 INTEGER mapping
  is satisfied at 64-bit in Python)

### Requirement: ET display only
Timestamps SHALL be stored and manipulated only in UTC epoch ms. Timezone
conversion SHALL occur only at display/presentation code; no domain or kernel
type SHALL carry an ET-offset or naive-local timestamp.
Source: SPEC V1 Sec 19.8.4 ("Display timezone operator-local (default ET)").

#### Scenario: Domain type has no timezone state
- **WHEN** an epoch-ms value in domain code is inspected
- **THEN** it carries no timezone or offset information; any ET rendering
  happens in presentation code outside `domain/**` and `kernels/**`

### Requirement: Injectable Clock port, as_of-only time
Domain and kernel code SHALL obtain current time only through an injected
Clock port (or an `as_of` parameter); direct wall-clock reads in
`src/quantflow/domain/**` and `src/quantflow/kernels/**` SHALL fail an AST
lint test. The AST scan SHALL reject the banned call names (`now`, `utcnow`,
`today`, `monotonic`, `time`, `time_ns`, `monotonic_ns`, `perf_counter`,
`perf_counter_ns`, `process_time`, `process_time_ns`, `urandom`), the banned
modules (`time`, `datetime`, `secrets`), concrete `quantflow.adapters.*`
imports, and relative imports (`from .` / `from ..`). Randomness, if any is
introduced later, SHALL be as_of-seeded only; `random` / `uuid` enforcement is
deferred (Q12).
Source: SPEC V1 Sec 2.9.4.2 ("No wall-clock reads except as_of"), Sec 2.9.4.3,
Sec 2.9.4.8 (AST lint pattern); constitution Sec 5; 005a review (scan
hardening).

#### Scenario: Wall-clock read in domain fails the AST test
- **WHEN** `datetime.now()`, `time.time()`, or equivalent is called directly in
  `domain/**` or `kernels/**`
- **THEN** the AST lint test fails

#### Scenario: Same as_of yields identical results
- **WHEN** a pure kernel is invoked twice with identical inputs including the
  same `as_of`
- **THEN** both invocations produce identical output (determinism golden test)

#### Scenario: No clock is reachable without injection
- **WHEN** domain or kernel code is executed without a Clock injected and
  without `as_of` supplied
- **THEN** the code cannot read the current time (no ambient fallback; fail closed)

#### Scenario: Extended scan set and relative imports are rejected
- **WHEN** a domain or kernel module calls an extended banned name (`time_ns`,
  `monotonic_ns`, `perf_counter`, `perf_counter_ns`, `process_time`,
  `process_time_ns`, `urandom`), imports the banned `secrets` module, or uses a
  relative import (`from . import x` / `from ..adapters import clock`)
- **THEN** the AST scan reports a violation for that shape; proven by
  `test_scan_detects_additional_clock_calls` (7 banned calls),
  `test_scan_detects_secrets_import` (1 hit), and
  `test_scan_detects_relative_imports` (2 hits) in
  `tests/unit/test_wall_clock_scan.py`
