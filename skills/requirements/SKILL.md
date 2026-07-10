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

**Reach the business *why* (5-Whys).** Before moving to Phase 4, make sure you understand the underlying business or user goal driving the request — not just the surface *what*. Apply 5-Whys as judgment, not ritual: if the root motivation is already clear from the request, don't belabor it; if it's murky, fold a *why* into this same Phase 3 message (e.g. "…and what problem does this solve for [the user]?"). Requirements generated against a misunderstood goal satisfy the letter and miss the point.

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

Work through six coverage areas. Do NOT go through them in a fixed order — follow where the conversation leads. Lead with your current assumption on each uncovered area and ask one targeted question to validate or correct it.

**Coverage areas:**
1. **Core functionality** — what the thing does (often partially established by the hypotheses)
2. **Stakeholders & user roles** — who uses the system, who is affected beyond the primary user (admin, operator, support, auditor, regulator, third-party integrations)
3. **Success criteria** — what done looks like; how you'd know it's working
4. **Non-functional concerns** — probe at minimum: performance expectations, security requirements, reliability/uptime needs, and accessibility or platform constraints. Infer from context where obvious; only ask if the domain makes NFRs non-obvious or high-stakes.
5. **Constraints** — tech, time, scope, regulatory, or design limits
6. **Out of scope** — what's explicitly not being built in this iteration

**Also sweep the commonly-omitted categories.** These are the areas requirements processes routinely skip — walk them silently and surface only those that matter for this domain. Governing rule (same restraint as below): **infer where obvious; only ask when the category is high-stakes and non-obvious.**

- Error / exception paths
- Compliance / regulatory constraints
- Data retention / migration / deletion
- Internationalization & accessibility
- Operational concerns — deployment, backup, monitoring, on-call
- Legal / licensing
- Stakeholder roles beyond "the user" — admin, operator, support, auditor, regulator, third-party

This is a gap check, not a script. A well-scoped request may need none of these raised explicitly; do not manufacture questions to cover the list.

**Per-exchange shape:**
- Briefly state what you've confirmed so far
- Surface your working assumption on the next uncovered area
- Ask one targeted question to validate or correct it

**Prefer numbered options.** When a question's answer space is enumerable, present 2–4 numbered candidate answers and invite the user to reply with a number (or add their own) instead of asking open-ended — this measurably improves answer quality. Reserve open-ended questions for genuinely open spaces. For example: *"For an unauthenticated user hitting a protected route, should the system (1) redirect to login, (2) return 401 with a JSON error, or (3) serve a public preview? Pick one, or describe another."*

Infer as much as possible from context. Only ask when you genuinely cannot determine something. A well-described request typically needs 2–4 exchanges. A vague one may need more.

When all six areas are confirmed, proceed to Phase 4.5.

## Phase 4.5: Context Synthesis

Before generating the artifact, synthesize the elicited information into a structured context object. This confirms shared understanding and serves as the direct input to the artifact generator.

Render in-conversation:

```
**Elicitation context:**

**Problem domain:** [what's being built + the underlying business/user goal]
**Stakeholders & users:** [primary user + any secondary roles identified]
**Core functionality:** [primary capabilities in plain terms]
**Success criteria:** [how you know it's working — measurable outcomes]
**Non-functional concerns:** [performance, security, reliability, accessibility — or "None identified"]
**Constraints:** [hard limits — or "None identified"]
**Out of scope:** [explicit exclusions — or "None identified"]
**Open questions:** [anything still uncertain — or "None"]
```

Ask: *"Does this capture the context correctly, or should I adjust anything before generating the requirements?"*

Do NOT proceed to Phase 5 until the user confirms. If corrections are needed, update the context object and re-confirm.

## Phase 5: Generate the Requirements Artifact Set

Phases 1–4.5 produce the **clarification context** (the Phase 4.5 "Elicitation context" block). Phase 5 hands that context to the multi-agent generation pipeline, which produces **atomic Markdown+YAML requirement files** — one requirement per file, with categorical IDs, EARS notation, ISO 25010 NFR scenarios, and traceability — not a single flat document.

The Phase 4.5 block serializes 1:1 to the `clarification_context` the orchestrator consumes:

```yaml
clarification_context:
  problem_domain: ...
  stakeholders_and_users: ...
  core_functionality: ...
  success_criteria: ...
  non_functional_concerns: ...   # or "None identified"
  constraints: ...               # or "None identified"
  out_of_scope: ...              # or "None identified"
  open_questions: ...            # or "None"
```

**Step 1 — Generate (multi-agent pipeline):**

Drive the pipeline through the agents under `agents/`, in this fixed order:

1. **requirements-orchestrator** — classifies needs into BABOK tiers (business → stakeholder → solution → transition), allocates categorical zero-padded IDs (FR/NFR/CON/BR/UC), and dispatches a brief to each specialist.
2. **fr-specialist** — functional requirements in EARS notation, each with rationale, fit criterion, and Gherkin acceptance criteria.
3. **nfr-specialist** — walks all nine ISO 25010:2023 quality characteristics (plus observability, deployability, compliance, cost) and emits each applicable NFR as a six-part quality attribute scenario.
4. **constraint-specialist** — constraints (CON) and business rules (BR), kept distinct from NFRs and traced to what they bound.
5. **requirements-critic** — two-phase INCOSE/ISO 29148 quality gate + ISO 25010 coverage check + anti-pattern flags, and runs the structural validator as a hard gate.
6. **requirements-formatter** — writes the atomic files plus the project-level
   `assumptions.md` (Assumptions / Dependencies / Open Questions), running only
   after the critic returns `gate: pass`.

Do not advance to the formatter until the critic reports a passing gate.

**Step 2 — Render in-conversation summary:**

Before writing any files, summarize the generated set for review:

```
## Requirements Summary: <Feature Name>

**Overview:** [2-3 sentences: what's being built, why, for whom]

**Context:** [Existing codebases: tech stack, affected modules. Omit for greenfield.]

**Functional (EARS):**
- FR-001 <title> — <one-line behavior>

**Non-Functional (ISO 25010 QAS):**
- NFR-001 <title> — <response measure>

**Constraints & Business Rules:**
- CON-001 / BR-001 <title>

**Assumptions & Dependencies:** [key A-#/D-# items, or "None identified"]
**Open Questions:** [Q-# items needing human follow-up, or "None"]

**Flagged for review:** [low-confidence items + open questions — or "None"]

**Next Step:** Architecture & design
```

**Step 3 — Sign-off gate:**

Ask: *"Does this capture it accurately, or should we adjust anything before I write the files?"*

Do NOT write the artifact files until the user confirms. If corrections are needed, re-dispatch the affected items to the owning specialist via the orchestrator, then re-summarize.

**Step 4 — Write atomic files, then validate (hard gate):**

On confirmation, run the formatter to write the files, then run the structural validator:

```bash
mkdir -p .sdlc/requirements/{functional,non-functional,constraints,business-rules,use-cases}
python3 skills/requirements/scripts/validate_requirements.py .sdlc/requirements
```

The validator MUST exit 0. If it exits non-zero, fix the flagged files (re-dispatch to the owning specialist) and re-run until clean. It requires `pyyaml` and `jsonschema` (`pip install pyyaml jsonschema`); see `skills/requirements/scripts/README.md`.

The formatter also writes `.sdlc/requirements/assumptions.md`. The structural
validator hard-gates its presence and its three headings (`## Assumptions`,
`## Dependencies`, `## Open Questions`) — a missing file or heading fails the gate.

Then run the advisory content-quality linter and address any `warn`-severity
findings (the structural validator is the hard gate; the content linter guides
prose quality):

```bash
python3 skills/requirements/scripts/lint_requirements_content.py .sdlc/requirements
```

**Step 5 — Generate the Definition of Done stub:**

Run **dod-generator** to derive `.sdlc/requirements/definition-of-done.md` from the requirement set (functional acceptance gates, NFR fitness gates, constraint/business-rule compliance, test coverage, docs, deployment readiness). This is an M1 stub that M3 expands.

**Step 6 — Commit:**

```bash
git add .sdlc/requirements/
git commit -m "docs: add requirements artifact set for <feature-name>"
```
