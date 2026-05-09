# groundwork

A Claude Code plugin that brings structure to software development — requirements gathering, planning, and SDLC discipline before you write a line of code.

> Built as an alternative to "vibe coding": lay the groundwork first.

## What it does

Groundwork intercepts vague implementation requests and guides you through a lightweight requirements process before anything gets built. Instead of jumping straight to code, you get a structured brief with acceptance criteria that both you and Claude agree on.

## Installation

**From Claude Code:**

```
/plugin marketplace add https://github.com/Stormbreaker9000/groundwork
```

Then install the plugin:

```
/plugin install groundwork@groundwork-dev
```

## Usage

Run `/groundwork` in any Claude Code session to see available workflows.

When you make a vague request like *"build me a login form"* or *"add dark mode"*, the `requirements` skill will pause and ask clarifying questions before touching code.

## Workflows

| Workflow | Trigger | Description |
|---|---|---|
| `requirements` | "build X", "add Y", "make it do Z" | Turns vague requests into a structured brief with acceptance criteria before any code is written |

### Requirements Brief format

```
## Requirements Brief

**Problem:** [One sentence: what breaks or is missing and for whom]

**Acceptance Criteria:**
- [ ] [Specific, testable condition]

**Constraints:** [What this must not do or must stay within]

**Out of Scope:** [What will not be addressed in this change]
```

Claude will not write code until you sign off on the brief.

## Roadmap

- [ ] Architecture design workflow
- [ ] Test planning workflow
- [ ] Release checklist workflow
- [ ] `PreToolUse` hooks to enforce requirements brief before implementation
- [ ] `requirements-analyst` agent for fully autonomous requirements gathering

## Plugin structure

```
groundwork/
├── .claude-plugin/       # Plugin manifests
├── skills/               # Markdown instruction sets (skill triggers)
├── commands/             # Slash commands (/groundwork)
├── hooks/                # Event-driven scripts (SessionStart)
└── agents/               # Dispatched subagents
```

## License

MIT
