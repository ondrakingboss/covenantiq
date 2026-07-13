from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.models.domain import Borrower, FinancialPeriod, PeriodType


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "borrowers.json"


def r(value: float) -> float:
    return round(value + 0.0, 2)


def normalize_period(raw: dict[str, Any], index: int) -> FinancialPeriod:
    revenue = float(raw["revenue"][index])
    ebitda = revenue * float(raw["ebitda_margin"][index])
    depreciation = revenue * float(raw["depreciation_pct"])
    ebit = ebitda - depreciation
    debt = float(raw["debt"][index])
    interest = debt * float(raw["interest_rate"][index])
    pretax_income = ebit - interest
    taxes = max(pretax_income, 0) * float(raw["tax_rate"])
    net_income = pretax_income - taxes
    cash = float(raw["cash"][index])
    ar = revenue * float(raw["ar_days"][index]) / 365
    inventory = revenue * float(raw["inventory_days"][index]) / 365
    other_current_assets = revenue * float(raw["other_current_assets_pct"])
    current_assets = cash + ar + inventory + other_current_assets
    current_liabilities = revenue * float(raw["current_liabilities_pct"][index])
    ocf = revenue * float(raw["ocf_margin"][index])
    capex = revenue * float(raw["capex_pct"][index])
    fcf = ocf - capex
    return FinancialPeriod(
        fiscal_year=raw["years"][index],
        period_type=PeriodType.HISTORICAL if index < 3 else PeriodType.PROJECTED,
        revenue=r(revenue), ebitda=r(ebitda), ebit=r(ebit), interest_expense=r(interest),
        taxes=r(taxes), net_income=r(net_income), cash=r(cash), accounts_receivable=r(ar),
        inventory=r(inventory), current_assets=r(current_assets),
        current_liabilities=r(current_liabilities), total_debt=r(debt),
        lease_liabilities=r(float(raw["lease_liabilities"][index])), operating_cash_flow=r(ocf),
        capital_expenditure=r(capex), free_cash_flow=r(fcf),
        mandatory_debt_amortization=r(float(raw["mandatory_amortization"][index])),
    )


def load_borrowers() -> list[Borrower]:
    raw_items = json.loads(DATA_PATH.read_text())
    return [
        Borrower(
            id=raw["id"], name=raw["name"], industry=raw["industry"],
            profile=raw["profile"], risk_summary=raw["risk_summary"],
            periods=[normalize_period(raw, i) for i in range(6)],
        )
        for raw in raw_items
    ]


def get_borrower(borrower_id: str) -> Borrower:
    for borrower in load_borrowers():
        if borrower.id == borrower_id:
            return borrower
    raise KeyError(f"Unknown borrower '{borrower_id}'")


def validate_internal_consistency(borrower: Borrower, tolerance: float = 0.02) -> list[str]:
    errors: list[str] = []
    for p in borrower.periods:
        if abs(p.free_cash_flow - (p.operating_cash_flow - p.capital_expenditure)) > tolerance:
            errors.append(f"{p.fiscal_year}: free cash flow does not reconcile")
        if p.current_assets + tolerance < p.cash + p.accounts_receivable + p.inventory:
            errors.append(f"{p.fiscal_year}: current assets omit a reported component")
        if abs(p.net_income - (p.ebit - p.interest_expense - p.taxes)) > 0.04:
            errors.append(f"{p.fiscal_year}: net income does not reconcile")
    return errors
