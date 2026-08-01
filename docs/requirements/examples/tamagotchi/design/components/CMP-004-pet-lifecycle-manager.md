---
id: CMP-004
type: component
title: Pet Lifecycle Manager
description: The state machine that carries a pet from healthy through sick to the terminal dead state, and the timers that decide when each transition is due.
traces_from:
- FR-008
- BR-001
- NFR-007
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: low
created_at: 2026-07-30
scope: project
parent_scope: null
responsibility: Owns the pet's lifecycle state and every transition between its values.
boundary: internal
depends_on:
- IF-001
- IF-002
- IF-005
---

# CMP-004 — Pet Lifecycle Manager

The state machine that carries a pet from healthy through sick to the terminal dead
state, and the timers that decide when each transition is due.

## Responsibility
Owns the pet's lifecycle state and every transition between its values.

## Rationale
FR-008 introduces something continuous Stat arithmetic cannot express: an
irreversible state. Per the Q-2 resolution death is permanent, so no Stat increase
may revive the pet — an asymmetry that a threshold check sitting inside the care
actions cannot enforce, because each action would have to know about every other
one's history. BR-001 sharpens the same point: death depends on a *continuous*
depletion with no intervening care, which is a fact about a timeline rather than
about the current values, so it needs an element that remembers. Placing that
element above the Stat custodian and gating care through it is what makes the
terminal state actually terminal.

This component traces from BR-001 and implements the sustained-neglect threshold
that BR-001's fit criterion defines. BR-001's *statement* additionally says that
upon death the pet is reset to a new pet; that clause is superseded by the Q-2
resolution taken in the design interview — death is permanent, one terminal
lifecycle path, no reset — which is why this machine has no reset transition. That
is not the design overruling a requirement: BR-001's own rationale defers the
clause to Q-2 and holds the rule at low confidence pending it, so what the design
settled was the question BR-001 itself declared open. BR-001's statement text
should be amended upstream to match; that amendment is recorded as an open
question (Q-5) for the requirements owner, and it concerns BR-001's wording rather
than the shape of this state machine.

Confidence is **low** because of open question **Q-1**: the sustained-Neglect,
sickness, and death thresholds are exactly the "thresholds" Q-1 leaves untuned. The
shape of the machine is settled — Q-2's resolution fixed it — but FR-008's
boundary-timing measure cannot be evaluated until the threshold values exist.
