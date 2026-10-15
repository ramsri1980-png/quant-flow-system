# 052 Capture worker (authorization-gated)
Epic: E5 | Depends: 050, 020 | Blockers: ADR-001 (C11) BLOCKING
Use: /opsx-propose @openspec/prompts/052-capture-worker.md
Capabilities: capture-gate, session-limits, parity-verification, halt-signals, isolation, adversarial-harness
Sources: ARCH V3 §F.0, F.N, F.I, F.S, F.L
Requirements:
1. Capture runs only when 050 gate passes.
2. Session cap 60 min, pacing floor, sequential per provider (named constants).
3. Parity verification fails closed.
4. Halt signals (F.I) stop capture; human resolves challenges.
5. Isolation (F.S): no DB, no vault token, MemoryMax measured.
6. Adversarial test harness (F.L).
Seed scenarios: gate closed; challenge appears; parity mismatch; halt signal; token TTL
Open questions (do not invent): BLOCKING ADR-001 decision. EXCLUDED from spec: F.H interaction emulation, stochastic human-mimicry rhythm, behavioral matching, fingerprint spoofing/launch-flag disguise
Out of scope: evasion of detection or challenges
