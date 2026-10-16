# Tasks: 005a Domain hardening (review fixes for 005)

Test-class mapping (constitution Sec 11): golden (enum overlap, scan
fixtures, AST ban), boundary/units/sign (micros_to_mills params, token
matching), missing/malformed (None/str/bool input), duplicate/idempotency
(N/A — no state), port contract (SystemClock uses factory), migration (N/A —
no DB code), replay (N/A), property invariants (existing hypothesis tests
must stay green), no-future-leakage (scan extension), temp-paths-only
(tmp_path fixtures). Adapt brief snippets to existing test conventions;
run the full suite after each item; one checkpoint commit per green item
(operator-approved; tests first per AGENTS rule 12).

## 0. Open questions recorded (Part 3 — record only)

- [x] 0.1 Q1-Q16 appended to `openspec/conflicts-and-gaps.md` under
  "Gaps / Open questions" during propose (recommended option first;
  none implemented).
- [x] 0.2 Re-verify at final review: all 16 items present, zero Part 3 code
  changes landed (no constants/renames/bounds/AST additions from Q1-Q16).
  Done: Q1-Q16 all present (lines 33-48 of `openspec/conflicts-and-gaps.md`).
  `src/quantflow/domain/constants.py` untouched (`git status` clean for it);
  no constant renamed, no epoch/duration bound added, no Q12 random/uuid
  ban added. Only Q1's pre-approved default (factory + wrapper AST ban) was
  applied as 005a Part 1/2, which design.md §Open Questions classifies
  NON-BLOCKING with "factory+AST proceeds"; Q2-Q16 remain record-only.

## 1. money-units: validate micros_to_mills (1.1)

- [x] 1.1 Red tests in `tests/unit/domain/test_units.py`: parametrized
  rejection of `1500.9, 1500.0, True, "1500", None` (TypeError);
  `2**63` (UnitValueError); half-even table
  `(0,0),(499,0),(500,0),(501,1),(1499,1),(1500,2),(1501,2),(2500,2),
  (-500,0),(-501,-1),(-1500,-2),(-2500,-2)`.
- [x] 1.2 Fix `micros_to_mills` in `src/quantflow/domain/units.py`: route
  through `checked_int(value, field="micros")`, then
  `_round_half_even_div(checked, MICROS_PER_MILL)`.
- [x] 1.3 Full suite green; no pre-existing test changed; commit.

## 2. Ban direct unit-wrapper construction (1.2)

- [x] 2.1 New `tests/unit/test_direct_unit_construction.py` per brief: AST
  scan over `src/quantflow/**` with `ALLOWED_FILES = {domain/units.py,
  domain/time.py}`, `WRAPPER_NAMES = {Cents, Micros, Mills, EpochMs,
  DurationMs}`; deliberately-bad fixture (`Cents(1.5)`,
  `t.EpochMs(-1)` → 2 hits); docstring documents the `typing.cast` limit.
  Red: `adapters/clock.py:17` flagged.
  Done: new test file added; fixture asserts exactly 2 hits.
- [x] 2.2 Fix `src/quantflow/adapters/clock.py`: `SystemClock.now_ms` →
  `epoch_ms(time.time_ns() // 1_000_000, field="now_ms")`; adjust imports
  (`epoch_ms`; keep `EpochMs` import only if still referenced).
  Done: now_ms routes through `epoch_ms`; `EpochMs` import retained for the
  return annotation.
- [x] 2.3 AST scan green on all of `src/` (pre-audit: clock.py:17 was the
  only violation — if apply finds more, replace each with its factory);
  `tests/unit/test_clock.py` green; commit.
  Done: scan green on `src/`; test_clock.py green (157 tests passing).

## 3. domain-enums: pin vocabulary behaviour (1.3)

- [x] 3.1 Add the brief's tests to `tests/unit/domain/test_enums.py`:
  overlap exactly `{ACTIVE, RETRACTED, EXPIRED}`; grade disjoint from both
  states; BASIC grade-only (`ClusterState("BASIC")` /
  `EpisodeState("BASIC")` raise VocabularyError); shared literals never
  compare equal (values do); no cross-vocabulary coercion;
  `FORMING/UPGRADED/REVERSED` rejected by ClusterState;
  `ACTIVE/active/Basic/""` rejected by ClusterGrade.
  Done: added overlap/grade-disjoint/shared-literal/coercion/parametrized
  rejection tests; BASIC-grade-only and cross-type coercion already covered.
- [x] 3.2 All pass with `enums.py` unchanged; full suite green; commit.
  Done: test_enums.py 36 passed; full suite 167 passed; enums.py untouched.
  (Commit deferred: per-item commits not approved.)

## 4. epoch-clock: token-boundary naming rule (1.4)

- [x] 4.1 Red tests in `tests/unit/domain/test_time.py`: reject
  `message_ms, image_ms, package_ms, voltage_ms, elapsed_ms_wait`;
  duration `age_ms, quote_age_ms, latency_ms, feed_staleness_ms,
  call_duration_ms, response_ms`; epoch `created_at, bar_ts,
  event_epoch_ms, epoch_ms, epoch_ms_wait`.
  Done: red first — 4 lookalike names failed before the fix.
- [x] 4.2 Implement `_has_token_suffix` / `_is_epoch_name` in
  `src/quantflow/domain/time.py` per brief (suffix match = equal or
  `_`+suffix; epoch = suffix | `epoch_` prefix | `_epoch_` token).
  Done: helpers added; `field_name_kind` classifies via them.
- [x] 4.3 Existing naming tests still green (pre-audit: none rely on loose
  matching). If any fails: record it under Open questions in
  `openspec/conflicts-and-gaps.md` and STOP on this item — do not weaken
  the new tests. Commit if green.
  Done: no existing test failed; test_time.py 32 passed; full suite 183
  passed. (Commit deferred: per-item commits not approved.)

## 5. Wall-clock AST scan hardening (1.5)

- [x] 5.1 `tests/unit/test_wall_clock_scan.py`: extend
  `BANNED_CALL_NAMES` (+`time_ns, monotonic_ns, perf_counter,
  perf_counter_ns, process_time, process_time_ns, urandom`) and
  `BANNED_MODULES` (+`secrets`); insert relative-import branch
  (`node.level > 0`) BEFORE the existing `ImportFrom and node.module`
  branch; comment the accepted generic-name trade-off
  (`.time()`/`.today()` flag any such method — fail closed by design).
  Done: ban sets extended; relative-import branch inserted before the
  `node.module` branch; fail-closed trade-off commented.
- [x] 5.2 Add the three fixture tests (4 clock-call hits; 2 relative-import
  hits `from . import x` + `from ..adapters import clock`; 1 secrets hit).
  Done: all three fixture tests added and passing.
- [x] 5.3 Scan passes on current `domain/` and `kernels/` (pre-audit: no
  relative imports, no newly banned calls present — convert if found);
  full suite green; commit. `random`/`uuid` untouched (Q12).
  Done: scan green on domain//kernels; full suite 186 passed; random/uuid
  unchanged. (Commit deferred: per-item commits not approved.)

## 6. Spec deltas and housekeeping (Parts 2, 4)

- [x] 6.1 Propose wrote `specs/{money-units,epoch-clock,domain-enums}/
  spec.md` deltas — run `openspec validate --change 005a-domain-hardening`
  (or `openspec status`) and fix any schema findings.
  Done: `openspec validate 005a-domain-hardening --type change` = valid.
  Fixed 2 findings (MODIFIED blocks had dropped scenarios): restored
  "Rounding is integer-only and half-even" (money-units) and "Shared literal
  does not bridge types" (domain-enums). Pre-existing `config.yaml` rules
  YAML warnings are unrelated to this change (config untouched).
- [x] 6.2 `git pull --rebase` before pushing
  (`.github/workflows/repo-index.yml` commits `docs/REPO_INDEX.md` to
  master).
  Done: branch had no unique commits; fast-forwarded with
  `git pull --rebase --autostash origin master` to origin/master
  `04ba126` (plain `--rebase` refuses on the deliberately-dirty tree).
  Changes preserved/uncommitted; not pushed.
- [x] 6.3 Confirm `tests/unit/test_reference_bundle.py` covers the
  `docs/reference/CURRENT` symlink (run it; if symlink coverage is absent,
  record in conflicts-and-gaps Open questions — do not add untested code
  here).
  Done: covered — `test_real_bundle_hashes_verify` asserts
  `_check_current_symlink(BUNDLE_DIR) == []` (`BUNDLE_DIR = docs/reference/
  CURRENT`); CURRENT resolves to release-v2.0.5.1-v5.1.5.1; 13 passed.

## 7. Final verification

- [x] 7.1 Lint/format: `ruff check` + `ruff format --check` green
  (commands per `pyproject.toml` / `docs/STACK.md`).
  Done: scoped to `src tests` per pyproject.toml `src = ["src", "tests"]`:
  `uv run ruff check src tests` → "All checks passed!" (exit 0);
  `uv run ruff format --check src tests` → "36 files already formatted"
  (exit 0). `tools/`, `pocs/`, `.agents/skills-disabled/` deliberately
  excluded per operator decision (not in declared src roots).
- [x] 7.2 `mypy --strict` green on `src/quantflow/**`.
  Done: `uv run mypy --strict src/quantflow` → "Success: no issues found in
  27 source files" (exit 0).
- [x] 7.3 Full `pytest` suite green.
  Done: `uv run pytest -q` → "186 passed in 4.79s" (exit 0).
- [x] 7.4 Coverage ≥ 95% on `src/quantflow/domain/**`.
  Done: `uv run pytest -q --cov=quantflow.domain --cov-report=term-missing`
  → domain TOTAL **100%** (222 stmts, 0 miss; 12 branches, 0 partial).
  Per-file: constants.py 100%, enums.py 100%, errors.py 100%, time.py 100%,
  units.py 100%, __init__.py 100%. (Full-package
  `--cov=src/quantflow` TOTAL 61% — low only from unexercised MCP/CLI
  adapters, which are out of this change's scope.)
- [x] 7.5 `python3 scripts/check_constants.py` exit 0.
  Done: `python3 scripts/check_constants.py` → no output, exit 0.
- [x] 7.6 No changes under `openspec/changes/archive/`,
  `docs/reference/`, applied migrations, or
  `src/quantflow/domain/constants.py`; nothing touches `/data`; no secrets
  in logs.
  Done: `git status --porcelain` and `git diff --stat` for those four paths
  → empty, no modifications. `grep -rn "/data"` across all touched
  src/tests files → no matches. No logging/secrets in the touched domain
  code (`token` appears only as the token-boundary naming helper in
  time.py). Note: `opencode.json` is modified in the working tree but is an
  unrelated, pre-existing harness config tweak (`qf-build` steps 30→50) —
  not a 005a artifact and left untouched.
- [x] 7.7 Confirm every Part 3 item (Q1-Q16) is recorded in
  `openspec/conflicts-and-gaps.md` and none is implemented.
  Done: grep shows Q1-Q16 present once each (lines 33-48). Implemented: none
  (constants.py unchanged; no renames/bounds/extra bans). Q1's brief-approved
  default is Part 1/2 scope, not a Part 3 resolution.

## 8. Post-review MINOR fixes (from /qf-review)

- [x] 8.1 Fixture coverage gap: extend `test_scan_detects_additional_clock_calls`
  to call all seven newly banned names (`time_ns`, `monotonic_ns`,
  `perf_counter`, `perf_counter_ns`, `process_time`, `process_time_ns`,
  `urandom`); assertion `== 4` → `== 7`.
  Done: red first (fixture yielded 7, asserted 4 → failed), then green;
  `tests/unit/test_wall_clock_scan.py` 6 passed.
- [x] 8.2 Spec scenario for the scan extensions: add "Extended scan set and
  relative imports are rejected" to the `epoch-clock` delta under the
  "Injectable Clock port, as_of-only time" requirement (baseline requirement
  reproduced with its existing scenarios; the new scenario names the three
  proving tests in `tests/unit/test_wall_clock_scan.py`).
  Done: `openspec validate 005a-domain-hardening --type change` = valid.
- [x] 8.3 Tighten `test_scan_detects_deliberately_bad_fixture` assertion
  `>= 4` → `== 5` (fixture yields exactly 5 violations).
- [x] 8.4 ruff check + ruff format --check + `mypy --strict` + full pytest
  green on touched code (commit deferred: per-item commits not approved).
  Done: `ruff check src tests` all passed; `ruff format --check src tests` 36
  files already formatted; `mypy --strict src/quantflow` no issues in 27
  files; `pytest -q` 186 passed (all exit 0).
