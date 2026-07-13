from app.services.debt_engine import build_multi_tranche_schedule


def test_tranche_and_consolidated_roll_forward(debt_structure):
    consolidated, tranches = build_multi_tranche_schedule(
        ["FY2026E"], {"FY2026E": 30}, {"FY2026E": 0}, debt_structure
    )
    senior = tranches["senior"][0]
    mezz = tranches["mezz"][0]
    total = consolidated[0]
    assert senior.opening_balance == 100
    assert senior.new_borrowing == 50
    assert senior.refinancing == 20
    assert senior.mandatory_amortization == 13
    assert senior.closing_balance == 117
    assert mezz.pik_accrual == 2.4
    assert mezz.closing_balance == 22.4
    assert total.opening_balance == 130
    assert total.new_borrowing == 50
    assert total.refinancing == 20
    assert total.closing_balance == 149.4


def test_revolver_availability_commitment_fee_and_weighted_rate(debt_structure):
    consolidated, tranches = build_multi_tranche_schedule(
        ["FY2026E"], {"FY2026E": 30}, {"FY2026E": 0}, debt_structure
    )
    revolver = tranches["rcf"][0]
    total = consolidated[0]
    assert revolver.undrawn_amount == 40
    assert revolver.commitment_fee == 0.4
    assert total.revolver_availability == 40
    assert total.total_liquidity == 70
    assert total.cash_interest == 15.55
    assert total.total_cash_interest == 15.95
    assert total.weighted_average_cash_interest_rate == 0.1
