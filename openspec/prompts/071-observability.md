# 071 Observability
Epic: E7 | Depends: 011 | Blockers: C4
Use: /opsx-propose @openspec/prompts/071-observability.md
Capabilities: metrics, health, alerts
Sources: SPEC V5 G1–G7, O.7.4, O.13.5
Requirements:
1. Read-only on decision tables; fail-open; never influences decisions.
2. Localhost-only health endpoint; no secrets in logs.
3. Dealer-map drift rules (read-only, fail-open) over dealer_map_regime: coverage_oi_share drop, net_gross_ratio jump vs trailing EWMA, flip-existence rate change, regime-flip rate per session; tier via SPEC V5 O.7.2 like canary-drift/EWMA-shift.
Seed scenarios: metrics store down; secret in log rejected
Open questions (do not invent): BLOCKING C4 alert ladder vs tests 18b/20a
Out of scope: dashboards
