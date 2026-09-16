---
id: TS-003
type: test_strategy
title: Network egress inspection
description: Enumerates the call sites that reach the network across both components.
test_level: integration
risk_level: high
risk_rationale: "An unnoticed egress path leaks data with no failing test to announce it."
enforcement: manual
verification_mode: inspection
traces_from: [CON-002]
traces_to:
  tests: []
  code: []
status: draft
confidence: high
created_at: "2026-09-15"
---

# Network egress inspection

Body prose. Inspected rather than executed, but genuinely about the boundary
between two components, so it keeps its test_level.
