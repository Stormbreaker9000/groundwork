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

**Purpose:** Explores what you want through hypothesis-led conversation — Claude reads your codebase if one exists, proposes what it thinks you need, then refines through targeted questions. Produces a structured requirements artifact (functional, non-functional, and domain requirements) saved to `.sdlc/requirements/`. Handles decomposition of large requests into focused units. No code is written until you sign off on the artifact.

**Why it matters:** Starting with a shared, written understanding of what's being built prevents wasted implementation work and creates a paper trail that feeds the architecture phase.

---

*More workflows will be added as groundwork matures. Run `/groundwork` after updating the plugin to see new additions.*
