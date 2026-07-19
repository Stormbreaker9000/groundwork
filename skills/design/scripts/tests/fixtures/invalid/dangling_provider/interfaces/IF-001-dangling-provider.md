---
id: IF-001
type: interface
title: dangling-provider
description: An interface whose provider component does not exist in the set.
traces_from: []
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: low
created_at: 2026-07-18
provider: CMP-999
operations:
  - name: ping
    summary: A single trivial operation.
interaction: synchronous
error_modes:
  - unreachable
---

# dangling-provider

`provider: CMP-999` — no such component exists in this set.
