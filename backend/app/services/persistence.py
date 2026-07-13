from __future__ import annotations

import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.models.domain import (
    PrivateCreditAnalysisRequest, SavedAnalysisCreate, SavedAnalysisRecord, SavedAnalysisSummary,
)
from app.services.private_credit_service import analyze_private_credit


def database_path() -> Path:
    configured = os.environ.get("COVENANTIQ_DB_PATH")
    return Path(configured) if configured else Path(__file__).resolve().parents[1] / "data" / "covenantiq.db"


def connect() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_database() -> None:
    with connect() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                borrower_id TEXT NOT NULL,
                analysis_name TEXT NOT NULL,
                request_json TEXT NOT NULL,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                latest_recommendation TEXT NOT NULL,
                risk_grade TEXT NOT NULL,
                first_breach_period TEXT
            )
        """)


def create_saved_analysis(payload: SavedAnalysisCreate) -> SavedAnalysisRecord:
    init_database()
    request = PrivateCreditAnalysisRequest(**payload.model_dump(exclude={"analysis_name"}))
    analysis = analyze_private_credit(request)
    analysis_id = str(uuid4())
    created_at = datetime.now(UTC).isoformat()
    first_breach = next(
        (scenario.first_breach_period for scenario in analysis.quarterly_scenarios
         if scenario.first_breach_period), None
    )
    with connect() as connection:
        connection.execute(
            """INSERT INTO analyses
            (id, borrower_id, analysis_name, request_json, response_json, created_at,
             latest_recommendation, risk_grade, first_breach_period)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                analysis_id, payload.borrower_id, payload.analysis_name,
                request.model_dump_json(), analysis.model_dump_json(), created_at,
                analysis.recommendation.recommendation, analysis.recommendation.risk_grade,
                first_breach,
            ),
        )
    return SavedAnalysisRecord(
        id=analysis_id, borrower_id=payload.borrower_id, analysis_name=payload.analysis_name,
        created_at=created_at, latest_recommendation=analysis.recommendation.recommendation,
        risk_grade=analysis.recommendation.risk_grade, first_breach_period=first_breach,
        request=request, analysis=analysis,
    )


def list_saved_analyses() -> list[SavedAnalysisSummary]:
    init_database()
    with connect() as connection:
        rows = connection.execute(
            """SELECT id, borrower_id, analysis_name, created_at, latest_recommendation,
               risk_grade, first_breach_period FROM analyses ORDER BY created_at DESC"""
        ).fetchall()
    return [SavedAnalysisSummary(**dict(row)) for row in rows]


def get_saved_analysis(analysis_id: str) -> SavedAnalysisRecord:
    init_database()
    with connect() as connection:
        row = connection.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    if row is None:
        raise KeyError(f"Unknown analysis '{analysis_id}'")
    return SavedAnalysisRecord(
        id=row["id"], borrower_id=row["borrower_id"], analysis_name=row["analysis_name"],
        created_at=row["created_at"], latest_recommendation=row["latest_recommendation"],
        risk_grade=row["risk_grade"], first_breach_period=row["first_breach_period"],
        request=PrivateCreditAnalysisRequest.model_validate_json(row["request_json"]),
        analysis=json.loads(row["response_json"]),
    )


def delete_saved_analysis(analysis_id: str) -> bool:
    init_database()
    with connect() as connection:
        cursor = connection.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    return cursor.rowcount > 0
