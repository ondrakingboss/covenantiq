from app.models.domain import DebtScheduleRow, MetricStatus
from app.services.ratio_engine import calculate_period_ratios


def debt_row():
    return DebtScheduleRow(
        fiscal_year="FY2026E", opening_balance=130, new_borrowing=0,
        mandatory_amortization=10, optional_repayment=0, closing_balance=120,
        cash_interest=8, effective_interest=8.4,
    )


def test_gross_and_net_leverage(period, loan):
    ratios = calculate_period_ratios(period, debt_row(), loan)
    assert ratios["gross_leverage"].value == 3.0
    assert ratios["net_leverage"].value == 2.5


def test_interest_coverage_and_dscr(period, loan):
    ratios = calculate_period_ratios(period, debt_row(), loan)
    assert ratios["interest_coverage"].value == 5.0
    assert ratios["dscr"].value == 1.56


def test_negative_ebitda_is_not_meaningful(period, loan):
    ratios = calculate_period_ratios(period.model_copy(update={"ebitda": -5}), debt_row(), loan)
    assert ratios["gross_leverage"].value is None
    assert ratios["gross_leverage"].status == MetricStatus.NOT_MEANINGFUL


def test_zero_interest_is_not_meaningful(period, loan):
    row = debt_row().model_copy(update={"cash_interest": 0})
    ratios = calculate_period_ratios(period, row, loan)
    assert ratios["interest_coverage"].value is None
    assert ratios["interest_coverage"].status == MetricStatus.NOT_MEANINGFUL
