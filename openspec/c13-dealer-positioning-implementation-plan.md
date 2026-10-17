# C13 — Dealer Positioning Implementation Plan

**Status:** PROPOSED — operator approval pending
**Scope:** Design contracts, safeguards, shadow logging,
and validation readiness.
**Authority:** Existing frozen SPEC/ARCH reference documents
and approved OpenSpec decisions.
**Not authorized:** New production estimator, model promotion,
unvalidated numerical constants, or reference-bundle edits.

## 1. Design principles

- Dealer inventory sign is inferred, not directly observed.
- Keep `OI_NAIVE` as the documented F3 reference convention.
- Do not treat aggressor side as verified customer identity.
- Pre-filtered alerts are not a complete options-flow tape.
- T+1 OI evidence is retrospective, not event-level truth.
- Shared data or assumptions invalidate claims of independent
  model evidence.
- Unknown data must remain unknown.
- Alternative estimators are shadow-only until explicitly
  approved after evaluation.
- No new formula, table, threshold, or migration without
  a demonstrated contract-level requirement and approval.

## 2. C13-01 — Baseline sign model

### Implementation steps

1. Inspect `openspec/formulas-dealer-greeks.md` and the
   relevant SPEC/ARCH definitions of dealer gamma and sign.
2. Define `OI_NAIVE` as an explicit model identifier.
3. Document its call/put sign assumptions and the
   applicable underlying scope.
4. Specify how model ID, version, source and sign
   assumption are attached to a derived result.
5. Identify any missing contract fields. Propose additions
   without assuming runtime implementation exists.
6. Add deterministic examples for calls, puts, missing OI
   and zero-position cases.

### Acceptance criteria

- Baseline assumptions are visible and unambiguous.
- Derived output is labelled estimated, not observed.
- Model identity and provenance can be reproduced.
- No existing frozen formula is silently replaced.

### Approval checkpoint

Operator reviews the baseline sign contract before
implementation of any production kernel.

## 3. C13-02 — Alternative sign assumptions

### Implementation steps

1. Define a model configuration contract supporting
   explicit underlying and model identifiers.
2. Keep production and shadow configuration separate.
3. Define a shadow-only comparison interface without
   choosing a new estimator formula.
4. Specify behavior for unavailable model inputs.
5. Require explicit approval for any model promotion.
6. Add tests demonstrating that shadow output cannot
   influence production decisions or rankings.

### Acceptance criteria

- Alternatives are reproducible and versioned.
- Per-underlying scope is explicit.
- Automatic prior selection is prohibited.
- Production decisions are invariant when only shadow
  configuration changes.

### Approval checkpoint

Operator approves candidate model definitions separately
from the architecture that hosts them.

## 4. C13-03 — Model independence and disagreement

### Implementation steps

1. Inventory model A (`OI_NAIVE`), model B
   (`SIGNED_FLOW`) and model C (`PROVIDER`) inputs
   from F3 and ARCH.
2. Classify shared observations, transformations,
   provider dependencies and assumptions.
3. Define comparison metadata identifying common inputs.
4. Specify when disagreement produces the documented
   `UNINFORMATIVE` result.
5. Distinguish genuine evidence disagreement from
   sensitivity to competing assumptions.
6. Add tests for agreement, disagreement, missing
   model data and shared-input cases.

### Acceptance criteria

- No unsupported independence claim remains.
- Comparison output identifies model dependencies.
- Disagreement cannot be presented as high confidence.
- Existing F3 semantics are preserved unless an
  explicitly approved amendment changes them.

### Approval checkpoint

Operator approves any change to F3 decision semantics.

## 5. C13-04 — Source fields and provenance

### Implementation steps

1. Inventory available fields from SPEC Vol 2 canonical
   DDL and relevant ARCH contracts.
2. Review SPEC Vol 1 alert-source limitations.
3. Review SPEC Vol 3 opening-evidence descriptions.
4. Review ARCH opening-evidence and T+1 OI workflows.
5. Build a field matrix with:
   - field name and source document
   - observed / inferred / derived / unavailable
   - temporal availability
   - scope and completeness
   - null/unknown handling
6. Explicitly distinguish:
   - observed alert-side data
   - inferred aggressor side
   - unknown customer identity
   - alert-only quantity vs full tape volume
   - prior-day OI
   - retrospective T+1 OI classifications
7. Identify conflicts between source claims and
   canonical schema. Do not invent missing fields.
8. Add test cases ensuring missing evidence remains
   unknown rather than defaulting to a directional sign.

### Acceptance criteria

- Every required field has a cited source or is marked
  as a proposed addition.
- Missing fields are not represented as implemented.
- Temporal leakage is prohibited by contract.
- Alert quantity is not called full-market volume.

### Approval checkpoint

Operator approves new source or schema requirements
before ingestion or persistence work begins.

## 6. C13-05 — Unapproved estimator exclusion

### Implementation steps

1. Define the approved production estimator boundary.
2. Define shadow-only candidate registration metadata.
3. Require model identifier, version, approval status
   and allowed execution scope.
4. Exclude Kimi's unvalidated blend, constants,
   automatic prior learning and 0DTE override.
5. Specify a failure mode for approval-pending models
   invoked from production decision paths.
6. Add tests that intentionally attempt prohibited
   invocation and verify rejection.
7. Require a reviewable approval record for any
   estimator promotion.

### Acceptance criteria

- Approval-pending estimators cannot affect production
  decisions, recommendations or confidence.
- No numerical constant is approved by implication.
- A model cannot promote itself.
- Missing approval metadata fails closed.

### Approval checkpoint

Operator must explicitly approve each estimator and
its numerical parameters before production use.

## 7. C13-06 — Reuse existing evaluation protocol

### Implementation steps

1. Inspect `openspec/evaluation-protocol.md`.
2. Locate brief 041b in the repository.
3. Inspect SPEC Vol 6 section F.3 sample-size rules.
4. Identify existing definitions for holdouts,
   markouts, leakage prevention and promotion gates.
5. Write only C13-specific evaluation extensions:
   - per-underlying hypotheses
   - model comparison pairs
   - model version and input coverage
   - sample inclusion/exclusion criteria
   - shadow-vs-baseline comparisons
   - negation as sensitivity testing only
6. Reuse existing sample-size requirements; do not
   introduce arbitrary new thresholds.
7. Define a reproducible evaluation report contract.
8. Prohibit automatic promotion based on hit counts.

### Acceptance criteria

- C13 does not duplicate the evaluation framework.
- Holdouts and leakage checks are explicitly applied.
- Each comparison identifies model versions and scope.
- Insufficient evidence yields no promotion claim.

### Approval checkpoint

Operator approves C13-specific hypotheses and promotion
criteria before interpreting results.

## 8. C13-07 — Static enforcement and CI

### Implementation steps

1. Inspect the existing Q6 open question and related
   enforcement proposals.
2. Identify actual production entry points and shadow
   allowlist paths from the repository.
3. Define how approval-pending estimators are marked.
4. Design an AST/static-analysis rule preventing
   approval-pending estimators or parameters from being
   referenced by protected production paths.
5. Do not rely solely on searching for a constant name:
   account for imports, aliases and indirection within
   the supported language scope.
6. Implement negative fixtures that deliberately violate
   the rule.
7. Implement positive fixtures for permitted shadow use.
8. Integrate the rule into the existing CI test workflow
   once the repository's real structure is verified.
9. Fail closed on unsupported or ambiguous cases, or
   document the limitation and require review.

### Acceptance criteria

- A forbidden production reference fails CI.
- A permitted shadow reference passes.
- Aliased references are tested.
- Enforcement is demonstrated, not merely documented.
- Protected paths and allowlists are explicit.

### Approval checkpoint

Operator approves the enforcement boundary and
exceptions before enabling the CI gate.

## 9. Cross-cutting prerequisite — Shadow logging

1. Identify the minimum inputs and derived outputs
   needed to replay comparisons.
2. Define event identity, timestamps, underlying,
   model ID/version, source provenance and missing-data
   status.
3. Review existing SPEC/ARCH persistence contracts and
   migrations before proposing storage.
4. If no compatible storage exists, propose the smallest
   justified storage change with keys, ownership,
   retention and replay behavior.
5. Keep shadow logging separate from production decisions.
6. Test deterministic replay and no production side effects.
7. Enable comparisons only after shadow data capture is
   demonstrably complete enough for the chosen protocol.

**Do not assume existing research storage is sufficient.
Do not create migration 053 without separate approval.**

## 10. Delivery order

### Stage A — Design and contract verification

- C13-01 baseline definition
- C13-03 dependency and disagreement semantics
- C13-04 provenance matrix
- Existing protocol and Q6 review
- Operator approval of proposed design changes

### Stage B — Guardrails

- C13-05 estimator approval boundary
- C13-07 AST/static enforcement
- Negative and positive CI tests

### Stage C — Shadow infrastructure

- Minimum shadow logging contract
- Storage gap assessment
- Replay and production-isolation tests

### Stage D — Model research

- C13-02 alternative shadow configurations
- C13-06 evaluation integration
- Per-underlying holdouts and sensitivity tests
- Evidence report and separate promotion decision

## 11. Agent deliverables

The implementation agent must provide:

1. Repository file inventory with verified paths.
2. SPEC/ARCH citation matrix for each proposed field.
3. File-by-file implementation proposal.
4. Minimal patches for approved changes only.
5. Tests and expected failure cases.
6. Explicit list of assumptions and unresolved gaps.
7. Operator-approval checkpoints.
8. Evidence that frozen references and checksums
   remain unchanged.

Do not invent runtime modules, schemas, numerical
parameters, or evidence of implementation.

## 12. Completion definition

**Design complete:** Contracts, unknown-data behavior,
dependencies, approval boundaries and tests are reviewed.

**Implementation complete:** Approved safeguards and
shadow logging exist and pass tests.

**Research complete:** Existing evaluation protocol
produces reproducible, adequately sampled evidence.

**Production approved:** A separate explicit operator
decision authorizes a validated estimator.

These are distinct states. None implies the next.
