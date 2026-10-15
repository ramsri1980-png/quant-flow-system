# 031 Option math and vol kernels
Epic: E3 | Depends: 005 | Blockers: formula gaps
Use: /opsx-propose @openspec/prompts/031-option-math-vol-kernels.md
Capabilities: greeks, implied-vol, surface
Sources: ARCH V4 §D; SPEC V1/V3 option-math sections
Requirements:
1. Pure BS/greeks/IV kernels in DOUBLE (analysis-only) with integer boundary conversion.
2. Solver non-convergence → explicit unavailable.
3. No I/O, no clock, no randomness.
Seed scenarios: deep ITM/OTM; zero vol/time; non-convergence; property: put-call parity within tolerance
Open questions (do not invent): tolerances and solver bounds if unnamed; day-count/rate source
Out of scope: provider quotes
