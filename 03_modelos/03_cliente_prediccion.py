# 03_cliente_prediccion.py — pedirle una predicción a NUESTRA propia API
#
# Levantamos la API del modelo en otra terminal antes de ejecutarlo:
#     cd 03_modelos
#     uvicorn 02_servir_modelo:app --port 8000
#
# (/v1/predict lo sirve la API de este capítulo, no la de citas del capítulo 2.
#  Para los dos endpoints a la vez, arrancamos cualquiera de las de 05_produccion.)
import requests

BASE = "http://127.0.0.1:8000"

# LA NOVEDAD: el parámetro `json=`. Hasta ahora usábamos `params=`, que rellena la
# query string; `json=` serializa el dict al CUERPO de la petición y pone por nosotros
# la cabecera Content-Type. Es la diferencia GET/POST en código: los filtros van en la
# URL, los datos van en el cuerpo.
r = requests.post(
    f"{BASE}/v1/predict",
    json={"largo_sepalo": 5.1,
          "ancho_sepalo": 3.5,
          "largo_petalo": 1.4,
          "ancho_petalo": 0.2},
    timeout=10,
)

# Aquí raise_for_status gana un matiz: si mandamos un pétalo negativo, la API responde
# 422 y esta línea lanza excepción. El contrato de Pydantic del servidor se convierte,
# del lado del cliente, en un error de Python que podemos capturar.
r.raise_for_status()

print("Predicción:", r.json())
