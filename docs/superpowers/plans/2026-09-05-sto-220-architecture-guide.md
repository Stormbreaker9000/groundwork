# Architecture Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fill the `/architecture/` section of the docs site with a stage map and hand-off contracts generated from the two orchestrators, plus hand-written invariants and rationale, so the pipeline is described as a whole and the generated half cannot drift from its source.

**Architecture:** A fifth exporter function in `site/scripts/export_reference.py` parses both orchestrator agent files into `pipeline.json`, asserting that every contract a stage heading names is actually defined in that stage's YAML. Two new React components render it. Four MDX pages consume the components and carry the prose. The existing `--check` drift gate covers the new output with no workflow change; one new CI assertion proves the rendered page is not silently empty.

**Tech Stack:** Python 3.12 stdlib only (no new dependencies), pytest, Next.js 16 / Nextra 4 (JSX, no TypeScript), GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-05-sto-220-architecture-guide-design.md`

## Global Constraints

- **Stdlib only** in `export_reference.py`. Every script in this repository is stdlib-only; adding a YAML parser is not permitted. Contract YAML is carried as *text*, never parsed into objects.
- **The site build stays Python-free.** No task may add a Python step to the site build. `pipeline.json` is committed, and the build reads the committed file.
- **Generated data is never restated in prose.** If a page needs a contract's shape, it renders the component. House rule from pass 1, and the reason the drift gate is meaningful.
- **Parsers raise, they never degrade silently.** The drift gate compares committed JSON against current output, so a consistently empty or wrong extraction reads as "current" forever. Every parser added here raises `ValueError` on a shape it does not recognise.
- **Fourteen dispatched agents, seven per stage.** `agents/` holds fifteen files; `requirements-analyst` is dispatched by nothing. No page may say fifteen.
- **The stage map stops at the design stage.** M3 and M4 are backlog. No page mentions them as though they exist.
- **Commit message prefix:** `feat(sto-220):` or `docs(sto-220):`, and every commit ends with the two attribution trailers used on this branch.

---

### Task 1: `export_pipeline()` — parse both orchestrators, assert the join

**Files:**
- Modify: `site/scripts/export_reference.py`
- Modify: `agents/requirements-orchestrator.md` (one heading, line 243 area)
- Modify: `site/scripts/tests/test_export_reference.py`
- Create: `site/content/_generated/pipeline.json` (generated, committed)

**Interfaces:**
- Produces: `export_pipeline() -> Dict[str, Any]`, keyed `"requirements"` and `"design"`. Each value is `{"agent": str, "source": str, "stages": [...]}`. Each stage is `{"number": str, "label": str, "retired": bool, "contracts": [...]}`. Each contract is `{"name": str, "yaml": str, "transients": [str]}`. Tasks 2 and 3 render exactly these keys.
- Produces: `PIPELINE_SOURCES`, `_contract_names()`, `_yaml_segments()` — used only by tests.

- [ ] **Step 1: Fix the requirements Stage 6.5 heading (spec D5)**

`agents/requirements-orchestrator.md` has `## Stage 6.5 — Synthesize the context artifact`. Its M2 sibling is `## Stage 9 — Synthesise the \`design_context_artifact\``. The M1 heading names its contract in bare prose, so the extractor cannot see it. Add the backticks:

```bash
python3 - <<'PY'
import pathlib
p = pathlib.Path('agents/requirements-orchestrator.md')
s = p.read_text()
old = "## Stage 6.5 — Synthesize the context artifact"
new = "## Stage 6.5 — Synthesize the `context_artifact`"
assert s.count(old) == 1
p.write_text(s.replace(old, new))
PY
grep -n "Stage 6.5" agents/requirements-orchestrator.md
```

Expected: `## Stage 6.5 — Synthesize the \`context_artifact\``

Do not change the verb spelling. `Synthesize` (M1) and `Synthesise` (M2) differ, and the extractor deliberately does not key on the verb — leaving them different is a live test that it does not.

- [ ] **Step 2: Write the failing tests**

Append to `site/scripts/tests/test_export_reference.py`:

```python
# --- pipeline export (STO-220) ---------------------------------------------

PIPELINE_STAGE_KEYS = {"number", "label", "retired", "contracts"}
PIPELINE_CONTRACT_KEYS = {"name", "yaml", "transients"}


def test_pipeline_export_covers_both_orchestrators():
    payload = er.export_pipeline()
    assert set(payload) == {"requirements", "design"}
    assert payload["requirements"]["agent"] == "requirements-orchestrator"
    assert payload["design"]["agent"] == "design-orchestrator"
    for stage in payload.values():
        for entry in stage["stages"]:
            assert set(entry) == PIPELINE_STAGE_KEYS
            for contract in entry["contracts"]:
                assert set(contract) == PIPELINE_CONTRACT_KEYS


def test_pipeline_export_reads_the_real_stage_order():
    payload = er.export_pipeline()
    req = [s["number"] for s in payload["requirements"]["stages"]]
    des = [s["number"] for s in payload["design"]["stages"]]
    assert req == ["1", "2", "3", "4", "5", "6", "6.5", "7"]
    assert des == ["1", "2", "3", "4", "5", "6", "7", "8",
                   "9", "9.5", "9.6", "10", "11", "12"]


def test_pipeline_export_names_every_contract():
    payload = er.export_pipeline()

    def names(stage):
        return [c["name"] for s in payload[stage]["stages"] for c in s["contracts"]]

    assert names("requirements") == [
        "generation_brief", "draft_requirements", "critique_report",
        "context_artifact", "formatter_result",
    ]
    assert names("design") == [
        "generation_brief", "draft_components", "draft_interfaces",
        "critique_report", "design_context_artifact", "formatter_result",
    ]


def test_pipeline_export_splits_one_fence_holding_two_contracts():
    # Design Stage 6 defines draft_components and draft_interfaces as two
    # top-level keys inside a single ```yaml fence. Each contract must get
    # its own slice, not the whole block twice.
    payload = er.export_pipeline()
    stage6 = next(s for s in payload["design"]["stages"] if s["number"] == "6")
    assert [c["name"] for c in stage6["contracts"]] == [
        "draft_components", "draft_interfaces",
    ]
    components, interfaces = stage6["contracts"]
    assert components["yaml"].startswith("draft_components:")
    assert interfaces["yaml"].startswith("draft_interfaces:")
    assert "draft_interfaces:" not in components["yaml"]


def test_pipeline_export_skips_past_a_non_matching_first_block():
    # Design Stage 8's section opens with a `capability_map:` block; the
    # contract its heading names is the SECOND block. Taking the first block
    # after the heading would publish the wrong shape under the right name.
    payload = er.export_pipeline()
    stage8 = next(s for s in payload["design"]["stages"] if s["number"] == "8")
    assert [c["name"] for c in stage8["contracts"]] == ["critique_report"]
    assert stage8["contracts"][0]["yaml"].startswith("critique_report:")


def test_pipeline_export_ignores_a_backticked_field():
    # Design Stage 7 is "Back-fill `depends_on`" — a field, not a contract,
    # and it carries no YAML at all. A rule keyed on "the heading contains
    # backticks" would raise here.
    payload = er.export_pipeline()
    stage7 = next(s for s in payload["design"]["stages"] if s["number"] == "7")
    assert stage7["contracts"] == []


def test_pipeline_export_marks_retired_stages():
    payload = er.export_pipeline()
    retired = [s["number"] for s in payload["design"]["stages"] if s["retired"]]
    assert retired == ["11", "12"]
    assert all(not s["retired"] for s in payload["requirements"]["stages"])


def test_pipeline_export_carries_the_transient_markers():
    payload = er.export_pipeline()
    stage6 = next(s for s in payload["design"]["stages"] if s["number"] == "6")
    components, interfaces = stage6["contracts"]
    assert components["transients"] == ["required_capabilities"]
    assert interfaces["transients"] == ["consumed_by", "satisfies_capabilities"]

    # M1 has a fourth transient. STO-220's ticket lists three, all from M2;
    # `applies_to` is declared by constraint-specialist and appears in no
    # hand-written summary of the pipeline. Pinned here so the count cannot
    # quietly drop back to the three someone remembered.
    stage5 = next(s for s in payload["requirements"]["stages"] if s["number"] == "5")
    assert stage5["contracts"][0]["transients"] == ["applies_to"]


def test_pipeline_export_raises_when_a_named_contract_has_no_yaml():
    # The assert-the-join behaviour. Renaming a contract in the heading but
    # not in the YAML must fail loudly: a silent skip would shrink the
    # published table while CI stayed green off self-consistent JSON.
    text = (
        "## Stage 4 — Dispatch: the `renamed_brief` hand-off\n\n"
        "```yaml\ngeneration_brief:\n  scope: all\n```\n"
    )
    with pytest.raises(ValueError, match="renamed_brief"):
        er._parse_pipeline(text, "agents/fake.md")


def test_pipeline_export_raises_when_a_file_has_no_stages():
    with pytest.raises(ValueError, match="no stage headings"):
        er._parse_pipeline("# Some agent\n\nNo stages here.\n", "agents/fake.md")


def test_contract_names_reads_the_heading_not_the_verb():
    assert er._contract_names("Dispatch: the `generation_brief` hand-off") == [
        "generation_brief"
    ]
    assert er._contract_names(
        "Collect drafts: the `draft_components` / `draft_interfaces` hand-offs"
    ) == ["draft_components", "draft_interfaces"]
    assert er._contract_names("Synthesise the `design_context_artifact`") == [
        "design_context_artifact"
    ]
    assert er._contract_names("Synthesize the `context_artifact`") == [
        "context_artifact"
    ]
    # No "the" before the backticks: a field, not a contract.
    assert er._contract_names("Back-fill `depends_on`") == []
    # "the" not followed by backticks: prose, not a contract.
    assert er._contract_names("Consume the clarification context") == []


def test_pipeline_is_one_of_the_gated_outputs():
    assert "pipeline.json" in export_reference.OUTPUTS
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python3 -m pytest site/scripts/tests/test_export_reference.py -q -k pipeline`
Expected: FAIL — `AttributeError: module 'export_reference' has no attribute 'export_pipeline'`

- [ ] **Step 4: Implement the exporter**

Insert into `site/scripts/export_reference.py`, after `export_stages()` and before `_serialize()`:

```python
# The two orchestrators are the only files that own hand-off contracts. Every
# other agent consumes or returns one; neither describes the pipeline.
PIPELINE_SOURCES = {
    "requirements": "agents/requirements-orchestrator.md",
    "design": "agents/design-orchestrator.md",
}

_STAGE_HEADING_RE = re.compile(r"^## Stage ([\d.]+) — (.+)$", re.M)
_YAML_BLOCK_RE = re.compile(r"^```yaml\n(.*?)^```", re.M | re.S)
_TOP_KEY_RE = re.compile(r"^([a-z_][a-z0-9_]*):", re.M)
_TRANSIENT_RE = re.compile(r"^\s*([a-z_][a-z0-9_]*):.*TRANSIENT", re.M)

# A heading names a contract when a backticked identifier follows the word
# "the": "Dispatch: the `generation_brief` hand-off", "Synthesise the
# `design_context_artifact`". Two shapes are deliberately NOT matched.
# "Back-fill `depends_on`" backticks a field and carries no YAML — keying on
# "the heading contains backticks" would raise on a stage that was never a
# contract. "Consume the clarification context" has the word but no backticks,
# so an intermediate shape is not promoted to a published contract. Keying on
# "the `x`" rather than on the verb is what lets the two orchestrators keep
# spelling Synthesi[sz]e differently without either one dropping out.
_CONTRACT_CLAUSE_RE = re.compile(r"\bthe ((?:`[a-z_][a-z0-9_]*`(?:\s*/\s*)?)+)")
_BACKTICKED_RE = re.compile(r"`([a-z_][a-z0-9_]*)`")


def _contract_names(label: str) -> List[str]:
    """The contract names a stage heading declares, in heading order."""
    clause = _CONTRACT_CLAUSE_RE.search(label)
    return _BACKTICKED_RE.findall(clause.group(1)) if clause else []


def _yaml_segments(section: str) -> Dict[str, str]:
    """Every top-level YAML key in a stage's section, mapped to its slice.

    A section may hold several fenced blocks, and one block may hold several
    top-level keys — design Stage 6 defines ``draft_components`` and
    ``draft_interfaces`` in a single fence, and design Stage 8 opens with a
    ``capability_map`` block before the ``critique_report`` its heading names.
    Slicing by top-level key rather than by block is what makes both come out
    right; taking "the first block after the heading" publishes Stage 8's
    wrong shape under the right name, and nothing downstream could tell.
    """
    segments: Dict[str, str] = {}
    for block in _YAML_BLOCK_RE.findall(section):
        keys = list(_TOP_KEY_RE.finditer(block))
        for index, key in enumerate(keys):
            end = keys[index + 1].start() if index + 1 < len(keys) else len(block)
            segments[key.group(1)] = block[key.start():end].rstrip() + "\n"
    return segments


def _parse_pipeline(text: str, source: str) -> List[Dict[str, Any]]:
    """One orchestrator's stages, in file order, with the contracts they own.

    Raises when a heading names a contract its own section does not define.
    That assertion is the reason this parser exists in this shape: the drift
    gate only compares committed JSON against current output, so a heading
    renamed without its YAML would quietly shrink the published table and CI
    would stay green on JSON that still matched itself. Failing loudly here is
    the same standard ``_coverage_areas`` holds for its anchor.
    """
    headings = list(_STAGE_HEADING_RE.finditer(text))
    if not headings:
        raise ValueError(f"no stage headings found in {source}")

    stages: List[Dict[str, Any]] = []
    for index, heading in enumerate(headings):
        end = (
            headings[index + 1].start()
            if index + 1 < len(headings)
            else len(text)
        )
        section = text[heading.start():end]
        label = heading.group(2).strip()
        segments = _yaml_segments(section)

        contracts: List[Dict[str, Any]] = []
        for name in _contract_names(label):
            if name not in segments:
                found = ", ".join(sorted(segments)) or "none"
                raise ValueError(
                    f"{source} Stage {heading.group(1)} names `{name}` but its "
                    f"section defines no such top-level YAML key (found: {found})"
                )
            body = segments[name]
            contracts.append(
                {
                    "name": name,
                    "yaml": body,
                    "transients": sorted(set(_TRANSIENT_RE.findall(body))),
                }
            )

        stages.append(
            {
                "number": heading.group(1),
                "label": label,
                "retired": label == "(retired)",
                "contracts": contracts,
            }
        )
    return stages


def export_pipeline() -> Dict[str, Any]:
    """The two stages' agent order and hand-off contracts, from the source.

    Deliberately carries contract YAML as text rather than parsing it. These
    blocks are illustrative shapes with inline comments — the ``# ← TRANSIENT``
    markers among them — not loadable documents, and every script in this
    repository is stdlib-only. Rendering the text verbatim is also what makes
    the published contract and the agent's own contract the same bytes.
    """
    out: Dict[str, Any] = {}
    for stage, source in PIPELINE_SOURCES.items():
        path = os.path.join(REPO_ROOT, source)
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        out[stage] = {
            "agent": os.path.basename(source)[:-len(".md")],
            "source": source,
            "stages": _parse_pipeline(text, source),
        }
    return out
```

Then add the output to the registry:

```python
OUTPUTS = {
    "rules.json": export_rules,
    "fields.json": export_fields,
    "agents.json": export_agents,
    "stages.json": export_stages,
    "pipeline.json": export_pipeline,
}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m pytest site/scripts/tests/test_export_reference.py -q`
Expected: PASS, all tests including the pre-existing ones.

If `test_pipeline_export_names_every_contract` fails on `context_artifact`, Step 1 did not land — re-check the heading.

- [ ] **Step 6: Generate the output and eyeball it once**

```bash
python3 site/scripts/export_reference.py
python3 -c "
import json
d = json.load(open('site/content/_generated/pipeline.json'))
for stage, body in d.items():
    print(stage, body['agent'], len(body['stages']), 'stages')
    for s in body['stages']:
        marks = ' [retired]' if s['retired'] else ''
        names = ', '.join(c['name'] for c in s['contracts']) or '-'
        print(f'  {s[\"number\"]:>4}  {names:<45}{marks}')
"
python3 site/scripts/export_reference.py --check && echo "GATE CLEAN"
```

Expected: 8 requirements stages, 14 design stages, 11 contracts total, Stages 11 and 12 marked retired, and `GATE CLEAN`.

- [ ] **Step 7: Commit**

```bash
git add site/scripts/export_reference.py site/scripts/tests/test_export_reference.py \
        site/content/_generated/pipeline.json agents/requirements-orchestrator.md
git commit -m "$(cat <<'EOF'
feat(sto-220): generate the pipeline stage map and hand-off contracts

Both orchestrators already carry their contracts as fenced YAML under
numbered stage headings. export_pipeline() reads them rather than restating
them, so the published contract and the agent's own contract are the same
bytes.

The parser asserts its join: a heading that names a contract its section
does not define raises instead of skipping. A skip would shrink the
published table while --check stayed green, because the committed JSON
would still match what the parser currently produces.

Three real shapes drove the rule. One fence holds two contracts, so slicing
is by top-level key rather than by block. One section's first block is not
the contract its heading names, so the search covers the section. And
"Back-fill `depends_on`" backticks a field, so the contract form keys on
"the `x`" rather than on the presence of backticks.

Requirements Stage 6.5 named its contract in bare prose while its M2 sibling
backticked it; adding the backticks is the smaller fix than teaching the
extractor to guess at unmarked contracts.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GGpuBVjBxgu4frXTbGTPqK
EOF
)"
```

---

### Task 2: `PipelineMap` and the stage-map page

**Files:**
- Create: `site/components/PipelineMap.jsx`
- Create: `site/content/architecture/_meta.js`
- Modify: `site/content/architecture/index.mdx` (replaces the stub wholesale)

**Interfaces:**
- Consumes: `pipeline.json` from Task 1 — `{stage: {agent, source, stages: [{number, label, retired, contracts}]}}`.
- Produces: `export function PipelineMap({ stage })` where `stage` is `"requirements"` or `"design"`.

- [ ] **Step 1: Write the component**

Create `site/components/PipelineMap.jsx`:

```jsx
import { Table } from 'nextra/components'
import pipeline from '../content/_generated/pipeline.json'

/**
 * One stage's pipeline order, from generated data.
 *
 * Nothing here restates a stage. Renumber a stage in the orchestrator,
 * re-run the exporter, and this table moves with it.
 *
 * Retired stages are rendered rather than filtered. The design orchestrator
 * stops at 12 with 11 and 12 retired, and a reader who counts to 10 and
 * finds nothing after it has to wonder whether the page is hiding something.
 * A visible gap answers the question the filtered version would raise.
 *
 * Uses nextra/components' Table for the same reason RuleTable does: MDX
 * component substitution never reaches a raw <table> inside an imported
 * .jsx component.
 */
export function PipelineMap({ stage }) {
  const section = pipeline[stage]

  if (!section) {
    return (
      <p>
        <strong>PipelineMap error:</strong> no pipeline data for stage{' '}
        <code>{stage}</code>. Known stages: {Object.keys(pipeline).join(', ')}.
      </p>
    )
  }

  return (
    <Table className="nextra-scrollbar x:not-first:mt-[1.25em] x:p-0">
      <thead>
        <Table.Tr>
          <Table.Th>Stage</Table.Th>
          <Table.Th>What happens</Table.Th>
          <Table.Th>Hand-off</Table.Th>
        </Table.Tr>
      </thead>
      <tbody>
        {section.stages.map(entry => (
          <Table.Tr key={entry.number}>
            <Table.Td>{entry.number}</Table.Td>
            <Table.Td>
              {entry.retired ? <em>retired</em> : entry.label}
            </Table.Td>
            <Table.Td>
              {entry.contracts.length === 0
                ? '—'
                : entry.contracts.map(contract => (
                    <code key={contract.name}>{contract.name}</code>
                  ))}
            </Table.Td>
          </Table.Tr>
        ))}
      </tbody>
    </Table>
  )
}
```

- [ ] **Step 2: Write the nav metadata**

Create `site/content/architecture/_meta.js`:

```js
export default {
  index: 'How the pipeline runs',
  contracts: 'Hand-off contracts',
  invariants: 'Invariants',
  rationale: 'Why it is shaped this way'
}
```

- [ ] **Step 3: Replace the stub page**

Overwrite `site/content/architecture/index.mdx`. Write the prose to these constraints, and check every claim against the file that implements it before publishing it:

- Open by saying who the section is for — someone about to change the pipeline, not someone about to run it — and link to `/guide/` for the latter.
- State the shape once: two stages, fourteen dispatched agents, seven each. Do not say fifteen.
- One `<PipelineMap stage="requirements" />` and one `<PipelineMap stage="design" />`, each introduced by a short paragraph naming which agents run in that stage and in what order.
- **The on-disk column is the point of the page.** After each map, a short subsection saying what exists under `.sdlc/` at each point in that stage — nothing before the formatter runs, atomic files after it, the validator re-run folded back in. This is the column whose absence produced STO-215 and STO-207, so it gets prose rather than a table cell.
- Explain the numbering gap in one sentence: the design orchestrator's Stages 11 and 12 are retired, the numbers were not reused, and the map shows them so the gap is not mistaken for an omission.
- Close by saying the map ends where the built pipeline ends — no M3, no M4 — and do not sketch them.

Required frontmatter, matching the other pages:

```mdx
---
title: How the pipeline runs
description: The two stages, the agents in each, and what exists on disk at every point.
---

import { PipelineMap } from '../../components/PipelineMap'
```

- [ ] **Step 4: Build and verify the page renders the generated rows**

```bash
cd site && npm run build
grep -q 'generation_brief' out/architecture/index.html && echo "MAP RENDERED"
grep -c 'retired' out/architecture/index.html
cd ..
```

Expected: `MAP RENDERED`, and a non-zero retired count.

- [ ] **Step 5: Commit**

```bash
git add site/components/PipelineMap.jsx site/content/architecture/_meta.js \
        site/content/architecture/index.mdx
git commit -m "$(cat <<'EOF'
docs(sto-220): the stage map, generated from both orchestrators

Replaces the pass-1 stub. The stage order and hand-off column come from
pipeline.json, so renumbering a stage in an orchestrator moves this page
rather than contradicting it.

The on-disk prose after each map is the part the ticket asked for by name:
STO-215, STO-207 and the Gate C twin were all the stated contract
disagreeing with what existed on disk at that point, and no artifact put
the two side by side.

Retired stages render as a visible gap. Filtering them would leave a reader
counting to 10 and wondering what the page was not showing them.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GGpuBVjBxgu4frXTbGTPqK
EOF
)"
```

---

### Task 3: `ContractTable` and the contracts page

**Files:**
- Create: `site/components/ContractTable.jsx`
- Create: `site/content/architecture/contracts.mdx`

**Interfaces:**
- Consumes: `pipeline.json` from Task 1, and `PipelineMap`'s stage keys.
- Produces: `export function ContractTable({ stage })`.

- [ ] **Step 1: Write the component**

Create `site/components/ContractTable.jsx`:

```jsx
import pipeline from '../content/_generated/pipeline.json'

/**
 * One stage's hand-off contracts, verbatim from the orchestrator that owns
 * them.
 *
 * The YAML is rendered as text, not re-serialized from a parsed object. The
 * blocks carry inline comments — the `# ← TRANSIENT` markers among them —
 * and a round-trip through any parser would drop exactly the annotations a
 * contributor most needs to see.
 *
 * Transients get their own line rather than a column: which fields die at
 * the formatter is the single fact about these shapes that a reader cannot
 * recover by looking at an emitted artifact, because by then they are gone.
 */
export function ContractTable({ stage }) {
  const section = pipeline[stage]

  if (!section) {
    return (
      <p>
        <strong>ContractTable error:</strong> no pipeline data for stage{' '}
        <code>{stage}</code>. Known stages: {Object.keys(pipeline).join(', ')}.
      </p>
    )
  }

  const contracts = section.stages.flatMap(entry =>
    entry.contracts.map(contract => ({ ...contract, stage: entry.number }))
  )

  if (contracts.length === 0) {
    return (
      <p>
        <strong>ContractTable error:</strong> no contracts found for{' '}
        <code>{stage}</code> in <code>{section.source}</code>.
      </p>
    )
  }

  return (
    <>
      {contracts.map(contract => (
        <section key={contract.name}>
          <h3 id={contract.name.replace(/_/g, '-')}>
            <code>{contract.name}</code>
          </h3>
          <p>
            Stage {contract.stage} of <code>{section.agent}</code>.
            {contract.transients.length > 0 && (
              <>
                {' '}Transient:{' '}
                {contract.transients.map((field, index) => (
                  <span key={field}>
                    {index > 0 && ', '}
                    <code>{field}</code>
                  </span>
                ))}
                {' '}— carried between agents, never written to disk.
              </>
            )}
          </p>
          <pre>
            <code>{contract.yaml}</code>
          </pre>
        </section>
      ))}
    </>
  )
}
```

- [ ] **Step 2: Write the page**

Create `site/content/architecture/contracts.mdx`:

```mdx
---
title: Hand-off contracts
description: Every shape passed between agents, verbatim from the orchestrator that owns it.
---

import { ContractTable } from '../../components/ContractTable'
```

Then, to these constraints:

- One paragraph saying the two orchestrators own every contract, that the blocks below are the same bytes as the agent files, and that no other agent defines one.
- `<ContractTable stage="requirements" />` and `<ContractTable stage="design" />` under their own H2s.
- A hand-written H2, **Why the shapes are these shapes**, covering two things the generated blocks cannot say:
  - **Why capabilities travel as prose, not IDs.** The component and interface authoring cycle would otherwise be circular — a component cannot cite an interface ID that the interface specialist has not allocated yet. STO-217 is the evidence that this is the pipeline's least self-evident decision. Read `agents/component-specialist.md:243-260` and `agents/design-orchestrator.md:274` before writing this, and describe what those files actually say.
  - **Where each transient dies, and what breaks if it survives.** `required_capabilities`, `consumed_by` and `satisfies_capabilities` are stripped before anything is written; the design schema sets `unevaluatedProperties: false`, so an artifact carrying one fails the structural gate. Verify that claim against the schema before publishing it.

- [ ] **Step 3: Build and verify**

```bash
cd site && npm run build
grep -q 'draft_interfaces' out/architecture/contracts/index.html && echo "CONTRACTS RENDERED"
grep -q 'TRANSIENT' out/architecture/contracts/index.html && echo "TRANSIENTS PRESERVED"
cd ..
```

Expected: both lines print. `TRANSIENTS PRESERVED` proves the YAML reached the page as text with its comments intact.

- [ ] **Step 4: Commit**

```bash
git add site/components/ContractTable.jsx site/content/architecture/contracts.mdx
git commit -m "$(cat <<'EOF'
docs(sto-220): the hand-off contracts, verbatim from their owners

Renders each contract as the bytes the orchestrator carries, comments
included. Re-serializing from a parsed object would drop the `# ← TRANSIENT`
markers, which are the one thing about these shapes a reader cannot recover
from an emitted artifact — by then the fields are gone.

The hand-written half covers what the blocks cannot say: why capabilities
travel as prose rather than IDs, and where each transient dies.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GGpuBVjBxgu4frXTbGTPqK
EOF
)"
```

---

### Task 4: The invariants page

**Files:**
- Create: `site/content/architecture/invariants.mdx`

**Interfaces:**
- Consumes: nothing generated. Prose only.

- [ ] **Step 1: Write the page**

Create `site/content/architecture/invariants.mdx` with frontmatter:

```mdx
---
title: Invariants
description: The rules that hold across both stages, and the file that enforces each one.
---
```

Six invariants, each an H2 stating the rule in one sentence, then a short paragraph, then **the file and line that enforces it** — a rule with no named enforcer is a rule someone will break. Open every source file and confirm before citing it:

1. **One artifact per file.** Atomic Markdown+YAML, named `<ID>-<kebab-title>.md`. Enforced by the two formatters and the structural validators.
2. **IDs are categorical, zero-padded, and allocated only by an orchestrator.** No specialist invents one.
3. **IDs are never reused.** A retired artifact's ID stays retired — the design orchestrator's retired Stages 11 and 12 are the same principle applied to stage numbers.
4. **The critic gates judgment; the formatter gates structure.** State plainly that the structural gate runs *after* the artifacts exist on disk, because it cannot run before, and note that STO-215 and STO-207 were both this invariant being stated wrongly in an agent file.
5. **Confidence and `review_queue` triage.** Low-confidence items are persisted for a human rather than silently accepted. Note honestly that `agents/requirements-formatter.md` describes `index.yaml` and its `review_queue` as optional while the skill and every generated set treat them as mandatory — that contradiction is filed as STO-269 #1 and is not resolved here.
6. **Generated reference data is committed, and CI fails on drift.** This is where the exporter tax gets written down, per spec D8: editing an agent `description:`, either `SKILL.md`'s coverage list, or any hand-off heading or its YAML reddens CI until `python3 site/scripts/export_reference.py` is re-run. Give the command. Pass 2 asked for this to be stated here rather than discovered.

- [ ] **Step 2: Build and check the page is reachable**

```bash
cd site && npm run build
test -f out/architecture/invariants/index.html && echo "PAGE BUILT"
grep -q 'export_reference.py' out/architecture/invariants/index.html && echo "TAX DOCUMENTED"
cd ..
```

Expected: both lines print.

- [ ] **Step 3: Commit**

```bash
git add site/content/architecture/invariants.mdx
git commit -m "$(cat <<'EOF'
docs(sto-220): the cross-cutting invariants, each with its enforcer named

Six rules that hold across both stages. Every one names the file that
enforces it, because a rule with no named enforcer is a rule someone will
break without noticing.

Two are written against known defects rather than around them: the critic
gates judgment while the formatter gates structure is stated with the
STO-215 and STO-207 failures that came from stating it wrongly, and the
review_queue entry records that the formatter's contract calls index.yaml
optional while the skill and every generated set treat it as mandatory.

Closes the loop pass 2 left open: the exporter tax is documented here, with
the command that clears it, rather than discovered by whoever reddens CI
next.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GGpuBVjBxgu4frXTbGTPqK
EOF
)"
```

---

### Task 5: The rationale page

**Files:**
- Create: `site/content/architecture/rationale.mdx`

**Interfaces:**
- Consumes: nothing generated. Prose only.

- [ ] **Step 1: Write the page**

Create `site/content/architecture/rationale.mdx`:

```mdx
---
title: Why it is shaped this way
description: The decisions that cannot be reconstructed from the code, and the failures that produced them.
---
```

This is the page STO-220 says is most worth writing while the reasoning is still fresh, and the only page with no gate behind it. Every claim is checked against a file or a ticket before it is published.

**H2 per decision, each tied to the failure that produced it:**

- **Why the design stage runs its own interview.** The requirement set cannot carry technology context by construction, so the stage either asks or invents. The first tamagotchi build paid to rip out an unexamined Electron recommendation. Note the narrow true form of the claim: no *requirement* commits to a technology, but `.sdlc/requirements/` does contain technology words — `assumptions.md` carries `Q-4` naming Electron and Tauri. `skills/design/SKILL.md:105-106` states the broader, false version; that is STO-269 #3 and is filed, not fixed here.
- **Why the component/interface cycle is broken with prose capabilities.** Cross-reference the contracts page rather than restating it.
- **Why structural gates run at the formatter, not the critic.** The artifacts do not exist when the critic runs.
- **Why every artifact is atomic.** Diff granularity, traceability edges that address a file, and a critic that can reject one requirement without re-litigating a document.

**Then an H2 for the standards grounding** — a short paragraph each on what the standard *buys*, not what it is: BABOK tiers, EARS, INCOSE/ISO 29148, ISO/IEC 25010:2023, ISO/IEC/IEEE 42010, ATAM, MADR, C4. A contributor changing a specialist needs to know which standard that specialist is answering to.

Do not restate the user guide. Where a reader needs the runnable version, link to `/guide/`.

- [ ] **Step 2: Build and verify the section is complete**

```bash
cd site && npm run build
for path in index contracts/index invariants/index rationale/index; do
  test -f "out/architecture/$path.html" && echo "$path ok" || echo "$path MISSING"
done
cd ..
```

Expected: four `ok` lines.

- [ ] **Step 3: Commit**

```bash
git add site/content/architecture/rationale.mdx
git commit -m "$(cat <<'EOF'
docs(sto-220): the rationale, tied to the failures that produced it

The half of the guide that cannot be generated and cannot be reconstructed
from the code. Each decision is stated with the failure that produced it —
the design stage interviews because the first tamagotchi build paid to rip
out an unexamined Electron recommendation, and structural gates sit at the
formatter because the artifacts do not exist when the critic runs.

The technology-context claim is published in its narrow true form: no
requirement commits to a technology, though .sdlc/requirements/ does carry
technology words. The skill file states the broader version, which is false
and filed as STO-269 #3.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GGpuBVjBxgu4frXTbGTPqK
EOF
)"
```

---

### Task 6: CI assertion, full verification, and file the findings

**Files:**
- Modify: `.github/workflows/ci.yml:60-70` (the `Built pages carry their generated rows` step)

**Interfaces:**
- Consumes: everything from Tasks 1–5.

- [ ] **Step 1: Extend the built-output assertion**

`ContractTable` and `PipelineMap` both return an error paragraph rather than throwing when their stage key is missing, so `next build` exits 0 on a broken page — the same silent-degrade path pass 2's B2 caught in `RuleTable`. Add two greps to the existing step:

```yaml
      - name: Built pages carry their generated rows
        run: |
          grep -q 'god-component' out/guide/reference/rules/index.html
          grep -q 'id="fr-001"' out/guide/examples/tamagotchi/requirements/functional/index.html
          grep -q 'generation_brief' out/architecture/index.html
          grep -q 'draft_interfaces' out/architecture/contracts/index.html
        working-directory: site
```

- [ ] **Step 2: Run the whole suite and both gates locally**

```bash
python3 -m pytest -q
python3 site/scripts/export_reference.py --check
python3 site/scripts/export_examples.py --check
cd site && npm run build && cd ..
```

Expected: all tests pass, both gates clean, build exits 0.

- [ ] **Step 3: Prove the drift gate actually covers the new output**

A gate nobody has seen fail is a gate nobody knows works.

```bash
python3 - <<'PY'
import pathlib
p = pathlib.Path('site/content/_generated/pipeline.json')
original = p.read_text()
p.write_text(original.replace('"generation_brief"', '"tampered"', 1))
PY
python3 site/scripts/export_reference.py --check; echo "exit=$? (expected 1)"
git checkout site/content/_generated/pipeline.json
python3 site/scripts/export_reference.py --check && echo "restored, gate clean"
```

Expected: `exit=1` with `stale: site/content/_generated/pipeline.json`, then clean.

- [ ] **Step 4: Prove the assert-the-join fires against the real file**

```bash
cp agents/design-orchestrator.md /tmp/design-orchestrator.bak
python3 - <<'PY'
import pathlib
p = pathlib.Path('agents/design-orchestrator.md')
s = p.read_text()
p.write_text(s.replace(
    "## Stage 10 — Format: the `formatter_result` hand-off",
    "## Stage 10 — Format: the `renamed_result` hand-off", 1))
PY
python3 site/scripts/export_reference.py; echo "exit=$? (expected non-zero)"
cp /tmp/design-orchestrator.bak agents/design-orchestrator.md
python3 site/scripts/export_reference.py --check && echo "restored, gate clean"
```

Expected: a `ValueError` naming `renamed_result`, then clean. Confirm `git status` is clean before continuing.

- [ ] **Step 5: File the findings**

Every source claim found while writing that needed a decision rather than a local fix. At minimum, one new Linear issue for the `requirements-analyst` orphan: it is dispatched by no skill, agent or script, the only references are the May 2026 scaffold docs calling it a stub, and `export_agents()` publishes it on the site's roster as though it were live. State both options — delete it, or wire it in — and do not pick one. Add any further STO-269-class findings to STO-269 as comments rather than new tickets, since it is explicitly one ticket per defect class.

- [ ] **Step 6: Commit, push, and open the PR**

```bash
git add .github/workflows/ci.yml
git commit -m "$(cat <<'EOF'
feat(sto-220): assert the architecture pages carry their generated rows

Both new components degrade to an error paragraph rather than throwing when
their stage key is missing, so next build exits 0 on a page that renders
nothing. This is pass 2's B2 lesson applied to the two pages pass 3 adds.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GGpuBVjBxgu4frXTbGTPqK
EOF
)"
git push -u origin markdadamo/sto-220-architecture-guide
```

Then open the PR titled `feat(sto-220): the architecture guide — stage map, generated hand-off contracts, invariants and rationale (pass 3 of 3)`, describing what is generated versus hand-written, the assert-the-join behaviour, and the findings filed. End the body with the PR trailer used on this repository.

- [ ] **Step 7: Report what CI actually did**

Watch the run. Report the result observed, not presumed — including the two new built-output greps. The deployed-site checks cannot be asserted from a working tree and are confirmed after merge, which is the standard passes 1 and 2 held themselves to.

---

## Self-Review

**Spec coverage.** D1 → Task 2 Step 3 (map stops at the design stage) and the Global Constraints. D2 → Tasks 2–5, one page each. D3 → Task 1. D4 → Task 1 Step 4 and Task 2 Step 1. D5 → Task 1 Step 1. D6 → Tasks 2, 3 and 6. D7 → Task 6 Step 5. D8 → Task 4 invariant 6. Testing table → Task 1 Steps 2–5, Task 6 Steps 2–4. No spec section is unimplemented.

**One refinement over the spec, deliberate.** D3 described the contract form as the `hand-off` and `Synthesise the …` heading shapes. The plan keys on `the \`x\`` instead, which excludes design Stage 7 without the extractor knowing any verb — closer to what D5 argues for than D5's own wording. The tests in Task 1 Step 2 pin both the inclusions and the exclusions.

**One deliberate exclusion to watch.** Design Stages 9.5 and 9.6 return `draft_adrs` and `draft_diagram_model` per their agents' descriptions, but neither heading names a contract, so neither is published. That matches the spec's Evidence table. If the writer of Task 3 judges these to be genuine hand-offs, that is a STO-269-class finding for Task 6 Step 5 — not a change to the extractor.
