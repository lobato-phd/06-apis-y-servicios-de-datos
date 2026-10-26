# routers/externo.py — salud y el proveedor de terceros
from fastapi import APIRouter, Depends, HTTPException
import requests

from . import estado
from .seguridad import verificar_api_key

router = APIRouter(tags=["operación"])


# Sin protección a propósito: la plataforma que lo consulta no tiene credenciales.
@router.get("/health")
def health():
    return {"status": "ok",
            "modelo_cargado": estado.modelo is not None,
            "citas_cargadas": len(estado.CITAS)}


# El eslabón que no controlamos: blindado con timeout, log y 503 controlado.
@router.get("/v1/tiempo")
def tiempo():
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": 40.97, "longitude": -5.66, "current_weather": True},
            timeout=5,               # timeout SIEMPRE
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException as exc:
        # El log lleva la causa técnica; el cliente recibe un 503 sin detalles internos.
        estado.logger.error(f"Proveedor externo caído: {exc}")
        raise HTTPException(503, "Servicio externo no disponible, reintenta en unos minutos")


# Capa 1 de seguridad, para compararla con el JWT de las citas.
@router.get("/v1/privado", dependencies=[Depends(verificar_api_key)], tags=["seguridad"])
def privado():
    return {"acceso": "concedido"}
