# app/routers/status.py
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 1) Contrato de salida
from ..schemas import StatusItem

# 2) DB: dependencia para obtener Session
from ..db import get_db

# 3) CRUD: leer el último estado por nodo
from ..crud import latest_status

router = APIRouter(tags=["status"])

@router.get("/status", response_model=List[StatusItem], summary="Último estado por nodo (desde BD)")
def status(db: Session = Depends(get_db)) -> List[StatusItem]:
    """
    Devuelve el último registro por nodo desde la base de datos.
    """
    return latest_status(db)
