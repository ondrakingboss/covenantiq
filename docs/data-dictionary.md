# Data dictionary

All amounts are USD millions unless stated otherwise. Fiscal-year suffix `A` means actual and `E` means estimate.

| Field | Definition |
|---|---|
| revenue | Recognized annual sales |
| ebitda | Earnings before interest, tax, depreciation, and amortization |
| ebit | EBITDA less modeled depreciation |
| interest_expense | Existing financial statement interest expense |
| taxes | Cash-tax proxy, floored at zero |
| net_income | EBIT less interest and taxes |
| cash | Unrestricted cash proxy |
| accounts_receivable | Trade receivables derived from receivable days |
| inventory | Inventory derived from inventory days |
| current_assets | Cash, receivables, inventory, and other current assets |
| current_liabilities | Modeled operating current liabilities |
| total_debt | Funded debt, excluding lease liabilities |
| lease_liabilities | Reported operating and finance lease liabilities |
| operating_cash_flow | Cash flow from operations before capital expenditure |
| capital_expenditure | Positive-form annual capital expenditure |
| free_cash_flow | Operating cash flow less capital expenditure |
| mandatory_debt_amortization | Existing scheduled principal repayment |
| annual_interest_rate | Decimal annual cash rate, where `0.08` means 8% |
| amortization_percentage | Decimal percentage of original new-loan principal repaid annually |
| calculated_value | Covenant metric result before threshold comparison |
| absolute_headroom | Direction-aware distance to threshold |
| percentage_headroom | Absolute headroom divided by absolute threshold |
| tranche_type | Revolver, senior secured term loan, or subordinated debt |
| refinancing_amount | Amount reducing a tranche opening balance at transaction close |
| pik_accrual | Non-cash interest added to tranche principal |
| commitment_amount | Revolving facility maximum capacity |
| revolver_availability | Commitment less ending drawn balance |
| commitment_fee | Cash fee on undrawn revolver capacity |
| weighted_average_cash_interest_rate | Average-balance-weighted cash coupon across tranches |
| quarterly period | Fiscal label such as `FY2026Q3` |
| sensitivity cell | Revenue-shock and margin-shock combination with recalculated outputs |

Raw borrower records also contain receivable days, inventory days, tax rate, depreciation percentage, cash-flow margin, capital-expenditure percentage, and current-liability percentage used in normalization.
