import pytest

from app.models.domain import (
    DebtStructureConfig, DebtTrancheConfig, FinancialPeriod, LoanConfig, PeriodType,
)


@pytest.fixture
def loan():
    return LoanConfig(
        new_loan_amount=100, annual_interest_rate=0.08, loan_term_years=5,
        amortization_percentage=0.05, upfront_fees=2, minimum_cash_requirement=10,
        existing_debt_refinanced_amount=40, revolving_credit_commitment=20,
    )


@pytest.fixture
def period():
    return FinancialPeriod(
        fiscal_year="FY2026E", period_type=PeriodType.PROJECTED,
        revenue=200, ebitda=40, ebit=30, interest_expense=8, taxes=5, net_income=17,
        cash=20, accounts_receivable=30, inventory=25, current_assets=90,
        current_liabilities=50, total_debt=120, lease_liabilities=10,
        operating_cash_flow=32, capital_expenditure=12, free_cash_flow=20,
        mandatory_debt_amortization=4,
    )


@pytest.fixture
def debt_structure():
    return DebtStructureConfig(tranches=[
        DebtTrancheConfig(
            id="rcf", name="Revolver", tranche_type="revolver", drawn_amount=10,
            interest_rate=0.08, maturity_period="FY2028E", commitment_amount=50,
            commitment_fee=0.01,
        ),
        DebtTrancheConfig(
            id="senior", name="Senior term loan", tranche_type="senior_secured_term_loan",
            opening_balance=100, new_borrowing=50, refinancing_amount=20,
            interest_rate=0.10, amortization_percentage=0.10, maturity_period="FY2030E",
        ),
        DebtTrancheConfig(
            id="mezz", name="Mezzanine", tranche_type="subordinated_debt",
            opening_balance=20, interest_rate=0.12, maturity_period="FY2031E",
            pik_interest=True,
        ),
    ], minimum_cash_requirement=10, excess_cash_flow_sweep_percentage=0.25)
