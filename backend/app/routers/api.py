from fastapi import APIRouter, HTTPException, Response, status

from app.models.domain import (
    AnalysisRequest, AnalysisResponse, Borrower, CovenantTestRequest, MemoRequest, MemoResponse,
    DealComparisonResponse, GuidedDemo,
    PrivateCreditAnalysisRequest, PrivateCreditAnalysisResponse, PrivateCreditMemoRequest,
    PrivateCreditMemoResponse, SavedAnalysisCreate, SavedAnalysisRecord, SavedAnalysisSummary,
    SavedComparisonRequest,
    ScenarioResult, ScenarioRunRequest, SensitivityRequest, SensitivityResponse,
)
from app.services.analysis_service import analyze
from app.services.comparison_engine import compare_saved_analyses
from app.services.financial_engine import get_borrower, load_borrowers
from app.services.guided_demo_service import get_guided_demos
from app.services.memo_engine import generate_memo_html, generate_private_credit_memo_html
from app.services.persistence import (
    create_saved_analysis, delete_saved_analysis, get_saved_analysis, list_saved_analyses,
)
from app.services.private_credit_service import analyze_private_credit
from app.services.sensitivity_engine import run_sensitivity


router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "covenantiq-api", "calculation_mode": "deterministic"}


@router.get("/borrowers", response_model=list[Borrower])
def borrowers() -> list[Borrower]:
    return load_borrowers()


@router.get("/borrowers/{borrower_id}", response_model=Borrower)
def borrower(borrower_id: str) -> Borrower:
    try:
        return get_borrower(borrower_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/guided-demos", response_model=list[GuidedDemo])
def guided_demos() -> list[GuidedDemo]:
    return get_guided_demos()


def _analyze_or_404(request: AnalysisRequest) -> AnalysisResponse:
    try:
        return analyze(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/loans/analyze", response_model=AnalysisResponse)
def analyze_loan(request: AnalysisRequest) -> AnalysisResponse:
    return _analyze_or_404(request)


@router.post("/scenarios/run", response_model=list[ScenarioResult])
def run_scenarios(request: ScenarioRunRequest) -> list[ScenarioResult]:
    return _analyze_or_404(request).scenarios


@router.post("/covenants/test")
def test_covenants_endpoint(request: CovenantTestRequest):
    analysis = _analyze_or_404(AnalysisRequest(
        borrower_id=request.borrower_id, loan=request.loan, covenants=request.covenants,
        scenario_ids=[request.scenario_id],
    ))
    return next(s.covenant_results for s in analysis.scenarios if s.scenario.id == request.scenario_id)


@router.post("/credit-memo/generate", response_model=MemoResponse)
def generate_credit_memo(request: MemoRequest) -> MemoResponse:
    analysis = _analyze_or_404(AnalysisRequest(**request.model_dump(exclude={"analyst_name"})))
    return MemoResponse(
        title=f"CovenantIQ Credit Memo: {analysis.borrower.name}",
        html=generate_memo_html(analysis, request.analyst_name), analysis=analysis,
    )


@router.post("/private-credit/analyze", response_model=PrivateCreditAnalysisResponse)
def analyze_private_credit_endpoint(request: PrivateCreditAnalysisRequest) -> PrivateCreditAnalysisResponse:
    try:
        return analyze_private_credit(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sensitivity/run", response_model=SensitivityResponse)
def sensitivity_endpoint(request: SensitivityRequest) -> SensitivityResponse:
    try:
        return run_sensitivity(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/credit-memo/generate-v2", response_model=PrivateCreditMemoResponse)
def generate_private_credit_memo(request: PrivateCreditMemoRequest) -> PrivateCreditMemoResponse:
    analysis_request = PrivateCreditAnalysisRequest(**request.model_dump(exclude={"analyst_name"}))
    try:
        analysis = analyze_private_credit(analysis_request)
        sensitivity = run_sensitivity(SensitivityRequest(
            borrower_id=request.borrower_id, debt_structure=request.debt_structure,
            covenants=request.covenants,
        ))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PrivateCreditMemoResponse(
        title=f"CovenantIQ IC Memo: {analysis.borrower.name}",
        html=generate_private_credit_memo_html(analysis, sensitivity, request.analyst_name),
        analysis=analysis, sensitivity=sensitivity,
    )


@router.post("/analyses", response_model=SavedAnalysisRecord, status_code=status.HTTP_201_CREATED)
def create_analysis(request: SavedAnalysisCreate) -> SavedAnalysisRecord:
    try:
        return create_saved_analysis(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/analyses", response_model=list[SavedAnalysisSummary])
def saved_analyses() -> list[SavedAnalysisSummary]:
    return list_saved_analyses()


@router.post("/analyses/compare", response_model=DealComparisonResponse)
def compare_analyses(request: SavedComparisonRequest) -> DealComparisonResponse:
    try:
        records = [get_saved_analysis(analysis_id) for analysis_id in request.analysis_ids]
        return compare_saved_analyses(records)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/analyses/{analysis_id}", response_model=SavedAnalysisRecord)
def saved_analysis(analysis_id: str) -> SavedAnalysisRecord:
    try:
        return get_saved_analysis(analysis_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/analyses/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_saved_analysis(analysis_id: str) -> Response:
    if not delete_saved_analysis(analysis_id):
        raise HTTPException(status_code=404, detail=f"Unknown analysis '{analysis_id}'")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
