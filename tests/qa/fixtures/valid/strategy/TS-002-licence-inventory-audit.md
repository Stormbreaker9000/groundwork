---
id: TS-002
type: test_strategy
title: Licence inventory audit
description: Enumerates every bundled dependency's licence against the permitted set.
risk_level: high
risk_rationale: "A non-permitted licence is silent until it is legally expensive, and no runtime signal reveals it."
enforcement: manual
verification_mode: inspection
traces_from: [CON-001]
traces_to:
  tests: []
  code: []
status: draft
confidence: high
created_at: "2026-09-15"
---

# Licence inventory audit

Body prose. No test_level: the audit crosses no component boundary.
