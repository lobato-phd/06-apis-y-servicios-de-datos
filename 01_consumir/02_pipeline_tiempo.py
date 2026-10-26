# 02_pipeline_tiempo.py — Extraer -> Transformar -> Cargar
# Una llamada a una API rara vez vive sola: suele ser la primera etapa de un pipeline.
import json
from pathlib import Path

import requests

# 1. EXTRAER. timezone evita que las fechas vengan en UTC (errores de un día).
r = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={"latitude": 40.97, "longitude": -5.66,
            "daily": "temperature_2m_max", "timezone": "Europe/Madrid"},
    timeout=10,
)
r.raise_for_status()
crudo = r.json()

# print(crudo["daily"])   # el proveedor devuelve dos listas paralelas

# 2. TRANSFORMAR: de "dos listas paralelas" a "lista de registros", que es lo que
# esperan una BD o un DataFrame. Esta etapa te AÍSLA: si el proveedor cambia su
# formato, solo tocas aquí. strict=True falla si las listas no miden lo mismo,
# en vez de truncar en silencio.
filas = [{"fecha": f, "temp_max": t}
         for f, t in zip(crudo["daily"]["time"],
                         crudo["daily"]["temperature_2m_max"],
                         strict=True)]

# 3. CARGAR. Junto al script, no en el directorio desde el que lo lances.
destino = Path(__file__).with_name("tiempo.json")
with open(destino, "w", encoding="utf-8") as fich:
    json.dump(filas, fich, indent=2, ensure_ascii=False)   # ensure_ascii: tildes legibles

# Un script que termina en silencio desconcierta.
print(f"{len(filas)} días guardados en {destino.name}")
