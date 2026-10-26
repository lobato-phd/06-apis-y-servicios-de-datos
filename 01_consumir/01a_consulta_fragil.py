# 01a — La versión ingenua: funciona hoy, falla mañana.
# La escribimos SIN red de seguridad a propósito. La compararemos con 01b.
import requests

# params construye la query string y codifica los valores por nosotros
r = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={
        "latitude": 40.97,      # Salamanca
        "longitude": -5.66,
        "current_weather": True,
    },
    # FALLO 1: sin timeout, si el servidor no responde el script se cuelga para siempre
)

# FALLO 2: imprimimos el código pero no actuamos sobre él; un 500 seguiría adelante
print(r.status_code)

datos = r.json()          # JSON -> dict de Python

# FALLO 3: acceso directo con []. Si falta la clave -> KeyError y traceback
print(datos["current_weather"]["temperature"])
