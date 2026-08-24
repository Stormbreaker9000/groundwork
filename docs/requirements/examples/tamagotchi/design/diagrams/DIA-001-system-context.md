---
id: DIA-001
type: diagram
title: "System Context"
description: "System context for Tamagotchi Desktop Pet: its actors, its boundary, and the external systems it depends on."
level: context
traces_from: [FR-001, FR-002, FR-008, FR-009, NFR-001, NFR-002, NFR-003, NFR-004, NFR-005, NFR-006, NFR-007, CON-001, CON-002]
traces_to: {}
status: draft
confidence: high
created_at: 2026-08-22
---

# System Context

```mermaid
C4Context
  title System Context — Tamagotchi Desktop Pet
  Person(actor_owner, "Pet Owner", "The single local user who cares for the pet.")
  System(sys, "Tamagotchi Desktop Pet", "An offline desktop pet whose state decays over real elapsed time.")
  System_Ext(ext_cmp_010, "OS Notification Service", "Presents a message to the owner on behalf of an application that is not in focus.")
  System_Ext(ext_cmp_011, "System Clock", "Reports the current wall-clock instant.")
  Rel(actor_owner, sys, "feeds, plays with and cleans the pet")
  Rel(sys, ext_cmp_011, "Wall-Clock Time Source", "IF-001")
  Rel(sys, ext_cmp_010, "Desktop Notification Delivery", "IF-012")
```
