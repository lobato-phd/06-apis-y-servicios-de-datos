# routers/prediccion.py — el modelo de ML detrás de un endpoint
from fastapi import APIRouter

from . import estado
from .esquemas import Medidas, Prediccion

router = APIRouter(prefix="/v1", tags=["ml"])


@router.post("/predict", response_model=Prediccion)
def predecir(m: Medidas):
    # El orden debe coincidir con el del entrenamiento: cambiarlo no da error,
    # solo predicciones falsas.
    entrada = [[m.largo_sepalo, m.ancho_sepalo, m.largo_petalo, m.ancho_petalo]]
    probs = estado.modelo.predict_proba(entrada)[0]
    idx = int(probs.argmax())
    # int() y float(): probs trae tipos de NumPy, no serializables a JSON.
    return Prediccion(especie=estado.ESPECIES[idx],
                      confianza=round(float(probs[idx]), 3))
