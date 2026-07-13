# Example requirement sets

Two complete artifact sets produced by the Groundwork requirements pipeline. Each
is an independent project with its own ID space — `FR-001` in one has nothing to do
with `FR-001` in the other — so each is validated on its own:

| Set | Path | Size |
| --- | --- | --- |
| GDPR data-subject rights | `gdpr/requirements/` | 8 requirements |
| Desktop tamagotchi | `tamagotchi/requirements/` | 22 requirements |

Validate a set by pointing the tools at that set's `requirements/` directory:

```bash
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/gdpr/requirements
python3 skills/requirements/scripts/lint_requirements_content.py docs/requirements/examples/gdpr/requirements
```

Do **not** point them at `docs/requirements/examples` — the walk is recursive, and
the two sets' ID spaces collide.

The tamagotchi set also ships a single-document rendering (`tamagotchi/CONSOLIDATED.md`)
and the dev-log draft that discusses it.
