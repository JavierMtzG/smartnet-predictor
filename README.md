# SmartNet Predictor — Fase 1 (Base de API)

API educativa para recibir lecturas de sensores de red (latencia, jitter, RSSI, ruido), validar/normalizar los datos y exponer estado por nodo. Esta fase usa **almacenamiento en memoria** (mock) y fija los **contratos** de la API.

## Estado de la fase
- ✅ `/health` — health check
- ✅ `/ingest` — ingesta por lote (mock en memoria) con validaciones Pydantic v2
- ✅ `/status` — último estado por nodo (snapshot)
- ✅ `/docs` — documentación automática (Swagger/OpenAPI)

## Stack actual
- Python 3.10+
- FastAPI (ASGI)
- Pydantic v2 (contratos/validación)
- Uvicorn (servidor ASGI)

## Estructura
app/
init.py
main.py # objeto ASGI y montaje de routers
schemas.py # contratos Pydantic (entrada/salida)
state.py # “pseudobase” en memoria (mock)
routers/
init.py
ingest.py # POST /ingest
status.py # GET /status
