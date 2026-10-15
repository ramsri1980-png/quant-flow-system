# 036 0DTE cluster kernels
Epic: E3 | Depends: 031, 035 | Blockers: none known
Use: /opsx-propose @openspec/prompts/036-zero-dte-cluster-kernels.md
Capabilities: cluster-grade, cluster-state, episode-state
Sources: SPEC V1/V3 0DTE sections; SPEC V2 §19 (cluster snapshots)
Requirements:
1. Research-only clusters: no route, size, or ACTIONABLE_NOW.
2. cluster_grade, cluster_state, episode_state use disjoint vocabularies; BASIC is a grade only.
3. zero_dte_cluster_snapshots append-only.
Seed scenarios: grade/state mixup rejected; empty cluster; 1DTE
Open questions (do not invent): thresholds only by named constant
Out of scope: trading decisions
