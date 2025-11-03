# ------------------------------------------------------------
# Simulador de sensores para poblar la API (/ingest) con datos
# realistas. Diseñado para:
#  - reproducibilidad (seed)
#  - eventos de degradación (lat/jitter↑, RSSI↓, ruido↑)
#  - etiqueta de fallo probabilística
#  - múltiples nodos en paralelo (simple)
# ------------------------------------------------------------

from __future__ import annotations
import time
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, List

import numpy as np
import requests


def utcnow() -> datetime:
    """Devuelve un datetime timezone-aware en UTC (forma correcta en Python 3.12+)."""
    return datetime.now(timezone.utc)


def generate_reading(node_id: str, degrade_chance: float, failure_bias: float) -> Dict[str, Any]:
    """
    Genera UNA lectura 'creíble' para un nodo.
    - degrade_chance: probabilidad de que esta lectura esté en un episodio degradado.
    - failure_bias: empujón extra a la probabilidad de fallo para no tener 0s eternos.

    Modelo simple:
      - Base normal: lat~N(20,5), jitter~N(3,1), RSSI~N(-65,4), ruido~N(-90,3)
      - Evento degradado (p.ej., congestión): lat +Exp(20), jitter +Exp(5), RSSI -N(6,2), ruido +N(6,2)
      - Prob de fallo: sigmoide(score) mezclada con failure_bias
    """
    # --- base saludable ---
    lat = np.random.normal(20, 5)          # ms
    jit = np.random.normal(3, 1)           # ms
    rssi = np.random.normal(-65, 4)        # dBm (más negativo = peor señal)
    noise = np.random.normal(-90, 3)       # dBm (más alto = más ruido)

    # --- posible degradación (congestión, interferencia, etc.) ---
    if np.random.rand() < degrade_chance:
        lat += np.random.exponential(20)
        jit += np.random.exponential(5)
        rssi += np.random.normal(-6, 2)    # más negativo
        noise += np.random.normal(6, 2)    # más ruidoso

    # --- score para fallo (combinación lineal “intuitiva”) ---
    #    pesos heurísticos: mayor lat/jitter/ruido aumentan score; RSSI bajo (más negativo) también.
    score = 0.04 * lat + 0.07 * jit - 0.06 * rssi + 0.05 * noise

    # --- prob. fallo con sigmoide + sesgo ---
    p_fail = 1.0 / (1.0 + np.exp(-(score - 2.5)))
    p_fail = 0.7 * p_fail + 0.3 * failure_bias  # mezcla para que haya variedad

    # --- clamp mínimos físicos ---
    lat = max(0.0, float(lat))
    jit = max(0.0, float(jit))

    return {
        "node_id": node_id,
        "ts": utcnow().isoformat(),   # ya en UTC (+00:00)
        "latency_ms": lat,
        "jitter_ms": jit,
        "rssi_dbm": float(rssi),
        "noise_dbm": float(noise),
        "failure": bool(np.random.rand() < p_fail),
    }


def build_batch(node_ids: List[str], degrade_chance: float, failure_bias: float) -> Dict[str, Any]:
    """Construye un lote con una lectura por nodo (lo que espera /ingest)."""
    return {
        "readings": [generate_reading(n, degrade_chance, failure_bias) for n in node_ids]
    }


def run_stream(
    api_url: str,
    nodes: int,
    period: float,
    degrade_chance: float,
    failure_bias: float,
    seed: int | None,
    max_batches: int | None,
) -> None:
    """
    Bucle de envío:
      - Cada 'period' segundos, envía un lote con N lecturas (una por nodo).
      - Si 'max_batches' es None, corre indefinidamente.
    """
    if seed is not None:
        np.random.seed(seed)

    node_ids = [f"node-{i:02d}" for i in range(1, nodes + 1)]
    endpoint = api_url.rstrip("/") + "/ingest"

    print(f"[sim] enviando a: {endpoint}")
    print(f"[sim] nodos: {node_ids} | periodo: {period}s | degrade_chance: {degrade_chance} | failure_bias: {failure_bias}")

    sent = 0
    while True:
        payload = build_batch(node_ids, degrade_chance, failure_bias)

        try:
            r = requests.post(endpoint, json=payload, timeout=5)
            ok = r.status_code
            print(f"[sim] {utcnow().isoformat()} -> HTTP {ok} :: {r.text[:120]}")

        except Exception as e:
            print(f"[sim] ERROR: {e}")

        sent += 1
        if max_batches is not None and sent >= max_batches:
            print("[sim] fin: alcanzado max_batches")
            break

        time.sleep(period)


def parse_args() -> argparse.Namespace:
    """Argumentos CLI para controlar la simulación sin tocar código."""
    ap = argparse.ArgumentParser(description="Simulador de sensores para SmartNet Predictor")
    ap.add_argument("--api", default="http://127.0.0.1:8000", help="URL base de la API (sin /ingest)")
    ap.add_argument("--nodes", type=int, default=3, help="Cantidad de nodos simulados")
    ap.add_argument("--period", type=float, default=2.0, help="Segundos entre lotes")
    ap.add_argument("--degrade", type=float, default=0.12, help="Probabilidad de episodio degradado por lectura")
    ap.add_argument("--failure-bias", type=float, default=0.05, help="Sesgo mínimo de probabilidad de fallo")
    ap.add_argument("--seed", type=int, default=42, help="Semilla para reproducibilidad (None para aleatorio)")
    ap.add_argument("--max-batches", type=int, default=None, help="Número de lotes y salir (None = infinito)")
    return ap.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_stream(
        api_url=args.api,
        nodes=args.nodes,
        period=args.period,
        degrade_chance=args.degrade,
        failure_bias=args.failure_bias,
        seed=args.seed,
        max_batches=args.max_batches,
    )