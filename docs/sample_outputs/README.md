# CovenantIQ sample outputs

This directory contains checked-in evidence generated from CovenantIQ’s fictional borrower data and deterministic Python engines. It is intended for portfolio review, not for a real credit decision.

## Included output

### Ironbridge Components investment-committee memo

[Open `ironbridge_ic_memo.html`](ironbridge_ic_memo.html).

The file is generated from Ironbridge’s default multi-tranche structure, covenant package, base and downside cases, sensitivity matrix, recommendation, and Audit Trail. It includes Sources & Uses, debt structure, annual and quarterly metrics, covenant analysis, key risks and mitigants, conditions precedent, monitoring recommendations, and the methodology disclaimer.

Expected demonstration result:

- Recommendation: **Decline**
- Risk grade: **8**
- First modeled covenant breach: **FY2026Q1**
- Audit focus: an early base-case quarterly covenant breach triggers the decline rule

## Companion screenshot evidence

| Surface | File |
|---|---|
| Landing page | [../assets/landing-page.png](../assets/landing-page.png) |
| Borrower selection | [../assets/borrower-selection.png](../assets/borrower-selection.png) |
| Analysis workspace | [../assets/analysis-workspace.png](../assets/analysis-workspace.png) |
| Multi-tranche debt schedule | [../assets/multi-tranche-debt-schedule.png](../assets/multi-tranche-debt-schedule.png) |
| Quarterly covenant tests | [../assets/quarterly-covenants.png](../assets/quarterly-covenants.png) |
| Sensitivity heatmap | [../assets/sensitivity-heatmap.png](../assets/sensitivity-heatmap.png) |
| Audit Trail | [../assets/audit-trail.png](../assets/audit-trail.png) |
| Saved analyses and comparison | [../assets/saved-analyses.png](../assets/saved-analyses.png) |
| Investment-committee memo | [../assets/ic-memo.png](../assets/ic-memo.png) |

## Expected case summaries

### Vantage Services

Vantage is the healthy approval demonstration. In the default structure it remains approvable in base and mild downside cases, with no early base-case quarterly covenant breach. In the verified default sensitivity request, opening net leverage moves from **1.18x** in the unshocked cell to **3.42x** in the most severe cell, while interest coverage moves from **5.34x** to **2.74x**.

### Ironbridge Components

Ironbridge is the stressed decline demonstration. Weak performance and leverage produce an early quarterly covenant breach and a deterministic decline. The memo and Audit Trail expose the exact failed comparison rather than adding generated rationale.

## Regenerate the memo

From the repository root, install backend dependencies, then run:

```bash
cd backend
../.venv/bin/python scripts/generate_sample_memo.py
```

The script writes `docs/sample_outputs/ironbridge_ic_memo.html` from current borrower data and calculation code. Review any output diff before publishing because a changed formula, rule, or demo input can legitimately change the memo.

## Disclaimer

All borrowers and transactions are fictional. These outputs are educational portfolio artifacts and do not constitute lending, investment, accounting, legal, or financial advice.
