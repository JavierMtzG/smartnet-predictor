# ------------------------------------------------------------
# Utilidades de ingeniería de características:
#  - Cargar histórico desde SQLite a pandas
#  - Agregar por ventanas (resample) por node_id
#  - Calcular estadísticas (mean, std, p95)
#  - Definir la etiqueta de fallo por ventana
# ------------------------------------------------------------

from __future__ import annotations

from typing import Tuple, List
import os
import json
import pandas as pd
from sqlalchemy import create_engine


# Columnas crudas tal como están en la tabla
RAW_COLS = [
    "id", "ts", "node_id", "latency_ms", "jitter_ms", "rssi_dbm", "noise_dbm", "failure"
]

# Especificación de las columnas de features (orden importa para el modelo)
#definiendo el std, mean, p95
FEATURE_COLS = [
    "latency_ms_mean", "latency_ms_std", "latency_ms_p95",
    "jitter_ms_mean",  "jitter_ms_std",  "jitter_ms_p95",
    "rssi_dbm_mean",   "rssi_dbm_std",   "rssi_dbm_p95",
    "noise_dbm_mean",  "noise_dbm_std",  "noise_dbm_p95",
]

#crea el dataframe
def load_dataframe(db_url: str | None = None) -> pd.DataFrame:
    """
    Lee la tabla sensor_readings completa desde SQLite (o la DB_URL dada)
    y devuelve un DataFrame con las columnas RAW_COLS.

    - db_url por defecto toma el env DB_URL (o sqlite:///./smartnet.db)
    - convierte 'ts' a datetime (timezone-aware si viene así)
    """
    db_url = db_url or os.getenv("DB_URL", "sqlite:///./smartnet.db")
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {}
    )
    #dataframe lee
    # Leemos toda la tabla (para proyecto educativo está bien).
    df = pd.read_sql("SELECT id, ts, node_id, latency_ms, jitter_ms, rssi_dbm, noise_dbm, failure FROM sensor_readings", engine)
    
    # Aseguramos tipo datetime en ts (pandas lo entiende y preserva offset +00:00)
    df["ts"] = pd.to_datetime(df["ts"], utc=True)

    # failure puede venir como 0/1 o NULL; convertimos a int (NULL -> 0)
    df["failure"] = df["failure"].fillna(0).astype(int)
    return df


def window_agg(df: pd.DataFrame, window: str = "15min") -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Convierte histórico crudo a dataset de entrenamiento por ventanas.

    Para cada node_id:
      - re-indexa por ts y hace resample en ventanas 'window'
      - calcula mean, std, p95 para cada métrica
      - la etiqueta 'failure' es el máximo en la ventana (hubo algún fallo?)

    Devuelve:
      X : DataFrame de features (columnas FEATURE_COLS)
      y : Serie binaria de etiquetas (0/1)
      frame : DataFrame completo con columnas auxiliares (ts de ventana y node_id)
    """
    if df.empty:
        raise ValueError("No hay datos en la base; ingesta primero.")

    df = df.sort_values(["node_id", "ts"]).copy()

    frames = []
    for node, g in df.groupby("node_id"):
        # resample por ventana de tiempo
        gr = g.set_index("ts").resample(window).agg({
            "latency_ms": ["mean", "std", lambda x: x.quantile(0.95)],
            "jitter_ms":  ["mean", "std", lambda x: x.quantile(0.95)],
            "rssi_dbm":   ["mean", "std", lambda x: x.quantile(0.95)],
            "noise_dbm":  ["mean", "std", lambda x: x.quantile(0.95)],
            "failure": "max",  # ¿hubo algún fallo en la ventana?
        })

        # aplanamos MultiIndex de columnas
        gr.columns = [
            "latency_ms_mean", "latency_ms_std", "latency_ms_p95",
            "jitter_ms_mean",  "jitter_ms_std",  "jitter_ms_p95",
            "rssi_dbm_mean",   "rssi_dbm_std",   "rssi_dbm_p95",
            "noise_dbm_mean",  "noise_dbm_std",  "noise_dbm_p95",
            "failure"
        ]
        gr["node_id"] = node
        frames.append(gr.reset_index())  # 'ts' ahora es el borde de la ventana

    full = pd.concat(frames, ignore_index=True)

    # quitamos ventanas vacías (pueden introducir NaN en std/p95)
    full = full.dropna(subset=FEATURE_COLS)

    X = full[FEATURE_COLS].copy()
    y = full["failure"].astype(int).copy()
    return X, y, full


def save_feature_spec(path: str):
    """
    Guarda el orden de columnas de features en JSON para
    que el serving (Fase 5) construya X con el MISMO orden.
    """
    spec = {"feature_columns": FEATURE_COLS}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)