from app.models.domain import (
    CovenantDefinition, CovenantType, PrivateCreditAnalysisRequest, SensitivityRequest,
)
from app.services.financial_engine import get_borrower
from app.services.private_credit_service import analyze_private_credit
from app.services.quarterly_engine import build_quarterly_projection
from app.services.sensitivity_engine import run_sensitivity


def test_seasonal_quarterly_projection_reconciles_and_phases_retail(debt_structure):
    borrower = get_borrower("meridian-retail")
    quarters, _, _ = build_quarterly_projection(
        borrower.id, borrower.periods, debt_structure
    )
    fy2026 = quarters[:4]
    assert round(sum(item.revenue for item in fy2026), 2) == borrower.periods[3].revenue
    assert fy2026[3].revenue > fy2026[0].revenue
    assert fy2026[3].operating_cash_flow > fy2026[0].operating_cash_flow


def test_quarterly_covenants_find_quarter_breach(debt_structure):
    covenants = [
        CovenantDefinition(name="Maximum leverage", covenant_type=CovenantType.MAX_GROSS_LEVERAGE, threshold=4.5),
        CovenantDefinition(name="Minimum coverage", covenant_type=CovenantType.MIN_INTEREST_COVERAGE, threshold=2.0),
    ]
    result = analyze_private_credit(PrivateCreditAnalysisRequest(
        borrower_id="ironbridge-components", debt_structure=debt_structure,
        covenants=covenants, scenario_ids=["base", "severe"],
    ))
    base = next(item for item in result.quarterly_scenarios if item.scenario.id == "base")
    assert base.first_breach_period == "FY2026Q1"
    assert all(item.first_breach_period == "FY2026Q1" for item in base.covenant_results)


def test_sensitivity_grid_dimensions_and_worsening(debt_structure):
    response = run_sensitivity(SensitivityRequest(
        borrower_id="vantage-services", debt_structure=debt_structure,
    ))
    assert len(response.revenue_shocks) == 7
    assert len(response.margin_shocks_bps) == 6
    assert len(response.cells) == 42
    base = next(c for c in response.cells if c.revenue_shock == 0 and c.margin_shock_bps == 0)
    severe = next(c for c in response.cells if c.revenue_shock == -0.30 and c.margin_shock_bps == -700)
    assert base.net_leverage is not None and severe.net_leverage is not None
    assert severe.net_leverage > base.net_leverage
    assert severe.interest_coverage < base.interest_coverage
    assert {cell.covenant_status for cell in response.cells} >= {"pass", "fail"}
