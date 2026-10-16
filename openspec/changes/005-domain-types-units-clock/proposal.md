# Proposal: 005 Domain types, units, clock

## Why

Epic E0. Every downstream feature (010+ migrations/repositories, 020+ capture,
030+ kernels) stores money as integer minor units, timestamps as UTC epoch ms,
reads time only through as_of, and references named constants from one home.
Without canonical domain types and a clock port in `src/quantflow/domain/`,
each later feature would invent its own representations, violating SPEC V1
Sec 1.4.13/1.4.33 and constitution Sec 4-5.

Feature brief: `openspec/prompts/005-domain-types-units-clock.md` (Epic E0,
depends: none).

Source sections cited (verified in `docs/reference/CURRENT` = v2.0.5.1/v5.1.5.1):
- SPEC V1 Sec 1.4 (principles), Sec 1.4.33-1.4.35, Sec 2.9.4 (determinism),
  Sec 19.4 (money and units), Sec 19.8 (date/time conventions)
- SPEC V2 Sec 19.2 (zero_dte_cluster_current enum CHECK constraints),
  Sec 19.4.4 (column types), Sec 19.6 invariant W, invariant AB
- ARCH V1 Sec AI.3 (canonical home of named constants)

## What Changes

- Typed integer wrappers for `_cents` (option prices), `_micros`
  (underlying/index), `_mills` (strikes/levels). Float rejected on the decision
  path; dollars only at formula boundaries. No DB code.
- UTC epoch-ms integer type; duration naming rule `*_ts/*_at/*_epoch_*` vs
  bounded `*latency_ms/*staleness_ms/*age_ms/*duration_ms/*response_ms`;
  ET display only (formatting concern, not storage).
- Injectable Clock port (as_of); no wall-clock reads in domain/kernels
  (AST-enforced, same pattern as SPEC V1 Sec 2.9.4.8).
- Three disjoint enum vocabularies as distinct types: cluster_grade,
  cluster_state, episode_state (BASIC is a grade only).
- Named-constants module generated/checked from ARCH V1 Sec AI.3; constants
  referenced by name, defined once.
- Reference-bundle check: SHA256SUMS manifest under
  `docs/reference/release-v2.0.5.1-v5.1.5.1/` verified by test (bundle frozen,
  runbook Task 5 done; C1 closed 2026-10-15).

## Capabilities

### New Capabilities

- `money-units`: integer unit-scaled value types for option/underlying/level
  prices; float rejection on the decision path; dollars conversion only at
  formula boundaries.
- `epoch-clock`: UTC epoch-ms time type, epoch/duration naming rule, ET
  display-only rule, and the injectable Clock port / as_of-only discipline for
  domain and kernels.
- `domain-enums`: disjoint cluster_grade / cluster_state / episode_state
  vocabularies with type-level separation despite overlapping literals.
- `repo-bootstrap`: named-constants module checked against ARCH V1 Sec AI.3
  (defined once, referenced by name) and frozen reference-bundle hash
  verification.

### Modified Capabilities

(none -- `openspec/specs/` is empty; all four capabilities are new.)

## Impact

- Code: `src/quantflow/domain/**` (units, time, enums, constants),
  `src/quantflow/ports/**` (Clock port), `scripts/` (constants check),
  `tests/unit|property|failure/**`.
- No migrations touched; no DB, provider, or kernel code (out of scope per
  brief). No changes to `~/.config/opencode` or system config.
- Dependencies: none new (typing only; pytest/hypothesis already present).
