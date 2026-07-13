from app.models.domain import CovenantDefinition, CovenantType
from app.services.covenant_engine import evaluate_covenants, first_breach
from app.services.ratio_engine import calculate_period_ratios


def _ratios(period, loan):
    return {period.fiscal_year: calculate_period_ratios(period, None, loan)}


def test_maximum_covenant_headroom(period, loan):
    c = CovenantDefinition(name="Max leverage", covenant_type=CovenantType.MAX_GROSS_LEVERAGE, threshold=3.5)
    result = evaluate_covenants([c], [period], _ratios(period, loan), "Base")[0]
    assert result.status == "pass"
    assert result.absolute_headroom == 0.5
    assert result.percentage_headroom == 0.14


def test_minimum_covenant_headroom(period, loan):
    c = CovenantDefinition(name="Min coverage", covenant_type=CovenantType.MIN_INTEREST_COVERAGE, threshold=4.0)
    result = evaluate_covenants([c], [period], _ratios(period, loan), "Base")[0]
    assert result.status == "pass"
    assert result.absolute_headroom == 1.0
    assert result.percentage_headroom == 0.25


def test_first_breach_detection_is_chronological(period, loan):
    periods = [period.model_copy(update={"fiscal_year": f"FY202{i}E", "ebitda": e}) for i, e in [(6, 40), (7, 20), (8, 30)]]
    ratios = {p.fiscal_year: calculate_period_ratios(p, None, loan) for p in periods}
    c = CovenantDefinition(name="Max leverage", covenant_type=CovenantType.MAX_GROSS_LEVERAGE, threshold=4.0)
    results = evaluate_covenants([c], periods, ratios, "Downside")
    assert results[1].status == "fail"
    assert all(r.first_breach_period == "FY2027E" for r in results)
    assert first_breach(results) == "FY2027E"
