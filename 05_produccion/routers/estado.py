# estado.py — lo que comparten todos los routers
#
# Al partir la app en varios ficheros aparece una pregunta nueva: ¿dónde viven los
# datos y el modelo, si ya no hay un único fichero donde ponerlos? Aquí: un módulo
# que los routers importan. Python solo ejecuta un módulo UNA vez por proceso, así
# que todos comparten exactamente los mismos objetos.
#
# En un proyecto real este fichero sería la conexión a la base de datos.
import csv
import json
import logging
import os
from pathlib import Path

import joblib

logger = logging.getLogger("uvicorn.error")

# La carpeta 05_produccion, un nivel por encima de routers/
RAIZ = Path(__file__).parents[1]

FICHERO_USUARIOS = RAIZ / "usuarios.csv"
FICHERO_REFRESH = RAIZ / "refresh_tokens.json"

# --- Configuración: los secretos se leen del entorno, nunca del código ---
SECRETO = os.environ.get("JWT_SECRET")
API_KEY = os.environ.get("API_KEY")
ALGORITMO = "HS256"
ACCESO_MIN = 15
REFRESH_DIAS = 7

ESPECIES = ["setosa", "versicolor", "virginica"]

# Se rellenan en el lifespan de 07_app.py, al arrancar. Empiezan vacíos a propósito:
# así se ve que el arranque es un momento con nombre, y no "lo que pasa al importar".
CITAS: list[dict] = []
modelo = None


def cargar_datos() -> None:
    """Carga citas y modelo. La llama el lifespan al arrancar."""
    global modelo
    with open(RAIZ / "citas.json", encoding="utf-8") as f:
        CITAS.extend(json.load(f))
    for i, c in enumerate(CITAS):
        c["id_interno"] = i          # campo interno: response_model impide que salga
    modelo = joblib.load(RAIZ / "modelo_iris.joblib")
    logger.info(f"Cargadas {len(CITAS)} citas y el modelo de clasificación")


def soltar_datos() -> None:
    """Libera lo cargado. La llama el lifespan al apagar."""
    global modelo
    CITAS.clear()
    modelo = None
    logger.info("Datos y modelo liberados")


def cargar_usuarios() -> dict[str, dict]:
    with FICHERO_USUARIOS.open(newline="", encoding="utf-8") as f:
        return {fila["username"]: fila for fila in csv.DictReader(f)}
