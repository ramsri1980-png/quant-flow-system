# 031 Greeks and vol kernels (rewritten, C12)
Epic: E3 | Depends: 005 | Blockers: C12 approval, C8
Use: /opsx-propose @openspec/prompts/031-option-math-vol-kernels.md
Capabilities: bsm-greeks (gamma, vanna, charm, delta), dollar-exposure-units, time-and-guards, implied-vol-decomposition
Sources: openspec/formulas-dealer-greeks.md F1, F2 (PROPOSED → needs operator approval); ARCH V4 §D.3; SPEC V1 §22.2 (Vanna=∂Δ/∂σ, Charm=∂Δ/∂t); reference oracle tools/greeks_reference.py.
Requirements:
1. Pure BSM kernel with carry q and forward-consistent inputs: gamma=e^(-qT)n(d1)/(Sσ√T); vanna=-e^(-qT)n(d1)d2/σ; charm=∂Δ/∂t calendar (formulas exactly as F1).
2. T in calendar years (ACT/365) from epoch ms; T clamped to DEALER_T_MIN_S (300 s); σ ≤ GREEKS_SIGMA_MIN or > GREEKS_SIGMA_MAX, missing IV, or T≤0 → option EXCLUDED and counted in coverage (never defaulted).
3. Dollar exposures exactly per F2: Gamma$ per +1% = Γ·S²·0.01·M·OI; Vanna$ per vol pt = Vanna·0.01·S·M·OI; Charm$ per day = Charm/365·S·M·OI. S converted from _micros at the boundary only.
4. D.3 decomposition unchanged; state MIN_VEGA unit explicitly (it is currently unitless in the docs).
5. Tests fail CI: grid 10 spots×5 vols×4 tenors×call/put×(r,q=0 and r,q>0): analytic vs central finite difference (gamma <1e-3, vanna/charm <1e-4 relative) and vs py_vollib/QuantLib (<0.5%); sign table of F1 as golden checks.
Seed scenarios: T→0 (clamp); σ missing; deep ITM/OTM; q>0; put=call charm at r=q=0; 0DTE vs 30DTE.
Open questions: BLOCKING approve the recommended DEALER_T_MIN_S / GREEKS_SIGMA_* values (apply_doc_patches.py writes them to ARCH V1 §AI.3) and F1–F2; NON-BLOCKING day-count (calendar vs trading-day) — pick calendar for greeks unless operator decides otherwise; r and q source.
Out of scope: dealer sign, levels, flips (034), provider IV ingestion.
