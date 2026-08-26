---
id: IF-014
type: interface
title: Save Integrity Validation
description: The contract that establishes whether a save file's contents are a committed state, separately from any unit that hands back a decoded pet state.
traces_from: [FR-012, NFR-004]
traces_to:
  adr: [ADR-002, ADR-003, ADR-004]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-013
operations:
- name: validate
  summary: Establish whether the supplied save-file contents are a committed state — complete and internally consistent as written — without putting them into service as a pet state.
  interaction: synchronous
error_modes:
- The contents are truncated, unparseable, or fail the consistency check — reported as not a committed state, which is the ordinary result FR-012's quarantine branch keys on rather than an exceptional one.
- The contents carry an unrecognised format version — treated as failing validation, so an unreadable generation is quarantined and preserved rather than trusted or discarded.
- Validation cannot be completed at all because the supplied bytes could not be read in full — reported as inconclusive and never as a pass, because a pass would put an unverified file into service as a committed state.
---

# IF-014 — Save Integrity Validation

The contract that establishes whether a save file's contents are a committed state, separately
from any unit that hands back a decoded pet state.

## Operations
- **validate** — Establish whether the supplied save-file contents are a committed state —
  complete and internally consistent as written — without putting them into service as a pet
  state.

## Interaction
Synchronous. The store's retrieval branches on the answer.

One operation, and the separation from decoding is the point: FR-012 splits the load path in two,
and integrity validation cannot be folded into the same unit that hands back a usable pet state,
or the failing branch would already have consumed the contents it must preserve untouched.

## Error Modes
- Contents truncated, unparseable, or failing the consistency check — reported as not a committed
  state; the ordinary result FR-012 keys on, not an exception.
- An unrecognised format version — treated as failing validation, so the file is quarantined and
  preserved rather than trusted or discarded.
- Validation cannot be completed at all — reported as inconclusive, never as a pass.

## Rationale
Satisfies CMP-012's declared need to establish whether a save file's contents are a committed
state. Confidence is medium: the glossary makes the mechanism implementation-defined and
dependent on the storage format, and while Q-4 is resolved (Tauri/Rust, a JSON file written by
atomic rename), the concrete check — structural decode alone, or a recorded checksum — is not
fixed by any requirement, and which one is chosen changes what inconclusive can mean.
