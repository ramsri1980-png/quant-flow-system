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
