# Spec Delta: domain-enums

## Purpose

Disjoint enum vocabularies for the 0DTE cluster state machine: cluster_grade,
cluster_state, and episode_state are three distinct types whose literals may
overlap in text but never in type. BASIC exists only in cluster_grade.

## MODIFIED Requirements

### Requirement: Three disjoint vocabularies as distinct types

The system SHALL define cluster_grade, cluster_state, and episode_state as
three distinct enum types. Vocabularies are disjoint as types: members SHALL
never compare equal across vocabularies and SHALL never coerce across them.
cluster_grade shares no literal with the other two. cluster_state and
episode_state share exactly `ACTIVE`, `RETRACTED`, `EXPIRED` (SPEC V2
Sec 19.2); `BASIC` is a grade only.
Source: SPEC V2 Sec 19.2 (zero_dte_cluster_current CHECK constraints:
cluster_grade IN ('BASIC','MEDIUM_CONFLUENCE','HIGH_CONFLUENCE');
cluster_state IN ('ACTIVE','MIXED','BULLISH_REVERSAL','BEARISH_REVERSAL',
'RETRACTED','EXPIRED'); episode_state IN ('FORMING','ACTIVE','UPGRADED',
'REVERSED','RETRACTED','EXPIRED')); constitution Sec 4 vocabularies.

#### Scenario: Overlap is exactly the documented shared literals

- **WHEN** the cluster_state and episode_state member sets are intersected
- **THEN** the intersection is exactly `{"ACTIVE", "RETRACTED", "EXPIRED"}`
  (no more, no less; golden test against SPEC V2 Sec 19.2)

#### Scenario: Grade is disjoint from both state vocabularies

- **WHEN** cluster_grade values are intersected with cluster_state values and
  with episode_state values
- **THEN** both intersections are empty

#### Scenario: Shared literals never compare equal across types

- **WHEN** `ClusterState.ACTIVE` and `EpisodeState.ACTIVE` are compared
- **THEN** they are not equal as members, while their underlying string
  values match (documents the intentional textual overlap)

#### Scenario: Members do not coerce across vocabularies

- **WHEN** a cluster_state member is used to construct an episode_state (or
  vice versa)
- **THEN** construction fails with a vocabulary error (no coercion)

#### Scenario: Shared literal does not bridge types

- **WHEN** a cluster_state value `RETRACTED` is passed where an episode_state
  is required
- **THEN** the call is rejected by the type system (and a runtime attempt to
  construct episode_state from a cluster_state enum instance fails)

#### Scenario: Episode-only literals are rejected by cluster_state

- **WHEN** `FORMING`, `UPGRADED`, or `REVERSED` is used to construct a
  cluster_state
- **THEN** construction fails with a vocabulary error

#### Scenario: Literal sets match the DDL exactly

- **WHEN** the enum member sets are compared against SPEC V2 Sec 19.2 CHECK
  constraints
- **THEN** each set matches exactly (no added, missing, or renamed members;
  golden test)
