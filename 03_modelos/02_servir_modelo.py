# 02_servir_modelo.py — El endpoint /v1/predict: un modelo de ML detrás de una API
#
#     uvicorn 02_servir_modelo:app --reload
#
# A pequeña escala, esto es lo que pasa cuando usamos ChatGPT o Claude desde una app:
# el modelo vive en un servidor, envuelto en una API que valida y devuelve JSON.
from pathlib import Path

import joblib
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="API de Predicción", version="1.0")

# Se carga UNA vez, al arrancar, FUERA de la función. Cargarlo dentro significaría
# leer el disco en cada petición: con Iris son milisegundos, con una red de verdad
# la API sería inservible.
modelo = joblib.load(Path(__file__).with_name("modelo_iris.joblib"))

# El modelo devuelve 0, 1 o 2. Esta lista los traduce, y el ORDEN debe ser el mismo
# que el de las etiquetas de entrenamiento.
ESPECIES = ["setosa", "versicolor", "virginica"]


# Pydantic hace de GUARDAESPALDAS DEL MODELO: nunca recibirá un pétalo de -3 cm.
# Un modelo no sabe defenderse solo — ante una entrada absurda no protesta,
# predice una barbaridad con toda seriedad.
class Medidas(BaseModel):
    largo_sepalo: float = Field(gt=0, lt=15, description="cm")
    ancho_sepalo: float = Field(gt=0, lt=15, description="cm")
    largo_petalo: float = Field(gt=0, lt=15, description="cm")
    ancho_petalo: float = Field(gt=0, lt=15, description="cm")


# Devolvemos especie Y confianza: no es lo mismo acertar al 99 % que al 34 %, y el
# cliente necesita ese dato para decidir si actúa o pide revisión humana.
class Prediccion(BaseModel):
    especie: str
    confianza: float


@app.post("/v1/predict", response_model=Prediccion)
def predecir(m: Medidas):
    # CUIDADO CON EL ORDEN: scikit-learn recibe una lista posicional, sin nombres.
    # Si intercambiamos dos medidas no hay error ni aviso: la API sigue respondiendo
    # y todas las predicciones pasan a ser falsas.
    #
    # Los corchetes dobles no son errata: espera una LISTA DE MUESTRAS, aunque
    # mandemos una sola. De ahí el [0] de después.
    entrada = [[m.largo_sepalo, m.ancho_sepalo, m.largo_petalo, m.ancho_petalo]]

    # predict() daría solo la especie; predict_proba() da la probabilidad de las tres.
    probs = modelo.predict_proba(entrada)[0]
    idx = int(probs.argmax())

    # int() y float() no sobran: probs contiene tipos de NumPy, no serializables a JSON.
    return Prediccion(especie=ESPECIES[idx], confianza=round(float(probs[idx]), 3))
