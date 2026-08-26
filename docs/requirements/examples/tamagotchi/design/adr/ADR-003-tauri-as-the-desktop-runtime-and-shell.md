---
id: ADR-003
type: adr
title: Tauri as the desktop runtime and shell
description: Which runtime and application shell the desktop product is built on, given a baseline-overhead exclusion screen and a single-codebase requirement.
traces_from: [CON-001, NFR-002, NFR-006, NFR-003, FR-001, FR-012]
traces_to: {}
status: draft
confidence: medium
created_at: '2026-08-24'
decision_status: accepted
considered_options:
- Tauri — a Rust core with an OS-supplied system webview
- An Electron-class shell bundling a full Chromium runtime
- A native view per platform
chosen_option: Tauri — a Rust core with an OS-supplied system webview
---

# ADR-003: Tauri as the desktop runtime and shell

## Context and Problem Statement

CON-001 excludes whole runtime families from the design space at selection time rather than tuning a figure afterwards: any candidate whose empty-shell baseline alone exceeds 40% of the idle-footprint budget is excluded, with a full Chromium/Electron-class shell named as the stated excluded example. That makes the runtime a boundary on the shell everything else is built inside — it is settled before any component exists and cannot be revisited by optimising component code. NFR-006 constrains the same choice from the other side by requiring one shared codebase across three targets, and NFR-003 requires native accessibility integration on each. The choice also fixes the storage mechanism that FR-001's persistence and FR-012's integrity validation are defined over, and it sets the floor under NFR-002's idle budget.

## Decision Drivers

- CON-001
- NFR-002
- NFR-006
- NFR-003
- FR-001
- FR-012

## Considered Options

### Tauri — a Rust core with an OS-supplied system webview

- Pros: The exclusion screen is passable on published baselines because the webview is supplied by the OS rather than bundled, and a single shared codebase stays viable for a team with no platform specialists. It also fixes the storage mechanism the rest of the design needed — a JSON save file written by atomic write-then-rename — which is what lets integrity validation and the atomic-replace contract be specified at all.
- Cons: Rendering and native accessibility both land on a shared webview, which is why both had to be pulled explicitly back inside the platform-adapter layer rather than being allowed to ride the runtime.

### An Electron-class shell bundling a full Chromium runtime

- Pros: The most familiar shell for a single shared codebase across three desktop targets, with the widest ecosystem and the least platform-specific work.
- Cons: Rejected on its empty-shell baseline: a bundled full Chromium runtime is the stated excluded example of a candidate whose baseline alone consumes more than the allowance the exclusion screen permits.

### A native view per platform

- Pros: The lowest achievable baseline overhead, and the most direct route to each platform's own native accessibility stack.
- Cons: Rejected on the team constraint: it abandons the single shared codebase outright and needs a dedicated specialist per platform, which the team does not have.

## Decision Outcome

Tauri — a Rust core with an OS-supplied system webview — is selected, rejecting an Electron-class shell on its empty-shell baseline against the exclusion screen, and native-per-platform on the team constraint. The selection is being built on, but it is provisional against measurement rather than settled by it: the exclusion screen cannot be executed until a reference machine is recorded, so the rejection rests on published baselines rather than on this project's own. The unexecuted screen and the missing runtime decision record are the subject of ADR-007 and are deliberately not merged into this record, which documents a decision that was taken.

### Consequences

- Good:
  - The empty-shell exclusion screen is passable on published baselines, and the Electron-class candidate is excluded on the figure the constraint names.
  - A single shared codebase across all three desktop targets stays viable for a team with no platform specialists, which is the constraint that ruled out native-per-platform.
  - Fixes the storage mechanism the persistence path needed — a JSON save file written by atomic write-then-rename — which is what lets integrity validation and the atomic-replace contract be specified at all.
- Bad:
  - The selection rests on published baselines rather than on this project's own measurement, because no reference machine has been recorded — so the exclusion is asserted rather than executed, and the runtime decision record the constraint requires does not yet exist.
  - Every downstream footprint argument inherits that provisionality, including the evaluation cadence period and the per-tick cost of the timer seam.
  - Puts rendering and native accessibility on a shared webview, which is why both had to be pulled explicitly back inside the platform-adapter layer rather than being allowed to ride the runtime.
