from __future__ import annotations

from app.models.domain import (
    ConsolidatedDebtScheduleRow, DebtScheduleRow, DebtStructureConfig, DebtTrancheType,
    FinancialPeriod, LoanConfig, TrancheScheduleRow,
)
from app.services.financial_engine import r


def build_debt_schedule(periods: list[FinancialPeriod], loan: LoanConfig) -> list[DebtScheduleRow]:
    """Build an annual schedule for projected periods.

    Existing debt is reduced by the refinanced amount at close. The new term loan is
    borrowed in the first projection year. Contractual amortization is based on original
    principal. A 25% excess-cash-flow sweep is applied when FCF exceeds contractual
    amortization and minimum cash is satisfied.
    """
    projected = [p for p in periods if p.period_type.value == "projected"]
    if not projected:
        return []
    legacy_debt = max(periods[2].total_debt - loan.existing_debt_refinanced_amount, 0)
    opening = legacy_debt
    annual_amort = loan.new_loan_amount * loan.amortization_percentage
    fee_amortization = loan.upfront_fees / loan.loan_term_years
    rows: list[DebtScheduleRow] = []
    for index, period in enumerate(projected):
        borrowing = loan.new_loan_amount if index == 0 else 0.0
        available = opening + borrowing
        mandatory = min(annual_amort + period.mandatory_debt_amortization, available)
        excess_cash = max(period.free_cash_flow - mandatory, 0)
        cash_above_minimum = max(period.cash - loan.minimum_cash_requirement, 0)
        optional = min(excess_cash * 0.25, cash_above_minimum, available - mandatory)
        closing = max(available - mandatory - optional, 0)
        average_balance = (available + closing) / 2
        cash_interest = average_balance * loan.annual_interest_rate
        effective_interest = cash_interest + fee_amortization
        rows.append(DebtScheduleRow(
            fiscal_year=period.fiscal_year, opening_balance=r(opening), new_borrowing=r(borrowing),
            mandatory_amortization=r(mandatory), optional_repayment=r(optional),
            closing_balance=r(closing), cash_interest=r(cash_interest),
            effective_interest=r(effective_interest),
        ))
        opening = closing
    return rows


def _opening_balance(tranche) -> float:
    if tranche.tranche_type == DebtTrancheType.REVOLVER and tranche.drawn_amount > 0:
        return tranche.drawn_amount
    return tranche.opening_balance


def _period_rank(label: str) -> tuple[int, int]:
    digits = "".join(ch for ch in label if ch.isdigit())
    year = int(digits[:4]) if len(digits) >= 4 else 0
    quarter = int(label.split("Q")[-1]) if "Q" in label else 4
    return year, quarter


def build_multi_tranche_schedule(
    period_labels: list[str], cash_by_period: dict[str, float], fcf_by_period: dict[str, float],
    structure: DebtStructureConfig, periods_per_year: int = 1,
) -> tuple[list[ConsolidatedDebtScheduleRow], dict[str, list[TrancheScheduleRow]]]:
    """Roll a deterministic multi-tranche debt structure through annual or quarterly periods."""
    balances = {tranche.id: _opening_balance(tranche) for tranche in structure.tranches}
    tranche_schedules: dict[str, list[TrancheScheduleRow]] = {
        tranche.id: [] for tranche in structure.tranches
    }
    consolidated: list[ConsolidatedDebtScheduleRow] = []
    period_fraction = 1 / periods_per_year
    priority = {
        DebtTrancheType.REVOLVER: 0,
        DebtTrancheType.SENIOR_SECURED: 1,
        DebtTrancheType.SUBORDINATED: 2,
    }
    for index, label in enumerate(period_labels):
        provisional: dict[str, dict[str, float]] = {}
        total_mandatory = 0.0
        total_cash_interest = 0.0
        for tranche in structure.tranches:
            opening = balances[tranche.id]
            borrowing = tranche.new_borrowing if index == 0 else 0.0
            refinancing = min(tranche.refinancing_amount if index == 0 else 0.0, opening)
            pre_amort_balance = max(opening - refinancing + borrowing, 0)
            scheduled_amort = pre_amort_balance * tranche.amortization_percentage * period_fraction
            if _period_rank(label) >= _period_rank(tranche.maturity_period):
                scheduled_amort = pre_amort_balance
            mandatory = min(scheduled_amort, pre_amort_balance)
            post_mandatory = pre_amort_balance - mandatory
            pik = post_mandatory * tranche.interest_rate * period_fraction if tranche.pik_interest else 0.0
            average_cash_balance = (pre_amort_balance + post_mandatory) / 2
            cash_interest = (
                average_cash_balance * tranche.interest_rate * period_fraction
                if tranche.cash_pay_interest else 0.0
            )
            provisional[tranche.id] = {
                "opening": opening, "borrowing": borrowing, "refinancing": refinancing,
                "mandatory": mandatory, "post_mandatory": post_mandatory,
                "pik": pik, "cash_interest": cash_interest,
                "average_cash_balance": average_cash_balance if tranche.cash_pay_interest else 0.0,
            }
            total_mandatory += mandatory
            total_cash_interest += cash_interest
        excess_fcf = max(fcf_by_period.get(label, 0) - total_mandatory - total_cash_interest, 0)
        cash_cushion = max(cash_by_period.get(label, 0) - structure.minimum_cash_requirement, 0)
        sweep = min(
            excess_fcf * structure.excess_cash_flow_sweep_percentage,
            cash_cushion,
            sum(item["post_mandatory"] + item["pik"] for item in provisional.values()),
        )
        optional_by_tranche = {tranche.id: 0.0 for tranche in structure.tranches}
        remaining_sweep = sweep
        for tranche in sorted(structure.tranches, key=lambda item: priority[item.tranche_type]):
            available = provisional[tranche.id]["post_mandatory"] + provisional[tranche.id]["pik"]
            repayment = min(available, remaining_sweep)
            optional_by_tranche[tranche.id] = repayment
            remaining_sweep -= repayment
        period_rows: list[TrancheScheduleRow] = []
        rate_numerator = 0.0
        rate_denominator = 0.0
        for tranche in structure.tranches:
            item = provisional[tranche.id]
            optional = optional_by_tranche[tranche.id]
            closing = max(item["post_mandatory"] + item["pik"] - optional, 0)
            undrawn = (
                max(tranche.commitment_amount - closing, 0)
                if tranche.tranche_type == DebtTrancheType.REVOLVER else 0.0
            )
            commitment_fee = (
                undrawn * tranche.commitment_fee * period_fraction
                if tranche.tranche_type == DebtTrancheType.REVOLVER else 0.0
            )
            row = TrancheScheduleRow(
                period=label, tranche_id=tranche.id, tranche_name=tranche.name,
                tranche_type=tranche.tranche_type, opening_balance=r(item["opening"]),
                new_borrowing=r(item["borrowing"]), refinancing=r(item["refinancing"]),
                mandatory_amortization=r(item["mandatory"]), optional_repayment=r(optional),
                pik_accrual=r(item["pik"]), closing_balance=r(closing),
                cash_interest=r(item["cash_interest"]), commitment_fee=r(commitment_fee),
                undrawn_amount=r(undrawn),
            )
            period_rows.append(row)
            tranche_schedules[tranche.id].append(row)
            balances[tranche.id] = closing
            rate_numerator += item["average_cash_balance"] * tranche.interest_rate
            rate_denominator += item["average_cash_balance"]
        revolver_availability = sum(row.undrawn_amount for row in period_rows)
        commitment_fees = sum(row.commitment_fee for row in period_rows)
        consolidated.append(ConsolidatedDebtScheduleRow(
            period=label,
            opening_balance=r(sum(row.opening_balance for row in period_rows)),
            new_borrowing=r(sum(row.new_borrowing for row in period_rows)),
            refinancing=r(sum(row.refinancing for row in period_rows)),
            mandatory_amortization=r(sum(row.mandatory_amortization for row in period_rows)),
            optional_repayment=r(sum(row.optional_repayment for row in period_rows)),
            pik_accrual=r(sum(row.pik_accrual for row in period_rows)),
            closing_balance=r(sum(row.closing_balance for row in period_rows)),
            cash_interest=r(sum(row.cash_interest for row in period_rows)),
            commitment_fees=r(commitment_fees),
            total_cash_interest=r(sum(row.cash_interest for row in period_rows) + commitment_fees),
            weighted_average_cash_interest_rate=(
                None if rate_denominator == 0 else r(rate_numerator / rate_denominator)
            ),
            revolver_availability=r(revolver_availability),
            total_liquidity=r(cash_by_period.get(label, 0) + revolver_availability),
        ))
    return consolidated, tranche_schedules


def build_annual_multi_tranche_schedule(
    periods: list[FinancialPeriod], structure: DebtStructureConfig,
) -> tuple[list[ConsolidatedDebtScheduleRow], dict[str, list[TrancheScheduleRow]]]:
    projected = [period for period in periods if period.period_type.value == "projected"]
    return build_multi_tranche_schedule(
        [period.fiscal_year for period in projected],
        {period.fiscal_year: period.cash for period in projected},
        {period.fiscal_year: period.free_cash_flow for period in projected},
        structure,
    )
