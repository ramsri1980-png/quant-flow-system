# Spec Delta — money-units

## ADDED Requirements

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
