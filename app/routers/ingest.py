# app/routers/ingest.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 1) Contrato de entrada (batch de lecturas)
from ..schemas import IngestBatch

# 2) DB: dependencia para obtener Session por petición
from ..db import get_db

# 3) CRUD que acabamos de definir (insertar lote)
from ..crud import insert_readings

router = APIRouter(tags=["ingest"])

@router.post("/ingest", summary="Ingestar lecturas de sensores (persistencia en SQLite)")
def ingest(payload: IngestBatch, db: Session = Depends(get_db)) -> dict:
    """
    Recibe lecturas, las valida y las inserta en la base de datos (histórico).
    Devuelve el número de filas insertadas.
    """
    inserted = insert_readings(db, payload.readings)
    return {"inserted": inserted}