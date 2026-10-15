# QuantFlow Constitution

Loaded on demand by /opsx-explore and /opsx-propose (not every message). Short form is in AGENTS.md.

## 1. Mission and mode
Local single-operator options-flow RESEARCH system: observe pre-filtered flow alerts from authorized sources, validate against dealer positioning/market structure, classify probabilistically, deliver via three workflows (flow alert, morning brief, ad hoc report) from one thesis → one immutable analysis snapshot → one market map. Mode: RESEARCH. No autonomous orders, ever (SPEC V1 §1.3.1). No LLM between observations and decisions (§1.3.4). No ML before E8; model output never reaches a decision unless promoted through active_model_manifest (SPEC V6 P2).

## 2. Document authority (who wins)
- Anti-detection/authorization: ARCH V3 §F. Decision precedence: SPEC V3 §8.4. Canonical DDL: SPEC V2 §19 (ARCH V2 mirrors it; SPEC wins). Named constants: ARCH V1 §AI.3.
- Route-specific exits: ARCH V4 §AH wins over SPEC V3 §15.5.
- SPEC V5, V6, V7 are additive/non-normative; where they conflict with another volume, the other volume wins. V7 modules (AE/AF/AG) are inert until adopted.
- Archived designs never override docs/reference/CURRENT. "Per prior" is banned in normative text; cite explicitly.

## 3. Principles (from SPEC V1 §1.4)
Correctness of a number outranks everything. Observed facts, inferences and decisions are never conflated. Thresholds apply to calibrated lower bounds. Capital preservation outranks signal capture. Numeric path is deterministic and kernels are pure and test-first. Only authorized data. Fail closed, log loudly. Every decision is auditable and versioned. Decision-critical state survives analytical-store outage (SQLite first). No executable recommendation before a live quote. Perp/proxy price never satisfies ACTIONABLE_NOW. Evidence grades (MEDIUM/HIGH_CONFLUENCE) are not probabilities.

## 4. Data rules
- Units: `_cents` option prices, `_micros` underlying/index, `_mills` strikes/levels; BIGINT in decision path; DOUBLE analysis-only; dollars only at formula boundaries (÷1e6).
- Time: UTC epoch ms. SQLite INTEGER, DuckDB BIGINT; no DuckDB TIMESTAMP. Names `*_ts/*_at/*_epoch_*` are epoch; `*latency_ms/*staleness_ms/*age_ms/*duration_ms` are bounded INTEGER durations. Dates: SQLite TEXT ISO, DuckDB DATE. Display ET.
- Evidence fields in decision-path tables reference immutable observation IDs; package_quote_current.package_quote_id (cache key) never enters decision evidence.
- Append-only: market_map_snapshots, dealer_level_maps, analysis_snapshots, zero_dte_cluster_snapshots, position_exit_events. Corrections append with supersedes_id.

## 5. Determinism and purity
Kernels/AnalysisSnapshotBuilder: pure functions of inputs; no wall clock except as_of; no randomness except as_of-seeded; same inputs+versions → byte-identical output; no provider calls; no calls to fetch_*, get_current_*, read_pointer_* (AST + doc lint). Provider logic lives only in adapters.

## 6. Process and security
quantd (single SQLite writer; DuckDB writes via db_pool_executor), provider_capture_worker (no DB, no vault token, MemoryMax measured), human_rhythm_scheduler. Capture talks to quantd via localhost/Unix socket IPC only; credentials only via one-time quantd-mediated token (TTL 60 s). Operator mutations only via quantctl → quantd with operator_control_audit rows. MCP/Muse tools are read-only fixed templates: no SQL, shell, URL, secret, order or migration tools. Secrets only in Bitwarden/systemd credentials; never in Git, logs or payloads (log payload_hash).

## 7. Decision rules
Order: external facts (RETRACTED > INVALIDATED > STAND_DOWN) → DQ gate → signal_valid → portfolio/market/entry outcomes (SPEC V3 §8.4). ACTIONABLE_NOW needs a calibrator, p_lower ≥ max(route threshold, p_BE + SAFETY_MARGIN), EV_lower > 0, declared exit handler satisfying ARCH V4 §AH, and fresh executable quotes. Until Stage 4 exit handlers exist, ACTIONABLE_NOW is unreachable by design. 0DTE/1DTE: research clusters only.

Dealer/greeks: formulas live in openspec/formulas-dealer-greeks.md. Exposures are dealer-signed by an explicit model; if two independent sign models disagree the regime is UNINFORMATIVE. No minute-by-minute recompute: maps refresh on TTL/event and carry their age. Dealer-derived features are SHADOW-ONLY (logged, no effect on grade/EV) until per-scope outcomes show lift. 0DTE maps built on prior-day OI are labelled provider-estimated/OI-stale.

## 8. Authorization and anti-detection
Automation is allowed only for sources with source_authorization APPROVED, unexpired, automation_allowed=1 and a specific recorded ToS provision. Fail closed on ambiguity. Challenges/CAPTCHA are resolved by the human; persistent challenge or 403 on an authorized source means the recorded provision is wrong: suspend and route to authorization review (ARCH V3 §F.0.8). Scope is set by ADR-001; until it exists, specs cover authorization gating, state machine, rate/session limits, verification and halt behavior only.

## 9. Persistence
Migrations forward-only with SHA-256 manifest; never edit applied; reserved IDs (SQLite 072–079; DuckDB 046–049) never auto-applied; AE/AF/AG (043–045) only when adopted; baseline never generated from the patched final DDL. Schema parity (ARCH V2 vs SPEC V2) enforced by hash test.

## 10. Observability
Read-only on decision tables; never influences decisions; fail-open; localhost-only health endpoint; no secrets in logs (SPEC V5 G1–G7).

## 11. Testing
Ladder: unit golden → property → contract → migration → repository → pipeline fixture → restart/idempotency → replay → workflow golden → acceptance → opt-in live smoke. Ten classes per feature: golden, boundary/units/sign, missing/stale/malformed, duplicate/idempotency/restart, port contract, migration fresh+upgrade, replay, property invariants, no-future-leakage, temp-paths-only. Coverage ≥95% kernels/** and domain/**. Never weaken domain tests to fix a live provider. The acceptance suite may only grow.

## 12. How to write specs here
- OpenSpec requirements: "### Requirement:" with SHALL, each with "#### Scenario:" WHEN/THEN, each citing its source section.
- Separate SPECIFIED (stated in docs) from UNSPECIFIED (heading-only, deferred, conflicting). Unspecified → Open Questions; never invent formulas, thresholds, schemas or enums.
- One feature = one change. Slice big features by capability. Do not mix epics.
- If a brief and a doc disagree, the doc wins; log it in conflicts-and-gaps.md.

## 13. Change control
Spec changes for frozen areas (ARCH V3 §F) need a diffed proposal and a re-run of §F.Q; the suite only grows. Resolve BLOCKING open questions with the operator before /opsx-apply.
