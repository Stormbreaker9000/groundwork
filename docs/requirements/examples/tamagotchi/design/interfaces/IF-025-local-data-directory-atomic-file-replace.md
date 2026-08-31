---
id: IF-025
type: interface
title: Local Data Directory Atomic File Replace
description: The platform-adapter contract for replacing a file inside the application's local data directory as one atomic operation, so an interrupted write never leaves a partially written file where the previous one stood.
traces_from: [FR-001, FR-009, NFR-004, NFR-005, NFR-006]
traces_to:
  adr: [ADR-002, ADR-003, ADR-004]
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
- name: replace_file_atomically
  summary: Replace a named file within the application's local data directory with the supplied bytes as one atomic operation — written to a temporary file and renamed into place — so that an interrupted write never leaves a partially written file where the previous one stood.
  interaction: synchronous
error_modes:
- The temporary file is written but the rename fails — the previously committed file remains in place, byte for byte, and the caller is told the replacement did not take effect.
- The local data directory cannot be resolved or created on this platform — nothing can be written, and the application has no system of record for this session.
- Permission denied, or the device is full — no bytes are replaced and the existing file is left untouched.
- The rename is not atomic on this platform or filesystem — the guarantee NFR-004 rests on is absent, an interrupted write can leave a torn file, and FR-012's quarantine path becomes the primary defence rather than the fallback; the condition is not detectable from inside this contract.
- The process is terminated between the temporary write and the rename — the previous file stands unmodified and the temporary file is left behind, which the next replace must be able to overwrite rather than treat as an obstruction.
---

# IF-025 — Local Data Directory Atomic File Replace

The platform-adapter contract for replacing a file inside the application's local data directory
as one atomic operation, so an interrupted write never leaves a partially written file where the
previous one stood.

## Operations
- **replace_file_atomically** — Replace a named file with the supplied bytes as one atomic
  operation — written to a temporary file and renamed into place.

## Interaction
Synchronous. Atomicity is only useful to a caller that learns whether the replace took effect;
NFR-004 turns on exactly that distinction, and FR-009's preference toggle turns on a weaker version
of it — an owner must not be shown a saved setting that never reached disk.

**Split out of IF-019 this round.** The two were one contract while their consumer sets matched.
The balance configuration now reads from the local data directory and never writes to it, so the
read's consumers are a strict superset of the replace's, and a merged contract would hand CMP-002
an atomic-replace operation it must never call. This is the Interface Segregation test applied to
a subset rather than to a disjoint pair, and it is the same test that keeps IF-020 and IF-021
separate from both.

## Error Modes
- The temporary file is written but the rename fails — the previously committed file remains byte
  for byte, and the caller is told the replacement did not take effect.
- The local data directory cannot be resolved or created — nothing can be written.
- Permission denied or device full — nothing replaced, existing file untouched.
- The rename is not atomic on this platform or filesystem — the guarantee NFR-004 rests on is
  absent and FR-012's quarantine becomes the primary defence; not detectable from inside here.
- The process is terminated between the temporary write and the rename — the previous file stands
  and a temporary file is left behind, which the next replace must overwrite rather than treat as
  an obstruction.

## Rationale
Satisfies the atomic-replace capability declared by CMP-012 (the save file) and CMP-014 (the
reminder preference). Atomicity lives in this primitive because no caller-side ordering can supply
it (NFR-004), and the write-then-rename mechanism is one of the platform-divergent seams NFR-006
names — which is why the fourth failure mode is stated as a property of the platform rather than
of the code.
