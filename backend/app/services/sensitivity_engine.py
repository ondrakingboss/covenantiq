from __future__ import annotations

from app.models.domain import (
    ScenarioDefinition, SensitivityCell, SensitivityRequest, SensitivityResponse,
)
from app.services.analysis_service import DEFAULT_COVENANTS
from app.services.covenant_engine import evaluate_covenants, first_breach
from app.services.debt_engine import build_annual_multi_tranche_schedule
from app.services.financial_engine import get_borrower
from app.services.private_credit_service import _scenario_loan
from app.services.quarterly_engine import build_quarterly_projection, quarterly_periods_for_covenants
from app.services.ratio_engine import calculate_consolidated_ratios, calculate_quarterly_ratios
from app.services.scenario_engine import apply_scenario


def run_sensitivity(request: SensitivityRequest) -> SensitivityResponse:
    borrower = get_borrower(request.borrower_id)
    covenants = request.covenants or DEFAULT_COVENANTS
    from app.models.domain import PrivateCreditAnalysisRequest
    scenario_loan = _scenario_loan(PrivateCreditAnalysisRequest(
        borrower_id=request.borrower_id, debt_structure=request.debt_structure,
        covenants=request.covenants, scenario_ids=["base"],
    ))
    cells: list[SensitivityCell] = []
    for revenue_shock in request.revenue_shocks:
        for margin_shock in request.margin_shocks_bps:
            scenario = ScenarioDefinition(
                id=f"sensitivity-{revenue_shock}-{margin_shock}", name="Sensitivity",
                revenue_change=revenue_shock, ebitda_margin_change_bps=margin_shock,
                interest_rate_change_bps=0,
            )
            periods, _ = apply_scenario(borrower.periods, scenario_loan, scenario)
            annual_schedule, _ = build_annual_multi_tranche_schedule(
                periods, request.debt_structure
            )
            ratios = calculate_consolidated_ratios(periods, annual_schedule)
            first_year = annual_schedule[0].period
            quarters, _, _ = build_quarterly_projection(
                request.borrower_id, periods, request.debt_structure
            )
            quarter_ratios = calculate_quarterly_ratios(quarters, periods)
            quarter_covenants = evaluate_covenants(
                covenants, quarterly_periods_for_covenants(quarters, periods),
                quarter_ratios, "Sensitivity",
            )
            statuses = {result.status for result in quarter_covenants}
            covenant_status = (
                "fail" if "fail" in statuses else "not_tested" if "not_tested" in statuses else "pass"
            )
            first_metrics = ratios[first_year]
            cells.append(SensitivityCell(
                revenue_shock=revenue_shock, margin_shock_bps=margin_shock,
                net_leverage=first_metrics["net_leverage"].value,
                interest_coverage=first_metrics["interest_coverage"].value,
                dscr=first_metrics["dscr"].value,
                minimum_liquidity=first_metrics["minimum_liquidity"].value,
                covenant_status=covenant_status,
                first_breach_period=first_breach(quarter_covenants),
            ))
    return SensitivityResponse(
        borrower_id=request.borrower_id, revenue_shocks=request.revenue_shocks,
        margin_shocks_bps=request.margin_shocks_bps, cells=cells,
    )
