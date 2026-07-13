from app.models.domain import AnalysisRequest, CovenantDefinition, CovenantType, LoanConfig
from app.services.analysis_service import analyze
from app.services.financial_engine import get_borrower
from app.services.scenario_engine import apply_scenario, get_scenario


def loan(amount=100, refinance=100):
    return LoanConfig(
        new_loan_amount=amount, annual_interest_rate=0.08, loan_term_years=5,
        amortization_percentage=0.05, upfront_fees=2, minimum_cash_requirement=10,
        existing_debt_refinanced_amount=refinance, revolving_credit_commitment=15,
    )


def test_scenario_revenue_and_margin_shocks():
    borrower = get_borrower("alder-manufacturing")
    severe = get_scenario("severe")
    periods, stressed_loan = apply_scenario(borrower.periods, loan(), severe)
    base = borrower.periods[3]
    shocked = periods[3]
    assert shocked.revenue == round(base.revenue * 0.8, 2)
    assert shocked.ebitda == round(shocked.revenue * (base.ebitda / base.revenue - 0.05), 2)
    assert stressed_loan.annual_interest_rate == 0.11
    assert shocked.operating_cash_flow < base.operating_cash_flow


def test_recommendation_logic_supports_strong_borrower():
    result = analyze(AnalysisRequest(
        borrower_id="vantage-services", loan=loan(80, 120), scenario_ids=["base", "mild", "severe"]
    ))
    assert result.recommendation.recommendation in {"Approve", "Approve with conditions"}
    assert result.recommendation.risk_grade in {"3", "4"}


def test_ironbridge_end_to_end_breaches_downside():
    covenants = [
        CovenantDefinition(name="Max leverage", covenant_type=CovenantType.MAX_GROSS_LEVERAGE, threshold=4.5),
        CovenantDefinition(name="Min coverage", covenant_type=CovenantType.MIN_INTEREST_COVERAGE, threshold=2.0),
        CovenantDefinition(name="Min liquidity", covenant_type=CovenantType.MIN_LIQUIDITY, threshold=15),
    ]
    result = analyze(AnalysisRequest(
        borrower_id="ironbridge-components", loan=loan(120, 80), covenants=covenants,
        scenario_ids=["base", "mild", "severe"],
    ))
    severe = next(s for s in result.scenarios if s.scenario.id == "severe")
    assert severe.first_breach_period is not None
    assert any(item.status == "fail" for item in severe.covenant_results)
    assert result.recommendation.recommendation in {"Further diligence required", "Decline"}
