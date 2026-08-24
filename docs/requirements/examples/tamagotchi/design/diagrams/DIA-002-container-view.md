---
id: DIA-002
type: diagram
title: "Container View"
description: "The deployable units of Tamagotchi Desktop Pet and the edges that cross between them."
level: container
traces_from: [BR-001, BR-002, CON-001, CON-002, CON-003, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, NFR-001, NFR-002, NFR-003, NFR-004, NFR-005, NFR-006, NFR-007]
traces_to: {}
status: draft
confidence: high
created_at: 2026-08-22
---

# Container View

```mermaid
C4Container
  title Container View — Tamagotchi Desktop Pet
  Person(actor_owner, "Pet Owner", "The single local user who cares for the pet.")
  System_Boundary(sys, "Tamagotchi Desktop Pet") {
    Container(ctr_desktop_app, "Desktop App", "Tauri Rust core + system webview", "One local process: simulation, persistence and UI.")
  }
  System_Ext(ext_cmp_010, "OS Notification Service", "Presents a message to the owner on behalf of an application that is not in focus.")
  System_Ext(ext_cmp_011, "System Clock", "Reports the current wall-clock instant.")
  Rel(actor_owner, ctr_desktop_app, "feeds, plays with and cleans the pet")
  Rel(ctr_desktop_app, ext_cmp_011, "Wall-Clock Time Source", "IF-001")
  Rel(ctr_desktop_app, ext_cmp_010, "Desktop Notification Delivery", "IF-012")
```
