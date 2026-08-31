---
id: IF-020
type: interface
title: Save File Quarantine Move
description: The platform-adapter contract that moves a save file byte-identically from the local data directory to the quarantine location, preserving it as evidence.
traces_from: [FR-012, NFR-004, NFR-006]
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
provider: CMP-017
operations:
- name: move_to_quarantine
  summary: Move a named file from the application's local data directory to the quarantine location byte-identically, modifying no byte of its contents and leaving no copy at the original path.
  interaction: synchronous
error_modes:
- The quarantine location cannot be resolved or created — the failing file cannot be preserved, so the caller must not go on to initialize a default pet whose own commit would overwrite the evidence.
- A file already exists at the quarantine destination — the move must not overwrite a previously quarantined file, so a distinct destination is required rather than a silent replace.
- The move crosses a filesystem boundary and degrades to copy-then-delete — the copy must be verified byte-identical before the original is removed, or the operation fails with the original left intact.
- Permission denied on the original file — it is left in place unmodified and the quarantine is reported as failed, never as completed.
---

# IF-020 — Save File Quarantine Move

The platform-adapter contract that moves a save file byte-identically from the local data
directory to the quarantine location, preserving it as evidence.

## Operations
- **move_to_quarantine** — Move a named file from the local data directory to the quarantine
  location byte-identically, modifying no byte of its contents and leaving no copy at the
  original path.

## Interaction
Synchronous. FR-012 requires the move to have completed before the default pet is initialized, so
the caller must block on it — an asynchronous move races the default pet's first commit for the
same path.

Separate from IF-019 and IF-025 even though the same adapter provides all three, because the
consumer sets are proper subsets rather than matches: only the pet state store quarantines
anything. Quarantine's failure modes are also unlike any ordinary file failure — a failed
quarantine must stop a launch, where a failed preference write must not.

Distinct from IF-021's `roll_over`, which is the other move-a-file-aside operation in the set:
that one discards its oldest copy by design, and this one must never discard anything.

## Error Modes
- The quarantine location cannot be resolved or created — the file cannot be preserved, so the
  caller must not initialize a default pet.
- A file already exists at the destination — a distinct destination is required rather than a
  silent replace over previously preserved evidence.
- The move degrades to copy-then-delete across a filesystem boundary — the copy is verified
  byte-identical before the original is removed, or the operation fails with the original intact.
- Permission denied on the original — left unmodified, and quarantine reported as failed.

## Rationale
Satisfies CMP-012's declared need to move a failing save file to quarantine. FR-012's fit
criterion counts byte-identical files at the quarantine location and zero files deleted or
overwritten in place, and NFR-006 names this move as one of the two most platform-divergent
operations in the product — which is why it sits in the adapter layer and why NFR-006's acceptance
suite runs it unmodified on all three targets rather than excepting it.
