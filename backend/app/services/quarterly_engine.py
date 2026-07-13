from __future__ import annotations

from app.models.domain import (
    DebtStructureConfig, FinancialPeriod, PeriodType, QuarterlyFinancialPeriod,
)
from app.services.debt_engine import build_multi_tranche_schedule
from app.services.financial_engine import r


DEFAULT_REVENUE_WEIGHTS = [0.24, 0.25, 0.25, 0.26]
SEASONALITY = {
    "meridian-retail": {
        "revenue": [0.21, 0.22, 0.24, 0.33],
        "ebitda": [0.17, 0.20, 0.23, 0.40],
        "ocf": [-0.08, 0.12, 0.24, 0.72],
        "capex": [0.22, 0.23, 0.25, 0.30],
    },
    "alder-manufacturing": {
        "revenue": [0.23, 0.24, 0.25, 0.28],
        "ebitda": [0.21, 0.23, 0.25, 0.31],
        "ocf": [0.12, 0.21, 0.27, 0.40],
        "capex": [0.20, 0.23, 0.27, 0.30],
    },
}


def seasonality_for(borrower_id: str) -> dict[str, list[float]]:
    return SEASONALITY.get(borrower_id, {
        "revenue": DEFAULT_REVENUE_WEIGHTS,
        "ebitda": DEFAULT_REVENUE_WEIGHTS,
        "ocf": [0.18, 0.23, 0.27, 0.32],
        "capex": [0.22, 0.24, 0.26, 0.28],
    })


def build_quarterly_projection(
    borrower_id: str, annual_periods: list[FinancialPeriod], structure: DebtStructureConfig,
) -> tuple[list[QuarterlyFinancialPeriod], list, dict]:
    annual_projected = [p for p in annual_periods if p.period_type == PeriodType.PROJECTED][:2]
    weights = seasonality_for(borrower_id)
    phased: list[dict[str, float | str]] = []
    for annual in annual_projected:
        year = annual.fiscal_year[:6]
        for quarter_index in range(4):
            label = f"{year}Q{quarter_index + 1}"
            revenue = annual.revenue * weights["revenue"][quarter_index]
            ebitda = annual.ebitda * weights["ebitda"][quarter_index]
            ocf = annual.operating_cash_flow * weights["ocf"][quarter_index]
            capex = annual.capital_expenditure * weights["capex"][quarter_index]
            phased.append({
                "period": label, "fiscal_year": annual.fiscal_year,
                "revenue": revenue, "ebitda": ebitda, "operating_cash_flow": ocf,
                "capital_expenditure": capex, "free_cash_flow": ocf - capex,
            })
    labels = [str(item["period"]) for item in phased]
    starting_cash = next(
        period.cash for period in reversed(annual_periods)
        if period.period_type == PeriodType.HISTORICAL
    )
    provisional_cash: dict[str, float] = {}
    running_cash = starting_cash
    for item in phased:
        running_cash = max(running_cash + float(item["free_cash_flow"]), 0)
        provisional_cash[str(item["period"])] = running_cash
    schedule, tranche_schedules = build_multi_tranche_schedule(
        labels, provisional_cash,
        {str(item["period"]): float(item["free_cash_flow"]) for item in phased},
        structure, periods_per_year=4,
    )
    debt_by_period = {row.period: row for row in schedule}
    quarters: list[QuarterlyFinancialPeriod] = []
    running_cash = starting_cash
    for item in phased:
        label = str(item["period"])
        debt = debt_by_period[label]
        running_cash = max(
            running_cash + float(item["free_cash_flow"]) - debt.total_cash_interest
            - debt.mandatory_amortization - debt.optional_repayment,
            0,
        )
        debt.total_liquidity = r(running_cash + debt.revolver_availability)
        quarters.append(QuarterlyFinancialPeriod(
            period=label, fiscal_year=str(item["fiscal_year"]), revenue=r(float(item["revenue"])),
            ebitda=r(float(item["ebitda"])), cash_interest=debt.total_cash_interest,
            capital_expenditure=r(float(item["capital_expenditure"])),
            operating_cash_flow=r(float(item["operating_cash_flow"])),
            free_cash_flow=r(float(item["free_cash_flow"])), ending_cash=r(running_cash),
            total_debt=debt.closing_balance, net_debt=r(debt.closing_balance - running_cash),
            mandatory_amortization=debt.mandatory_amortization,
            revolver_availability=debt.revolver_availability, total_liquidity=debt.total_liquidity,
        ))
    return quarters, schedule, tranche_schedules


def quarterly_periods_for_covenants(
    quarters: list[QuarterlyFinancialPeriod], annual_periods: list[FinancialPeriod],
) -> list[FinancialPeriod]:
    annual_by_year = {period.fiscal_year: period for period in annual_periods}
    return [
        FinancialPeriod(
            fiscal_year=quarter.period, period_type=PeriodType.PROJECTED,
            revenue=quarter.revenue, ebitda=quarter.ebitda, ebit=quarter.ebitda,
            interest_expense=quarter.cash_interest, taxes=0,
            net_income=quarter.ebitda - quarter.cash_interest,
            cash=quarter.ending_cash, accounts_receivable=0, inventory=0,
            current_assets=quarter.ending_cash,
            current_liabilities=annual_by_year[quarter.fiscal_year].current_liabilities,
            total_debt=quarter.total_debt,
            lease_liabilities=annual_by_year[quarter.fiscal_year].lease_liabilities,
            operating_cash_flow=quarter.operating_cash_flow,
            capital_expenditure=quarter.capital_expenditure,
            free_cash_flow=quarter.free_cash_flow,
            mandatory_debt_amortization=quarter.mandatory_amortization,
        ) for quarter in quarters
    ]
