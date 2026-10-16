# domain-constants Specification

## Purpose
TBD - created by archiving change 005b-domain-fail-closed. Update Purpose after archive.

## Requirements

### Requirement: Approved constants accessor
The generated constants module SHALL expose every named constant value and
SHALL additionally expose an `approved(name)` accessor. `approved(name)`
SHALL return the constant value only when the name is NOT in the
approval-pending set; otherwise it SHALL raise `ConstantsError`. Direct
reads of any approval-pending constant name inside `src/quantflow/domain/**`
or `src/quantflow/kernels/**` SHALL fail an AST test.
Source: ARCH V1 Sec AI.3 (approval-pending set); 005a review Q6.

#### Scenario: Approved constant is readable
- **WHEN** `approved("THETA_MICROCENTS_PER_CENT")` is called
- **THEN** the current integer value is returned

#### Scenario: Pending constant raises
- **WHEN** `approved("<some-approval-pending-name>")` is called
- **THEN** `ConstantsError` is raised

#### Scenario: Unknown name raises
- **WHEN** `approved("NOT_A_REAL_CONSTANT")` is called
- **THEN** `ConstantsError` is raised

#### Scenario: Direct pending read in domain fails AST test
- **WHEN** a module under `src/quantflow/domain/**` or
  `src/quantflow/kernels/**` reads an approval-pending constant name
  directly (not via `approved(...)`)
- **THEN** the AST test fails and the read must be replaced by `approved(...)`

### Requirement: Constant names encode their unit suffix

Every UPPER_SNAKE_CASE constant exposed by the generated domain constants module
SHALL end in a registered unit or shape suffix, or appear in an explicit allowlist
that records a reason. A lint SHALL fail on a constant that is neither registered nor
allowlisted; the allowlist SHALL grow only deliberately, one entry at a time.
Source: 005c brief D1/B1b; ARCH V1 §AI.3; conflicts Q3/Q4.

#### Scenario: Registered suffix vocabulary
- **WHEN** the registered suffix set is inspected
- **THEN** it is `_MS`, `_S`, `_DAYS`, `_D`, `_USD`, `_CENTS`, `_MICROS`, `_MILLS`,
  `_MICROCENTS`, `_BPS`, `_MB`, `_PCT`, `_PPM`, `_RATIO`, `_FRAC`, `_PCTL`, `_MULT`,
  `_COUNT`, `_SNAPS`, `_H`, `_WEIGHT`

#### Scenario: Registered suffix passes
- **WHEN** a constant such as `THETA_MICROCENTS_PER_CENT` (`_MICROCENTS`) or
  `ZERO_DTE_MEMBER_LATENCY_MAX_MS` (`_MS`) is linted
- **THEN** the unit-suffix lint reports no violation

#### Scenario: Unregistered suffix without an allowlist entry fails
- **WHEN** the generated module exposes an UPPER_SNAKE constant whose suffix is not
  registered and which is not allowlisted
- **THEN** the lint fails and names the constant

#### Scenario: Deliberately-bad fixture fails the lint
- **WHEN** the lint runs over a fixture containing a constant with an unknown suffix
- **THEN** the lint reports a violation for that constant

#### Scenario: Allowlisted constant requires a recorded reason
- **WHEN** a constant is exempted from the suffix rule
- **THEN** the allowlist entry carries a non-empty reason string, and an entry
  without a reason fails the lint

### Requirement: Whole percent points and dimensionless ratios are distinct suffixes

`_PCT` SHALL carry whole percent points as an integer (`60` means 60%). `_RATIO`
SHALL carry a dimensionless [0,1] ratio as a float. No fraction-valued `_PCT`
constant SHALL remain. `_PCTL` SHALL carry an integer percentile rank (e.g. 20, 80,
90), distinct from `_PCT`. Decision-path thresholds that gate a state remain a
`_PPM` migration follow-up and SHALL NOT be converted in this change.
Source: 005c brief D1/B1b; ARCH V1 §AI.3; conflicts Q3.

#### Scenario: Fraction-valued percent constant is renamed to ratio
- **WHEN** the generated module is inspected
- **THEN** `SPX_FALSE_CROSS_TOLERANCE_RATIO` equals `0.0015` and
  `SPX_FALSE_CROSS_TOLERANCE_PCT` is not exposed

#### Scenario: Whole percent point keeps the percent suffix
- **WHEN** `BUDGET_FLOW_ALERT_RESERVE_PCT` and `BUDGET_PREMARKET_BORROW_PCT` are read
- **THEN** they remain `_PCT` with integer values 60 and 20

#### Scenario: Percentile keeps the percentile suffix
- **WHEN** `VANNA_THETA_PCTL` is read
- **THEN** it remains `_PCTL` with integer value 90

#### Scenario: No fraction-valued percent constant remains
- **WHEN** the lint scans the generated module for `_PCT` constants with a value
  strictly between 0 and 1
- **THEN** it reports no violation

### Requirement: Lane latency cutoffs are named with their millisecond unit

The lane latency hard-cutoff constants SHALL be named
`LANE_LATENCY_CUTOFF_MS_2DTE` (3000), `LANE_LATENCY_CUTOFF_MS_SHORT_TACTICAL`
(5000), `LANE_LATENCY_CUTOFF_MS_SWING` (10000), and
`LANE_LATENCY_CUTOFF_MS_LONGER_HORIZON` (30000). The generated module SHALL NOT
expose the bare lane names as latency constants.
Source: ARCH V1 §AI.3 ("Lane latency hard cutoffs (ms)"); 005c brief D1/Q4.

#### Scenario: Renamed latency constants carry the millisecond unit
- **WHEN** the four `LANE_LATENCY_CUTOFF_MS_*` constants are read
- **THEN** their values are 3000, 5000, 10000, and 30000

#### Scenario: Bare lane names are not latency constants
- **WHEN** the generated module is inspected for `TACTICAL_2DTE`, `SHORT_TACTICAL`,
  `SWING`, or `LONGER_HORIZON`
- **THEN** none is exposed as a latency constant (the lane labels reused by
  ARCH V1 §AI.4–§AI.6 are out of scope)

### Requirement: The approval-pending set is exhaustive and labelled from its source

In the generated constants module every AI.3 constant SHALL be either readable as a
value (approved) or accompanied by a `<NAME>_APPROVAL_PENDING = True` companion. A
validator SHALL fail with a clear error when a constant is neither.
Source: 005c brief D1/Q5; ARCH V1 §AI.3; conflicts Q5.

#### Scenario: Pending set is taken from the RECOMMENDED block
- **WHEN** the pending set is derived
- **THEN** it is exactly the ARCH V1 §AI.3 `[RECOMMENDED ...]` block members, and the
  module's pending-set label is that marker's own text (not a hardcoded string)

#### Scenario: Block member is pending with a companion flag
- **WHEN** `DEALER_T_MIN_S` (inside the `[RECOMMENDED ...]` block) is inspected
- **THEN** `DEALER_T_MIN_S_APPROVAL_PENDING` is `True`

#### Scenario: Constant above the block is approved
- **WHEN** `MIN_VEGA` (declared above the `[RECOMMENDED ...]` marker) is inspected
- **THEN** it is readable as a value and has no `_APPROVAL_PENDING` companion

#### Scenario: Orphan constant fails the validator
- **WHEN** a constant is neither approved nor marked pending
- **THEN** the validator exits non-zero with a clear error naming the constant

#### Scenario: Pending label is derived from the marker
- **WHEN** the ARCH V1 §AI.3 `[RECOMMENDED ...]` marker text changes
- **THEN** the module's pending-set label changes with it, with no hardcoded
  "C12 dealer/greeks" string in the generator
