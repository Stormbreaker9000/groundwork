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
