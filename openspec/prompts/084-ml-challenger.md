# 084 ML challenger
Epic: E8 | Depends: 033, 041 | Blockers: C3
Use: /opsx-propose @openspec/prompts/084-ml-challenger.md
Capabilities: ml-challenger, model-manifest
Sources: SPEC V6 F.3, F.10, P2
Requirements:
1. Model output reaches decisions only via promotion in active_model_manifest.
2. Per-scope N_scope ≥ max(300,20p), 75/75 classes, no pooling (F.3 wins over F.10).
Seed scenarios: insufficient N; pooled attempt rejected
Open questions (do not invent): C3 recorded
Out of scope: auto-promotion
