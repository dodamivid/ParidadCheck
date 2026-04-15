import io
from datetime import datetime

import pandas as pd
from fastapi import HTTPException

from backend.constants.legislacion import COLUMNAS_REQUERIDAS, GENEROS_VALIDOS, TIPOS_VALIDOS
from backend.models.candidatura import Candidatura

# Valores booleanos aceptados (case-insensitive)
_BOOL_TRUE  = {"true", "1", "si", "sí", "yes"}
_BOOL_FALSE = {"false", "0", "no"}


def _parse_bool(value: str, columna: str, fila: int) -> bool:
    """Convierte una cadena a bool. Lanza HTTPException(422) si el valor no es reconocido."""
    normalizado = value.strip().lower()
    if normalizado in _BOOL_TRUE:
        return True
    if normalizado in _BOOL_FALSE:
        return False
    raise HTTPException(
        status_code=422,
        detail=f"Fila {fila}: valor '{value}' en columna '{columna}' no es booleano válido "
               f"(acepta: true/false, 1/0, si/no).",
    )


def parsear_csv(file_bytes: bytes) -> list[Candidatura]:
    """
    Parsea el contenido de un archivo CSV en bytes y devuelve una lista de Candidatura.

    Raises:
        HTTPException(422): Si el CSV tiene columnas faltantes, valores inválidos,
                            registros de múltiples partidos, o cualquier error de formato.
    """
    try:
        df = pd.read_csv(
            io.BytesIO(file_bytes),
            dtype=str,
            encoding="utf-8-sig",   # maneja BOM que agrega Excel
            keep_default_na=False,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"No se pudo leer el CSV: {exc}") from exc

    # Normalizar nombres de columnas (strip de espacios)
    df.columns = df.columns.str.strip()

    # 1. Verificar columnas requeridas
    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltantes:
        raise HTTPException(
            status_code=422,
            detail=f"Columnas faltantes en el CSV: {', '.join(faltantes)}",
        )

    if df.empty:
        raise HTTPException(status_code=422, detail="El CSV no contiene registros.")

    # 2. Normalizar strings: strip + uppercase en campos clave
    for col in ["nombre", "partido", "cargo", "distrito"]:
        df[col] = df[col].str.strip()
    df["genero"] = df["genero"].str.strip().str.upper()
    df["tipo"]   = df["tipo"].str.strip().str.upper()

    # 3. Validar partido único
    partidos = df["partido"].unique()
    if len(partidos) > 1:
        raise HTTPException(
            status_code=422,
            detail=f"El CSV contiene múltiples partidos: {', '.join(partidos)}. "
                   "Suba un CSV por partido.",
        )

    # 4. Acumular errores fila por fila antes de lanzar la excepción
    errores: list[str] = []
    candidaturas: list[Candidatura] = []

    for idx, row in df.iterrows():
        fila = int(idx) + 2  # 1-indexed, contando encabezado

        # genero
        if row["genero"] not in GENEROS_VALIDOS:
            errores.append(
                f"Fila {fila}: genero '{row['genero']}' inválido. Valores permitidos: M, F, NB."
            )

        # tipo
        if row["tipo"] not in TIPOS_VALIDOS:
            errores.append(
                f"Fila {fila}: tipo '{row['tipo']}' inválido. Valores permitidos: PROPIETARIO, SUPLENTE."
            )

        # posicion
        try:
            posicion = int(row["posicion"])
        except (ValueError, TypeError):
            errores.append(f"Fila {fila}: posicion '{row['posicion']}' no es un número entero.")
            posicion = None

        # fecha_nacimiento
        try:
            fecha_nacimiento = datetime.strptime(row["fecha_nacimiento"].strip(), "%Y-%m-%d").date()
        except ValueError:
            errores.append(
                f"Fila {fila}: fecha_nacimiento '{row['fecha_nacimiento']}' inválida. "
                "Use el formato YYYY-MM-DD."
            )
            fecha_nacimiento = None

        # booleanos — acumular errores individualmente
        try:
            indigena = _parse_bool(row["indigena"], "indigena", fila)
        except HTTPException as exc:
            errores.append(exc.detail)
            indigena = None

        try:
            discapacidad = _parse_bool(row["discapacidad"], "discapacidad", fila)
        except HTTPException as exc:
            errores.append(exc.detail)
            discapacidad = None

        try:
            lgbtq = _parse_bool(row["lgbtq"], "lgbtq", fila)
        except HTTPException as exc:
            errores.append(exc.detail)
            lgbtq = None

        # Solo construir la candidatura si no hubo errores en esta fila
        if not any(
            f"Fila {fila}:" in e for e in errores
        ):
            candidaturas.append(
                Candidatura(
                    nombre=row["nombre"],
                    genero=row["genero"],
                    partido=row["partido"],
                    cargo=row["cargo"],
                    tipo=row["tipo"],
                    posicion=posicion,
                    distrito=row["distrito"],
                    indigena=indigena,
                    discapacidad=discapacidad,
                    fecha_nacimiento=fecha_nacimiento,
                    lgbtq=lgbtq,
                )
            )

    if errores:
        raise HTTPException(
            status_code=422,
            detail={"mensaje": "El CSV contiene errores de formato.", "errores": errores},
        )

    return candidaturas
