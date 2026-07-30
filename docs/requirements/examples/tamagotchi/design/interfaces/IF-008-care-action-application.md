---
id: IF-008
type: interface
title: Care Action Application
description: The contract through which an owner's selected care action is applied to the pet's Stats, and the only way any Stat value is allowed to increase.
traces_from:
- FR-003
- FR-004
- FR-005
- FR-006
- NFR-003
- BR-001
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: 2026-07-30
scope: project
parent_scope: null
provider: CMP-003
operations:
- name: apply_care_action
  summary: Apply one owner-selected care action — feed, play, clean, or begin sleep — to the pet's Stats, reporting whether it was applied, refused, or had no effect.
- name: end_sleep
  summary: End an in-progress sleep interaction, crediting energy in proportion to the fraction of the configured duration that elapsed.
interaction: synchronous
error_modes:
- Action refused because the pet is in the terminal dead state — death is permanent per the Q-2 resolution, so no care action may restore a Stat and the caller must be told rather than shown an unchanged value.
- Action applied but the Stat was already at its maximum — the caller must be able to tell this apart from a refusal, because the two mean different things to the owner and to NFR-003's accessible feedback.
- Action arrives while a sleep interaction is in progress — the caller must be told whether it was refused, queued, or interrupted the sleep, because FR-006 gives an interrupted sleep a different outcome from a completed one.
- Timeout with unknown commit state — the action may or may not have been applied and may or may not have been persisted, so the caller must re-read the current Stats rather than retrying blindly and double-feeding.
---

# IF-008 — Care Action Application

The contract through which an owner's selected care action is applied to the pet's
Stats, and the only way any Stat value is allowed to increase.

## Operations
- **apply_care_action** — Apply one owner-selected care action — feed, play, clean, or
  begin sleep — to the pet's Stats, reporting whether it was applied, refused, or had
  no effect.
- **end_sleep** — End an in-progress sleep interaction, crediting energy in proportion
  to the fraction of the configured duration that elapsed.

## Interaction
Synchronous, and worth stating why, because the alternative is defensible. The window
already learns the new Stat values over IF-005, so the action could be fire-and-forget
with the result arriving as a change notification — which would keep the IPC hop off
the click path. It is synchronous because an action can be *refused*: a dead pet
(BR-001, Q-2) or a sleep already in progress produces no stat change at all, so a
consumer waiting for a change notification would wait forever and show the owner
nothing. NFR-003 makes that concrete — a keyboard-operated control has to announce an
outcome. What would tip it is a refusal being modelled as its own notification; the
cost would be an outcome channel that has to be correlated back to the click.

## Error Modes
- Action refused because the pet is in the terminal dead state — death is permanent per
  the Q-2 resolution, so no care action may restore a Stat and the caller must be told
  rather than shown an unchanged value.
- Action applied but the Stat was already at its maximum — the caller must be able to
  tell this apart from a refusal, because the two mean different things to the owner
  and to NFR-003's accessible feedback.
- Action arrives while a sleep interaction is in progress — the caller must be told
  whether it was refused, queued, or interrupted the sleep, because FR-006 gives an
  interrupted sleep a different outcome from a completed one.
- Timeout with unknown commit state — the action may or may not have been applied and
  may or may not have been persisted, so the caller must re-read the current Stats
  rather than retrying blindly and double-feeding.

## Rationale
Satisfies CMP-006's declared need to apply an owner's care action. FR-003 to FR-006 are
all triggered by the owner selecting feed, play, clean, or sleep, and CON-001 puts the
simulation on the native side of the process boundary, so the window captures the
selection and this contract carries it across. Keeping mutation on its own interface,
separate from IF-005's read-only observation, is what makes CMP-003 the single
authority over Stat values.

This contract traces from BR-001 and enforces the terminal end of the
sustained-neglect threshold BR-001's fit criterion defines: past that threshold the
pet is dead and every care action is refused. BR-001's *statement* additionally
says that upon death the pet is reset to a new pet; that clause is superseded by
the Q-2 resolution taken in the design interview — death is permanent, one terminal
lifecycle path, no reset — which is why this contract offers a refusal mode and no
reset operation. That is not the design overruling a requirement: BR-001's own
rationale defers the clause to Q-2 and holds the rule at low confidence pending it,
so what the design settled was the question BR-001 itself declared open. BR-001's
statement text should be amended upstream to match; that amendment is recorded as
an open question (Q-5) for the requirements owner, and it concerns BR-001's wording
rather than the shape of this contract.
