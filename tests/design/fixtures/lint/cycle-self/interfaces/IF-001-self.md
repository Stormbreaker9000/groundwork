---
id: IF-001
type: interface
title: alpha-query
description: Reads alpha state.
traces_from:
  - FR-001
traces_to: {}
status: draft
confidence: medium
created_at: 2026-08-14
provider: CMP-001
operations:
  - name: read_alpha
    summary: Return the current alpha state.
    interaction: synchronous
error_modes:
  - Alpha has not been initialised.
---

# alpha-query

Provided by CMP-001, which also consumes it.
