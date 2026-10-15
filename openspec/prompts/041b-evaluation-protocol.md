# 041b Evaluation protocol, tags, ratings, report
Epic: E4 | Depends: 041, 034, 036 | Blockers: dealer_map_regime (DuckDB 051) for H1/H4/H6
Use: /opsx-propose @openspec/prompts/041b-evaluation-protocol.md
Capabilities: evaluation-report, event-tags, operator-ratings
Sources: openspec/evaluation-protocol.md; SPEC V1 §2.20.8 (cluster outcomes); SPEC V2 §19 signal_outcomes, zero_dte_cluster_snapshots (flow_strength, dealer_alignment, confluence_score), zero_dte_cluster_outcomes, shadow_samples; ARCH V1 (all operator mutations via quantctl → quantd, operator_control_audit); tools/eval_stats.py, tools/event_tags.py.
Requirements:
1. Weekly read-only report job implements the protocol (H1–H6, day-clustered bootstrap, Holm, INSUFFICIENT rule, protocol commit hash in output). It never writes to decision tables or flips flags.
2. Baseline comparison uses stored columns only (flow_strength vs confluence_score/dealer_alignment; dealer_map_regime join). No recomputation of alert-time values (no future leakage).
3. Event tags: computed deterministically from reference/event_calendar.csv + third-Friday/quarter-end rules; calendar file is versioned; missing calendar rows → tag absent, never guessed.
4. Operator rating: `quantctl rate <alert_kind> <alert_ref> useful|not_useful|unsure [--reason CODE] [--note TEXT]` → quantd writes an operator_control_audit row (channel QUANTCTL) and an operator_alert_ratings row (DuckDB 052). No inbound Discord/webhook channel.
5. Reports and ratings are append-only; latest rating per alert wins at read time.
Seed scenarios: group below minimum N → INSUFFICIENT; two alerts same day counted as one cluster; calendar missing; rating twice (latest wins); quantctl without audit write → rejected; sign_fragile alerts excluded from H1.
Open questions: BLOCKING approve [P] minimums (60 sessions, 100 alerts/group) and primary horizons; NON-BLOCKING who maintains event_calendar.csv and from which official source; report delivery channel (file vs Discord digest).
Out of scope: changing alert grading, ML, auto-promotion of flags.
