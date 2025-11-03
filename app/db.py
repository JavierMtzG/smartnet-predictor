# 1) Importamos piezas de SQLAlchemy para crear:
#    - el "engine" (conexión a la base de datos),
#    - la "session" (unidad de trabajo),
#    - y la "Base" (clase base para modelos ORM).
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# 2) URL de la BD:
#    - Por defecto, SQLite en un archivo local en la raíz del proyecto.
#    - Más adelante podrás cambiar a PostgreSQL con algo tipo:
#      postgresql+psycopg2://user:pass@host:5432/dbname
DB_URL = os.getenv("DB_URL", "sqlite:///./smartnet.db")

# 3) Creamos el engine.
#    - Para SQLite en fichero, hay que pasar 'check_same_thread=False'
#      porque el driver sqlite por defecto es estrictito con hilos.
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
)

# 4) Creamos un "session factory".
#    - autocommit=False: controlamos cuándo confirmar cambios (commit).
#    - autoflush=False: no volcamos cambios a la BD automáticamente
#      hasta que lo pidamos (o antes de ciertas queries).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5) Declarative Base:
#    - De aquí heredarán nuestros modelos (tablas).
Base = declarative_base()

# 6) Dependencia para FastAPI:
#    - Nos da una Session por petición y la cierra al terminar.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()