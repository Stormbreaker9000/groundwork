---
id: FR-001
type: functional
tier: solution
title: Apply offline decay on launch
description: When the application starts, the system shall apply the elapsed-time decay to the pet's stat values.
rationale: The pet must age while the application is closed, or the neglect mechanic is meaningless.
fit_criterion: Stat values decay by the modelled rate for every hour of elapsed downtime, within a 1-minute tolerance.
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: "2026-07-13"
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-001 — Apply offline decay on launch
