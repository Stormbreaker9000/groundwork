---
id: IF-002
type: interface
title: beta-query
description: Reads beta state.
traces_from:
  - FR-001
traces_to: {}
status: draft
confidence: medium
created_at: 2026-08-14
provider: CMP-002
operations:
  - name: read_beta
    summary: Return the current beta state.
    interaction: synchronous
error_modes:
  - Beta has not been initialised.
---

# beta-query

Provided by CMP-002, consumed by CMP-001.
