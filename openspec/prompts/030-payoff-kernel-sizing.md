# 030 Payoff kernel and sizing
Epic: E3 | Depends: 005 | Blockers: none known
Use: /opsx-propose @openspec/prompts/030-payoff-kernel-sizing.md
Capabilities: payoff-kernel, sizing
Sources: SPEC V1/V3 payoff and sizing sections; ARCH V4 §D
Requirements:
1. Pure integer payoff for single legs and spreads at expiry/mark.
2. Sizing as pure function of inputs; capital preservation outranks capture.
3. Same inputs+versions → byte-identical output.
Seed scenarios: golden payoffs; sign/units boundary; zero/negative width; property: payoff bounded by width
Open questions (do not invent): sizing parameters not in §AI.3; rounding rule
Out of scope: execution, orders
