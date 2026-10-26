# probar_auth.py — el ciclo de vida completo, contra el servidor en marcha
#
# Levantamos la API en otra terminal antes de ejecutarlo:
#     cd 05_produccion
#     $env:JWT_SECRET = "un-secreto-largo-y-aleatorio"
#     uvicorn 06_auth_jwt:app --port 8000
#
# Recorre las seis etapas de una sesión OAuth2 y demuestra sus garantías: que el
# refresh rota, que el logout revoca y que un token usado no vuelve a servir.
import requests

BASE = "http://127.0.0.1:8000"
# Contra el despliegue real: BASE = "https://apis-y-servicios-de-datos.onrender.com"

# Estas credenciales deben existir en usuarios.csv (si no, las creamos con
# crear_usuario.py).
USUARIO = "manuel"
CLAVE = "pepito"

# 1. Login: OAuth2 manda las credenciales como FORMULARIO (data=), no como JSON.
r = requests.post(f"{BASE}/auth/token",
                  data={"username": USUARIO, "password": CLAVE}, timeout=10)
r.raise_for_status()
tokens = r.json()
print("1. Login OK - access y refresh recibidos")

# 2. Petición autenticada. "Bearer" = al portador: el token vale por sí mismo.
cab = {"Authorization": f"Bearer {tokens['access_token']}"}
r = requests.get(f"{BASE}/auth/me", headers=cab, timeout=10)
r.raise_for_status()
print("2. /auth/me:", r.json())

# 3. Refresh: entrego el refresh, recibo una pareja NUEVA (rotación).
r = requests.post(f"{BASE}/auth/refresh",
                  json={"refresh_token": tokens["refresh_token"]}, timeout=10)
r.raise_for_status()
nuevos = r.json()
print("3. Refresh OK - pareja nueva emitida")

# 4. El refresh viejo ya no vale: fue rotado. A partir de aquí no usamos
#    raise_for_status: los fallos son el resultado esperado.
r = requests.post(f"{BASE}/auth/refresh",
                  json={"refresh_token": tokens["refresh_token"]}, timeout=10)
print("4. Refresh viejo ->", r.status_code, r.json().get("detail"))

# 5. Logout: revoco el refresh vigente. Responde 204, sin cuerpo.
r = requests.post(f"{BASE}/auth/logout",
                  json={"refresh_token": nuevos["refresh_token"]}, timeout=10)
print("5. Logout ->", r.status_code)

# 6. Refrescar tras el logout: imposible. La revocación es real.
r = requests.post(f"{BASE}/auth/refresh",
                  json={"refresh_token": nuevos["refresh_token"]}, timeout=10)
print("6. Refresh tras logout ->", r.status_code, r.json().get("detail"))

# NOTA: el access token del paso 2 SIGUE funcionando tras el logout, hasta que
# caduque. Es el precio de que los JWT sean autosuficientes, y la razón de sus 15 min.
