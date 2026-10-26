# 02_parametros.py — Path parameters y query parameters
#
#     uvicorn 02_parametros:app --reload
#
# PATH param  -> identifica UN recurso concreto        /citas/2
# QUERY param -> filtra, ordena o pagina una COLECCIÓN /citas?autor=Einstein
from fastapi import FastAPI, HTTPException

app = FastAPI()

# Los datos viven en memoria: al reiniciar el servidor vuelven a este estado.
CITAS = [
    {"autor": "Einstein", "texto": "La imaginación es más importante que el conocimiento"},
    {"autor": "Descartes", "texto": "Pienso, luego existo"},
    {"autor": "Einstein", "texto": "No todo lo que cuenta puede ser contado"},
]


@app.get("/")
def raiz():
    return {"mensaje": "Hola, máster"}


# QUERY PARAMS: los argumentos que NO aparecen en la ruta los busca FastAPI en la
# query string. Tener valor por defecto es lo que los hace OPCIONALES; sin él,
# FastAPI los exigiría y respondería 422.
@app.get("/citas")
def listar_citas(autor: str | None = None, limite: int | None = None):
    resultado = CITAS
    if autor:
        # Con == exacto: "einstein" en minúsculas no encontraría nada.
        resultado = [c for c in resultado if c["autor"] == autor]
    # Sin `limite`, [:None] devuelve la lista entera.
    return resultado[:limite]


# PATH PARAM: el {indice} llega como argumento. El type hint `: int` no es
# decorativo — con /citas/hola, FastAPI responde un error claro sin escribir nada.
#
# OJO al orden: FastAPI prueba las rutas de arriba abajo. Si añadimos /citas/buscar,
# la ponemos ANTES que esta o "buscar" se interpretará como un {indice}.
@app.get("/citas/{indice}")
def obtener_cita(indice: int):
    if not 0 <= indice < len(CITAS):
        # 404 honesto en lugar de un 500 por IndexError: "eso no existe", no "me he roto".
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return CITAS[indice]
