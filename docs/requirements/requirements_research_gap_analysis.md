# Gap Analysis: Requirements Research vs. Plugin Implementation

**Date:** 2026-05-12
**Based on:** `requirements_research.md`
**Plugin reviewed:** `skills/requirements/SKILL.md`, `agents/requirements-analyst.md`

---

## High-Impact Gaps

### 1. EARS notation not enforced

The research's strongest single recommendation — EARS patterns (Ubiquitous / Event-driven / State-driven / Unwanted-behavior / Optional / Complex) — never appears in the skill or artifact template. Functional requirements are currently free-form bullets. EARS is the structural move that makes FRs testable and parseable by downstream workflows.

### 2. ISO 25010:2023 NFR walkthrough missing

Research is emphatic: "NFR omission is a prompting problem, not a model-capability problem." When explicitly prompted against ISO 25010's 9 quality characteristics, LLMs achieve 80.4% expert-level NFR coverage. The current Phase 4 has no ISO 25010 checklist walk — it surfaces only NFRs that happen to come up in conversation, guaranteeing systematic omissions.

The 9 characteristics to walk: Functional Suitability, Performance Efficiency, Compatibility, Interaction Capability (was Usability), Reliability, Security, Maintainability, Flexibility (was Portability), Safety (new in 2023). Plus extensions the standard omits: observability, deployability, compliance, cost.

### 3. Commonly-missed categories not elicited

Research lists what LLMs systematically skip: error/exception paths, compliance/regulatory constraints, data retention/migration/deletion, i18n and accessibility, operational concerns (deployment, backup, monitoring, on-call), legal/licensing, and stakeholder roles beyond "the user" (admin, operator, support, auditor, regulator). Phase 4 has no mechanism to surface these.

### 4. Gherkin AC format not used

Research recommends Given/When/Then for acceptance criteria because it doubles as executable spec (Cucumber/SpecFlow/Behave). The current artifact uses `- [ ] checkbox` format — testable in intent but not in form.

### 5. Assumptions as first-class artifact section

Research: "Surface assumptions and dependencies explicitly in a dedicated section rather than burying them in requirement text — this is one of the highest-leverage moves an LLM can make, because it forces the model to externalize what it would otherwise quietly hallucinate." The current artifact has no Assumptions section.

### 6. No self-critique / anti-pattern detection pass

Research recommends a critic pass before presenting the summary:
- Vague-qualifier linter: user-friendly, fast, robust, scalable, etc.
- Compound-requirement detector: requirements with `and`/`or` in the action clause
- Implementation-bias flag: solution-tier requirements leaking into stakeholder requirements

The current skill goes directly from conversation → summary with no quality gate.

---

## Medium-Impact Gaps

### 7. Rationale field missing

Volere's mandatory rationale — the *why* behind each requirement — is absent. Research calls this indispensable for downstream LLM workflows (consistent design decisions). The Overview section captures overall purpose, but there is no per-requirement rationale.

### 8. 5-Whys not applied

Research recommends applying 5-Whys in the clarification phase to surface the underlying business goal. The hypothesize step jumps to *what* without ensuring *why* is understood.

### 9. Numbered options vs. open-ended questions

Research (Santos et al. 2025): "Few-shot prompting with numbered options outperformed free-form prompting by 22.7%." The skill instructs Claude to ask targeted questions but doesn't specify presenting numbered options.

---

## Larger-Scope Gaps (likely intentional simplifications)

### 10. BABOK 4-tier hierarchy not used

Business → Stakeholder → Solution → Transition. The current plugin conflates these into FR/NFR/Domain. Adopting this would force upward traceability and is the research's recommended structural spine.

### 11. Six-part QAS structure for NFRs

Research recommends the SEI ATAM six-part quality attribute scenario (source, stimulus, environment, artifact, response, response measure) for every NFR. This makes NFRs measurable and ADR-derivable. The current NFR section is free-form.

### 12. Atomic files with YAML frontmatter and stable IDs

Research recommends `FR-ORDER-014-cancel-pending-order.md` with full frontmatter (id, type, status, priority, ears_pattern, confidence, traces_from, traces_to, verification_method). The current plugin saves one flat Markdown file per feature.

### 13. Downstream emission (Stage 6) entirely absent

Gherkin `.feature` files, test stubs, ADR backlog, DoD checklist from the same requirements artifact. This is a reasonable scope deferral — it would be its own workflow phase.

---

## Effort Summary

| Gap | Where to fix | Effort |
|---|---|---|
| EARS for FRs | Phase 5 artifact template + Phase 4 guidance | Low |
| ISO 25010 NFR walkthrough | Add as Phase 4 checklist step | Low |
| Commonly-missed categories | Add explicit prompts to Phase 4 | Low |
| Gherkin AC format | Phase 5 artifact template | Low |
| Assumptions section | Phase 5 artifact template | Low |
| Self-critique / anti-pattern pass | Add Phase 4.5 between conversation and summary | Medium |
| Rationale per requirement | Phase 5 artifact template | Low |
| 5-Whys in hypothesis phase | Phase 3 guidance | Low |
| BABOK 4-tier hierarchy | Structural change across all phases | High |
| Six-part QAS for NFRs | Phase 5 artifact template (NFR section) | Medium |
| Atomic files with frontmatter | Phase 5 save step | High |
| Downstream emission | New workflow phase | High |
