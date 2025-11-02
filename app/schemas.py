#PAra los contratos pydantic (entrada y salida)
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

#El BaseModel es lo mínimo para definir modelos de datos, field es para metadatos y validaciones
#por campo, rangos longitudes, y field_validator transforma los campos
from pydantic import BaseModel, Field, field_validator


class ReadingIn(BaseModel):
    """
    Lectura cruda que envía un "sensor" (simulado).
    - node_id: identificador del nodo/antena.
    - ts: timestamp en UTC (aware). Si no viene, lo completaremos al ingresar.
    - latency_ms / jitter_ms / rssi_dbm / noise_dbm: métricas clave de red.
    - failure: etiqueta opcional (útil para entrenamiento más adelante).
    """
    #min y max leng evitan valores basura largas o cadenas vacias
    node_id: str = Field(..., min_length=1, max_length=64)
    #para las timestamp, pueden mandarlo o no, sino lo completamos al ingestar
    ts: Optional[datetime] = None
    #para no encontrar jitter o latencias negativas
    latency_ms: float = Field(..., ge=0)
    jitter_ms: float = Field(..., ge=0)
    #el dbm suele ser negativo
    rssi_dbm: float  # dBm, normalmente negativo
    noise_dbm: float
    failure: Optional[bool] = None
    
    #pydantic usamos field_validator con mode "before" para normalizar la entrada
    #al poner before el validador corre antes de la validacion de tipos, si ts no viene=none
    # si vieen como string tratamos, si viene como datetime lo tendremos al final como utc aware
    @field_validator("ts", mode="before")
    @classmethod
    def ensure_aware_utc(cls, v: Optional[datetime | str]) -> Optional[datetime]:
        """
        Normalizamos `ts` para que siempre sea datetime "aware" en UTC.
        - Si viene como string ISO8601, lo parseamos (soporta sufijo 'Z').
        - Si viene naive (sin tz), asumimos UTC explícitamente.
        - Si ya trae tz, lo convertimos a UTC.
        """
        if v is None:
            return None

        if isinstance(v, str):
            # Soportamos 'Z' (UTC) convirtiéndolo al offset '+00:00'
            v = v.replace("Z", "+00:00")
            try:
                v = datetime.fromisoformat(v)
            except ValueError:
                # Pydantic ya validará formatos; aquí sólo intentamos ser amigables con 'Z'
                raise

        if not isinstance(v, datetime):
            raise TypeError("ts debe ser un datetime o un string ISO8601")

        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)

        return v.astimezone(timezone.utc)

#es el contrato de entrada del endpoint ingest: recibimos un lote, pues los sensores envian normalmente varias meustras en un post

class IngestBatch(BaseModel):
    """
    Lote de lecturas para /ingest.
    Elegimos 'readings' como key clara y extensible.
    """
    readings: List[ReadingIn] = Field(..., min_items=1)

#es el contrato de salida status que se muestra al cliente, muestra la última lectura conocida por node_id. con su ts y predict tendra finalmente su propio contrato de salida
class StatusItem(BaseModel):
    """
    Estado resumido por nodo (última lectura conocida).
    Contrato de salida de /status.
    """
    node_id: str
    ts: datetime
    latency_ms: float
    jitter_ms: float
    rssi_dbm: float
    noise_dbm: float
    # Nota: no exponemos 'failure' aquí; el status es telemetría actual.
    
    
    #Los esquemas definen que entra y que sale, cuando pasemos de memoria a sql la api sigue identica
    #Las validaciones de ge=0 latencia en ms y jitter en ms evitan valores negativos imposibles
    #node_id con minima y máxima longitud evitan entradas basura y readings con min_items =1 evita que se lea nada o mas que eso
    