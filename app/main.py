# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timezone

# 1) Importamos engine y Base para poder crear las tablas
from .db import engine
from .models import Base

# 2) Routers (ya actualizados a BD)
from .routers import ingest, status

app = FastAPI(
    title="SmartNet Predictor",
    version="0.3.0",
    description="API de sensores inteligentes para predicción de fallos en red."
)

class HealthResponse(BaseModel):
    ok: bool
    service: str
    version: str
    time_utc: datetime

@app.on_event("startup")
def on_startup():
    """
    Hook de arranque:
    - Crea las tablas si no existen (idempotente).
    """
    Base.metadata.create_all(bind=engine)

@app.get("/", summary="Welcome endpoint")
def root():
    return {"message": "Welcome to SmartNet Predictor — DB-backed API (SQLite)"}

@app.get("/health", response_model=HealthResponse, summary="Health check del servicio")
def health() -> HealthResponse:
    return HealthResponse(
        ok=True,
        service="smartnet-predictor",
        version=app.version,
        time_utc=datetime.now(timezone.utc),
    )

# Montaje de routers (API modular)
app.include_router(ingest.router)
app.include_router(status.router)
