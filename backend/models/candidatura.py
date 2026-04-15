from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Modelo interno — usado por el parser y el motor de reglas
# ---------------------------------------------------------------------------

class Candidatura(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str
    genero: str           # M | F | NB  (validado por el parser)
    partido: str
    cargo: str
    tipo: str             # PROPIETARIO | SUPLENTE  (normalizado por el parser)
    posicion: int
    distrito: str
    indigena: bool
    discapacidad: bool
    fecha_nacimiento: date
    lgbtq: bool


# ---------------------------------------------------------------------------
# Modelos de respuesta — estructura exacta del JSON que devuelve /api/validar
# ---------------------------------------------------------------------------

class CriterioParidad(BaseModel):
    cumple: bool
    porcentaje_cumplimiento: float
    articulo: str
    descripcion: str


class Incumplimiento(BaseModel):
    tipo: str
    descripcion: str
    candidatos_afectados: list[str]
    articulo: str
    sugerencia: str


class ResultadoValidacion(BaseModel):
    partido: str
    total_candidaturas: int
    resultado_global: Literal["SUCCESS", "WARNING", "DANGER"]
    criterios: dict[str, Any]
    incumplimientos: list[Incumplimiento]
