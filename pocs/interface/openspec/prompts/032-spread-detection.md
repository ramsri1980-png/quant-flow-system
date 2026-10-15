# 032 Spread detection
Epic: E3 | Depends: 031 | Blockers: J.1-J.2 heading-only
Use: /opsx-propose @openspec/prompts/032-spread-detection.md
Capabilities: spread-detector
Sources: ARCH V4 §J (headings); SPEC V1 flow classification
Requirements:
1. Detect spreads/legs from canonical events deterministically.
2. Ambiguous grouping → unclassified, not guessed.
3. Output carries evidence IDs.
Seed scenarios: vertical; ratio; ambiguous multi-leg; duplicate print
Open questions (do not invent): BLOCKING J.1–J.2 are headings only — rules unspecified
Out of scope: scoring
