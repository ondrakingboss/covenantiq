from __future__ import annotations

from collections import defaultdict

from app.models.domain import (
    CovenantDefinition, CovenantTestResult, CovenantType, FinancialPeriod, MetricResult, MetricStatus,
)
from app.services.financial_engine import r


RATIO_KEYS = {
    CovenantType.MAX_GROSS_LEVERAGE: "gross_leverage",
    CovenantType.MAX_NET_LEVERAGE: "net_leverage",
    CovenantType.MIN_INTEREST_COVERAGE: "interest_coverage",
    CovenantType.MIN_DSCR: "dscr",
    CovenantType.MIN_FIXED_CHARGE_COVERAGE: "fixed_charge_coverage",
    CovenantType.MIN_LIQUIDITY: "minimum_liquidity",
}
MAXIMUM_TYPES = {
    CovenantType.MAX_GROSS_LEVERAGE,
    CovenantType.MAX_NET_LEVERAGE,
    CovenantType.MAX_CAPEX,
}


def _severity(headroom_pct: float | None, tested: bool) -> str:
    if not tested:
        return "not_tested"
    assert headroom_pct is not None
    if headroom_pct >= 0.10:
        return "none"
    if headroom_pct >= 0:
        return "watch"
    if headroom_pct >= -0.10:
        return "moderate"
    return "severe"


def evaluate_covenants(
    covenants: list[CovenantDefinition], periods: list[FinancialPeriod],
    ratios: dict[str, dict[str, MetricResult]], scenario_name: str,
) -> list[CovenantTestResult]:
    projected = [p for p in periods if p.period_type.value == "projected"]
    results: list[CovenantTestResult] = []
    by_name: dict[str, list[CovenantTestResult]] = defaultdict(list)
    for covenant in covenants:
        for period in projected:
            if covenant.covenant_type == CovenantType.MAX_CAPEX:
                metric_value = period.capital_expenditure
                metric_status = MetricStatus.VALID
            else:
                ratio = ratios[period.fiscal_year][RATIO_KEYS[covenant.covenant_type]]
                metric_value = ratio.value
                metric_status = ratio.status
            if metric_status != MetricStatus.VALID or metric_value is None:
                result = CovenantTestResult(
                    covenant_name=covenant.name, covenant_type=covenant.covenant_type,
                    fiscal_year=period.fiscal_year, scenario=scenario_name,
                    calculated_value=None, metric_status=metric_status, threshold=covenant.threshold,
                    status="not_tested", absolute_headroom=None, percentage_headroom=None,
                    severity="not_tested",
                )
            else:
                headroom = (covenant.threshold - metric_value
                            if covenant.covenant_type in MAXIMUM_TYPES
                            else metric_value - covenant.threshold)
                pct = headroom / abs(covenant.threshold) if covenant.threshold != 0 else None
                passed = headroom >= 0
                result = CovenantTestResult(
                    covenant_name=covenant.name, covenant_type=covenant.covenant_type,
                    fiscal_year=period.fiscal_year, scenario=scenario_name,
                    calculated_value=r(metric_value), metric_status=metric_status,
                    threshold=covenant.threshold, status="pass" if passed else "fail",
                    absolute_headroom=r(headroom), percentage_headroom=None if pct is None else r(pct),
                    severity=_severity(pct, True) if pct is not None else ("none" if passed else "severe"),
                )
            results.append(result)
            by_name[covenant.name].append(result)
    for tests in by_name.values():
        first = next((item.fiscal_year for item in tests if item.status == "fail"), None)
        for item in tests:
            item.first_breach_period = first
    return results


def first_breach(results: list[CovenantTestResult]) -> str | None:
    years = list(dict.fromkeys(result.fiscal_year for result in results))
    return next((year for year in years if any(r.fiscal_year == year and r.status == "fail" for r in results)), None)
