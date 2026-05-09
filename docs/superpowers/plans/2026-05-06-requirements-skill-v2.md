# Requirements Skill v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the rigid 4-question requirements skill with a hypothesis-led conversational workflow that actively explores codebases, decomposes large requests, and saves a structured requirements artifact.

**Architecture:** Single file rewrite (`skills/requirements/SKILL.md`) plus directory scaffolding for artifacts (`docs/requirements/`) and an update to the `/groundwork` command index. No code — this is entirely markdown skill content and directory structure.

**Tech Stack:** Markdown with YAML frontmatter (skill), Bash (find/ls commands referenced in skill body)

---

### Task 1: Establish docs/requirements/ artifact directory

**Files:**
- Create: `docs/requirements/.gitkeep`

- [ ] **Step 1: Create the directory and gitkeep**

```bash
mkdir -p docs/requirements && touch docs/requirements/.gitkeep
```

- [ ] **Step 2: Verify directory exists and is tracked**

```bash
git status docs/requirements/
```

Expected: `docs/requirements/.gitkeep` shown as untracked

- [ ] **Step 3: Commit**

```bash
git add docs/requirements/.gitkeep
git commit -m "feat: add docs/requirements artifact directory"
```

---

### Task 2: Rewrite skills/requirements/SKILL.md

**Files:**
- Modify: `skills/requirements/SKILL.md` (full rewrite)

- [ ] **Step 1: Write the new SKILL.md**

Replace the entire contents of `skills/requirements/SKILL.md` with:

````markdown
---
name: requirements
description: Use when a user describes something they want to build or add — guides a conversational requirements process that produces a structured artifact before any code is written. Handles both greenfield projects and additions to existing codebases.
---

# Requirements

Turn what the user wants into a structured requirements artifact through hypothesis-led conversation. This is phase 1 of the groundwork SDLC workflow.

## When This Applies

Invoke when the user describes something they want to build or add:
- "I want to build X"
- "Add Y to my project"
- "I need a feature that..."
- A description of an application or system

Do NOT invoke for:
- Questions or explanations
- Bug reports with clear reproduction steps
- Requests to read, explore, or explain existing code
- When superpowers:brainstorming is already active

## Phase 1: Detect Project Context

Before asking anything, determine whether this is a greenfield project or an existing codebase.

Run these commands silently to check:

```bash
find . -maxdepth 3 \( -name "package.json" -o -name "Cargo.toml" -o -name "pyproject.toml" -o -name "go.mod" \) 2>/dev/null | head -5
ls src/ lib/ app/ 2>/dev/null | head -10
```

**If existing codebase found:** Read 3–5 targeted files to understand the tech stack, structure, and conventions relevant to the request. Read: the root config file (package.json/Cargo.toml etc.), the entry point or main module, and any existing files most relevant to what's being requested. Stop when you have enough to form grounded hypotheses — this is a bounded scan, not a full audit.

**If no codebase found:** Proceed directly to Phase 2.

## Phase 2: Decompose If Needed

If the request describes a system with 3 or more distinct functional areas that would each independently produce their own acceptance criteria, decompose before proceeding:

*"This covers a few independent areas — [list the units]. It'll be cleaner to handle each as its own requirements conversation. Want to start with [most foundational unit]?"*

Each unit gets its own full Phase 3–5 cycle and its own saved artifact. The decomposition is a routing decision made in conversation, not a separate document.

If the request is focused (one feature, one addition, one area), skip decomposition and proceed to Phase 3.

## Phase 3: Hypothesize

Generate 3–5 domain-informed hypotheses about what the feature probably needs. Base these on the request domain and — for existing codebases — what you found in Phase 1.

Present as a single message: *"Here's what I'm thinking this needs: [hypotheses as a bulleted list]. Does that match your vision, or are there pieces missing or wrong?"*

This is ONE question. Do not ask multiple questions here.

**Example — greenfield desktop tamagotchi app:**
- Pet entity with state (hunger, happiness, health) that persists between sessions
- Time-based decay — state degrades even while the app is closed
- User interaction set (feed, play, clean)
- Visual representation of the pet with mood states
- Consequence mechanic for neglect (death/reset)

**Example — adding dark mode to an existing React/Tailwind app:**
- `darkMode: 'class'` in Tailwind config (if not already set)
- Theme toggle component, likely near the navbar where other settings live
- `localStorage` persistence for the user's preference
- `prefers-color-scheme` media query detection as a system-default fallback

## Phase 4: Converse

Work through four coverage areas. Do NOT go through them in a fixed order — follow where the conversation leads. Lead with your current assumption on each uncovered area and ask one targeted question to validate or correct it.

**Coverage areas:**
1. **Core functionality** — what the thing does (often partially established by the hypotheses)
2. **Success criteria** — what done looks like; how you'd know it's working
3. **Constraints** — tech, time, scope, or design limits
4. **Out of scope** — what's explicitly not being built in this iteration

**Per-exchange shape:**
- Briefly state what you've confirmed so far
- Surface your working assumption on the next uncovered area
- Ask one targeted question to validate or correct it

Infer as much as possible from context. Only ask when you genuinely cannot determine something. A well-described request typically needs 2–3 exchanges. A vague one may need more.

When all four areas are confirmed, transition: *"I think I have everything I need. Let me summarize before we save it."*

## Phase 5: Artifact

**Step 1 — Render in-conversation summary:**

```
## Requirements Summary: <Feature Name>

**Overview:** [2-3 sentences: what's being built, why, for whom]

**Context:** [For existing codebases: tech stack, affected modules, relevant patterns. Omit for greenfield.]

**Functional Requirements:**
- [What the system does]

**Non-Functional Requirements:**
- [Performance, reliability, accessibility, etc. — omit section if none identified]

**Domain Requirements:**
- [Rules and concepts inherent to the problem space — omit section if none identified]

**Acceptance Criteria:**
- [ ] [Specific, testable condition]
- [ ] [Specific, testable condition]

**Constraints:** [Tech, scope, or design limits]

**Out of Scope:** [What's explicitly not being built now]

**Next Step:** Architecture & design
```

**Step 2 — Sign-off gate:**

Ask: *"Does this capture it accurately, or should we adjust anything before saving?"*

Do NOT save the artifact until the user confirms.

**Step 3 — Save artifact:**

Create `docs/requirements/YYYY-MM-DD-<kebab-case-feature-name>.md` with this exact structure:

```markdown
# Requirements: <Feature Name>

**Date:** YYYY-MM-DD
**Status:** Approved

## Overview

[2-3 sentences describing what's being built, why, and for whom]

## Context

[For existing codebases: tech stack, affected modules, relevant patterns.
For greenfield: "New project — no existing codebase."]

## Functional Requirements

- [What the system does]

## Non-Functional Requirements

- [Performance, reliability, accessibility, etc.]

*(Omit this section if none identified)*

## Domain Requirements

- [Rules and concepts inherent to the problem space]

*(Omit this section if none identified)*

## Acceptance Criteria

- [ ] [Specific, testable condition]
- [ ] [Specific, testable condition]

## Constraints

[What this must not do, or boundaries it must stay within]

## Out of Scope

[What will not be addressed in this change]

## Next Step

Architecture & design
```

**Step 4 — Commit:**

```bash
git add docs/requirements/YYYY-MM-DD-<name>.md
git commit -m "docs: add requirements for <feature-name>"
```
````

- [ ] **Step 2: Verify frontmatter fields**

```bash
head -5 skills/requirements/SKILL.md
```

Expected:
```
---
name: requirements
description: Use when a user describes something they want to build or add — guides a conversational requirements process that produces a structured artifact before any code is written. Handles both greenfield projects and additions to existing codebases.
---
```

- [ ] **Step 3: Verify all five phases are present**

```bash
grep "^## Phase" skills/requirements/SKILL.md
```

Expected output (5 lines):
```
## Phase 1: Detect Project Context
## Phase 2: Decompose If Needed
## Phase 3: Hypothesize
## Phase 4: Converse
## Phase 5: Artifact
```

- [ ] **Step 4: Verify sign-off gate is present**

```bash
grep -c "Do NOT save" skills/requirements/SKILL.md
```

Expected: `1`

- [ ] **Step 5: Verify artifact commit instruction is present**

```bash
grep "git commit" skills/requirements/SKILL.md
```

Expected: a line containing `git commit -m "docs: add requirements for`

- [ ] **Step 6: Trace greenfield scenario mentally**

Read through the skill and verify it would handle "I want to build a desktop tamagotchi app" correctly:
- Phase 1: `find` finds no project files → greenfield path
- Phase 2: "build a whole app" has 4+ areas → decomposition prompt fires
- Phase 3: hypotheses generated from tamagotchi domain knowledge
- Phase 4: conversation covers core functionality, success criteria, constraints, out of scope
- Phase 5: summary rendered, sign-off requested, artifact saved to `docs/requirements/`

If the trace reveals any gaps, fix the skill content before committing.

- [ ] **Step 7: Trace existing codebase scenario mentally**

Read through the skill and verify it would handle "add dark mode to my React app" correctly:
- Phase 1: `find` finds `package.json` → existing codebase path, reads 3-5 files
- Phase 2: single feature, no decomposition needed
- Phase 3: hypotheses grounded in Tailwind/React findings
- Phase 4: short conversation, infers most things from codebase context
- Phase 5: Context section included in artifact

If the trace reveals any gaps, fix the skill content before committing.

- [ ] **Step 8: Commit**

```bash
git add skills/requirements/SKILL.md
git commit -m "feat: rewrite requirements skill with hypothesis-led v2 workflow"
```

---

### Task 3: Update commands/groundwork.md

**Files:**
- Modify: `commands/groundwork.md`

The `/groundwork` command index currently describes the requirements skill with v1 language ("asks four clarifying questions one at a time"). Update it to describe v2 behavior.

- [ ] **Step 1: Update the requirements section in commands/groundwork.md**

Replace the `### requirements` section (lines 19–25) with:

```markdown
### requirements

**Trigger:** Describe something you want to build or add ("I want to build X", "add Y to my app", "I need a feature that...")

**Purpose:** Explores what you want through hypothesis-led conversation — Claude reads your codebase if one exists, proposes what it thinks you need, then refines through targeted questions. Produces a structured requirements artifact (functional, non-functional, and domain requirements) saved to `docs/requirements/`. Handles decomposition of large requests into focused units. No code is written until you sign off on the artifact.

**Why it matters:** Starting with a shared, written understanding of what's being built prevents wasted implementation work and creates a paper trail that feeds the architecture phase.
```

- [ ] **Step 2: Verify the updated file still has valid frontmatter**

```bash
head -5 commands/groundwork.md
```

Expected: frontmatter block with `description:`, `argument-hint:`, `allowed-tools:` fields intact.

- [ ] **Step 3: Commit**

```bash
git add commands/groundwork.md
git commit -m "docs: update /groundwork requirements description for v2"
```

---

## Verification

After all tasks complete:

- [ ] Run `git log --oneline -5` — confirm 3 commits on top of the pre-task baseline
- [ ] Run `ls docs/requirements/` — confirm `.gitkeep` exists
- [ ] Run `grep "^## Phase" skills/requirements/SKILL.md` — confirm all 5 phases present
- [ ] Run `grep "description:" skills/requirements/SKILL.md | head -1` — confirm trigger description matches spec
- [ ] Open a new Claude Code session, make a vague build request — confirm the skill now opens with hypotheses rather than "What problem does this solve?"
