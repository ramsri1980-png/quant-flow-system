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

## Still open (deferred to relevant feature)

- **C7** — cosmetic invariant label collision with ARCH §AH/§AI. Deferred; no functional impact until both referenced together.
- **C10** — baseline manifest. Belongs to feature 010 per ARCH Vol 2 §C.3.
- **C12** — dealer/greeks formulas. Adopted from `openspec/formulas-dealer-greeks.md`; final validation lands with features 031/033/034/035/036.

## Rejected

- **"Drop schedule jitter for provider access"** — violates ARCH Vol 3 §F.0.1a ("may only be strengthened"). Rejected 2026-10-15.
- **"Exclude interaction emulation / mimicry / fingerprint"** — violates §F.A, §F.B, §F.H, §F.P. Rejected 2026-10-15.
