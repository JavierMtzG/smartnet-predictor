# 1) Tipos y utilidades de typing y fechas.
from typing import List
from datetime import datetime, timezone

# 2) Pydantic schemas (entrada/salida).
from .schemas import ReadingIn, StatusItem

# 3) ORM: Session (conexión viva) y nuestro modelo.
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from .models import SensorReading

def insert_readings(db: Session, readings: List[ReadingIn]) -> int:
    """
    Inserta un lote de lecturas en la tabla SensorReading.
    Devuelve el número de filas insertadas.
    """
    # 4) Transformamos `ReadingIn` (Pydantic) a objetos ORM.
    rows = []
    for r in readings:
        rows.append(
            SensorReading(
                ts=r.ts or datetime.now(timezone.utc),
                node_id=r.node_id,
                latency_ms=r.latency_ms,
                jitter_ms=r.jitter_ms,
                rssi_dbm=r.rssi_dbm,
                noise_dbm=r.noise_dbm,
                failure=r.failure,
            )
        )

    # 5) Añadimos todas las filas en bloque y confirmamos.
    db.add_all(rows)
    db.commit()

    return len(rows)


def latest_status(db: Session) -> List[StatusItem]:
    """
    Devuelve el último registro por node_id como lista de StatusItem.
    Implementación: subconsulta con MAX(ts) y join.
    """
    # 6) Subconsulta: para cada node_id, el timestamp máximo (el más reciente).
    subq = (
        select(
            SensorReading.node_id.label("node_id"),
            func.max(SensorReading.ts).label("max_ts"),
        )
        .group_by(SensorReading.node_id)
        .subquery()
    )

    # 7) Join con la tabla real para recuperar el resto de columnas
    #    de las filas cuyo ts == max_ts para cada node_id.
    stmt = (
        select(SensorReading)
        .join(
            subq,
            and_(
                SensorReading.node_id == subq.c.node_id,
                SensorReading.ts == subq.c.max_ts,
            ),
        )
        .order_by(SensorReading.node_id.asc())
    )

    # 8) Ejecutamos y convertimos a StatusItem (contrato de salida).
    results = db.execute(stmt).scalars().all()

    return [
        StatusItem(
            node_id=row.node_id,
            ts=row.ts,
            latency_ms=row.latency_ms,
            jitter_ms=row.jitter_ms,
            rssi_dbm=row.rssi_dbm,
            noise_dbm=row.noise_dbm,
        )
        for row in results
    ]