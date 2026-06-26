---
id: BR-002
type: business_rule
tier: business
title: Legally retained data is exempt from erasure
description: Personal data subject to a legal retention obligation is exempt from an erasure request until its mandated retention period expires, after which it is deleted.
rationale: GDPR Article 17(3) suspends the right to erasure where processing is necessary for compliance with a legal obligation; encoding which categories are exempt gives the erasure logic a single source of truth.
fit_criterion: 100% of erasure operations preserve data within an active legal-retention window and delete it within 30 days of that window expiring.
priority: must
confidence: high
verification_method: test
status: draft
created_at: 2026-06-26
traces_from: []
traces_to:
  design: []
  tests: []
  code: [FR-002]
scope: project
parent_scope: null
---

# BR-002 — Legally retained data is exempt from erasure

## Statement
Personal data that is subject to a legal retention obligation is exempt from an
erasure request until its mandated retention period expires, after which it is
deleted.

## Implemented by
FR-002 (Permanently delete account and personal data) applies this exemption when
erasing account data.

## Rationale
GDPR Article 17(3) suspends the right to erasure where processing is necessary for
compliance with a legal obligation; the policy encodes which categories are exempt
so the erasure logic has a single source of truth.

## Fit Criterion
100% of erasure operations preserve data within an active legal-retention window
and delete it within 30 days of that window expiring.
