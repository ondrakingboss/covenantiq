# CovenantIQ design brief

- Design read: A daily-use underwriting instrument for commercial credit analysts; sober, exact, and dense without feeling cramped.
- Concept spine: Calibration instrument. Hairlines, measured columns, tabular numerals, and explicit state changes make the interface feel audited.
- Delivery tier: Editorial app. Fast static state transitions and restrained chart animation only.
- Palette: paper `#f4f5f2`, ink `#14232c`, deep navy `#173c47`, desaturated teal `#2f6f67`, mist `#dce4e2`, risk red `#9a342d`. Teal is the single non-status accent.
- Type: Arial/Helvetica for neutral institutional legibility; system monospace for labels and figures.
- Signature interaction: D2 adapted to an app as sticky analytical tabs. The context bar remains fixed while the analyst moves through statement, structure, ratio, covenant, and scenario layers.
- Corner language: Mostly sharp with a single 4px control radius. Hairline rules provide hierarchy.
- Screen plan: institutional landing; borrower dossier grid; analysis ledger; scenario matrix; printable memo.
- v0.2 extension: preserve the calibration-instrument spine while adding six dense analytical states inside the borrower ledger: consolidated overview, tranche structure, quarterly compliance, scenarios, sensitivity heatmap, and IC memo. Add a separate ruled archive table for SQLite-saved cases.
- v0.2 data grammar: tranche schedules use horizontal workpaper tables; quarterly breaches use compact chronological blocks; sensitivity uses a muted green/red matrix with numeric results in every cell. No decorative visualization is introduced.
- Mobile: tables scroll horizontally, navigation condenses, charts retain 280px minimum height, forms become one column.
- CTA inventory: landing uses a solid rectangular launch control; borrower rows use full-row arrow movement; analysis uses a compact bordered calculation control; memo uses a plain print action.
- Asset plan: code-native CIQ monogram and favicon only. Decorative imagery is intentionally omitted because every visual region is reserved for decision-useful product data.
- Anti-convergence ledger: first build in this chat; palette, type, app-shell hero, sticky-ledger interaction, squared CTA garments, and hairline borders derive from credit files and underwriting workpapers.
- v0.3 trust extension: the Audit Trail reads as a review dossier, with a decision summary, evidence tiles, and expandable rules containing exact threshold tests and references.
- v0.3 comparison grammar: one dense backend-sourced table, a single restrained safer badge, and disclosed methodology instead of decorative scoring graphics.
- v0.3 guided flow: three reviewer cards with expected outcomes, learning points, and portfolio talking points; empty, loading, error, mobile overflow, and print states retain the institutional hierarchy.
