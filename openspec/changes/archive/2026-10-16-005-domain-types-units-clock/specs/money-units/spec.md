# Spec Delta: money-units

## Purpose
Canonical integer representation of money and price values for the decision
path: option prices in cents, underlying/index prices in micros, strikes and
levels in mills. Floats are rejected on the decision path; dollars appear only
at formula boundaries.

## ADDED Requirements

### Requirement: Typed integer unit wrappers
The system SHALL represent option prices as an integer `_cents` wrapper,
underlying/index prices as an integer `_micros` wrapper, and strikes/levels as
an integer `_mills` wrapper. Wrappers SHALL be constructible only from
integers that fit in a signed 64-bit range (SQLite INTEGER 64-bit; DuckDB
BIGINT for decision-path unit columns) and SHALL reject construction outside
that range rather than wrap or clamp.
Source: SPEC V1 Sec 19.4.1-19.4.4; SPEC V1 Sec 1.4.13, 1.4.25; SPEC V2 Sec
19.4.4; constitution Sec 4.

#### Scenario: Construct from a valid integer
- **WHEN** a `_cents` value is constructed from a Python `int` within signed 64-bit range
- **THEN** the value is stored exactly with no loss

#### Scenario: Overflow at construction is rejected
- **WHEN** a `_micros` value is constructed from an integer outside signed 64-bit range
- **THEN** construction fails with an explicit error (no wrap, no clamp, no default)

#### Scenario: Negative value round-trips unchanged
- **WHEN** a `_mills` value is constructed from a negative integer within signed 64-bit range
- **THEN** the value round-trips unchanged (no silent clamping; sign rules for
  derived quantities belong to the kernels that consume these types)

### Requirement: Float is rejected on the decision path
No decision-path API SHALL accept a `float` where a unit-typed integer is
required. Passing a `float` to a unit wrapper constructor SHALL raise a type
error. DOUBLE columns and float arithmetic are analysis-only.
Source: SPEC V1 Sec 19.4.6 ("DOUBLE columns are analysis only"); SPEC V1 Sec
1.4.6 (deterministic numeric path); constitution Sec 4.

#### Scenario: Float passed where int is required
- **WHEN** a `float` (e.g. a dollar amount) is passed to a `_cents` wrapper constructor
- **THEN** construction raises a type error and no value enters the decision path

### Requirement: Dollars only at formula boundaries
The domain layer SHALL NOT convert unit integers to dollars. Any
unit-to-dollars conversion (division by 1,000,000 micros/microcents scales or
100/1000 unit scales as applicable at each formula) SHALL exist only at a
formula boundary in kernel code, never in `src/quantflow/domain/**` types.
Rounding SHALL be integer-only with round-half-even at the display boundary
(operator ruling 2026-10-15): the decision path carries integers end-to-end
and no fractional dollars value enters or persists there; where an integer
unit conversion or a display-boundary dollars conversion requires rounding,
it uses round-half-even.
Source: constitution Sec 4 ("dollars only at formula boundaries (÷1e6)");
SPEC V1 Sec 19.4; ARCH V1 Sec AI.3 (THETA_MICROCENTS_PER_CENT 1000000);
operator ruling 2026-10-15 (design.md Open Questions, rounding resolved).

#### Scenario: Domain types expose no dollars accessor
- **WHEN** the domain unit wrappers are inspected
- **THEN** they expose integer unit arithmetic only, with no `to_dollars` or
  float-producing accessor in `src/quantflow/domain/**`

#### Scenario: Rounding is integer-only and half-even
- **WHEN** an integer unit conversion requires rounding (e.g. micros → mills)
  or a dollars figure is produced for display at a formula boundary
- **THEN** the result is an integer produced with round-half-even; no
  fractional (float) dollars value enters or persists in the decision path

#### Scenario: Rounding behavior is not invented per formula
- **WHEN** a unit-to-dollars conversion is required by a formula
- **THEN** it applies round-half-even at the display boundary (the single
  global rule; no per-formula rounding mode is assumed or invented)
