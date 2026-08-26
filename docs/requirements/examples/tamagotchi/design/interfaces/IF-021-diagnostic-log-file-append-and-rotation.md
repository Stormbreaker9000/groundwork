---
id: IF-021
type: interface
title: Diagnostic Log File Append and Rotation
description: The platform-adapter contract for appending records to the diagnostic log file, measuring its current size, and rolling it over so the log component can hold total occupancy under the fixed rotation cap NFR-007 requires.
traces_from: [NFR-007, NFR-005, NFR-006]
traces_to:
  adr: [ADR-002, ADR-003]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-017
operations:
- name: append_file
  summary: Append the supplied bytes to a named file within the application's local data directory, creating the file if it is absent, and report the number of bytes actually written.
  interaction: synchronous
- name: file_size
  summary: Return the current size in bytes of a named file within the application's local data directory, or report that no such file is present, so the caller can decide whether its cap has been reached.
  interaction: synchronous
- name: roll_over
  summary: Move a named file aside to a rolled copy, discard the oldest rolled copy beyond the number the caller asks to retain, and leave the original path free for a new file.
  interaction: synchronous
error_modes:
- The local data directory cannot be resolved, or the file cannot be opened for append — no record is written and the caller must account for it as lost.
- The device is full or permission is denied — the append fails, and the caller must not assume the record landed simply because the call returned.
- A partial append leaves a truncated final record — the byte count actually written is reported, so a half-written record can be detected rather than replayed later as though it were whole.
- Concurrent appends from more than one writer interleave mid-record — records must be submitted whole, since a spliced record fails NFR-007's replay with no indication of its cause.
- The roll-over moves the live file aside but the discard of the oldest retained copy fails — total occupancy exceeds the cap until the next successful roll, and the caller is told rather than left believing the cap holds.
- The roll-over cannot move the live file at all — permission denied, or the file is held open elsewhere — and the log stays at its current size; the caller must decide whether to keep appending past the cap or to drop records, and IF-016 chooses to drop.
- The size measured by `file_size` is stale by the time `roll_over` is asked for, because appends continued in between — the cap is therefore enforced approximately and can be exceeded transiently by at most the records written in that gap; NFR-007 requires the log to stay under a cap indefinitely, not at every instant.
---

# IF-021 — Diagnostic Log File Append and Rotation

The platform-adapter contract for appending records to the diagnostic log file, measuring its
current size, and rolling it over so the log component can hold total occupancy under the fixed
rotation cap NFR-007 requires.

## Operations
- **append_file** — Append the supplied bytes to a named file within the local data directory,
  creating it if absent, and report the number of bytes actually written.
- **file_size** — Return the current size in bytes of a named file, or report that no such file
  is present.
- **roll_over** — Move a named file aside to a rolled copy, discard the oldest rolled copy beyond
  the number the caller asks to retain, and leave the original path free.

## Interaction
All three synchronous, which is worth distinguishing from IF-016. Recording an event is
asynchronous to its *caller* — no transition waits on a log write — but the log component itself
must learn whether its bytes landed and how many, because it owns the cap and cannot account for
a file whose size it does not know. The asynchrony is absorbed at IF-016, not pushed down here.
`roll_over` in particular must be synchronous: the next append goes to the path it just freed.

**The rotation half is new, and it closes a real gap rather than adding polish.** Last round this
contract carried `append_file` alone, because append was the whole of the log component's
declared file surface. That left NFR-007's "total log size stays under a fixed rotation cap
indefinitely" with no implementer, and left IF-016's cap-reached path with nowhere to go but
permanent silent record loss — a log that stops describing the pet exactly when the pet has the
longest history to describe. The component set now declares the measuring and rolling capability,
so the operations land here.

The split between measuring and rolling is deliberate. The log component owns the cap and the
decision that it has been reached; the adapter owns the platform-specific file operations. Giving
the adapter a single `append_and_roll_if_over(cap)` would move that policy decision across the
layer boundary and put a balance-like tuning value inside the platform layer, where NFR-006's
conditional-count would then have to follow it.

Separate from IF-019 and IF-025: the diagnostic log is the only consumer of all three operations
here, it never needs an atomic replace, and the save-file and preference consumers never append,
measure or roll. Disjoint consumer sets, so a separate contract.

## Error Modes
- The directory cannot be resolved, or the file cannot be opened for append — no record written.
- Device full or permission denied — the append fails, and a returned call is not evidence the
  record landed.
- A partial append leaves a truncated final record — the byte count written is reported.
- Concurrent appends interleave mid-record — records must be submitted whole.
- The roll moves the live file aside but the discard of the oldest copy fails — occupancy exceeds
  the cap until the next successful roll, and the caller is told.
- The roll cannot move the live file at all — the log stays at its size, and the caller decides
  whether to append past the cap or drop; IF-016 drops.
- The measured size is stale by the time the roll is asked for — the cap is enforced approximately
  and can be exceeded transiently, which is what "under a cap indefinitely" allows and "under a
  cap at every instant" would not.

## Rationale
Satisfies both of CMP-015's file capabilities: appending to the log, and measuring and rolling it
over. One contract for the two because their consumer set is the same single component and the
three operations are used in one sequence — measure, roll if over, append. Confidence is raised to
high this round: the operations now follow directly from NFR-007's two clauses rather than leaving
one of them unimplementable. What NFR-007 does not fix is the cap's value or the number of rolled
copies retained, and both are caller-supplied here rather than assumed.
