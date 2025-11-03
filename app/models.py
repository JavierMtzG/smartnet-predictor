# 1) Columnas y tipos para definir el esquema de la tabla.
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Index
from sqlalchemy.sql import func

# 2) Base heredada de db.py (padre de todos los modelos).
from .db import Base

class SensorReading(Base):
    """
    Tabla que guarda el histórico de lecturas de sensores.
    Cada POST /ingest inserta filas nuevas aquí.
    """
    # 3) Nombre de la tabla en la BD.
    __tablename__ = "sensor_readings"

    # 4) Columnas:
    id = Column(Integer, primary_key=True, index=True)   # id autoincremental
    ts = Column(DateTime(timezone=True), nullable=False) # timestamp (UTC-aware)
    node_id = Column(String(64), nullable=False, index=True)  # nodo/antena
    latency_ms = Column(Float, nullable=False)           # latencia (ms, >= 0)
    jitter_ms = Column(Float, nullable=False)            # jitter (ms, >= 0)
    rssi_dbm = Column(Float, nullable=False)             # RSSI en dBm
    noise_dbm = Column(Float, nullable=False)            # Ruido en dBm
    failure = Column(Boolean, nullable=True)             # etiqueta opcional

    # 5) Índice compuesto para acelerar consultas por (node_id, ts)
    __table_args__ = (
        Index("ix_sensor_readings_node_ts", "node_id", "ts"),
    )