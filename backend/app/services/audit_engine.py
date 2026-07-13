from __future__ import annotations

from app.models.domain import (
    AuditEvidence,
    AuditRuleTrace,
    AuditTrail,
    CovenantTestResult,
    MetricResult,
    MultiScenarioResult,
    QuarterlyScenarioResult,
    RecommendationResult,
)


def _period_rank(period: str) -> tuple[int, int]:
    digits = "".join(character for character in period if character.isdigit())
    year = int(digits[:4]) if len(digits) >= 4 else 9999
    quarter = int(period[-1]) if "Q" in period and period[-1].isdigit() else 5
    return year, quarter


def _metric_evidence(
    metric: MetricResult,
    period: str,
    label: str,
    operator: str,
    threshold: float | None,
    unit: str,
    adverse: bool,
) -> AuditEvidence:
    actual = metric.value
    comparison = (
        f"{label}: unavailable"
        if actual is None
        else f"{label}: {actual:.2f}{'x' if unit == 'x' else 'm'} {operator} "
             f"{threshold:.2f}{'x' if unit == 'x' else 'm'}"
    )
    return AuditEvidence(
        label=label,
        actual_value=actual,
        operator=operator,
        threshold=threshold,
        unit=unit,
        period=period,
        scenario="Base",
        status="unavailable" if actual is None else ("adverse" if adverse else "supports"),
        comparison=comparison,
        calculation_reference=f"Base / {period} / {metric.metric}",
    )


def _covenant_evidence(result: CovenantTestResult) -> AuditEvidence:
    maximum = result.covenant_type.value.startswith("maximum")
    operator = "<=" if maximum else ">="
    unit = "USD millions" if "liquidity" in result.covenant_type.value or "expenditure" in result.covenant_type.value else "x"
    actual = result.calculated_value
    suffix = "m" if unit == "USD millions" else "x"
    comparison = (
        f"{result.fiscal_year} {result.covenant_name}: unavailable"
        if actual is None
        else f"{result.fiscal_year} {result.covenant_name}: {actual:.2f}{suffix} "
             f"{operator} {result.threshold:.2f}{suffix} ({result.status})"
    )
    return AuditEvidence(
        label=result.covenant_name,
        actual_value=actual,
        operator=operator,
        threshold=result.threshold,
        unit=unit,
        period=result.fiscal_year,
        scenario=result.scenario,
        status="adverse" if result.status == "fail" else "supports" if result.status == "pass" else "unavailable",
        comparison=comparison,
        calculation_reference=f"{result.scenario} / {result.fiscal_year} / {result.covenant_type.value}",
    )


def _unique_breaches(
    annual: list[MultiScenarioResult], quarterly: list[QuarterlyScenarioResult]
) -> list[CovenantTestResult]:
    seen: set[tuple[str, str, str]] = set()
    breaches: list[CovenantTestResult] = []
    for scenario in [*quarterly, *annual]:
        for result in scenario.covenant_results:
            key = (result.scenario, result.fiscal_year, result.covenant_name)
            if result.status == "fail" and key not in seen:
                breaches.append(result)
                seen.add(key)
    return sorted(breaches, key=lambda item: (_period_rank(item.fiscal_year), item.scenario, item.covenant_name))


def build_audit_trail(
    annual: list[MultiScenarioResult],
    quarterly: list[QuarterlyScenarioResult],
    recommendation: RecommendationResult,
    minimum_cash: float,
) -> AuditTrail:
    base = next(item for item in annual if item.scenario.id == "base")
    base_quarterly = next(item for item in quarterly if item.scenario.id == "base")
    downside = next((item for item in annual if item.scenario.id in {"severe", "combined"}), annual[-1])
    first_year = next(period.fiscal_year for period in base.periods if period.period_type.value == "projected")
    metrics = base.ratios[first_year]
    leverage = metrics["gross_leverage"]
    net_leverage = metrics["net_leverage"]
    coverage = metrics["interest_coverage"]
    dscr = metrics["dscr"]
    liquidity = metrics["minimum_liquidity"]
    fcfads = metrics["fcf_after_debt_service"]
    base_annual_failures = [result for result in base.covenant_results if result.status == "fail"]
    downside_failures = [result for result in downside.covenant_results if result.status == "fail"]
    early_base_failures = [
        result for result in base_quarterly.covenant_results
        if result.status == "fail" and _period_rank(result.fiscal_year) <= _period_rank("FY2026Q4")
    ]
    breaches = _unique_breaches(annual, quarterly)
    first_breach = min((item.fiscal_year for item in breaches), key=_period_rank) if breaches else None

    supporting_metrics = [
        _metric_evidence(leverage, first_year, "Gross leverage", "<=", 3.0, "x", leverage.value is None or leverage.value > 3.0),
        _metric_evidence(net_leverage, first_year, "Net leverage", "<=", 4.0, "x", net_leverage.value is None or net_leverage.value > 4.0),
        _metric_evidence(coverage, first_year, "Interest coverage", ">=", 3.0, "x", coverage.value is None or coverage.value < 3.0),
        _metric_evidence(dscr, first_year, "DSCR", ">=", 1.15, "x", dscr.value is None or dscr.value < 1.15),
        _metric_evidence(liquidity, first_year, "Minimum liquidity", ">=", minimum_cash * 1.15, "USD millions", liquidity.value is None or liquidity.value < minimum_cash * 1.15),
        _metric_evidence(fcfads, first_year, "FCF after debt service", ">", 0.0, "USD millions", fcfads.value is None or fcfads.value <= 0),
    ]

    early_evidence = [_covenant_evidence(result) for result in early_base_failures[:4]]
    base_evidence = [_covenant_evidence(result) for result in base_annual_failures[:4]]
    downside_evidence = [_covenant_evidence(result) for result in downside_failures[:4]]
    rules = [
        AuditRuleTrace(
            rule_id="PC-DECLINE-01",
            rule="Decline if a base-case covenant breach occurs within the first four projected quarters.",
            triggered=bool(early_base_failures),
            impact="Critical",
            evidence=early_evidence,
            related_output="Recommendation changed to Decline." if early_base_failures else "No decline override.",
            explanation=(
                f"Base-case compliance fails in {base_quarterly.first_breach_period}; an early breach is incompatible with approval."
                if early_base_failures else "The base case remains compliant through the first four projected quarters."
            ),
            calculation_references=[e.calculation_reference for e in early_evidence] or ["Base / quarterly covenant_results"],
        ),
        AuditRuleTrace(
            rule_id="PC-DECLINE-02",
            rule="Decline if at least two base-case annual covenant tests fail.",
            triggered=len(base_annual_failures) >= 2,
            impact="High",
            evidence=base_evidence,
            related_output="Supports Decline." if len(base_annual_failures) >= 2 else "No decline signal.",
            explanation=f"{len(base_annual_failures)} base-case annual covenant tests fail.",
            calculation_references=[e.calculation_reference for e in base_evidence] or ["Base / annual covenant_results"],
        ),
        AuditRuleTrace(
            rule_id="PC-CONDITION-01",
            rule="Require conditions when the selected severe downside produces covenant failures.",
            triggered=bool(downside_failures),
            impact="High",
            evidence=downside_evidence,
            related_output="Adds downside monitoring and covenant conditions." if downside_failures else "No downside condition added.",
            explanation=f"{len(downside_failures)} covenant tests fail in {downside.scenario.name}.",
            calculation_references=[e.calculation_reference for e in downside_evidence] or [f"{downside.scenario.name} / covenant_results"],
        ),
        AuditRuleTrace(
            rule_id="PC-LIQUIDITY-01",
            rule="Flag liquidity when modeled liquidity has less than a 15% cushion over minimum cash.",
            triggered=liquidity.value is None or liquidity.value < minimum_cash * 1.15,
            impact="High",
            evidence=[supporting_metrics[4]],
            related_output="Adds minimum-cash protection and monthly reporting." if liquidity.value is None or liquidity.value < minimum_cash * 1.15 else "Liquidity cushion supports the decision.",
            explanation=supporting_metrics[4].comparison,
            calculation_references=[supporting_metrics[4].calculation_reference],
        ),
        AuditRuleTrace(
            rule_id="PC-CASHFLOW-01",
            rule="Flag debt-service capacity when base-case free cash flow after debt service is non-positive.",
            triggered=fcfads.value is None or fcfads.value <= 0,
            impact="High",
            evidence=[supporting_metrics[5]],
            related_output="Supports a negative recommendation." if fcfads.value is None or fcfads.value <= 0 else "Cash generation supports approval.",
            explanation=supporting_metrics[5].comparison,
            calculation_references=[supporting_metrics[5].calculation_reference],
        ),
        AuditRuleTrace(
            rule_id="PC-APPROVE-01",
            rule="Approve when base and selected downside cases retain covenant compliance and interpretable debt-service capacity.",
            triggered=not base_annual_failures and not downside_failures and not early_base_failures and leverage.value is not None and coverage.value is not None,
            impact="Moderate",
            evidence=supporting_metrics[:4],
            related_output="Supports Approve." if recommendation.recommendation == "Approve" else "Approval rule not satisfied.",
            explanation="Core leverage, coverage, and covenant tests are evaluated together; no single metric determines approval.",
            calculation_references=[item.calculation_reference for item in supporting_metrics[:4]],
        ),
    ]

    drivers: list[str] = []
    for scenario in annual:
        definition = scenario.scenario
        if definition.id == "base":
            continue
        drivers.append(
            f"{definition.name}: revenue {definition.revenue_change:.0%}, EBITDA margin "
            f"{definition.ebitda_margin_change_bps:+d} bps, interest rates "
            f"{definition.interest_rate_change_bps:+d} bps."
        )
    explanation = " ".join(recommendation.primary_reasons)
    if first_breach:
        explanation += f" The earliest modeled covenant breach is {first_breach}."
    else:
        explanation += " No modeled covenant breach occurs in the selected scenarios."
    triggered_rules = [rule for rule in rules if rule.triggered]
    references = list(dict.fromkeys(
        [*recommendation.calculation_references, *[ref for rule in triggered_rules for ref in rule.calculation_references]]
    ))
    return AuditTrail(
        final_recommendation=recommendation.recommendation,
        risk_grade=recommendation.risk_grade,
        confidence_level=recommendation.confidence_level,
        rules=rules,
        supporting_metrics=supporting_metrics,
        covenant_breaches=breaches,
        scenario_drivers=drivers,
        first_breach_period=first_breach,
        human_readable_explanation=explanation,
        calculation_references=references,
    )
