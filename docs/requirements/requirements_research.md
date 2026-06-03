# Designing an LLM-driven requirements generator

**Build the plugin around five well-established pillars: ISO/IEC/IEEE 29148's nine quality attributes as the per-requirement gate, BABOK v3's four-tier hierarchy as the structural spine, EARS notation as the syntactic form, ISO/IEC 25010:2023's nine quality characteristics as the NFR coverage checklist, and Volere's atomic "snowcard" — with mandatory rationale and fit criterion — as the metadata schema.** Layer on AI-era patterns (ClarifyGPT-style pre-generation clarification, a generator/critic/formatter multi-agent split, ISO 25010-driven NFR prompting, and Anthropic structured outputs) to mitigate the LLM-specific failure modes empirical studies now document: NFR omission, implementation bias, surface-fluency over technical adequacy, and systematic over-correction. The artifact should be **Markdown-with-YAML-frontmatter, one atomic requirement per file, with stable categorical IDs**, because that format is simultaneously human-editable, git-diffable, and reliably parseable by downstream LLM workflows that generate architecture, design, tests, and a Definition of Done.

The rest of this report develops these recommendations with evidence, concrete examples, and copyable templates. Where the literature disagrees, the disagreement is flagged.

---

## What makes a requirement "good" — the consensus rubric

The authoritative list is **ISO/IEC/IEEE 29148:2018 §5.2.4–5.2.5**, which defines nine characteristics every individual requirement must satisfy. INCOSE's _Guide for Writing Requirements_ (v4, 2023) aligns one-to-one, and Karl Wiegers' classic six-criterion list is a strict subset. Together these form the de-facto industry consensus the plugin should encode as its quality gate.

A well-formed requirement is **necessary** (removal causes a deficiency, traceable to a higher-level source), **appropriate** (specified at the right level of abstraction), **unambiguous** (one and only one interpretation), **complete** (subject, action, object, conditions, and measurable criterion all present), **singular** (one requirement, no `and`/`or` conjunctions), **feasible** (achievable within constraints), **verifiable** (provable via inspection, analysis, demonstration, or test), **correct** (faithfully represents the source need), and **conforming** (follows an approved syntax pattern). Wiegers adds **prioritized** at the individual level; 29148 places priority in metadata.

At the **set** level, 29148 §5.2.6 requires **completeness, consistency, affordability, boundedness, comprehensibility, and validatability**. Wiegers further emphasizes **modifiability** (unique labels, related items grouped, cross-referenced) and **traceability**. The most commonly omitted set-level property in practice is non-redundancy — duplicated requirements drift apart on updates.

The standards converge so closely on these criteria that the plugin can treat them as universal. The 2025 paper "Leveraging LLMs for QA of Software Requirements vs ISO 29148" (arXiv 2408.10886) operationalizes exactly this rubric as an automated checker, and the QRA QVscribe and Jama Software Requirements Advisor tools sell the same idea commercially.

### Anti-patterns to detect and rewrite

The literature (Wiegers' "10 Requirements Traps," INCOSE GtWR, Jama checklists, EARS guidance) converges on a stable list of failure modes the plugin must catch:

- **Vague qualifiers without metrics**: _user-friendly, easy, intuitive, fast, rapid, efficient, robust, flexible, scalable, secure, minimize, maximize, optimize, support, approximately, as appropriate, etc., and/or, TBD_.
- **Compound statements**: any `and`/`or` in the action clause signals multiple requirements glued together.
- **Implementation bias**: prescribing technology, framework, or UI choices in stakeholder/business-level requirements — move into an explicit Constraints section if mandated.
- **Passive voice with nameless subjects**: "X shall be displayed" hides the responsible actor.
- **Universal quantifiers without bounds**: _all, any, every, no_ used loosely.
- **Negative or double-negative phrasing**: "shall not" is hard to verify; recast positively.
- **Speculative tense**: _could, may eventually, in the future_ — not requirements.
- **Mixed granularity** in the same section (atomic UI behavior next to entire subsystem behavior).
- **Missing rationale**: orphan requirements cannot be challenged or descoped intelligently.
- **Unprioritized "all-critical" lists**: prevents trade-off when scope is cut.

### Bad → good rewrites the plugin should produce

|Bad|Diagnosis|Good rewrite|
|---|---|---|
|The system shall be user-friendly.|Vague, unverifiable.|Novice users (≤2 hours training) shall complete the checkout task in ≤90 seconds with ≤1 error in 95% of attempts (usability test, n≥10).|
|The system shall be fast.|Subjective.|The system shall return search results over a corpus of ≤10M documents in ≤500 ms at p95 under 200 req/s sustained load.|
|The login page shall be secure.|No threat model, no control.|The system shall authenticate users via OAuth 2.0 with PKCE; failed login attempts shall be rate-limited to 5 per account per 15 minutes; credentials in transit shall use TLS 1.3.|
|The system shall support reporting and exporting and printing of orders.|Compound — three requirements.|Split into REQ-101 (PDF reports), REQ-102 (CSV export), REQ-103 (network-printer printing).|
|If possible, the dashboard should load reasonably quickly.|Optional, vague.|The dashboard shall render first meaningful paint within 2.0 s at p75 on 4G (CrUX, 28-day window).|
|The product shall switch between displaying and hiding markup instantaneously.|"Instantaneously" infeasible; trigger ambiguous.|When the user activates the Toggle Markup command, the system shall change the visibility of all HTML tags in the current document within 200 ms.|

---

## The standards landscape, and which parts matter

**ISO/IEC/IEEE 29148:2018** is the current authoritative standard, having superseded IEEE 830-1998, 1233-1998, and 1362-1998. It defines three integrated processes (Business/Mission Analysis, Stakeholder Needs Definition, System/Software Requirements Definition) and three corresponding document types (StRS, SyRS, SRS). Its lasting contribution is the explicit nine-attribute quality rubric and the "shall" sentence pattern: `[Conditions] [Subject] shall [Action] [Object] [Constraints]`. Use **shall** for mandatory, **should** for recommended, **may** for permitted, **will** for declaration of intent — a discipline the plugin should enforce.

**IEEE 830** is officially superseded but its three-section SRS outline (Introduction → Overall Description → Specific Requirements) remains the de-facto template in industry, academia, and government RFPs. The plugin should use 29148's content rules with 830's familiar scaffolding when a full SRS document is requested.

**ISO/IEC 25010:2023** is the NFR taxonomy that matters now. The 2023 revision expanded the model from 8 to **9 top-level characteristics**: Functional Suitability, Performance Efficiency, Compatibility, **Interaction Capability** (renamed from Usability, with new sub-characteristics including _inclusivity_, _user engagement_, _user assistance_, _self-descriptiveness_), Reliability (with new _faultlessness_ sub-characteristic), Security (adds _resistance_), Maintainability, **Flexibility** (renamed from Portability; adds _scalability_ as a sub-characteristic), and **Safety** (newly added as a top-level characteristic). Quality-in-use moved to ISO/IEC 25019:2023. The plugin must use the 2023 set, not the 2011 one most blog posts still cite, and should extend it with categories the standard still omits: **observability** (logs, metrics, tracing), **deployability**, **compliance** (GDPR, HIPAA, SOX, PCI-DSS), and **cost/economic** constraints.

**BABOK v3** contributes the cleanest hierarchical classification: Business Requirements (why) → Stakeholder Requirements (what users need) → Solution Requirements (functional + non-functional) → Transition Requirements (one-time cutover capabilities). The plugin should use this as its top-level structural spine because it forces upward traceability — every solution requirement must trace to a stakeholder need, which traces to a business outcome.

**Volere** is the most useful single template, particularly its **atomic requirement shell** (the "snowcard"). Two fields make it distinctive and indispensable for LLM-generated requirements: a mandatory **rationale** (which gives downstream LLMs the _why_ they need for consistent design choices), and a mandatory **fit criterion** (a measurable test oracle — if you can't write a fit criterion, the requirement is too vague). Volere also pairs **customer satisfaction** and **customer dissatisfaction** scores (1–5 each), which together identify Kano-style must-haves versus delighters.

**INVEST** (Independent, Negotiable, Valuable, Estimable, Small, Testable; Bill Wake, 2003) and **SMART** (Specific, Measurable, Achievable, Relevant, Time-bound) are lightweight gates that sit beneath the standards above. INVEST applies at the user-story level; SMART works well for acceptance criteria and NFR targets. Neither replaces 29148's rubric for system-level requirements.

There is real **consensus** across these frameworks on the core quality attributes and on the FR/NFR split. The notable **disagreements** are minor: Wiegers makes "System Requirements" a separate tier while BABOK folds them into Solution Requirements; the strict FR/NFR dichotomy breaks down for hybrid items like safety-related interlocks; and the Boehm cost-of-defect curve (1× in requirements vs. 100× in production) is contested in modern CI/CD environments (Menzies et al. 2016) though the underlying principle — that requirements defects propagate — remains valid.

---

## Types of requirements and how to balance them

The hierarchy worth implementing is BABOK's four tiers plus explicit separation of constraints, business rules, assumptions, and dependencies. **A well-balanced requirements set for a typical business application is roughly 60–70% functional, 15–25% NFR, 5–10% constraints, plus referenced business rules and explicit assumptions/dependencies.** NFRs are the most frequently omitted category and the most likely source of late, costly rework — which is exactly the case for prompting LLMs against an explicit ISO 25010 checklist.

**Constraints are distinct from NFRs.** An NFR specifies a quality target ("p95 latency ≤ 200 ms"); a constraint is an absolute boundary on the design space ("must run on Oracle 19c with no schema changes"). Constraints fall into four buckets: technical, regulatory/compliance, business (budget, schedule, contractual), and environmental/operational.

**Business rules are not requirements.** A rule like "customers under 18 cannot purchase alcohol" exists in policy independent of the system; the requirement is what the system does to enforce it. Trace each rule to all requirements that implement it so policy changes flow to one place.

**Assumptions and dependencies** are first-class artifacts. Assumptions are statements believed true without proof; dependencies are external conditions the project relies on. Surface both explicitly in a dedicated section rather than burying them in requirement text — this is one of the highest-leverage moves an LLM can make, because it forces the model to externalize what it would otherwise quietly hallucinate.

The categories the plugin should proactively elicit but that LLMs systematically skip: error and exception paths (only happy paths get written), compliance/regulatory constraints, data retention/migration/deletion, internationalization and accessibility, operational concerns (deployment, backup, monitoring, on-call), legal/licensing, and stakeholder roles beyond "the user" (admin, operator, support, auditor, regulator).

---

## Choosing notation: EARS as default, with format-by-context overrides

Six formats matter, each with a sweet spot. **The strongest single recommendation is to default to EARS notation for functional requirements**, because it is the format most amenable to LLM generation, LLM parsing, and downstream test/architecture derivation — and because Kiro (AWS), GitHub Spec Kit's community (issue #1356), and the safety-critical industries have already standardized on it.

**EARS** (Mavin et al., Rolls-Royce, RE'09) constrains natural English into five sentence patterns plus a complex combination:

- **Ubiquitous** (always active): "The `<system>` shall `<response>`."
- **Event-driven**: "When `<trigger>`, the `<system>` shall `<response>`."
- **State-driven**: "While `<state>`, the `<system>` shall `<response>`."
- **Unwanted behavior**: "If `<unwanted condition>`, then the `<system>` shall `<response>`."
- **Optional feature**: "Where `<feature is included>`, the `<system>` shall `<response>`."
- **Complex**: "While `<state>`, when `<trigger>`, the `<system>` shall `<response>`."

EARS is structured English — no specialist tools, low training cost, and LLMs parse it natively. It maps cleanly to test types: event-driven becomes integration tests, state-driven becomes state-machine tests, unwanted-behavior becomes error/edge-case tests. Its limit is around three preconditions per statement; beyond that, offload to a referenced decision table.

**User stories (Connextra format)** — "As a `<role>`, I want `<goal>`, so that `<benefit>`" — remain the right format at the stakeholder tier. They are conversation placeholders, not specifications. Pair every story with explicit acceptance criteria (Given/When/Then preferred) and apply INVEST as the gate. Use **Mike Cohn's SPIDR technique** for splitting (Spike, Paths, Interfaces, Data, Rules).

**Use cases (Cockburn)** outperform user stories when flows involve multiple actors, many alternative paths, or regulated environments. Use the brief form for early discovery and the fully-dressed form (scope, level, primary actor, stakeholders & interests, preconditions, success guarantee, minimal guarantee, trigger, main success scenario, extensions, special requirements) when contractual rigor is needed.

**Job stories (Klement/Intercom)** — "When `<situation>`, I want to `<motivation>`, so I can `<outcome>`" — remove persona bias and focus on the triggering event. They shine in early discovery when personas are weakly differentiated, and pair well with user stories later in the backlog.

**Gherkin (Given/When/Then)** is the right form for acceptance criteria because it doubles as an executable specification when consumed by Cucumber, SpecFlow, Behave, or similar BDD runners. Use scenario outlines with example tables for permutations; use the v6+ `Rule` keyword to group scenarios under a business rule.

**SRS "shall" prose** remains mandatory in regulated industries (medical IEC 62304, aerospace DO-178C, automotive ISO 26262, defense, FDA, FAR/DFARS procurement). EARS sentences are themselves "shall" sentences with extra structure, so an EARS-by-default plugin naturally satisfies SRS audiences.

### Format decision matrix

|Context|Primary format|Secondary|
|---|---|---|
|Consumer mobile app, fast Agile|User stories + Gherkin AC|Job stories for discovery|
|B2B SaaS, mid-complexity|User stories + GWT; story map at release|Impact map for quarterly|
|Enterprise workflow, many roles|Fully-dressed use cases|EARS for specific rules|
|Medical / avionics / automotive|EARS + SRS shall|Use cases for clinical workflows|
|Embedded / IoT firmware|EARS (state and event patterns excel)|SRS for constraints|
|Internal admin tooling|User stories + rule-based AC|—|
|Greenfield product discovery|Job stories + impact map|User stories later|
|Vendor RFP / fixed-price contract|SRS + use cases|EARS for behavior|

The quickest heuristic: **single-sentence answer needed → EARS; cross-functional conversation → user story; multi-actor process → use case; executable validation → Gherkin; opportunity exploration → job story; regulator-acceptable artifact → SRS or EARS.**

---

## What recent research tells us about LLMs writing requirements

The literature has matured fast. The 2025 systematic review by **Zadenoori, Dąbrowski, Alhoshan, Zhao, and Ferrari** (arXiv 2509.11446) surveyed 74 primary studies from 2023–2024 and found that focus has shifted decisively from classification and defect detection to **elicitation and validation**. GPT-based models dominate (~90% of studies), most evaluations are zero-shot (44%) or few-shot (29%), and RAG (6%) and interactive prompting (5%) remain underexplored despite empirical evidence that both work.

Empirical results consistently show LLMs are **strong on surface fluency and syntactic quality, weak on semantic and pragmatic quality**. The QUS-framework studies (arXiv 2507.15157, 2504.00513) and the RUST-framework study (arXiv 2603.28163) all converge on this finding: LLM-generated user stories score high on readability and uniformity, low on independence, atomicity, specifiability, and technical adequacy. Few-shot prompting outperformed free-form prompting by **22.7%** in the Santos et al. (SciTePress 2025) user-story study. The 2025 "Analysis of LLMs vs Human Experts in RE" study (arXiv 2501.19297) found LLM-generated requirements were preferred by users when blinded, ran **720× faster at ~0.06% of human cost** — but flagged perception bias as a confound.

The most actionable single finding for the plugin is from **Ronanki, Cabrero-Daniel, and Berger (REW 2023, arXiv 2307.07381)**: ChatGPT-generated requirements scored comparably to expert-written ones on most quality attributes but were systematically weaker on **feasibility and on capturing implicit qualities like trustworthy-AI principles**. Models don't know what they don't know, and they don't surface NFRs unless asked. The 2025 NFR-generation paper (arXiv 2503.15248) confirms this from the other direction: when LLMs are prompted with an explicit ISO/IEC 25010:2023 framework, they achieve **80.4% agreement with industry experts on NFR classification** and 5.0/5 median validity scores. The conclusion is mechanical — **NFR coverage is a prompting problem, not a model-capability problem**.

Multi-agent decomposition is the highest-promise direction. **MARE** (Jin et al., arXiv 2405.03256, 2024) demonstrated that splitting RE work across Stakeholder, Collector, Modeler, Checker, and Documenter agents outperforms single-agent prompting. **Elicitron** (Autodesk Research, 2024) simulates diverse synthetic users to surface latent needs a single human won't think of. The **ethics-advocate** critic pattern (Yamani et al., arXiv 2507.08392, 2025) captured most expert-elicited ethics requirements plus additional ones a 30-minute interview missed. **ClarifyGPT** (Mu et al., FSE 2024, arXiv 2310.10996) detects ambiguity by generating N candidate solutions and checking output divergence on type-aware test inputs, then asks targeted clarifying questions — raising GPT-4 Pass@1 from 70.96% to 80.80%.

### Pitfalls with empirical evidence

The empirical literature now documents specific LLM failure modes the plugin must guard against:

- **Hallucinated features and constraints** (Liu et al., ACM 2025; Xu et al., arXiv 2401.11817). RAG over project documents materially reduces this.
- **Implementation bias** — jumping to solutions in stakeholder requirements (Spec Kit and Kiro materials explicitly call this out).
- **Systematic over-correction** (arXiv 2603.00539, 2508.12358): when asked to _explain and fix_, LLMs hallucinate defects that aren't there. Mitigation: separate the comprehension and critique phases with a **two-phase reflective prompt**.
- **Cognitive bias amplification** (arXiv 2601.08045): anchoring, confirmation, and availability biases are amplified, not reduced, in human-LLM pairs.
- **Weak ambiguity detection**: GPT-3.5 and Llama detect ambiguity only marginally above chance; ambiguity is encoded internally (arXiv 2509.13664) but not surfaced. The model needs to be prompted to look.
- **NFR omission** unless explicitly prompted with a framework (the central finding of multiple 2024–2025 papers).
- **Prompt-variation fragility** (RobuNFR, arXiv 2503.22851): NFR quality fluctuates significantly across prompt rephrasings.

### Prompting patterns that work

**White et al.** (arXiv 2303.07839, 2023) catalogued the canonical patterns. The most useful for requirements work: **Requirements Simulator** (LLM acts as the system, surfaces missing requirements), **Specification Disambiguation** (LLM flags ambiguous terms and proposes interpretations), **Change Request Simulation** (LLM reasons about impact of a hypothetical change), **Fact Check List** (LLM produces an explicit list of unverified facts at the end), **Persona Pattern** (role prompting for stakeholder viewpoints).

For Claude specifically: **wrap each prompt component in XML tags** (Claude was trained heavily on `<instructions>`, `<context>`, `<example>`, `<requirements>` markers); include **three to five examples** because "one good example beats five adjectives"; use **Anthropic's Structured Outputs API** with JSON Schema for any artifact crossing a tool boundary; **prefill the assistant turn** with the opening character of the expected structure to force well-formed output; include the **"if unsure, say so" rule** as a top-level instruction (this is Anthropic's recommended hallucination mitigation); and in Claude Code skills, treat the **Gotchas section** as the highest-value content — it's where you encode the failure modes you've actually observed.

### Recommended multi-agent architecture for the plugin

Synthesizing the empirical results, the plugin should implement a five-stage pipeline rather than a single prompt:

1. **Clarifier** — ClarifyGPT-pattern. Run an internal consistency check on the user idea; ask 1–3 targeted clarifying questions only when divergence is high. Present numbered options rather than open-ended questions to improve user response quality.
2. **Elicitor / generator** — produces FR + NFR drafts in EARS/JSON with mandatory assumptions and open-questions sections.
3. **Persona simulator** (optional) — Elicitron-style synthetic stakeholders to surface latent needs, especially for consumer or multi-stakeholder products.
4. **Critic agents** — separated by concern: a quality critic (INCOSE/29148 rubric), an NFR completeness critic (ISO 25010:2023 walkthrough), and a compliance/ethics critic. Keep comprehension and critique in distinct prompts to avoid over-correction.
5. **Formatter** — emits final JSON or Markdown with stable IDs, traceability links, and confidence scores per requirement.

This mirrors empirically successful frameworks (MARE, BMAD-METHOD, Sami et al.'s four-agent system) and addresses the specific failure modes the literature documents.

### The current tooling landscape

Commercial: **QRA QVscribe** (NLP-based requirements quality analysis, INCOSE/EARS compliance checking, AI-guided rewrite suggestions, integrates with Jama, DOORS, Polarion), **Jama Connect AI**, **Visure Requirements ALM** (pre-built templates for ISO 26262, IEC 62304, IEC 61508, DO-178C), **Modern Requirements Copilot4DevOps** (Azure DevOps), **ReqView**.

Spec-driven / AI-coding tools that touch requirements: **GitHub Spec Kit** (`/speckit.constitution → specify → clarify → plan → tasks → implement → analyze`, works with Claude Code, community pushing for EARS integration), **AWS Kiro** (idea → requirements.md in EARS → design.md → tasks.md, built on Claude Sonnet 4.0/3.7, with steering files for persistent context), **GitHub Copilot Workspace** (Task → Spec → Plan → Code with editable artifacts at every gate), **BMAD-METHOD** (multi-agent: Analyst → PM → Architect → PO → SM → Dev → QA, produces brief, PRD, architecture doc, sharded stories). These are the tools to learn from architecturally; Kiro and Spec Kit are the closest competitors in approach.

---

## Connecting requirements to architecture, design, tests, and DoD

The bridge from NFRs to architecture is the **six-part quality attribute scenario** from SEI's ATAM methodology: source of stimulus, stimulus, environment, artifact, response, and response measure. The response measure is what makes the NFR testable and what becomes the assertion in a performance test, the SLO in a monitoring system, and the decision driver in an Architecture Decision Record. The plugin should emit every NFR in this six-part structure rather than as prose — it forces measurability and translates one-to-one into downstream artifacts.

Worked example (Performance/Latency scenario):

|Part|Value|
|---|---|
|Source of stimulus|Authenticated customer (external)|
|Stimulus|Submits an order via `POST /orders`|
|Environment|Normal operations, load ≤ 80% capacity|
|Artifact|Order API service + Order DB|
|Response|Order persisted, 201 returned, `orders.created` event published|
|Response measure|End-to-end latency ≤ 200 ms at p95 over rolling 5-min window; error rate ≤ 0.1%|

SEI's analysis of 15 years of ATAM data across 31 projects identified **modifiability, performance, availability, interoperability, and deployability** as the most architecturally influential quality attributes. These are the five the plugin should treat as first-class when generating a utility tree.

Each architecturally significant requirement should produce one or more **Architecture Decision Records**. The dominant templates are **Nygard's** (Title, Status, Context, Decision, Consequences) and **MADR 4.0** (adds Decision Drivers, Considered Options, Confirmation, Pros/Cons per option). The plugin should populate the ADR's `decision_drivers` field with NFR IDs, giving bidirectional traceability for free.

**Definition of Done versus acceptance criteria** is a distinction many teams blur. Per the Scrum Guide and Mike Cohn, **DoD is product-wide and stable across sprints** — it captures intrinsic quality (code reviewed, tests pass, security scan clean, deployed to staging). **Acceptance criteria are PBI-specific** and capture extrinsic quality (does this story behave as the customer expects?). A PBI is done only when both are satisfied. The plugin can derive a project-wide DoD checklist from the NFR set (every NFR with a `verification_method` field becomes a DoD gate) and emit per-story AC from the functional requirements.

Acceptance criteria written in Given/When/Then map directly to executable Cucumber/SpecFlow/Behave tests. Fit criteria from Volere snowcards become test oracles. The Requirements Traceability Matrix — required for FDA, DO-178C, ISO 26262, NASA SWE-059 — is derivable, not authored, when `traces_from` and `traces_to` are populated on every requirement file.

---

## Recommended artifact schema and document structure

The plugin should emit **Markdown with YAML frontmatter, one atomic requirement per file, organized in a conventional directory layout** that supports both human editing (in any editor) and LLM parsing (deterministic headings and frontmatter):

```
docs/requirements/
  index.yaml                       # machine index of all req IDs + metadata
  glossary.md                      # terminology — critical for downstream LLMs
  stakeholders.md
  assumptions.md
  constraints.md
  out-of-scope.md
  functional/
    FR-ORDER-014-cancel-pending-order.md
    FR-ORDER-015-...
  non-functional/
    NFR-PERF-API-001-order-api-latency.md
  use-cases/
    UC-ORDER-CHECKOUT.md
  traceability-matrix.csv          # generated, not authored
docs/decisions/                    # ADRs in MADR format
  0001-use-event-sourcing.md
```

Each atomic requirement file uses **categorical + zero-padded sequential IDs** (`FR-ORDER-014`, `NFR-PERF-API-001`, `CON-NNN`, `BR-NNN`, `UC-NNN`, `ADR-NNNN`), never re-uses an ID after deletion (set `status: obsolete` instead), and pairs the human ID with an immutable UUID for ReqIF-compatible tool interchange.

Canonical schema (per file):

````yaml
---
id: FR-ORDER-014
title: Cancel pending order
type: functional                    # functional | non_functional | constraint | business_rule
status: approved                    # draft | reviewed | approved | implemented | verified | obsolete
priority: must                      # MoSCoW: must | should | could | won't
ears_pattern: event_driven          # ubiquitous | event | state | unwanted | optional | complex
confidence: high                    # high | medium | low — for HITL triage
source: PM-Alice
owner: order-platform-team
version: 1.2
traces_from: [BR-RETENTION-02, US-142]
traces_to:
  design: [ADR-0021-order-state-machine]
  tests:  [TC-ORDER-CANCEL-001, TC-ORDER-CANCEL-002]
  code:   [src/order/cancel_handler.py]
nfr_links: [NFR-PERF-API-001, NFR-SEC-AUTHZ-003]
verification_method: test           # test | inspection | analysis | demonstration
---

# FR-ORDER-014 — Cancel pending order

## Description
When an authenticated customer issues a cancellation request for an order in
status Pending, the system shall transition the order to status Cancelled
within 60 seconds.

## Rationale
Customers expect to cancel before fulfillment to avoid charges; cancellation
requests are currently 18% of all support tickets.

## Acceptance Criteria
### AC-1 — Successful cancellation
```gherkin
Given an authenticated customer with a Pending order O
When the customer issues DELETE /orders/{O.id}
Then the order status becomes Cancelled
 And a cancellation email is dispatched within 60 seconds
 And the orders.cancelled event is published
````

### AC-2 — Reject when already fulfilling

```gherkin
Given an order O in status Fulfilling
When the customer issues DELETE /orders/{O.id}
Then the API returns 409 Conflict
 And the order status is unchanged
```

## Fit Criterion

100% of cancellation requests on Pending orders succeed in tests; 0% on Fulfilling orders.

## Assumptions

- Orders transition Pending → Fulfilling only via the fulfillment worker.
- Email delivery is handled by the notifications service (separate SLA).

```

For NFRs, replace the Acceptance Criteria section with a **six-part quality attribute scenario block** as shown earlier — this is the single highest-leverage structural choice in the schema because it forces measurability and translates directly into ADR decision drivers, performance test specs, SLO definitions, and DoD gates.

Mandatory fields per requirement: `id`, `title`, `type`, `status`, `description`, `rationale`, `acceptance_criteria` (or `quality_attribute_scenario` for NFRs), `verification_method`, `traces_from`. Recommended: `priority`, `owner`, `version`, `source`, `fit_criterion`, `confidence`, `assumptions`, `history`, `risk`.

The full **requirements document outline** the plugin should generate when asked for a complete artifact: document metadata → purpose & scope → stakeholders → users/personas → glossary → assumptions → constraints → out-of-scope → context & system boundary → business/domain rules → functional requirements → use cases/stories with AC → NFRs (organized by ISO 25010 category, each as a QAS) → external interfaces → data requirements → open issues → DoD → verification plan & traceability matrix → appendices.

---

## A concrete recipe for the plugin

Pulling everything together, here is the prescriptive recipe a well-designed Claude Code plugin should follow when turning a user idea into a downstream-ready requirements artifact.

**Stage 1 — Clarification before commitment.** Take the user's seed idea verbatim. Run an internal consistency check (generate two or three candidate interpretations; if they diverge significantly, ask). Present one to three numbered clarifying questions rather than open-ended ones. Apply the 5-Whys to surface the underlying business goal. Identify stakeholder classes by asking "who uses this, who is affected, who pays, who maintains it." Surface assumptions and dependencies explicitly.

**Stage 2 — Structured generation.** Use a system prompt that wraps role, context, instructions, and output schema in XML tags. Force the model to emit an Assumptions and Open Questions section before any requirements. Generate requirements at all four BABOK tiers (business → stakeholder → solution → transition where applicable). Write functional requirements in EARS notation. Walk through all nine ISO/IEC 25010:2023 quality characteristics explicitly and emit at least one NFR per applicable category, each as a six-part quality attribute scenario. Tag each requirement with confidence (high/medium/low) and an implementation-bias-risk flag. Output strict JSON or Markdown-with-frontmatter via Anthropic's Structured Outputs API.

**Stage 3 — Self-critique with separated concerns.** Run distinct critic passes: an INCOSE/29148 quality critic (atomicity, unambiguity, completeness, testability, conformance to EARS), an ISO 25010 NFR-coverage critic, and a compliance/ethics critic. Keep the comprehension and critique phases in separate prompts to avoid over-correction. Use a forbidden-word linter (the vague-qualifier list above) and a conjunction detector for compound requirements.

**Stage 4 — Format for downstream consumption.** Emit one Markdown file per requirement with YAML frontmatter, in the directory layout shown above. Populate `traces_from` and `traces_to` so the traceability matrix is derivable. For every NFR, populate the QAS structure so it can become both an ADR decision driver and a test assertion. Generate a glossary file and reference its terms — this is what keeps downstream LLM workflows from drifting on terminology.

**Stage 5 — Human-in-the-loop gates.** Make every artifact editable in natural language (Copilot Workspace pattern). Surface confidence scores and flag low-confidence requirements for explicit human review. Treat the spec as living: when code changes, re-run validation against the spec (Kiro hook pattern) and propose spec updates rather than letting drift accumulate.

**Stage 6 — Downstream emission.** From the same requirements artifact, the plugin can generate Gherkin `.feature` files (from AC blocks), test stubs (pytest/jest, one per AC), performance test scaffolds (k6/Locust, keyed to NFR response measures), a STRIDE threat-model skeleton (keyed to security NFRs), a stub ADR backlog (one per architecturally significant requirement), and the Definition of Done checklist (project-wide NFRs that apply to every PBI). This embeds shift-left from day zero and turns the SRS into a living test specification — which is the single most underexploited capability of an AI plugin operating inside a coding environment.

The principal risks to manage: NFR omission (mitigate with explicit ISO 25010 walkthrough), implementation bias (mitigate with critic agent that flags solution-leakage at stakeholder tier), surface fluency masking technical inadequacy (mitigate with INCOSE rubric scoring and require fit criteria), and silent hallucination (mitigate with mandatory assumptions section and "if unsure, say so" instruction).

---

## Conclusion

The plugin's design problem is not a research problem. The standards consensus on requirements quality is mature and stable; the prompt patterns and multi-agent architectures that mitigate LLM-specific failure modes have empirical support from 2023–2025 research; and the artifact format that survives the round-trip from human author to LLM generator to downstream LLM consumer is well understood. **The real differentiator is rigor of enforcement**: defaulting to EARS rather than free prose, prompting against ISO/IEC 25010:2023 rather than letting NFRs go unsolicited, separating generation from critique to avoid over-correction, and treating rationale and fit criterion as mandatory fields rather than nice-to-haves. The plugin that wins is the one whose Gotchas file grows fastest — because every observed failure becomes encoded into the next generation's prompt. A specification artifact that is itself a living, executable, traceable bridge to architecture, design, tests, and Definition of Done is the most leveraged single product an AI coding environment can produce, and the research is now clear enough that building it well is an engineering problem rather than a research one.
```