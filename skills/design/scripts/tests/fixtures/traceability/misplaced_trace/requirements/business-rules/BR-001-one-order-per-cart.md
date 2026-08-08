---
id: BR-001
type: business_rule
priority: must
status: approved
traces_from: []
traces_to:
  design: []
  tests:
  - FR-001
  code:
  - FR-001
  - src/orders/cart.ts
---

# One order per cart

The other half of the pre-STO-102 shape: the old rule told business rules to
list the FRs implementing them under traces_to.tests/code. The real source-file
reference alongside them is what proves the rule flags only resolving ids.
