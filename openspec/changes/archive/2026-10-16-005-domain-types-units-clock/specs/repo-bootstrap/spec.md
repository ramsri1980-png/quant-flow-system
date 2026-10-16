# Spec Delta: repo-bootstrap

## Purpose
Foundational repo guarantees for E0: every UPPER_SNAKE_CASE named constant is
defined exactly once and sourced from ARCH V1 Sec AI.3, and the frozen
reference bundle under docs/reference/CURRENT is hash-verified.

## ADDED Requirements

### Requirement: Named constants defined once, sourced from AI.3
Every named constant used in code SHALL be defined exactly once in a single
constants module whose values are generated from and checked against ARCH V1
Sec AI.3 of the frozen bundle. Code SHALL reference constants by name; a
duplicate definition of the same constant name anywhere else in
`src/quantflow/**` SHALL fail a lint/check test. UPPER_SNAKE_CASE tokens
that do not resolve to the constants module SHALL fail the check.
Source: SPEC V1 Sec 1.4.33 ("Named numeric constants are defined exactly once
in ARCH v5.1.5.1 Vol 1 Sec AI.3 and referenced by name elsewhere... enforced
by a document-level lint that scans for UPPER_SNAKE_CASE tokens"); ARCH V1
Sec AI.3 ("canonical home of every UPPER_SNAKE_CASE named constant").

#### Scenario: Drifted constant value fails the check
- **WHEN** a value in the generated constants module differs from ARCH V1 Sec
  AI.3 in the frozen bundle
- **THEN** the check test fails naming the constant

#### Scenario: Duplicated constant fails the check
- **WHEN** an UPPER_SNAKE_CASE constant is redefined in a module under
  `src/quantflow/**` outside the constants module
- **THEN** the duplication check fails

#### Scenario: AI.3 RECOMMENDED values are not silently adopted
- **WHEN** constants marked in AI.3 as "[RECOMMENDED values; running the
  patch script = approval]" (C12 dealer/greeks set) are generated
- **THEN** they carry an explicit approval-pending marker and their use in
  decision features remains gated until operator approval (shadow-only until
  outcomes justify, per constitution Sec 7)

### Requirement: Reference bundle hash-verified
A repository check SHALL verify that every file in
`docs/reference/CURRENT` (symlink to the frozen release directory) matches
its SHA256SUMS entry and that the bundle contains the expected frozen file
set. Mismatch, missing file, or broken symlink SHALL fail the check.
Source: runbook Task 5 (freeze: 11 files, SHA256SUMS verified, CURRENT
symlink); constitution Sec 2 (docs/reference/CURRENT is the truth bundle).

#### Scenario: Tampered bundle file fails
- **WHEN** a file under `docs/reference/CURRENT/` no longer matches its
  SHA256SUMS hash
- **THEN** the check fails naming the file

#### Scenario: Broken CURRENT symlink fails
- **WHEN** `docs/reference/CURRENT` does not resolve to the frozen release
  directory
- **THEN** the check fails
