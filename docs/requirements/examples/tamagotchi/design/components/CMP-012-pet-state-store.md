---
id: CMP-012
type: component
title: Pet State Store
description: The custodian of the save file as the system's single system of record — committing a pet state atomically, and handing back the committed pet state or reporting that none is available.
traces_from: [FR-001, FR-012, NFR-004, NFR-005, NFR-007, CON-002, BR-002]
traces_to:
  adr: [ADR-001, ADR-002, ADR-003, ADR-004]
  diagrams: [DIA-003]
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Owns custody of the pet state save file as the system's single system of record.
boundary: internal
depends_on: [IF-014, IF-016, IF-018, IF-019, IF-020, IF-025]
---

# CMP-012 — Pet State Store

The custodian of the save file as the system's single system of record — committing a
pet state atomically, and handing back the committed pet state or reporting that none
is available.

## Responsibility
Owns custody of the pet state save file as the system's single system of record.

## Rationale
FR-001 writes on every stat change rather than on a timer, which makes a mid-write kill
an ordinary event and forces commit atomicity into the store rather than leaving it to
the caller. BR-002 is verified by inspecting every code path that writes, clears or
replaces persisted pet state — affordable only because every such path converges here.
One committed generation is retained (Q-9, resolved), because atomic write-then-rename
already prevents an interrupted write from replacing a committed file.

This component orders the failed-read path but implements neither half of it:
validation belongs to CMP-013 and the byte-identical move to CMP-017, per FR-012's
requirement that neither be folded into the unit that hands back a decoded pet state.
The quarantine move completes before any new write, so a default pet cannot overwrite
the evidence. CON-002 and NFR-005 bind this component absolutely — the local file is
the only permissible system of record, and it holds no network client of any kind.
