# Groundwork

This repository builds the **groundwork** Claude Code plugin: SDLC discipline
workflows that put structure in front of code.

## Layout

`plugin/` is the published surface — the whole of it, and nothing outside it,
is copied into every install (`.claude-plugin/marketplace.json` points at it).
Adding a file there adds it to every user's download; `tests/test_plugin_package.py`
is what enforces the boundary.

Everything else is repository-only: `tests/` (pytest, with the fixtures that
used to ship), `site/` (the Nextra documentation site), `docs/` (specs, plans
and research), `assets/` (brand).

## Working here

- Python is stdlib-only, everywhere, including the site scripts.
- `site/content/_generated/` is committed and CI fails on drift. After editing
  a linter rule, either JSON Schema, an agent's frontmatter `description:`,
  either `SKILL.md`'s coverage list, or an orchestrator's stage headings or
  hand-off YAML, re-run `python3 site/scripts/export_reference.py`.
- `python3 -m pytest -q` runs everything from the repository root.
