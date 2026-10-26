# routers/auth.py — login, refresh con rotación, logout y "quién soy"
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from .esquemas import RefreshIn, TokenOut
from .seguridad import (comprobar_credenciales, decodificar, emitir_pareja,
                        guardar_refresh, refresh_vivos, usuario_actual)

router = APIRouter(prefix="/auth", tags=["auth"])


# OAuth2PasswordRequestForm hace que el login reciba un FORMULARIO, no JSON: lo
# exige el estándar OAuth2, y por eso hace falta python-multipart.
@router.post("/token", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends()):
    if not comprobar_credenciales(form.username, form.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "Usuario o contraseña incorrectos",
                            headers={"WWW-Authenticate": "Bearer"})
    return emitir_pareja(form.username)


# ROTACIÓN: cada refresh sirve una sola vez, lo que delata un robo.
@router.post("/refresh", response_model=TokenOut)
def refrescar(datos: RefreshIn):
    payload = decodificar(datos.refresh_token, "refresh")
    vivos = refresh_vivos()
    if payload.get("jti") not in vivos:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "Refresh token revocado o ya usado")
    del vivos[payload["jti"]]
    guardar_refresh(vivos)
    return emitir_pareja(payload["sub"])


# REVOCACIÓN. Ojo: el access que ya tenga el cliente sigue valiendo hasta caducar.
@router.post("/logout", status_code=204)
def logout(datos: RefreshIn):
    payload = decodificar(datos.refresh_token, "refresh")
    vivos = refresh_vivos()
    vivos.pop(payload.get("jti"), None)
    guardar_refresh(vivos)


@router.get("/me")
def yo(usuario: dict = Depends(usuario_actual)):
    return {"username": usuario["username"], "nombre": usuario["nombre"]}
