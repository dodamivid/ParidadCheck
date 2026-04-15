"""
Tests unitarios para el motor de paridad de ParidadCheck.
Se prueban las 7 reglas directamente (sin capa HTTP).
"""
import pytest
from datetime import date
from fastapi import HTTPException

from backend.models.candidatura import Candidatura
from backend.services.csv_parser import parsear_csv
from backend.services.motor_paridad import validar


# ---------------------------------------------------------------------------
# Helper: construye una Candidatura con valores por defecto válidos
# ---------------------------------------------------------------------------

def make_candidatura(**overrides) -> Candidatura:
    defaults = dict(
        nombre="Candidato Ejemplo",
        genero="M",
        partido="PAN",
        cargo="DIPUTADO_LOCAL",
        tipo="PROPIETARIO",
        posicion=1,
        distrito="D01",
        indigena=False,
        discapacidad=False,
        fecha_nacimiento=date(1985, 6, 15),
        lgbtq=False,
    )
    defaults.update(overrides)
    return Candidatura(**defaults)


def formula(posicion: int, distrito: str, cargo: str,
            genero_prop: str, genero_sup: str,
            nombre_prop: str = None, nombre_sup: str = None) -> list[Candidatura]:
    """Crea una fórmula propietario-suplente."""
    return [
        make_candidatura(
            nombre=nombre_prop or f"Prop {posicion}",
            genero=genero_prop,
            tipo="PROPIETARIO",
            posicion=posicion,
            distrito=distrito,
            cargo=cargo,
        ),
        make_candidatura(
            nombre=nombre_sup or f"Sup {posicion}",
            genero=genero_sup,
            tipo="SUPLENTE",
            posicion=posicion,
            distrito=distrito,
            cargo=cargo,
        ),
    ]


# ---------------------------------------------------------------------------
# Test 1 — Lista perfecta → SUCCESS, todos los criterios cumplen
# ---------------------------------------------------------------------------

def test_lista_perfecta_success():
    """
    20 candidaturas: 10M/10F, perfectamente alternados por posición,
    fórmulas con géneros opuestos, con acción afirmativa completa.
    Resultado esperado: SUCCESS con todos los criterios en cumple=True.
    """
    candidaturas = []

    # 10 fórmulas: propietario M + suplente F, posiciones 1-10
    for i in range(1, 11):
        genero_prop = "M" if i % 2 == 1 else "F"
        genero_sup  = "F" if genero_prop == "M" else "M"
        candidaturas.extend(
            formula(i, "D01", "DIPUTADO_LOCAL", genero_prop, genero_sup)
        )

    # Añadir acciones afirmativas sobre los propietarios sin romper la paridad
    # horizontal: usamos model_copy para preservar genero/tipo/posicion/distrito/cargo
    # originales y solo modificar los campos de acción afirmativa.
    candidaturas[0] = candidaturas[0].model_copy(update={
        "nombre": "Propietario Indígena",
        "indigena": True,
        "fecha_nacimiento": date(2001, 3, 10),  # joven
    })
    candidaturas[2] = candidaturas[2].model_copy(update={
        "nombre": "Propietario Discapacidad",
        "discapacidad": True,
    })
    candidaturas[4] = candidaturas[4].model_copy(update={
        "nombre": "Propietario LGBTQ",
        "lgbtq": True,
    })

    resultado = validar(candidaturas)

    assert resultado.resultado_global == "SUCCESS"
    assert resultado.criterios["paridad_horizontal"]["cumple"] is True
    assert resultado.criterios["paridad_vertical"]["cumple"] is True
    assert resultado.criterios["paridad_transversal"]["cumple"] is True
    assert resultado.criterios["accion_indigena"]["cumple"] is True
    assert resultado.criterios["accion_discapacidad"]["cumple"] is True
    assert resultado.criterios["accion_juventud"]["cumple"] is True
    assert resultado.criterios["accion_lgbtq"]["cumple"] is True
    assert len(resultado.incumplimientos) == 0


# ---------------------------------------------------------------------------
# Test 2 — Violación de paridad vertical → DANGER
# ---------------------------------------------------------------------------

def test_paridad_vertical_violacion_danger():
    """
    Lista donde dos posiciones consecutivas tienen el mismo género.
    Resultado esperado: DANGER, paridad_vertical.cumple == False,
    y los nombres de los candidatos aparecen en incumplimientos.
    """
    # Alternancia correcta salvo posiciones 3 y 4 (ambas M)
    generos = ["M", "F", "M", "M", "F", "F", "M", "F", "M", "F"]
    candidaturas = []
    for i, g in enumerate(generos, start=1):
        tipo = "PROPIETARIO" if i % 2 == 1 else "SUPLENTE"
        nombre = f"Candidato {i}"
        candidaturas.append(
            make_candidatura(
                nombre=nombre, genero=g, tipo=tipo,
                posicion=i, distrito="D01", cargo="DIPUTADO_LOCAL",
                indigena=(i == 1), discapacidad=(i == 3),
                lgbtq=(i == 5), fecha_nacimiento=date(2001, 1, 1) if i == 7 else date(1985, 1, 1),
            )
        )

    resultado = validar(candidaturas)

    assert resultado.resultado_global == "DANGER"
    assert resultado.criterios["paridad_vertical"]["cumple"] is False

    tipos = [inc.tipo for inc in resultado.incumplimientos]
    assert "PARIDAD_VERTICAL" in tipos

    articulos = [inc.articulo for inc in resultado.incumplimientos if inc.tipo == "PARIDAD_VERTICAL"]
    assert all(a == "Art. 233 LGIPE" for a in articulos)


# ---------------------------------------------------------------------------
# Test 3 — Acción afirmativa faltante (discapacidad) → WARNING
# ---------------------------------------------------------------------------

def test_accion_discapacidad_faltante_warning():
    """
    Lista con paridad de género perfecta pero cero candidaturas con discapacidad.
    Resultado esperado: WARNING, accion_discapacidad.cumple == False.
    """
    candidaturas = []
    for i in range(1, 11):
        genero_prop = "M" if i % 2 == 1 else "F"
        genero_sup  = "F" if genero_prop == "M" else "M"
        candidaturas.extend(
            formula(i, "D01", "DIPUTADO_LOCAL", genero_prop, genero_sup)
        )

    # Agregar acciones afirmativas EXCEPTO discapacidad, preservando género/tipo/pos
    # originales con model_copy para no romper la paridad horizontal.
    candidaturas[0] = candidaturas[0].model_copy(update={
        "nombre": "Propietario Indígena",
        "indigena": True,
        "fecha_nacimiento": date(2001, 1, 1),
    })
    candidaturas[2] = candidaturas[2].model_copy(update={
        "nombre": "Propietario LGBTQ",
        "lgbtq": True,
    })

    resultado = validar(candidaturas)

    assert resultado.resultado_global == "WARNING"
    assert resultado.criterios["accion_discapacidad"]["cumple"] is False
    assert resultado.criterios["paridad_horizontal"]["cumple"] is True
    assert resultado.criterios["paridad_vertical"]["cumple"] is True
    assert resultado.criterios["paridad_transversal"]["cumple"] is True

    tipos = [inc.tipo for inc in resultado.incumplimientos]
    assert "ACCION_DISCAPACIDAD" in tipos


# ---------------------------------------------------------------------------
# Test 4 — Violación de paridad horizontal → DANGER
# ---------------------------------------------------------------------------

def test_paridad_horizontal_violacion_danger():
    """
    Una fórmula donde propietario y suplente son del mismo género (ambos M).
    Los nombres de ambos deben aparecer en candidatos_afectados.
    """
    candidaturas = []
    # Fórmula incorrecta en posición 1: M + M
    candidaturas.extend(
        formula(1, "D01", "DIPUTADO_LOCAL", "M", "M",
                nombre_prop="Juan Pérez", nombre_sup="Carlos Ruiz")
    )
    # Resto de fórmulas correctas (F + M)
    for i in range(2, 11):
        genero_prop = "F" if i % 2 == 0 else "M"
        genero_sup  = "M" if genero_prop == "F" else "F"
        candidaturas.extend(
            formula(i, "D01", "DIPUTADO_LOCAL", genero_prop, genero_sup)
        )

    # Acciones afirmativas mínimas
    candidaturas.append(
        make_candidatura(nombre="Indígena", genero="F", tipo="PROPIETARIO",
                         posicion=11, distrito="D01", indigena=True,
                         fecha_nacimiento=date(2001, 1, 1), lgbtq=True, discapacidad=True)
    )

    resultado = validar(candidaturas)

    assert resultado.resultado_global == "DANGER"
    assert resultado.criterios["paridad_horizontal"]["cumple"] is False

    h_incumplimientos = [inc for inc in resultado.incumplimientos if inc.tipo == "PARIDAD_HORIZONTAL"]
    assert len(h_incumplimientos) >= 1
    nombres_afectados = h_incumplimientos[0].candidatos_afectados
    assert "Juan Pérez" in nombres_afectados
    assert "Carlos Ruiz" in nombres_afectados


# ---------------------------------------------------------------------------
# Test 5 — CSV con columna faltante → HTTPException 422
# ---------------------------------------------------------------------------

def test_csv_columna_faltante_422():
    """
    Un CSV que no incluye la columna 'lgbtq' debe lanzar HTTPException 422
    con mención explícita del campo faltante.
    """
    csv_sin_lgbtq = (
        "nombre,genero,partido,cargo,tipo,posicion,distrito,indigena,discapacidad,fecha_nacimiento\n"
        "Ana García,F,PAN,DIPUTADO_LOCAL,PROPIETARIO,1,D01,false,false,1990-05-20\n"
    )

    with pytest.raises(HTTPException) as exc_info:
        parsear_csv(csv_sin_lgbtq.encode("utf-8"))

    assert exc_info.value.status_code == 422
    detalle = str(exc_info.value.detail)
    assert "lgbtq" in detalle.lower()
