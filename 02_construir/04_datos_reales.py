# 04_datos_reales.py — Exponer un dataset real
#
#     uvicorn 04_datos_reales:app --reload
#
# Hasta ahora servíamos tres citas escritas a mano; aquí van 100 de verdad.
# El fichero nos lo dan hecho: en el capítulo 4 aprenderemos a fabricarlo nosotros.
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

# title y version salen como cabecera en /docs.
app = FastAPI(title="API de Citas", version="1.0")

# Se lee UNA vez al arrancar (es código de módulo), no en cada petición.
# Efecto secundario: si editamos citas.json, hay que reiniciar.
with open(Path(__file__).with_name("citas.json"), encoding="utf-8") as f:
    CITAS = json.load(f)

for i, c in enumerate(CITAS):
    c["id_interno"] = i          # campo interno

# VERSIONADO: el /v1/ de la ruta. Barato hoy, carísimo cuando ya tenemos clientes.
@app.get("/v1/citas")
def listar(autor: str | None = None,
           limite: int | None = Query(default=None, ge=1),
           desplazamiento: int = Query(default=0, ge=0)):
    datos = CITAS
    if autor:
        # `in` en vez de `==`, y .lower() en ambos lados: "eins" encuentra a Einstein.
        datos = [c for c in datos if autor.lower() in c["autor"].lower()]

    # PAGINACIÓN. No devolvemos la lista pelada sino un sobre con `total`:
    # sin ese dato el cliente no sabe cuántas páginas le quedan.
    return {
        "total": len(datos),
        # Sin `limite`, se devuelven todas desde `desplazamiento`.
        "resultados": (datos[desplazamiento:] if limite is None
                       else datos[desplazamiento : desplazamiento + limite]),
    }


@app.get("/v1/citas/{indice}")
def detalle(indice: int):
    if not 0 <= indice < len(CITAS):
        # Mismo formato de error en toda la API: {"detail": "..."}
        raise HTTPException(404, "Cita no encontrada")

    # OJO: devuelve la cita CON su id_interno, que se está escapando al cliente.
    # El fichero 05 lo tapa con response_model.
    return CITAS[indice]
