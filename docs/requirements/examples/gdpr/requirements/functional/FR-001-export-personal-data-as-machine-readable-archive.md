---
id: FR-001
type: functional
tier: solution
title: Export personal data as machine-readable archive
description: When an authenticated user submits a request to export their personal data, the system shall generate a machine-readable archive containing all personal data held for their account within 30 days of the request.
rationale: GDPR Article 20 grants a data subject the right to receive their personal data in a portable format; self-service export discharges this legal obligation directly and reduces the volume of manual data-subject-access-request handling.
fit_criterion: 100% of export requests produce a downloadable archive within 30 days of submission; a field-level audit of each generated archive against the catalogued data map confirms 0 omitted fields, checked across a sample of test accounts spanning every data store in scope.
priority: must
confidence: high
verification_method: test
ears_pattern: event
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

# FR-001 — Export personal data as machine-readable archive

## Description
When an authenticated user submits a request to export their personal data,
the system shall generate a machine-readable archive containing all personal
data held for their account within 30 days of the request.

## Rationale
GDPR Article 20 grants a data subject the right to receive their personal
data in a portable format; self-service export discharges this legal
obligation directly and reduces the volume of manual
data-subject-access-request handling.

## Acceptance Criteria
### AC-1 — Successful export request
```gherkin
Given an authenticated user with personal data held across the system's
  catalogued data stores
When the user submits a request to export their personal data
Then the system generates a machine-readable archive containing all of
  that personal data
And the archive is made available to the user within 30 days of the request
```

### AC-2 — Archive completeness across all data stores
```gherkin
Given an authenticated user whose personal data spans multiple catalogued
  data stores
When the export archive is generated for that user's request
Then a field-level audit of the archive against the catalogued data map
  finds 0 omitted fields
```

## Fit Criterion
100% of export requests produce a downloadable archive within 30 days of
submission; a field-level audit of each generated archive against the
catalogued data map confirms 0 omitted fields, checked across a sample of
test accounts spanning every data store in scope.
