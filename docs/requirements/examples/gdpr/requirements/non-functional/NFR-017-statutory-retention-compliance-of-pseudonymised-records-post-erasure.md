---
id: NFR-017
type: non_functional
tier: solution
title: Statutory-retention compliance of pseudonymised records post-erasure
description: Financial and tax records within their mandated retention period shall be preserved only in pseudonymised form, isolated from active personal-data stores, after account erasure, in conformance with applicable statutory retention obligations.
rationale: 'Directly enforces the stated constraint: "Statutory retention overrides erasure: financial and tax records within their mandated retention period must be preserved in pseudonymised form, isolated from active personal-data stores, even after the account is erased."'
fit_criterion: 100% of retained records post-erasure are pseudonymised and stored outside active personal-data stores; a compliance audit confirms conformance with the documented statutory retention rules, with 0 exceptions.
priority: must
confidence: high
verification_method: inspection
status: draft
created_at: '2026-08-26'
traces_from:
- CON-001
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-017 — Statutory-retention compliance of pseudonymised records post-erasure

## ISO 25010 Characteristic
Extension: Compliance

## Quality Attribute Scenario
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

## Rationale
This is the single point where the two legal obligations in scope
(Article 17 erasure and statutory financial/tax retention) directly
conflict; getting this wrong either violates erasure or violates
retention law, so it is treated as a `must` with high confidence
given the brief states it as a hard constraint.
