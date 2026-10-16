# Proposal: 005a Domain hardening (review fixes for 005)

## Why

The archived change 005 shipped domain types/units/clock, but its own review
found five fail-closed gaps: `micros_to_mills` truncates floats silently,
`typing.NewType` wrappers are runtime no-ops (direct `Cents(1.5)` /
`SystemClock.now_ms` bypass validation), the naming rule's bare `endswith`
misclassifies `message_ms` as a duration, the enum-disjointness wording
contradicts SPEC V2 Sec 19.2 (cluster_state and episode_state legitimately
share literals), and the wall-clock AST scan is missing several banned calls.
Epic E0; violations of constitution Sec 3 (fail closed) and Sec 4 (units).

Feature brief: `openspec/prompts/005a-domain-hardening.md`
(Parts 1, 2, 4; Part 3 recorded only — see Impact).

Source sections cited (via existing specs, verified in `docs/reference/CURRENT` = v2.0.5.1/v5.1.5.1):
- SPEC V1 Sec 19.4 (money and units), Sec 19.8.3 Rule 1-2 (date/time naming)
- SPEC V1 Sec 2.9.4.8 (AST lint pattern), SPEC V2 Sec 19.2 (enum CHECK constraints)
- constitution Sec 3 (fail closed), Sec 4 (units/vocabularies)
- 005 review of `src/quantflow/domain/{units,time,enums}.py`,
  `src/quantflow/adapters/clock.py`, `tests/unit/test_wall_clock_scan.py`

## What Changes

- 1.1 `micros_to_mills` validates input via `checked_int` (TypeError on
  non-int/bool, UnitValueError out-of-signed-64-bit); half-even boundary
  tests added.
- 1.2 Factory-only construction of unit wrappers: new AST test bans direct
  `Cents/Micros/Mills/EpochMs/DurationMs(...)` outside `domain/units.py`
  and `domain/time.py`; `SystemClock.now_ms` switches to the `epoch_ms()`
  factory. NewType stays (brief default; Q1 alternative recorded).
- 1.3 Enum vocabulary behaviour pinned by tests only (`enums.py` unchanged):
  cluster_state ∩ episode_state == exactly {ACTIVE, RETRACTED, EXPIRED};
  cluster_grade disjoint from both; BASIC grade-only; shared literals never
  compare equal; no cross-vocabulary coercion.
- 1.4 Token-boundary matching in `field_name_kind`: `message_ms`,
  `image_ms`, `package_ms` rejected as ambiguous; `quote_age_ms` is a
  duration; epoch detection uses suffix/`epoch_`-prefix/`_epoch_` tokens.
- 1.5 Wall-clock AST scan hardened: banned call names extended
  (`time_ns`, `monotonic_ns`, `perf_counter`, `perf_counter_ns`,
  `process_time`, `process_time_ns`, `urandom`), `secrets` module banned,
  relative imports banned in `domain/**` and `kernels/**`; fixture tests
  prove each ban. `random`/`uuid` untouched (Q12).
- Part 2: spec deltas for `money-units` (factory-only construction;
  rounding split into domain-integer rule and presentation-boundary rule),
  `epoch-clock` (underscore-delimited token semantics), `domain-enums`
  (disjoint-as-types definition replacing the false "same literal fails"
  scenario).
- Part 3 (record only): Q1-Q16 appended to
  `openspec/conflicts-and-gaps.md` under Gaps/Open questions; none
  implemented here — resolution belongs to 005b or the consuming feature.
- Part 4: housekeeping — `git pull --rebase` before push
  (`.github/workflows/repo-index.yml` commits `docs/REPO_INDEX.md` to
  master); confirm `tests/unit/test_reference_bundle.py` covers the
  `docs/reference/CURRENT` symlink.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `money-units`: construction only through validating factories (AST
  enforced); conversion input validation; rounding rules split into two
  explicit rules.
- `epoch-clock`: naming-rule token semantics for `*` patterns + rejection/
  duration scenarios for lookalike names.
- `domain-enums`: disjointness defined as type behaviour (no cross-equality,
  no coercion) with the exact documented overlap `{ACTIVE, RETRACTED,
  EXPIRED}`.

## Impact

- Code: `src/quantflow/domain/units.py`, `src/quantflow/domain/time.py`,
  `src/quantflow/adapters/clock.py`; tests:
  `tests/unit/domain/test_units.py`, `tests/unit/domain/test_time.py`,
  `tests/unit/domain/test_enums.py`, `tests/unit/test_wall_clock_scan.py`,
  new `tests/unit/test_direct_unit_construction.py`.
- Untouched: `domain/enums.py`, `domain/constants.py` (generated),
  `openspec/changes/archive/2026-10-16-005-domain-types-units-clock/`,
  `docs/reference/**`, applied migrations, `/data`. No DB code, no new
  dependencies.
- Process note: artifacts hand-written per operator instruction
  2026-10-16 (this session had no openspec CLI); run `openspec validate` /
  `openspec status --change 005a-domain-hardening` to confirm schema
  compliance before apply.
