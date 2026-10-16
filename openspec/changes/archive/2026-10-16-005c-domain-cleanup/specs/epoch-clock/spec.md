# Spec Delta — epoch-clock

## MODIFIED Requirements

### Requirement: Epoch vs duration naming rule

Field names matching `*_ts`, `*_at`, `*_until`, `*_epoch_ms`, `*_epoch_ns`, or
`*epoch_*` SHALL be epoch values. Field names matching `*latency_ms`,
`*staleness_ms`, `*age_ms`, `*duration_ms`, or `*response_ms` SHALL be bounded
durations carried as integers. A `*` in these patterns means an underscore-delimited
prefix: a name matches a duration suffix only if it equals the suffix or ends with
`_` plus the suffix. Names matching `_ms` without a duration or epoch qualifier SHALL
be rejected as ambiguous. Names that match BOTH an epoch pattern and a duration
pattern (for example `epoch_latency_ms`) SHALL be rejected as ambiguous; silent
precedence is not permitted. A schema-style rule test SHALL verify this for every
typed field name this feature introduces.
Source: SPEC V1 Sec 19.8.3 Rule 1 and Rule 2 ("Ambiguous names (e.g., *_ms without a
duration qualifier) fail the test and require an explicit rename"); 005a review Q13;
005c brief D4 (`*_until` added).

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

#### Scenario: Name matching both patterns is rejected
- **WHEN** a field named `epoch_latency_ms` is classified (matches `*epoch_*`
  and `*latency_ms`)
- **THEN** the naming rule raises a field-name error (ambiguous)

#### Scenario: `_until` names are epoch values
- **WHEN** a field named `cooldown_until` is classified
- **THEN** the naming rule returns `epoch`

#### Scenario: Duration values are BIGINT-parity with a validated maximum
- **WHEN** a duration value is constructed that is negative or exceeds
  `DURATION_MS_MAX` (named structural constant, validated in code)
- **THEN** construction fails explicitly (fail closed, no wrap, no clamp);
  DurationMs keeps 64-bit BIGINT / SQLite INTEGER parity -- no int32 type
  bound; structural value bound 2**31-1 enforced at construction
  (operator ruling 2026-10-15; the SPEC V1 Sec 19.8.3 Rule 2 INTEGER mapping
  is satisfied at 64-bit in Python)

### Requirement: Injectable Clock port, as_of-only time

Domain and kernel code SHALL obtain current time only through an injected Clock port
(or an `as_of` parameter); direct wall-clock reads in `src/quantflow/domain/**` and
`src/quantflow/kernels/**` SHALL fail an AST lint test. The AST scan SHALL reject the
banned call names (`now`, `utcnow`, `today`, `monotonic`, `time`, `time_ns`,
`monotonic_ns`, `perf_counter`, `perf_counter_ns`, `process_time`, `process_time_ns`,
`urandom`, `getrandbits`, `uuid1`, `uuid4`), the banned modules (`time`, `datetime`,
`secrets`, `random`, `uuid`), concrete `quantflow.adapters.*` imports, and relative
imports (`from .` / `from ..`). Randomness SHALL be as_of-seeded only, enforced by
rejecting the `random` and `uuid` modules outright; a randomness-seeded method call
on an injected generator SHALL NOT be treated as a wall-clock violation.
Source: SPEC V1 Sec 2.9.4.2 ("No wall-clock reads except as_of"), Sec 2.9.4.3, Sec
2.9.4.8 (AST lint pattern); constitution Sec 5; 005a review (scan hardening + Q12);
005b review follow-up (005c brief D5).

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

#### Scenario: Random and uuid imports are rejected
- **WHEN** a domain or kernel module imports `random` or `uuid` (and then calls
  `random.randint`, `random.randrange`, `random.getrandbits`, `secrets.token_hex`,
  `uuid.uuid1`, or `uuid.uuid4`)
- **THEN** the AST scan reports a violation for the banned module import of each
  shape (the module ban, not a call name, governs these)

#### Scenario: Injected generator method is not a wall-clock violation
- **WHEN** a fixture `def f(rng): return rng.random() + rng.normal()` uses an
  injected generator's randomness-seeded methods
- **THEN** the AST scan reports zero violations (the `random` module ban, not the
  call name, governs randomness)

## ADDED Requirements

### Requirement: Frozen-DDL time-token columns classify under the naming rule

Every SPEC V2 §19.2 column name that declares a time semantic — an epoch or duration
token on an underscore token boundary — SHALL classify as epoch or duration. Names with
no time token are out of scope by construction; no non-time allowlist is maintained.
`*_date` columns follow SPEC V1 §19.8.1 (TEXT) and SHALL NOT classify as epoch or
duration.
Source: SPEC V1 §19.8.3 Rule 1; SPEC V2 §19.2; 005c brief D4/2.4.

#### Scenario: Every time-token column classifies
- **WHEN** the conformance test filters the §19.2 column names to those carrying a
  time token (`_ts`, `_at`, `_until`, `_ms`, `_ns`, `epoch_*`)
- **THEN** every such name classifies as `epoch` or `duration` (none raises
  `FieldNameError`)

#### Scenario: `cooldown_until` classifies as epoch
- **WHEN** `cooldown_until` (SPEC V2 §19.2 `spx_crossing_state_current` and its DuckDB
  form) is classified
- **THEN** it returns `epoch` (regression: it raised `FieldNameError` before `_until`
  was an epoch suffix)

#### Scenario: `rearmed_at` classifies as epoch
- **WHEN** `rearmed_at` is classified
- **THEN** it returns `epoch` via the `_at` suffix

#### Scenario: A column with no time token is out of scope
- **WHEN** a §19.2 column name carries no time token (e.g. `rows_inserted`,
  `attempt_count`)
- **THEN** it is not required to classify and the conformance test does not fail

#### Scenario: A substring token does not declare a time semantic
- **WHEN** `max_attempts` (contains, but does not end with, `_at`) or
  `spot_at_entry_micros` is examined
- **THEN** it is not treated as a time declaration and the conformance test does not
  fail

#### Scenario: Date columns are TEXT, not epoch values
- **WHEN** a `*_date` column (e.g. `session_date`, SPEC V1 §19.8.1) is examined
- **THEN** it is TEXT and does not classify as epoch or duration

#### Scenario: Known time columns are pinned
- **WHEN** a positive list of known §19.2 time columns (`created_at`, `updated_at`,
  `applied_at`, `quote_ts`, `entry_ts`, `provider_ts`, `staleness_ms`, and others) is
  classified
- **THEN** each returns its expected `epoch` or `duration` kind
