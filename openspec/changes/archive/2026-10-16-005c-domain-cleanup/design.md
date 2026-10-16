# Design — 005c domain cleanup

## Context

See proposal.md — Why. Current state that shapes the approach:

- `src/quantflow/domain/constants.py` is **generated** by `scripts/gen_constants.py`
  from ARCH V1 §AI.3 only (parser anchored on the last `^AI.3` header). The
  generator sets a `pending` flag when a line contains `[RECOMMENDED`, emitting
  `<NAME>_APPROVAL_PENDING = True` for block members, and renders an
  `approved(name)` accessor (005b Q6). Its module docstring and the pending-block
  comment hardcode "(C12 dealer/greeks)".
- `scripts/check_constants.py` verifies source-tree constants against AI.3
  (`scan_source_tree`) and byte-compares the committed module against a fresh
  regeneration (`verify_no_drift`). It does **not** verify the approved vs.
  approval-pending partition.
- `src/quantflow/domain/time.py` classifies field names with
  `EPOCH_NAME_SUFFIXES = ("_ts", "_at", "_epoch_ms", "_epoch_ns")`; `cooldown_until`
  therefore raises `FieldNameError`. `epoch_ms()`/`duration_ms()` both delegate to
  `units.checked_int`, which rejects `bool` with `TypeError`; the epoch range error
  message does not distinguish below-`MIN` from above-`MAX`.
- `tests/unit/test_wall_clock_scan.py` bans `"random"`, `"randint"`, `"randrange"`
  as **call names** (005b Q12), which flags injected-generator
  `rng.random()`/`rng.normal()` methods.
- ARCH V1 §AI.3 declares the lane latency cutoffs with unit "(ms)"; §AI.4–§AI.6 reuse
  the same lane tokens (`TACTICAL_2DTE`, `SHORT_TACTICAL`, `SWING`, `LONGER_HORIZON`)
  for different concepts (chase limits, lane labels, cache TTLs in seconds).
- There is no `kernels/` package yet.

Frozen bundle: `docs/reference/CURRENT` is a symlink to
`docs/reference/release-v2.0.5.1-v5.1.5.1`.

## Goals / Non-Goals

**Goals**

- One unit/shape suffix per constant; no fraction-valued `_PCT`; lane latency named
  with its unit; injected-generator randomness is not a wall-clock violation.
- Make the approve-vs-pending partition machine-checkable and its label sourced from
  ARCH rather than hardcoded.
- Close the `cooldown_until` regression and lock the naming rule against the frozen
  DDL with a conformance test.
- Close the 005b test gaps and add a fail-closed dollars-conversion guard.

**Non-Goals**

- Not migrating decision-path ratio thresholds to integer `_PPM` (see Open Questions).
- Not adding an `EpochNs` type (Q10 deferred to feature 020).
- Not moving `EPOCH_MS_MIN/MAX` or the suffix tuples out of `time.py`/`units.py`.
- Not editing ARCH Vol 2–4, ARCH Vol 3, SPEC Vol 4 §11, or the anti-detection
  surface (renames propagate only within ARCH Vol 1 and SPEC V1 §19.8.3).
- Not implementing the optional constitution §12 layout rule.

## Decisions

**D1 — three suffixes by shape, plus a percentile suffix.** `_PCT` = whole percent
points (int); `_PPM` = parts-per-million for decision-path thresholds; `_RATIO` =
dimensionless [0,1] (float). `_PCTL` is registered as a fourth, distinct shape for
integer percentile ranks (B1b). _Alternative considered:_ a blanket ppm/bps
conversion — rejected by Q2 (dimensionless ratios stay float). The **11** renames
(all in §AI.3):
`SPX_FALSE_CROSS_TOLERANCE_PCT`, `SPX_APPROACHING_PCT`,
`SPX_APPROACHING_RETREAT_PCT`, `SPX_CONFIRMATION_BUFFER_PCT`,
`GAMMA_FLIP_AGREEMENT_PCT`, `WALL_PROXIMITY_PCT`,
`ZERO_DTE_CONFIRMATION_BUFFER_PCT`, `ZERO_DTE_MEDIUM_MIN_COVERAGE_PCT`,
`STRUCTURE_STOP_MIN_PCT`, `PAPER_DEPTH_PARTICIPATION_PCT`,
`PAYOFF_KERNEL_MAX_INVALID_PCT` → `_RATIO`. `BUDGET_FLOW_ALERT_RESERVE_PCT` (60) and
`BUDGET_PREMARKET_BORROW_PCT` (20) stay `_PCT`. `DEALER_R_PCTL_MIN` (20),
`DEALER_R_PCTL_FULL` (80), `VANNA_THETA_PCTL` (90) stay `_PCTL`.

**D1 — scope.** Renames propagate within ARCH Vol 1, not just §AI.3, so the frozen spec
remains internally consistent. Same file, same SHA256SUMS entry.

**D2 — structural constants stay put.** `EPOCH_MS_MIN/MAX`, `DURATION_MS_MAX`,
`INT64_MIN/MAX`, `MICROS_PER_MILL`, and the `EPOCH_NAME_SUFFIXES` /
`DURATION_NAME_SUFFIXES` tuples are type invariants, not tunable config; they remain
in `time.py`/`units.py` and are already in `check_constants.STRUCTURAL_ALLOWLIST`.
The exemption from AGENTS rule 8 is documented in `AGENTS.md` and in the
`check_constants.py` docstring (doc-only; no code move).

**D3 — `_epoch_ns` deferred.** No `EpochNs` type in 005c (Q10 lands with feature 020).

**D4 — `_until` is an epoch suffix.** Add `"_until"` to `EPOCH_NAME_SUFFIXES`. ARCH
frozen scope permits the matching SPEC V1 §19.8.3 Rule 1 edit (append `*_until` to
the epoch pattern list); no other SPEC Vol 1 text changes.

**D5 — call-name ban corrected, module ban kept.** Remove `"random"`, `"randint"`,
`"randrange"` from `BANNED_CALL_NAMES`. `BANNED_MODULES` keeps `"random"`, so
`import random` and `from random import ...` still fail (the module ban covers
`random.randint`/`randrange`/`getrandbits` and `secrets`/`uuid`). `getrandbits` is
retained as a call name: it is not a numpy `Generator`/`RandomState` method, so it
cannot arise from an injected generator. _Alternative:_ allowlist injected-parameter
methods — rejected as fragile (the scan has no type information). Existing fixtures
`test_scan_detects_random_and_uuid_shapes` (expected count drops to 6: 3 module
imports + `getrandbits`/`uuid1`/`uuid4`) and
`test_scan_detects_random_and_uuid_from_imports` (still 3, via module ban) are updated
to match the new contract; no coverage is removed (module ban still proves each
shape).

**2.1 Q3 split.** Rename the 11 names in ARCH V1 §AI.3, regenerate via
`scripts/gen_constants.py`, update imports/tests. `python3 scripts/gen_constants.py`
is the only writer of `domain/constants.py` (never hand-edit).

**2.2 Q4 lane rename + unit-suffix lint.** Rename the four lane latency constants in
ARCH §AI.3 to `LANE_LATENCY_CUTOFF_MS_2DTE` / `_SHORT_TACTICAL` / `_SWING` /
`_LONGER_HORIZON` (values preserved). New `tests/unit/domain/test_unit_suffix_lint.py`
walks the generated module's module-level UPPER_SNAKE assignments: a name passes if it
ends in a registered suffix (`_MS _S _DAYS _D _USD _CENTS _MICROS _MILLS _MICROCENTS
_BPS _MB _PCT _PPM _RATIO _FRAC _PCTL _MULT _COUNT _SNAPS _H _WEIGHT`), or is in an
explicit `{name: reason}` allowlist. _Note:_ the rule is **endswith**, so constants
whose unit sits mid-name (e.g. `DEALER_R_PCTL_MIN`, `ZERO_DTE_FLOW_WEIGHT_DELTA`,
`TRACE_FLAG_COUNT_ALERT`, `MIN_VEGA`, `LEVEL_THETA`) go on the allowlist with a
reason. The same lint asserts no `_PCT` value is strictly between 0 and 1
(fraction-`_PCT` guard). A `tmp_path` fixture with a bad constant proves the lint
fails.

**2.3 Q5 generator + approval invariant.** B3: pending is the ARCH §AI.3
`[RECOMMENDED ...]` block; `MIN_VEGA` (line 606, above the marker) is approved.
`gen_constants.py` adds a separate `parse_pending_label` (the parser
`parse_ai3_constants` keeps returning the entry list, so existing callers are
unaffected) and uses the label in the module docstring and pending-block comment (drop
the hardcoded "C12 dealer/greeks"). `check_constants.py` gains
`verify_approval_companions`: for each
parsed constant, require either a plain value assignment (approved) or a
`<NAME>_APPROVAL_PENDING = True` assignment (pending), and reject a constant that is
neither; exit non-zero with a clear message. Regenerate the module.

**2.4 cooldown_until + DDL conformance.** Add `"_until"` to `EPOCH_NAME_SUFFIXES`
(and `*_until` to SPEC V1 §19.8.3 Rule 1); `_is_epoch_name` already uses
`endswith(tuple)`. New `tests/unit/domain/test_ddl_column_conformance.py` reads SPEC V2
§19.2 only and extracts `name TYPE` pairs; the brief's regex is line-leading only, so
the test anchors on start-of-line **or** a preceding comma to catch the second column
on comma-joined lines (e.g. `cooldown_until INTEGER, rearmed_at INTEGER`).

The conformance test classifies only DDL column names that contain a time token;
columns with no time token are out of scope by construction. This mirrors how
`field_name_kind` is used in practice — on fields whose names declare a time semantic.
(Operator ruling 2026-10-16: the frozen §19.2 holds 528 non-time columns, so a literal
non-time allowlist is the wrong shape and is not maintained.) The token match is
boundary-anchored, not a substring match — `max_attempts` and `spot_at_entry_micros`
merely contain `_at` and declare no time semantic. `*_date` columns carry their own
convention (SPEC V1 §19.8.1, TEXT in ISO 8601) and are asserted TEXT, not
epoch/duration. A positive list of known §19.2 time columns (`cooldown_until`,
`rearmed_at`, `created_at`, `updated_at`, `applied_at`, `quote_ts`, `entry_ts`,
`provider_ts`, `staleness_ms`, …) pins regressions even if the token filter drifts.

**2.5 005b regression.** See D5.

**2.6 Test gaps.** `units.checked_int` already raises `TypeError` on `bool`, so
`test_epoch_ms_rejects_bool` / `test_duration_ms_rejects_bool` assert `TypeError`
(no new guard needed). `test_units.py` gains a Hypothesis oracle:
`micros_to_mills(v) == int((Decimal(v)/1000).quantize(Decimal(1),
rounding=ROUND_HALF_EVEN))` over `[INT64_MIN, INT64_MAX]`. `time.epoch_ms()` splits
its range check into below-`MIN` and above-`MAX` branches with distinct messages; the
two `match=` assertions in `test_time.py` are updated.

**2.7 Q14 dollars AST guard.** New `tests/unit/domain/test_dollars_conversion_scan.py`
AST-scans `domain/**` and `kernels/**` for `BinOp(Div)` whose divisor is the literal
`100`, `1000`, `1_000_000` or a named dollars divisor (`MICROS_PER_DOLLAR`,
`MILLS_PER_DOLLAR`, `CENTS_PER_DOLLAR`). The enclosing-function allowlist starts
**empty** (fail closed) and legitimate kernels register in a follow-up. `kernels/` does
not exist yet and `micros_to_mills` does not divide directly — it delegates to
`_round_half_even_div` (which uses `divmod`) — so `domain/**` contains no true-division
`BinOp` today and the real-tree scan passes trivially; detection is proven by positive
fixtures (a dollars literal and a named dollars divisor).

**2.8 AGENTS.md corrections.** Doc-only: reword the disjoint-vocabulary line (Q2:
`cluster_state`/`episode_state` share ACTIVE/RETRACTED/EXPIRED per SPEC V2 §19.2;
BASIC is a grade only); add the narrowed rule-2 float interpretation and the `_PPM`
rule for state-gating thresholds; add the Q7 structural-constant exemption. AGENTS.md
is kept ≤ 40 lines.

## Reuse

Reused, no new modules in `src/`: `quantflow.domain.constants` (generated),
`quantflow.domain.time` (`field_name_kind`, `EPOCH_NAME_SUFFIXES`),
`quantflow.domain.units` (`checked_int`, `micros_to_mills`, `MICROS_PER_MILL`),
`quantflow.domain.errors`. Reused scripts: `scripts/gen_constants.py`,
`scripts/check_constants.py`. New test modules only (no new source module needs
justification): `tests/unit/domain/test_unit_suffix_lint.py`,
`tests/unit/domain/test_ddl_column_conformance.py`,
`tests/unit/domain/test_dollars_conversion_scan.py`; extended
`tests/unit/domain/test_units.py`, `tests/unit/domain/test_time.py`,
`tests/unit/test_wall_clock_scan.py`.

## Risks / Trade-offs

- [Manual ARCH §AI.3 edits could drift from the generated module] → regeneration plus
  `check_constants.py` drift check in CI/tests catches it.
- [The `endswith` suffix lint needs a large allowlist and can look arbitrary] → every
  entry carries a written reason; additions are one-at-a-time and reviewed.
- [DDL conformance could hide a real time-column bug] → the test is scope-inverted:
  only names declaring a time token are classified, and every such name must classify
  as epoch/duration (there is no non-time allowlist to hide behind); the
  `cooldown_until`/`rearmed_at` scenarios and a pinned positive list cover regressions.
- [Rename is breaking for the generated module's importers] → all importers are
  updated in the same change; no external consumers exist yet (single-operator
  research repo, no published API).
- [Empty dollars allowlist may flag a future kernel] → intended fail-closed
  behaviour; the kernel registers itself with a reason.

## Migration Plan

Forward-only; **no** SQLite/DuckDB migration is touched (no schema change). Order:
ARCH §AI.3 + SPEC V1 §19.8.3 doc edits → `gen_constants.py`/`check_constants.py` →
regenerate `constants.py` → `time.py` → tests. Rollback = revert the change's commits
(all code plus the two frozen-doc section edits); the anti-detection hash gate below
does not cover ARCH Vol 1 / SPEC Vol 1.

## Frozen-bundle scope and anti-detection gate

Allowed frozen-bundle edits: ARCH V1 (the 11 `*_PCT`→`*_RATIO` references propagated
across the whole volume, D1 — scope, plus the §AI.3 lane-constant rename) and SPEC V1
§19.8.3 (`*_until` added to Rule 1), plus the `SHA256SUMS` manifest entry for those two
files (operator-approved 2026-10-16). ARCH Vol 2–4 and every other SPEC file are out of
scope: revert and report.

**B7 drift note.** The lane tokens `TACTICAL_2DTE`, `SHORT_TACTICAL`, `SWING`,
`LONGER_HORIZON` also appear in ARCH V1 §AI.1 (line 594 lane key), §AI.4 (chase limits),
§AI.5 (DTE lane labels / `calibrator_scope`), and §AI.6 (cache TTLs, seconds). Those are
**DTE-lane identifiers, not the §AI.3 latency constant**, so they are intentionally left
unchanged (operator decision 2026-10-16): renaming them would make statements such as
`LANE_LATENCY_CUTOFF_MS_2DTE   2 DTE (own rules)` false and would desync the lane
vocabulary from ARCH Vol 4 / SPEC. The §AI.3 rename decouples the latency constant name
from the lane name; only the §AI.3 latency constants are generated. The 11 `*_PCT`→
`*_RATIO` references, by contrast, all denote the renamed constant and were propagated
throughout ARCH Vol 1 (lines 30, 43, 481, 484, 842–846). ARCH Vol 2–4 are not touched.

Pre-commit gate (run before committing anything):
`sha256sum docs/reference/CURRENT/ARCH_v5.1.5.1_Vol3_Capture_AntiDetection.md` must
equal `2d7a90e533196af61745bc4efd3259b7b64b519b8ec78662392b50a911285e23`; abort and
report otherwise.

## Open Questions

- **NON-BLOCKING — `_PPM` migration (D1).** Decision-path thresholds that gate a
  state (e.g. `ZERO_DTE_MEDIUM_FLOW_STRENGTH_MIN`, `ZERO_DTE_HIGH_CONFLUENCE_MIN`,
  `DEALER_COVERAGE_MIN`, `MIN_VOL_INDEX_COVERAGE`) remain float ratios in 005c. The
  migration to integer `_PPM` needs an ARCH amendment and is a follow-up.
- **NON-BLOCKING — unit-suffix allowlist contents.** The exact allowlist entries are
  enumerated when the lint first runs on the regenerated module; every entry carries a
  reason. B4's set is the starting point.
- **RESOLVED (2026-10-16) — DDL non-time allowlist breadth.** SPEC V2 §19.2 holds 528
  non-time columns, so a literal non-time allowlist was the wrong shape. Operator
  ruling: the conformance test classifies only column names that declare a time token;
  columns with no time token are out of scope by construction and no allowlist is
  maintained (design §2.4, epoch-clock delta).
- **NON-BLOCKING — Part 3 conflicts-log append deferred.** The brief's Part 3 asks to
  append the "Resolved (2026-10-16)" entries to `openspec/conflicts-and-gaps.md`, but
  this PROPOSE phase is restricted to the change's own artifacts. The exact entries are
  captured as an apply-phase task (tasks group 9) rather than written now.

No BLOCKING open questions remain (B1, B1b, B3, B4, B7 answered 2026-10-16).
