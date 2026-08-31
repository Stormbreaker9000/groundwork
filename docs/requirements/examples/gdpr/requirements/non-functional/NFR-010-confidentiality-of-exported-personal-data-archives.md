---
id: NFR-010
type: non_functional
tier: solution
title: Confidentiality of exported personal-data archives
description: Generated export archives shall be encrypted at rest and retrievable only via an authenticated, time-limited download link scoped to the requesting user.
rationale: 'Explicit non-functional concern in the brief: "Confidentiality of the exported personal-data archive (encryption at rest, authenticated time-limited download links)." A full personal-data export is a concentrated, high-value target and requires stronger protection than the source records scattered across separate stores.'
fit_criterion: 100% of export archives are encrypted at rest using an industry-standard algorithm (assumed AES-256 or equivalent, not specified in the brief); download links expire within an assumed 72-hour window and are rejected for any user other than the requester in 100% of access-control test cases, with 0 unauthorized retrievals in penetration testing.
priority: must
confidence: high
verification_method: test
status: draft
created_at: '2026-08-26'
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-010 — Confidentiality of exported personal-data archives

## ISO 25010 Characteristic
Security → Confidentiality

## Quality Attribute Scenario
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

## Rationale
A completed export is the single largest concentration of a data
subject's personal data the system ever produces; encryption at rest
plus scoped, time-limited links are the two controls the brief calls
out explicitly to prevent that concentration from becoming a breach
vector.
