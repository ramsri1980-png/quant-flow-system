# Spec Delta: domain-enums

## Purpose
Disjoint enum vocabularies for the 0DTE cluster state machine: cluster_grade,
cluster_state, and episode_state are three distinct types whose literals may
overlap in text but never in type. BASIC exists only in cluster_grade.

## ADDED Requirements

### Requirement: Three disjoint vocabularies as distinct types
The system SHALL define cluster_grade, cluster_state, and episode_state as
three distinct enum types. A value of one type SHALL NOT be assignable,
comparable, or accepted where another is required, even when the underlying
string literal is identical (e.g. `RETRACTED` exists in both cluster_state
and episode_state; `ACTIVE` in both cluster_state and episode_state).
Source: SPEC V2 Sec 19.2 (zero_dte_cluster_current CHECK constraints:
cluster_grade IN ('BASIC','MEDIUM_CONFLUENCE','HIGH_CONFLUENCE');
cluster_state IN ('ACTIVE','MIXED','BULLISH_REVERSAL','BEARISH_REVERSAL',
'RETRACTED','EXPIRED'); episode_state IN ('FORMING','ACTIVE','UPGRADED',
'REVERSED','RETRACTED','EXPIRED')); constitution Sec 4 vocabularies.

#### Scenario: Shared literal does not bridge types
- **WHEN** a cluster_state value `RETRACTED` is passed where an episode_state
  is required
- **THEN** the call is rejected by the type system (and a runtime attempt to
  construct episode_state from a cluster_state enum instance fails)

#### Scenario: Literal sets match the DDL exactly
- **WHEN** the enum member sets are compared against SPEC V2 Sec 19.2 CHECK
  constraints
- **THEN** each set matches exactly (no added, missing, or renamed members;
  golden test)

### Requirement: BASIC is a grade only
The literal `BASIC` SHALL exist only in cluster_grade. It SHALL NOT appear in
cluster_state or episode_state, and BASIC-graded clusters SHALL NOT be
treated as directional alerts (BASIC_SHADOW is a snapshot type, not a state
vocabulary member).
Source: SPEC V2 Sec 19.2 (CHECK constraints; snapshot_type 'BASIC_SHADOW'
requires alert_grade='BASIC'); SPEC V2 Sec 19.6 invariant AB; SPEC V1 Sec
1.4.35.

#### Scenario: BASIC as a state is rejected
- **WHEN** `BASIC` is used as a cluster_state or episode_state value
- **THEN** construction fails (not a member of those vocabularies)

#### Scenario: Grade never implies probability
- **WHEN** a cluster_grade value is consumed
- **THEN** it is treated as an evidence grade, never as a numeric probability
  (no implicit conversion to float)

### Requirement: Enum literals are closed sets
Each vocabulary SHALL be a closed set: an unlisted literal (including
case-variants, e.g. 'basic' or 'High_Confluence') SHALL be rejected, never
silently coerced.
Source: SPEC V2 Sec 19.2 CHECK constraints (closed IN lists); constitution
Sec 3 (fail closed).

#### Scenario: Unknown or case-mangled literal is rejected
- **WHEN** a string outside the exact member list (wrong case, extra
  whitespace, unknown token) is used to construct an enum value
- **THEN** construction fails explicitly
