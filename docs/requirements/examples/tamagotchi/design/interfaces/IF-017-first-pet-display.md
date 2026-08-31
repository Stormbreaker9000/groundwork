---
id: IF-017
type: interface
title: First Pet Display
description: The contract through which the pet is displayed for the first time in a session, completing at the first render that closes NFR-009's measurement window.
traces_from: [FR-002, FR-007, FR-011, NFR-003, NFR-009]
traces_to:
  adr: [ADR-002, ADR-003]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-016
operations:
- name: present_initial
  summary: Display the pet for the first time in this session from the live pet state, returning when the first render has completed — the closing boundary of the window NFR-009 measures from the completion of the committed-save read.
  interaction: synchronous
error_modes:
- First render cannot complete because no rendering surface is available — the launch sequence has no closing boundary to measure NFR-009 against and must report the failure rather than proceed as though the pet were displayed.
- The live pet state cannot be read at the moment of first display — nothing is drawn and the launch fails, rather than an empty pet being shown; a blank first render is the one frame the owner is guaranteed to see.
- The pet's mood expression or health status has no textual equivalent to announce — the state is not perceivable to a screen-reader user at the moment they first meet the pet, which NFR-003 counts as a failure rather than a degradation.
- Called more than once in a session — refused; a second first render would reopen a measurement window NFR-009 defines as closing once, and the recurring redraw is IF-030's job.
- 'The pet is displayed before decay has been applied — not a failure this contract can detect, and named here because FR-002 makes the ordering the launch sequence''s obligation: this operation renders whatever the live pet state holds when it is called.'
---

# IF-017 — First Pet Display

The contract through which the pet is displayed for the first time in a session, completing at
the first render that closes NFR-009's measurement window.

## Operations
- **present_initial** — Display the pet for the first time in this session from the live pet
  state, returning when the first render has completed.

## Interaction
Synchronous, and that is the whole reason this contract exists apart from IF-030. NFR-009
defines its measurement window as ending at first render, which is only expressible if first
render is an event the launch sequence causes and can observe completing. It happens once per
session; its ordering after decay is FR-002's requirement rather than a preference; and a first
render that fails fails the launch.

**This contract used to carry the recurring redraw as well, and should not have.** The previous
round bundled `present_initial` and `refresh` because CMP-009 and CMP-011 had declared the same
capability string, and the exactly-once rule left no way to split them from the interface layer.
That was recorded as a finding rather than resolved, and the component set has since split the
capability in two. The halves are now what they always were: disjoint consumers, opposed
interaction modes, and opposed failure semantics — a failed first render must fail the launch,
while a failed redraw must not fail the evaluation that asked for it. IF-030 carries the other
half.

Drawing and announcing are not done here. This contract decides *that* the pet is displayed and
when; the platform work of painting a surface and exposing status text to a native accessibility
stack goes through IF-027, inside the adapter layer NFR-006 names.

## Error Modes
- No rendering surface available — reported, because NFR-009's window has no closing boundary.
- The live pet state cannot be read at first display — nothing is drawn and the launch fails,
  rather than an empty pet being shown.
- A mood expression or health status has no textual equivalent to announce — a failure under
  NFR-003, not a degradation.
- Called more than once in a session — refused; the recurring redraw is IF-030's job.
- The pet is displayed before decay has been applied — undetectable here, and named because
  FR-002 makes the ordering the launch sequence's obligation.

## Rationale
Satisfies CMP-011's declared need to display the pet for the first time in this session.
Confidence is medium: Q-8 (still_open) asks whether the Sleeping state is rendered to the owner.
The operation survives either answer — the Awake/Sleeping field is already part of pet state —
but what the first render is obliged to show and announce does not.
