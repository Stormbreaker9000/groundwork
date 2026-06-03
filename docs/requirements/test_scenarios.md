# Requirements Skill — Manual Test Scenarios

Use these scenarios to exercise the `/groundwork requirements` skill end-to-end. Each entry includes the prompt to paste into a fresh session, the project context, and what to watch for during the conversation.

---

## How to Use

1. Start a new Claude Code session in a relevant directory (see each scenario's setup note).
2. Paste the **Prompt** verbatim — no extra framing.
3. Work through the full conversation until the artifact is saved and committed.
4. Check against the **What to watch for** notes to verify correct behavior.

---

## Scenario 1 — Simple CRUD Feature (Baseline)

**Prompt:**
> Add a notes feature to the app. Users should be able to write, edit, and delete notes.

**Project type:** Addition to an existing codebase (any REST API with a DB will do; a minimal Express/Postgres app is ideal)

**Why it's interesting:**
This is the simplest possible case — straightforward CRUD with no edge cases. It tests that the skill doesn't over-engineer the conversation: hypotheses should be grounded and concise, the exchange count should stay at 2–3, and the artifact should be lean. A regression here means the skill is adding friction to simple requests.

**What to watch for:**
- Skill reads the existing codebase before hypothesizing (Phase 1)
- Hypotheses reference the actual stack found (e.g., "Sequelize model" not generic "database table")
- Does not ask redundant questions about things clearly implied by the stack
- Artifact has specific, testable acceptance criteria — not vague ones like "notes work correctly"
- Commit message follows the expected convention

---

## Scenario 2 — Compliance Constraints (GDPR Right to Erasure)

**Prompt:**
> We need to add a data export and account deletion feature. Users must be able to download all their data and permanently delete their account.

**Project type:** Addition to an existing codebase with user accounts and stored personal data

**Why it's interesting:**
GDPR Article 17 (right to erasure) and Article 20 (data portability) impose specific legal requirements that must appear in the artifact — not just as "functional requirements" but as domain requirements with defined behavior. The skill needs to surface that deletion must be irreversible, that export must include all PII across all tables, and that there may be retention exceptions (e.g., billing records). The user may not volunteer these constraints; the hypotheses should surface them.

**What to watch for:**
- Hypotheses mention legal/compliance context (GDPR, data portability, retention exceptions)
- Domain Requirements section appears in the artifact and is populated
- Acceptance criteria include irreversibility and completeness of export — not just "a button exists"
- Out of Scope explicitly handles what happens to anonymized/aggregate data
- Skill asks about downstream systems if the codebase has integrations (analytics, email providers)

---

## Scenario 3 — Non-Obvious NFRs (Real-Time Collaboration)

**Prompt:**
> Add real-time collaborative editing to our document editor so multiple users can work on the same document at once.

**Project type:** Addition to an existing codebase (a single-user document editor with save/load)

**Why it's interesting:**
This request sounds like a feature but is actually an architectural shift. The non-functional requirements — conflict resolution strategy, latency targets, connection recovery behavior, presence indicators — are load-bearing and non-obvious to a user who hasn't built real-time systems. The skill should surface these through hypotheses rather than accepting a thin functional description. A naive artifact that only says "users can edit simultaneously" is a failure mode.

**What to watch for:**
- Hypotheses include conflict resolution (OT vs CRDT vs last-write-wins), latency expectations, and offline/reconnect behavior
- NFR section is populated with at least latency, consistency model, and concurrent user target
- Skill asks about the current persistence layer — WebSockets require server-side changes not obvious from a REST API
- Artifact does not treat "real-time" as a given without pinning down what "real-time" means (e.g., < 500ms propagation)
- Scope boundary: does presence (who's online) need to be built now or later?

---

## Scenario 4 — Greenfield with Unclear Stakeholders

**Prompt:**
> I want to build a tool that helps independent musicians manage their releases — things like tracking which platforms their music is on, release dates, promo materials, and that kind of stuff.

**Project type:** Greenfield — no existing codebase

**Why it's interesting:**
The domain is clear but the stakeholders and success conditions are not. "Independent musicians" covers a solo bedroom producer and a small band with a manager. "Manage" could mean anything from a spreadsheet replacement to an automated distributor integration. The skill should push for a specific primary user and a concrete first-use scenario, not accept the vague framing as ground truth. Phase 1 will find no codebase, so hypotheses must be built purely from domain reasoning.

**What to watch for:**
- Skill correctly detects no existing codebase and skips Phase 1 reads
- Hypotheses are domain-grounded despite no codebase context
- Skill asks who the primary user is and what their most painful current workflow looks like
- Artifact's Overview names a specific target user (not "musicians in general")
- Out of Scope handles distributor API integration if it came up but was deferred
- Acceptance criteria describe user-facing outcomes, not implementation details

---

## Scenario 5 — Multi-Role Feature (Content Approval Workflow)

**Prompt:**
> We need an approval workflow for blog posts. Writers submit drafts, editors review and can approve or reject with comments, and admins can override any decision.

**Project type:** Addition to an existing CMS or content management codebase

**Why it's interesting:**
Three roles with different permissions and different views of the same data. The skill must elicit what each role sees, what actions each can take, and what happens in edge cases: what if an editor rejects a post an admin already approved? Can writers edit a post after submission? What happens to comments on rejection? These branch conditions won't be volunteered — they need to be surfaced through targeted questions. This scenario also tests whether the skill decomposes (it shouldn't — this is one coherent feature).

**What to watch for:**
- Skill does NOT decompose — writer/editor/admin are roles within one workflow, not separate features
- Hypotheses enumerate the state machine (draft → submitted → approved/rejected → published)
- At least one exchange probes the edge case of role conflicts or re-submission after rejection
- Functional Requirements section is organized by role or by state transition — not a flat list
- Acceptance criteria cover each role's key actions with specific conditions

---

## Scenario 6 — Data Migration with Transition Concerns

**Prompt:**
> We're moving our user preferences from a flat JSON blob stored in the users table to a dedicated preferences table with typed columns. We need to migrate existing data over.

**Project type:** Addition/refactor to an existing codebase with production data

**Why it's interesting:**
Migrations have a dual lifecycle: the schema change and the data backfill, with a window where both the old and new format must work. The skill should surface the zero-downtime requirement (if any), the rollback strategy, what happens to preferences written during the migration window, and how the cutover is validated. Users often think of migrations as a one-step operation; the skill should reveal the phases.

**What to watch for:**
- Hypotheses include the dual-read/dual-write transition period and rollback path
- Skill asks about production data volume — a 10-row dev table and a 10M-row prod table have different migration strategies
- Constraints section captures zero-downtime requirement or explicitly notes it was out of scope
- Acceptance criteria include a post-migration validation step (e.g., row count reconciliation)
- Out of Scope handles whether the old column is dropped in this iteration or a follow-up

---

## Scenario 7 — Internationalization and Accessibility

**Prompt:**
> We need to add multi-language support to the checkout flow. We have users in the US, France, and Japan, so we need English, French, and Japanese at minimum. Also, the checkout needs to be accessible — we've had complaints about it failing with screen readers.

**Project type:** Addition to an existing e-commerce frontend (React or similar)

**Why it's interesting:**
Two distinct cross-cutting concerns bundled in one request — i18n and a11y. The skill should decide whether to decompose (probably not — they're both checkout-scoped and will touch the same files) and then surface the non-obvious NFRs for each: locale-specific formatting (currency, dates, address formats), RTL support for future locales, WCAG compliance level, and the testing strategy for screen readers. The user's phrasing ("had complaints") suggests existing violations that need to be fixed, not just new ones to avoid.

**What to watch for:**
- Skill considers but decides against decomposition — both are checkout-scoped additions
- Hypotheses include locale-specific formatting (not just translated strings) and WCAG target level
- NFR section covers locale formatting, fallback locale behavior, and accessibility standard (WCAG 2.1 AA vs AAA)
- Skill asks whether RTL support is needed — Japanese is not RTL, but it surfaces future-proofing intent
- Out of Scope handles whether non-checkout pages are in scope for this iteration
- Acceptance criteria include screen-reader-specific tests, not just visual checks

---

## Scenario 8 — Vague Scope That Should Trigger Decomposition

**Prompt:**
> Build a dashboard for our marketing team. They want to see campaign performance, manage their content calendar, and track their budget spend.

**Project type:** Greenfield internal tool (or addition if there's an existing marketing app)

**Why it's interesting:**
Three functionally independent areas, each with its own data model, user interactions, and acceptance criteria. The skill should decompose this rather than producing one bloated artifact that conflates campaign analytics, a calendar UI, and financial tracking. The decomposition exchange is itself a testable behavior — the skill must name the units clearly and propose a starting point, not just ask a vague clarifying question.

**What to watch for:**
- Skill triggers the Phase 2 decomposition path — explicitly names the three independent units
- Decomposition message proposes a concrete starting unit (e.g., "Want to start with campaign performance since it's the most foundational?")
- Does NOT attempt to write one combined artifact for all three areas
- Full Phase 3–5 cycle runs for whichever unit the user picks
- Remaining units are acknowledged as future conversations, not silently dropped
