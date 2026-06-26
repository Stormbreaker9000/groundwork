---
id: CON-001
type: constraint
tier: solution
title: Run on Oracle 19c without schema changes
description: >
  The system must operate against the existing Oracle 19c database with no
  schema modifications.
rationale: >
  The shared Oracle instance is governed by a separate DBA team; schema changes
  require a quarterly change-control cycle the project cannot absorb.
fit_criterion: >
  All persistence operations succeed against an unmodified Oracle 19c schema in
  the integration environment.
priority: must
confidence: high
verification_method: inspection
status: approved
created_at: 2026-06-26
traces_from: []
traces_to: {}
---

# CON-001 — Run on Oracle 19c without schema changes

## Description
The system must operate against the existing Oracle 19c database with no schema
modifications. This is a technical/environmental constraint, not a quality
target.
