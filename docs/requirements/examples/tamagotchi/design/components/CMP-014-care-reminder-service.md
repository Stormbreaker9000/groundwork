---
id: CMP-014
type: component
title: Care Reminder Service
description: The optional care-reminder feature in full — the owner's enablement preference, the rule that decides when a pet stat's crossing of its neglect threshold warrants a reminder, and the request that presents it.
traces_from: [FR-009, NFR-005, CON-002, CON-003]
traces_to:
  adr: [ADR-002]
  diagrams: [DIA-003]
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Owns the optional care-reminder feature, from the owner's enablement of it through to the reminder it raises.
boundary: internal
depends_on: [IF-001, IF-019, IF-022, IF-025]
---

# CMP-014 — Care Reminder Service

The optional care-reminder feature in full — the owner's enablement preference, the rule
that decides when a pet stat's crossing of its neglect threshold warrants a reminder,
and the request that presents it.

## Responsibility
Owns the optional care-reminder feature, from the owner's enablement of it through to
the reminder it raises.

## Rationale
FR-009 is the only requirement that crosses the process boundary out of the
application, and it is the one place a "local" delivery mechanism could quietly acquire
a network dependency, which CON-002 forbids outright and NFR-005 measures at the
network interface. Isolating the feature — its enablement, its trigger rule and its
request for delivery — makes the "zero notifications and zero network requests when the
feature is disabled" half of its fit criterion a property of one component.

The threshold comparison lives here rather than in the evaluator so that FR-009's
trigger and CMP-005's neglect clock read the same configured thresholds without either
owning the other's rule.

FR-009's condition is not "reminders are on" but "enabled by the owner", which means the
preference needs a writer the owner can reach, not only a reader the trigger consults. It
is owned here — alongside the trigger it gates — and read and changed through this
component by the owner-facing surface, which is the only element an owner acts on. Without
that edge the preference would be permanently at its default and FR-009's enabled arm
would be unreachable by any owner action, which the fit criterion tests both halves of.
The default itself is off: an absent or unreadable preference file is treated as disabled,
so the feature can never surprise an owner who has not asked for it.

Confidence is medium: FR-009 is a should-priority requirement, and no requirement in the
digest states where the owner's reminder preference is persisted, so this component's
ownership of that setting remains an assumption even though its writer is now named.
