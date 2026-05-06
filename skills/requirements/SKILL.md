---
name: requirements
description: Use before implementing any feature or change - turns vague requests into structured requirements with acceptance criteria before any code is written.
---

# Requirements Gathering

Stop before writing code. Turn the request into a brief that both you and the user agree on.

## When This Applies

Invoke this skill when the user makes a vague implementation request:
- "Build X"
- "Add Y"
- "Make it do Z"
- "I want a feature that..."

Do NOT invoke for questions, explanations, bug reports with clear reproduction steps, or requests to read/explore code.

## Process

Ask one clarifying question at a time. Do not present a list of questions. Do not start implementing.

**Question 1 — Problem:** What specific problem does this solve? Who experiences it and when?

**Question 2 — Done:** What does success look like? How will you know when it's working?

**Question 3 — Constraints:** Are there things this must not do, or boundaries it must stay within?

**Question 4 — Scope:** What is explicitly out of scope for this change?

Once you have answers, produce the requirements brief.

## Requirements Brief Format

```
## Requirements Brief

**Problem:** [One sentence: what breaks or is missing and for whom]

**Acceptance Criteria:**
- [ ] [Specific, testable condition]
- [ ] [Specific, testable condition]

**Constraints:** [What this must not do or must stay within]

**Out of Scope:** [What will not be addressed in this change]
```

## Sign-Off Gate

Present the brief and ask: "Does this match what you have in mind, or should we adjust anything before proceeding?"

Do NOT write any code until the user confirms the brief.
