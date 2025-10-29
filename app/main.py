# código de la app, el main.py  

#importamos FastAPI que es el núcleo del framework para definir la app y rutas
from fastapi import FastAPI

#usamos pydantic para definir modelos de datos, lo usamos para tipar y validar entradas/salidas y documentar la APU
from pydantic import BaseModel

#importamos datetime para tener una timestamp de las medidas en /health
from datetime import datetime, timezone

#creamos la instancia de la aplicación 
app = FastAPI(title = "SmartNet Predictor", version= "0.1.1")

#Estamos definiendo la forma del JSON que devuelve /health
class HealthRespone(BaseModel):
    ok: bool
    service: str
    version: str
    time_utc: datetime 
    
    
@app.get("/")
def root():
    return {"message":"Welcome to SmartNet Predictor - base API"}

#Creamos endpoint health para que kubernete/railway consulten si el servicio está vivo
@app.get("/health", response_model=HealthRespone, summary="Health")
def health() -> HealthRespone:
    #No accede a la BD ni al modelo, solo confirma que está operativo el proceso
    
    #Devolvemos un diccionario que FastAPI serializa como JSON 
    #Entre lo que incluimos tenemos
    #   - ok : una flag de true o false para verificarlo fácil como persona o máquina
    #   - service: nombre del servicio para los logs
    #   - version: se enlaca con appversion, para no repetir el valor de nuevo
    #   - time_utc: para tener una marca de tiempo
    
    return {
        "ok": True,
        "service": "smartnet-predictor",
        "version": app.version,
        "time_utc": datetime.now(timezone.utc).isoformat()
    }    