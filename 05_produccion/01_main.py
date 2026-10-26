# 01_main.py — La API completa: datos + modelo + proveedor externo
#
#     cd 05_produccion
#     uvicorn 01_main:app --reload --port 8000
#
# Todo el curso en una aplicación: citas scrapeadas (cap. 4), modelo entrenado
# (cap. 3) y una llamada a un tercero (cap. 1). Los ficheros siguientes parten
# de este y le añaden lo que hace falta para sobrevivir en producción.
import json
from pathlib import Path

import joblib
import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="API de Citas", version="1.0")

# --- Datos: el citas.json scrapeado en el Bloque 4 ---
# Ruta relativa al script: dentro del contenedor el cwd es /app.
with open(Path(__file__).with_name("citas.json"), encoding="utf-8") as f:
    CITAS = json.load(f)

for i, c in enumerate(CITAS):
    c["id_interno"] = i          # campo interno: para la demo de response_model

# --- Modelo: se carga UNA vez, al arrancar ---
modelo = joblib.load(Path(__file__).with_name("modelo_iris.joblib"))
ESPECIES = ["setosa", "versicolor", "virginica"]


# --- Contratos (Pydantic) ---
class CitaOut(BaseModel):
    texto: str
    autor: str
    etiquetas: list[str]          # ojo a lo que NO está: id_interno


class ListaCitasOut(BaseModel):   # el contrato de la respuesta paginada
    total: int
    resultados: list[CitaOut]


class Medidas(BaseModel):
    largo_sepalo: float = Field(gt=0, lt=15, description="cm")
    ancho_sepalo: float = Field(gt=0, lt=15, description="cm")
    largo_petalo: float = Field(gt=0, lt=15, description="cm")
    ancho_petalo: float = Field(gt=0, lt=15, description="cm")


class Prediccion(BaseModel):
    especie: str
    confianza: float


# --- Endpoints de datos ---
@app.get("/v1/citas", response_model=ListaCitasOut)
def listar(autor: str | None = None,
           limite: int | None = Query(default=None, ge=1),
           desplazamiento: int = Query(default=0, ge=0)):
    datos = CITAS
    if autor:
        datos = [c for c in datos if autor.lower() in c["autor"].lower()]
    return {
        "total": len(datos),
        # Sin `limite`, se devuelven todas desde `desplazamiento`.
        "resultados": (datos[desplazamiento:] if limite is None
                       else datos[desplazamiento : desplazamiento + limite]),
    }


@app.get("/v1/citas/{indice}", response_model=CitaOut)
def detalle(indice: int):
    if not 0 <= indice < len(CITAS):
        raise HTTPException(404, "Cita no encontrada")
    return CITAS[indice]


# --- Endpoint de ML ---
@app.post("/v1/predict", response_model=Prediccion)
def predecir(m: Medidas):
    # El orden debe coincidir con el del entrenamiento: cambiarlo no da error,
    # solo predicciones falsas. (Ver 03_modelos.)
    entrada = [[m.largo_sepalo, m.ancho_sepalo, m.largo_petalo, m.ancho_petalo]]
    probs = modelo.predict_proba(entrada)[0]
    idx = int(probs.argmax())
    return Prediccion(especie=ESPECIES[idx], confianza=round(float(probs[idx]), 3))


# --- Endpoint que depende de un tercero ---
# El eslabón débil: si Open-Meteo se cae, el cliente recibe un 500 sin explicación
# y en el servidor no queda rastro. El fichero 02_logger.py arregla eso.
@app.get("/v1/tiempo")
def tiempo():
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": 40.97, "longitude": -5.66, "current_weather": True},
        timeout=5,
    )
    r.raise_for_status()
    return r.json()
