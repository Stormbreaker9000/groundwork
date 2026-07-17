---
id: FR-001
type: functional
tier: solution
title: Export all personal data on request
description: When an authenticated user submits a data-export request, the system shall make available a machine-readable archive containing all personal data held for that user within 30 days of the request.
rationale: GDPR Article 20 (right to data portability) entitles a data subject to receive their personal data in a structured, commonly used, machine-readable format; self-service export discharges this legal obligation and reduces manual data-subject-access-request handling.
fit_criterion: 100% of data-export requests yield an archive within 30 days, and a field-level audit confirms the archive contains every personal-data field held for the user across all stores (0 omissions).
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: 2026-06-26
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-001 — Export all personal data on request

## Description
When an authenticated user submits a data-export request, the system shall make
available a machine-readable archive containing all personal data held for that
user within 30 days of the request.

## Rationale
GDPR Article 20 (right to data portability) entitles a data subject to receive
their personal data in a structured, commonly used, machine-readable format.
Providing self-service export discharges this legal obligation and reduces manual
data-subject-access-request handling.

## Acceptance Criteria
### AC-1 — Export includes all personal data across stores
```gherkin
Given an authenticated user with personal data in the profile, orders, and activity-log stores
When the user submits a data-export request
Then the system produces a machine-readable archive within 30 days
And the archive contains the user's personal data from every store that holds it
```

### AC-2 — Export is delivered in a portable format
```gherkin
Given a completed data-export request
When the user opens the generated archive
Then the data is provided in a structured, machine-readable format (JSON or CSV)
```

## Fit Criterion
100% of data-export requests yield an archive within 30 days, and a field-level
audit confirms the archive contains every personal-data field held for the user
across all stores (0 omissions).
