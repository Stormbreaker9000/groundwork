# Definition of Done — GDPR Data Export & Account Deletion

**Date:** 2026-06-26
**Status:** Draft (M1 stub)
**Scope:** project  <!-- project | epic | story — from the requirements `scope` field; `parent_scope` links a story/epic to its parent -->

> **M1 stub.** This Definition of Done is generated from the requirements set as a
> baseline. It is intentionally partial: the full DoD — architectural fitness
> functions, QA-strategy coverage gates, and complete operational readiness — is
> produced in M3 (STO-104), which expands this file. Do not treat it as complete.

A backlog item or release is **Done** only when every applicable gate below holds.
Each gate references a requirement ID so this checklist stays derivable from
`.sdlc/requirements/`.

## 1. Functional Acceptance Gates
Derived from the Gherkin acceptance criteria of each functional requirement (FR).
- [ ] FR-001 — Export all personal data on request: all acceptance-criteria scenarios pass.
- [ ] FR-002 — Permanently delete account and personal data: all acceptance-criteria scenarios pass.
- [ ] FR-003 — Require re-authentication before account deletion: all acceptance-criteria scenarios pass.

## 2. Non-Functional Fitness Gates
Derived from each NFR's six-part quality attribute scenario response measure and its
`verification_method`. The response measure is the threshold that must hold.
- [ ] NFR-001 — Confidentiality of exported personal-data archives: archives encrypted with AES-256 at rest, download links require the requesting user's authenticated session and expire within 24 hours, and a penetration test finds 0 archives retrievable without authentication (verify by test).
- [ ] NFR-002 — Data export generation time under normal load: 95% of export requests for accounts holding <= 1 GB complete and become available within 1 hour, and 100% complete within the 30-day legal ceiling (verify by test).

## 3. Constraint & Business-Rule Compliance
- [ ] CON-001 — Statutory retention of financial records overrides erasure: for every deleted account with financial records in the statutory window, those records remain retrievable in pseudonymised form for the full period and a compliance inspection finds 0 unlawful early deletions.
- [ ] BR-001 — Account deletion is irreversible: after deletion completes, no administrative or automated path restores the erased data and a recovery attempt in testing succeeds 0% of the time.
- [ ] BR-002 — Legally retained data is exempt from erasure: 100% of erasure operations preserve data within an active legal-retention window and delete it within 30 days of that window expiring.

## 4. Test Coverage Expectations
- [ ] Every `must`/`should` FR has at least one automated test mapped to its acceptance criteria.
- [ ] Every NFR with `verification_method: test` has an automated check asserting its response measure (NFR-001, NFR-002).
- [ ] Coverage target met (set per project; default: no `must` requirement left untested).

## 5. Documentation Requirements
- [ ] Requirement artifacts under `.sdlc/requirements/` are updated and internally traceable.
- [ ] User-facing changes are documented (README / changelog / API docs as applicable), including the irreversibility notice surfaced to users before deletion.

## 6. Deployment / Operational Readiness
- [ ] Build, lint, and the structural requirements validator pass in CI:
      `python3 skills/requirements/scripts/validate_requirements.py .sdlc/requirements`
- [ ] Deployment and rollback path verified for the change.
- [ ] Observability (logs / metrics) is in place for new behavior, where applicable — including audit logging of export and deletion events.

## Traceability Note
Gates are generated from the requirement set: a gate with no corresponding
requirement should be removed, and new requirements should add gates here on
regeneration. Constraints and business rules surface as compliance gates via their
`fit_criterion`.
