# QuantFlow — agent rules (keep ≤ 40 lines; loaded every session)

Project: local single-operator options-flow RESEARCH system. No orders, no autonomy, no LLM in the decision path, no ML before E8.
Truth: docs/reference/CURRENT/ (SPEC v2.0.5.1 V1–V7, ARCH v5.1.5.1 V1–V4). Cite as "SPEC V3 §8.4" / "ARCH V4 §D.5". Never write "per prior".
Full rules: openspec/constitution.md (read it when proposing/designing). Open conflicts: openspec/conflicts-and-gaps.md.
Flow: /opsx-explore → /opsx-propose @openspec/prompts/<NNN-group>/<FFF>-*.md (or prompts/NNN-*.md if unsplit) → /opsx-apply → /opsx-verify → /opsx-archive. Change name = NNN-FFF-slug, always flat (constitution §12). One session per phase.

Non-negotiables
1. Fail closed. Missing/stale/ambiguous evidence → explicit unavailable/WATCH, never a silent default or 0.
2. Units: option prices `_cents`, underlying/index `_micros`, strikes/levels `_mills`; all BIGINT in decision path; DOUBLE is analysis-only. Epoch ms: SQLite INTEGER, DuckDB BIGINT, no DuckDB TIMESTAMP. No floats for money, time, quantity or price; dimensionless [0,1] ratios may be float (e.g. `opposing_share`, `confluence_score`, coverage caps). Decision-path thresholds that gate a state use integer `_PPM`; whole percent points use integer `_PCT`.
3. Kernels are pure: no I/O, no wall clock, no randomness except as_of-seeded. AnalysisSnapshotBuilder never calls fetch_*, get_current_*, read_pointer_*.
4. Only quantd writes SQLite/DuckDB. Capture process: no DB, no vault token.
5. Decision order is SPEC V3 §8.4 with signal_valid (§8.1a). Renderers never upgrade a decision. 0DTE/1DTE are research-only (no route, size, ACTIONABLE_NOW).
6. Distinct non-bridging types. `cluster_state` and `episode_state` share ACTIVE / RETRACTED / EXPIRED by SPEC V2 §19.2. BASIC is a grade only.
7. Migrations are forward-only; never edit an applied one; pending = enabled − baseline_covered − applied (never MAX(id)).
8. Named constants live once in ARCH V1 §AI.3 (UPPER_SNAKE_CASE); reference by name, never restate. Exempt: structural constants (`INT64_MIN/MAX`, `MICROS_PER_MILL`, `DURATION_MS_MAX`, `EPOCH_MS_MIN/MAX`, suffix tuples) live in units.py/time.py by design — type invariants, not tunable config.
9. Automation only on sources with a recorded authorization (SPEC V1 §4.1, ARCH V3 §F.0). CAPTCHA/challenge/403 are never bypassed: stop, route to review.
10. Never touch /data in dev/tests (temp paths only). No secrets/payloads in repo or logs. No time.sleep in async.
11. Spec gap or conflict → list under "Open questions" and stop. Do not invent formulas, thresholds or schemas.
12. Tests first: 10 test classes per feature; ≥95% coverage on kernels/** and domain/**.
13. Archived designs never override CURRENT.
14. Reuse first: search openspec/modules.md and src/ before creating anything; extend/compose existing ports and kernels.
15. Every design.md has a "Reuse" section (modules reused; why any new module is needed).
16. Dealer/greeks logic follows openspec/formulas-dealer-greeks.md: dealer sign is an explicit parameter, features run shadow-only until outcomes justify them.

are unavailable in the current session, use available native tools.
For discovery, use native search/glob. For reading, use native read
with a maximum of 120 lines per call. For grep, use head_limit <= 20.
Before modifying symbols, search for dependent references and report
them. Preserve all other safety, specification, and validation rules.
Never call tools that are not exposed in the current session.
When harness tools are available, follow rules 17 and 18 normally.

## Lean tool usage

- **Read:** Use native search to locate files, then read exact line ranges
  (`sed -n 'START,ENDp'`). Avoid full-file dumps; expand only as needed.
- **Edit:** Use native targeted edits. Preserve unrelated content and inspect
  bounded `git diff` output before committing.
- **Execute:** Redirect verbose command output to local logs and return concise
  summaries, failures, and exit codes. Retrieve full details only when needed.
- **Pytest:** Use `python3 tools/quant_capture.py --lines 35 -- <project-python>
  -m pytest -q --tb=short <selected tests>`. Use the project's test environment,
  preserve requested test scope, and inspect `FULL_LOG` selectively on failure.
  Collection errors are not test failures. Never claim success on nonzero exit.
