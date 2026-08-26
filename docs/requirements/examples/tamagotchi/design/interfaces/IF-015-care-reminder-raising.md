---
id: IF-015
type: interface
title: Care Reminder Raising
description: The contract through which a pet-state evaluation reports the stat movement it caused, so that any neglect-threshold crossing can be turned into a local care reminder.
traces_from: [FR-009, CON-002, CON-003, NFR-005]
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
- name: raise_for_stat_change
  summary: Present a local care reminder for each pet stat that crossed its neglect threshold between the supplied pre-change and post-change stat values, where the owner has enabled reminders.
  interaction: asynchronous
error_modes:
- Reminders are disabled by the owner — nothing is presented and no notification service is contacted at all, which FR-009's zero-notifications-and-zero-network-requests criterion requires.
- The local notification service is unavailable or the OS has denied notification permission — the reminder is dropped rather than retried or queued, since a queued backlog would arrive as a burst at the next launch.
- The owner's reminder preference cannot be read — reminders are treated as disabled, so an unreadable preference can never cause an unwanted notification; the owner-facing surface is told separately through IF-028, so the setting is never displayed as a confident Off on the strength of a failed read.
- Neglect thresholds unavailable — no crossing can be detected and no reminder is raised.
- The same crossing is reported twice by consecutive evaluations — reminded once, because a stat sitting just below its threshold must not produce a reminder on every tick of the cadence.
---

# IF-015 — Care Reminder Raising

The contract through which a pet-state evaluation reports the stat movement it caused, so that
any neglect-threshold crossing can be turned into a local care reminder.

## Operations
- **raise_for_stat_change** — Present a local care reminder for each pet stat that crossed its
  neglect threshold between the supplied pre-change and post-change stat values, where the owner
  has enabled reminders.

## Interaction
Asynchronous, and the choice is close enough to record. The evaluation hands over the crossing
and continues; it does not block on the host notification service, whose latency is outside the
application's control and would otherwise land inside NFR-009's launch window. The cost is that
the evaluation cannot report a reminder failure to anyone — a dropped reminder is invisible to
the path that caused it. Making it synchronous would surface that, at the price of coupling
every launch's timing to the OS notification service. FR-009 is a *should* and reminders are
advisory, which is what tips it: a missed reminder must never delay or fail a pet-state
evaluation.

**Separate from IF-028, the preference contract, deliberately.** CMP-014 provides both, and the
consumer sets are disjoint: the evaluator raises reminders and never touches the setting, and
the owner-facing surface reads and changes the setting and never raises a reminder. They also
differ in interaction — this one is fire-and-forget, and a preference change must be confirmed
durable before the owner is shown a new toggle position. Folding them together would give the
evaluator a setter it has no business holding, which is close to how FR-009's enabled arm came
to be unreachable in the first place.

## Error Modes
- Reminders disabled by the owner — nothing presented, no notification service contacted at all.
- The notification service is unavailable or permission denied — the reminder is dropped rather
  than retried or queued, since a queued backlog arrives as a burst at the next launch.
- The reminder preference cannot be read — treated as disabled here, so an unreadable preference
  can never cause an unwanted notification; the surface learns the difference through IF-028.
- Neglect thresholds unavailable — no crossing detected, no reminder raised.
- The same crossing reported twice by consecutive evaluations — reminded once.

## Rationale
Satisfies CMP-009's declared need to raise warranted care reminders; decay applied during an
evaluation is the only thing that lowers a stat across its threshold. Confidence is medium:
FR-009 is a *should* whose de-duplication window — how long a stat may sit below its threshold
before it is worth reminding again — is fixed by no requirement, and the last error mode above
states the obligation without being able to state its period.
