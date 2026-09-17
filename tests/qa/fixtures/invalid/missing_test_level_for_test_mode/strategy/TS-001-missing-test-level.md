---
id: TS-001
type: test_strategy
title: Missing test level for an executed check
description: verification_mode is test, so test_level is required and absent.
risk_level: medium
risk_rationale: "Exercises the conditional test_level requirement in isolation."
enforcement: ci
verification_mode: test
traces_from: [FR-001]
traces_to:
  tests: []
  code: []
status: draft
confidence: high
created_at: "2026-09-15"
---

# Missing test level for an executed check

Body prose.
