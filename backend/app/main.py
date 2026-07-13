from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import cors_origins
from app.routers.api import router
from app.services.persistence import init_database


app = FastAPI(
    title="CovenantIQ API", version="1.0.0",
    description="Deterministic corporate credit analysis and covenant stress testing.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.include_router(router)
init_database()
