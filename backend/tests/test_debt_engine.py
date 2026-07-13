from app.models.domain import PeriodType
from app.services.debt_engine import build_debt_schedule


def test_debt_balance_roll_forward(period, loan):
    historical = [period.model_copy(update={"fiscal_year": f"FY202{i}A", "period_type": PeriodType.HISTORICAL, "total_debt": 120}) for i in range(3, 6)]
    projected = [period.model_copy(update={"fiscal_year": f"FY202{i}E", "cash": 10, "free_cash_flow": 0}) for i in range(6, 9)]
    rows = build_debt_schedule(historical + projected, loan)
    assert rows[0].opening_balance == 80
    assert rows[0].new_borrowing == 100
    assert rows[0].mandatory_amortization == 9
    assert rows[0].closing_balance == 171
    assert rows[1].opening_balance == rows[0].closing_balance
    assert rows[1].closing_balance == rows[1].opening_balance - rows[1].mandatory_amortization


def test_interest_uses_average_balance_and_fee_amortization(period, loan):
    historical = [period.model_copy(update={"period_type": PeriodType.HISTORICAL, "total_debt": 40})] * 3
    projected = [period.model_copy(update={"cash": 10, "free_cash_flow": 0})]
    row = build_debt_schedule(historical + projected, loan)[0]
    assert row.opening_balance == 0
    assert row.closing_balance == 91
    assert row.cash_interest == 7.64
    assert row.effective_interest == 8.04
