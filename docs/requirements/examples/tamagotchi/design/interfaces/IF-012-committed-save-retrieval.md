---
id: IF-012
type: interface
title: Committed Save Retrieval
description: The contract through which the launch path asks for the committed pet state and is told which of the two recovery cases applies where none is returned.
traces_from: [FR-010, FR-012, NFR-004, NFR-007, NFR-009]
traces_to:
  adr: [ADR-001, ADR-002, ADR-003, ADR-004]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-012
operations:
- name: retrieve
  summary: 'Return the committed pet state held in the save file, or report which recovery case applies: no save file present, or a file present that failed integrity validation and has already been moved byte-identically to the quarantine location.'
  interaction: synchronous
error_modes:
- No save file is present — reported as its own outcome, with no quarantine artifact created, which FR-010's AC-2 requires explicitly.
- The save file fails integrity validation — reported as its own distinct outcome, and only once the file has been moved byte-identically to quarantine; the caller must not initialize a default pet before that move has completed, or the default pet's own commit would overwrite the evidence (FR-012).
- The quarantine move itself fails — retrieval reports failure rather than a recovery case, because reporting a recovery case would licence the caller to write over a file that was never preserved.
- The file is present but cannot be reached at all — permission denied, device error — reported as an unreadable-state failure and never as no committed state, since NFR-004 forbids falling through to a default pet where a committed state may survive.
---

# IF-012 — Committed Save Retrieval

The contract through which the launch path asks for the committed pet state and is told which
of the two recovery cases applies where none is returned.

## Operations
- **retrieve** — Return the committed pet state held in the save file, or report which recovery
  case applies: no save file present, or a file present that failed integrity validation and has
  already been moved byte-identically to the quarantine location.

## Interaction
Synchronous. NFR-009 measures from the completion of the committed-save read to first render, so
that completion has to be an observable boundary the launch sequence waits on.

One operation with a three-way outcome, rather than a `read` plus a separate `exists`. NFR-004's
discriminating clause rules out any design in which a failed read falls through to the default-pet
path without first establishing that no committed state survives — a two-call shape leaves a
window between the check and the read where exactly that can happen.

## Error Modes
- No save file present — its own outcome, with no quarantine artifact created (FR-010 AC-2).
- The file fails integrity validation — its own outcome, reported only once the file has been
  moved byte-identically to quarantine, so the default pet's commit cannot overwrite the evidence.
- The quarantine move fails — retrieval reports failure rather than a recovery case.
- The file is present but unreachable — reported as an unreadable-state failure, never as absence.

## Rationale
Satisfies CMP-011's declared need to retrieve the committed pet state. FR-010 and FR-012 own
different halves of the recovery space and this operation's outcome is what tells them apart —
which is why the two cases are distinct outcomes rather than one no-state answer.

Separate from IF-013 (commit) even though CMP-012 provides both: see IF-013's Interaction note.
