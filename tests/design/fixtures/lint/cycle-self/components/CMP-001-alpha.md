---
id: CMP-001
type: component
title: alpha
description: A component that consumes its own contract.
traces_from:
  - FR-001
traces_to: {}
status: draft
confidence: medium
created_at: 2026-08-14
responsibility: Owns the alpha aggregate.
boundary: internal
depends_on:
  - IF-001
---

# alpha

Provides IF-001 and consumes it — a one-component cycle.
