from __future__ import annotations

from datetime import date
from html import escape

from app.models.domain import (
    AnalysisResponse, DebtTrancheType, PrivateCreditAnalysisResponse, SensitivityResponse,
)


def _money(value: float | None) -> str:
    return "N/M" if value is None else f"${value:,.1f}m"


def _ratio(value: float | None) -> str:
    return "N/M" if value is None else f"{value:.2f}x"


def generate_memo_html(analysis: AnalysisResponse, analyst_name: str) -> str:
    borrower = analysis.borrower
    base = next(s for s in analysis.scenarios if s.scenario.id == "base")
    first_year = next(p.fiscal_year for p in base.periods if p.period_type.value == "projected")
    metrics = base.ratios[first_year]
    scenario_rows = "".join(
        f"<tr><td>{escape(s.scenario.name)}</td><td>{escape(s.first_breach_period or 'No breach')}</td>"
        f"<td>{_ratio(next(iter([s.ratios[p.fiscal_year]['gross_leverage'].value for p in s.periods if p.period_type.value == 'projected']), None))}</td></tr>"
        for s in analysis.scenarios
    )
    covenant_rows = "".join(
        f"<tr><td>{escape(c.covenant_name)}</td><td>{escape(c.fiscal_year)}</td>"
        f"<td>{'N/M' if c.calculated_value is None else f'{c.calculated_value:.2f}'}</td>"
        f"<td>{c.threshold:.2f}</td><td class='{c.status}'>{c.status.upper()}</td></tr>"
        for c in base.covenant_results
    )
    def lis(items: list[str]) -> str:
        return "".join(f"<li>{escape(item)}</li>" for item in items) or "<li>None identified by the rule set.</li>"
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>CovenantIQ Credit Memo: {escape(borrower.name)}</title>
<style>body{{font:14px Arial,sans-serif;color:#17212b;margin:40px;line-height:1.45}}header{{border-bottom:3px solid #173c47;padding-bottom:18px}}h1{{font-size:28px;margin:0}}h2{{font-size:16px;margin-top:28px;border-bottom:1px solid #c7ced2;padding-bottom:6px}}.meta{{color:#59656d}}.verdict{{border-left:5px solid #2f6f67;background:#eef3f1;padding:14px;margin:22px 0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;border-bottom:1px solid #d9dfe2;text-align:right}}th:first-child,td:first-child{{text-align:left}}.fail{{color:#9a342d;font-weight:bold}}.pass{{color:#286557;font-weight:bold}}@media print{{body{{margin:14mm}}.no-print{{display:none}}}} </style></head>
<body><header><div class='meta'>COVENANTIQ | PRELIMINARY CREDIT MEMORANDUM</div><h1>{escape(borrower.name)}</h1><div class='meta'>Prepared {date.today().isoformat()} by {escape(analyst_name)} | {escape(borrower.units)}</div></header>
<section class='verdict'><strong>{analysis.recommendation.recommendation}</strong> | Risk grade {analysis.recommendation.risk_grade} | {analysis.recommendation.confidence_level} confidence<br>{escape(analysis.recommendation.primary_reasons[0])}</section>
<h2>Transaction overview</h2><p>Proposed term loan: {_money(analysis.loan.new_loan_amount)} at {analysis.loan.annual_interest_rate*100:.2f}% for {analysis.loan.loan_term_years} years. Annual amortization: {analysis.loan.amortization_percentage*100:.1f}%. Minimum cash: {_money(analysis.loan.minimum_cash_requirement)}.</p>
<h2>Business and financial summary</h2><p>{escape(borrower.profile)} {escape(borrower.risk_summary)}</p>
<table><thead><tr><th>Opening projected metric</th><th>Result</th><th>Status</th></tr></thead><tbody>
<tr><td>Gross leverage</td><td>{_ratio(metrics['gross_leverage'].value)}</td><td>{metrics['gross_leverage'].status.value}</td></tr>
<tr><td>Net leverage</td><td>{_ratio(metrics['net_leverage'].value)}</td><td>{metrics['net_leverage'].status.value}</td></tr>
<tr><td>Interest coverage</td><td>{_ratio(metrics['interest_coverage'].value)}</td><td>{metrics['interest_coverage'].status.value}</td></tr>
<tr><td>DSCR</td><td>{_ratio(metrics['dscr'].value)}</td><td>{metrics['dscr'].status.value}</td></tr>
<tr><td>Minimum liquidity</td><td>{_money(metrics['minimum_liquidity'].value)}</td><td>{metrics['minimum_liquidity'].status.value}</td></tr></tbody></table>
<h2>Covenant analysis</h2><table><thead><tr><th>Covenant</th><th>Period</th><th>Calculated</th><th>Threshold</th><th>Status</th></tr></thead><tbody>{covenant_rows}</tbody></table>
<h2>Scenario analysis</h2><table><thead><tr><th>Scenario</th><th>First breach</th><th>Opening leverage</th></tr></thead><tbody>{scenario_rows}</tbody></table>
<h2>Positive factors</h2><ul>{lis(analysis.recommendation.positive_factors)}</ul><h2>Key risks</h2><ul>{lis(analysis.recommendation.key_risks)}</ul><h2>Proposed conditions</h2><ul>{lis(analysis.recommendation.proposed_conditions)}</ul>
<h2>Methodology and disclaimer</h2><p>Outputs are deterministic and rule-based. Ratio formulas, inputs, periods, results, and limitations are included in the accompanying analysis response. {escape(analysis.recommendation.disclaimer)}</p></body></html>"""


def generate_private_credit_memo_html(
    analysis: PrivateCreditAnalysisResponse, sensitivity: SensitivityResponse, analyst_name: str,
) -> str:
    borrower = analysis.borrower
    base = next(item for item in analysis.annual_scenarios if item.scenario.id == "base")
    severe = next((item for item in analysis.annual_scenarios if item.scenario.id == "severe"), base)
    base_quarterly = next(item for item in analysis.quarterly_scenarios if item.scenario.id == "base")
    opening_year = base.consolidated_debt_schedule[0].period
    base_metrics = base.ratios[opening_year]
    severe_metrics = severe.ratios[opening_year]
    senior_source = sum(t.new_borrowing for t in analysis.debt_structure.tranches
                        if t.tranche_type == DebtTrancheType.SENIOR_SECURED)
    revolver_source = sum(t.new_borrowing for t in analysis.debt_structure.tranches
                          if t.tranche_type == DebtTrancheType.REVOLVER)
    subordinated_source = sum(t.new_borrowing for t in analysis.debt_structure.tranches
                              if t.tranche_type == DebtTrancheType.SUBORDINATED)
    refinance_use = sum(t.refinancing_amount for t in analysis.debt_structure.tranches)
    source_rows = [
        ("New senior debt", senior_source), ("Revolver draw", revolver_source),
        ("Subordinated debt", subordinated_source),
        ("Sponsor equity contribution", analysis.sources_uses.sponsor_equity_contribution),
        ("Cash on balance sheet", analysis.sources_uses.cash_on_balance_sheet),
    ]
    use_rows = [
        ("Refinance existing debt", refinance_use),
        ("Transaction fees", analysis.sources_uses.transaction_fees),
        ("Cash to balance sheet", analysis.sources_uses.cash_to_balance_sheet),
        ("Acquisition purchase price", analysis.sources_uses.acquisition_purchase_price),
        ("General corporate purposes", analysis.sources_uses.general_corporate_purposes),
    ]
    total_sources = sum(value for _, value in source_rows)
    total_uses = sum(value for _, value in use_rows)
    sources_uses_rows = "".join(
        f"<tr><td>{escape(source)}</td><td>{_money(source_value)}</td>"
        f"<td>{escape(use)}</td><td>{_money(use_value)}</td></tr>"
        for (source, source_value), (use, use_value) in zip(source_rows, use_rows)
    )
    historical = [period for period in borrower.periods if period.period_type.value == "historical"]
    projected = [period for period in borrower.periods if period.period_type.value == "projected"]
    financial_rows = lambda periods: "".join(
        f"<tr><td>{p.fiscal_year}</td><td>{_money(p.revenue)}</td><td>{_money(p.ebitda)}</td>"
        f"<td>{_money(p.free_cash_flow)}</td><td>{_money(p.total_debt)}</td></tr>" for p in periods
    )
    tranche_rows = "".join(
        f"<tr><td>{escape(t.name)}</td><td>{escape(t.tranche_type.value.replace('_', ' '))}</td>"
        f"<td>{_money(t.opening_balance if t.tranche_type != DebtTrancheType.REVOLVER else t.drawn_amount)}</td>"
        f"<td>{_money(t.new_borrowing)}</td><td>{t.interest_rate*100:.2f}%</td>"
        f"<td>{t.amortization_percentage*100:.1f}%</td><td>{escape(t.maturity_period)}</td></tr>"
        for t in analysis.debt_structure.tranches
    )
    covenant_rows = "".join(
        f"<tr><td>{escape(c.covenant_name)}</td><td>{c.threshold:.2f}</td>"
        f"<td>{c.calculated_value if c.calculated_value is not None else 'N/M'}</td>"
        f"<td class='{c.status}'>{c.status.upper()}</td></tr>"
        for c in base.covenant_results if c.fiscal_year == opening_year
    )
    failed_cells = [cell for cell in sensitivity.cells if cell.covenant_status == "fail"]
    worst_cell = sensitivity.cells[-1]
    audit_rows = ""
    audit_explanation = ""
    if analysis.audit_trail:
        triggered = [rule for rule in analysis.audit_trail.rules if rule.triggered]
        audit_rows = "".join(
            f"<tr><td>{escape(rule.rule_id)}</td><td>{escape(rule.rule)}</td>"
            f"<td>{escape(rule.impact)}</td><td>{escape(rule.related_output)}</td></tr>"
            for rule in triggered
        ) or "<tr><td colspan='4'>No adverse recommendation rule triggered.</td></tr>"
        audit_explanation = escape(analysis.audit_trail.human_readable_explanation)
    def lis(items: list[str], fallback: str) -> str:
        return "".join(f"<li>{escape(item)}</li>" for item in items) or f"<li>{escape(fallback)}</li>"
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>CovenantIQ IC Memo: {escape(borrower.name)}</title>
<style>@page{{size:A4;margin:14mm 13mm}}*{{box-sizing:border-box}}body{{font:13px Arial,Helvetica,sans-serif;color:#17212b;margin:38px;line-height:1.48;-webkit-print-color-adjust:exact;print-color-adjust:exact}}header{{border-bottom:3px solid #173c47;padding-bottom:16px}}h1{{font-size:27px;margin:2px 0}}h2{{font-size:15px;margin-top:25px;border-bottom:1px solid #aeb9bb;padding-bottom:5px;page-break-after:avoid;break-after:avoid}}p,li{{orphans:3;widows:3}}.meta{{color:#59656d;font-size:11px}}.verdict{{border-left:5px solid #2f6f67;background:#eef3f1;padding:13px;margin:20px 0}}table{{width:100%;border-collapse:collapse;margin:8px 0 15px}}thead{{display:table-header-group}}tr{{break-inside:avoid}}th,td{{padding:7px;border-bottom:1px solid #d9dfe2;text-align:right;vertical-align:top}}th:first-child,td:first-child{{text-align:left}}.fail{{color:#9a342d;font-weight:bold}}.pass{{color:#286557;font-weight:bold}}.two{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}.small{{font-size:11px;color:#59656d}}.audit{{border:1px solid #aeb9bb;padding:12px;margin:14px 0 20px}}.audit h3{{font-size:12px;margin:0 0 8px;text-transform:uppercase;letter-spacing:.06em}}@media print{{body{{margin:0}}h2{{break-after:avoid}}table{{break-inside:auto}}.two{{display:grid}}.verdict,.audit{{break-inside:avoid}}}}</style></head><body>
<header><div class='meta'>COVENANTIQ | INVESTMENT COMMITTEE MEMORANDUM</div><h1>{escape(borrower.name)}</h1><div class='meta'>Prepared {date.today().isoformat()} by {escape(analyst_name)} | {escape(borrower.units)}</div></header>
<h2>1. Executive recommendation</h2><section class='verdict'><strong>{analysis.recommendation.recommendation}</strong> | Risk grade {analysis.recommendation.risk_grade} | {analysis.recommendation.confidence_level} confidence<br>{escape(' '.join(analysis.recommendation.primary_reasons))}</section><section class='audit'><h3>Decision audit summary</h3><p>{audit_explanation}</p><table><thead><tr><th>Rule</th><th>Trigger</th><th>Impact</th><th>Decision effect</th></tr></thead><tbody>{audit_rows}</tbody></table></section>
<h2>2. Transaction overview</h2><p>{len(analysis.debt_structure.tranches)}-tranche financing with {_money(base.consolidated_debt_schedule[0].closing_balance)} opening projected debt, {base.consolidated_debt_schedule[0].weighted_average_cash_interest_rate or 0:.2%} weighted average cash rate, and {_money(analysis.debt_structure.minimum_cash_requirement)} minimum cash.</p>
<h2>3. Sources and uses</h2><table><thead><tr><th>Sources</th><th>Amount</th><th>Uses</th><th>Amount</th></tr></thead><tbody>{sources_uses_rows}<tr><th>Total sources</th><th>{_money(total_sources)}</th><th>Total uses</th><th>{_money(total_uses)}</th></tr><tr><td>Funding surplus / (shortfall)</td><td>{_money(total_sources-total_uses)}</td><td></td><td></td></tr></tbody></table>
<h2>4. Borrower overview</h2><p>{escape(borrower.profile)} {escape(borrower.risk_summary)}</p>
<h2>5. Historical financial performance</h2><table><thead><tr><th>Period</th><th>Revenue</th><th>EBITDA</th><th>FCF</th><th>Debt</th></tr></thead><tbody>{financial_rows(historical)}</tbody></table>
<h2>6. Projected financial performance</h2><table><thead><tr><th>Period</th><th>Revenue</th><th>EBITDA</th><th>FCF</th><th>Debt</th></tr></thead><tbody>{financial_rows(projected)}</tbody></table>
<h2>7. Debt structure</h2><table><thead><tr><th>Tranche</th><th>Type</th><th>Opening</th><th>New</th><th>Rate</th><th>Amort.</th><th>Maturity</th></tr></thead><tbody>{tranche_rows}</tbody></table>
<h2>8. Covenant package</h2><table><thead><tr><th>Covenant</th><th>Threshold</th><th>{opening_year}</th><th>Status</th></tr></thead><tbody>{covenant_rows}</tbody></table><p class='small'>First quarterly base-case breach: {escape(base_quarterly.first_breach_period or 'No modeled breach')}.</p>
<div class='two'><section><h2>9. Base-case credit metrics</h2><table><tbody><tr><td>Net leverage</td><td>{_ratio(base_metrics['net_leverage'].value)}</td></tr><tr><td>Interest coverage</td><td>{_ratio(base_metrics['interest_coverage'].value)}</td></tr><tr><td>DSCR</td><td>{_ratio(base_metrics['dscr'].value)}</td></tr><tr><td>Liquidity</td><td>{_money(base_metrics['minimum_liquidity'].value)}</td></tr></tbody></table></section>
<section><h2>10. Downside-case credit metrics</h2><table><tbody><tr><td>Net leverage</td><td>{_ratio(severe_metrics['net_leverage'].value)}</td></tr><tr><td>Interest coverage</td><td>{_ratio(severe_metrics['interest_coverage'].value)}</td></tr><tr><td>DSCR</td><td>{_ratio(severe_metrics['dscr'].value)}</td></tr><tr><td>Liquidity</td><td>{_money(severe_metrics['minimum_liquidity'].value)}</td></tr></tbody></table></section></div>
<h2>11. Sensitivity analysis summary</h2><p>{len(failed_cells)} of {len(sensitivity.cells)} grid cells produce a covenant failure. At the most severe tested cell ({worst_cell.revenue_shock:.0%} revenue, {worst_cell.margin_shock_bps} bps margin), net leverage is {_ratio(worst_cell.net_leverage)}, coverage is {_ratio(worst_cell.interest_coverage)}, and first breach is {escape(worst_cell.first_breach_period or 'not identified')}.</p>
<div class='two'><section><h2>12. Key risks</h2><ul>{lis(analysis.recommendation.key_risks, 'No additional rule-generated risk.')}</ul></section><section><h2>13. Mitigants</h2><ul>{lis(analysis.recommendation.positive_factors, 'No additional rule-generated mitigant.')}</ul></section></div>
<h2>14. Proposed conditions precedent</h2><ul>{lis(analysis.recommendation.proposed_conditions, 'No additional rule-generated condition precedent.')}</ul>
<h2>15. Monitoring recommendations</h2><ul><li>Quarterly compliance certificates using the modeled covenant definitions.</li><li>Monthly liquidity reporting when headroom is below 15%.</li><li>Updated 13-week cash flow forecast following any covenant failure.</li></ul>
<h2>16. Methodology and limitations disclaimer</h2><p>Outputs are deterministic and rule-based. Quarterly projections use simplified phasing of annual borrower data. Revolver mechanics do not include a borrowing base or intra-quarter draws. {escape(analysis.recommendation.disclaimer)}</p></body></html>"""
