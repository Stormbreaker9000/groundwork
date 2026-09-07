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

### qa

**Trigger:** A validated requirement set *and* an approved design set both exist and you're ready to define the test strategy ("what should we test?", "let's define the QA strategy", "write the test plan").

**Purpose:** Runs a QA interview covering only what neither prior stage carries — test tooling and any existing suite's conventions, what CI can actually run and fail on, and coverage targets and risk appetite (including what the team has decided not to test) — opening with any open questions the design stage left unresolved. The entry gate runs all three structural validators (requirements, design, and cross-artifact traceability) before anything else, because this stage is about to add a third set of edges to that graph. Then runs a multi-agent pipeline (orchestrator → functional/quality-attribute test specialists → critic → formatter) that emits **atomic Markdown+YAML test-strategy files** with categorical IDs (`TS-`) under `.sdlc/qa/`, plus a projected `qa-strategy.md` covering test levels, scope by component, risk-based prioritisation, tooling, coverage targets, and an accepted-risk register. A structural validator and the cross-artifact traceability check both gate after writing. No files are written until you sign off.

**Why it matters:** A coverage number nobody believes is worse than an honest gap. This stage forces the team to say what CI can actually enforce and what it has deliberately declined to test, and records both as first-class, traceable artifacts instead of leaving them as tribal knowledge.

---

*More workflows will be added as groundwork matures. Run `/groundwork` after updating the plugin to see new additions.*
