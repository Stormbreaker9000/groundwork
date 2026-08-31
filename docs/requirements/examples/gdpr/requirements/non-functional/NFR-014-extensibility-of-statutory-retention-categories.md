---
id: NFR-014
type: non_functional
tier: solution
title: Extensibility of statutory retention categories
description: The retention-override mechanism that isolates records from erasure shall support adding a new regulated record type as a retention category without changes to core deletion logic.
rationale: 'Open question Q-2 ("Which regulated record types override erasure, beyond financial?" — owner: legal) signals the retention-category set is not yet finalized and may grow; the mechanism should be adaptable rather than hard-coded to the currently-known financial/tax category.'
fit_criterion: Adding a new statutory-retention record type is achievable via configuration/data rather than core deletion-logic changes, verified via analysis of the retention-category mechanism.
priority: should
confidence: low
verification_method: analysis
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

# NFR-014 — Extensibility of statutory retention categories

## ISO 25010 Characteristic
Flexibility → Adaptability

## Quality Attribute Scenario
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

## Rationale
This is a direct consequence of open question Q-2: since the
retention-category list is explicitly unresolved and owned by legal
rather than product/engineering, the architecture should not assume the
list is fixed at launch.
