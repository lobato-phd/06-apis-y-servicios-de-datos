# 03_pydantic_y_crud.py — Pydantic y el CRUD completo
#
#     uvicorn 03_pydantic_y_crud:app --reload
#
# Abrimos http://127.0.0.1:8000/docs — Swagger UI, generada sola. Los verbos nuevos
# (POST, PUT, PATCH, DELETE) solo se prueban desde ahí: el navegador solo hace GET.
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

CITAS = [
    {"autor": "Einstein", "texto": "La imaginación es más importante que el conocimiento"},
    {"autor": "Descartes", "texto": "Pienso, luego existo"},
    {"autor": "Einstein", "texto": "No todo lo que cuenta puede ser contado"},
]


# CONTRATO DE ENTRADA. Pydantic valida ANTES de que nuestra función se ejecute:
# texto vacío, likes = -5 o likes = "muchos" se rechazan con un 422.
class Cita(BaseModel):
    texto: str = Field(min_length=1, max_length=500)
    autor: str = Field(min_length=2)
    etiquetas: list[str] = []
    likes: int = Field(default=0, ge=0)   # ge = greater or equal


# El mismo contrato con todo opcional. Hace falta porque PUT exige la cita entera
# y PATCH debe aceptar un solo campo suelto: sin esto, un PATCH parcial daría 422.
class CitaParcial(BaseModel):
    texto: str | None = Field(default=None, min_length=1, max_length=500)
    autor: str | None = Field(default=None, min_length=2)
    etiquetas: list[str] | None = None
    likes: int | None = Field(default=None, ge=0)


@app.get("/")
def raiz():
    return {"mensaje": "Hola, máster"}


# GET: lectura de recursos
@app.get("/citas")
def listar_citas(autor: str | None = None, limite: int | None = None):
    resultado = CITAS
    if autor:
        resultado = [c for c in resultado if c["autor"] == autor]
    # Sin `limite`, [:None] devuelve la lista entera.
    return resultado[:limite]


@app.get("/citas/{indice}")
def obtener_cita(indice: int):
    if not 0 <= indice < len(CITAS):
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return CITAS[indice]


# POST: creación. El cuerpo JSON se convierte en un objeto `Cita` por el type hint.
# 201 (Created) en vez de 200: el código de estado también comunica.
@app.post("/citas", status_code=201)
def crear_cita(cita: Cita):
    CITAS.append(cita.model_dump())        # model_dump: de objeto Pydantic a dict
    return {"creada": True, "total": len(CITAS)}


# PUT: reemplazo. Recibe la cita ENTERA — si omitimos `likes`, no se conserva el
# anterior: toma el valor por defecto (0), porque el recurso nuevo SUSTITUYE al viejo.
# Ahí se ve la idempotencia: repetimos el mismo PUT diez veces y el estado no cambia.
@app.put("/citas/{indice}")
def reemplazar_cita(indice: int, cita: Cita):
    if not 0 <= indice < len(CITAS):
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    CITAS[indice] = cita.model_dump()
    return CITAS[indice]


# PATCH: modificación parcial. exclude_unset=True es la pieza clave: descarta los
# campos que el cliente NO envió. Sin él llegarían como None y borrarían los datos.
@app.patch("/citas/{indice}")
def modificar_cita(indice: int, cambios: CitaParcial):
    if not 0 <= indice < len(CITAS):
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    CITAS[indice].update(cambios.model_dump(exclude_unset=True))
    return CITAS[indice]


# DELETE: 204 (No Content) significa "hecho, y no tengo nada que contarte",
# así que no se devuelve nada.
#
# OJO: usamos la POSICIÓN como identificador. Al borrar la cita 0, el /citas/2 de
# un cliente pasa a apuntar a otra distinta. Por eso las APIs reales usan un id estable.
@app.delete("/citas/{indice}", status_code=204)
def borrar_cita(indice: int):
    if not 0 <= indice < len(CITAS):
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    CITAS.pop(indice)
