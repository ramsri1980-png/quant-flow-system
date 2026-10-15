# QuantFlow — agent rules (keep ≤ 40 lines; loaded every session)

Project: local single-operator options-flow RESEARCH system. No orders, no autonomy, no LLM in the decision path, no ML before E8.
Truth: docs/reference/CURRENT/ (SPEC v2.0.5.1 V1–V7, ARCH v5.1.5.1 V1–V4). Cite as "SPEC V3 §8.4" / "ARCH V4 §D.5". Never write "per prior".
Full rules: openspec/constitution.md (read it when proposing/designing). Open conflicts: openspec/conflicts-and-gaps.md.
Flow: /opsx-explore → /opsx-propose @openspec/prompts/NNN-*.md → /opsx-apply → /opsx-verify → /opsx-archive. One session per phase.

Non-negotiables
1. Fail closed. Missing/stale/ambiguous evidence → explicit unavailable/WATCH, never a silent default or 0.
2. Units: option prices `_cents`, underlying/index `_micros`, strikes/levels `_mills`; all BIGINT in decision path; DOUBLE is analysis-only. Epoch ms: SQLite INTEGER, DuckDB BIGINT, no DuckDB TIMESTAMP.
3. Kernels are pure: no I/O, no wall clock, no randomness except as_of-seeded. AnalysisSnapshotBuilder never calls fetch_*, get_current_*, read_pointer_*.
4. Only quantd writes SQLite/DuckDB. Capture process: no DB, no vault token.
5. Decision order is SPEC V3 §8.4 with signal_valid (§8.1a). Renderers never upgrade a decision. 0DTE/1DTE are research-only (no route, size, ACTIONABLE_NOW).
6. cluster_grade / cluster_state / episode_state are disjoint vocabularies; BASIC is a grade only.
7. Migrations are forward-only; never edit an applied one; pending = enabled − baseline_covered − applied (never MAX(id)).
8. Named constants live once in ARCH V1 §AI.3 (UPPER_SNAKE_CASE); reference by name, never restate.
9. Automation only on sources with a recorded authorization (SPEC V1 §4.1, ARCH V3 §F.0). CAPTCHA/challenge/403 are never bypassed: stop, route to review.
10. Never touch /data in dev/tests (temp paths only). No secrets/payloads in repo or logs. No time.sleep in async.
11. Spec gap or conflict → list under "Open questions" and stop. Do not invent formulas, thresholds or schemas.
12. Tests first: 10 test classes per feature; ≥95% coverage on kernels/** and domain/**.
13. Archived designs never override CURRENT.
14. Reuse first: search openspec/modules.md and src/ before creating anything; extend/compose existing ports and kernels.
15. Every design.md has a "Reuse" section (modules reused; why any new module is needed).
16. Dealer/greeks logic follows openspec/formulas-dealer-greeks.md: dealer sign is an explicit parameter, features run shadow-only until outcomes justify them.
