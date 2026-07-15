# CovenantIQ public launch package

Verified live application: [covenantiq-eight.vercel.app](https://covenantiq-eight.vercel.app/)

Public repository: [github.com/ondrakingboss/covenantiq](https://github.com/ondrakingboss/covenantiq)

## LinkedIn launch post

I wanted to build something closer to a real credit-risk workflow than another generic AI finance dashboard.

So I built CovenantIQ, a public-beta credit risk workbench for private-credit analysis.

The application brings the main steps of a credit review into one traceable workflow:

- multi-tranche debt modeling across revolver, senior secured, and subordinated debt;
- annual and quarterly covenant compliance;
- downside sensitivity across operating scenarios and a two-variable revenue/margin grid;
- saved deal structures and deterministic structure comparison;
- Audit Trail explanations that show which rule triggered, the supporting metric, and the exact threshold comparison; and
- investment-committee memo generation from the same calculated outputs.

The central design choice was to keep the finance engine deterministic. Debt balances, cash interest, leverage, coverage, DSCR, liquidity, covenant headroom, sensitivity cells, and preliminary recommendations are calculated in Python using explicit formulas and reviewable rules. There are no black-box AI financial calculations.

Two sample borrower files make the workflow concrete:

- Vantage Services shows the healthier approval case, with strong coverage, positive cash generation, and no early base-case covenant breach in the default structure.
- Ironbridge Components shows the distressed case: Decline, risk grade 8, and a first modeled covenant breach in FY2026Q1. Its Audit Trail links that result to the specific rule, period, metric, and failed threshold.

Tech stack: FastAPI, Python, Next.js, TypeScript, SQLite, Recharts, Render, and Vercel.

I built CovenantIQ to demonstrate financial-domain engineering, explainable decision logic, and product design for an analyst workflow. I would welcome feedback from people working in private credit, commercial banking, leveraged finance, fintech, or financial software.

CovenantIQ is a public beta using sample borrower data. Outputs are for product demonstration and education only and do not constitute lending, investment, legal, accounting, or financial advice.

## LinkedIn Featured description

CovenantIQ is a public-beta credit-risk workbench for deterministic private-credit analysis: multi-tranche debt, quarterly covenants, downside sensitivity, audit trails, saved structures, and IC memos. Built with Python/FastAPI and Next.js.

Character count: 240, including spaces.

## Pinned comment

Live app: https://covenantiq-eight.vercel.app/

GitHub: https://github.com/ondrakingboss/covenantiq

CovenantIQ uses sample borrower data. The calculations and recommendations are deterministic and intended for product demonstration and education only.

## Screenshot recommendations

Recommended carousel order:

1. `docs/assets/landing-page.png` — opening product frame and the traceable decision-chain positioning.
2. `docs/assets/saved-analyses.png` — Vantage Services approval structures, sponsor-equity comparison, and deterministic safer-structure selection.
3. `docs/assets/audit-trail.png` — Ironbridge decline, FY2026Q1 first breach, adverse metrics, and the beginning of the rule trace.
4. `docs/assets/sensitivity-heatmap.png` — revenue and EBITDA-margin sensitivity with leverage and first-breach results.

All four files exist at 1425×990 pixels except `saved-analyses.png`, which is 1440×1000. The existing screenshots were captured before the latest public-beta navigation-copy pass, so the header wording in the images is older than the deployed interface. Refreshing these captures before posting would give the strongest public presentation; the analytical content shown remains representative of the current product.

Suggested image captions:

- Credit conclusions flow from normalized statements through debt, covenants, stress, and a rule-based decision.
- Saved Vantage structures compare leverage, coverage, liquidity, sponsor equity, and covenant results using backend-calculated metrics.
- Ironbridge's decline is traceable to an FY2026Q1 breach and explicit threshold evidence.
- Every sensitivity cell recalculates the financial statements, debt service, ratios, liquidity, and covenant result.

## 60–90 second walkthrough script

“This is CovenantIQ, a public-beta credit risk workbench I built to model a more realistic private-credit review.

I’ll start with Vantage Services, the healthier case. The workspace combines normalized financial statements with a multi-tranche debt structure, consolidated interest, leverage, coverage, liquidity, and annual and quarterly covenant tests. In the default structure, the rules-based result is Approve.

Now I’ll switch to Ironbridge Components. Revenue is falling, margins are compressed, and debt-service capacity is weak. The model returns Decline with a first covenant breach in FY2026Q1. The Audit Trail is the important part: it shows the exact decision rule, calculated metric, threshold, period, scenario, and supporting reference instead of generating a black-box explanation.

The sensitivity grid then reruns revenue and EBITDA-margin shocks through the statements, debt schedule, ratios, liquidity, and covenants. Saved analyses let me compare financing structures, including debt levels and sponsor equity, using backend-calculated metrics.

Finally, the same deterministic outputs flow into a print-ready investment-committee memo. All financial calculations are implemented in Python—there is no LLM calculating debt balances, ratios, covenant compliance, or recommendations.

CovenantIQ is deployed on Vercel and Render and uses sample borrower data. It is a public-beta portfolio project for demonstration and education, not professional financial advice.”

## Short CV bullet

- Built and deployed CovenantIQ, a deterministic private-credit workbench modeling multi-tranche debt, quarterly covenants, downside sensitivity, saved deal structures, explainable recommendations, and IC memos using FastAPI/Python, Next.js/TypeScript, SQLite, Recharts, Render, and Vercel.
