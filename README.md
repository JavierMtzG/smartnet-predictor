# SmartNet Predictor

Proyecto educativo para construir una **API de sensores inteligentes** con FastAPI 
que predice fallos o degradación en red usando ML. Empezamos por la base (API),
y luego iremos añadiendo BD, datos sintéticos, entrenamiento y dashboard.

## Estado del Bloque 1
- API mínima con FastAPI y endpoint `/healthz` funcionando.
- Estructura limpia para crecer sin caos.

## Cómo ejecutar (resumen)
- Entorno virtual activo (`.venv`).
- Dependencias instaladas desde `requirements.txt`.
- Arrancar con: `uvicorn app.main:app --reload` y visitar `/healthz`.
