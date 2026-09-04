<!--
  GENERATED FILE — do not edit.
  Source: docs/requirements/examples/gdpr/requirements/non-functional/
  Regenerate: python3 site/scripts/export_examples.py
-->

# Non-functional requirements

The 15 non-functional requirements from the `gdpr` worked example, exactly as the pipeline wrote them.

## NFR-001 — Export data completeness across all catalogued data stores [#nfr-001]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | high |
| Verification | test |

### ISO 25010 Characteristic
Functional Suitability → Functional completeness / correctness

### Quality Attribute Scenario
- **Source of stimulus:** Authenticated data subject.
- **Stimulus:** Submits a data export request.
- **Environment:** Normal operation, spanning every data store in the
  already-catalogued data map.
- **Artifact:** Export generation subsystem.
- **Response:** The generated archive contains every personal-data field
  held for the account across all catalogued stores.
- **Response measure:** A field-level audit finds 0 omissions across
  100% of data stores, sampled quarterly and on every export-pipeline
  release.

### Rationale
Directly protects the stated success criterion that field-level audits
confirm 0 omissions across all stores; an incomplete export fails the
Article 20 obligation even when delivered inside the 30-day window.

## NFR-002 — Erasure completeness excluding statutory-retention records [#nfr-002]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | high |
| Verification | test |

### ISO 25010 Characteristic
Functional Suitability → Functional correctness

### Quality Attribute Scenario
- **Source of stimulus:** Authenticated data subject.
- **Stimulus:** Confirms a deletion request via re-authentication.
- **Environment:** Normal operation, after the erasure process completes.
- **Artifact:** Erasure processing subsystem across all catalogued
  personal-data stores.
- **Response:** All personal data is removed except pseudonymised
  statutory-retention records isolated from active stores; the account's
  credentials no longer authenticate.
- **Response measure:** A data audit finds 0 personal-data records
  outside the documented statutory-retention set; 100% of authentication
  attempts against the deleted account fail.

### Rationale
Directly protects the stated success criteria for post-deletion audit
results and authentication failure — the measurable definition of "the
account is actually gone."

## NFR-003 — Export generation time under normal load [#nfr-003]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | low |
| Verification | test |
| Traces from | [FR-001](/guide/examples/gdpr/requirements/functional/#fr-001) |

### ISO 25010 Characteristic
Performance Efficiency → Time behavior

### Quality Attribute Scenario
- **Source of stimulus:** Authenticated data subject.
- **Stimulus:** Submits a request to export their personal data.
- **Environment:** Normal operating load, export-worker utilisation
  <= 80%.
- **Artifact:** Export generation service and the durable object
  store holding generated archives (D-1).
- **Response:** The export archive is generated and made available
  for download via an authenticated link (see NFR-001).
- **Response measure:** p95 turnaround <= 72 hours; 100% of exports
  available within the 30-day statutory ceiling, measured over a
  rolling 30-day window.

### Rationale
FR-001 commits to a 30-day statutory ceiling for data portability
requests, but the brief leaves the practical turnaround target open
(Q-1, owner: product). A 72-hour p95 budget is an interim
engineering target that keeps the self-service export experience
responsive well inside the legal ceiling while product confirms the
real requirement, so design and capacity planning have a concrete
number to build to rather than stalling on the open question.

## NFR-005 — Export archive format interoperability [#nfr-005]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | should |
| Status | draft |
| Confidence | medium |
| Verification | test |

### ISO 25010 Characteristic
Compatibility → Interoperability

### Quality Attribute Scenario
- **Source of stimulus:** Authenticated data subject (or a downstream
  tool acting on their behalf).
- **Stimulus:** Downloads and opens the export archive.
- **Environment:** Normal operation, using common third-party tooling
  (archive utilities, JSON/CSV parsers).
- **Artifact:** Export archive format and its published specification.
- **Response:** The archive opens and parses correctly without
  proprietary software.
- **Response measure:** 100% of archives validate against the published
  schema via automated validation and open successfully in standard
  tooling during verification testing.

### Rationale
Portability under Article 20 is only meaningful if the receiving party
(the data subject or another controller) can actually consume the data;
an undocumented or proprietary format would satisfy the letter of
"machine-readable" while failing its intent.

## NFR-006 — User error protection for irreversible account deletion [#nfr-006]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | medium |
| Verification | test |

### ISO 25010 Characteristic
Interaction Capability → User error protection

### Quality Attribute Scenario
- **Source of stimulus:** Authenticated data subject.
- **Stimulus:** Initiates account deletion.
- **Environment:** Normal operation, self-service deletion flow.
- **Artifact:** Deletion request UI/flow.
- **Response:** The system presents an explicit irreversibility warning
  and requires a distinct confirmation, separate from the
  re-authentication step, before the request is queued.
- **Response measure:** 100% of deletion initiations require the
  distinct acknowledgment step; 0 deletion requests are queued without
  both the acknowledgment and the re-authentication event recorded.

### Rationale
Because "no administrative or automated path restores erased data,"
the interaction design carries real weight in preventing accidental,
unrecoverable harm — this is the interaction-layer counterpart to the
security-layer re-authentication control (NFR-011).

## NFR-007 — Accessibility of export and deletion self-service flows [#nfr-007]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | should |
| Status | draft |
| Confidence | low |
| Verification | test |
| Traces from | [FR-001](/guide/examples/gdpr/requirements/functional/#fr-001), [FR-002](/guide/examples/gdpr/requirements/functional/#fr-002), [FR-003](/guide/examples/gdpr/requirements/functional/#fr-003) |

### ISO 25010 Characteristic
Interaction Capability → Accessibility / Inclusivity

### Quality Attribute Scenario
- **Source of stimulus:** Authenticated data subject using assistive
  technology (e.g. screen reader, keyboard-only navigation).
- **Stimulus:** Navigates the export or deletion self-service flow,
  including the re-authentication step-up and the
  irreversibility-acknowledgment step.
- **Environment:** Normal operation, any supported assistive
  technology.
- **Artifact:** Export and deletion self-service UI flow.
- **Response:** All flow steps, including re-authentication and the
  irreversibility acknowledgment, are operable and perceivable via
  assistive technology per WCAG 2.2 AA success criteria.
- **Response measure:** 0 critical violations, verified by automated
  scan plus manual screen-reader and keyboard-only walkthrough.

### Rationale
Export and deletion are the only two capabilities this set gives the
data subject, and both are exercised through self-service UI with no
operator fallback (no admin/support role is described anywhere in
the brief). A data subject who cannot perceive or operate the flow —
including the re-authentication step-up (FR-003) and the
irreversibility acknowledgment (BR-001) — is functionally denied a
statutory right with no alternate path, so accessibility conformance
is load-bearing rather than cosmetic.

## NFR-008 — Availability of the GDPR self-service portal [#nfr-008]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | should |
| Status | draft |
| Confidence | low |
| Verification | test |
| Traces from | [FR-001](/guide/examples/gdpr/requirements/functional/#fr-001), [FR-002](/guide/examples/gdpr/requirements/functional/#fr-002) |

### ISO 25010 Characteristic
Reliability → Availability

### Quality Attribute Scenario
- **Source of stimulus:** Authenticated data subject.
- **Stimulus:** Attempts to submit an export or deletion request.
- **Environment:** Normal operation, any hour (self-service, no
  business-hours restriction implied by the brief).
- **Artifact:** Export and deletion request-submission API
  endpoints.
- **Response:** The endpoint accepts and begins processing the
  request.
- **Response measure:** >= 99.9% monthly availability, measured via
  uptime monitoring over a rolling monthly window.

### Rationale
GDPR Articles 20 and 17 give the data subject a right to exercise at
a time of their choosing, and this set provides only one path to do
so — self-service, with no operator or admin fallback described
anywhere in the brief. An unavailable submission endpoint is an
unavailable statutory right, so the portal's availability target is
set high despite the brief not stating a figure itself.

## NFR-009 — Fault tolerance and recovery of export generation [#nfr-009]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | should |
| Status | draft |
| Confidence | medium |
| Verification | test |

### ISO 25010 Characteristic
Reliability → Fault tolerance / recoverability

### Quality Attribute Scenario
- **Source of stimulus:** A transient failure (e.g., data-store
  timeout) during export generation.
- **Stimulus:** One or more source stores fail to respond during
  archive assembly.
- **Environment:** Normal operation, no sustained outage.
- **Artifact:** Export generation pipeline.
- **Response:** The pipeline retries and recovers, producing one
  correct archive with no data loss or duplication.
- **Response measure:** >= 99% of transient failures resolved within 3
  retry attempts; 100% of affected requests still complete within the
  30-day ceiling, verified via fault-injection testing.

### Rationale
Because export completeness is audited at the field level (NFR-001), a
failure that silently drops a store's contribution rather than
retrying would produce an incomplete archive that still "succeeds" —
fault tolerance closes that gap.

## NFR-010 — Confidentiality of exported personal-data archives [#nfr-010]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | high |
| Verification | test |

### ISO 25010 Characteristic
Security → Confidentiality

### Quality Attribute Scenario
- **Source of stimulus:** An unauthorized third party (attacker,
  another authenticated user, or an actor with a leaked link).
- **Stimulus:** Attempts to access or intercept the export archive or
  its download link.
- **Environment:** Normal operation, archive at rest in the durable
  object store and in transit during download.
- **Artifact:** Export archive and its download link.
- **Response:** The archive remains encrypted at rest and unreadable
  without authorization; the download link is honored only for the
  requesting, authenticated user and only within its validity window.
- **Response measure:** 100% of archives encrypted at rest (assumed
  AES-256 or equivalent); links expire within an assumed 72-hour
  window; 0 unauthorized retrievals across access-control and
  penetration testing.

### Rationale
A completed export is the single largest concentration of a data
subject's personal data the system ever produces; encryption at rest
plus scoped, time-limited links are the two controls the brief calls
out explicitly to prevent that concentration from becoming a breach
vector.

## NFR-011 — Deletion requires fresh re-authentication and auto-cancels if unconfirmed [#nfr-011]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | high |
| Verification | test |

### ISO 25010 Characteristic
Security → Authenticity / non-repudiation

### Quality Attribute Scenario
- **Source of stimulus:** Authenticated data subject, or an attacker
  operating a hijacked or unattended session.
- **Stimulus:** A deletion request is submitted, with or without a
  subsequent step-up re-authentication event.
- **Environment:** Normal operation, within or beyond the 24-hour
  confirmation window.
- **Artifact:** Deletion confirmation flow and its integration with the
  existing identity provider's step-up re-authentication capability.
- **Response:** Deletion executes only if a step-up re-authentication
  event is recorded within the window; otherwise the request is
  automatically cancelled and the account/data are left unchanged.
- **Response measure:** 0 accounts deleted without a recorded
  re-authentication event in the prior 24 hours; 100% of unconfirmed
  requests auto-cancelled with no data mutation.

### Rationale
Because deletion is irreversible with no recovery path, the
re-authentication gate is the last checkpoint against an attacker with
a stolen session, or a user's own accidental click, triggering
permanent account loss.

## NFR-012 — Tamper-evident audit logging of export and deletion events [#nfr-012]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | low |
| Verification | inspection |

### ISO 25010 Characteristic
Security → Accountability / non-repudiation

### Quality Attribute Scenario
- **Source of stimulus:** Any actor (data subject, identity provider
  callback, or system scheduler) causing an export or deletion
  lifecycle event.
- **Stimulus:** A request is created, confirmed, cancelled, or
  completed.
- **Environment:** Normal operation.
- **Artifact:** Audit logging subsystem for export/deletion events.
- **Response:** The event is written to an immutable, tamper-evident
  log entry, independent of the account's own data.
- **Response measure:** 100% of lifecycle events captured with actor,
  timestamp, and outcome; entries are immutable/tamper-evident; no
  automated deletion occurs absent a defined retention policy (open
  question Q-3); verified via log-integrity inspection and a sample
  compliance audit.

### Rationale
After erasure, the account's own records are gone by design; the audit
log is the only remaining evidence that the process was followed
correctly (re-authentication occurred, retention rules were applied),
which is exactly what a regulator or internal auditor would ask to see.
No retention duration for this log is specified anywhere in the
elicited context, so no duration is asserted here; entries are kept
indefinitely by default until legal defines the actual required
retention period (Q-3).

## NFR-014 — Extensibility of statutory retention categories [#nfr-014]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | should |
| Status | draft |
| Confidence | low |
| Verification | analysis |

### ISO 25010 Characteristic
Flexibility → Adaptability

### Quality Attribute Scenario
- **Source of stimulus:** Legal/compliance function.
- **Stimulus:** Identifies a new regulated record type (beyond
  financial/tax) that must override erasure.
- **Environment:** Normal operation, outside of an active deletion
  incident.
- **Artifact:** Retention-override / pseudonymisation-and-isolation
  mechanism.
- **Response:** The new record type is added as a retention category
  and honored by the erasure pipeline.
- **Response measure:** The addition is achievable via
  configuration/data rather than core deletion-logic changes, verified
  via mechanism analysis.

### Rationale
This is a direct consequence of open question Q-2: since the
retention-category list is explicitly unresolved and owned by legal
rather than product/engineering, the architecture should not assume the
list is fixed at launch.

## NFR-015 — Monitoring and alerting on requests approaching the statutory deadline [#nfr-015]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | should |
| Status | draft |
| Confidence | medium |
| Verification | test |

### ISO 25010 Characteristic
Extension: Observability

### Quality Attribute Scenario
- **Source of stimulus:** Clock / scheduled monitoring job.
- **Stimulus:** An export or deletion request is still open as it nears
  the 30-day statutory ceiling.
- **Environment:** Normal operation.
- **Artifact:** Monitoring/alerting pipeline over export and deletion
  request state.
- **Response:** Operations receives an alert identifying the at-risk
  request before the ceiling is breached.
- **Response measure:** 100% of requests within an assumed 5-day margin
  of the ceiling trigger an alert, verified via test; 0 silent
  breaches.

### Rationale
The 100%-within-30-days success criterion is a compliance-critical
target with no tolerance; achieving it in practice requires visibility
into at-risk requests early enough for a human to intervene, not only
an after-the-fact audit. This inference sits directly beneath a fixed,
high-confidence legal constraint (FR-001's 30-day ceiling) rather than
a speculative failure mode absent from the brief — unlike NFR-016's
deployment-safety inference — which is why it is held at medium rather
than low confidence.

## NFR-016 — Safe deployment and rollback without corrupting in-flight requests [#nfr-016]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | could |
| Status | draft |
| Confidence | low |
| Verification | demonstration |

### ISO 25010 Characteristic
Extension: Deployability

### Quality Attribute Scenario
- **Source of stimulus:** Engineering team performing a release.
- **Stimulus:** A deployment or rollback occurs while export/deletion
  jobs are in-flight.
- **Environment:** Normal release activity.
- **Artifact:** Export generation and erasure processing pipelines and
  their deployment mechanism.
- **Response:** In-flight jobs either complete safely or resume
  cleanly after the release; none are left partially applied.
- **Response measure:** 0 jobs left in an inconsistent state, verified
  via a deployment/rollback demonstration under simulated in-flight
  load.

### Rationale
Given that deletion is irreversible and has no recovery path, a
release-induced partial deletion would be indistinguishable from a
severe data-integrity incident; deployability safeguards are the
operational counterpart to the functional atomicity implied by
NFR-002.

## NFR-017 — Statutory-retention compliance of pseudonymised records post-erasure [#nfr-017]

| Field | Value |
| --- | --- |
| Type | non_functional |
| Tier | solution |
| Priority | must |
| Status | draft |
| Confidence | high |
| Verification | inspection |
| Traces from | [CON-001](/guide/examples/gdpr/requirements/constraints/#con-001) |

### ISO 25010 Characteristic
Extension: Compliance

### Quality Attribute Scenario
- **Source of stimulus:** Erasure process, at the point statutory
  retention records are separated from the deletion target.
- **Stimulus:** An account with financial/tax records under mandated
  retention is erased.
- **Environment:** Normal operation.
- **Artifact:** Retention-isolation and pseudonymisation mechanism.
- **Response:** The regulated records are pseudonymised and moved to
  storage isolated from active personal-data stores; all other
  personal data is erased.
- **Response measure:** 100% of retained records are pseudonymised and
  isolated; a compliance audit finds 0 exceptions against the
  documented retention rules.

### Rationale
This is the single point where the two legal obligations in scope
(Article 17 erasure and statutory financial/tax retention) directly
conflict; getting this wrong either violates erasure or violates
retention law, so it is treated as a `must` with high confidence
given the brief states it as a hard constraint.
