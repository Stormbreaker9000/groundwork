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

Do not write any code at any point during this skill. This skill produces a requirements artifact only.

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

First, get the current date and ensure the directory exists:

```bash
TODAY=$(date +%Y-%m-%d)
mkdir -p .sdlc/requirements
```

Create `.sdlc/requirements/$TODAY-<kebab-case-feature-name>.md` with this exact structure:

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
TODAY=$(date +%Y-%m-%d)
git add .sdlc/requirements/$TODAY-<name>.md
git commit -m "docs: add requirements for <feature-name>"
```
