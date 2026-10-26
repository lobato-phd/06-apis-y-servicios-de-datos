# seguridad.py — las dos capas: API key y OAuth2 + JWT
#
# Vive aparte de los routers porque lo usan varios: `usuario_actual` protege la
# escritura de citas, y también /auth/me. Una dependencia compartida en un módulo
# propio es el patrón normal en cuanto la app pasa de un fichero.
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from . import estado

# --- Capa 1: API key ---
cabecera_api_key = APIKeyHeader(name="X-API-Key")


def verificar_api_key(key: str = Security(cabecera_api_key)):
    if estado.API_KEY is None:
        estado.logger.error("API_KEY no está definida en el entorno")
        raise HTTPException(500, "El servidor no tiene configurada su API key")
    if not secrets.compare_digest(key, estado.API_KEY):   # tiempo constante
        raise HTTPException(401, "API key inválida")


# --- Capa 2: OAuth2 + JWT ---
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/token")


# Un JWT no se puede revocar: por eso los access duran minutos y de los refresh,
# que duran días, se lleva registro aquí. Es lo que hace posible el logout.
def refresh_vivos() -> dict:
    if not estado.FICHERO_REFRESH.exists():
        return {}
    vivos = json.loads(estado.FICHERO_REFRESH.read_text(encoding="utf-8"))
    ahora = datetime.now(timezone.utc).isoformat()
    return {jti: d for jti, d in vivos.items() if d["expira"] > ahora}


def guardar_refresh(vivos: dict) -> None:
    estado.FICHERO_REFRESH.write_text(json.dumps(vivos, indent=2), encoding="utf-8")


# Un JWT va FIRMADO, no cifrado: en el payload nunca van datos sensibles.
def crear_token(username: str, tipo: str, vida: timedelta, jti: str | None = None) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {"sub": username, "type": tipo, "iat": ahora, "exp": ahora + vida}
    if jti:
        payload["jti"] = jti
    return jwt.encode(payload, estado.SECRETO, algorithm=estado.ALGORITMO)


def emitir_pareja(username: str) -> dict:
    jti = str(uuid.uuid4())
    vivos = refresh_vivos()
    vivos[jti] = {
        "username": username,
        "expira": (datetime.now(timezone.utc)
                   + timedelta(days=estado.REFRESH_DIAS)).isoformat(),
    }
    guardar_refresh(vivos)
    return {
        "access_token": crear_token(username, "access",
                                    timedelta(minutes=estado.ACCESO_MIN)),
        "refresh_token": crear_token(username, "refresh",
                                     timedelta(days=estado.REFRESH_DIAS), jti),
        "token_type": "bearer",
    }


def decodificar(token: str, tipo: str) -> dict:
    try:
        payload = jwt.decode(token, estado.SECRETO, algorithms=[estado.ALGORITMO])
    except jwt.ExpiredSignatureError:       # antes que InvalidTokenError, su clase padre
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token caducado")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")
    # Sin esto, un refresh (que dura DÍAS) valdría como access.
    if payload.get("type") != tipo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            f"Se esperaba un token de tipo {tipo}")
    return payload


def comprobar_credenciales(username: str, password: str) -> bool:
    usuario = estado.cargar_usuarios().get(username)
    # Un solo mensaje para ambos casos: decir cuál falla confirmaría qué cuentas existen.
    return usuario is not None and bcrypt.checkpw(password.encode(),
                                                  usuario["hash"].encode())


def usuario_actual(token: str = Depends(oauth2)) -> dict:
    payload = decodificar(token, "access")
    usuario = estado.cargar_usuarios().get(payload["sub"])
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "El usuario ya no existe")
    return usuario
