import pickle
import os
import pandas as pd
from typing import Optional

_BASE = os.path.dirname(__file__)

with open(os.path.join(_BASE, "modelo_prioridad.pkl"), "rb") as f:
    _model = pickle.load(f)

with open(os.path.join(_BASE, "imputer.pkl"), "rb") as f:
    _imputer = pickle.load(f)

FEATURES = ["peso_kg", "largo_cm", "ancho_cm", "alto_cm"]


def predecir_prioridad(
    peso_kg: Optional[float],
    largo_cm: Optional[float],
    ancho_cm: Optional[float],
    alto_cm: Optional[float],
) -> str:
    """Devuelve 'ALTA', 'MEDIA' o 'BAJA'."""
    import math
    X = pd.DataFrame([[
        peso_kg if peso_kg is not None else math.nan,
        largo_cm if largo_cm is not None else math.nan,
        ancho_cm if ancho_cm is not None else math.nan,
        alto_cm if alto_cm is not None else math.nan,
    ]], columns=FEATURES)
    X_imp = _imputer.transform(X)
    return str(_model.predict(X_imp)[0])
