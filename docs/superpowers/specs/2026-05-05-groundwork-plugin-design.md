# Groundwork Plugin — Scaffold Design

**Date:** 2026-05-05
**Status:** Approved

## Purpose

Groundwork is a Claude Code plugin that supports disciplined software development by guiding users through structured SDLC workflows. The immediate goal is a working scaffold that proves the plugin is picked up by Claude — one real example of each pillar (skill, command, hook, agent) — so every future capability has a clear, verified home to grow into.

The name reflects the intent: lay groundwork before building, rather than "vibe coding" into implementation.

## Directory Structure

```
groundwork/
├── .claude-plugin/
│   ├── plugin.json          # Plugin identity: name, version, author, description
│   └── marketplace.json     # Local dev self-registration (points to ./)
├── package.json             # npm-style metadata (type: module)
├── CLAUDE.md                # Injected into Claude's context when plugin is active
├── README.md                # Human-facing documentation
├── .gitignore
├── skills/
│   └── requirements/
│       └── SKILL.md         # Requirements-gathering workflow
├── commands/
│   └── groundwork.md        # /groundwork slash command
├── hooks/
│   ├── hooks.json           # Event → script wiring
│   └── session-start        # Shell script, runs on SessionStart
└── agents/
    └── requirements-analyst.md  # Stub agent for requirements gathering
```

## Manifests

### `.claude-plugin/plugin.json`

Plugin identity file. Required by the Claude Code plugin loader.

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

### `.claude-plugin/marketplace.json`

Enables local development registration. Point Claude Code at this directory as a marketplace source.

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

### `package.json`

```json
{
  "name": "groundwork",
  "version": "0.1.0",
  "type": "module"
}
```

## CLAUDE.md

Injected into Claude's context when the plugin is active. Establishes the plugin's presence and intent without being verbose.

Content: a short paragraph naming the plugin, its purpose (disciplined SDLC workflows), and a pointer to `/groundwork` for available workflows. This is the primary proof-of-pickup signal during development.

## Skills

### `skills/requirements/SKILL.md`

The first skill. Triggers when a user makes a vague implementation request and guides the session through structured requirements-gathering before any code is written.

**Frontmatter:**
```yaml
---
name: requirements
description: Use before implementing any feature or change - turns vague requests into structured requirements with acceptance criteria before any code is written.
---
```

**Workflow the skill teaches Claude:**
1. Detect a vague implementation request ("build X", "add Y", "make it do Z")
2. Pause before touching code
3. Ask one clarifying question at a time: what problem does this solve, who needs it, what does done look like, what's out of scope
4. Produce a structured brief: Problem, Constraints, Acceptance Criteria, Out of Scope
5. Get explicit user sign-off on the brief before proceeding

The description field is trigger-accurate: scoped narrowly enough not to fire on every message, but reliably on feature/change requests.

## Commands

### `commands/groundwork.md` → `/groundwork`

The plugin's entry point slash command.

**Frontmatter:**
```yaml
description: Overview of the groundwork plugin — lists available SDLC workflows and how to use them
argument-hint: "[workflow-name]"
allowed-tools: ["Read"]
```

**Behavior:**
- No args: lists all available workflows with one-line descriptions and how to trigger each
- With arg (e.g., `/groundwork requirements`): focused explanation of that workflow

This command grows with the plugin — as new skills and workflows are added, `/groundwork` becomes their index. It also serves as an immediate verification tool during development: if `/groundwork` responds correctly, the command wiring is confirmed.

## Hooks

### `hooks/hooks.json`

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

### `hooks/session-start`

A shell script that runs on every session start. For the scaffold it prints a short confirmation that the groundwork plugin is active. This is the most direct proof-of-pickup signal during development: if you see the banner, the hook wiring works.

The script is kept minimal — a single `echo` to stdout. Future sessions can inject project-specific SDLC context here.

## Agents

### `agents/requirements-analyst.md`

A stub agent definition. Establishes the slot for a future agent that can be dispatched to gather and structure requirements independently.

**Frontmatter:**
```yaml
description: Analyzes user requests to produce structured requirements briefs with problem statement, constraints, acceptance criteria, and out-of-scope boundaries.
```

**Body:** A short role description and placeholder behavior. No active logic in the scaffold — the file's presence proves the directory convention and gives a target for the first real agent implementation.

## Verification Checklist

After scaffolding, confirm pickup by:

1. Register the local directory as a marketplace source in Claude Code settings
2. Open a new Claude Code session in any project directory
3. Check the session-start hook fires (banner visible in terminal output)
4. Confirm `groundwork` appears in the installed plugins list
5. Run `/groundwork` — confirm the command responds
6. Make a vague feature request — confirm the `requirements` skill triggers

## Future Growth

The scaffold is intentionally minimal. Planned additions as the plugin matures:

- Additional SDLC skills: architecture design, test planning, release prep, incident response
- Active hook scripts: pre-tool-use guards that intercept implementation attempts without a requirements brief
- Real agent dispatch: requirements-analyst as a dispatched subagent
- Marketplace publication once the plugin is stable
