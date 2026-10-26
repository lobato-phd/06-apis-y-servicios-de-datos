# esquemas.py — los contratos Pydantic, en un sitio y no repetidos
#
# Los routers los importan de aquí. Cuando un modelo se usa en dos endpoints de
# ficheros distintos, tenerlo suelto en cada uno es la forma más rápida de que
# acaben divergiendo.
from pydantic import BaseModel, Field


class Cita(BaseModel):                      # entrada: crear o reemplazar
    texto: str = Field(min_length=1, max_length=500)
    autor: str = Field(min_length=2)
    etiquetas: list[str] = []
    likes: int = Field(default=0, ge=0)


class CitaParcial(BaseModel):               # entrada: modificar solo lo enviado
    texto: str | None = Field(default=None, min_length=1, max_length=500)
    autor: str | None = Field(default=None, min_length=2)
    etiquetas: list[str] | None = None
    likes: int | None = Field(default=None, ge=0)


class CitaOut(BaseModel):                   # salida: sin id_interno
    texto: str
    autor: str
    etiquetas: list[str]


class ListaCitasOut(BaseModel):
    total: int
    resultados: list[CitaOut]


class Medidas(BaseModel):
    largo_sepalo: float = Field(gt=0, lt=15, description="cm")
    ancho_sepalo: float = Field(gt=0, lt=15, description="cm")
    largo_petalo: float = Field(gt=0, lt=15, description="cm")
    ancho_petalo: float = Field(gt=0, lt=15, description="cm")


class Prediccion(BaseModel):
    especie: str
    confianza: float


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshIn(BaseModel):
    refresh_token: str
