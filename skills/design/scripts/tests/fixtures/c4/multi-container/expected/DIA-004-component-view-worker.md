---
id: DIA-004
type: diagram
title: "Component View — Worker"
description: "Internal structure of the Worker container."
level: component
container: worker
traces_from: [FR-003]
traces_to: {}
status: draft
confidence: high
created_at: 2026-08-22
---

# Component View — Worker

```mermaid
C4Component
  title Component View — Worker
  Container_Boundary(ctr_worker, "Worker") {
    Component(cmp_004, "Notification Worker", "Python", "Sends order confirmations.")
  }
  Container(ctr_app, "Order App", "Python", "Single deployable service.")
  Rel(cmp_004, ctr_app, "Order Persistence", "IF-001")
```
