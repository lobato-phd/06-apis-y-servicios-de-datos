# 01b — La misma consulta que 01a, con los tres hábitos que la hacen fiable.
import requests

r = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={
        "latitude": 40.97,  # Si cambiamos a 999 tendremos un 400: Bad Request
        "longitude": -5.66,
        "current_weather": True,  # Si cambiamos a False, tendremos el "mensaje bonito"
    },
    timeout=10,  # Hábito 1: timeout SIEMPRE. Sin él, un servidor lento bloquea el proceso.
)

# Hábito 2: comprobar el estado. Lanza excepción si 4xx o 5xx.
r.raise_for_status()

datos = r.json()

# Hábito 3: acceso defensivo. .get() devuelve None en vez de reventar con KeyError;
# el {} intermedio permite encadenar aunque falte el nivel superior.
temperatura = datos.get("current_weather", {}).get("temperature")
if temperatura is None:
    print("La respuesta no trae lo esperado")
else:
    print(f"Temperatura actual: {temperatura} °C")
