from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_and_borrowers():
    assert client.get("/health").json()["status"] == "ok"
    assert len(client.get("/borrowers").json()) == 5


def test_invalid_loan_is_readable():
    response = client.post("/loans/analyze", json={
        "borrower_id": "northstar-cloud",
        "loan": {"new_loan_amount": -1, "annual_interest_rate": 2, "loan_term_years": 0,
                 "amortization_percentage": 2, "upfront_fees": 0, "minimum_cash_requirement": 0,
                 "existing_debt_refinanced_amount": 0, "revolving_credit_commitment": 0},
    })
    assert response.status_code == 422
    assert response.json()["detail"]
