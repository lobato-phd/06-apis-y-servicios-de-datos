# 07_app.py — EL FINAL COMPLETO: todo el módulo en una sola aplicación
#
#     cd 05_produccion
#     $env:API_KEY = "clave-secreta-de-prueba"
#     $env:JWT_SECRET = "un-secreto-largo-y-aleatorio"
#     uvicorn 07_app:app --reload --port 8000
#
# Los ficheros 01 a 06 añaden una pieza cada uno, en un solo fichero, para poder
# explicarlas por separado. Este los junta — y al juntarlos ya no caben en uno solo:
# eran 380 líneas. Así que aquí aparecen las tres herramientas que usa cualquier
# proyecto FastAPI en cuanto crece:
#
#   ROUTERS   la API partida en módulos por tema (routers/)
#   LIFESPAN  qué pasa al arrancar y al apagar, con nombre y en un sitio
#   MIDDLEWARE una capa que envuelve TODAS las peticiones
#
# Y la regla que lo ordena: leer es público, escribir exige un token.
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as ErrorHTTP

from routers import auth, citas, estado, externo, prediccion

AQUI = Path(__file__).parent


# =====================================================================
#  LIFESPAN · arranque y apagado
# =====================================================================
# Todo lo que hay ANTES del yield se ejecuta al arrancar; lo de después, al apagar.
# En los ficheros 01-06 los datos se cargaban en código de módulo, que funciona pero
# tiene dos pegas: ocurre "al importar" (un momento difuso) y no hay ningún sitio
# donde soltar lo cargado. Aquí el arranque es un momento con nombre.
#
# Sustituye a @app.on_event("startup") y @app.on_event("shutdown"), que siguen
# funcionando pero están deprecados desde FastAPI 0.93.
@asynccontextmanager
async def lifespan(app: FastAPI):
    if not estado.SECRETO:
        raise RuntimeError(
            "Falta la variable de entorno JWT_SECRET.\n"
            '  PowerShell: $env:JWT_SECRET = "un-secreto-largo-y-aleatorio"\n'
            '  Docker:     docker run -e JWT_SECRET="..." -e API_KEY="..." ...'
        )
    estado.cargar_datos()          # <- arranque
    yield
    estado.soltar_datos()          # <- apagado: aquí se cierran conexiones y ficheros


app = FastAPI(
    title="API de Citas — completa",
    version="2.0",
    description="Datos, modelo de ML, proveedor externo y seguridad en dos capas.",
    lifespan=lifespan,
)


# =====================================================================
#  ERRORES · una sola forma para toda la API (RFC 9457, Problem Details)
# =====================================================================
# Por defecto FastAPI es incoherente sin querer: en un 404 la clave `detail` es
# un texto, y en el 422 de Pydantic es una LISTA de objetos. Quien nos consume
# tendría que mirar de qué tipo es antes de usarla.
#
# Estos dos manejadores dan la misma forma a TODOS los errores: los HTTPException
# nuestros, los 404 de rutas inexistentes, los 405 y la validación. `detail` es
# siempre un texto; el desglose campo a campo viaja aparte, en `errors`.
# (Ver sección 3.2 de la guía. Los ficheros 01-06 conservan a propósito el
#  comportamiento por defecto, que es el que se explica en el capítulo 2.)
def problema(request: Request, status: int, titulo: str, detalle: str, **extra):
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={"title": titulo, "status": status, "detail": detalle,
                 "instance": request.url.path, **extra},
    )


@app.exception_handler(ErrorHTTP)
async def error_http(request: Request, exc: ErrorHTTP):
    return problema(request, exc.status_code, "Error en la petición", exc.detail)


@app.exception_handler(RequestValidationError)
async def error_validacion(request: Request, exc: RequestValidationError):
    return problema(request, 422, "Datos de entrada inválidos",
                    "Revisa los campos indicados en 'errors'",
                    errors=jsonable_encoder(exc.errors()))


# =====================================================================
#  MIDDLEWARE · una capa alrededor de cada petición
# =====================================================================
# Un middleware envuelve TODAS las peticiones: se ejecuta antes de que la ruta
# reciba nada y después de que responda. Es el sitio de lo transversal — medir,
# registrar, añadir cabeceras — para no repetirlo en cada endpoint.
#
# `call_next(request)` es "que siga su camino": ejecuta el resto de middlewares y,
# al final, tu endpoint. Lo de antes de esa línea pasa a la ida; lo de después, a
# la vuelta. Si olvidas devolver `response`, la petición muere aquí.
@app.middleware("http")
async def medir_tiempo(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    duracion = time.perf_counter() - t0
    # Cabecera propia: quien nos consuma puede ver cuánto tardamos, y nosotros
    # detectar endpoints lentos sin instrumentar nada más.
    response.headers["X-Tiempo-Proceso"] = f"{duracion:.4f}"
    if duracion > 1:
        estado.logger.warning(f"Petición lenta: {request.url.path} ({duracion:.2f} s)")
    return response


# El CORS que llevamos usando desde 05_cors.py era exactamente esto: un middleware,
# solo que escrito por otros. add_middleware es para clases; el decorador de arriba,
# para funciones propias.
#
# OJO AL ORDEN: el último que se añade es el primero que se ejecuta. Aquí CORS
# envuelve a medir_tiempo, así que las cabeceras de CORS se aplican también a las
# respuestas de error.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://apis-y-servicios-de-datos.onrender.com",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Tiempo-Proceso"],   # sin esto el navegador la oculta al JS
)


# =====================================================================
#  ROUTERS · la API partida por temas
# =====================================================================
# Cada router trae sus rutas ya con su prefijo y sus tags. Montarlos es una línea,
# y el fichero principal queda como un índice legible de lo que hace la aplicación.
app.include_router(externo.router)       # /health, /v1/tiempo, /v1/privado
app.include_router(auth.router)          # /auth/*
app.include_router(citas.router)         # /v1/citas
app.include_router(prediccion.router)    # /v1/predict

# La misma API sirve la página y los datos: mismo origen, no hay CORS.
app.mount("/web", StaticFiles(directory=AQUI / "web", html=True), name="web")
