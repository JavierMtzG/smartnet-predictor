# ------------------------------------------------------------
# Entrenamiento baseline:
#  - carga histórico desde SQLite
#  - agrega por ventanas (15min por defecto)
#  - entrena pipeline: StandardScaler + LogisticRegression
#  - evalúa (ROC-AUC) y guarda artefactos en artifacts/
# ------------------------------------------------------------

from __future__ import annotations

import os
import json
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, classification_report
import joblib

from ml.features import load_dataframe, window_agg, save_feature_spec

ART_DIR = os.getenv("ARTIFACTS", "artifacts")
MODEL_PATH = os.path.join(ART_DIR, "model.joblib")
FEATURE_SPEC_PATH = os.path.join(ART_DIR, "feature_spec.json")

def main(window: str = "15min", test_size: float = 0.25, seed: int = 42):
    # 1) Cargar histórico completo desde SQLite
    df = load_dataframe()
    if df.empty:
        raise SystemExit("No hay datos en la BD. Ejecuta el generador sintético o ingesta manualmente.")

    # 2) Agregar por ventanas -> X (features) y (labels)
    X, y, full = window_agg(df, window=window)

    # 3) Si todas las etiquetas son iguales, no se puede evaluar AUC
    if y.nunique() < 2:
        raise SystemExit("Todas las etiquetas son iguales (todo 0 o todo 1). Ajusta el generador: --degrade/--failure-bias.")

    # 4) Split reproducible
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y
    )

    # 5) Pipeline: escalar + regresión logística
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000))
    ])

    # 6) Entrenar
    pipe.fit(X_train, y_train)

    # 7) Evaluar (ROC-AUC) + reporte
    p_val = pipe.predict_proba(X_val)[:, 1]
    auc = roc_auc_score(y_val, p_val)
    print({"window": window, "val_auc": round(float(auc), 4)})

    # (opcional) ver umbral clásico 0.5
    yhat = (p_val >= 0.5).astype(int)
    print(classification_report(y_val, yhat, digits=3))

    # 8) Guardar artefactos
    os.makedirs(ART_DIR, exist_ok=True)
    joblib.dump(pipe, MODEL_PATH)
    save_feature_spec(FEATURE_SPEC_PATH)

    print(f"✔ Modelo guardado en: {MODEL_PATH}")
    print(f"✔ Especificación de features en: {FEATURE_SPEC_PATH}")

if __name__ == "__main__":
    main()