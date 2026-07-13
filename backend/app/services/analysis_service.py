from __future__ import annotations

from app.models.domain import (
    AnalysisRequest, AnalysisResponse, CovenantDefinition, CovenantType, ScenarioResult,
)
from app.services.covenant_engine import evaluate_covenants, first_breach
from app.services.debt_engine import build_debt_schedule
from app.services.financial_engine import get_borrower
from app.services.ratio_engine import calculate_ratios
from app.services.recommendation_engine import recommend
from app.services.scenario_engine import apply_scenario, get_scenario


DEFAULT_COVENANTS = [
    CovenantDefinition(name="Maximum gross leverage", covenant_type=CovenantType.MAX_GROSS_LEVERAGE, threshold=4.5),
    CovenantDefinition(name="Minimum interest coverage", covenant_type=CovenantType.MIN_INTEREST_COVERAGE, threshold=2.0),
    CovenantDefinition(name="Minimum DSCR", covenant_type=CovenantType.MIN_DSCR, threshold=1.15),
    CovenantDefinition(name="Minimum liquidity", covenant_type=CovenantType.MIN_LIQUIDITY, threshold=15.0),
]

ASSUMPTIONS = [
    "All monetary values are USD millions and annual periods are fiscal years.",
    "New term debt funds in the first projected year; refinanced debt is removed at close.",
    "Contractual amortization equals the configured percentage of original principal plus existing mandatory amortization.",
    "A 25% excess-cash-flow sweep is applied when modeled FCF and cash exceed contractual requirements.",
    "Cash interest uses average annual debt balance; upfront fees are amortized straight-line for effective interest.",
    "CFADS equals operating cash flow plus cash interest less capital expenditure.",
    "Annual lease fixed charge is approximated as 15% of reported lease liabilities.",
    "Scenario shocks are applied to projected statements, working capital, cash flow, liquidity, debt, and interest before ratios are calculated.",
]


def analyze(request: AnalysisRequest) -> AnalysisResponse:
    borrower = get_borrower(request.borrower_id)
    covenants = request.covenants or DEFAULT_COVENANTS
    scenario_ids = list(dict.fromkeys(["base", *request.scenario_ids]))
    scenarios: list[ScenarioResult] = []
    for scenario_id in scenario_ids:
        definition = get_scenario(scenario_id)
        periods, stressed_loan = apply_scenario(borrower.periods, request.loan, definition)
        schedule = build_debt_schedule(periods, stressed_loan)
        ratios = calculate_ratios(periods, schedule, stressed_loan)
        covenant_results = evaluate_covenants(covenants, periods, ratios, definition.name)
        scenarios.append(ScenarioResult(
            scenario=definition, periods=periods, debt_schedule=schedule, ratios=ratios,
            covenant_results=covenant_results, first_breach_period=first_breach(covenant_results),
        ))
    return AnalysisResponse(
        borrower=borrower, loan=request.loan, scenarios=scenarios,
        recommendation=recommend(scenarios, request.loan.minimum_cash_requirement),
        assumptions=ASSUMPTIONS,
    )
