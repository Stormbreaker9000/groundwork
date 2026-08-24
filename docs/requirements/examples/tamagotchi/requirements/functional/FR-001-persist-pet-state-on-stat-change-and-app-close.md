---
id: FR-001
type: functional
tier: stakeholder
title: Persist pet state on stat change and app close
description: When a pet stat value changes or the owner closes the application, the system shall persist the current pet state to local storage.
rationale: "Without persistence the pet's progress and current condition would be lost between sessions, defeating the premise that the pet is a persistent companion the owner returns to — the core mechanic the daily-return habit loop depends on. Persistence covers the pet state in full and not only its stat values: FR-006's Sleeping state and FR-011's wake deadline both survive an application close only because the Awake/Sleeping field and the sleep-entry timestamp are persisted with everything else."
fit_criterion: "Every field of the pet state held at close round-trips unchanged: across 50 restart cycles, 100% of persisted fields are present in the restored state and equal to their pre-close values, with 0 fields absent and 0 fields differing. The fields under test include, and are not limited to, every pet stat value, the health status, the Awake/Sleeping state field, the sleep-entry timestamp wherever the pet is Sleeping, and the last-saved timestamp."
priority: must
confidence: high
verification_method: test
ears_pattern: event
status: draft
created_at: 2026-08-24
traces_from: [CON-002, BR-002]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# FR-001 — Persist pet state on stat change and app close

## Description
When a pet stat value changes or the owner closes the application, the system shall
persist the current pet state to local storage.

## Rationale
Without persistence the pet's progress and current condition would be lost between
sessions, defeating the premise that the pet is a persistent companion the owner returns
to — the core mechanic the daily-return habit loop depends on. Persistence covers the pet
state in full and not only its stat values: FR-006's Sleeping state and FR-011's wake
deadline both survive an application close only because the Awake/Sleeping field and the
sleep-entry timestamp are persisted with everything else.

## Acceptance Criteria
### AC-1 — State is written when a stat changes
```gherkin
Given the owner performs a feed action that changes the pet's hunger stat
When the stat change is applied
Then the updated pet state, including the new stat value and a save timestamp, is written to local storage immediately
```

### AC-2 — State is written on application close
```gherkin
Given the pet's current state has not yet been saved since the last stat change
When the owner closes the application
Then the final pet state is written to local storage before the process exits
```

### AC-3 — Sleep state and its entry timestamp survive a close
```gherkin
Given the pet is in the Sleeping state with a recorded sleep-entry timestamp
And a positive interval of less than the defined sleep duration will have elapsed when the application is reopened
When the owner closes the application and reopens it
Then the pet is in the Sleeping state
And its sleep-entry timestamp equals the value recorded before the close
```

## Fit Criterion
Every field of the pet state held at close round-trips unchanged: across 50 restart cycles,
100% of persisted fields are present in the restored state and equal to their pre-close
values, with 0 fields absent and 0 fields differing. The fields under test include, and are
not limited to, every pet stat value, the health status, the Awake/Sleeping state field, the
sleep-entry timestamp wherever the pet is Sleeping, and the last-saved timestamp.
