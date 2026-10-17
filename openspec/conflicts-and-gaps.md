# Conflicts and gaps found in the design bundle (review before the affected feature)

Rule: the doc with authority wins (constitution §2). Items are BLOCKING for the listed features until resolved.

## Conflicts
| ID | Where | Problem | Suggested resolution | Blocks |
|---|---|---|---|---|
| C1 | Runbook Task 5 vs files | Runbook freezes v2.0.5/v5.1.5 (10 files). Bundle is v2.0.5.1/v5.1.5.1 (11 files incl. SPEC V7). Filename `Vol3_Capture_Antidetection` vs `Vol3_Capture_AntiDetection`. | Freeze v2.0.5.1/v5.1.5.1; dir `release-v2.0.5.1-v5.1.5.1`; 11 files; update runbook. | 005 |
| C2 | Runbook Session 3 | Uses SpecKit (`/speckit-*`, `.specify/`); you now use OpenSpec. | Replace with OpenSpec flow in AGENTS.md; constitution → config.yaml + this folder. | all |
| C3 | SPEC V6 F.10 vs F.3 | F.10 Phase B says "300 pooled usable outcomes"; F.3 requires per-scope N_scope ≥ max(300, 20p), 75/75 classes, no pooling. | F.3 wins (per-scope). | 084 |
| C4 | SPEC V5 O.7.4 vs O.13.5 | O.7.4 ladder has STEP2_CHANNEL 1 h after STEP1; tests 18b/20a say no further re-emit while an unacked descendant exists and exactly one re-emit in 24 h. | Decide ladder vs one-shot; then fix tests. | 071 |
| C5 | SPEC V3 §17.5 vs SPEC V2 §19.3 | §17.5 prescribes two partial unique indexes on signal_outcomes; DDL uses PK incl. outcome_scope_id (DuckDB has no partial indexes). | DDL wins; edit §17.5. | 041 |
| C6 | SPEC V4 §20.72 | Points to §20.67, inside the reserved range 20.2–20.70. | Remove or define. | 072 |
| C7 | SPEC V2 §19.6 vs ARCH V4/V1 | Invariant labels "AH" and "AI" collide with ARCH V4 §AH and ARCH V1 §AI. | Always cite doc-qualified; rename invariants. | all (cosmetic) |
| C8 | SPEC V1 §19.4.4 vs SPEC V2 §19.4.4 | V1: all unit columns BIGINT. V2: SQLite INTEGER(64), DuckDB `_cents/_mills` "INTEGER or BIGINT as declared"; DDL mixes both. | Pick one rule (BIGINT in decision path) and align DDL. | 005, 012 |
| C9 | SPEC V2 §19.3 spx_crossing_state_history | `cooldown_until INTEGER, rearmed_at INTEGER` in DuckDB violate §19.8.3 Rule 1 (epoch cols must be BIGINT). | Change to BIGINT in the baseline. | 010, 054 |
| C10 | ARCH V2 §C.3 | Final DDL in §19.2 contains 070/071 tables, but baseline must stop at SQLite 069/DuckDB 041. | Generate baseline only from the historical chain; apply 070/071, 042/050 as pending. Historical migrations 001–064/001–037 may not exist yet. | 010 |
| C11 | Runbook Task 4 | ADR-001 (anti-detection scope) undecided. | Choose interpretation A (authorized session management) or stop. | 052, 064 |
| C13 | ARCH V2 §C.3 vs brief 010a D1 | Migration manifest named `MANIFEST.md` in ARCH; brief mandates a single machine-readable `migrations/MANIFEST.json` with a defined entry schema. | Make `MANIFEST.json` canonical (log drift); queue an ARCH V2 §C.3 wording amendment. Resolve before 010a apply. | 010a, 010b |
| C14 | SPEC V2 §19.2 vs brief 010a D12 | Ledger PK `migration_id` stores one row per migration, so it cannot hold per-attempt retry history; brief requires an audited retry workflow. | Keep one row per `migration_id` (retry = FAILED→OK UPDATE), record the audited attempt trail outside the ledger; if a per-attempt trail is required, amend the SPEC contract (do not change DDL silently). | 010a, 010b |
| C12 | SPEC V1/ARCH V4 dealer logic | No BS gamma/vanna/charm formulas, units, T clamp or carry in any volume; dealer sign undefined ("per signed fixture"); D.17–D.20/D.23/D.24 headings only; D.14c GammaAlign ORs opposite mechanisms, D_c=max biases up, vanna uses cluster-contaminated ΔIV and a likely unreachable 0.10 threshold; D.21 mixes charm into 0DTE; H.2 constants arbitrary. | Adopt openspec/formulas-dealer-greeks.md (F1–F8) after operator approval; shadow-first. | 031, 033, 034, 035, 036 |

## Gaps (heading-only or deferred in the docs; briefs mark these as Open Questions)
- ARCH V4 §AB.4–AB.13 deferred; SPEC V1 §2.11A.6–15 point to them (circular).
- ARCH V4 formulas not given: D.17–D.20, D.23, D.24 (tactical relevance, paired netting, flip alignment, persistence, derived flip, walls).
- ARCH V4 headings only: H.1, H.4–H.6, I.1–I.9, J.1–J.3, K, L.2–L.4, O.*, P, Q, R.2–R.7, S.5, S.7, T, U, V, W, X, Y.
- SPEC V1 §6.2/6.5, 9.2–9.4 (check lists, aggressor, opening-evidence clarification) are titles.
- IPC: no "pause capture intake" event (ARCH V1 M.1 step 1) and no ACK message type in the event list.
- canonical JSON hashing rules, CANONICAL_TRACE_NAMESPACE value, content-hash composition for dedup: unspecified.
- Offsite backup target: ARCH V1 says rclone crypt → B2/R2; runbook uses MEGA for the LUKS header only.
- Provider payload schemas and raw_color → normalized_meaning mapping tables: need fixtures.

### Open questions from brief 005a (still open — 2026-10-16)

Items below remain open; they belong to 005c or a later change. Items already
resolved appear under "## Resolved (2026-10-16)" further down.

- **Q3** — `_PCT` semantics. `SPX_FALSE_CROSS_TOLERANCE_PCT = 0.0015` is a
  fraction, but `BUDGET_FLOW_ALERT_RESERVE_PCT = 60` and
  `BUDGET_PREMARKET_BORROW_PCT = 20` are percent points. A 0.60 vs 60
  confusion is possible. Needs an ARCH amendment to normalize the names.
- **Q4** — Unitless constants. `TACTICAL_2DTE = 3000`, `SHORT_TACTICAL = 5000`,
  `SWING = 10000`, `LONGER_HORIZON = 30000` have no unit in the name. Confirm
  the unit and rename in ARCH.
- **Q5** — Approval-pending flags. `MIN_VEGA` has no `_APPROVAL_PENDING`
  companion, and the generated docstring calls the pending set "C12
  dealer/greeks" although it includes SPX, WAL, budget and newsletter
  constants. Verify against ARCH V1 Sec AI.3, then fix
  `scripts/gen_constants.py` if needed.
- **Q7** — Structural constants location. `INT64_MIN/MAX`, `MICROS_PER_MILL`,
  `DURATION_MS_MAX` and the suffix tuples live in `units.py`/`time.py`, not
  `constants.py` (AGENTS rule 8). Confirm they are exempt, and check what
  `scripts/check_constants.py` covers.
- **Q10** — `_epoch_ns`. The naming rule accepts it but there is no nanosecond
  type. Add `EpochNs` or drop the suffix.

## Resolved (2026-10-15)

- **C1** — bundle frozen at v2.0.5.1 / v5.1.5.1 (11 files). Runbook Task 5 updated. Closed 2026-10-15.
- **C2** — SpecKit retired. OpenSpec flow lives in `openspec/config.yaml` + `openspec/constitution.md`. Closed 2026-10-15.
- **C3** — SPEC Vol 6 F.3 wins (per-scope, no pooling). Decision recorded; closing finalises with feature 084.
- **C4** — one-shot re-emit confirmed per SPEC Vol 5 §O.7.4. Decision recorded; closing finalises with feature 071.
- **C5** — DDL wins; SPEC Vol 3 §17.5 rewritten to match `signal_outcomes` PK. Closed 2026-10-15.
- **C6** — SPEC Vol 4 §20.72 pointer to reserved §20.67 removed. Closed 2026-10-15.
- **C8** — SPEC Vol 2 §19.4.4 is canonical (DDL home). SQLite INTEGER (64-bit); DuckDB `_cents/_mills/_micros` in decision path declared BIGINT. SPEC Vol 1 §19.4.4's "all BIGINT" is a summary. Closed 2026-10-15.
- **C9** — DuckDB `spx_crossing_state_history.cooldown_until` and `rearmed_at` changed to BIGINT. Closed 2026-10-15.
- **C11** — ADR-001 amended with source-scope-only clarification. §E/§F apply in full to authorized sources. Closed 2026-10-15.
- **RQ-002** — `signal_valid` ordering confirmed present in SPEC Vol 3 §8.1a/§8.4 (7 occurrences). Closed 2026-10-15.
- **RQ-004** — grade/state/episode split confirmed present in SPEC Vol 2 §19.2 (`episode_state`, 4 occurrences). Closed 2026-10-15.
- **RQ-005** — `package_quote_current.package_quote_id` confirmed cache-only, never in decision evidence (SPEC Vol 2 §19.6 invariant AM). Closed 2026-10-15.
- **RQ-006** (feature 005) — Rounding for unit conversions: integer-only with round-half-even at the display boundary; no fractional dollars in the decision path. Operator ruling 2026-10-15. Closed 2026-10-15.
- **RQ-007** (feature 005) — DurationMs bound: BIGINT/64-bit parity with a validated maximum `DURATION_MS_MAX = 2**31 - 1` in code (structural value bound — the Rule 2 column-safe bound — enforced at construction; the type stays 64-bit, i.e. no int32 *type* bound); the PROPOSED int32 bound is rejected. Operator ruling 2026-10-15. Closed 2026-10-15.

## Still open (deferred to relevant feature)

- **C7** — cosmetic invariant label collision with ARCH §AH/§AI. Deferred; no functional impact until both referenced together.
- **C10** — baseline manifest. Belongs to feature 010 per ARCH Vol 2 §C.3.
- **C12** — dealer/greeks formulas. Adopted from `openspec/formulas-dealer-greeks.md`; final validation lands with features 031/033/034/035/036.
- **RQ-008** (feature 005) — AI.1/AI.2 named constants (BASE_RISK_PCT, PREMIUM_STOP_PCT, THETA_BUDGET_PCT, TIME_STOP_DAYS, VOLATILITY_EXIT_IVR) have no home in `domain/constants.py`: the 005 spec delta scopes generation to ARCH Vol 1 §AI.3 only (parser anchored on the last `^AI.3` header so changelog mentions cannot shift it). A feature that needs an AI.1/AI.2 constant must extend `scripts/gen_constants.py` deliberately. NON-BLOCKING.
## Rejected

- **"Drop schedule jitter for provider access"** — violates ARCH Vol 3 §F.0.1a ("may only be strengthened"). Rejected 2026-10-15.
- **"Exclude interaction emulation / mimicry / fingerprint"** — violates §F.A, §F.B, §F.H, §F.P. Rejected 2026-10-15.


## Resolved (2026-10-16)

- **Q1** — Wrapper strategy. RESOLVED (005a). Factory-only plus AST ban
  shipped. `Cents`/`Micros`/`Mills` remain NewType aliases; direct construction
  is banned outside `domain/units.py` and `domain/time.py` by
  `tests/unit/test_direct_unit_construction.py`.

- **Q2** -- Floats in `constants.py`. Decision: narrower rule. Ban floats only
  for money/time/quantity/price. Dimensionless [0,1] ratios (opposing_share,
  confluence_score, coverage caps, calibrated_probability, loss_ratio) stay
  float. Do NOT blanket-convert to ppm/bps. To be written into AGENTS.md as
  the interpretation of rule 2. Implementation deferred to 005c.

- **Q6** -- Approval-pending constants. RESOLVED (005b). Added `approved(name)`
  accessor in `src/quantflow/domain/constants.py` plus AST ban on direct reads
  of pending names in `domain/**` and `kernels/**`. Tests:
  `tests/unit/domain/test_constants_access.py`.

- **Q8** -- Epoch ms plausible range. RESOLVED (005b). `EPOCH_MS_MIN =
  1_262_304_000_000` (2010-01-01Z), `EPOCH_MS_MAX = 2_840_140_800_000`
  (2060-01-01Z) in `src/quantflow/domain/time.py`. `epoch_ms()` rejects
  out-of-range values with `UnitValueError`. Tests:
  `tests/unit/domain/test_time.py`.

- **Q9** -- `DURATION_MS_MAX = 2**31-1` (~24.86 days). RESOLVED -- no conflict.
  SPEC Vol 4 Sec 18.14 lists cooldown values in SECONDS (behavioral-drift =
  2592000 = 30 days; flow-state-change = 3600 = 1 hour). SPEC Vol 1 Sec 19.8.3
  Rule 2 applies to `*_ms` duration columns, not to the cooldown config table.
  Cooldowns are stored in seconds; DurationMs values in `*_duration_ms` columns
  are sub-day in practice. No overflow.

- **Q11** -- Monotonic clock port. RESOLVED -- deferred. No consumer needs a
  monotonic reading today. `EpochMs` remains wall-clock. Add `MonotonicMs` to
  the Clock port when a timing-sensitive path requires it (feature 014).

- **Q12** -- Randomness and uuid. RESOLVED (005b). AST scan extended in
  `tests/unit/test_wall_clock_scan.py`: `BANNED_MODULES` includes `random`,
  `uuid`, `secrets`; `BANNED_CALL_NAMES` includes `getrandbits`, `randint`,
  `random`, `randrange`, `uuid1`, `uuid4`, `urandom`.

- **Q13** -- Ambiguous time field names. RESOLVED (005b). `field_name_kind`
  raises `FieldNameError` when a name matches both epoch and duration patterns
  (e.g. `epoch_latency_ms`). Code: `src/quantflow/domain/time.py`. Tests:
  `tests/unit/domain/test_time.py`.

- **Q14** -- Dollars conversion for cents/mills. Decision recorded. Conversion
  allowed ONLY inside designated kernels (flow strength D.14b, FDI D.25, hedge
  pressure D.21). Renderers use a separate display accessor. Banned elsewhere.
  Current spec text already says this. **AST enforcement deferred to 005c.**

- **Q15** -- `pocs/interface/` drift. RESOLVED -- freeze as snapshot.
  `pocs/interface/README.md` created in commit `fc7a6a8` pointing to canonical
  files at repo root. Do not delete (loses provenance). Do not sync
  (re-drifts).

- **Q16** -- Unreviewed archived 005 items. DEFERRED (not resolved). Archived
  `design.md`, `proposal.md`, `tasks.md`, the domain-enums and repo-bootstrap
  specs, `errors.py`, `ports/clock.py`, and the SPEC citations were not
  reviewed. Revisit if a future change reveals an inconsistency.

### 005c resolutions (2026-10-16)

- **Q2** -- Narrow-float rule. IMPLEMENTED (005c). AGENTS.md rule 2 gained the
  narrow-float interpretation: no floats for money/time/quantity/price;
  dimensionless [0,1] ratios stay float; decision-path thresholds that gate a
  state use integer `_PPM`; whole percent points use integer `_PCT`. The 11
  fraction-valued `*_PCT` constants in ARCH V1 Sec AI.3 were renamed to
  `*_RATIO` (D1). The `_PPM` migration of state-gating thresholds remains a
  design follow-up.

- **Q3** -- Suffix policy. RESOLVED (005c). `_PCT` = whole percent points (int),
  `_PPM` = parts-per-million (int, decision path), `_RATIO` = dimensionless
  [0,1] (float), `_PCTL` = integer percentile rank. Lint:
  `tests/unit/domain/test_unit_suffix_lint.py` (registered-suffix set plus a
  `{name: reason}` allowlist).

- **Q4** -- Lane latency constants. RESOLVED (005c). The four `Sec AI.3` lane
  constants were renamed to `LANE_LATENCY_CUTOFF_MS_2DTE`,
  `LANE_LATENCY_CUTOFF_MS_SHORT_TACTICAL`, `LANE_LATENCY_CUTOFF_MS_SWING`,
  `LANE_LATENCY_CUTOFF_MS_LONGER_HORIZON` (unit suffix carries the unit). DTE
  lane *identifiers* elsewhere in ARCH V1 (Sec AI.1/AI.4/AI.5/AI.6) are
  intentionally unchanged; the rename decouples the constant from the lane name.

- **Q5** -- Generator + approval invariant. RESOLVED (005c).
  `scripts/gen_constants.py` derives the pending-set label from the ARCH Sec
  AI.3 `[RECOMMENDED ...]` marker (`parse_pending_label`);
  `scripts/check_constants.py::verify_approval_companions` fails closed unless
  every AI.3 constant is either approved (a value assignment) or carries a
  `<NAME>_APPROVAL_PENDING` companion. Tests:
  `tests/unit/test_constants_check.py`.

- **Q7** -- Structural constants location. RESOLVED (005c) -- documentation only,
  no code move. Structural constants (`INT64_MIN/MAX`, `MICROS_PER_MILL`,
  `DURATION_MS_MAX`, `EPOCH_MS_MIN/MAX`, suffix tuples) stay in
  `units.py`/`time.py` by design: they are type invariants, not tunable config,
  and are exempt from the "named constants live once in ARCH V1 Sec AI.3" rule
  (AGENTS rule 8). Exemption documented in AGENTS.md rule 8 and in the
  `check_constants.py` module docstring.

- **Q10** -- `_epoch_ns`. DEFERRED (not resolved) to feature 020, which handles
  nanosecond timestamps. No `EpochNs` type is added in 005c.

- **cooldown_until** -- RESOLVED (005c). `_until` added to `EPOCH_NAME_SUFFIXES`
  in `src/quantflow/domain/time.py` and to SPEC V1 Sec 19.8.3 Rule 1, so
  `cooldown_until`/`blocked_until`/`valid_until` classify as epoch. Test:
  `tests/unit/domain/test_ddl_column_conformance.py`.

- **random call-name regression** -- RESOLVED (005c). `random`, `randint` and
  `randrange` were removed from `BANNED_CALL_NAMES` in
  `tests/unit/test_wall_clock_scan.py` (they are not numpy
  `Generator`/`RandomState` methods, so an injected generator's
  `rng.random()`/`rng.normal()` must not be flagged); `getrandbits` is retained
  as a call name and the `random` module ban is kept, so `import random` and
  `from random import randint` still fail.

- **F1 (005c follow-up)** — Stale `_PCT` references outside the 005c frozen scope.
  `docs/reference/release-v2.0.5.1-v5.1.5.1/SPEC_v2.0.5.1_Vol3_Decision.md` lines
  236 and 275 still cite `SPX_FALSE_CROSS_TOLERANCE_PCT` (0.0015) after the 005c
  rename to `_RATIO`. Not in 005c's declared frozen scope (ARCH Vol 1 + SPEC Vol 1
  §19.8.3 only). Follow-up change needed to align SPEC Vol 3 with the renamed
  constant, or accept the drift as documentation-only. Non-blocking.

## 010a Open Questions (pre-resolved 2026-10-17)

| ID | Conflict | Resolution |
|---|---|---|
| 010a-Q1 | ARCH says MANIFEST.md; 010a prompt mandates MANIFEST.json | 010a uses MANIFEST.json; 010b reconciles via design.md D16 |
| 010a-Q2 | ARCH uses 000_baseline_v2.0.5.1.sql; 010a uses ID 000_baseline | 000_baseline is logical ID; filename per D10 |
| 010a-Q3 | DuckDB 050 PROPOSED CORE REPAIR vs ADOPT-ONLY in D5 | 010a classifies as ADOPT-ONLY per D5 |
| 010a-Q4 | Ledger PK cannot hold per-attempt history | Retry audit in operator_control_audit per D12 |
| 010a-Q5 | Python 3.14 vs 3.12; symlink | Non-issue; pyproject is ground truth |

## C13 — Dealer Positioning Derivation

**Status: PROPOSED — operator approval pending.**
**Scope: design clarification; no production model change.**

1. **C13-01 — Baseline:** Preserve F3 `OI_NAIVE` as a labelled
   dealer-position assumption, not observed inventory.
2. **C13-02 — Alternatives:** Permit explicit per-underlying
   alternative sign assumptions in shadow research only.
   No automatic prior selection or production promotion.
3. **C13-03 — Independence:** Do not describe two models as
   independent evidence when they share alerts, OI, providers,
   or other material inputs. Record shared dependencies.
4. **C13-04 — Provenance:** Distinguish observed alert data,
   inferred aggressor side, unknown customer identity,
   alert-only volume, prior-day OI, and retrospective T+1
   opening/closing evidence. Unknown remains unknown.
5. **C13-05 — Estimator:** Reject the proposed flow/OI blend,
   unvalidated constants, automatic learning, 0DTE override,
   and uncalibrated confidence. Do not infer full dealer
   inventory from pre-filtered alerts.
6. **C13-06 — Evaluation:** Reuse
   `openspec/evaluation-protocol.md`, brief 041b, and
   SPEC Vol 6 §F.3 sample-size rules. Require per-underlying
   holdouts, leakage checks, provenance, and sensitivity
   testing. Negation is a sensitivity test, not a new
   production model.
7. **C13-07 — Enforcement:** Shadow-first. Propose Q6-style
   AST enforcement preventing unapproved estimators from
   entering production decision paths. Do not claim the
   guard exists before it is implemented and tested.

**Implementation constraints:** No migration 053, no frozen
reference edits, no `tools/apply_doc_patches.py`, no invented
runtime implementation, and no automatic production promotion.
Classify fields using SPEC/ARCH contracts. Propose storage only
if demonstrated necessary; do not assume research tables exist.

**Closure:** Operator approves the design decisions separately.
Model effectiveness and production promotion require empirical
validation under the existing evaluation protocol.

Implementation plan: `openspec/c13-dealer-positioning-implementation-plan.md`

## 010a Review Findings (2026-10-17)

### Fixed in fix(010a-review) commit

| ID | Finding | Severity | Resolution |
|---|---|---|---|
| 010a-R1 | `status.pending_count = len(applied_ok)` reported applied as pending | MAJOR | Renamed to `applied_count`, printed correctly |
| 010a-R2 | `verify` raised "not found in ledger" for pending entries (violates D15) | MAJOR | Pending now reported, does not fail exit code |
| 010a-R4 | `retry_failed` audit was stdout-only; no operator_control_audit write | MAJOR | Best-effort DB write if table exists; stdout fallback otherwise |
| 010a-R5 | `retry_failed` hardcoded `migrations/MANIFEST.json` | MINOR | Added `--manifest-path` option |

### Deferred / accepted

| ID | Finding | Severity | Resolution |
|---|---|---|---|
| 010a-R3 | SQL splitter uses `sqlite3.complete_statement` for both stores | MINOR | Works for 010a synthetic DDL. `duckdb.extract_statements` deferred to 011 if macros needed |
| 010a-R6 | Unmanifested 051/052 files under migrations/duckdb/ | DEFERRED | 010a scope per D5: "051/052 handled by 010b" |

### False positives

| Finding | Why |
|---|---|
| Missing change dir | Archived to `openspec/changes/archive/2026-10-17-010a-migration-runner-core/` |
| No MANIFEST.json | 010a uses synthetic fixtures only; real manifest is 010b |
| Only 2 test files | 8 files exist across `tests/migration/` (2) + `tests/unit/migration/` (5) + `tests/unit/test_migration_scaffolding.py` |
| `Connection = Any` | D13 doesn't mandate Protocol; mypy-strict clean |
| verify missing DB-newer check | Present at `cli/main.py` (~line 260) |
| `_detect_cycles ready.pop()` | Cosmetic; correct algorithm |
| `check_baseline_closure` duplicates `_require_dependencies` | Refactor opportunity, not a bug |
