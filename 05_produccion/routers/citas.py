# routers/citas.py — todo lo que tiene que ver con citas, en un solo sitio
#
# Un APIRouter es una mini-aplicación: tiene los mismos decoradores que `app`
# (.get, .post, .put...) pero no sabe servir sola. 07_app.py la monta con
# include_router y entonces sus rutas pasan a existir.
from fastapi import APIRouter, Depends, HTTPException, Query

from . import estado
from .esquemas import Cita, CitaOut, CitaParcial, ListaCitasOut
from .seguridad import usuario_actual

# prefix: todas las rutas de abajo cuelgan de /v1/citas, y aquí se escriben en corto.
# tags:   agrupa estos endpoints bajo un mismo título en /docs.
router = APIRouter(prefix="/v1/citas", tags=["citas"])


# ------------------------------------------------------------------ lectura
@router.get("", response_model=ListaCitasOut)
def listar(autor: str | None = None,
           limite: int | None = Query(default=None, ge=1, description="Sin valor: todas"),
           desplazamiento: int = Query(default=0, ge=0)):
    datos = estado.CITAS
    if autor:
        datos = [c for c in datos if autor.lower() in c["autor"].lower()]
    return {"total": len(datos),
            "resultados": (datos[desplazamiento:] if limite is None
                           else datos[desplazamiento : desplazamiento + limite])}


@router.get("/{indice}", response_model=CitaOut)
def detalle(indice: int):
    if not 0 <= indice < len(estado.CITAS):
        raise HTTPException(404, "Cita no encontrada")
    return estado.CITAS[indice]


# ------------------------------------------------------------------ escritura
# Leer es público, escribir exige token. Depends(usuario_actual) corre ANTES que el
# cuerpo de la función: sin token válido, la petición no llega a tocar los datos.
#
# (Si TODAS las rutas del router necesitaran token, se pondría una sola vez en el
#  propio router: APIRouter(..., dependencies=[Depends(usuario_actual)]).)
@router.post("", response_model=CitaOut, status_code=201)
def crear(cita: Cita, usuario: dict = Depends(usuario_actual)):
    nueva = cita.model_dump()
    nueva["id_interno"] = len(estado.CITAS)
    estado.CITAS.append(nueva)
    estado.logger.info(f"{usuario['username']} creó una cita de {nueva['autor']}")
    return nueva


# PUT sustituye el recurso entero: omitir `likes` lo deja en 0, no lo conserva.
@router.put("/{indice}", response_model=CitaOut)
def reemplazar(indice: int, cita: Cita, usuario: dict = Depends(usuario_actual)):
    if not 0 <= indice < len(estado.CITAS):
        raise HTTPException(404, "Cita no encontrada")
    nueva = cita.model_dump()
    nueva["id_interno"] = estado.CITAS[indice].get("id_interno", indice)
    estado.CITAS[indice] = nueva
    return nueva


# PATCH modifica solo lo enviado: sin exclude_unset, los campos ausentes llegarían
# como None y borrarían los datos existentes.
@router.patch("/{indice}", response_model=CitaOut)
def modificar(indice: int, cambios: CitaParcial, usuario: dict = Depends(usuario_actual)):
    if not 0 <= indice < len(estado.CITAS):
        raise HTTPException(404, "Cita no encontrada")
    estado.CITAS[indice].update(cambios.model_dump(exclude_unset=True))
    return estado.CITAS[indice]


# 204: hecho, y sin cuerpo que devolver.
# Ojo: el identificador es la POSICIÓN, así que al borrar cambian las siguientes.
@router.delete("/{indice}", status_code=204)
def borrar(indice: int, usuario: dict = Depends(usuario_actual)):
    if not 0 <= indice < len(estado.CITAS):
        raise HTTPException(404, "Cita no encontrada")
    estado.CITAS.pop(indice)
    estado.logger.info(f"{usuario['username']} borró la cita {indice}")
