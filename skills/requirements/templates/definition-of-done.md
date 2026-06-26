# Definition of Done — {{FEATURE_NAME}}

**Date:** {{DATE}}
**Status:** Draft (M1 stub)
**Scope:** {{SCOPE}}  <!-- project | epic | story — from the requirements `scope` field; `parent_scope` links a story/epic to its parent -->

> **M1 stub.** This Definition of Done is generated from the requirements set as a
> baseline. It is intentionally partial: the full DoD — architectural fitness
> functions, QA-strategy coverage gates, and complete operational readiness — is
> produced in M3 (STO-104), which expands this file. Do not treat it as complete.

A backlog item or release is **Done** only when every applicable gate below holds.
Each gate references a requirement ID so this checklist stays derivable from
`.sdlc/requirements/`.

## 1. Functional Acceptance Gates
Derived from the Gherkin acceptance criteria of each functional requirement (FR).
- [ ] {{FR_ID}} — {{FR_TITLE}}: all acceptance-criteria scenarios pass.
<!-- one row per FR -->

## 2. Non-Functional Fitness Gates
Derived from each NFR's six-part quality attribute scenario response measure and its
`verification_method`. The response measure is the threshold that must hold.
- [ ] {{NFR_ID}} — {{NFR_TITLE}}: {{NFR_RESPONSE_MEASURE}} (verify by {{NFR_VERIFICATION_METHOD}}).
<!-- one row per NFR -->

## 3. Constraint & Business-Rule Compliance
- [ ] {{CON_OR_BR_ID}} — {{TITLE}}: {{FIT_CRITERION}} holds.
<!-- one row per CON / BR -->

## 4. Test Coverage Expectations
- [ ] Every `must`/`should` FR has at least one automated test mapped to its acceptance criteria.
- [ ] Every NFR with `verification_method: test` has an automated check asserting its response measure.
- [ ] Coverage target met (set per project; default: no `must` requirement left untested).

## 5. Documentation Requirements
- [ ] Requirement artifacts under `.sdlc/requirements/` are updated and internally traceable.
- [ ] User-facing changes are documented (README / changelog / API docs as applicable).

## 6. Deployment / Operational Readiness
- [ ] Build, lint, and the structural requirements validator pass in CI:
      `python3 skills/requirements/scripts/validate_requirements.py .sdlc/requirements`
- [ ] Deployment and rollback path verified for the change.
- [ ] Observability (logs / metrics) is in place for new behavior, where applicable.

## Traceability Note
Gates are generated from the requirement set: a gate with no corresponding
requirement should be removed, and new requirements should add gates here on
regeneration. Constraints and business rules surface as compliance gates via their
`fit_criterion`.
