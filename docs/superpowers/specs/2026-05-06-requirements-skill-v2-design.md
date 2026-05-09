# Requirements Skill v2 — Design

**Date:** 2026-05-06
**Status:** Approved
**Replaces:** `skills/requirements/SKILL.md` (v1 scaffold)

## Purpose

Redesign the requirements skill from a rigid 4-question form into a hypothesis-led conversational workflow that feels like talking to a knowledgeable collaborator. The skill should understand the problem domain well enough to make informed suggestions, explore existing codebases actively, handle decomposition of large requests, and produce a structured requirements artifact that feeds naturally into the next SDLC phase (architecture/design).

## Context: Plugin SDLC Vision

The groundwork plugin will eventually cover the full SDLC. Requirements is the first phase; architecture/design is the next. The requirements artifact is designed to hand off cleanly to that future phase — structured enough to be consumed by a design workflow without re-asking questions.

## Phases

The skill moves through four phases in order:

### Phase 1: Detect

Before asking anything, Claude determines the project context:

- **Greenfield** — no existing codebase (no `package.json`, `src/`, `lib/`, or equivalent at the working directory root)
- **Existing codebase** — project files found; proceed to active exploration

For existing codebases, Claude runs a lightweight scan:
- `find . -maxdepth 3 -name "package.json" -o -name "Cargo.toml" -o -name "pyproject.toml" -o -name "go.mod"` — identify tech stack
- `ls src/` or equivalent — understand structure
- Read 2–3 key files (entry point, main module, relevant feature area) — understand patterns and conventions

The exploration is bounded: 3–5 targeted reads, not a full audit. Claude stops when it has enough to form grounded hypotheses.

### Phase 2: Hypothesize

Based on the request and any codebase findings, Claude generates 3–5 domain-informed hypotheses about what the feature probably needs.

**Greenfield example** ("I want to build a desktop tamagotchi app"):
- Pet entity with state (hunger, happiness, health) that persists between sessions
- Time-based decay — state changes even while the app is closed
- User interaction set (feed, play, clean)
- Visual representation of the pet with mood states
- Some form of consequence mechanic for neglect (death/reset)

**Existing codebase example** ("add dark mode to this React app"):
- CSS custom properties or a theme provider (already using Tailwind — probably `darkMode: 'class'`)
- Theme toggle component, likely in the navbar where settings controls live
- `localStorage` persistence for the preference
- System preference detection (`prefers-color-scheme`) as fallback

Hypotheses are presented as: *"Here's what I'm thinking this needs — [list]. Does that match your vision, or are there pieces missing or wrong?"*

This is a single confirming question, not a list of questions.

### Phase 3: Converse

Claude tracks four coverage areas. It works through them naturally — not in a fixed order — leading with its current assumption on each uncovered area and asking one targeted question to validate or correct it.

**Coverage areas:**

1. **Core functionality** — what the thing does (usually partially or fully established by the hypotheses)
2. **Success criteria** — what "done" looks like; how you'd know it's working
3. **Constraints** — tech, time, scope, or design limits
4. **Out of scope** — what's explicitly not being built in this round

**Conversation shape per exchange:**
- State what has been confirmed so far
- Surface the working assumption on the next uncovered area
- Ask one targeted question

Claude infers as much as possible and only asks when it genuinely cannot determine something from context. For a well-described request, 2–3 exchanges should be sufficient. For a vague one, more may be needed.

### Phase 3a: Decomposition (large requests only)

If the request describes a system with multiple independent logical units (e.g., "build a tamagotchi app" encompasses pet mechanics, persistence, UI, and time system), Claude flags this before proceeding:

*"This covers a few independent areas — [list units]. It'll be cleaner to handle each as its own requirements conversation. Want to start with [most foundational unit]?"*

Each unit then gets its own full Phase 2–4 cycle and its own artifact. The decomposition itself is not an artifact — it's a routing decision made in conversation.

**Decomposition criteria:** flag when the request contains 3+ distinct functional areas that would each independently produce acceptance criteria.

### Phase 4: Artifact

When all four coverage areas are confirmed, Claude transitions:

*"I think I have everything I need. Let me summarize before we save it."*

**In-conversation summary** (rendered in chat):

```
## Requirements Summary: <Feature Name>

**Overview:** [2-3 sentences: what's being built, why, for whom]

**Functional Requirements:**
- [What the system does]

**Non-Functional Requirements:**
- [Performance, reliability, offline support, etc. — omit section if none apply]

**Domain Requirements:**
- [Rules and concepts inherent to the problem space — omit section if none apply]

**Acceptance Criteria:**
- [ ] [Specific, testable condition]
- [ ] [Specific, testable condition]

**Constraints:** [Tech, scope, or design limits]

**Out of Scope:** [What's explicitly not being built now]

**Next Step:** Architecture & design
```

For existing codebases, a **Context** section appears above Functional Requirements:
```
**Context:** [Tech stack, affected modules, relevant existing patterns]
```

**Sign-off gate:** Present the summary and ask: *"Does this capture it accurately, or should we adjust anything before saving?"*

Do NOT save the artifact until the user confirms.

**On confirmation:** Save to `docs/requirements/YYYY-MM-DD-<kebab-case-feature-name>.md` and commit:

```bash
git add docs/requirements/YYYY-MM-DD-<name>.md
git commit -m "docs: add requirements for <feature-name>"
```

## Artifact File Format

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

## Trigger Description (frontmatter)

The skill's `description` field must remain trigger-accurate — specific enough not to fire on every message, reliable enough to fire on implementation requests:

```
description: Use when a user describes something they want to build or add — guides a conversational requirements process that produces a structured artifact before any code is written. Handles both greenfield projects and additions to existing codebases.
```

## What the Skill Does NOT Do

- Does not write code
- Does not produce architecture or technical design decisions
- Does not create tasks or implementation plans
- Does not invoke other skills
- Does not save until the user confirms the summary

## Boundaries with superpowers:brainstorming

The brainstorming skill is a full design process (spec → plan → implementation). The requirements skill is narrower: it produces a requirements artifact and stops. If a user is already mid-brainstorm (superpowers:brainstorming is active), the requirements skill should not trigger. The trigger description handles this implicitly — brainstorming sessions start with "let's build" framing that the requirements skill also catches, but the brainstorming skill takes priority per the skill priority rules in using-superpowers.
