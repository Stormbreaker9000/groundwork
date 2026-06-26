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

*More workflows will be added as groundwork matures. Run `/groundwork` after updating the plugin to see new additions.*
