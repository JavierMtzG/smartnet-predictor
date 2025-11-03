
from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, List
from .schemas import ReadingIn, StatusItem

# Diccionario que actúa como base de datos temporal:
# la clave es el node_id y el valor es la última lectura (ReadingIn) recibida.
_last_by_node: Dict[str, ReadingIn] = {}


def upsert_reading(r: ReadingIn) -> None:
    """
    Inserta o actualiza la última lectura de un nodo.
    - Si no trae ts: lo fijamos a 'ahora' en UTC (aware).
    - Si llega una lectura con ts más antiguo que la guardada, la ignoramos.
    """
    
    # Si el sensor no envía 'ts', le asignamos la hora actual en UTC.
    ts = r.ts or datetime.now(timezone.utc)
    # Obtenemos la lectura actual almacenada para ese nodo (si existe).
    current = _last_by_node.get(r.node_id)

    # Condición de actualización:
    # - Si no hay lectura guardada.
    # - O si la nueva lectura tiene un timestamp más reciente que la anterior.
    if current is None or (current.ts or datetime.fromtimestamp(0, tz=timezone.utc)) <= ts:
        r.ts = ts
        _last_by_node[r.node_id] = r


def list_status() -> List[StatusItem]:
    """
    Devuelve el último estado por nodo, listo para serializar en /status.
    Ordenamos por node_id para respuestas deterministas (útil en pruebas).
    """
    # Convertimos cada ReadingIn en un StatusItem (contrato de salida).
    items = [
        StatusItem(
            node_id=r.node_id,
            ts=r.ts or datetime.now(timezone.utc),
            latency_ms=r.latency_ms,
            jitter_ms=r.jitter_ms,
            rssi_dbm=r.rssi_dbm,
            noise_dbm=r.noise_dbm,
        )
        for r in _last_by_node.values()
    ]
    # Ordenamos los resultados por node_id para respuestas deterministas.
    return sorted(items, key=lambda x: x.node_id)
