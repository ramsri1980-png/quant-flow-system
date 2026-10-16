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

### Open questions from brief 005a (recorded 2026-10-16; recommended option first; NONE implemented — resolve in 005b or the consuming feature)

- **Q1** — Wrapper strategy. Default in 1.2 of 005a is factory-only plus AST ban (implemented). Alternative: make wrappers int subclasses with a validating `__new__` (also needs arithmetic rules so `Cents + Micros` raises). Confirm.
- **Q2** — Floats in `constants.py`. Thresholds like `DEALER_COVERAGE_MIN = 0.80`, `SPX_*_PCT`, weights, and `MIN_VEGA` are floats, but AGENTS rule 2 says no floats in the decision path. Options: declare them analysis-side only, or restate as integers (for example ppm) via an ARCH V1 §AI.3 amendment.
- **Q3** — `_PCT` semantics. `SPX_FALSE_CROSS_TOLERANCE_PCT = 0.0015` is a fraction, but `BUDGET_FLOW_ALERT_RESERVE_PCT = 60` and `BUDGET_PREMARKET_BORROW_PCT = 20` are percent points. A 0.60 vs 60 confusion is possible. Needs an ARCH amendment to normalize the names.
- **Q4** — Unitless constants. `TACTICAL_2DTE = 3000`, `SHORT_TACTICAL = 5000`, `SWING = 10000`, `LONGER_HORIZON = 30000` have no unit in the name. Confirm the unit and rename in ARCH.
- **Q5** — Approval-pending flags. `MIN_VEGA` has no `_APPROVAL_PENDING` companion, and the generated docstring calls the pending set "C12 dealer/greeks" although it includes SPX, WAL, budget and newsletter constants. Verify against ARCH V1 §AI.3, then fix `scripts/gen_constants.py` if needed.
- **Q6** — Enforcing approval-pending. Nothing stops a kernel from using a pending constant. Option: an accessor that raises unless approved, or a lint test.
- **Q7** — Structural constants location. `INT64_MIN/MAX`, `MICROS_PER_MILL`, `DURATION_MS_MAX` and the suffix tuples live in `units.py`/`time.py`, not `constants.py` (AGENTS rule 8). Confirm they are exempt, and check what `scripts/check_constants.py` covers.
- **Q8** — Plausible epoch range. `epoch_ms` accepts any int64, so seconds (~1.7e9) or microseconds pass silently. Operator must supply min/max bounds.
- **Q9** — `DURATION_MS_MAX = 2**31-1` (~24.86 days). **RESOLVED — no conflict.** SPEC Vol 4 §18.14 lists cooldown values in SECONDS (behavioral-drift = 2592000 = 30 days; flow-state-change = 3600 = 1 hour). SPEC Vol 1 §19.8.3 Rule 2 applies to *_ms duration columns, not to the cooldown config table. Cooldowns are stored in seconds; DurationMs values in *_duration_ms columns are sub-day in practice. No overflow. Documentation note only.
- **Q10** — `_epoch_ns`. The naming rule accepts it but there is no nanosecond type. Add `EpochNs` or drop the suffix.
- **Q11** — Clock port. `time.time_ns()` is not monotonic. Decide whether the port needs a monotonic reading for durations.
- **Q12** — Randomness and uuid. Constitution allows only as_of-seeded randomness. Decide how to lint `random`, `uuid`, `os.urandom` in `domain/**` and `kernels/**`.
- **Q13** — Name matches both epoch and duration (for example `epoch_latency_ms`): currently returns "epoch". Should it be rejected as ambiguous?
- **Q14** — Dollars conversion for cents/mills. Confirm whether any formula converts them, and with what divisor.
- **Q15** — `pocs/interface/` drift. It duplicates `AGENTS.md`, `.opencode/`, and `openspec/` and already differs (it lacks `041b-evaluation-protocol.md`). Freeze it as a POC snapshot, delete it, or sync it.
- **Q16** — Unreviewed items. The archived 005 `design.md`, `proposal.md`, `tasks.md`, the domain-enums and repo-bootstrap specs, `errors.py`, `ports/clock.py`, and the SPEC citations were not reviewed. Verify them.


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

- **Q2** -- Floats in constants.py vs AGENTS rule 2. RESOLVED -- narrower rule.
  Ban floats only for money/time/quantity/price (quantities with units).
  Dimensionless [0,1] ratios (opposing_share, confluence_score, coverage caps,
  calibrated_probability, loss_ratio) stay float. Do NOT blanket-convert to
  ppm/bps -- that churns ~30 constants and forces formula rewrites. Record in
  AGENTS.md as the interpretation of rule 2.
- **Q11** -- Monotonic clock port. RESOLVED -- deferred.
  No consumer needs a monotonic reading today. EpochMs remains wall-clock.
  Add a separate MonotonicMs reading to the Clock port only when a
  timing-sensitive path requires it.
- **Q14** -- Dollars conversion for cents/mills. RESOLVED.
  Conversion allowed ONLY inside designated kernels (flow strength D.14b,
  FDI D.25, hedge pressure D.21) -- those formulas require
  S = spot_micros / 1_000_000 before evaluating X_k / D_i. Renderers use a
  separate display accessor. Banned everywhere else. Current spec text
  ("dollars only at formula boundaries") already says this; no spec edit.
- **Q15** -- pocs/interface/ drift. RESOLVED -- freeze as snapshot.
  Create pocs/interface/README.md pointing to canonical files at repo root.
  Do not delete (loses provenance). Do not sync (re-drifts).
- **Q16** -- Unreviewed archived 005 items. RESOLVED -- deferred.
  No blocking gaps surfaced during 005b implementation. Revisit if a future
  change reveals an inconsistency with the archived 005 design, proposal,
  or tasks.
