---
id: NFR-001
type: non_functional
tier: solution
title: Export data completeness across all catalogued data stores
description: Every export archive shall contain the complete personal-data record held for the account across all data stores in the catalogued data map, with no field-level omissions.
rationale: Directly protects the success criterion "100% of export requests yield an archive within 30 days, with a field-level audit confirming 0 omissions across all stores" — an incomplete export fails the Article 20 obligation even if delivered on time.
fit_criterion: A field-level audit of generated export archives against the catalogued data map finds 0 omissions across 100% of data stores, sampled quarterly and on every export-pipeline release.
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

# NFR-001 — Export data completeness across all catalogued data stores

## ISO 25010 Characteristic
Functional Suitability → Functional completeness / correctness

## Quality Attribute Scenario
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

## Rationale
Directly protects the stated success criterion that field-level audits
confirm 0 omissions across all stores; an incomplete export fails the
Article 20 obligation even when delivered inside the 30-day window.
