---
id: FR-001
type: functional
priority: must
status: approved
traces_from:
- BR-001
traces_to:
  design: []
  tests:
  - tests/orders/test_place_order.py
  code: []
---

# Place an order

Correctly shaped: it cites the business rule it implements in `traces_from`,
and its `traces_to.tests` holds a test path. Nothing here may be flagged.
