# 06_auth_jwt.py — OAuth2 completo: login, JWT de acceso, refresh con rotación y logout
#
#     cd 05_produccion
#     $env:JWT_SECRET = "un-secreto-largo-y-aleatorio"    <- OBLIGATORIO, antes de arrancar
#     uvicorn 06_auth_jwt:app --reload --port 8000
#
# El nivel siguiente a la API key de 04_api_key.py. Lo probamos con
# herramientas/probar_auth.py, o desde /docs con el botón "Authorize".
#
# LA IDEA CENTRAL SON DOS TOKENS CON PAPELES DISTINTOS:
#   - access  (minutos) viaja en CADA petición; robarlo sirve de poco, caduca ya.
#   - refresh (días)    casi no viaja; solo pide un access nuevo cuando caduca.
# Así hay sesiones largas sin credenciales de larga vida circulando por ahí.
import csv
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

# --- Configuración ---
# El secreto con el que se FIRMAN los tokens: quien lo tenga puede fabricar
# tokens de cualquier usuario. Nunca va en el código.
SECRETO = os.environ.get("JWT_SECRET")
if not SECRETO:
    # Mejor morir al arrancar con un mensaje claro que con un KeyError críptico.
    raise RuntimeError(
        "Falta la variable de entorno JWT_SECRET.\n"
        '  PowerShell: $env:JWT_SECRET = "un-secreto-largo-y-aleatorio"\n'
        '  Docker:     docker run -e JWT_SECRET="..." -p 8000:8000 imagen_citas'
    )

ALGORITMO = "HS256"
ACCESO_MIN = 15                              # vida del access token (bájalo a 1 para verlo caducar)
REFRESH_DIAS = 7                             # vida del refresh token

# Rutas relativas al script: en el contenedor el cwd es /app.
FICHERO_USUARIOS = Path(__file__).with_name("usuarios.csv")
FICHERO_REFRESH = Path(__file__).with_name("refresh_tokens.json")

app = FastAPI(title="Demo OAuth2 + JWT", version="1.0")

# Indica a FastAPI dónde se piden los tokens: de ahí sale el formulario de "Authorize".
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/token")


# --- Almacén de usuarios (CSV) ---
# Se relee en cada llamada (al contrario que el modelo): así podemos dar de alta a
# alguien con herramientas/crear_usuario.py y entrar sin reiniciar. Con una BD
# sería una consulta, y el planteamiento es el mismo.
def cargar_usuarios() -> dict[str, dict]:
    with FICHERO_USUARIOS.open(newline="", encoding="utf-8") as f:
        return {fila["username"]: fila for fila in csv.DictReader(f)}


# --- Registro de refresh tokens vivos (JSON): el estado que permite revocar ---
#
# LA TENSIÓN DE FONDO DE TODO JWT: es autosuficiente (se valida con la firma, sin
# consultar nada) y por eso mismo NO SE PUEDE REVOCAR — vale hasta que caduque,
# aunque cerremos sesión. Solución: los access se dejan stateless porque duran
# minutos, y de los refresh, que duran días, se lleva registro. Este JSON es lo
# único que hace posibles el logout y la rotación.
def refresh_vivos() -> dict:
    if not FICHERO_REFRESH.exists():
        return {}
    vivos = json.loads(FICHERO_REFRESH.read_text(encoding="utf-8"))
    ahora = datetime.now(timezone.utc).isoformat()
    return {jti: d for jti, d in vivos.items() if d["expira"] > ahora}  # purga caducados


def guardar_refresh(vivos: dict) -> None:
    # Un JSON vale para un laboratorio; en producción sería Redis o una tabla
    # (aquí dos peticiones simultáneas podrían pisarse).
    FICHERO_REFRESH.write_text(json.dumps(vivos, indent=2), encoding="utf-8")


# --- Fabricar y verificar tokens ---
#
# AVISO: un JWT va FIRMADO, no cifrado. Copiamos uno en jwt.io y lo veremos en claro.
# La firma garantiza que nadie lo ha MODIFICADO, no que nadie lo haya leído:
# en el payload nunca van datos sensibles.
def crear_token(username: str, tipo: str, vida: timedelta, jti: str | None = None) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": username,          # subject: de quién es el token
        "type": tipo,             # "access" o "refresh": impide usar uno como el otro
        "iat": ahora,             # issued at
        "exp": ahora + vida,      # expiración: jwt.decode la comprueba por ti
    }
    if jti:
        payload["jti"] = jti      # id único del token: la llave de la revocación
    return jwt.encode(payload, SECRETO, algorithm=ALGORITMO)


def emitir_pareja(username: str) -> dict:
    jti = str(uuid.uuid4())
    vivos = refresh_vivos()
    vivos[jti] = {
        "username": username,
        "expira": (datetime.now(timezone.utc) + timedelta(days=REFRESH_DIAS)).isoformat(),
    }
    guardar_refresh(vivos)
    return {
        "access_token": crear_token(username, "access", timedelta(minutes=ACCESO_MIN)),
        "refresh_token": crear_token(username, "refresh", timedelta(days=REFRESH_DIAS), jti),
        "token_type": "bearer",
    }


def decodificar(token: str, tipo: str) -> dict:
    try:
        # decode comprueba la firma Y la caducidad: un byte tocado y ya no cuadra.
        payload = jwt.decode(token, SECRETO, algorithms=[ALGORITMO])
    except jwt.ExpiredSignatureError:
        # Antes que InvalidTokenError, que es su clase padre: al revés nunca
        # distinguiríamos "caducado" de "inválido".
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token caducado")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")

    # Sin esto, un refresh (que dura DÍAS) valdría como access. El campo "type"
    # es lo que mantiene separados los dos papeles.
    if payload.get("type") != tipo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Se esperaba un token de tipo {tipo}")
    return payload


# --- Dependencia: usuario actual a partir del access token ---
# Depends(oauth2) extrae el token de "Authorization: Bearer ...". Cualquier
# endpoint que dependa de esta función queda protegido con una línea.
def usuario_actual(token: str = Depends(oauth2)) -> dict:
    payload = decodificar(token, "access")
    usuario = cargar_usuarios().get(payload["sub"])
    if usuario is None:
        # Token válido pero cuenta borrada mientras seguía vivo: el hueco del JWT.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "El usuario ya no existe")
    return usuario


# --- Contratos ---
class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshIn(BaseModel):
    refresh_token: str


# --- Endpoints ---
# OAuth2PasswordRequestForm hace que el login reciba un FORMULARIO, no JSON: lo
# exige el estándar OAuth2, y por eso hace falta python-multipart.
@app.post("/auth/token", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends()):
    usuario = cargar_usuarios().get(form.username)

    # Un solo mensaje para ambos casos: decir "ese usuario no existe" confirmaría
    # a un atacante qué cuentas SÍ existen.
    if usuario is None or not bcrypt.checkpw(form.password.encode(), usuario["hash"].encode()):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return emitir_pareja(form.username)


# ROTACIÓN: cada refresh sirve UNA sola vez. Es una alarma antirrobo: si alguien
# nos copia el refresh y lo usa, el nuestro dará "revocado o ya usado".
@app.post("/auth/refresh", response_model=TokenOut)
def refrescar(datos: RefreshIn):
    payload = decodificar(datos.refresh_token, "refresh")
    vivos = refresh_vivos()
    if payload.get("jti") not in vivos:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token revocado o ya usado")
    del vivos[payload["jti"]]          # ROTACIÓN: cada refresh sirve UNA sola vez
    guardar_refresh(vivos)
    return emitir_pareja(payload["sub"])


# REVOCACIÓN: cerrar sesión es borrar el refresh del registro. Ojo: el access que
# ya tenga el cliente SIGUE valiendo hasta caducar — de ahí sus minutos de vida.
@app.post("/auth/logout", status_code=204)
def logout(datos: RefreshIn):
    payload = decodificar(datos.refresh_token, "refresh")
    vivos = refresh_vivos()
    vivos.pop(payload.get("jti"), None)   # REVOCACIÓN: el refresh muere ahora mismo
    guardar_refresh(vivos)


@app.get("/auth/me")
def yo(usuario: dict = Depends(usuario_actual)):
    return {"username": usuario["username"], "nombre": usuario["nombre"]}


@app.get("/v1/secreto")
def secreto(usuario: dict = Depends(usuario_actual)):
    return {"mensaje": f"Solo para tus ojos, {usuario['nombre']}"}


@app.get("/health")
def health():
    return {"status": "ok"}
