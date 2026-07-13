from app.models.domain import (
    PrivateCreditAnalysisRequest, SavedAnalysisCreate, SensitivityRequest,
)
from app.services.memo_engine import generate_private_credit_memo_html
from app.services.persistence import create_saved_analysis, delete_saved_analysis, get_saved_analysis
from app.services.private_credit_service import analyze_private_credit
from app.services.sensitivity_engine import run_sensitivity


def test_saved_analysis_create_read_delete(tmp_path, monkeypatch, debt_structure):
    monkeypatch.setenv("COVENANTIQ_DB_PATH", str(tmp_path / "test.db"))
    saved = create_saved_analysis(SavedAnalysisCreate(
        analysis_name="Committee case", borrower_id="vantage-services",
        debt_structure=debt_structure, scenario_ids=["base", "mild"],
    ))
    reopened = get_saved_analysis(saved.id)
    assert reopened.analysis.recommendation == saved.analysis.recommendation
    saved_base = reopened.analysis.annual_scenarios[0].ratios["FY2026E"]["net_leverage"].value
    original_base = saved.analysis.annual_scenarios[0].ratios["FY2026E"]["net_leverage"].value
    assert saved_base == original_base
    assert delete_saved_analysis(saved.id) is True


def test_investment_committee_memo_has_required_sections(debt_structure):
    request = PrivateCreditAnalysisRequest(
        borrower_id="vantage-services", debt_structure=debt_structure,
        scenario_ids=["base", "severe"],
    )
    analysis = analyze_private_credit(request)
    sensitivity = run_sensitivity(SensitivityRequest(
        borrower_id=request.borrower_id, debt_structure=debt_structure,
    ))
    html = generate_private_credit_memo_html(analysis, sensitivity, "Test Desk")
    for heading in [
        "Executive recommendation", "Sources and uses", "Debt structure",
        "Covenant package", "Sensitivity analysis summary",
        "Proposed conditions precedent", "Monitoring recommendations",
        "Methodology and limitations disclaimer",
    ]:
        assert heading in html
