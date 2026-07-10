# Assumptions, Dependencies & Open Questions

## Assumptions
- A-1: There is a single local desktop owner per installation; no multi-user, account, server, or operator roles apply.
- A-2: The host OS exposes a reliable wall-clock the app can read at launch to compute the elapsed offline interval since the last save.
- A-3: The full pet state is small enough to persist to a single local file or embedded store; no external database is required.
- A-4: Colorblind-safe palettes combined with shape/text redundancy are sufficient to convey mood without a user-tunable palette in v1.
- A-5: The reference decay model and its balance values are placeholders pending tuning; requirements reference them by name rather than fixing numeric curves.

## Dependencies
- D-1: A cross-platform UI/runtime toolkit (final choice pending) capable of meeting the idle-footprint budget.
- D-2: OS-level local storage / filesystem access for the persisted state and quarantined save files.
- D-3: An OS notification facility for optional local reminders.
- D-4: OS accessibility APIs (screen reader / accessibility tree) able to surface the app's control and mood labels.

## Open Questions
- Q-1: What is the exact decay-curve and balance tuning (rates, thresholds, increments)? (owner: product/design)
- Q-2: Is death permanent, or a configurable soft reset? (owner: product)
- Q-3: Which platforms ship in v1 — all three, or Windows-first? (owner: product)
- Q-4: Which framework/runtime is chosen given the footprint constraint (Electron vs Tauri vs native)? (owner: engineering)
