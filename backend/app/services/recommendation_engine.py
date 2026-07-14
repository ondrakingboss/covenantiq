from __future__ import annotations

from app.models.domain import (
    MultiScenarioResult, QuarterlyScenarioResult, RecommendationResult, ScenarioResult,
)


DISCLAIMER = (
    "CovenantIQ is a public beta using sample borrower data. Outputs are for product demonstration "
    "and education only and do not constitute lending, investment, legal, accounting, or financial advice."
)


def _first_projected_metric(scenario: ScenarioResult, key: str):
    year = next(p.fiscal_year for p in scenario.periods if p.period_type.value == "projected")
    return scenario.ratios[year][key]


def recommend(scenarios: list[ScenarioResult], minimum_cash: float) -> RecommendationResult:
    base = next(s for s in scenarios if s.scenario.id == "base")
    severe = next((s for s in scenarios if s.scenario.id in {"severe", "combined"}), scenarios[-1])
    leverage = _first_projected_metric(base, "gross_leverage")
    coverage = _first_projected_metric(base, "interest_coverage")
    liquidity = _first_projected_metric(base, "minimum_liquidity")
    fcfads = _first_projected_metric(base, "fcf_after_debt_service")
    base_fails = [r for r in base.covenant_results if r.status == "fail"]
    severe_fails = [r for r in severe.covenant_results if r.status == "fail"]
    early_severe = any(r.status == "fail" and r.fiscal_year.endswith("26E") for r in severe.covenant_results)
    reasons: list[str] = []
    positives: list[str] = []
    risks: list[str] = []
    conditions: list[str] = []

    if leverage.value is not None and leverage.value <= 3.0:
        positives.append(f"Opening projected gross leverage is {leverage.value:.2f}x.")
    else:
        risks.append("Opening projected leverage is elevated or not meaningful.")
    if coverage.value is not None and coverage.value >= 3.0:
        positives.append(f"Opening projected interest coverage is {coverage.value:.2f}x.")
    else:
        risks.append("Opening projected interest coverage is below 3.0x or unavailable.")
    if fcfads.value is not None and fcfads.value > 0:
        positives.append("Base-case free cash flow after debt service is positive.")
    else:
        risks.append("Base-case free cash flow after debt service is non-positive.")
    if severe_fails:
        risks.append(f"{len(severe_fails)} covenant tests fail in {severe.scenario.name}.")
        conditions.append("Require quarterly covenant reporting and a 13-week liquidity forecast on trigger.")
    if liquidity.value is not None and liquidity.value < minimum_cash * 1.15:
        risks.append("Modeled liquidity has less than 15% cushion over minimum cash.")
        conditions.append("Maintain a blocked minimum-cash reserve and monthly liquidity reporting.")

    if len(base_fails) >= 2 or (early_severe and (fcfads.value is None or fcfads.value < 0)):
        recommendation, grade = "Decline", "8"
        reasons.append("Base-case covenant weakness or immediate stress failure combines with inadequate debt-service cash flow.")
    elif base_fails or leverage.value is None or coverage.value is None:
        recommendation, grade = "Further diligence required", "6"
        reasons.append("Base-case compliance or ratio interpretability requires resolution before approval.")
    elif severe_fails:
        recommendation, grade = "Approve with conditions", "4"
        reasons.append("Base case is supportable, but downside covenant resilience is limited.")
        conditions.append("Set covenant levels with at least 15% opening headroom and prohibit distributions while stressed.")
    else:
        recommendation, grade = "Approve", "3"
        reasons.append("Base and selected downside cases retain modeled covenant compliance and debt-service capacity.")

    confidence = "High" if leverage.status.value == "valid" and coverage.status.value == "valid" else "Low"
    if confidence == "High" and len(scenarios) < 3:
        confidence = "Moderate"
    return RecommendationResult(
        recommendation=recommendation, risk_grade=grade, confidence_level=confidence,
        primary_reasons=reasons, positive_factors=positives, key_risks=risks,
        proposed_conditions=list(dict.fromkeys(conditions)),
        calculation_references=[
            "Base / first projected year / gross_leverage",
            "Base / first projected year / interest_coverage",
            "Base / first projected year / minimum_liquidity",
            f"{severe.scenario.name} / covenant_results",
        ], disclaimer=DISCLAIMER,
    )


def recommend_private_credit(
    annual_scenarios: list[MultiScenarioResult],
    quarterly_scenarios: list[QuarterlyScenarioResult],
    minimum_cash: float,
) -> RecommendationResult:
    """Extend the verified annual rules with a transparent early-breach override."""
    recommendation = recommend(annual_scenarios, minimum_cash)  # type: ignore[arg-type]
    base_quarterly = next(item for item in quarterly_scenarios if item.scenario.id == "base")
    early_failures = [
        result for result in base_quarterly.covenant_results
        if result.status == "fail" and result.fiscal_year.startswith("FY2026Q")
    ]
    if not early_failures:
        return recommendation
    first = base_quarterly.first_breach_period or early_failures[0].fiscal_year
    return recommendation.model_copy(update={
        "recommendation": "Decline",
        "risk_grade": "8",
        "primary_reasons": [
            f"Base-case covenant compliance fails within the first four projected quarters ({first}).",
            *recommendation.primary_reasons,
        ],
        "key_risks": list(dict.fromkeys([
            f"Base-case covenant breach occurs in {first}.",
            *recommendation.key_risks,
        ])),
        "calculation_references": list(dict.fromkeys([
            f"Base / {first} / covenant_results",
            *recommendation.calculation_references,
        ])),
    })
