from app.services.financial_engine import load_borrowers, validate_internal_consistency


def test_all_borrowers_are_complete_and_consistent():
    borrowers = load_borrowers()
    assert len(borrowers) == 5
    assert all(len(b.periods) == 6 for b in borrowers)
    assert all(len([p for p in b.periods if p.period_type.value == "historical"]) == 3 for b in borrowers)
    assert all(validate_internal_consistency(b) == [] for b in borrowers)
