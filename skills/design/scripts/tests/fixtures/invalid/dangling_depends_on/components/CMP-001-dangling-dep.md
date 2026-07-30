---
id: CMP-001
type: component
title: dangling-dep
description: A component that depends on an interface which does not exist in the set.
traces_from: []
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: low
created_at: 2026-07-18
responsibility: Declares a dependency on a non-existent interface.
boundary: internal
depends_on:
  - IF-999
---

# dangling-dep

`depends_on: [IF-999]` — no such interface exists in this set.
