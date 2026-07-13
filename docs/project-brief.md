# CovenantIQ v1.0 — one-page project brief

## One-sentence summary

CovenantIQ is a deterministic private-credit analysis platform that models multi-tranche debt, quarterly covenant compliance, downside sensitivity, saved deal structures, and investment-committee memo generation.

## Problem

Credit analysis is frequently distributed across spreadsheets, covenant trackers, scenario tabs, and memo templates. Reviewers can see an answer but may struggle to reproduce which inputs, formulas, thresholds, and decision rules produced it.

## Solution

CovenantIQ connects fictional borrower statements to debt schedules, ratios, quarterly covenant tests, downside cases, a rule-based preliminary recommendation, an evidence-level Audit Trail, saved structure comparison, and a print-optimized memo. Financial results are deterministic Python outputs; the frontend does not calculate or invent them.

## Intended audience

Private-credit, commercial-banking, leveraged-finance, and corporate-credit reviewers; fintech product teams; and engineering reviewers assessing financial-domain architecture. It is an educational portfolio project, not a production underwriting system.

## Key capabilities

- Five internally consistent fictional borrowers and normalized annual statements
- Revolver, senior secured, and subordinated or mezzanine debt tranches
- Annual and FY2026E–FY2027E quarterly credit metrics and covenant tests
- Five downside cases and a 7 × 6 revenue/margin sensitivity matrix
- Deterministic recommendation rules with exact evidence references
- SQLite-saved analysis snapshots and backend structure comparison
- Sources & Uses and a sixteen-section investment-committee memo
- Guided healthy, distressed, and deal-comparison demos

## Finance concepts demonstrated

Debt roll-forwards, average-balance cash interest, PIK accrual, commitment fees, weighted average cost, gross and net leverage, interest coverage, DSCR, fixed-charge coverage, liquidity, covenant headroom, first-breach detection, quarterly seasonality, working-capital stress, cash sweeps, Sources & Uses, and preliminary credit risk rules.

## Technical architecture

```text
Next.js + TypeScript + Recharts
             ↓ validated JSON
FastAPI + Pydantic routers
             ↓
independent Python finance engines
             ↓
SQLite snapshots + print-optimized HTML memo
```

The API orchestrates independent calculation modules. Pydantic validates the domain boundary. SQLite stores both the request and exact calculated response. React renders backend outputs and explanations.

## Verification evidence

- 26 backend tests passed
- Next.js production build passed
- Health, borrower, and guided-demo endpoints smoke-tested
- Ironbridge returns a decline and quarterly first breach
- Vantage remains the healthy approval demonstration case
- Screenshot gallery and generated Ironbridge memo are checked in

## Visual evidence

[Workspace](assets/analysis-workspace.png) · [Debt schedule](assets/multi-tranche-debt-schedule.png) · [Quarterly covenants](assets/quarterly-covenants.png) · [Sensitivity](assets/sensitivity-heatmap.png) · [Audit Trail](assets/audit-trail.png) · [Saved analyses](assets/saved-analyses.png) · [IC memo](assets/ic-memo.png)

## Known limitations

The data and policies are fictional. Quarterly phasing and revolver mechanics are simplified. SQLite is single-instance and unauthenticated. Covenant documents, lender-specific policy, legal interpretation, live borrower data, and production approval workflows are not modeled. The memo is HTML rather than a rendered PDF.

## Roadmap

Managed PostgreSQL and authentication; versioned reviewer workflows; monthly liquidity forecasting; richer covenant definitions; portfolio concentration views; and page-tested PDF rendering.

## Disclaimer

CovenantIQ is an educational portfolio project and does not constitute lending, investment, accounting, legal, or financial advice.
