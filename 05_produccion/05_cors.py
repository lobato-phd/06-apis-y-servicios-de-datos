# 05_cors.py — Capa 2 de seguridad: CORS
#
#     cd 05_produccion
#     $env:API_KEY = "clave-secreta-de-prueba"
#     uvicorn 05_cors:app --reload --port 8000
#
# CORS decide QUÉ WEBS pueden llamar a nuestra API desde el navegador. Ojo: la regla
# la aplica EL NAVEGADOR, no nuestro servidor — un curl entra igual. No sustituye a
# la API key: protegen cosas distintas.
#
# LA DEMO, en dos pasos (ver web/demo_cors.html):
#   1. Mismo origen: http://127.0.0.1:8000/web/demo_cors.html -> CORS ni interviene.
#   2. Otro origen: abrimos el HTML con Live Server (:5500) -> el navegador exige
#      permiso, y funciona solo porque el 5500 está en la lista de abajo.
#      Lo quitamos de allow_origins, recargamos, y veremos el error.
import json
import logging
import os
import secrets
from pathlib import Path

import joblib
import requests
from fastapi import Depends, FastAPI, HTTPException, Query, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="API de Citas", version="1.0")

# SIN barra final: la cabecera Origin es siempre "esquema://host:puerto", sin
# ruta; con barra no coincide nunca. Y localhost != 127.0.0.1 para el navegador,
# aunque apunten a la misma máquina.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://apis-y-servicios-de-datos.onrender.com",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.environ.get("API_KEY")

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


# --- Seguridad: endpoint privado, requiere cabecera X-API-Key ---
cabecera = APIKeyHeader(name="X-API-Key")


def verificar(key: str = Security(cabecera)):
    if API_KEY is None:
        logger.error("API_KEY no está definida en el entorno")
        raise HTTPException(500, "El servidor no tiene configurada su API key")
    if not secrets.compare_digest(key, API_KEY):   # comparación en tiempo constante
        raise HTTPException(401, "API key inválida")


@app.get("/v1/privado", dependencies=[Depends(verificar)])
def privado():
    return {"acceso": "concedido"}


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


# --- Servir el estático de la carpeta web (demo de CORS) ---
# La misma API sirve la página Y los datos: mismo origen, no hay CORS. Montar el
# frontend en la propia API es la forma más simple de que el problema ni exista.
# Queda en http://127.0.0.1:8000/web/demo_cors.html
app.mount("/web", StaticFiles(directory=Path(__file__).parent / "web", html=True), name="web")
