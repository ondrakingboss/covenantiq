from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PeriodType(str, Enum):
    HISTORICAL = "historical"
    PROJECTED = "projected"


class FinancialPeriod(StrictModel):
    fiscal_year: str
    period_type: PeriodType
    revenue: float
    ebitda: float
    ebit: float
    interest_expense: float
    taxes: float
    net_income: float
    cash: float
    accounts_receivable: float
    inventory: float
    current_assets: float
    current_liabilities: float
    total_debt: float
    lease_liabilities: float
    operating_cash_flow: float
    capital_expenditure: float = Field(ge=0)
    free_cash_flow: float
    mandatory_debt_amortization: float = Field(ge=0)


class Borrower(StrictModel):
    id: str
    name: str
    industry: str
    profile: str
    risk_summary: str
    units: str = "USD millions"
    periods: list[FinancialPeriod] = Field(min_length=6, max_length=6)


class LoanConfig(StrictModel):
    new_loan_amount: float = Field(gt=0, le=10_000)
    annual_interest_rate: float = Field(ge=0, le=0.5)
    loan_term_years: int = Field(ge=1, le=15)
    amortization_percentage: float = Field(ge=0, le=1)
    upfront_fees: float = Field(ge=0, le=1_000)
    minimum_cash_requirement: float = Field(ge=0)
    existing_debt_refinanced_amount: float = Field(ge=0)
    revolving_credit_commitment: float = Field(default=0, ge=0)

    @field_validator("existing_debt_refinanced_amount")
    @classmethod
    def sensible_refinancing(cls, value: float) -> float:
        return round(value, 6)


class CovenantType(str, Enum):
    MAX_GROSS_LEVERAGE = "maximum_gross_leverage"
    MAX_NET_LEVERAGE = "maximum_net_leverage"
    MIN_INTEREST_COVERAGE = "minimum_interest_coverage"
    MIN_DSCR = "minimum_dscr"
    MIN_FIXED_CHARGE_COVERAGE = "minimum_fixed_charge_coverage"
    MIN_LIQUIDITY = "minimum_liquidity"
    MAX_CAPEX = "maximum_annual_capital_expenditure"


class CovenantDefinition(StrictModel):
    name: str = Field(min_length=2, max_length=80)
    covenant_type: CovenantType
    threshold: float


class ScenarioDefinition(StrictModel):
    id: str
    name: str
    revenue_change: float = Field(ge=-0.9, le=1)
    ebitda_margin_change_bps: int = Field(ge=-5000, le=5000)
    interest_rate_change_bps: int = Field(ge=-1000, le=5000)
    receivable_days_increase: float = Field(default=0, ge=0, le=365)
    inventory_days_increase: float = Field(default=0, ge=0, le=365)
    working_capital_outflow_pct_revenue: float = Field(default=0, ge=0, le=0.5)


class MetricStatus(str, Enum):
    VALID = "valid"
    NOT_MEANINGFUL = "not_meaningful"
    UNAVAILABLE = "unavailable"


class MetricResult(StrictModel):
    metric: str
    value: float | None
    status: MetricStatus
    formula: str
    inputs: dict[str, float | None]
    source_periods: list[str]
    interpretation: str
    limitations: list[str] = []


class DebtScheduleRow(StrictModel):
    fiscal_year: str
    opening_balance: float
    new_borrowing: float
    mandatory_amortization: float
    optional_repayment: float
    closing_balance: float
    cash_interest: float
    effective_interest: float


class CovenantTestResult(StrictModel):
    covenant_name: str
    covenant_type: CovenantType
    fiscal_year: str
    scenario: str
    calculated_value: float | None
    metric_status: MetricStatus
    threshold: float
    status: Literal["pass", "fail", "not_tested"]
    absolute_headroom: float | None
    percentage_headroom: float | None
    first_breach_period: str | None = None
    severity: Literal["none", "watch", "moderate", "severe", "not_tested"]


class RecommendationResult(StrictModel):
    recommendation: Literal[
        "Approve", "Approve with conditions", "Further diligence required", "Decline"
    ]
    risk_grade: str
    confidence_level: Literal["High", "Moderate", "Low"]
    primary_reasons: list[str]
    positive_factors: list[str]
    key_risks: list[str]
    proposed_conditions: list[str]
    calculation_references: list[str]
    disclaimer: str


class ScenarioResult(StrictModel):
    scenario: ScenarioDefinition
    periods: list[FinancialPeriod]
    debt_schedule: list[DebtScheduleRow]
    ratios: dict[str, dict[str, MetricResult]]
    covenant_results: list[CovenantTestResult]
    first_breach_period: str | None


class AnalysisRequest(StrictModel):
    borrower_id: str
    loan: LoanConfig
    covenants: list[CovenantDefinition] = Field(default_factory=list)
    scenario_ids: list[str] = Field(default_factory=lambda: ["base", "mild", "severe"])


class AnalysisResponse(StrictModel):
    borrower: Borrower
    loan: LoanConfig
    scenarios: list[ScenarioResult]
    recommendation: RecommendationResult
    assumptions: list[str]


class ScenarioRunRequest(AnalysisRequest):
    pass


class CovenantTestRequest(StrictModel):
    borrower_id: str
    loan: LoanConfig
    covenants: list[CovenantDefinition]
    scenario_id: str = "base"


class MemoRequest(AnalysisRequest):
    analyst_name: str = Field(default="CovenantIQ Credit Desk", max_length=80)


class MemoResponse(StrictModel):
    title: str
    html: str
    analysis: AnalysisResponse


class DebtTrancheType(str, Enum):
    REVOLVER = "revolver"
    SENIOR_SECURED = "senior_secured_term_loan"
    SUBORDINATED = "subordinated_debt"


class DebtTrancheConfig(StrictModel):
    id: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=2, max_length=80)
    tranche_type: DebtTrancheType
    opening_balance: float = Field(default=0, ge=0)
    new_borrowing: float = Field(default=0, ge=0)
    refinancing_amount: float = Field(default=0, ge=0)
    interest_rate: float = Field(ge=0, le=0.5)
    amortization_percentage: float = Field(default=0, ge=0, le=1)
    maturity_period: str = Field(default="FY2030E", min_length=6, max_length=12)
    cash_pay_interest: bool = True
    pik_interest: bool = False
    commitment_amount: float = Field(default=0, ge=0)
    drawn_amount: float = Field(default=0, ge=0)
    commitment_fee: float = Field(default=0, ge=0, le=0.1)


class DebtStructureConfig(StrictModel):
    tranches: list[DebtTrancheConfig] = Field(min_length=1, max_length=12)
    minimum_cash_requirement: float = Field(default=0, ge=0)
    excess_cash_flow_sweep_percentage: float = Field(default=0.25, ge=0, le=1)


class SourcesUses(StrictModel):
    sponsor_equity_contribution: float = Field(default=0, ge=0)
    cash_on_balance_sheet: float = Field(default=0, ge=0)
    transaction_fees: float = Field(default=0, ge=0)
    cash_to_balance_sheet: float = Field(default=0, ge=0)
    acquisition_purchase_price: float = Field(default=0, ge=0)
    general_corporate_purposes: float = Field(default=0, ge=0)


class TrancheScheduleRow(StrictModel):
    period: str
    tranche_id: str
    tranche_name: str
    tranche_type: DebtTrancheType
    opening_balance: float
    new_borrowing: float
    refinancing: float
    mandatory_amortization: float
    optional_repayment: float
    pik_accrual: float
    closing_balance: float
    cash_interest: float
    commitment_fee: float
    undrawn_amount: float


class ConsolidatedDebtScheduleRow(StrictModel):
    period: str
    opening_balance: float
    new_borrowing: float
    refinancing: float
    mandatory_amortization: float
    optional_repayment: float
    pik_accrual: float
    closing_balance: float
    cash_interest: float
    commitment_fees: float
    total_cash_interest: float
    weighted_average_cash_interest_rate: float | None
    revolver_availability: float
    total_liquidity: float


class QuarterlyFinancialPeriod(StrictModel):
    period: str
    fiscal_year: str
    revenue: float
    ebitda: float
    cash_interest: float
    capital_expenditure: float
    operating_cash_flow: float
    free_cash_flow: float
    ending_cash: float
    total_debt: float
    net_debt: float
    mandatory_amortization: float
    revolver_availability: float
    total_liquidity: float


class MultiScenarioResult(StrictModel):
    scenario: ScenarioDefinition
    periods: list[FinancialPeriod]
    consolidated_debt_schedule: list[ConsolidatedDebtScheduleRow]
    tranche_schedules: dict[str, list[TrancheScheduleRow]]
    ratios: dict[str, dict[str, MetricResult]]
    covenant_results: list[CovenantTestResult]
    first_breach_period: str | None


class QuarterlyScenarioResult(StrictModel):
    scenario: ScenarioDefinition
    periods: list[QuarterlyFinancialPeriod]
    consolidated_debt_schedule: list[ConsolidatedDebtScheduleRow]
    tranche_schedules: dict[str, list[TrancheScheduleRow]]
    ratios: dict[str, dict[str, MetricResult]]
    covenant_results: list[CovenantTestResult]
    first_breach_period: str | None


class PrivateCreditAnalysisRequest(StrictModel):
    borrower_id: str
    debt_structure: DebtStructureConfig
    covenants: list[CovenantDefinition] = Field(default_factory=list)
    scenario_ids: list[str] = Field(default_factory=lambda: ["base", "mild", "severe"])
    sources_uses: SourcesUses = Field(default_factory=SourcesUses)


class AuditEvidence(StrictModel):
    label: str
    actual_value: float | None
    operator: Literal["<=", ">=", "<", ">", "="]
    threshold: float | None
    unit: Literal["x", "USD millions", "count", "status"]
    period: str
    scenario: str
    status: Literal["supports", "adverse", "neutral", "unavailable"]
    comparison: str
    calculation_reference: str


class AuditRuleTrace(StrictModel):
    rule_id: str
    rule: str
    triggered: bool
    impact: Literal["Low", "Moderate", "High", "Critical"]
    evidence: list[AuditEvidence]
    related_output: str
    explanation: str
    calculation_references: list[str]


class AuditTrail(StrictModel):
    final_recommendation: str
    risk_grade: str
    confidence_level: str
    rules: list[AuditRuleTrace]
    supporting_metrics: list[AuditEvidence]
    covenant_breaches: list[CovenantTestResult]
    scenario_drivers: list[str]
    first_breach_period: str | None
    human_readable_explanation: str
    calculation_references: list[str]


class PrivateCreditAnalysisResponse(StrictModel):
    borrower: Borrower
    debt_structure: DebtStructureConfig
    annual_scenarios: list[MultiScenarioResult]
    quarterly_scenarios: list[QuarterlyScenarioResult]
    recommendation: RecommendationResult
    sources_uses: SourcesUses
    assumptions: list[str]
    audit_trail: AuditTrail | None = None


class SensitivityRequest(StrictModel):
    borrower_id: str
    debt_structure: DebtStructureConfig
    covenants: list[CovenantDefinition] = Field(default_factory=list)
    revenue_shocks: list[float] = Field(default_factory=lambda: [0, -0.05, -0.10, -0.15, -0.20, -0.25, -0.30])
    margin_shocks_bps: list[int] = Field(default_factory=lambda: [0, -100, -200, -300, -500, -700])


class SensitivityCell(StrictModel):
    revenue_shock: float
    margin_shock_bps: int
    net_leverage: float | None
    interest_coverage: float | None
    dscr: float | None
    minimum_liquidity: float | None
    covenant_status: Literal["pass", "fail", "not_tested"]
    first_breach_period: str | None


class SensitivityResponse(StrictModel):
    borrower_id: str
    revenue_shocks: list[float]
    margin_shocks_bps: list[int]
    cells: list[SensitivityCell]


class PrivateCreditMemoRequest(PrivateCreditAnalysisRequest):
    analyst_name: str = Field(default="CovenantIQ Private Credit", max_length=80)


class PrivateCreditMemoResponse(StrictModel):
    title: str
    html: str
    analysis: PrivateCreditAnalysisResponse
    sensitivity: SensitivityResponse


class SavedAnalysisCreate(PrivateCreditAnalysisRequest):
    analysis_name: str = Field(min_length=2, max_length=100)


class SavedAnalysisSummary(StrictModel):
    id: str
    borrower_id: str
    analysis_name: str
    created_at: str
    latest_recommendation: str
    risk_grade: str
    first_breach_period: str | None


class SavedAnalysisRecord(SavedAnalysisSummary):
    request: PrivateCreditAnalysisRequest
    analysis: PrivateCreditAnalysisResponse


class SavedComparisonRequest(StrictModel):
    analysis_ids: list[str] = Field(min_length=2, max_length=4)


class DealComparisonEntry(StrictModel):
    analysis_id: str
    structure_name: str
    borrower_id: str
    recommendation: str
    risk_grade: str
    net_leverage: float | None
    gross_leverage: float | None
    interest_coverage: float | None
    dscr: float | None
    minimum_liquidity: float | None
    first_breach_period: str | None
    total_debt: float
    sponsor_equity: float
    weighted_average_cash_interest_rate: float | None
    covenant_pass_count: int
    covenant_fail_count: int
    covenant_not_tested_count: int
    safety_score: float
    safety_factors: list[str]


class DealComparisonResponse(StrictModel):
    borrower_id: str
    entries: list[DealComparisonEntry]
    safer_analysis_id: str
    safer_structure_name: str
    rationale: list[str]
    methodology: list[str]


class GuidedDemo(StrictModel):
    id: str
    title: str
    borrower_id: str | None = None
    route: str
    explanation: str
    learning_point: str
    talking_points: list[str]
    expected_outcome: str
