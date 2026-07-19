---
id: CMP-001
type: component
title: ok
description: A valid component; the fault in this case is the malformed assumptions.md.
traces_from: []
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: reviewed
confidence: high
created_at: 2026-07-18
responsibility: Valid in isolation; used to isolate the assumptions-heading gate.
boundary: internal
depends_on: []
---

# ok

This artifact is valid. This case's `assumptions.md` is missing a required
heading, which is the gate under test.
