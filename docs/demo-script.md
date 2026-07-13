# CovenantIQ 60–90 second demo script

## Before recording

Start on the landing page with the API running. Keep the Vantage and Ironbridge analysis routes available, and save a conservative and aggressive structure for Vantage if you want to show comparison without pausing to enter terms.

## Spoken walkthrough

“CovenantIQ is a deterministic private-credit analysis platform. It turns borrower financials and a proposed debt structure into quarterly covenant tests, downside sensitivity, an explainable recommendation, and an investment-committee memo. All financial logic runs in Python; there is no LLM calculating ratios or making the decision.

I’ll start with the guided demos. Vantage Services is the healthy case. In the workspace, I can review historical and projected performance, configure revolver, senior, and subordinated tranches, and see the consolidated debt schedule. The base and mild cases remain approvable because coverage, liquidity, and free cash flow support the structure.

The quarterly covenant view is important: it tests FY2026 and FY2027 quarter by quarter, so the model identifies the first breach period rather than hiding seasonality inside an annual average.

Now I’ll switch to Ironbridge Components. This borrower declines, with the first modeled breach in FY2026Q1. The Audit Trail explains exactly why: it shows the rule that fired, the failed covenant, the calculated value, the threshold, the scenario, and the calculation reference. The language is generated from those results deterministically.

The sensitivity grid runs 42 combinations of revenue and margin pressure. Each cell recalculates leverage, coverage, DSCR, liquidity, covenant status, and first breach, so worsening colors represent a full statement-level rerun rather than a cosmetic ratio adjustment.

On Saved Analyses, I can compare conservative and aggressive structures for the same borrower. The backend selects the safer structure using disclosed criteria such as leverage, coverage, liquidity, breaches, risk grade, and sponsor equity.

Finally, the IC memo uses the same calculated output to assemble Sources & Uses, debt structure, covenant analysis, downside cases, risks, conditions, monitoring recommendations, and methodology in a print-ready format.

The project demonstrates private-credit concepts, deterministic financial engineering, explainable decision rules, persistence, API design, testing, and an analyst-focused Next.js interface. It is an educational portfolio project, not a production lending system or financial advice.”

## Click path and talking points

| Time | Action | Point to make |
|---:|---|---|
| 0:00 | Open `/` and click **Take the guided tour** | Deterministic end-to-end workflow; no AI calculation layer. |
| 0:10 | Open **Healthy borrower approval** | Vantage is the approval story; evidence supports the decision. |
| 0:24 | Show debt schedule and quarterly covenants | Consolidated and tranche-level mechanics feed quarter-specific tests. |
| 0:37 | Open Ironbridge and expand **Why this recommendation?** | Exact rule, threshold comparison, first breach, and reference. |
| 0:50 | Show the sensitivity matrix | 42 deterministic recalculations, not frontend arithmetic. |
| 1:02 | Open **Saved analyses** and compare two Vantage cases | Backend-owned safer-structure selection and disclosed scoring. |
| 1:15 | Open the IC memo and print preview | One calculated result set flows into the decision document. |
| 1:25 | Return to the landing page | Close with finance, engineering, and explainability scope plus disclaimer. |

If time is limited, prioritize Ironbridge’s Audit Trail, the sensitivity grid, and the saved-structure comparison. Those surfaces show the project’s central claim: every displayed conclusion can be traced to deterministic inputs and rules.
