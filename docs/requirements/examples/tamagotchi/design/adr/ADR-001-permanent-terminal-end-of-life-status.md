---
id: ADR-001
type: adr
title: Permanent terminal end-of-life status
description: Whether a pet that reaches the terminal end-of-life status stays terminal permanently, or whether the owner is offered a configurable soft reset to a fresh default pet.
traces_from: [BR-002, BR-001, FR-008]
traces_to: {}
status: draft
confidence: high
created_at: '2026-08-24'
decision_status: accepted
considered_options:
- Permanent terminal status with no disposition
- Configurable soft reset to a fresh default pet
chosen_option: Permanent terminal status with no disposition
---

# ADR-001: Permanent terminal end-of-life status

## Context and Problem Statement

The terminal end-of-life status is named neutrally in the glossary precisely because what follows it was undecided, and BR-002 froze the question: until it was settled, no terminal pet's accumulated state could be discarded and no disposition could be implemented at all, because whichever answer was taken had to become a single project-wide policy applied consistently. BR-001 constrains the same boundary from the other side by requiring that the terminal status arise only from sustained unremedied neglect and never from an application fault, and FR-008 owns the transition that reaches it. The decision had to be taken before the health-progression path could be decomposed, because a disposition — had one been selected — would have needed an owner, a trigger and a write path of its own.

## Decision Drivers

- BR-002
- BR-001
- FR-008

## Considered Options

### Permanent terminal status with no disposition

- Pros: Gives BR-002 the single project-wide policy it requires the answer to take, and keeps the emotional weight that makes the daily-return habit carry stakes. The design needs no disposition component at all: the terminal status becomes a health status the progression can reach and nothing downstream consumes, which is why BR-002's prohibition survives as a structural property rather than as a rule someone must remember to keep.
- Cons: An owner who loses a pet after one bad week has no in-product recovery, which is the abandonment risk the alternative existed to mitigate.

### Configurable soft reset to a fresh default pet

- Pros: Mitigates abandonment by giving the owner a way back after a terminal outcome, and was the option BR-002 was written to keep reachable.
- Cons: Requires a disposition to exist as an implemented behaviour with its own owner and write path, and a configurable one introduces a second lifecycle path alongside the terminal one, which is what BR-002's single-project-wide-policy clause was written to prevent from proliferating.

## Decision Outcome

The terminal end-of-life status is permanent. There is one terminal lifecycle path, no reset setting, and no disposition that discards a terminal pet's accumulated state. The terminal status is therefore a health status the progression can reach and nothing downstream is permitted to consume, which is what turns BR-002's prohibition into a structural property of the decomposition rather than a discipline every future writer of persisted state must remember.

### Consequences

- Good:
  - BR-002 gets the single project-wide policy its fit criterion requires the answer to take, and the count of terminal-pet disposition implementations stays at zero by construction.
  - No disposition component is needed anywhere in the decomposition, so no path exists that could discard or overwrite a terminal pet's accumulated state.
  - The emotional weight that makes the daily-return habit carry stakes is retained.
- Bad:
  - Forecloses the configurable soft reset the question held open, and accepts the abandonment risk that option existed to mitigate — an owner who loses a pet after one bad week has no in-product recovery.
  - BR-002 was written to keep both answers reachable; taking the permanent answer spends that optionality.
