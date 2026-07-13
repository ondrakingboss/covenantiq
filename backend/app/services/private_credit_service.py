from __future__ import annotations

from app.models.domain import (
    LoanConfig, MultiScenarioResult, PrivateCreditAnalysisRequest, PrivateCreditAnalysisResponse,
    QuarterlyScenarioResult,
)
from app.services.analysis_service import DEFAULT_COVENANTS
from app.services.audit_engine import build_audit_trail
from app.services.covenant_engine import evaluate_covenants, first_breach
from app.services.debt_engine import build_annual_multi_tranche_schedule
from app.services.financial_engine import get_borrower
from app.services.quarterly_engine import build_quarterly_projection, quarterly_periods_for_covenants
from app.services.ratio_engine import calculate_consolidated_ratios, calculate_quarterly_ratios
from app.services.recommendation_engine import recommend_private_credit
from app.services.scenario_engine import apply_scenario, get_scenario


PRIVATE_CREDIT_ASSUMPTIONS = [
    "Each tranche is modeled independently and consolidated after tranche-level roll-forward.",
    "Refinancing reduces the specified tranche opening balance at close; new borrowing funds in the first projected period.",
    "Cash interest uses average balance. PIK accrues to principal. Revolver commitment fees apply to ending undrawn capacity.",
    "Excess-cash-flow sweep capacity is allocated to revolver, then senior secured debt, then subordinated debt.",
    "Quarterly FY2026E and FY2027E projections phase annual values using documented borrower-specific seasonal weights.",
    "Quarterly leverage uses quarter-end debt and annual EBITDA proxy; quarterly coverage and DSCR annualize the quarter run rate.",
    "No borrowing-base, intra-quarter draw, hedging, tax shield, or legal covenant-document mechanics are modeled.",
]


def _scenario_loan(request: PrivateCreditAnalysisRequest) -> LoanConfig:
    total_new = sum(tranche.new_borrowing for tranche in request.debt_structure.tranches)
    weighted_rate_numerator = sum(
        tranche.interest_rate * max(tranche.opening_balance + tranche.new_borrowing, 0)
        for tranche in request.debt_structure.tranches
    )
    weighted_rate_denominator = sum(
        max(tranche.opening_balance + tranche.new_borrowing, 0)
        for tranche in request.debt_structure.tranches
    )
    return LoanConfig(
        new_loan_amount=max(total_new, 0.01),
        annual_interest_rate=(weighted_rate_numerator / weighted_rate_denominator
                              if weighted_rate_denominator else 0),
        loan_term_years=5, amortization_percentage=0, upfront_fees=0,
        minimum_cash_requirement=request.debt_structure.minimum_cash_requirement,
        existing_debt_refinanced_amount=0,
        revolving_credit_commitment=sum(
            tranche.commitment_amount for tranche in request.debt_structure.tranches
            if tranche.tranche_type.value == "revolver"
        ),
    )


def _stressed_structure(request: PrivateCreditAnalysisRequest, rate_bps: int):
    return request.debt_structure.model_copy(update={
        "tranches": [
            tranche.model_copy(update={
                "interest_rate": min(tranche.interest_rate + rate_bps / 10_000, 0.5)
            }) for tranche in request.debt_structure.tranches
        ]
    })


def analyze_private_credit(request: PrivateCreditAnalysisRequest) -> PrivateCreditAnalysisResponse:
    borrower = get_borrower(request.borrower_id)
    covenants = request.covenants or DEFAULT_COVENANTS
    scenario_ids = list(dict.fromkeys(["base", *request.scenario_ids]))
    annual_results: list[MultiScenarioResult] = []
    quarterly_results: list[QuarterlyScenarioResult] = []
    scenario_loan = _scenario_loan(request)
    for scenario_id in scenario_ids:
        scenario = get_scenario(scenario_id)
        periods, _ = apply_scenario(borrower.periods, scenario_loan, scenario)
        structure = _stressed_structure(request, scenario.interest_rate_change_bps)
        annual_schedule, annual_tranches = build_annual_multi_tranche_schedule(periods, structure)
        annual_ratios = calculate_consolidated_ratios(periods, annual_schedule)
        annual_covenants = evaluate_covenants(covenants, periods, annual_ratios, scenario.name)
        annual_results.append(MultiScenarioResult(
            scenario=scenario, periods=periods, consolidated_debt_schedule=annual_schedule,
            tranche_schedules=annual_tranches, ratios=annual_ratios,
            covenant_results=annual_covenants, first_breach_period=first_breach(annual_covenants),
        ))
        quarters, quarter_schedule, quarter_tranches = build_quarterly_projection(
            request.borrower_id, periods, structure
        )
        quarter_ratios = calculate_quarterly_ratios(quarters, periods)
        covenant_periods = quarterly_periods_for_covenants(quarters, periods)
        quarter_covenants = evaluate_covenants(
            covenants, covenant_periods, quarter_ratios, scenario.name
        )
        quarterly_results.append(QuarterlyScenarioResult(
            scenario=scenario, periods=quarters, consolidated_debt_schedule=quarter_schedule,
            tranche_schedules=quarter_tranches, ratios=quarter_ratios,
            covenant_results=quarter_covenants,
            first_breach_period=first_breach(quarter_covenants),
        ))
    recommendation = recommend_private_credit(
        annual_results, quarterly_results, request.debt_structure.minimum_cash_requirement
    )
    audit_trail = build_audit_trail(
        annual_results, quarterly_results, recommendation,
        request.debt_structure.minimum_cash_requirement,
    )
    return PrivateCreditAnalysisResponse(
        borrower=borrower, debt_structure=request.debt_structure,
        annual_scenarios=annual_results, quarterly_scenarios=quarterly_results,
        recommendation=recommendation,
        sources_uses=request.sources_uses, assumptions=PRIVATE_CREDIT_ASSUMPTIONS,
        audit_trail=audit_trail,
    )
