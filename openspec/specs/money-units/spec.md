# money-units Specification

## Purpose
Canonical integer representation of money and price values for the decision
path: option prices in cents, underlying/index prices in micros, strikes and
levels in mills. Floats are rejected on the decision path; dollars appear only
at formula boundaries.

## Requirements

### Requirement: Typed integer unit wrappers
The system SHALL represent option prices as an integer `_cents` wrapper,
underlying/index prices as an integer `_micros` wrapper, and strikes/levels as
an integer `_mills` wrapper. Unit values SHALL be created only through the
validating factory functions (`cents`, `micros`, `mills`). Direct NewType
construction is prohibited outside `domain/units.py` and `domain/time.py` and
is enforced by an AST test. Factories SHALL reject non-int, bool, and
out-of-signed-64-bit inputs. Values SHALL fit in a signed 64-bit range
(SQLite INTEGER 64-bit; DuckDB BIGINT for decision-path unit columns), and
construction outside that range SHALL fail rather than wrap or clamp.
Source: SPEC V1 Sec 19.4.1-19.4.4; SPEC V1 Sec 1.4.13, 1.4.25; SPEC V2 Sec
19.4.4; constitution Sec 4 (005a review: factory-only construction).

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

#### Scenario: Unit conversion functions validate input
- **WHEN** `micros_to_mills` receives a float or bool
- **THEN** a type error is raised (fail closed; no truncation or coercion)

#### Scenario: Direct NewType construction outside the two allowed files fails the AST test
- **WHEN** a unit wrapper (`Cents`, `Micros`, `Mills`) is called directly anywhere under
  `src/quantflow/**` other than `domain/units.py` or `domain/time.py`
- **THEN** the AST test fails and the call must be replaced by its validating factory

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
unit-to-dollars conversion SHALL exist only at a formula boundary in kernel
code, never in `src/quantflow/domain/**` types, and SHALL use the divisor
named by that formula's units (micros/microcents scales, 100/1000 unit
scales); no single divisor is assumed for cents or mills, which do not scale
by 1,000,000. Rounding SHALL follow two distinct rules: (a) integer unit
conversions inside the domain (e.g. micros to mills) are integer-only with
round-half-even; (b) any dollars figure produced for display is produced at
the presentation boundary, also with round-half-even. The decision path
carries integers end-to-end and no fractional dollars value enters or
persists there.
Source: constitution Sec 4 ("dollars only at formula boundaries (÷1e6)");
SPEC V1 Sec 19.4; ARCH V1 Sec AI.3 (THETA_MICROCENTS_PER_CENT 1000000);
operator ruling 2026-10-15 (design.md Open Questions, rounding resolved);
005a review (rounding split into rules (a) and (b)).

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

### Requirement: Integer unit conversions are exactly round-half-even

`micros_to_mills` SHALL equal
`int((Decimal(v) / 1000).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))` for every
input integer `v` in the signed 64-bit range, with no float intermediate.
Source: SPEC V1 §19.4 (unit contract); RQ-006 operator ruling (2026-10-15);
money-units "Dollars only at formula boundaries"; 005c brief 2.6.

#### Scenario: Conversion matches the Decimal oracle
- **WHEN** `micros_to_mills(v)` is evaluated for an integer `v` drawn from
  `[INT64_MIN, INT64_MAX]`
- **THEN** it equals the Decimal round-half-even oracle result

#### Scenario: Negative ties round to even
- **WHEN** a negative value sits exactly on a rounding tie (e.g. `-500` micros)
- **THEN** the result rounds to the even mill, matching the oracle

#### Scenario: Non-integer input is rejected
- **WHEN** `micros_to_mills` receives a float or bool
- **THEN** a type error is raised (fail closed; no truncation or coercion)

### Requirement: Dollars conversion is confined to allowlisted kernels

No module under `src/quantflow/domain/**` or `src/quantflow/kernels/**` SHALL divide
by a dollars/money scale literal (`100`, `1000`, `1_000_000`) or a named
dollars-divisor constant, unless the enclosing function is on an explicit allowlist.
The allowlist SHALL start empty (fail closed); each converting kernel registers
deliberately in a follow-up.
Source: SPEC V1 §19.4.6 ("DOUBLE columns are analysis only"); constitution Sec 4;
conflicts Q14; 005c brief 2.7.

#### Scenario: Domain tree passes with an empty allowlist
- **WHEN** the AST scan runs over `src/quantflow/domain/**` and
  `src/quantflow/kernels/**` with no allowlist entries
- **THEN** it reports no violation (no domain code divides by those scales)

#### Scenario: Deliberately-bad fixture is flagged
- **WHEN** a fixture divides a value by `1_000_000` (or `100` / `1000`) outside an
  allowlisted function
- **THEN** the AST scan reports a violation for that expression

#### Scenario: Allowlisted formula-boundary kernel passes
- **WHEN** a kernel named on the allowlist performs the documented dollars conversion
- **THEN** the AST scan reports no violation for that function

#### Scenario: Integer unit conversion is not a dollars conversion
- **WHEN** `micros_to_mills` divides by the named `MICROS_PER_MILL` constant
- **THEN** the scan does not flag it (the guard targets dollars scale literals and
  named dollars divisors only, not domain unit-scale constants)
