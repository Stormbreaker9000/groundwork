---
id: CON-001
type: constraint
tier: business
title: Statutory-retained financial and tax records survive erasure in pseudonymised, isolated form
description: Financial and tax records subject to a statutory retention period must be preserved through the account-erasure process; they may not be physically deleted while their mandated retention period is active. Preservation must take the form of pseudonymised records held in storage isolated from the active personal-data stores used to serve export and other self-service operations, and this isolation must persist even after the rest of the account and its personal data have been erased.
rationale: Financial and tax record-keeping law imposes a minimum statutory retention period on these records, independent of a data subject's erasure request under GDPR Article 17(3); this constraint exists so that meeting that legal retention obligation does not require the organisation to violate it by deleting the records early. This is a hard boundary on where and in what form data may exist next, not a tunable quality target.
fit_criterion: For every account erased while a financial or tax record is within its statutory retention window, a post-erasure audit finds the record present in pseudonymised form in the isolated retention store and absent from every active personal-data store; 0 such records are found in active stores post-erasure, and 0 are found deleted before their retention window expires.
priority: must
confidence: high
verification_method: inspection
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

# CON-001 — Statutory-retained financial and tax records survive erasure in pseudonymised, isolated form

## Statement
Financial and tax records subject to a statutory retention period must be
preserved through the account-erasure process; they may not be physically
deleted while their mandated retention period is active. Preservation must
take the form of pseudonymised records held in storage isolated from the
active personal-data stores used to serve export and other self-service
operations, and this isolation must persist even after the rest of the
account and its personal data have been erased.

## Category
regulatory

## Bounds / Implemented by
Bounds the erasure behaviour of FR-002 (Erase account and personal data on
confirmed deletion request) by fixing what may and may not be physically
deleted, and fixes the compliance target that NFR-017 (Statutory-retention
compliance of pseudonymised records post-erasure) measures against.

## Rationale
Financial and tax record-keeping law imposes a minimum statutory retention
period on these records, independent of a data subject's erasure request
under GDPR Article 17(3); this constraint exists so that meeting that legal
retention obligation does not require the organisation to violate it by
deleting the records early. This is a hard boundary on where and in what
form data may exist next, not a tunable quality target.

## Fit Criterion
For every account erased while a financial or tax record is within its
statutory retention window, a post-erasure audit finds the record present in
pseudonymised form in the isolated retention store and absent from every
active personal-data store; 0 such records are found in active stores
post-erasure, and 0 are found deleted before their retention window expires.
