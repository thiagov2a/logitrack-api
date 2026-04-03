import pickle
import os
from typing import Optional

_BASE = os.path.join(os.path.dirname(__file__), "..", "..", "analysis")

with open(os.path.join(_BASE, "modelo_prioridad.pkl"), "rb") as f:
    _model = pickle.load(f)

with open(os.path.join(_BASE, "imputer.pkl"), "rb") as f:
    _imputer = pickle.load(f)


def predecir_prioridad(
    peso_kg: Optional[float],
    largo_cm: Optional[float],
    ancho_cm: Optional[float],
    alto_cm: Optional[float],
) -> str:
    """Devuelve 'ALTA', 'MEDIA' o 'BAJA'."""
    X = [[
        peso_kg if peso_kg is not None else float("nan"),
        largo_cm if largo_cm is not None else float("nan"),
        ancho_cm if ancho_cm is not None else float("nan"),
        alto_cm if alto_cm is not None else float("nan"),
    ]]
    X_imp = _imputer.transform(X)
    return str(_model.predict(X_imp)[0])
