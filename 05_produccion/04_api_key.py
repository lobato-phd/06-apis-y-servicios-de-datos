# 04_api_key.py — Capa 1 de seguridad: API key
#
#     cd 05_produccion
#     $env:API_KEY = "clave-secreta-de-prueba"     <- PowerShell, ANTES de arrancar
#     uvicorn 04_api_key:app --reload --port 8000
#
# Igual que 03_health.py más un endpoint privado. Lo probamos en /docs con el botón
# "Authorize", o con:
#     curl -H "X-API-Key: clave-secreta-de-prueba" http://127.0.0.1:8000/v1/privado
#
# La variable vive SOLO en esa terminal, y ese es el espejo local de lo que hace
# la nube: la plataforma inyecta el secreto y nuestro código lo lee. Nunca en el código.
import json
import logging
import os
import secrets
from pathlib import Path

import joblib
import requests
from fastapi import Depends, FastAPI, HTTPException, Query, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="API de Citas", version="1.0")

# Se lee al arrancar, no en cada petición. Con os.environ["API_KEY"] a secas,
# olvidar la variable da un KeyError -> 500 con traceback en cada llamada.
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
# APIKeyHeader indica a FastAPI dónde esperar la clave, y de paso hace que /docs
# muestre el botón "Authorize".
cabecera = APIKeyHeader(name="X-API-Key")


def verificar(key: str = Security(cabecera)):
    if API_KEY is None:
        # 500, no 401: el cliente no ha hecho nada mal, el mal configurado
        # es el servidor.
        logger.error("API_KEY no está definida en el entorno")
        raise HTTPException(500, "El servidor no tiene configurada su API key")

    # compare_digest compara en tiempo constante. Un `!=` se corta en la primera
    # letra distinta, y esa diferencia de tiempo permite adivinar la clave.
    if not secrets.compare_digest(key, API_KEY):
        raise HTTPException(401, "API key inválida")


# dependencies=[...] comprueba ANTES de entrar: si no pasa, el cuerpo no se ejecuta.
@app.get("/v1/privado", dependencies=[Depends(verificar)])
def privado():
    return {"acceso": "concedido"}


# --- El pulso del servicio ---
# Sin protección a propósito: la plataforma que lo consulta no tiene nuestra API key,
# y un /health con credenciales haría que nos reiniciaran el contenedor en bucle.
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
