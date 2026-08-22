---
id: CMP-002
type: component
title: beta
description: The other half of a mutual dependency.
traces_from:
  - FR-001
traces_to: {}
status: draft
confidence: medium
created_at: 2026-08-14
responsibility: Owns the beta aggregate.
boundary: internal
depends_on:
  - IF-001
---

# beta

Consumes IF-001, which CMP-001 provides. Get this direction backwards and there
is no cycle to find — CMP-001 consumes IF-002 (provided by CMP-002), CMP-002
consumes IF-001 (provided by CMP-001).
