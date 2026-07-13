"""Generate the checked-in deterministic Ironbridge IC memo sample."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models.domain import (
    CovenantDefinition,
    CovenantType,
    DebtStructureConfig,
    DebtTrancheConfig,
    PrivateCreditAnalysisRequest,
    SensitivityRequest,
    SourcesUses,
)
from app.services.memo_engine import generate_private_credit_memo_html
from app.services.private_credit_service import analyze_private_credit
from app.services.sensitivity_engine import run_sensitivity


def main() -> None:
    structure = DebtStructureConfig(
        minimum_cash_requirement=10,
        excess_cash_flow_sweep_percentage=0.25,
        tranches=[
            DebtTrancheConfig(
                id="rcf", name="Revolving credit facility", tranche_type="revolver",
                drawn_amount=12, commitment_amount=40, interest_rate=0.09,
                commitment_fee=0.005, maturity_period="FY2028E",
            ),
            DebtTrancheConfig(
                id="senior", name="Senior secured term loan",
                tranche_type="senior_secured_term_loan", opening_balance=155,
                new_borrowing=45, refinancing_amount=30, interest_rate=0.105,
                amortization_percentage=0.05, maturity_period="FY2030E",
            ),
            DebtTrancheConfig(
                id="mezz", name="Subordinated debt", tranche_type="subordinated_debt",
                opening_balance=25, new_borrowing=10, interest_rate=0.13,
                pik_interest=True, maturity_period="FY2031E",
            ),
        ],
    )
    covenants = [
        CovenantDefinition(name="Maximum gross leverage", covenant_type=CovenantType.MAX_GROSS_LEVERAGE, threshold=4.5),
        CovenantDefinition(name="Maximum net leverage", covenant_type=CovenantType.MAX_NET_LEVERAGE, threshold=4.0),
        CovenantDefinition(name="Minimum interest coverage", covenant_type=CovenantType.MIN_INTEREST_COVERAGE, threshold=2.0),
        CovenantDefinition(name="Minimum DSCR", covenant_type=CovenantType.MIN_DSCR, threshold=1.15),
        CovenantDefinition(name="Minimum liquidity", covenant_type=CovenantType.MIN_LIQUIDITY, threshold=15),
    ]
    request = PrivateCreditAnalysisRequest(
        borrower_id="ironbridge-components", debt_structure=structure,
        covenants=covenants, scenario_ids=["base", "mild", "severe", "combined"],
        sources_uses=SourcesUses(
            sponsor_equity_contribution=65, cash_on_balance_sheet=10,
            transaction_fees=5, cash_to_balance_sheet=8,
            general_corporate_purposes=87,
        ),
    )
    analysis = analyze_private_credit(request)
    sensitivity = run_sensitivity(SensitivityRequest(
        borrower_id=request.borrower_id, debt_structure=structure, covenants=covenants,
    ))
    html = generate_private_credit_memo_html(analysis, sensitivity, "CovenantIQ Demonstration")
    output = Path(__file__).resolve().parents[2] / "docs" / "sample_outputs" / "ironbridge_ic_memo.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    print(f"Generated {output}")


if __name__ == "__main__":
    main()
