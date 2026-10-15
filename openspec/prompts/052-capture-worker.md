# 052 Capture worker (authorization-gated)

Epic: E5 | Depends: 050, 020 | Blockers: C11 (ADR-001 source-scope only)
Use: /qf-propose @openspec/prompts/052-capture-worker.md
Capabilities: capture-gate, session-limits, parity-verification, halt-signals, isolation, adversarial-harness, session-rhythm, interaction-hygiene
Sources: ARCH V3 §E.0–E.14, §F.0, §F.A, §F.B, §F.C, §F.D, §F.H, §F.I, §F.L, §F.N, §F.P, §F.S; SPEC V1 §4.1

Requirements:
1. Capture runs only when 050 gate passes (source_authorization APPROVED, unexpired, automation_allowed=1, ToS provision recorded).
2. Session lifecycle per ARCH V3 §E: log-normal median 30 min, hard cap 60 min; truncated-sampling primitive §E.0; start-hour draw §E.3; weekly multipliers §E.4.
3. Session pacing per §E.6 (micro-breaks), §E.7 (pacing floor), §E.8 (opening sequence), §E.9 (idle disengagement), §E.10 (winding-down).
4. Reference browser setup per §F.A: Google Chrome stable, headed under Xvfb, persistent user_data_dir, launch-flag hygiene (no --enable-automation, no --headless).
5. Fingerprint coherence per §F.B: canvas/WebGL/AudioContext are the physical machine's real values shared by all cohorts; variation limited to launch-flag-controllable properties (User-Agent, Accept-Language, window size, timezone, locale); cross-layer matrix evaluates at session start, INCOMPATIBLE aborts.
6. Traffic shape per §F.C: connection reuse, no parallel TLS handshakes, H2 SETTINGS matching cohort.
7. Loopback fingerprint echo per §F.D: navigate to echo.quant.internal (127.0.0.1:9443) before provider contact; session binding hash from pre-session echo + passive observations.
8. Renderer & interaction hygiene per §F.H: bezier + tremor + jitter mouse, overshoot-correct, lognormal inter-key delays 80–350 ms, occasional typo/backspace, occasional Tab/Enter nav, variable-velocity scroll with pauses.
9. Parity verification fails closed (§F.G reference fields).
10. Halt signals (§F.I) stop capture; human resolves challenges (§F.0.5).
11. Isolation per §F.S: no DB access, no vault token, MemoryMax measured.
12. Adversarial test harness per §F.L, runs daily, weekly audit.
13. Prohibited list per §F.P applies in full: no headless, no fresh context per session, no JS patching of navigator (except fp_seed), no font injection, no per-request canvas/WebGL/audio noise, no third-party fingerprint-echo services in authenticated sessions, no automated CAPTCHA solving, no Playwright, no Puppeteer, no DoH in the capture namespace.

Seed scenarios: gate closed; challenge appears; parity mismatch; halt signal; token TTL; session cap hit mid-break; restart mid-session preserves minimum cooldown; jitter distribution boundary-mass.

Open questions (do not invent): ADR-001 source-scope decision (which sources are authorized for automation; does not reduce §E/§F requirements for authorized sources).

Out of scope: bypass of provider access controls, automated challenge/CAPTCHA solving, evasion of unauthorized sources.
