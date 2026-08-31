---
id: CMP-006
type: component
title: Sleep Cycle
description: The owner of the Awake/Sleeping state field and the sleep-entry timestamp, including entry into the Sleeping state and the elapsed-duration wake deadline with its re-basing rule.
traces_from: [FR-001, FR-006, FR-011, NFR-007]
traces_to:
  adr: []
  diagrams: [DIA-003]
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Owns the pet's Awake/Sleeping transitions and the sleep-entry timestamp they turn on.
boundary: internal
depends_on: [IF-001, IF-016, IF-018]
---

# CMP-006 — Sleep Cycle

The owner of the Awake/Sleeping state field and the sleep-entry timestamp, including
entry into the Sleeping state and the elapsed-duration wake deadline with its
re-basing rule.

## Responsibility
Owns the pet's Awake/Sleeping transitions and the sleep-entry timestamp they turn on.

## Rationale
FR-011 introduces a second, incompatible non-positive-interval rule alongside FR-002's
(requirements A-6): a deadline re-bases its origin where a quantity merely clamps. Two rules over
the same clock reading mean the clock contract cannot expose a single "elapsed since"
and be done — the discriminator has to live somewhere the design names, and this is
that place for the deadline half. The clock contract this component consumes therefore
returns a signed interval and applies neither rule.

Entry is idempotent per FR-006's fit criterion, and requirements A-8 fixes that there is no
owner-initiated wake: the pet leaves Sleeping only on elapsed sleep duration, tested at
launch before display and on the running cadence. Sleep does not alter stat decay, so
nothing here touches CMP-004.
