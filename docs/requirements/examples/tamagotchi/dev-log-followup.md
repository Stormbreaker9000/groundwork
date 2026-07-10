---
title: "Groundwork Dev Log 2: Closing the Gaps the Tamagotchi Found"
description: "A while back I ran a desktop tamagotchi through Groundwork's requirements workflow and wrote down everything it got wrong. This is the re-run — same pet, same prompt, after building the fixes."
publishedAt: "2026-07-10"
tags: ["groundwork", "sdlc", "requirements", "dev-log", "llm"]
draft: true
---

> Portable draft for eyeofthestorm.dev — adjust frontmatter / add cover art to match the site's post format before publishing.

In the [first Groundwork dev log](https://eyeofthestorm.dev/posts/dev-log-building-groundwork) I pointed the plugin's requirements workflow at a desktop tamagotchi and let it run. Then I wrote down everything the output was missing. That list of complaints wasn't really a review — it was a backlog. This post is what happened after I built it.

Same pet. Same starting prompt. Here's the before and after.

## The scoreboard

Every gap I flagged in the first post, and where it stands now:

| What the first run missed | Status | How |
| --- | --- | --- |
| Functional reqs were free-form bullets, no EARS | ✅ closed | 10 FRs, each a single EARS sentence with a declared pattern |
| The entire non-functional side was absent | ✅ closed | 7 ISO 25010 quality-attribute-scenario NFRs |
| Error paths, retention, accessibility, ops never came up | ✅ closed | An error-path FR, plus accessibility, local-data, and ops-logging NFRs |
| Acceptance criteria weren't Given/When/Then | ✅ closed | Every FR carries Gherkin AC, including negative scenarios |
| No assumptions written down | ✅ closed | A dedicated `assumptions.md` (assumptions, dependencies, open questions) |
| No self-critique / vague-word lint | ✅ closed | A content linter runs over the whole set |
| **The Electron footprint choice slipped through** | ✅ closed | Surfaced as an NFR + a constraint + an open question, flagged for review |

Seven for seven. But the last row is the one that actually matters, so I'll come back to it.

## What I built

The gaps sorted themselves into a handful of pieces, which became the M1 milestone:

- **A real interview.** The clarify step now drives past *what* to the business *why* (5-Whys), asks numbered-option questions instead of open-ended ones where it can, and runs a silent sweep over the categories LLMs habitually skip — error paths, compliance, data retention, accessibility, operations, legal, and roles beyond "the user." It's a gap check, not an interrogation: it only raises what's non-obvious and high-stakes.
- **Specialist authors.** Functional requirements come out of an agent that only knows EARS and Gherkin. Non-functional requirements come out of one that walks all nine ISO 25010 quality characteristics and writes each as a six-part scenario with a measurable response. Constraints and business rules get their own author, kept distinct from NFRs.
- **A content linter.** A deterministic pass that flags vague qualifiers ("fast", "robust"), compound requirements (`and`/`or` gluing two behaviors together), EARS non-conformance, passive voice that hides the actor, and implementation bias leaking into high-tier requirements. It's advisory — it feeds the critic and the human, it doesn't silently rewrite.
- **Externalized assumptions.** The one that the research called the highest-leverage anti-hallucination move: a dedicated section where the model has to write down what it's assuming, what it depends on, and what it still doesn't know — instead of quietly baking guesses into requirement text.
- **Confidence triage.** Every requirement carries a confidence level. Anything resting on an open question or an unconfirmed assumption is marked low and collected into a review queue, so the human gate is *review the five uncertain things*, not *re-read all twenty-two*.

## The re-run

Same tamagotchi. The pipeline produced **22 atomic requirements** — 10 functional, 7 non-functional, 3 constraints, 2 business rules — plus the assumptions file and a machine index.

Two gates ran over the result:

- The **structural validator**: 22/22 files pass. Schema-clean, IDs unique, EARS pattern present on every FR, no dangling traces, assumptions file present with its three sections.
- The **content linter**: zero findings. No vague qualifiers, no compound requirements, no passive-nameless subjects.

The first run gave me a page of bullets. This one gives me a validated, traceable set I could hand to an architect.

## The moment that made it worth it

Here's the thing that actually sold me on the whole exercise.

In the original build, the plugin waved me toward Electron, I took it, and I later ripped it out for Tauri because the footprint was wrong for an always-on desktop pet. That switch cost real time. The requirements never flagged it — footprint just wasn't a thing the process thought about.

This time, the footprint question is impossible to miss. It shows up in **three** places, all pointing at the same decision:

**NFR-002** turns it into a testable budget:

> While running idle in the background, the application process shall consume no more than the defined CPU and resident-memory budget on the reference machine.
> *Response measure:* over a 10-minute idle window, average CPU ≤ 1% of one core and resident memory ≤ 150 MB, sampled every second.
> *Confidence: low* — "the exact budget numbers depend on the framework selected, so this target is held at low confidence until that decision is made."

**CON-001** records it as a hard boundary. And **Q-4** in the assumptions file states the actual decision out loud:

> Q-4: Which framework/runtime is chosen given the footprint constraint (Electron vs Tauri vs native)? *(owner: engineering)*

And because NFR-002 and CON-001 are both low-confidence, they land in the review queue with their reasons attached:

```
- NFR-002 (low) — idle-footprint budget depends on Q-4 (framework: Electron vs Tauri vs native)
- CON-001 (low) — runtime footprint boundary rests on Q-4 (framework choice)
```

The workflow doesn't pretend to know the answer. It states the requirement, admits the uncertainty, and puts the framework decision in front of me *before* anyone writes code. That's exactly the decision I got wrong the first time by not making it a decision at all.

## A look at the artifacts

The previously-missing error path is now a first-class requirement, and it's a nice showcase of the EARS "unwanted" pattern plus Gherkin:

```markdown
FR-010 — Recover from corrupted or missing save file   (unwanted / must / high)

Description: If the saved state file is missing or fails integrity validation on
load, then the system shall start a new pet from default values without terminating.

AC-2 — Corrupted save file is quarantined, not loaded
  Given a saved state file whose integrity check fails
  When the application starts
  Then the application starts a new default pet
  And the unreadable file is retained under a quarantine name for diagnostics
```

The full generated set — all 22 requirements, the assumptions file, and the review queue — is consolidated into a single document alongside this post: [`CONSOLIDATED.md`](./CONSOLIDATED.md). The raw atomic files are in [`requirements/`](./requirements/).

## Keeping myself honest

It's still an LLM writing requirements, and I want to be straight about what that means:

- The concrete numbers (the 150 MB budget, the 60-second thresholds) are reasonable placeholders, not gospel. They're *testable*, which is the point — but a human still has to sign off on the values.
- The low-confidence flags aren't a bug to be driven to zero. Five of twenty-two items are uncertain because the underlying product decisions genuinely aren't made yet. The win is that the uncertainty is *labeled and collected* instead of hidden.
- A human still gates the set. The whole design is to make that gate cheap — review the five flagged items and the four open questions, not the entire wall of text.

## What's next

M1 — the requirements stage — is done. Next up is M2: turning a validated requirement set like this one into an architecture (component decomposition, interface design, ADRs, C4 diagrams) with the same discipline. The tamagotchi will be the guinea pig again.

The first dev log was a list of things the tool couldn't do yet. This one is the same pet clearing every item on that list. That's the loop I wanted Groundwork to close.
