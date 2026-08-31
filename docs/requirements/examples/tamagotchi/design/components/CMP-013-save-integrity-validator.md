---
id: CMP-013
type: component
title: Save Integrity Validator
description: The check applied to a save file's contents at read, establishing whether the file is complete and internally consistent enough to be treated as a committed state.
traces_from: [FR-012, NFR-004]
traces_to:
  adr: [ADR-002, ADR-003, ADR-004]
  diagrams: [DIA-003]
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Establishes whether a save file's contents are a committed state.
boundary: internal
depends_on: []
---

# CMP-013 — Save Integrity Validator

The check applied to a save file's contents at read, establishing whether the file is
complete and internally consistent enough to be treated as a committed state.

## Responsibility
Establishes whether a save file's contents are a committed state.

## Rationale
FR-012 splits the load path in two — a read that succeeds and a read that fails
validation and must preserve its evidence byte-identically before anything else writes
— so integrity validation cannot live in the same unit that hands back a decoded pet
state. Separating it also gives NFR-004's 200-trial fault injection a unit to drive
directly with truncated and corrupted content, rather than only through a launch.

Committed status is established at write time; this check is how a reader confirms it,
not what creates it. Confidence is medium because the glossary leaves the mechanism
implementation-defined — a checksum over the file, or a strict decode against CMP-001's
field set — and this stage defers that choice to the decision record.
