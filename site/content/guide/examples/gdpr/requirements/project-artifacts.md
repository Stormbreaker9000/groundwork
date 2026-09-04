<!--
  GENERATED FILE — do not edit.
  Source: docs/requirements/examples/gdpr/requirements/
  Regenerate: python3 site/scripts/export_examples.py
-->

# Project artifacts

The stage-level files that sit alongside the atomic artifacts: the vocabulary they are written in, what was assumed, and what is still open.
## Glossary [#glossary]

### Terms
- **Confirmation window**: The 24-hour period after a deletion request is submitted during which the data subject must complete step-up re-authentication; if it lapses unconfirmed, the request auto-cancels with no data mutation.
- **Data map**: The organisation's already-catalogued inventory of where personal data is stored across its data stores; export and erasure coverage is scoped to this catalogue, and data outside it is out of scope. *Also: catalogued data map.*
- **Data subject**: The identified or identifiable natural person whose personal data the system holds and who exercises the GDPR rights (export, erasure) these requirements implement.
- **Erasure**: The permanent, irreversible removal of a data subject's personal data from all active personal-data stores, excluding data preserved under an active statutory-retention exemption. *Also: deletion.*
- **Personal data**: Any information relating to an identified or identifiable data subject, held by the system in any of its catalogued data stores (see Data map).
- **Pseudonymisation**: Processing personal data such that it can no longer be attributed to a specific data subject without additional, separately-held information; used here to retain statutory-retained records after account erasure while limiting re-identification.
- **Statutory retention**: A legal obligation to continue retaining (and, in this set, pseudonymising and isolating) a data subject's personal data for a defined period notwithstanding an erasure request; this set's only identified instance is financial and tax records, though the category is not necessarily limited to those (see open question Q-2). *Also: legal retention obligation.*
- **Statutory retention set**: The subset of a data subject's records that fall under an active statutory-retention obligation at a given time, and are therefore exempt from erasure until that obligation expires. *Also: retention set, retention category.*
- **Step-up re-authentication**: A stronger, additional authentication challenge performed via the existing identity provider immediately before an irreversible action (here, confirming account deletion), distinct from ordinary session authentication. *Also: re-authentication.*

## Assumptions [#assumptions]

### Assumptions
- A-1: The existing identity provider's step-up re-authentication flow returns a discrete, system-observable "confirmed" event that can be correlated to a specific pending deletion request within the 24-hour confirmation window.
- A-2: "Personal data held for the account" is fully and accurately described by the already-catalogued data map; data outside that map is out of scope for export and erasure.
- A-3: The 30-day windows for both export generation and deletion completion are measured as elapsed calendar time from the triggering event (request or confirmation timestamp), not business days.
- A-4: Only one deletion request can be pending confirmation for a given account at a time; behavior for a second deletion request submitted while one is already pending is undefined by this set.
- A-5: A p95 export-turnaround target of 72 hours (NFR-003) is an assumed interim engineering target, not a confirmed figure, pending Q-1.
- A-6: WCAG 2.2 Level AA (NFR-007) is assumed as the applicable accessibility standard for the export/deletion self-service flows; no accessibility law or target was stated in the elicited context.
- A-7: A monthly availability target of >= 99.9% (NFR-008) is assumed for the request-submission endpoints; no SLA was stated in the elicited context.
- A-8: AES-256 (or an equivalent industry-standard algorithm) is assumed for export-archive encryption at rest, and a 72-hour download-link expiry window is assumed (NFR-010); the elicited context specifies the encryption and time-limited-link mechanism but not the algorithm or exact duration.
- A-9: A 5-day margin before the 30-day statutory ceiling is assumed as the alerting threshold for at-risk requests (NFR-015); no specific early-warning window was stated.
- A-10: Financial and tax records are assumed not necessarily to be the complete list of statutory-retention categories (NFR-014, CON-001, BR-002); the set may need to grow pending Q-2's answer from legal.
- A-11: Pseudonymisation of statutorily-retained financial/tax records (CON-001) is assumed to meet the bar GDPR Article 17(3)(b) sets for putting data beyond ordinary processing use, without requiring a separate legal sign-off step in-system.
- A-12: BR-002's retention exemption is assumed to apply per-record (or per-record-category) — only the specific statutory-retention records are held back from FR-002's erasure, not the account as a whole.
- A-13: No retention period was specified for the tamper-evident audit log (NFR-012) in the elicited context; retention is assumed indefinite, with no automated deletion, until superseded by a future retention policy, pending Q-3.

### Dependencies
- D-1: A durable object store must be available to hold generated export archives before FR-001 and NFR-010 can be implemented and verified.
- D-2: The existing identity provider must expose a step-up re-authentication flow before FR-003 and NFR-011 can be implemented and verified; no new authentication mechanism is to be built.
- D-3: The already-catalogued data map must be complete and accurate — NFR-001's and NFR-002's completeness measures are bounded by, and only as good as, that catalogue.
- D-4: Legal's finalized enumeration of statutory-retention record types beyond financial and tax (open question Q-2) is needed to fully verify FR-002's fit criterion, to finalize NFR-014's and NFR-017's compliance scope, and may require broadening BR-002 and CON-001 beyond financial/tax records.
- D-5: Product's answer to the maximum acceptable export turnaround (open question Q-1) is needed to replace NFR-003's assumed 72-hour target with a confirmed figure.

### Open Questions
- Q-1: What is the maximum acceptable turnaround for an export request? (The 30-day statutory ceiling in FR-001 is fixed and not in question; this asks for the practical operational target within that ceiling — currently assumed as a 72-hour p95 in NFR-003 — pending this answer.) (owner: product)
- Q-2: Which regulated record types override erasure, beyond financial? (owner: legal)
- Q-3: What is the required/legally mandated retention period for the tamper-evident export/deletion audit log (NFR-012)? No retention duration for this log was stated in the elicited context. (owner: legal)

## Definition of done [#definition-of-done]

> **M1 STUB** — generated by the `dod-generator` agent from the requirements in
> `.sdlc/requirements/`. This is a foundational checklist; **M3 (STO-104)**
> expands it into the full Definition of Done generator. Edit the source
> requirement files (not this file) and regenerate to keep gates in sync.

- **Project / feature:** GDPR Data Export & Account Deletion
- **Generated:** 2026-08-26
- **Derived from:** 3 functional + 15 non-functional requirements
- **Scope:** project (`scope` / `parent_scope` reserved for future agile slicing — STO-104)

A work item is **Done** only when **every** gate below is satisfied. Gates are
derived mechanically from the requirement set: do not hand-edit; update the
source requirement and regenerate.

### 1. Functional Acceptance Gates
*Derived from each functional requirement's EARS description, Gherkin acceptance
criteria, and `fit_criterion`. One gate per FR; the linked file holds the
authoritative, executable acceptance criteria.*

- [ ] **FR-001 — Export personal data as machine-readable archive** (must): all acceptance-criteria scenarios in
  `.sdlc/requirements/functional/FR-001-export-personal-data-as-machine-readable-archive.md` pass.
  Fit criterion: 100% of export requests produce a downloadable archive within 30 days of submission; a field-level audit of each generated archive against the catalogued data map confirms 0 omitted fields, checked across a sample of test accounts spanning every data store in scope.
  Verification: test.

- [ ] **FR-002 — Erase account and personal data on confirmed deletion request** (must): all acceptance-criteria scenarios in
  `.sdlc/requirements/functional/FR-002-erase-account-and-personal-data-on-confirmed-deletion-request.md` pass.
  Fit criterion: For 100% of confirmed deletion requests sampled in acceptance testing, a data audit conducted on or before day 30 after confirmation finds 0 personal-data records for the account outside the documented statutory-retention set, and 100% of authentication attempts against the deleted account fail.
  Verification: test.

- [ ] **FR-003 — Cancel unconfirmed account deletion request within 24-hour window** (must): all acceptance-criteria scenarios in
  `.sdlc/requirements/functional/FR-003-cancel-unconfirmed-account-deletion-request-within-24-hour-window.md` pass.
  Fit criterion: 100% of deletion requests left unconfirmed for 24 hours are automatically cancelled with 0 mutations to account state or personal data; 0 accounts are deleted without a corresponding recorded re-authentication event within the 24-hour window.
  Verification: test.

### 2. NFR Fitness Gates
*Derived from each non-functional requirement's six-part quality attribute
scenario (QAS). The **response measure** is the pass/fail oracle; the
`verification_method` is how it is confirmed.*

- [ ] **NFR-001 — Export data completeness across all catalogued data stores** (must): meets response measure —
  A field-level audit finds 0 omissions across 100% of data stores, sampled quarterly and on every export-pipeline release.
  — for the QAS *Submits a data export request* on *Export generation subsystem*
  under *Normal operation, spanning every data store in the already-catalogued data map*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-001-export-data-completeness-across-all-catalogued-data-stores.md`.

- [ ] **NFR-002 — Erasure completeness excluding statutory-retention records** (must): meets response measure —
  A data audit finds 0 personal-data records outside the documented statutory-retention set; 100% of authentication attempts against the deleted account fail.
  — for the QAS *Confirms a deletion request via re-authentication* on *Erasure processing subsystem across all catalogued personal-data stores*
  under *Normal operation, after the erasure process completes*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-002-erasure-completeness-excluding-statutory-retention-records.md`.

- [ ] **NFR-003 — Export generation time under normal load** (must): meets response measure —
  p95 turnaround <= 72 hours; 100% of exports available within the 30-day statutory ceiling, measured over a rolling 30-day window.
  — for the QAS *Submits a request to export their personal data* on *Export generation service and the durable object store holding generated archives (D-1)*
  under *Normal operating load, export-worker utilisation <= 80%*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-003-export-generation-time-under-normal-load.md`.

- [ ] **NFR-005 — Export archive format interoperability** (should): meets response measure —
  100% of archives validate against the published schema via automated validation and open successfully in standard tooling during verification testing.
  — for the QAS *Downloads and opens the export archive* on *Export archive format and its published specification*
  under *Normal operation, using common third-party tooling (archive utilities, JSON/CSV parsers)*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-005-export-archive-format-interoperability.md`.

- [ ] **NFR-006 — User error protection for irreversible account deletion** (must): meets response measure —
  100% of deletion initiations require the distinct acknowledgment step; 0 deletion requests are queued without both the acknowledgment and the re-authentication event recorded.
  — for the QAS *Initiates account deletion* on *Deletion request UI/flow*
  under *Normal operation, self-service deletion flow*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-006-user-error-protection-for-irreversible-account-deletion.md`.

- [ ] **NFR-007 — Accessibility of export and deletion self-service flows** (should): meets response measure —
  0 critical violations, verified by automated scan plus manual screen-reader and keyboard-only walkthrough.
  — for the QAS *Navigates the export or deletion self-service flow, including the re-authentication step-up and the irreversibility-acknowledgment step* on *Export and deletion self-service UI flow*
  under *Normal operation, any supported assistive technology*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-007-accessibility-of-export-and-deletion-self-service-flows.md`.

- [ ] **NFR-008 — Availability of the GDPR self-service portal** (should): meets response measure —
  >= 99.9% monthly availability, measured via uptime monitoring over a rolling monthly window.
  — for the QAS *Attempts to submit an export or deletion request* on *Export and deletion request-submission API endpoints*
  under *Normal operation, any hour (self-service, no business-hours restriction implied by the brief)*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-008-availability-of-the-gdpr-self-service-portal.md`.

- [ ] **NFR-009 — Fault tolerance and recovery of export generation** (should): meets response measure —
  >= 99% of transient failures resolved within 3 retry attempts; 100% of affected requests still complete within the 30-day ceiling, verified via fault-injection testing.
  — for the QAS *One or more source stores fail to respond during archive assembly* on *Export generation pipeline*
  under *Normal operation, no sustained outage*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-009-fault-tolerance-and-recovery-of-export-generation.md`.

- [ ] **NFR-010 — Confidentiality of exported personal-data archives** (must): meets response measure —
  100% of archives encrypted at rest (assumed AES-256 or equivalent); links expire within an assumed 72-hour window; 0 unauthorized retrievals across access-control and penetration testing.
  — for the QAS *Attempts to access or intercept the export archive or its download link* on *Export archive and its download link*
  under *Normal operation, archive at rest in the durable object store and in transit during download*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-010-confidentiality-of-exported-personal-data-archives.md`.

- [ ] **NFR-011 — Deletion requires fresh re-authentication and auto-cancels if unconfirmed** (must): meets response measure —
  0 accounts deleted without a recorded re-authentication event in the prior 24 hours; 100% of unconfirmed requests auto-cancelled with no data mutation.
  — for the QAS *A deletion request is submitted, with or without a subsequent step-up re-authentication event* on *Deletion confirmation flow and its integration with the existing identity provider's step-up re-authentication capability*
  under *Normal operation, within or beyond the 24-hour confirmation window*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-011-deletion-requires-fresh-re-authentication-and-auto-cancels-if-unconfirmed.md`.

- [ ] **NFR-012 — Tamper-evident audit logging of export and deletion events** (must): meets response measure —
  100% of lifecycle events captured with actor, timestamp, and outcome; entries are immutable/tamper-evident; no automated deletion occurs absent a defined retention policy (open question Q-3); verified via log-integrity inspection and a sample compliance audit.
  — for the QAS *A request is created, confirmed, cancelled, or completed* on *Audit logging subsystem for export/deletion events*
  under *Normal operation*.
  Verification: inspection.
  Source: `.sdlc/requirements/non-functional/NFR-012-tamper-evident-audit-logging-of-export-and-deletion-events.md`.

- [ ] **NFR-014 — Extensibility of statutory retention categories** (should): meets response measure —
  The addition is achievable via configuration/data rather than core deletion-logic changes, verified via mechanism analysis.
  — for the QAS *Identifies a new regulated record type (beyond financial/tax) that must override erasure* on *Retention-override / pseudonymisation-and-isolation mechanism*
  under *Normal operation, outside of an active deletion incident*.
  Verification: analysis.
  Source: `.sdlc/requirements/non-functional/NFR-014-extensibility-of-statutory-retention-categories.md`.

- [ ] **NFR-015 — Monitoring and alerting on requests approaching the statutory deadline** (should): meets response measure —
  100% of requests within an assumed 5-day margin of the ceiling trigger an alert, verified via test; 0 silent breaches.
  — for the QAS *An export or deletion request is still open as it nears the 30-day statutory ceiling* on *Monitoring/alerting pipeline over export and deletion request state*
  under *Normal operation*.
  Verification: test.
  Source: `.sdlc/requirements/non-functional/NFR-015-monitoring-and-alerting-on-requests-approaching-the-statutory-deadline.md`.

- [ ] **NFR-016 — Safe deployment and rollback without corrupting in-flight requests** (could): meets response measure —
  0 jobs left in an inconsistent state, verified via a deployment/rollback demonstration under simulated in-flight load.
  — for the QAS *A deployment or rollback occurs while export/deletion jobs are in-flight* on *Export generation and erasure processing pipelines and their deployment mechanism*
  under *Normal release activity*.
  Verification: demonstration.
  Source: `.sdlc/requirements/non-functional/NFR-016-safe-deployment-and-rollback-without-corrupting-in-flight-requests.md`.

- [ ] **NFR-017 — Statutory-retention compliance of pseudonymised records post-erasure** (must): meets response measure —
  100% of retained records are pseudonymised and isolated; a compliance audit finds 0 exceptions against the documented retention rules.
  — for the QAS *An account with financial/tax records under mandated retention is erased* on *Retention-isolation and pseudonymisation mechanism*
  under *Normal operation*.
  Verification: inspection.
  Source: `.sdlc/requirements/non-functional/NFR-017-statutory-retention-compliance-of-pseudonymised-records-post-erasure.md`.

### 3. Test Coverage Expectations
- [ ] Every `must` / `should` FR above has at least one automated test mapped to
  its acceptance criteria (Gherkin → executable test), recorded in the FR's
  `traces_to.tests`.
- [ ] Every NFR with `verification_method: test` has an automated fitness check
  asserting its QAS response measure: NFR-001, NFR-002, NFR-003, NFR-005, NFR-006, NFR-007, NFR-008, NFR-009, NFR-010, NFR-011, NFR-015.
- [ ] NFRs with `verification_method` of `inspection` / `analysis` /
  `demonstration` have a recorded, signed-off evidence artifact: NFR-012, NFR-014, NFR-016, NFR-017.
- [ ] No FR/NFR marked `must` remains without a corresponding test or evidence
  link (no dangling `traces_to`). **Flagged as currently unmet:** every requirement
  in this set has an empty `traces_to.tests`, including all `must`-priority
  requirements — FR-001, FR-002, FR-003, NFR-001, NFR-002, NFR-003, NFR-006,
  NFR-010, NFR-011, NFR-012, NFR-017, BR-001, BR-002, CON-001.

### 4. Documentation Requirements
- [ ] Public-facing behavior described by `must` FRs is documented (user/API
  docs as applicable): FR-001, FR-002, FR-003.
- [ ] Operational NFRs (security, reliability, observability, deployability) have
  runbook / config notes: NFR-008 (reliability), NFR-009 (reliability),
  NFR-010 (security), NFR-011 (security), NFR-012 (observability),
  NFR-015 (observability), NFR-016 (deployability).
- [ ] `.sdlc/requirements/` is current: every implemented requirement has
  `status: implemented` (or `verified`) and populated `traces_to.code`.
- [ ] Architecture-significant decisions are captured as ADRs referenced from the
  relevant requirements' `traces_to.design`.

### 5. Deployment / Operational Readiness
- [ ] Security NFR gates pass before release: NFR-010, NFR-011, NFR-012.
- [ ] Reliability / availability NFR targets are met or have an accepted waiver:
  NFR-008, NFR-009.
- [ ] Observability is in place (logs / metrics / traces) for the response
  measures asserted above.
- [ ] Applicable constraints (`CON-*`) and business rules (`BR-*`) are honored in
  the deployed configuration: CON-001, BR-001, BR-002.
- [ ] Rollback / cutover path exists for any transition-tier requirement.

---
*This file is generated. Do not edit by hand — change the requirement files in
`.sdlc/requirements/` and re-run the `dod-generator` agent. M3 (STO-104) will
replace this stub with scope-aware, CI-enforceable gates.*
