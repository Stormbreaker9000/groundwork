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

**Trigger:** Make any vague implementation request ("build X", "add Y", "make it do Z")

**Purpose:** Stops implementation before it starts. Asks four clarifying questions one at a time, then produces a requirements brief with acceptance criteria. You sign off on the brief before any code is written.

**Why it matters:** Vague requests lead to code that solves the wrong problem. Five minutes of requirements gathering saves hours of rework.

---

*More workflows will be added as groundwork matures. Run `/groundwork` after updating the plugin to see new additions.*
