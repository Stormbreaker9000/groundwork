---
id: IF-019
type: interface
title: Local Data Directory File Read
description: The platform-adapter contract for reading the bytes of a file inside the application's local data directory, whose concrete path is platform-specific.
traces_from: [FR-009, FR-010, FR-012, NFR-004, NFR-005, NFR-006]
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
- name: read_file
  summary: Return the bytes of a named file within the application's local data directory, or report that no such file is present.
  interaction: synchronous
error_modes:
- The local data directory cannot be resolved or created on this platform — no file can be read, and the application has neither a system of record nor a balance configuration to launch against.
- The named file is not present — reported as its own outcome rather than as a read error, because FR-010's no-save-file case and FR-012's unreadable-file case must be distinguishable by the caller, and a first launch with no reminder-preference file is an ordinary state rather than a fault.
- The file is present but unreadable — permission denied, device error — reported as a read failure and never as absence, since absence licenses the caller to write over it.
- The file is read while another writer is mid-replace — the atomic replace in IF-025 is what makes this impossible for files this application writes; for a file edited outside the application, such as the balance configuration, a torn read is possible and surfaces as unparseable content to the caller.
---

# IF-019 — Local Data Directory File Read

The platform-adapter contract for reading the bytes of a file inside the application's local data
directory, whose concrete path is platform-specific.

## Operations
- **read_file** — Return the bytes of a named file within the application's local data directory,
  or report that no such file is present.

## Interaction
Synchronous. Every caller branches immediately on what came back — a present save file, an absent
one, an unreadable one — and none of them has anything to do until it knows.

**This contract carried the atomic replace last round, and no longer does.** The two capabilities
were merged then because their consumer sets were identical: the pet state store read and replaced
the save file, and the reminder service read and replaced the preference file. The balance
configuration (CMP-002) has since become a third reader, and it never writes — its source is
loaded once at launch and is not the application's to modify. The consumer sets are now a strict
subset rather than a match, so the merge no longer holds: keeping them together would give the
balance configuration a dependency on an atomic-replace operation it has no business being able
to call. The replace lives in IF-025.

The split has a second benefit worth stating, since it is what makes it more than bookkeeping:
the failure modes separate cleanly. Everything here is about not being able to see a file;
everything in IF-025 is about a write not landing. Bundled, the list read as a mixture in which
neither caller could tell which half applied to it.

## Error Modes
- The local data directory cannot be resolved or created — no file can be read at all.
- The named file is not present — its own outcome, not a read error, so FR-010's and FR-012's
  cases stay distinguishable and a first launch without a preference file is ordinary.
- The file is present but unreadable — a read failure, never absence, since absence licenses the
  caller to write over it.
- A torn read while another writer is mid-replace — impossible for files this application writes,
  because IF-025 replaces atomically; possible for a balance configuration edited outside the
  application, where it surfaces as unparseable content.

## Rationale
Satisfies the read capability declared by CMP-002 (the balance configuration source), CMP-012
(the save file) and CMP-014 (the reminder preference). The directory path lives here because it
is one of the platform-divergent seams NFR-006 names.
