# 06_cliente.py — consumir TU propia API, con los hábitos del Bloque 1
#
# Levanta la API en otra terminal antes de ejecutarlo:
#     cd 02_construir
#     uvicorn 05_contrato_salida:app --port 8000
#
#
# Mira el log de Uvicorn mientras corre: dos programas tuyos hablándose por HTTP.
import requests

# La URL base en una constante: el día que deje de ser 127.0.0.1, se cambia en un sitio.
BASE = "http://127.0.0.1:8000"

# Hábitos 1 y 2, los mismos que en 01_consumir/01b_consulta_robusta.py.
r = requests.get(f"{BASE}/v1/citas", params={"autor": "einstein"}, timeout=10)
r.raise_for_status()
datos = r.json()

print(f"{datos['total']} citas de Einstein; la primera:")

# Hábito 3: acceso defensivo. Que la API sea tuya no garantiza que hoy traiga datos;
# si el filtro no encuentra nada, el [0] reventaría con IndexError.
if datos["resultados"]:
    print("  " + datos["resultados"][0]["texto"][:60] + "...")
else:
    print("  (ninguna: la API no ha devuelto resultados)")
