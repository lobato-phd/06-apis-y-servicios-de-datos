# 03_health.py — Disponibilidad: que nos encuentren siempre vivos
#
#     cd 05_produccion
#     uvicorn 03_health:app --reload --port 8000
#
# Igual que 02_logger.py con dos diferencias: el dominio del proveedor vuelve a
# ser el bueno y aparece el endpoint /health.
import json
import logging
from pathlib import Path

import joblib
import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="API de Citas", version="1.0")

# --- Datos: el citas.json scrapeado en el Bloque 4 ---
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
    etiquetas: list[str]


class ListaCitasOut(BaseModel):
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


# --- El pulso del servicio ---
# No es decorativo: Render, Railway o Azure lo llaman cada pocos segundos y, si
# falla, REINICIAN el contenedor solos. Por eso comprueba también el modelo: un
# proceso vivo cuyo modelo no cargó está arrancado pero no sirve para nada.
#
# Regla de oro: rápido y sin llamar a terceros. Si comprobara Open-Meteo, una
# caída ajena provocaría el reinicio de nuestro propio contenedor.
@app.get("/health")
def health():
    return {"status": "ok", "modelo_cargado": modelo is not None}


# --- Endpoint que depende de un tercero, blindado ---
@app.get("/v1/tiempo")
def tiempo():
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": 40.97, "longitude": -5.66, "current_weather": True},
            timeout=5,               # timeout SIEMPRE
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException as exc:
        logger.error(f"Proveedor externo caído: {exc}")
        raise HTTPException(503, "Servicio externo no disponible, reintenta en unos minutos")


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
    entrada = [[m.largo_sepalo, m.ancho_sepalo, m.largo_petalo, m.ancho_petalo]]
    probs = modelo.predict_proba(entrada)[0]
    idx = int(probs.argmax())
    return Prediccion(especie=ESPECIES[idx], confianza=round(float(probs[idx]), 3))
