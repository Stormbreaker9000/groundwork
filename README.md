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
| `requirements` | "build X", "add Y", "make it do Z" | Turns a vague request into atomic, validated requirement artifacts under `.sdlc/requirements/` — functional and non-functional requirements, constraints, business rules, assumptions, a glossary and a Definition of Done |
| `design` | a validated requirement set exists | Turns requirements into an architecture under `.sdlc/design/` — components, interface contracts, MADR architecture decision records and C4 diagrams, each traced back to the requirements that motivated it |

Claude will not write code until you sign off.

## Documentation

Full documentation, including the content-rule reference, is at
**https://stormbreaker9000.github.io/groundwork/**.

## Roadmap

- [x] Architecture design workflow
- [ ] Test planning workflow
- [ ] Release checklist workflow
- [ ] `PreToolUse` hooks to enforce requirements brief before implementation

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
