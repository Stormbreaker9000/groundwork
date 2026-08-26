---
id: IF-028
type: interface
title: Care Reminder Preference
description: The contract through which the owner-facing surface reads the owner's care-reminder setting and changes it — the "enabled by the owner" precondition FR-009 hangs its whole behaviour on.
traces_from: [FR-009, CON-002, NFR-003, NFR-005]
traces_to:
  adr: [ADR-002]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-014
operations:
- name: read_preference
  summary: Return whether the owner has enabled care reminders, or report that no preference has ever been set, so the surface can show the real setting rather than a guess.
  interaction: synchronous
- name: set_preference
  summary: Record the owner's choice to enable or disable care reminders and return once that choice is durable, so the setting the surface shows is one that will survive the session.
  interaction: synchronous
error_modes:
- No preference has ever been set — reported as its own outcome and treated as disabled, because FR-009's reminders are opt-in and a default-on reminder is a notification the owner never asked for.
- The preference cannot be read — reported to the surface as unreadable rather than as disabled, so the owner is not shown a confident Off for a setting that was never established; the raising path treats the same failure as disabled, which is the safe reading there and the wrong one here.
- The change cannot be made durable because the atomic replace failed — the change is reported as not saved and the surface must not move the control, since a toggle that shows On and silently reverts at the next launch is worse than one that refuses.
- Reminders are enabled but the host has denied the application notification permission — the preference is set and no reminder can ever be delivered; the surface must be able to tell the owner, because an enabled toggle that produces nothing is indistinguishable from a broken feature.
- The preference is changed while an evaluation is mid-flight — the reminder that evaluation raises may reflect either setting; FR-009 is a should and one reminder either side of a toggle is accepted rather than serialized against the evaluation cadence.
---

# IF-028 — Care Reminder Preference

The contract through which the owner-facing surface reads the owner's care-reminder setting and
changes it — the "enabled by the owner" precondition FR-009 hangs its whole behaviour on.

## Operations
- **read_preference** — Return whether the owner has enabled care reminders, or report that no
  preference has ever been set.
- **set_preference** — Record the owner's choice and return once it is durable.

## Interaction
Both synchronous. `read_preference` because the surface cannot draw a control whose position it
does not know. `set_preference` because durability is the point: FR-009's condition outlives the
session that set it, and an owner who toggles reminders on and finds them off at the next launch
has been lied to by the control. The cost is that the owner's toggle blocks on a file write; it is
a single small file and a deliberate owner action, which is the opposite of the recurring hot path
where that cost would matter.

**Its own contract, not an operation on IF-015.** Both are provided by the reminder service, so
merging was the question. The consumer sets are disjoint — IF-015's consumer is the pet-state
evaluator, which raises reminders and has no business changing the owner's settings, and this
one's is the presentation shell, which never raises a reminder. They differ in interaction as
well: raising is fire-and-forget, and a preference change must be confirmed durable. Merging would
have put a setter in the evaluator's dependency surface, which is uncomfortably close to how
FR-009's enabled arm became unreachable in the first place.

**What this fixes.** FR-009 reads "Where care-reminder notifications are enabled by the owner",
and until this round nothing in the design could enable them. IF-015 read the effect of the
preference, IF-015's own failure mode treated an unreadable preference as disabled, and no
operation anywhere set it — so the never-writable default was permanently off and FR-009's enabled
arm was unreachable by construction. The feature validated as a design and could not have shipped
working.

Note the deliberate asymmetry in the second failure mode: an unreadable preference is *disabled*
to the raising path and *unreadable* to the surface. Treating it as disabled is the safe default
where the consequence is an unwanted notification; it is the wrong default where the consequence
is showing the owner a setting they never chose.

## Error Modes
- No preference has ever been set — its own outcome, treated as disabled, because FR-009's
  reminders are opt-in.
- The preference cannot be read — reported as unreadable to the surface, disabled to the raising
  path.
- The change cannot be made durable — reported as not saved, and the control must not move.
- Enabled while the host denies notification permission — set, undeliverable, and the owner must
  be able to be told.
- Changed mid-evaluation — the reminder that evaluation raises may reflect either setting; FR-009
  is a should and this is accepted rather than serialized.

## Rationale
Satisfies CMP-016's declared need to read and change the owner's care-reminder preference. The
preference belongs to the feature it gates rather than to the surface that displays it, which is
why the provider is the reminder service and not the shell. Confidence is medium: FR-009 is a
*should* and states nothing about where the control lives, how the owner reaches it, or whether
the preference survives a save-file quarantine — the last of which is why it is assumed to live in
its own file rather than inside the pet state.
