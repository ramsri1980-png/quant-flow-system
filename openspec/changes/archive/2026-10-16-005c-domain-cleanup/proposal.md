# Proposal

## Why

Brief `openspec/prompts/005c-domain-cleanup.md` (Epic E0 setup; depends on 005b, merged)
closes the domain-cleanup items 005a left open and the 005b review follow-ups. Two are
live correctness bugs: the frozen DDL epoch column `cooldown_until` raises
`FieldNameError` from `field_name_kind`, and 005b's `BANNED_CALL_NAMES` addition of
`random`/`randint`/`randrange` forbids the as_of-seeded `rng.random()` pattern that
Q12 explicitly permits. The rest are hygiene: `_PCT` mixes whole-percent and
fraction semantics, the lane-latency constants carry no unit, the generator mislabels
its approval-pending set, and two unit/name test gaps remain.

## What Changes

- **BREAKING** (generated module) Rename the 11 fraction-valued `*_PCT` constants to
  `*_RATIO`; they stay float. Whole percent points keep `_PCT` (integer).
- Rename the lane-latency constants to `LANE_LATENCY_CUTOFF_MS_*`; values unchanged
  (3000/5000/10000/30000). ARCH V1 §AI.3 already labels them "(ms)".
- Register the suffix vocabulary `_MS _S _DAYS _D _USD _CENTS _MICROS _MILLS
  _MICROCENTS _BPS _MB _PCT _PPM _RATIO _FRAC _PCTL _MULT _COUNT _SNAPS _H _WEIGHT`
  and add an AST unit-suffix lint over the generated module.
- Make the approval-pending set exhaustive and derive its label from the ARCH V1
  §AI.3 `[RECOMMENDED ...]` marker; `check_constants.py` fails on an orphan constant.
- Add `_until` to the epoch name suffixes and add a frozen-DDL column conformance
  test over SPEC V2 §19.2.
- 005b regression fix: remove `random`, `randint`, `randrange` from the banned call
  names; keep the module bans.
- Add a `micros_to_mills` Decimal-oracle hypothesis test and bool-boundary tests;
  split the epoch range error messages so below-`MIN` and above-`MAX` differ.
- Add a fail-closed AST guard against dollars conversion (`/100`, `/1000`,
  `/1_000_000` or named dollars divisors) in `domain/**` and `kernels/**`, with an
  empty starting allowlist.
- Documentation only: AGENTS.md Q2 narrow-float rule, Q7 structural-constant
  exemption, and the disjoint-vocabulary rewording.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `domain-constants`: unit-suffix policy and registered suffixes, the `_PCT`→`_RATIO`
  split, the lane-latency renames, and the exhaustive approval-pending invariant.
- `epoch-clock`: `*_until` becomes an epoch suffix, frozen-DDL column conformance,
  and the corrected banned-call-name set (injected generators allowed).
- `money-units`: an exact round-half-even conversion contract and a fail-closed
  dollars-conversion AST guard.

## Impact

Affected code: `scripts/gen_constants.py`, `scripts/check_constants.py`,
`src/quantflow/domain/constants.py` (generated), `src/quantflow/domain/time.py`;
tests under `tests/unit/domain/**` and `tests/unit/test_wall_clock_scan.py`;
doc-only `AGENTS.md`. Frozen-bundle scope: ARCH V1 (renames propagate throughout the volume, not just §AI.3) (constant renames and
the lane unit label) and SPEC V1 §19.8.3 (add `*_until`) change. No dependency or
schema-migration changes.

Out of scope, exactly as the brief states: no change to ARCH Vol 3, SPEC Vol 4 §11,
or the anti-detection surface; no new `EpochNs` type (Q10 deferred); no conversion of
decision-path floats to `_PPM` (noted as a design follow-up only); no move of
`EPOCH_MS_MIN/MAX` to `constants.py`; the optional constitution §12 layout rule is
not part of this change; the archived 005 / 005a / 005b changes are not edited.
