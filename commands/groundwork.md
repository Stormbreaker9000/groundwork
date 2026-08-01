---
description: Overview of the groundwork plugin — lists available SDLC workflows and how to use them
argument-hint: "[workflow-name]"
allowed-tools: ["Read"]
---

# /groundwork

The groundwork plugin provides structured SDLC workflows. Each workflow is a skill that guides a specific phase of software development.

## Usage

- `/groundwork` — show all available workflows
- `/groundwork <workflow-name>` — explain a specific workflow in detail

## Available Workflows

### requirements

**Trigger:** Describe something you want to build or add ("I want to build X", "add Y to my app", "I need a feature that...")

**Purpose:** Guides a hypothesis-led clarification interview (Claude reads your codebase if one exists, proposes what it thinks you need, then refines through targeted questions), then runs a multi-agent generation pipeline (orchestrator → FR/NFR/constraint specialists → critic → formatter) that emits **atomic Markdown+YAML requirement files** with categorical IDs (FR/NFR/CON/BR) under `.sdlc/requirements/` — functional requirements in EARS notation, non-functional requirements as ISO 25010 quality-attribute scenarios — checked by a structural validator, plus a Definition of Done stub. Handles decomposition of large requests into focused units. No files are written until you sign off.

**Why it matters:** Starting with a shared, written understanding of what's being built prevents wasted implementation work and creates a paper trail that feeds the architecture phase.

---

### design

**Trigger:** A validated requirement set exists under `.sdlc/requirements/` and you're ready to turn it into an architecture ("design this", "let's do the architecture", "turn the requirements into components").

**Purpose:** Runs an architecture interview covering what requirements deliberately cannot carry — runtime and stack, persistence, deployment target, integration points, operational and team constraints — opening with any open questions the requirements stage left for architecture to decide. Then runs a multi-agent pipeline (orchestrator → component/interface specialists → critic → formatter) that emits **atomic Markdown+YAML design files** with categorical IDs (CMP/IF) under `.sdlc/design/`, plus `assumptions.md` and `drivers.md`. Components declare a single responsibility; interfaces declare provider, operations, interaction style, and error modes. A critic gates on ISO/IEC/IEEE 42010 and ATAM before anything is written, and a structural validator gates after. No files are written until you sign off.

**Why it matters:** The architecture stage is where technology decisions get made silently if nobody forces them into the open. This one asks, records the drivers and tradeoffs behind the decomposition, and hands the next stage a traceable component graph instead of a diagram.

---

*More workflows will be added as groundwork matures. Run `/groundwork` after updating the plugin to see new additions.*
