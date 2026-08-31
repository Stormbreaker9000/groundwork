---
id: IF-026
type: interface
title: Balance Configuration Load
description: The contract through which the launch sequence causes the balance and tuning parameter set to be read from its configuration source exactly once, so that every parameter read for the rest of the session is served from memory.
traces_from: [FR-010, NFR-001, NFR-008, NFR-009]
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-002
operations:
- name: load
  summary: Read the balance and tuning parameter set from its configuration source and hold it in memory for the remainder of the session, returning once the whole set is available or once the load has definitively failed.
  interaction: synchronous
error_modes:
- The configuration source is missing or unreadable — no parameter set is held, and the launch is abandoned rather than continued against absent balance values; every component that reads a parameter would otherwise fail one at a time, far later than launch and far from the cause.
- The source is present but its contents cannot be parsed — the same outcome, reported distinctly from absence, so that a corrupted or hand-edited configuration is not mistaken for a first run.
- The source parses but carries no parameter set at all — treated as unparseable rather than as a valid empty configuration, because an empty configuration defers the failure to the first reader that needs a value and makes it look like an absent-parameter fault instead of a bad source.
- Load is asked for a second time in the same session — refused rather than re-read, because replacing the parameter set mid-session would change a decay rate underneath a computation already in flight and break NFR-001's comparison against a fixed reference decay model.
- The source is edited while the application runs — not observed at all; the loaded set is the session's set, and Q-1's tuning loop therefore requires a relaunch to take effect.
---

# IF-026 — Balance Configuration Load

The contract through which the launch sequence causes the balance and tuning parameter set to be
read from its configuration source exactly once, so that every parameter read for the rest of the
session is served from memory.

## Operations
- **load** — Read the balance and tuning parameter set from its configuration source and hold it
  in memory for the remainder of the session, returning once the whole set is available or once
  the load has definitively failed.

## Interaction
Synchronous, and ordered. Nothing else in the launch sequence can run before it: the default pet
is built from configured starting values, the decay applied before first display needs the curve,
and the wake test needs the sleep duration. The lifecycle sequencer is the only component
positioned to order this read before its dependants and to abandon the launch if it fails, which
is why it is the only consumer.

**Why this exists as a contract separate from IF-001.** Last round there was only IF-001, and it
carried both the reads and the source-level failures — a missing or unparseable configuration
file — which its provider could not structurally have had, since nothing gave that provider a way
to reach a file. The fix is not to delete the failures, which are real, but to give them a place:
the load happens once, here, and the reads that follow are memory reads, there.

The separation earns its keep against NFR-008 and requirements A-17. Those require the decay computation to be
invocable 1,000 times against an in-memory starting state with no save file read and no
application launch. The decay computation reads `decay_parameters` on each repetition, so if a
parameter read could fall back to loading its source, the constraint would be unmeetable — every
repetition would be a potential file access. Load-once makes the whole transitive read set of
IF-003 file-free, and the fourth failure mode below is what keeps it that way: there is no
reload, so there is no second path to a file.

One operation, and the whole parameter set at once. A per-group load would let a launch proceed
with half a configuration and would multiply the ordering obligations the sequencer has to get
right.

## Error Modes
- The source is missing or unreadable — no set is held and the launch is abandoned.
- The source is present but unparseable — the same outcome, reported distinctly from absence, so a
  corrupt or hand-edited configuration is not mistaken for a first run.
- The source parses but carries no parameter set — treated as unparseable, not as a valid empty
  configuration.
- Load is asked for twice in one session — refused, because a mid-session parameter change would
  move a decay rate underneath a computation in flight.
- The source is edited while the application runs — not observed; Q-1's tuning loop needs a
  relaunch to take effect.

## Rationale
Satisfies CMP-011's declared need to load the balance and tuning parameters into memory.
Confidence is medium: no requirement states that the balance parameters live in a file separate
from the save file, or names their format — that shape is inferred from Q-1's tuning loop being
live and ongoing, and from the requirement set's consistent refusal to fix the values. What is not
inferred is the once-per-session ordering, which NFR-008 forces.
