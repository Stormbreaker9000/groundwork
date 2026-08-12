# M2 Mixed-Mode Interaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move `interaction` from the interface contract onto each operation, so a contract whose operations differ can describe itself honestly and the critic's prose-versus-field rule becomes checkable.

**Architecture:** `interaction` is deleted from the interface branch of `design.schema.json` and added as a required property of `operations.items`, keeping the same two-value enum. `unevaluatedProperties: false` then rejects a stale contract-level field on the schema path; the stdlib fallback path gains its first nested check plus a named retired-field error, because it cannot see either. The four agent contracts and the worked example follow the shape.

**Tech Stack:** JSON Schema draft 2020-12; Python 3 standard library plus optional `pyyaml`/`jsonschema`; pytest; Markdown agent-definition files.

**Spec:** `docs/superpowers/specs/2026-08-11-m2-mixed-mode-interaction-design.md`

## Global Constraints

- **`mixed` is never a stored value.** No enum anywhere gains a third member. A mixed contract is one whose operations disagree; consumers that want the word compute it. (Spec D1.)
- **The enum stays exactly `["synchronous", "asynchronous"]`**, moved verbatim onto the operation. (Spec D1.)
- **The contract-level field is retired, not deprecated.** There is no transition period in which both shapes validate. (Spec D2.)
- **`error_modes` stays contract-level.** Do not move it, split it, or add per-operation error modes. (Spec "Out of scope".)
- **The consumer-set guard is instructional only.** Do not add a critic check, a validator rule, or a schema constraint for it. (Spec D4.)
- **Never edit `critique-report.yaml` or `drivers.md`** under `docs/requirements/examples/`. They are output of a real pipeline run under the old schema and are accurate as history. (Spec D7.)
- **Do not split IF-006.** It is recorded as a divergence; acting on it is STO-219. (Spec "Out of scope".)
- **Do not touch `diagrams/`, `index.yaml`, `requirement.schema.json`, or `validate_traceability.py`.** None reads `interaction`.
- Baseline before starting: `python3 -m pytest skills/ -q` reports **154 passed**.

---

## File Structure

| File | Responsibility | Change |
| --- | --- | --- |
| `skills/design/schema/design.schema.json` | The contract the whole stage is gated on | Modify — interface branch, line 5 description, line 176 `$comment` |
| `skills/design/scripts/validate_design.py` | Structural gate, both paths | Modify — fallback required list, enums, new nested check |
| `skills/design/scripts/tests/test_validate_design.py` | Suite for the above | Modify — 2 stale assertions, 8 new cases, 1 new regression |
| `skills/design/scripts/tests/fixtures/valid/interfaces/IF-001-payment-api.md` | Conformant fixture | Modify |
| `skills/design/scripts/tests/fixtures/invalid/dangling_provider/interfaces/IF-001-dangling-provider.md` | Invalid-for-another-reason fixture; must stay valid on `interaction` | Modify |
| `docs/requirements/examples/tamagotchi/design/interfaces/*.md` | 12 worked-example artifacts | Modify |
| `docs/requirements/examples/tamagotchi/README.md` | Honest record of the run | Modify — findings list and count |
| `agents/interface-specialist.md` | Teaches the shape and the guard | Modify — 4 sites + 1 new example |
| `agents/design-orchestrator.md` | Hand-off shape | Modify — 1 template |
| `agents/design-formatter.md` | Writes the frontmatter | Modify — template + branch rule |
| `agents/design-critic.md` | The prose-versus-field gate | Modify — rule at line 68 |
| `skills/design/SKILL.md` | Human-facing summary | Modify — summary line |

Four tasks. Task 1 changes the shape and both gates. Task 2 migrates the worked example and adds the structural regression that was missing. Tasks 3 and 4 update the agent contracts that produce the shape.

---

### Task 1: Schema, both validator paths, and fixtures

The schema, the fallback validator, and the fixtures must move together: the moment the schema changes, `test_valid_set_passes` fails on the old fixture, and `_FALLBACK_REQUIRED_BY_TYPE` still demanding a top-level `interaction` fails `test_valid_set_passes_in_fallback_mode`. There is no smaller green increment.

**Files:**
- Modify: `skills/design/schema/design.schema.json:5,176,187-242`
- Modify: `skills/design/scripts/validate_design.py:142-155,181-206`
- Modify: `skills/design/scripts/tests/test_validate_design.py:265-272,347-367`
- Modify: `skills/design/scripts/tests/fixtures/valid/interfaces/IF-001-payment-api.md:17-22`
- Modify: `skills/design/scripts/tests/fixtures/invalid/dangling_provider/interfaces/IF-001-dangling-provider.md:16-19`

**Interfaces:**
- Consumes: `vd._fallback_validate(data: Dict[str, Any]) -> List[str]`, `vd.core.make_validator(schema_path)`, `core_validator()` and `_schema_errors(validator, data)` — all already in the suite.
- Produces: `vd._FALLBACK_OPERATION_INTERACTIONS: Set[str]`; `vd._fallback_check_operations(data: Dict[str, Any]) -> List[str]`. Later tasks rely on the frontmatter shape only, not on these names.

- [ ] **Step 1: Move `_base_interface` to the target shape**

This comes first so the new tests fail cleanly rather than throwing `KeyError`
on a key the builder does not yet carry. It turns several existing tests red
until Step 10 — that is the red phase, not a mistake.

In `skills/design/scripts/tests/test_validate_design.py`, change `_base_interface` (lines 265–272) to:

```python
def _base_interface():
    return {
        "id": "IF-001", "type": "interface", "title": "x", "description": "x",
        "traces_from": [], "traces_to": {}, "status": "draft", "confidence": "high",
        "created_at": "2026-07-18", "provider": "CMP-001",
        "operations": [{"name": "a", "summary": "b", "interaction": "synchronous"}],
        "error_modes": ["boom"],
    }
```

- [ ] **Step 2: Write the failing schema-path tests**

Append to `skills/design/scripts/tests/test_validate_design.py`, after `test_interface_field_on_component_is_rejected` (line 303):

```python
# ---------------------------------------------------------------------------
# STO-216: interaction is per-operation. `mixed` is never a stored value — a
# mixed contract is one whose operations disagree.
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not vd.core.HAVE_JSONSCHEMA, reason="jsonschema not installed")
def test_schema_rejects_contract_level_interaction():
    """The retired field. Rejected by unevaluatedProperties, not by an explicit
    rule: once `interaction` leaves the interface branch's `properties`, a stale
    one is unevaluated. Get the branch edit wrong and this silently accepts."""
    validator = core_validator()
    interface = _base_interface()
    interface["interaction"] = "synchronous"
    errors = _schema_errors(validator, interface)
    assert errors, "schema wrongly accepted a contract-level interaction"


@pytest.mark.skipif(not vd.core.HAVE_JSONSCHEMA, reason="jsonschema not installed")
def test_schema_requires_operation_interaction():
    validator = core_validator()
    interface = _base_interface()
    del interface["operations"][0]["interaction"]
    errors = _schema_errors(validator, interface)
    assert errors, "schema wrongly accepted an operation with no interaction"


@pytest.mark.skipif(not vd.core.HAVE_JSONSCHEMA, reason="jsonschema not installed")
def test_schema_rejects_bad_operation_interaction():
    validator = core_validator()
    interface = _base_interface()
    interface["operations"][0]["interaction"] = "eventual"
    errors = _schema_errors(validator, interface)
    assert errors, "schema wrongly accepted an out-of-enum operation interaction"


@pytest.mark.skipif(not vd.core.HAVE_JSONSCHEMA, reason="jsonschema not installed")
def test_schema_rejects_mixed_as_an_operation_value():
    """`mixed` is a reading of a contract, never a stored value (spec D1)."""
    validator = core_validator()
    interface = _base_interface()
    interface["operations"][0]["interaction"] = "mixed"
    errors = _schema_errors(validator, interface)
    assert errors, "schema wrongly accepted 'mixed' as an operation value"


@pytest.mark.skipif(not vd.core.HAVE_JSONSCHEMA, reason="jsonschema not installed")
def test_schema_accepts_mixed_contract():
    """The case that could not exist before: one contract, two modes."""
    validator = core_validator()
    interface = _base_interface()
    interface["operations"] = [
        {"name": "record", "summary": "Accept an entry.", "interaction": "asynchronous"},
        {"name": "flush", "summary": "Make accepted entries durable.", "interaction": "synchronous"},
    ]
    assert _schema_errors(validator, interface) == []
```

- [ ] **Step 3: Run them to verify they fail**

Run: `python3 -m pytest skills/design/scripts/tests/test_validate_design.py -k "schema_re or schema_acc" -v`

Expected: **1 failed, 4 passed** — and the 4 passes are vacuous, which is worth understanding before continuing.

`test_schema_accepts_mixed_contract` is the only genuinely discriminating test right now. It fails because the old `operations.items` carries `additionalProperties: false` with no `interaction` property, so *any* per-operation `interaction` is rejected.

That same fact is why the other four pass for the wrong reason: they assert only that errors exist, and errors do exist — not because a contract-level `interaction` is retired or an enum is enforced, but because the operations carry a key the old schema does not allow. Their real assertion is made in Step 7: after the schema change they must **still** pass, now for the stated reason, while the mixed test flips green. A test that is green in both phases is only evidence when you know why it was green in the first.

If `test_schema_accepts_mixed_contract` passes here, stop — the schema is not in the state this plan assumes.

- [ ] **Step 4: Move `interaction` onto the operation in the schema**

In `skills/design/schema/design.schema.json`, replace the interface branch's `then` block (lines 187–242) with:

```json
      "then": {
        "required": [
          "provider",
          "operations",
          "error_modes"
        ],
        "properties": {
          "provider": {
            "type": "string",
            "description": "The single component that provides this contract. Exactly one CMP- ID.",
            "pattern": "^CMP(-[A-Z0-9]+)*-[0-9]{3,}$"
          },
          "operations": {
            "type": "array",
            "description": "The operations this contract exposes, at architecture altitude (name + summary + interaction; no payload schemas).",
            "minItems": 1,
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "name",
                "summary",
                "interaction"
              ],
              "properties": {
                "name": {
                  "type": "string",
                  "minLength": 1
                },
                "summary": {
                  "type": "string",
                  "minLength": 1
                },
                "interaction": {
                  "type": "string",
                  "description": "Interaction style for THIS operation: `synchronous` when the consumer blocks on the result and cannot proceed without it, `asynchronous` otherwise. Declared per operation because interaction is a property of an operation, not of the contract bundling it — `flush` blocks and `record` does not, whatever contract holds them. A contract whose operations disagree is mixed-mode, which needs no stored name of its own (STO-216).",
                  "enum": [
                    "synchronous",
                    "asynchronous"
                  ]
                }
              }
            }
          },
          "error_modes": {
            "type": "array",
            "description": "How this contract can fail. An interface that does not say how it fails is a gap; at least one mode is required.",
            "minItems": 1,
            "items": {
              "type": "string",
              "minLength": 1
            },
            "uniqueItems": true
          }
        }
      }
```

- [ ] **Step 5: Correct the two schema comments that still name it as a contract field**

Line 5, `"description"` — replace the substring:

`interface specs (IF-) carry provider/operations/interaction/error_modes.`

with:

`interface specs (IF-) carry provider/operations/error_modes, with interaction declared per operation (STO-216).`

Line 176, `"$comment"` — replace the substring:

`provider/operations/interaction/error_modes are valid only on an interface.`

with:

`provider/operations/error_modes are valid only on an interface, and a retired contract-level interaction is left unevaluated and so rejected.`

- [ ] **Step 6: Update both fixtures**

In `skills/design/scripts/tests/fixtures/valid/interfaces/IF-001-payment-api.md`, replace lines 17–22:

```yaml
operations:
  - name: authorize
    summary: Reserve funds on a card without capturing them.
    interaction: synchronous
  - name: capture
    summary: Capture previously authorized funds.
    interaction: synchronous
```

(Both operations block — this fixture stays a uniform contract. End-to-end coverage of a genuinely mixed contract through the CLI comes from the tamagotchi regression in Task 2, which has four of them from real data.)

In `skills/design/scripts/tests/fixtures/invalid/dangling_provider/interfaces/IF-001-dangling-provider.md`, replace lines 16–19:

```yaml
operations:
  - name: ping
    summary: A single trivial operation.
    interaction: synchronous
```

This fixture must fail only on `provider: CMP-999`. Leaving a stale `interaction` here would make it fail for two reasons and let a regression in the provider check hide.

- [ ] **Step 7: Run the schema-path tests to verify they pass**

Run: `python3 -m pytest skills/design/scripts/tests/test_validate_design.py -k "schema_re or schema_acc" -v`

Expected: 5 passed.

- [ ] **Step 8: Write the failing fallback-path tests**

Append to `skills/design/scripts/tests/test_validate_design.py`, after `test_fallback_flags_bad_enum` (line 332):

```python
def test_fallback_flags_retired_contract_level_interaction():
    """Deliberately NOT parity with the schema path. There,
    unevaluatedProperties rejects the stale field generically; here nothing
    would, and reduced mode would accept a field nothing reads — the silent-drop
    class STO-102 fixed in artifact_core.py."""
    iface = _base_interface()
    iface["interaction"] = "synchronous"
    errors = vd._fallback_validate(iface)
    assert any("per operation" in e for e in errors), errors


def test_fallback_flags_missing_operation_interaction():
    iface = _base_interface()
    del iface["operations"][0]["interaction"]
    errors = vd._fallback_validate(iface)
    assert any("interaction" in e and "operations[0]" in e for e in errors), errors


def test_fallback_flags_bad_operation_interaction_enum():
    iface = _base_interface()
    iface["operations"][0]["interaction"] = "eventual"
    errors = vd._fallback_validate(iface)
    assert any("eventual" in e and "operations[0]" in e for e in errors), errors


def test_fallback_accepts_mixed_contract():
    iface = _base_interface()
    iface["operations"] = [
        {"name": "record", "summary": "Accept an entry.", "interaction": "asynchronous"},
        {"name": "flush", "summary": "Make accepted entries durable.", "interaction": "synchronous"},
    ]
    assert vd._fallback_validate(iface) == []


def test_fallback_ignores_operations_on_a_component():
    """The nested check is interface-only; a component has no `operations`."""
    assert vd._fallback_validate(_base_component()) == []
```

- [ ] **Step 9: Run them to verify they fail**

Run: `python3 -m pytest skills/design/scripts/tests/test_validate_design.py -k fallback -v`

Expected: FAIL. The four new interface cases fail because `_fallback_validate` has no nested check, and `test_fallback_accepts_valid_per_type` also fails once `_base_interface` changes in Step 10 — it is fixed by the same edit.

- [ ] **Step 10: Add the nested check to the fallback path**

In `skills/design/scripts/validate_design.py`, change `_FALLBACK_REQUIRED_BY_TYPE["interface"]` (line 144) from:

```python
    "interface": ["provider", "operations", "interaction", "error_modes"],
```

to:

```python
    # `interaction` is per-operation as of STO-216; checked by
    # `_fallback_check_operations`, not by this flat list.
    "interface": ["provider", "operations", "error_modes"],
```

Delete the `"interaction"` line from `_FALLBACK_ENUMS` (line 152) — that dict is a flat scan of top-level keys and cannot reach into a list of mappings. Then add, immediately after the `_FALLBACK_ENUMS` block:

```python
# Per-operation interaction enum (STO-216). Kept separate from _FALLBACK_ENUMS
# because that dict only scans top-level keys.
_FALLBACK_OPERATION_INTERACTIONS = {"synchronous", "asynchronous"}
```

Add this function immediately above `_fallback_validate`:

```python
def _fallback_check_operations(data: Dict[str, Any]) -> List[str]:
    """Per-operation `interaction` checks for the stdlib path (STO-216).

    Also reports a retired contract-level `interaction`. That check has no
    counterpart in `_FALLBACK_ENUMS` on purpose: on the schema path
    `unevaluatedProperties: false` rejects the stale field, and this path cannot
    express that, so without an explicit check reduced mode would accept a field
    nothing reads.
    """
    errors: List[str] = []
    if "interaction" in data:
        errors.append(
            "schema(fallback): 'interaction' is declared per operation, not on "
            "the contract — move it into each entry of 'operations' (STO-216)"
        )
    operations = data.get("operations")
    if not isinstance(operations, list):
        return errors  # presence/shape is the required-field check's business
    for index, operation in enumerate(operations):
        if not isinstance(operation, dict):
            errors.append(f"schema(fallback): operations[{index}] must be a mapping")
            continue
        name = operation.get("name", "?")
        value = operation.get("interaction")
        if value in (None, ""):
            errors.append(
                f"schema(fallback): operations[{index}] ('{name}') missing "
                "required field 'interaction'"
            )
        elif value not in _FALLBACK_OPERATION_INTERACTIONS:
            errors.append(
                f"schema(fallback): operations[{index}] ('{name}') "
                f"'interaction'='{value}' not in "
                f"{sorted(_FALLBACK_OPERATION_INTERACTIONS)}"
            )
    return errors
```

Then wire it into `_fallback_validate`, immediately before the `traces_to` guard (line 200):

```python
    if data.get("type") == "interface":
        errors.extend(_fallback_check_operations(data))
```

- [ ] **Step 11: Update the parser assertion that pins the old shape**

`_base_interface` was already moved in Step 1. The remaining stale assertion is in `test_stdlib_parser_handles_list_of_mappings` (lines 347–367) — update the expected parse and the key set — the parser now has to carry three-key mappings through a list, which is what this test exists to pin:

```python
    assert data["operations"] == [
        {"name": "authorize",
         "summary": "Reserve funds on a card without capturing them.",
         "interaction": "synchronous"},
        {"name": "capture",
         "summary": "Capture previously authorized funds.",
         "interaction": "synchronous"},
    ]
    # No phantom keys leaked from inside operations into the top-level mapping.
    assert "summary" not in data
    assert "interaction" not in data
    assert "- name" not in data
    assert set(data) == {
        "id", "type", "title", "description", "traces_from", "traces_to",
        "status", "confidence", "created_at", "provider", "operations",
        "error_modes",
    }
```

The added `assert "interaction" not in data` is load-bearing: `interaction` is now a key *inside* each operation, so if the stdlib parser ever regresses to flattening list items into the parent mapping, this is the assertion that catches it.

- [ ] **Step 12: Run the whole suite**

Run: `python3 -m pytest skills/ -q`

Expected: **164 passed** (154 baseline + 10 new).

- [ ] **Step 13: Commit**

```bash
git add skills/design/schema/design.schema.json \
        skills/design/scripts/validate_design.py \
        skills/design/scripts/tests/test_validate_design.py \
        skills/design/scripts/tests/fixtures/
git commit -m "feat(sto-216): declare interaction per operation, not per contract

Interaction is a property of an operation: flush blocks and record does not,
whatever contract bundles them. The field moves into operations.items and is
retired from the interface branch, where unevaluatedProperties:false now rejects
a stale one. No enum gains a third value — a mixed contract is one whose
operations disagree, which needs no stored name.

The stdlib fallback gains its first nested check plus an explicit retired-field
error. That error has no counterpart on the schema path on purpose: there
unevaluatedProperties catches it, here nothing would, and reduced mode would
accept a field nothing reads.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Migrate the worked example, and add the structural gate it never had

The only regression over the worked example is `test_shipped_tamagotchi_example_is_clean` (`test_validate_traceability.py:452`), and that tool never schema-validates. Nothing runs `validate_design.py` over `docs/requirements/examples/`, so after Task 1 all 12 interface artifacts are invalid and no test says so. The gate is written first, watched fail, then satisfied.

**Files:**
- Modify: `skills/design/scripts/tests/test_validate_design.py` — add `REPO_ROOT` and one regression test
- Modify: `docs/requirements/examples/tamagotchi/design/interfaces/*.md` — all 12
- Modify: `docs/requirements/examples/tamagotchi/README.md`

**Interfaces:**
- Consumes: `run(design_dir)` (line 25) and `HERE` (line 18), both already in the suite.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the failing regression test**

In `skills/design/scripts/tests/test_validate_design.py`, add below `SCHEMA = vd.default_schema_path()` (line 22):

```python
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
```

and append at the end of the file:

```python
# ---------------------------------------------------------------------------
# Real-world regression: the shipped tamagotchi worked example
# ---------------------------------------------------------------------------
def test_shipped_tamagotchi_example_passes_structural_gate(capsys):
    """The worked example must satisfy the schema it ships alongside.

    `test_validate_traceability.py:452` already pins this set, but that tool
    never schema-validates — so until STO-216 nothing ran THIS validator over
    `docs/requirements/examples/`. A shape change could stale all 12 interface
    artifacts with nothing turning red, which is how STO-216 found them.
    """
    example = os.path.join(
        REPO_ROOT, "docs", "requirements", "examples", "tamagotchi", "design"
    )
    code = run(example)
    out = capsys.readouterr().out
    assert code == 0, out
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 -m pytest skills/design/scripts/tests/test_validate_design.py::test_shipped_tamagotchi_example_passes_structural_gate -v`

Expected: FAIL, reporting a contract-level `interaction` and a missing per-operation one on each of the 12 interfaces.

- [ ] **Step 3: Migrate the eight uniform interfaces**

For each file below, delete the top-level `interaction:` line and add `interaction: <value>` as a third key on every entry of `operations`, indented to align with `summary`. Every operation in these eight takes the value the contract carried:

| File | Operations | Value for all |
| --- | --- | --- |
| `IF-001-wall-clock-time-source.md` | `now`, `elapsed_since` | `synchronous` |
| `IF-003-durable-pet-state-persistence.md` | `load`, `commit` | `synchronous` |
| `IF-004-decay-computation.md` | `apply_decay`, `maximum_offline_interval` | `synchronous` |
| `IF-007-mood-evaluation.md` | `current_mood` | `synchronous` |
| `IF-008-care-action-application.md` | `apply_care_action`, `end_sleep` | `synchronous` |
| `IF-009-session-state-seeding.md` | `seed_from_snapshot`, `seed_defaults` | `synchronous` |
| `IF-010-care-reminder-preference-control.md` | `reminders_enabled`, `set_reminders_enabled` | `synchronous` |
| `IF-011-reminder-preference-persistence.md` | `read_reminder_preference`, `write_reminder_preference` | `synchronous` |

Their `## Interaction` body sections are already correct for every operation and must not be reworded.

- [ ] **Step 4: Migrate the four mixed interfaces — frontmatter**

Same edit, but each operation takes its own value:

| File | Operation | Value |
| --- | --- | --- |
| `IF-002-diagnostic-log-recording.md` | `record` | `asynchronous` |
| | `flush` | `synchronous` |
| `IF-005-pet-stat-observation.md` | `current_stats` | `synchronous` |
| | `subscribe_to_stat_changes` | `asynchronous` |
| `IF-006-pet-lifecycle-state.md` | `current_lifecycle_state` | `synchronous` |
| | `subscribe_to_transitions` | `asynchronous` |
| `IF-012-desktop-notification-delivery.md` | `show_reminder` | `asynchronous` |
| | `delivery_available` | `synchronous` |

- [ ] **Step 5: Correct the four `## Interaction` body sections**

Each currently opens by claiming one mode for the whole contract. Keep the argument, correct the claim.

`IF-002-diagnostic-log-recording.md` — replace the `## Interaction` section with:

```markdown
## Interaction
Mixed: `record` is asynchronous, `flush` is synchronous, and that split is the
resolution of a genuinely close call worth naming. NFR-002's <= 1% idle
CPU budget argues against putting a synchronous disk write on the decay path, which
fires on a timer for the whole life of the process. NFR-007 pulls the other way: a
24-hour session must have zero missing transition entries, and an accepted-but-buffered
entry is exactly the one a crash loses. The resolution is asynchronous accept plus an
explicit `flush` that CMP-007 calls on the shutdown path and CMP-004 calls after a
lifecycle transition — and the caller does block on that flush, because a flush nobody
waits on cannot establish durability before process exit, which is the only thing flush
exists to do. What would tip `record` to synchronous is evidence that transition entries
are being lost in fault-injection testing; the cost of that would be a disk write inside
every stat mutation.
```

`IF-005-pet-stat-observation.md` — replace the `## Interaction` section with:

```markdown
## Interaction
Mixed: `subscribe_to_stat_changes` is asynchronous, `current_stats` synchronous.
Four components declared this capability as "track ... as they change",
and NFR-002's <= 1% idle CPU budget forbids each of them polling for it: FR-007's
one-second expression update and FR-009's one-minute reminder latency both have to be
met by being told, not by asking. The snapshot read exists for recovery and for the
first read after seeding, not as the normal path — but its caller does block on it, so
it is declared for what it is rather than folded into the contract's dominant mode.
What makes this medium rather than
high: the push mechanism is inferred from the budget, not declared. The consumers on
the webview side of the Tauri process boundary (CMP-006) receive these notifications
over an IPC hop that the in-process consumers do not, which is a latency asymmetry
FR-007's one-second bound has to absorb.
```

`IF-006-pet-lifecycle-state.md` — replace the `## Interaction` section with:

```markdown
## Interaction
Mixed: `current_lifecycle_state` is synchronous, `subscribe_to_transitions`
asynchronous. While one value had to cover both, this was the closest call in the set —
the three consumers want opposite things from one contract. CMP-003 must know the
lifecycle state *before* it mutates a Stat, because the Q-2 resolution makes death
permanent and no restorative arithmetic may run after it; that is a blocking read on the
write path. CMP-005 and CMP-006 want the opposite: a push, so that a
transition reaches the mood mapping and the window without polling under NFR-002.
Both are on the contract, and each is now declared for what it is. What the
single-value form forced was a choice between them, resolved toward the blocking read
because a missed push shows a stale mood for a moment while a missed gate revives a dead
pet. That choice is no longer necessary — but the divergent consumer sets underneath it
are, and they are what the README records: CMP-003 uses only the read, CMP-005 and
CMP-006 only the push, so this should have been two contracts.
```

`IF-012-desktop-notification-delivery.md` — replace the `## Interaction` section with:

```markdown
## Interaction
Mixed: `show_reminder` is asynchronous, `delivery_available` synchronous.
Nothing in the system waits on a reminder: the owner may not be at the
machine, the OS may hold or coalesce it, and no pet state depends on the outcome.
Blocking the scheduler on an OS call would also put a foreign latency inside the process
that NFR-002's idle budget has to cover. `delivery_available` is the exception a single
contract-level value could not express — the caller must have its answer before it
decides whether to try at all.
```

- [ ] **Step 6: Run the regression to verify it passes**

Run: `python3 -m pytest skills/design/scripts/tests/test_validate_design.py::test_shipped_tamagotchi_example_passes_structural_gate -v`

Expected: PASS.

- [ ] **Step 7: Update the README's findings list**

In `docs/requirements/examples/tamagotchi/README.md`, replace this bullet:

```markdown
- **Three interfaces** (`IF-002`, `IF-006`, `IF-012`) carry both a blocking and a
  non-blocking operation, but `interaction` is a single enum. The schema cannot express a
  mixed-mode contract, so no wording of these artifacts would satisfy the check.
```

with:

```markdown
- **One interface** (`IF-006`) carries a blocking read and a push whose consumers want
  different halves of it: `CMP-003` uses only `current_lifecycle_state`, `CMP-005` and
  `CMP-006` only `subscribe_to_transitions`. Divergent consumer sets are a split under
  the Interface Segregation rule — the same fault as `IF-003` below, and the finding
  survives for that reason rather than the one originally recorded.

  It was first written up here as one of *three* interfaces the schema could not
  describe, because `interaction` was then a single contract-level enum. STO-216 moved
  the field onto the operation, which cleared `IF-002` and `IF-012` — both have
  coincident consumer sets and are legitimately mixed — and left `IF-006`'s real defect
  visible underneath. A fourth, `IF-005`, had the identical shape and was never flagged
  at all: its body argued the contract's dominant mode ("the snapshot read exists for
  recovery and for the first read after seeding, not as the normal path") and the critic
  had no per-operation field to check that against. It is legitimately mixed and now
  says so. That a whole-contract field let one instance argue its way past the gate is
  the clearest evidence for why the field moved.
```

Then change the sentence introducing the list from `Seven findings remain open` to `Five findings remain open` — three responsibility phrasings, `IF-006`, and the `CMP-001` `traces_from` flag.

- [ ] **Step 8: Cross-reference from the granularity section**

At the end of the `IF-003` bullet in *Two granularity artifacts, recorded rather than fixed*, append:

```markdown
  `IF-006` above is the same fault reached from the other direction: it arrived
  disguised as a schema limitation and only became legible as a segregation problem
  once STO-216 removed the disguise.
```

- [ ] **Step 9: Run the whole suite**

Run: `python3 -m pytest skills/ -q`

Expected: **165 passed**. `test_shipped_tamagotchi_example_is_clean` still passes untouched — `validate_traceability.py` does not read `interaction`.

- [ ] **Step 10: Commit**

```bash
git add skills/design/scripts/tests/test_validate_design.py \
        docs/requirements/examples/tamagotchi/
git commit -m "feat(sto-216): migrate the worked example, and gate it structurally

The 12 tamagotchi interfaces move interaction onto their operations. Eight are
uniform. Four are mixed — IF-002, IF-005, IF-006, IF-012 — and each now declares
what its own body already described; the bodies keep their arguments and drop
only the claim that one mode covers the contract.

Adds the gate that should already have existed: nothing ran validate_design.py
over docs/requirements/examples/. The one regression there invokes
validate_traceability.py, which by its own constraints never schema-validates,
so these 12 artifacts had no structural check in CI and this change would have
staled them silently.

Two of the three standing interaction findings clear. IF-006 does not — it was a
segregation defect wearing a schema limitation, and it joins IF-003. IF-005 is
recorded as a fourth instance the critic never caught.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: The interface specialist — output shape, the guard, and a mixed example

**Files:**
- Modify: `agents/interface-specialist.md:228-241,250-262,275-281,378-392`

**Interfaces:**
- Consumes: nothing.
- Produces: the `draft_interfaces` shape Task 4's orchestrator and formatter templates must match exactly — `operations: [ { name, summary, interaction } ]` and no contract-level `interaction`.

- [ ] **Step 1: Rewrite the `interaction` section**

Replace the whole `## interaction` section (lines 228–241) with:

```markdown
## `interaction`

Declared **per operation**, not on the contract. `synchronous` when the consumer
blocks on the result and cannot proceed without it. `asynchronous` otherwise —
fire-and-forget, event-driven, queued, or polled-for-later.

Ask it of each operation separately. `flush` blocks and `record` does not, and
no fact about the contract holding them changes either answer. A contract whose
operations disagree is **mixed-mode**; there is no `mixed` value to write and
none is needed, because the mixture is visible in the operations themselves.

**Mixed is legal only when the operations share a consumer set.** If every
component that consumes this contract uses every operation on it, a mixed
contract is the right shape — splitting it would force consumers to depend on
two contracts they always use together. If the consumer sets diverge, so that
one component takes only the blocking operation and another only the
non-blocking one, that is **two interfaces**, not one mixed interface. The
Interface Segregation rule in the merge/split list above governs; mixed
interaction is not an exemption from it, and reaching for it to avoid a split is
the failure this rule exists to prevent.

When the choice for a given operation is genuinely close — a notification that
could reasonably be awaited or queued, a write that could be confirmed or
accepted-then-settled — **say so in the body**, naming what would tip it and
what it costs either way. The critic runs an ATAM-lite pass and looks for
sensitivity points; interaction style is one of the most common ones, because it
trades latency against coupling and failure isolation. Recording the tension is
how it reaches `drivers.md` instead of evaporating.
```

- [ ] **Step 2: Update the output template**

In the `## Output` block, replace:

```yaml
    operations: [ { name, summary } ]
    interaction: synchronous | asynchronous
```

with:

```yaml
    operations: [ { name, summary, interaction } ]   # interaction is PER OPERATION
```

- [ ] **Step 3: Update the schema-shape paragraph**

Replace the sentence:

`must be schema-shaped as returned: `type: interface`, `status: draft`, `interaction` one of the two enum values, `operations` and `error_modes` both non-empty.`

with:

`must be schema-shaped as returned: `type: interface`, `status: draft`, every entry in `operations` carrying an `interaction` that is one of the two enum values, and `operations` and `error_modes` both non-empty. Do **not** emit a contract-level `interaction` — the schema's `unevaluatedProperties: false` rejects it.`

- [ ] **Step 4: Update the worked example and add a mixed one**

In the existing card-payment example (lines ~378–392), replace the operations block and delete the contract-level line:

```yaml
  operations:
    - name: authorize
      summary: Reserve funds against a card for an order total, returning an authorisation reference.
      interaction: synchronous
    - name: capture
      summary: Settle a previously authorised amount against the same reference.
      interaction: synchronous
    - name: void
      summary: Release an authorisation that will not be captured.
      interaction: synchronous
```

Then add, immediately after that example, a second one — the guard is taught nowhere else and a rule with no example in a file that teaches by example gets missed:

````markdown
A mixed contract in the same system, and why this one is allowed to be mixed:

```yaml
  - id: IF-002
    type: interface
    title: Payment Audit Recording
    description: The contract through which payment activity is recorded for audit and forced durable before a reconciliation boundary.
    provider: CMP-003
    operations:
      - name: record
        summary: Accept an audit entry for eventual durable storage.
        interaction: asynchronous
      - name: flush
        summary: Make every previously accepted entry durable before returning.
        interaction: synchronous
    error_modes:
      - "Entry volume exceeds the buffer between flushes — entries are dropped, and the caller is told which window was lost."
      - "Flush times out with entries unwritten — durability is not established and the caller must not treat the window as recorded."
    consumed_by: [CMP-001, CMP-004]
    satisfies_capabilities:
      - { component: CMP-001, capability: "record payment activity for audit" }
      - { component: CMP-004, capability: "record payment activity for audit" }
```

`record` does not block and `flush` must, so the contract is mixed. It is
allowed to be mixed because `CMP-001` (order-service) and `CMP-004`
(refund-processor) both use both operations — `record` on their normal path,
`flush` before they close a reconciliation window. Splitting would give each of
them two contracts they always hold together.

Had `CMP-001` used only `record` and `CMP-004` only `flush`, the consumer sets
would diverge and this would be two interfaces instead.
````

`CMP-001` is the order-service already used in the example above; `CMP-003` and
`CMP-004` are introduced here and referenced nowhere else in this file.

- [ ] **Step 5: Verify by inspection**

Agent Markdown has no test suite, so verify against checkable claims:

```bash
grep -n "interaction" agents/interface-specialist.md
```

Expected: no line matching `^\s*interaction: synchronous \| asynchronous$` at contract level in any YAML block; every `operations:` block in the file shows `interaction` nested under an operation; the guard paragraph contains both "share a consumer set" and "two interfaces".

```bash
python3 -c "
import re,sys
t=open('agents/interface-specialist.md').read()
bad=[l for l in t.splitlines() if re.match(r'^ {4}interaction:', l)]
print('contract-level interaction lines:', bad)
sys.exit(1 if bad else 0)"
```

Expected: `contract-level interaction lines: []`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add agents/interface-specialist.md
git commit -m "feat(sto-216): teach per-operation interaction and the consumer-set guard

The interaction section now asks the question of each operation rather than the
contract, and states the guard: mixed is legal only when the operations share a
consumer set, and divergent sets are a split. Mixed interaction is not an
exemption from Interface Segregation — reaching for it to dodge a split is the
failure the rule exists to prevent.

The guard is instructional rather than a critic check, following STO-217's
precedent, and because no stage holds per-operation consumption data for a check
to read. So it gets a worked example: a legitimately mixed logging contract with
its consumer-set justification, and the counterfactual that would make it two.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Orchestrator, formatter, critic, and the stage summary

**Files:**
- Modify: `agents/design-orchestrator.md:259-260`
- Modify: `agents/design-formatter.md:222-226,249-253`
- Modify: `agents/design-critic.md:67-71`
- Modify: `skills/design/SKILL.md:251`

**Interfaces:**
- Consumes: the `draft_interfaces` shape Task 3 fixed.
- Produces: nothing.

- [ ] **Step 1: Update the orchestrator hand-off template**

In `agents/design-orchestrator.md`, in the `draft_interfaces` block, replace:

```yaml
    operations: [ { name, summary } ]
    interaction: synchronous | asynchronous
```

with:

```yaml
    operations: [ { name, summary, interaction } ]   # interaction is PER OPERATION
```

- [ ] **Step 2: Update the formatter frontmatter template**

In `agents/design-formatter.md`, replace:

```yaml
operations:
  - name: <operation name>
    summary: <one-line summary>
interaction: synchronous | asynchronous
```

with:

```yaml
operations:
  - name: <operation name>
    summary: <one-line summary>
    interaction: synchronous | asynchronous
```

- [ ] **Step 3: Update the formatter's branch-field rule**

Replace the sentence:

`and only an interface's branch fields (`provider`, `operations`, `interaction`, `error_modes`) on a `type: interface` file.`

with:

`and only an interface's branch fields (`provider`, `operations`, `error_modes`) on a `type: interface` file. `interaction` is **not** a contract field: it belongs on each entry of `operations`, and a top-level one fails the schema.`

- [ ] **Step 4: Make the critic's rule per-operation**

In `agents/design-critic.md`, replace the bullet at lines 67–71:

```markdown
- **Interaction matches the described wait.** If the body says the consumer
  blocks on the result, `interaction` must be `synchronous`, and vice versa.
  A mismatch between the prose and the field is a `revise` — one of the two is
  wrong and you cannot silently pick which.
```

with:

```markdown
- **Each operation's interaction matches the described wait.** `interaction` is
  declared per operation (STO-216), so check it per operation: if the body
  describes a consumer blocking on *that* operation's result, its `interaction`
  must be `synchronous`, and vice versa. A mismatch between the prose and the
  field is a `revise` — one of the two is wrong and you cannot silently pick
  which.

  Do not accept an argument about the contract's *dominant* mode. "The snapshot
  read is not the normal path" is not a reason for a blocking read to be
  declared asynchronous; a contract whose operations genuinely differ is
  mixed-mode, and each operation says what it is. There is no `mixed` value and
  none is needed. A body that argues one mode for a contract whose operations
  disagree is itself the finding.
```

- [ ] **Step 5: Update the stage summary line**

In `skills/design/SKILL.md`, replace line 251:

```markdown
- IF-001 <title> — provider: CMP-XXX, interaction: synchronous | asynchronous
```

with:

```markdown
- IF-001 <title> — provider: CMP-XXX, interaction: synchronous | asynchronous | mixed
```

and add immediately below the Interfaces block:

```markdown
`interaction` is declared per operation, so render `mixed` here when a
contract's operations disagree. It is computed for this summary only and is
never written to an artifact.
```

- [ ] **Step 6: Verify by inspection**

```bash
grep -rn "^interaction:" agents/ skills/
```

Expected: no output — no contract-level `interaction` survives in any agent contract or skill file.

Anchor on column 0, not on an indent width. An earlier draft of this step tested
`^(interaction:|    interaction:)`, which is wrong: indentation means different
things in the two templates. In `design-orchestrator.md` the interface is a list
item under `draft_interfaces:`, so a key at four spaces is a sibling of `type:`
— contract-level, and a real defect. In `design-formatter.md` the template is a
raw frontmatter block where `operations:` nests its own list, so a key at four
spaces is a property of the operation — exactly what this ticket requires. One
regex cannot mean both, and the version that flagged the formatter's correct
output as a defect would push an implementer to break it.

```bash
grep -c "per operation" agents/design-critic.md
```

Expected: at least 1.

- [ ] **Step 7: Run the whole suite and both validators over the worked example**

```bash
python3 -m pytest skills/ -q
python3 skills/design/scripts/validate_design.py docs/requirements/examples/tamagotchi/design
python3 skills/design/scripts/validate_traceability.py \
    docs/requirements/examples/tamagotchi/design \
    --requirements docs/requirements/examples/tamagotchi/requirements
```

Expected: 165 passed; both validators exit 0.

- [ ] **Step 8: Commit**

```bash
git add agents/design-orchestrator.md agents/design-formatter.md \
        agents/design-critic.md skills/design/SKILL.md
git commit -m "feat(sto-216): carry per-operation interaction through the pipeline

The orchestrator hand-off and formatter frontmatter templates emit interaction
on the operation; the formatter's branch-field rule says explicitly that a
contract-level one fails the schema.

The critic's rule becomes per-operation, which is what makes it checkable at
all: a whole-contract claim could only be weighed against a whole body, and
IF-005 shows a body arguing its dominant mode beats that. The rule now refuses
that argument by name.

SKILL.md renders 'mixed' in the stage summary when a contract's operations
disagree, computed for display and never written.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Verification

After Task 4, the ticket is complete when all of the following hold:

- `python3 -m pytest skills/ -q` reports 165 passed.
- Both design validators exit 0 over the tamagotchi worked example.
- `grep -rn "^interaction:" --include="*.md" agents/ skills/ docs/` returns nothing.
- `grep -rn '"mixed"' skills/design/schema/design.schema.json` returns nothing — no enum gained a third value.
- `git status --short docs/requirements/examples/gdpr/` is empty — the gdpr example has no design artifacts and must not have been touched.
- `git diff --stat $(git merge-base main HEAD) HEAD -- docs/requirements/examples/tamagotchi/design/critique-report.yaml docs/requirements/examples/tamagotchi/design/drivers.md` is empty — generated history was not edited (spec D7). Use the merge-base, not `HEAD~N`: fix rounds add commits, so any fixed offset silently narrows the range and can report a clean diff over a change it never looked at.
