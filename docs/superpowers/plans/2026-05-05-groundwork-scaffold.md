# Groundwork Plugin Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold a complete, loadable Claude Code plugin with one working example of each pillar — manifest, skill, command, hook, and agent — that proves the plugin is picked up by Claude.

**Architecture:** All plugin content lives in the repo root. The `.claude-plugin/` directory holds the manifests the loader needs; `skills/`, `commands/`, `hooks/`, and `agents/` hold one real example each. The session-start hook outputs JSON to inject context into Claude's session; all other files are markdown or JSON config.

**Tech Stack:** Bash (session-start hook), JSON (manifests, hooks.json), Markdown with YAML frontmatter (skill, command, agent, CLAUDE.md)

---

### Task 1: Plugin Manifests

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`
- Create: `package.json`

- [ ] **Step 1: Create the plugin identity manifest**

Create `.claude-plugin/plugin.json`:

```json
{
  "name": "groundwork",
  "description": "SDLC discipline workflows for Claude Code — requirements, planning, and structured development practices",
  "version": "0.1.0",
  "author": {
    "name": "Mark D'Adamo",
    "email": "mark.dadamo@gmail.com"
  },
  "license": "MIT"
}
```

- [ ] **Step 2: Verify plugin.json is valid JSON**

Run: `python3 -m json.tool .claude-plugin/plugin.json`
Expected: the JSON echoed back with no error

- [ ] **Step 3: Create the local dev marketplace manifest**

Create `.claude-plugin/marketplace.json`:

```json
{
  "name": "groundwork-dev",
  "description": "Local development marketplace for the groundwork plugin",
  "owner": {
    "name": "Mark D'Adamo",
    "email": "mark.dadamo@gmail.com"
  },
  "plugins": [
    {
      "name": "groundwork",
      "description": "SDLC discipline workflows for Claude Code",
      "version": "0.1.0",
      "source": "./"
    }
  ]
}
```

- [ ] **Step 4: Verify marketplace.json is valid JSON**

Run: `python3 -m json.tool .claude-plugin/marketplace.json`
Expected: the JSON echoed back with no error

- [ ] **Step 5: Create package.json**

Create `package.json`:

```json
{
  "name": "groundwork",
  "version": "0.1.0",
  "type": "module"
}
```

- [ ] **Step 6: Verify package.json is valid JSON**

Run: `python3 -m json.tool package.json`
Expected: the JSON echoed back with no error

- [ ] **Step 7: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json package.json
git commit -m "feat: add plugin manifests"
```

---

### Task 2: Root Content Files

**Files:**
- Create: `CLAUDE.md`
- Create: `README.md`
- Create: `.gitignore`

- [ ] **Step 1: Create CLAUDE.md**

This file is injected into Claude's context when the plugin is active. Keep it short — it proves pickup without being noisy.

Create `CLAUDE.md`:

```markdown
# Groundwork Plugin

The **groundwork** plugin is active. It provides SDLC discipline workflows to help you build software with structure instead of instinct.

Run `/groundwork` to see available workflows.
```

- [ ] **Step 2: Create README.md**

Create `README.md`:

```markdown
# groundwork

A Claude Code plugin for disciplined software development workflows.

Groundwork guides you through structured SDLC practices — requirements gathering, architecture decisions, and release discipline — before you write code.

## Installation

Register the local directory as a marketplace source in Claude Code:

1. Open Claude Code settings
2. Add this repo's path as a marketplace source
3. Install the `groundwork` plugin

## Usage

Run `/groundwork` in any Claude Code session to see available workflows.

## Workflows

| Workflow | Trigger | Description |
|---|---|---|
| Requirements | Say "build X" or "add Y" | Turns vague requests into structured briefs before any code is written |

## Development

The plugin uses the standard Claude Code plugin structure:
- `skills/` — markdown instruction sets
- `commands/` — slash commands
- `hooks/` — event-driven scripts
- `agents/` — dispatched subagents
- `.claude-plugin/` — manifests
```

- [ ] **Step 3: Create .gitignore**

Create `.gitignore`:

```
.DS_Store
*.pyc
__pycache__/
node_modules/
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md README.md .gitignore
git commit -m "feat: add root content files"
```

---

### Task 3: Requirements Skill

**Files:**
- Create: `skills/requirements/SKILL.md`

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p skills/requirements
```

- [ ] **Step 2: Create SKILL.md**

Create `skills/requirements/SKILL.md`:

```markdown
---
name: requirements
description: Use before implementing any feature or change - turns vague requests into structured requirements with acceptance criteria before any code is written.
---

# Requirements Gathering

Stop before writing code. Turn the request into a brief that both you and the user agree on.

## When This Applies

Invoke this skill when the user makes a vague implementation request:
- "Build X"
- "Add Y"
- "Make it do Z"
- "I want a feature that..."

Do NOT invoke for questions, explanations, bug reports with clear reproduction steps, or requests to read/explore code.

## Process

Ask one clarifying question at a time. Do not present a list of questions. Do not start implementing.

**Question 1 — Problem:** What specific problem does this solve? Who experiences it and when?

**Question 2 — Done:** What does success look like? How will you know when it's working?

**Question 3 — Constraints:** Are there things this must not do, or boundaries it must stay within?

**Question 4 — Scope:** What is explicitly out of scope for this change?

Once you have answers, produce the requirements brief.

## Requirements Brief Format

```
## Requirements Brief

**Problem:** [One sentence: what breaks or is missing and for whom]

**Acceptance Criteria:**
- [ ] [Specific, testable condition]
- [ ] [Specific, testable condition]

**Constraints:** [What this must not do or must stay within]

**Out of Scope:** [What will not be addressed in this change]
```

## Sign-Off Gate

Present the brief and ask: "Does this match what you have in mind, or should we adjust anything before proceeding?"

Do NOT write any code until the user confirms the brief.
```

- [ ] **Step 3: Verify frontmatter is present**

Run: `head -5 skills/requirements/SKILL.md`
Expected: output starts with `---` followed by `name: requirements`

- [ ] **Step 4: Commit**

```bash
git add skills/requirements/SKILL.md
git commit -m "feat: add requirements skill"
```

---

### Task 4: Groundwork Command

**Files:**
- Create: `commands/groundwork.md`

- [ ] **Step 1: Create the commands directory**

```bash
mkdir -p commands
```

- [ ] **Step 2: Create groundwork.md**

Create `commands/groundwork.md`:

```markdown
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
```

- [ ] **Step 3: Verify frontmatter fields**

Run: `head -6 commands/groundwork.md`
Expected: output shows `---`, `description:`, `argument-hint:`, `allowed-tools:` fields

- [ ] **Step 4: Commit**

```bash
git add commands/groundwork.md
git commit -m "feat: add /groundwork command"
```

---

### Task 5: Session-Start Hook

**Files:**
- Create: `hooks/hooks.json`
- Create: `hooks/session-start`

- [ ] **Step 1: Create the hooks directory**

```bash
mkdir -p hooks
```

- [ ] **Step 2: Create hooks.json**

Create `hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start",
            "async": false
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 3: Verify hooks.json is valid JSON**

Run: `python3 -m json.tool hooks/hooks.json`
Expected: JSON echoed back with no error

- [ ] **Step 4: Create session-start script**

Create `hooks/session-start`:

```bash
#!/usr/bin/env bash
set -euo pipefail

context="[groundwork] SDLC discipline plugin is active. Run /groundwork to see available workflows."

if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  printf '{\n  "hookSpecificOutput": {\n    "hookEventName": "SessionStart",\n    "additionalContext": "%s"\n  }\n}\n' "$context"
else
  printf '{\n  "additionalContext": "%s"\n}\n' "$context"
fi

exit 0
```

- [ ] **Step 5: Make the script executable**

```bash
chmod +x hooks/session-start
```

- [ ] **Step 6: Verify the script runs and outputs valid JSON**

Run: `hooks/session-start | python3 -m json.tool`
Expected: JSON echoed back — you'll see `hookSpecificOutput` or `additionalContext` depending on whether `CLAUDE_PLUGIN_ROOT` is set. Either is correct.

- [ ] **Step 7: Commit**

```bash
git add hooks/hooks.json hooks/session-start
git commit -m "feat: add session-start hook"
```

---

### Task 6: Requirements Analyst Agent Stub

**Files:**
- Create: `agents/requirements-analyst.md`

- [ ] **Step 1: Create the agents directory**

```bash
mkdir -p agents
```

- [ ] **Step 2: Create requirements-analyst.md**

Create `agents/requirements-analyst.md`:

```markdown
---
description: Analyzes user requests to produce structured requirements briefs with problem statement, constraints, acceptance criteria, and out-of-scope boundaries.
---

# Requirements Analyst

You are a requirements analyst. Your job is to take a vague user request and produce a structured requirements brief before any implementation begins.

## Your Output

Always produce a brief in this format:

```
## Requirements Brief

**Problem:** [One sentence: what breaks or is missing and for whom]

**Acceptance Criteria:**
- [ ] [Specific, testable condition]
- [ ] [Specific, testable condition]

**Constraints:** [What this must not do or must stay within]

**Out of Scope:** [What will not be addressed in this change]
```

## How to Get There

Ask the user one question at a time:

1. What specific problem does this solve?
2. What does success look like?
3. What constraints apply?
4. What is out of scope?

Do not ask all questions at once. Do not start implementing. Do not write code.

When you have answers to all four, present the brief and ask for confirmation before handing back to the main session.
```

- [ ] **Step 3: Verify frontmatter is present**

Run: `head -4 agents/requirements-analyst.md`
Expected: output starts with `---` followed by `description:`

- [ ] **Step 4: Commit**

```bash
git add agents/requirements-analyst.md
git commit -m "feat: add requirements-analyst agent stub"
```

---

## Verification

After all tasks are complete, verify the plugin loads correctly:

- [ ] **Register as local marketplace source** in Claude Code: add the repo path as a marketplace URL in settings, then install the `groundwork` plugin
- [ ] **Open a new Claude Code session** — check that the session-start hook context appears (`[groundwork] SDLC discipline plugin is active.`)
- [ ] **Run `/groundwork`** — confirm the command responds with the workflow list
- [ ] **Make a vague request** (e.g., "build me a login form") — confirm the `requirements` skill triggers and asks a clarifying question before touching code
- [ ] **Check CLAUDE.md is visible** in Claude's project context (look for "Groundwork Plugin" in the system context)
