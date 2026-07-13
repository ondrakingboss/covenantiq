# Financial methodology

All calculations are deterministic Python functions. No LLM or external AI API participates in financial values, covenant status, scenario results, risk grade, or recommendation.

## Normalization

Raw JSON contains six annual periods per borrower plus operating assumptions. The normalization engine derives a consistent statement set:

- EBITDA = revenue × EBITDA margin
- EBIT = EBITDA − depreciation
- Interest expense = debt × period interest rate
- Taxes = max(EBIT − interest, 0) × tax rate
- Net income = EBIT − interest − taxes
- Receivables = revenue × receivable days ÷ 365
- Inventory = revenue × inventory days ÷ 365
- Current assets = cash + receivables + inventory + other current assets
- Free cash flow = operating cash flow − capital expenditure

## Debt schedule

- Opening legacy debt = latest actual debt − debt refinanced, floored at zero
- New borrowing occurs in the first projected year
- Mandatory amortization = original loan × configured amortization percentage + existing mandatory amortization, capped at balance
- Optional repayment = minimum of 25% of excess FCF, cash above minimum, and remaining debt
- Cash interest = average annual balance × annual cash rate
- Effective interest = cash interest + straight-line amortization of upfront fees

## Ratios

- Gross leverage = total debt ÷ EBITDA
- Net leverage = (total debt − cash) ÷ EBITDA
- Interest coverage = EBITDA ÷ cash interest
- CFADS = operating cash flow + cash interest − capital expenditure
- DSCR = CFADS ÷ (cash interest + mandatory amortization)
- Fixed-charge coverage = (EBITDA − capital expenditure) ÷ (cash interest + mandatory amortization + 15% of lease liabilities)
- Current ratio = current assets ÷ current liabilities
- Quick ratio = (current assets − inventory) ÷ current liabilities
- Minimum liquidity = cash + undrawn revolving commitment
- Free cash flow after debt service = free cash flow − cash interest − mandatory amortization

If EBITDA is non-positive, leverage is `not_meaningful`. If cash interest is zero, interest coverage is `not_meaningful`. Missing inputs are `unavailable`. The engine does not replace these cases with zero.

## Covenants

For maximum covenants, absolute headroom is threshold − calculated value. For minimum covenants, it is calculated value − threshold. Percentage headroom divides absolute headroom by the absolute threshold where non-zero. Negative headroom is a failure.

Severity uses percentage headroom: at least 10% is `none`; 0% to 10% is `watch`; 0% to −10% is `moderate`; below −10% is `severe`. Unavailable or not-meaningful values are `not_tested`, never silently passed.

## Scenario translation

Shocks apply only to projected periods. Revenue is changed by the scenario percentage. EBITDA is recalculated from shocked revenue and a basis-point margin change. Receivable and inventory balances are rebuilt from shocked revenue and increased days. A further working-capital outflow is deducted from operating cash flow. Capital expenditure scales by half the revenue shock. Cash accumulates negative FCF variance. Interest rates flow through both statement interest and the proposed debt schedule. Ratios and covenants are then recalculated from the shocked statements and schedule.

## Recommendation rules

The rules inspect opening projected gross leverage, interest coverage, liquidity, free cash flow after debt service, base-case covenant failures, severe-case failures, and timing.

- `Decline`: at least two base failures, or immediate severe failure combined with negative debt-service cash flow
- `Further diligence required`: a base failure or non-meaningful core ratio
- `Approve with conditions`: base supportable but selected severe case fails
- `Approve`: base and selected downside cases remain compliant and cash-generative

Risk grades map to the rule branch (3, 4, 6, or 8). Calculation references in the response identify the source metrics.

## Multi-tranche debt

Each revolver, senior secured, and subordinated tranche rolls independently:

- Pre-amortization balance = opening balance − refinancing + new borrowing
- Mandatory amortization = pre-amortization balance × annual amortization percentage × period fraction
- PIK accrual = post-amortization balance × coupon × period fraction
- Cash interest = average pre/post-amortization balance × cash coupon × period fraction
- Revolver availability = commitment − ending drawn balance, floored at zero
- Commitment fee = undrawn revolver capacity × commitment-fee rate × period fraction
- Ending balance = post-amortization balance + PIK − optional repayment

The optional excess-cash-flow sweep is limited by positive FCF after contractual debt service and cash above minimum. It is allocated to revolver, then senior secured debt, then subordinated debt. Consolidated weighted average cash rate equals the average-balance-weighted cash coupon.

## Quarterly projection

FY2026E and FY2027E are split into eight quarters. Annual revenue, EBITDA, OCF, and capex totals reconcile to each annual projection before debt service. Meridian Retail uses 21%/22%/24%/33% revenue phasing with Q4-weighted cash conversion. Alder Manufacturing uses 23%/24%/25%/28% revenue phasing and back-half-weighted OCF. Other borrowers use a moderate 24%/25%/25%/26% revenue pattern.

Quarterly cash equals prior cash plus quarterly FCF less consolidated cash interest, mandatory amortization, and optional repayment. Leverage uses quarter-end debt divided by the annual EBITDA proxy. Coverage and DSCR annualize the current quarter run rate. These are deliberate simplifications, not lender-grade LTM calculations.

## Sensitivity grid

The grid applies each revenue shock and EBITDA margin-basis-point shock to projected operating statements before recalculating cash flow, multi-tranche debt, ratios, and quarterly covenant tests. Default dimensions are seven revenue shocks by six margin shocks, producing 42 deterministic cells. Each cell returns opening net leverage, coverage, DSCR, liquidity, covenant state, and first quarterly breach.

## SQLite persistence

The `analyses` table stores identifiers, borrower, name, timestamp, recommendation metadata, the exact validated request JSON, and the exact calculated response JSON. Reopening does not silently recalculate the stored result. The database is created automatically and can be redirected with `COVENANTIQ_DB_PATH`.

## Recommendation audit trail

The private-credit recommendation adds a quarterly override to the verified annual rules: a base-case covenant breach in FY2026Q1 through FY2026Q4 produces a Decline. The Audit Trail evaluates this and every disclosed rule whether or not it triggers. Evidence records include actual value, comparison operator, threshold, unit, scenario, period, status, and an exact calculation reference.

The plain-language audit explanation is assembled from rule outputs and the calculated first-breach result. It is deterministic template logic, not generated by an LLM.

## Deal comparison safety score

Saved structures for the same borrower are compared using their stored backend results. The score rewards stronger recommendation categories, lower risk grades, no base-case quarterly breach, lower net leverage, stronger interest coverage and DSCR, liquidity relative to funded capital, and a modest sponsor-equity contribution. Every component is returned as a readable safety factor.

The highest score is labeled safer. This is a relative educational comparison, not a lender rating or approval policy.
