from __future__ import annotations

from app.models.domain import (
    ConsolidatedDebtScheduleRow, DebtScheduleRow, FinancialPeriod, LoanConfig, MetricResult,
    MetricStatus, QuarterlyFinancialPeriod,
)
from app.services.financial_engine import r


def metric(
    name: str, value: float | None, status: MetricStatus, formula: str,
    inputs: dict[str, float | None], period: str, interpretation: str,
    limitations: list[str] | None = None,
) -> MetricResult:
    return MetricResult(
        metric=name, value=None if value is None else r(value), status=status, formula=formula,
        inputs={k: None if v is None else r(v) for k, v in inputs.items()}, source_periods=[period],
        interpretation=interpretation, limitations=limitations or [],
    )


def safe_ratio(
    name: str, numerator: float | None, denominator: float | None, formula: str,
    period: str, numerator_name: str, denominator_name: str, positive_denominator: bool = False,
) -> MetricResult:
    inputs = {numerator_name: numerator, denominator_name: denominator}
    if numerator is None or denominator is None:
        return metric(name, None, MetricStatus.UNAVAILABLE, formula, inputs, period,
                      "Required input is unavailable.", ["No ratio was inferred from missing data."])
    if positive_denominator and denominator <= 0:
        return metric(name, None, MetricStatus.NOT_MEANINGFUL, formula, inputs, period,
                      f"{denominator_name} is zero or negative, so this ratio is not meaningful.",
                      ["A numeric zero would be misleading."])
    if denominator == 0:
        return metric(name, None, MetricStatus.NOT_MEANINGFUL, formula, inputs, period,
                      f"{denominator_name} is zero, so this ratio is not meaningful.",
                      ["A numeric infinity is not presented as a finite result."])
    value = numerator / denominator
    return metric(name, value, MetricStatus.VALID, formula, inputs, period,
                  f"Calculated as {r(numerator)} divided by {r(denominator)}.")


def calculate_period_ratios(
    period: FinancialPeriod, debt: DebtScheduleRow | None, loan: LoanConfig,
) -> dict[str, MetricResult]:
    total_debt = debt.closing_balance if debt else period.total_debt
    cash_interest = debt.cash_interest if debt else period.interest_expense
    mandatory = debt.mandatory_amortization if debt else period.mandatory_debt_amortization
    cfads = period.operating_cash_flow + cash_interest - period.capital_expenditure
    debt_service = cash_interest + mandatory
    lease_charge = period.lease_liabilities * 0.15
    fixed_charges = cash_interest + mandatory + lease_charge
    fcf_after_debt_service = period.free_cash_flow - cash_interest - mandatory
    undrawn_revolver = loan.revolving_credit_commitment
    liquidity = period.cash + undrawn_revolver
    return {
        "gross_leverage": safe_ratio("Gross leverage", total_debt, period.ebitda,
            "Total debt / EBITDA", period.fiscal_year, "total_debt", "ebitda", True),
        "net_leverage": safe_ratio("Net leverage", total_debt - period.cash, period.ebitda,
            "(Total debt - cash) / EBITDA", period.fiscal_year, "net_debt", "ebitda", True),
        "interest_coverage": safe_ratio("Interest coverage", period.ebitda, cash_interest,
            "EBITDA / cash interest", period.fiscal_year, "ebitda", "cash_interest", True),
        "dscr": safe_ratio("DSCR", cfads, debt_service,
            "CFADS / (cash interest + mandatory amortization)", period.fiscal_year,
            "cfads", "total_debt_service", True),
        "fixed_charge_coverage": safe_ratio("Fixed-charge coverage",
            period.ebitda - period.capital_expenditure, fixed_charges,
            "(EBITDA - capital expenditure) / (cash interest + mandatory amortization + lease charge)",
            period.fiscal_year, "ebitda_less_capex", "fixed_charges", True),
        "current_ratio": safe_ratio("Current ratio", period.current_assets, period.current_liabilities,
            "Current assets / current liabilities", period.fiscal_year,
            "current_assets", "current_liabilities", True),
        "quick_ratio": safe_ratio("Quick ratio", period.current_assets - period.inventory,
            period.current_liabilities, "(Current assets - inventory) / current liabilities",
            period.fiscal_year, "quick_assets", "current_liabilities", True),
        "minimum_liquidity": metric("Minimum liquidity", liquidity, MetricStatus.VALID,
            "Cash + undrawn revolving commitment", {"cash": period.cash, "undrawn_revolver": undrawn_revolver},
            period.fiscal_year, "Available modeled liquidity before any borrowing-base restrictions.",
            ["Revolver availability is assumed fully undrawn and unrestricted."]),
        "free_cash_flow": metric("Free cash flow", period.free_cash_flow, MetricStatus.VALID,
            "Operating cash flow - capital expenditure",
            {"operating_cash_flow": period.operating_cash_flow, "capital_expenditure": period.capital_expenditure},
            period.fiscal_year, "Negative values indicate cash consumption before debt service."),
        "fcf_after_debt_service": metric("Free cash flow after debt service", fcf_after_debt_service,
            MetricStatus.VALID, "Free cash flow - cash interest - mandatory amortization",
            {"free_cash_flow": period.free_cash_flow, "cash_interest": cash_interest,
             "mandatory_amortization": mandatory}, period.fiscal_year,
            "Residual cash generation after modeled contractual debt service."),
    }


def calculate_ratios(
    periods: list[FinancialPeriod], schedule: list[DebtScheduleRow], loan: LoanConfig,
) -> dict[str, dict[str, MetricResult]]:
    debt_by_year = {row.fiscal_year: row for row in schedule}
    return {
        period.fiscal_year: calculate_period_ratios(period, debt_by_year.get(period.fiscal_year), loan)
        for period in periods
    }


def calculate_consolidated_period_ratios(
    period: FinancialPeriod, debt: ConsolidatedDebtScheduleRow,
) -> dict[str, MetricResult]:
    total_debt = debt.closing_balance
    cash_interest = debt.total_cash_interest
    mandatory = debt.mandatory_amortization
    cfads = period.operating_cash_flow + cash_interest - period.capital_expenditure
    debt_service = cash_interest + mandatory
    lease_charge = period.lease_liabilities * 0.15
    fixed_charges = debt_service + lease_charge
    return {
        "gross_leverage": safe_ratio("Gross leverage", total_debt, period.ebitda,
            "Consolidated debt / EBITDA", period.fiscal_year, "consolidated_debt", "ebitda", True),
        "net_leverage": safe_ratio("Net leverage", total_debt - period.cash, period.ebitda,
            "(Consolidated debt - cash) / EBITDA", period.fiscal_year, "net_debt", "ebitda", True),
        "interest_coverage": safe_ratio("Interest coverage", period.ebitda, cash_interest,
            "EBITDA / consolidated cash interest", period.fiscal_year, "ebitda", "cash_interest", True),
        "dscr": safe_ratio("DSCR", cfads, debt_service,
            "CFADS / consolidated debt service", period.fiscal_year, "cfads", "debt_service", True),
        "fixed_charge_coverage": safe_ratio("Fixed-charge coverage",
            period.ebitda - period.capital_expenditure, fixed_charges,
            "(EBITDA - capex) / (cash interest + amortization + lease charge)",
            period.fiscal_year, "ebitda_less_capex", "fixed_charges", True),
        "current_ratio": safe_ratio("Current ratio", period.current_assets, period.current_liabilities,
            "Current assets / current liabilities", period.fiscal_year,
            "current_assets", "current_liabilities", True),
        "quick_ratio": safe_ratio("Quick ratio", period.current_assets - period.inventory,
            period.current_liabilities, "(Current assets - inventory) / current liabilities",
            period.fiscal_year, "quick_assets", "current_liabilities", True),
        "minimum_liquidity": metric("Minimum liquidity", debt.total_liquidity, MetricStatus.VALID,
            "Cash + revolver availability", {"cash": period.cash,
            "revolver_availability": debt.revolver_availability}, period.fiscal_year,
            "Modeled cash plus undrawn revolving commitment."),
        "free_cash_flow": metric("Free cash flow", period.free_cash_flow, MetricStatus.VALID,
            "Operating cash flow - capital expenditure", {"operating_cash_flow": period.operating_cash_flow,
            "capital_expenditure": period.capital_expenditure}, period.fiscal_year,
            "Negative values indicate cash consumption before debt service."),
        "fcf_after_debt_service": metric("Free cash flow after debt service",
            period.free_cash_flow - cash_interest - mandatory, MetricStatus.VALID,
            "Free cash flow - consolidated cash interest - mandatory amortization",
            {"free_cash_flow": period.free_cash_flow, "cash_interest": cash_interest,
             "mandatory_amortization": mandatory}, period.fiscal_year,
            "Residual cash generation after consolidated contractual debt service."),
    }


def calculate_consolidated_ratios(
    periods: list[FinancialPeriod], schedule: list[ConsolidatedDebtScheduleRow],
) -> dict[str, dict[str, MetricResult]]:
    debt_by_period = {row.period: row for row in schedule}
    return {
        period.fiscal_year: calculate_consolidated_period_ratios(period, debt_by_period[period.fiscal_year])
        for period in periods if period.fiscal_year in debt_by_period
    }


def calculate_quarterly_ratios(
    quarters: list[QuarterlyFinancialPeriod], annual_periods: list[FinancialPeriod],
) -> dict[str, dict[str, MetricResult]]:
    annual_by_year = {period.fiscal_year[:6]: period for period in annual_periods}
    results: dict[str, dict[str, MetricResult]] = {}
    for quarter in quarters:
        annual = annual_by_year[quarter.fiscal_year[:6]]
        cash_interest_run_rate = quarter.cash_interest * 4
        amortization_run_rate = quarter.mandatory_amortization * 4
        cfads_run_rate = quarter.operating_cash_flow * 4 + cash_interest_run_rate - quarter.capital_expenditure * 4
        lease_charge = annual.lease_liabilities * 0.15
        results[quarter.period] = {
            "gross_leverage": safe_ratio("Gross leverage", quarter.total_debt, annual.ebitda,
                "Quarter-end debt / annual EBITDA proxy", quarter.period, "total_debt", "annual_ebitda", True),
            "net_leverage": safe_ratio("Net leverage", quarter.net_debt, annual.ebitda,
                "Quarter-end net debt / annual EBITDA proxy", quarter.period, "net_debt", "annual_ebitda", True),
            "interest_coverage": safe_ratio("Interest coverage", annual.ebitda, cash_interest_run_rate,
                "Annual EBITDA / annualized quarterly cash interest", quarter.period,
                "annual_ebitda", "annualized_cash_interest", True),
            "dscr": safe_ratio("DSCR", cfads_run_rate, cash_interest_run_rate + amortization_run_rate,
                "Annualized quarterly CFADS / annualized quarterly debt service", quarter.period,
                "annualized_cfads", "annualized_debt_service", True),
            "fixed_charge_coverage": safe_ratio("Fixed-charge coverage",
                annual.ebitda - quarter.capital_expenditure * 4,
                cash_interest_run_rate + amortization_run_rate + lease_charge,
                "(Annual EBITDA - annualized capex) / annualized fixed charges", quarter.period,
                "ebitda_less_annualized_capex", "annualized_fixed_charges", True),
            "minimum_liquidity": metric("Minimum liquidity", quarter.total_liquidity, MetricStatus.VALID,
                "Quarter-end cash + revolver availability", {"cash": quarter.ending_cash,
                "revolver_availability": quarter.revolver_availability}, quarter.period,
                "Quarter-end modeled liquidity."),
            "free_cash_flow": metric("Free cash flow", quarter.free_cash_flow, MetricStatus.VALID,
                "Quarterly operating cash flow - quarterly capex", {"operating_cash_flow": quarter.operating_cash_flow,
                "capital_expenditure": quarter.capital_expenditure}, quarter.period,
                "Quarterly cash generation before debt service."),
            "fcf_after_debt_service": metric("Free cash flow after debt service",
                quarter.free_cash_flow - quarter.cash_interest - quarter.mandatory_amortization,
                MetricStatus.VALID, "Quarterly FCF - cash interest - mandatory amortization",
                {"free_cash_flow": quarter.free_cash_flow, "cash_interest": quarter.cash_interest,
                 "mandatory_amortization": quarter.mandatory_amortization}, quarter.period,
                "Quarterly residual cash after debt service."),
        }
    return results
