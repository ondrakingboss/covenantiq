from __future__ import annotations

from copy import deepcopy

from app.models.domain import FinancialPeriod, LoanConfig, ScenarioDefinition
from app.services.financial_engine import r


DEFAULT_SCENARIOS = [
    ScenarioDefinition(id="base", name="Base", revenue_change=0, ebitda_margin_change_bps=0,
                       interest_rate_change_bps=0),
    ScenarioDefinition(id="mild", name="Mild downside", revenue_change=-0.10,
                       ebitda_margin_change_bps=-200, interest_rate_change_bps=100,
                       receivable_days_increase=5, inventory_days_increase=3,
                       working_capital_outflow_pct_revenue=0.01),
    ScenarioDefinition(id="severe", name="Severe downside", revenue_change=-0.20,
                       ebitda_margin_change_bps=-500, interest_rate_change_bps=300,
                       receivable_days_increase=12, inventory_days_increase=7,
                       working_capital_outflow_pct_revenue=0.025),
    ScenarioDefinition(id="liquidity", name="Liquidity shock", revenue_change=-0.05,
                       ebitda_margin_change_bps=-100, interest_rate_change_bps=100,
                       receivable_days_increase=20, inventory_days_increase=10,
                       working_capital_outflow_pct_revenue=0.0125),
    ScenarioDefinition(id="combined", name="Combined stress", revenue_change=-0.25,
                       ebitda_margin_change_bps=-600, interest_rate_change_bps=400,
                       receivable_days_increase=25, inventory_days_increase=15,
                       working_capital_outflow_pct_revenue=0.035),
]


def get_scenario(scenario_id: str) -> ScenarioDefinition:
    for scenario in DEFAULT_SCENARIOS:
        if scenario.id == scenario_id:
            return scenario
    raise KeyError(f"Unknown scenario '{scenario_id}'")


def apply_scenario(
    periods: list[FinancialPeriod], loan: LoanConfig, scenario: ScenarioDefinition,
) -> tuple[list[FinancialPeriod], LoanConfig]:
    shocked: list[FinancialPeriod] = []
    cumulative_cash_effect = 0.0
    for period in periods:
        if period.period_type.value == "historical" or scenario.id == "base":
            shocked.append(deepcopy(period))
            continue
        base_margin = period.ebitda / period.revenue if period.revenue else 0
        revenue = period.revenue * (1 + scenario.revenue_change)
        margin = base_margin + scenario.ebitda_margin_change_bps / 10_000
        ebitda = revenue * margin
        depreciation = period.ebitda - period.ebit
        ebit = ebitda - depreciation
        interest = period.interest_expense + period.total_debt * scenario.interest_rate_change_bps / 10_000
        pretax = ebit - interest
        implied_tax_rate = period.taxes / max(period.ebit - period.interest_expense, 0.01)
        taxes = max(pretax, 0) * min(max(implied_tax_rate, 0), 0.35)
        net_income = pretax - taxes
        base_ar_days = period.accounts_receivable / period.revenue * 365 if period.revenue else 0
        base_inventory_days = period.inventory / period.revenue * 365 if period.revenue else 0
        ar = revenue * (base_ar_days + scenario.receivable_days_increase) / 365
        inv_days = base_inventory_days + (scenario.inventory_days_increase if period.inventory > 0 else 0)
        inventory = revenue * inv_days / 365
        incremental_wc = max(ar - period.accounts_receivable, 0) + max(inventory - period.inventory, 0)
        incremental_wc += revenue * scenario.working_capital_outflow_pct_revenue
        ebitda_delta = ebitda - period.ebitda
        ocf = period.operating_cash_flow + ebitda_delta - incremental_wc
        capex = period.capital_expenditure * (1 + scenario.revenue_change * 0.5)
        fcf = ocf - capex
        cumulative_cash_effect += min(fcf - period.free_cash_flow, 0)
        cash = max(period.cash + cumulative_cash_effect, 0)
        other_current_assets = max(period.current_assets - period.cash - period.accounts_receivable - period.inventory, 0)
        current_assets = cash + ar + inventory + other_current_assets
        current_liabilities = period.current_liabilities + revenue * scenario.working_capital_outflow_pct_revenue * 0.35
        shocked.append(period.model_copy(update={
            "revenue": r(revenue), "ebitda": r(ebitda), "ebit": r(ebit),
            "interest_expense": r(interest), "taxes": r(taxes), "net_income": r(net_income),
            "cash": r(cash), "accounts_receivable": r(ar), "inventory": r(inventory),
            "current_assets": r(current_assets), "current_liabilities": r(current_liabilities),
            "operating_cash_flow": r(ocf), "capital_expenditure": r(capex), "free_cash_flow": r(fcf),
        }))
    stressed_loan = loan.model_copy(update={
        "annual_interest_rate": min(loan.annual_interest_rate + scenario.interest_rate_change_bps / 10_000, 0.5)
    })
    return shocked, stressed_loan
