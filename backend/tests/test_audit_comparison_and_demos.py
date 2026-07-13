from app.models.domain import DebtStructureConfig, SavedAnalysisCreate
from app.services.comparison_engine import compare_saved_analyses
from app.services.financial_engine import get_borrower
from app.services.guided_demo_service import get_guided_demos
from app.services.persistence import create_saved_analysis
from app.services.private_credit_service import analyze_private_credit
from app.models.domain import PrivateCreditAnalysisRequest


def test_ironbridge_audit_trail_explains_decline(debt_structure):
    analysis = analyze_private_credit(PrivateCreditAnalysisRequest(
        borrower_id="ironbridge-components",
        debt_structure=debt_structure,
        scenario_ids=["base", "mild", "severe"],
    ))
    audit = analysis.audit_trail
    assert audit is not None
    assert audit.final_recommendation == "Decline"
    assert audit.first_breach_period == "FY2026Q1"
    early_rule = next(rule for rule in audit.rules if rule.rule_id == "PC-DECLINE-01")
    assert early_rule.triggered is True
    assert early_rule.evidence
    assert "FY2026Q1" in early_rule.evidence[0].comparison
    assert early_rule.evidence[0].threshold is not None


def test_audit_evidence_contains_calculation_references(debt_structure):
    analysis = analyze_private_credit(PrivateCreditAnalysisRequest(
        borrower_id="vantage-services",
        debt_structure=debt_structure,
        scenario_ids=["base", "mild", "severe"],
    ))
    audit = analysis.audit_trail
    assert audit is not None
    assert all(item.calculation_reference for item in audit.supporting_metrics)
    assert all(rule.calculation_references for rule in audit.rules)
    assert any("gross_leverage" in ref for ref in audit.calculation_references)


def test_comparison_selects_lower_debt_higher_equity_structure(tmp_path, monkeypatch, debt_structure):
    monkeypatch.setenv("COVENANTIQ_DB_PATH", str(tmp_path / "comparison.db"))
    aggressive = debt_structure
    conservative = DebtStructureConfig(
        tranches=[
            tranche.model_copy(update={
                "opening_balance": tranche.opening_balance * 0.55,
                "new_borrowing": tranche.new_borrowing * 0.55,
                "drawn_amount": tranche.drawn_amount * 0.25,
            })
            for tranche in debt_structure.tranches
        ],
        minimum_cash_requirement=debt_structure.minimum_cash_requirement,
        excess_cash_flow_sweep_percentage=0.5,
    )
    aggressive_record = create_saved_analysis(SavedAnalysisCreate(
        analysis_name="Aggressive structure",
        borrower_id="vantage-services",
        debt_structure=aggressive,
        scenario_ids=["base", "mild", "severe"],
        sources_uses={"sponsor_equity_contribution": 5},
    ))
    conservative_record = create_saved_analysis(SavedAnalysisCreate(
        analysis_name="Conservative structure",
        borrower_id="vantage-services",
        debt_structure=conservative,
        scenario_ids=["base", "mild", "severe"],
        sources_uses={"sponsor_equity_contribution": 45},
    ))
    comparison = compare_saved_analyses([aggressive_record, conservative_record])
    assert len(comparison.entries) == 2
    assert comparison.safer_analysis_id == conservative_record.id
    entries = {entry.structure_name: entry for entry in comparison.entries}
    assert entries["Conservative structure"].net_leverage < entries["Aggressive structure"].net_leverage
    assert entries["Conservative structure"].sponsor_equity > entries["Aggressive structure"].sponsor_equity
    assert entries["Conservative structure"].safety_score > entries["Aggressive structure"].safety_score


def test_guided_demo_routes_and_borrowers_are_valid():
    demos = get_guided_demos()
    assert {demo.id for demo in demos} == {
        "healthy-approval", "distressed-decline", "structure-comparison"
    }
    for demo in demos:
        assert demo.route.startswith("/")
        assert demo.talking_points
        if demo.borrower_id:
            assert get_borrower(demo.borrower_id).id == demo.borrower_id
