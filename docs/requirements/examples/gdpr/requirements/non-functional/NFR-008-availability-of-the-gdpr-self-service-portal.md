---
id: NFR-008
type: non_functional
tier: solution
title: Availability of the GDPR self-service portal
description: The export and deletion request-submission endpoints shall achieve at least 99.9% monthly availability for authenticated data subjects to initiate requests.
rationale: GDPR Articles 20 and 17 give the data subject a right to exercise at a time of their choosing, and this set provides only one path to do so — self-service, with no operator or admin fallback described anywhere in the brief. An unavailable submission endpoint is an unavailable statutory right, so the portal's availability target is set high despite the brief not stating a figure itself.
fit_criterion: '>= 99.9% monthly availability (<= ~43 minutes downtime/month, excluding announced maintenance windows) for the export and deletion request-submission endpoints, measured via uptime monitoring over a rolling monthly window.'
priority: should
confidence: low
verification_method: test
status: draft
created_at: '2026-08-26'
traces_from:
- FR-001
- FR-002
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-008 — Availability of the GDPR self-service portal

## ISO 25010 Characteristic
Reliability → Availability

## Quality Attribute Scenario
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

## Rationale
GDPR Articles 20 and 17 give the data subject a right to exercise at
a time of their choosing, and this set provides only one path to do
so — self-service, with no operator or admin fallback described
anywhere in the brief. An unavailable submission endpoint is an
unavailable statutory right, so the portal's availability target is
set high despite the brief not stating a figure itself.
