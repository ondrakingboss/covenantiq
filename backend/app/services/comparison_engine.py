from __future__ import annotations

from app.models.domain import DealComparisonEntry, DealComparisonResponse, SavedAnalysisRecord


RECOMMENDATION_POINTS = {
    "Approve": 40,
    "Approve with conditions": 28,
    "Further diligence required": 14,
    "Decline": 0,
}


def _metric_value(record: SavedAnalysisRecord, name: str) -> float | None:
    base = next(item for item in record.analysis.annual_scenarios if item.scenario.id == "base")
    period = base.consolidated_debt_schedule[0].period
    return base.ratios[period][name].value


def _entry(record: SavedAnalysisRecord) -> DealComparisonEntry:
    base = next(item for item in record.analysis.annual_scenarios if item.scenario.id == "base")
    quarterly = next(item for item in record.analysis.quarterly_scenarios if item.scenario.id == "base")
    schedule = base.consolidated_debt_schedule[0]
    net_leverage = _metric_value(record, "net_leverage")
    gross_leverage = _metric_value(record, "gross_leverage")
    coverage = _metric_value(record, "interest_coverage")
    dscr = _metric_value(record, "dscr")
    liquidity = _metric_value(record, "minimum_liquidity")
    recommendation = record.analysis.recommendation.recommendation
    grade = int(record.analysis.recommendation.risk_grade)
    debt = schedule.closing_balance
    sponsor = record.request.sources_uses.sponsor_equity_contribution
    pass_count = sum(result.status == "pass" for result in quarterly.covenant_results)
    fail_count = sum(result.status == "fail" for result in quarterly.covenant_results)
    not_tested_count = sum(result.status == "not_tested" for result in quarterly.covenant_results)

    score = float(RECOMMENDATION_POINTS.get(recommendation, 0))
    factors = [f"Recommendation contributes {RECOMMENDATION_POINTS.get(recommendation, 0)} points."]
    grade_points = max(0, 10 - grade) * 2
    score += grade_points
    factors.append(f"Risk grade {grade} contributes {grade_points} points; lower grades score better.")
    if quarterly.first_breach_period is None:
        score += 15
        factors.append("No base-case quarterly breach contributes 15 points.")
    else:
        factors.append(f"Base-case first breach at {quarterly.first_breach_period} contributes no resilience points.")
    if net_leverage is not None:
        points = max(0.0, 6 - net_leverage) * 4
        score += points
        factors.append(f"Net leverage of {net_leverage:.2f}x contributes {points:.1f} points; lower is safer.")
    if coverage is not None:
        points = min(max(coverage, 0), 6) * 2
        score += points
        factors.append(f"Interest coverage of {coverage:.2f}x contributes {points:.1f} points.")
    if dscr is not None:
        points = min(max(dscr, 0), 3) * 4
        score += points
        factors.append(f"DSCR of {dscr:.2f}x contributes {points:.1f} points.")
    if liquidity is not None and debt + sponsor > 0:
        liquidity_points = min(10.0, max(0.0, liquidity / (debt + sponsor) * 10))
        score += liquidity_points
        factors.append(f"Liquidity relative to funded capital contributes {liquidity_points:.1f} points.")
    if debt + sponsor > 0:
        equity_points = min(10.0, sponsor / (debt + sponsor) * 10)
        score += equity_points
        factors.append(f"Sponsor equity contribution contributes {equity_points:.1f} points.")

    return DealComparisonEntry(
        analysis_id=record.id,
        structure_name=record.analysis_name,
        borrower_id=record.borrower_id,
        recommendation=recommendation,
        risk_grade=record.analysis.recommendation.risk_grade,
        net_leverage=net_leverage,
        gross_leverage=gross_leverage,
        interest_coverage=coverage,
        dscr=dscr,
        minimum_liquidity=liquidity,
        first_breach_period=quarterly.first_breach_period,
        total_debt=debt,
        sponsor_equity=sponsor,
        weighted_average_cash_interest_rate=schedule.weighted_average_cash_interest_rate,
        covenant_pass_count=pass_count,
        covenant_fail_count=fail_count,
        covenant_not_tested_count=not_tested_count,
        safety_score=round(score, 2),
        safety_factors=factors,
    )


def compare_saved_analyses(records: list[SavedAnalysisRecord]) -> DealComparisonResponse:
    if len(records) < 2:
        raise ValueError("At least two analyses are required for comparison.")
    borrower_ids = {record.borrower_id for record in records}
    if len(borrower_ids) != 1:
        raise ValueError("Deal structures can only be compared for the same borrower.")
    entries = [_entry(record) for record in records]
    safer = max(entries, key=lambda item: (item.safety_score, -float(item.net_leverage or 999)))
    others = [item for item in entries if item.analysis_id != safer.analysis_id]
    rationale = [f"{safer.structure_name} has the highest deterministic safety score ({safer.safety_score:.1f})."]
    if others:
        closest = max(others, key=lambda item: item.safety_score)
        if safer.net_leverage is not None and closest.net_leverage is not None and safer.net_leverage < closest.net_leverage:
            rationale.append(f"Net leverage is lower at {safer.net_leverage:.2f}x versus {closest.net_leverage:.2f}x.")
        if safer.sponsor_equity > closest.sponsor_equity:
            rationale.append(f"Sponsor equity is higher at ${safer.sponsor_equity:.1f}m versus ${closest.sponsor_equity:.1f}m.")
        if safer.first_breach_period is None and closest.first_breach_period is not None:
            rationale.append(f"The safer structure has no base-case quarterly breach; the comparator first breaches in {closest.first_breach_period}.")
    return DealComparisonResponse(
        borrower_id=records[0].borrower_id,
        entries=entries,
        safer_analysis_id=safer.analysis_id,
        safer_structure_name=safer.structure_name,
        rationale=rationale,
        methodology=[
            "The safety score rewards stronger recommendations, lower risk grades, and no base-case quarterly breach.",
            "Lower net leverage, stronger interest coverage and DSCR, and greater liquidity increase the score.",
            "Sponsor equity receives a modest positive contribution; the score is comparative, not a lender rating.",
        ],
    )
