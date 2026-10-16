# Spec Delta: money-units

## Purpose

Canonical integer representation of money and price values for the decision
path: option prices in cents, underlying/index prices in micros, strikes and
levels in mills. Floats are rejected on the decision path; dollars appear only
at formula boundaries.

## MODIFIED Requirements

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
