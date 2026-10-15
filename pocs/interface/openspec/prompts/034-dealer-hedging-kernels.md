# 034 Dealer hedging kernels
Epic: E3 | Depends: 031 | Blockers: D.17-D.20, D.23, D.24 formulas missing
Use: /opsx-propose @openspec/prompts/034-dealer-hedging-kernels.md
Capabilities: gex-style-levels, flip, walls
Sources: ARCH V4 §D
Requirements:
1. Specify only formulas actually given in ARCH V4 §D; everything else is open.
2. Pure, deterministic, append-only dealer_level_maps output.
Seed scenarios: stale chain; empty chain; flip absent
Open questions (do not invent): BLOCKING tactical relevance, paired netting, flip alignment, persistence, derived flip, walls (D.17–D.20/D.23/D.24) — no formulas
Out of scope: any invented formula
