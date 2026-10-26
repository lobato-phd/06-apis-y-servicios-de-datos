# 05_contrato_salida.py — response_model: contrato también a la salida
#
#     uvicorn 05_contrato_salida:app --reload
#
# Ya validamos lo que ENTRA (Pydantic + 422). Falta controlar lo que SALE.
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(title="API de Citas", version="1.0")


# CONTRATO DE SALIDA: los únicos campos que verá el mundo exterior.
# Fijémonos en lo que NO está: id_interno. Eso es lo que lo hace útil.
class CitaOut(BaseModel):
    texto: str
    autor: str
    etiquetas: list[str]


# El contrato de una respuesta PAGINADA. list[CitaOut] recorta cada elemento.
class ListaCitasOut(BaseModel):
    total: int
    resultados: list[CitaOut]


with open(Path(__file__).with_name("citas.json"), encoding="utf-8") as f:
    CITAS = json.load(f)

for i, c in enumerate(CITAS):
    c["id_interno"] = i


# El listado también lleva contrato, y no es un detalle menor: es el endpoint que
# MÁS datos devuelve. Si le quitamos el response_model, el id_interno reaparece en las
# cien citas de golpe — el contrato se aplica endpoint por endpoint, y basta uno
# olvidado para que se escape todo lo que los demás protegen.
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


# Lo elegante: la función NO cambia, sigue devolviendo la cita entera con su
# id_interno. Es FastAPI quien recorta al pasar por CitaOut. El filtrado no vive
# en el código, vive en el contrato.
#
# Y hace dos cosas más: VALIDA la salida (si faltara `etiquetas` nos enteraríamos
# nosotros, no nuestro cliente) y publica en /docs qué campos recibirá quien nos consuma.
@app.get("/v1/citas/{indice}", response_model=CitaOut)
def detalle(indice: int):
    if not 0 <= indice < len(CITAS):
        raise HTTPException(404, "Cita no encontrada")
    return CITAS[indice]
