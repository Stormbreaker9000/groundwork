---
id: ADR-004
type: adr
title: Single committed generation of the save file
description: Whether the store retains one committed generation of the save file or keeps the previous generation as a second fallback.
traces_from: [NFR-004, FR-012, BR-002, NFR-002]
traces_to: {}
status: draft
confidence: high
created_at: '2026-08-24'
decision_status: accepted
considered_options:
- One committed generation retained
- Two committed generations retained, the previous kept as a fallback
chosen_option: One committed generation retained
---

# ADR-004: Single committed generation of the save file

## Context and Problem Statement

NFR-004's discriminating clause requires that where a committed state existed before a kill, that committed state is the one restored, and that recovery to a default pet occurs in 0% of such trials. The question is what supplies that guarantee: an atomic write primitive alone, or an atomic write plus a retained previous generation to fall back to. Retention interacts with FR-012, because the fallback path for a file that fails integrity validation is quarantine plus a default pet, and with BR-002, whose preservation clause is about not losing accumulated state. It also interacts with NFR-002, because a rotation is more idle I/O and disk than a single write per commit.

## Decision Drivers

- NFR-004
- FR-012
- BR-002
- NFR-002

## Considered Options

### One committed generation retained

- Pros: A simpler store contract and one write per commit rather than a rotation, and less idle I/O and disk against the footprint budget. Atomic write-then-rename already prevents an interrupted write from replacing a committed file, which is the failure mode the crash-safety measure actually exercises.
- Cons: Post-commit media corruption has no second generation to fall back to and resolves to quarantine plus a default pet — total loss of accumulated state.

### Two committed generations retained, the previous kept as a fallback

- Pros: Survives post-commit media corruption of the live file, which is the one failure class atomicity does not cover, and was the residual gap the requirements stage recommended against accepting.
- Cons: A rotation rather than one write per commit, on a write path whose frequency is a function of the evaluation cadence, so it spends idle I/O and disk against the footprint budget; and it widens the store contract and the set of paths that write or replace persisted pet state.

## Decision Outcome

One committed generation of the save file is retained, not two. The argument rests on atomic write-then-rename already preventing an interrupted write from replacing a committed file, which is the failure mode the crash-safety measure is written to exercise — leaving only post-commit media corruption uncovered.

### Consequences

- Good:
  - A simpler store contract, one write per commit rather than a rotation, and less idle I/O and disk against the footprint budget.
  - Atomic write-then-rename already prevents an interrupted write from replacing a committed file, which is the failure mode the crash-safety measure actually exercises.
- Bad:
  - Post-commit media corruption has no second generation to fall back to; it resolves to quarantine plus a default pet, which is total loss of accumulated state, and BR-002's preservation clause is then satisfied only in the weak sense that the corrupt bytes are preserved at the quarantine location.
  - The atomicity the whole argument rests on is a property of the platform and is not detectable from inside the atomic-replace contract, which concedes this as an error mode of its own.
  - The requirements stage recorded this as a residual gap and recommended against it; taking the one-generation answer accepts that gap for v1.
