"""
Tests de performance para ParidadCheck.

Issue #1 exige que el endpoint /api/validar-csv responda en menos de 500ms
con un CSV de hasta 500 filas. Este archivo genera un CSV de 500 candidaturas
con paridad perfecta y todas las acciones afirmativas cubiertas, lo envía
al endpoint vía TestClient y mide el tiempo de respuesta wall clock.
"""
import math
import time

from fastapi.testclient import TestClient

from backend.constants.legislacion import (
    UMBRAL_DISCAPACIDAD,
    UMBRAL_INDIGENA,
    UMBRAL_JUVENTUD,
    UMBRAL_LGBTQ,
)
from backend.main import app

client = TestClient(app)

PERFORMANCE_BUDGET_MS = 500
TOTAL_FILAS = 500
FORMULAS = TOTAL_FILAS // 2  # 250 fórmulas propietario-suplente


def _build_500_row_csv() -> bytes:
    """
    Genera un CSV de 500 candidaturas válidas:
    - 250 fórmulas propietario-suplente
    - Propietarios alternando M (posiciones impares) y F (pares) → paridad vertical OK
    - Suplentes con género opuesto al propietario → paridad horizontal OK
    - 250 M + 250 F en total → paridad transversal 50/50 exacta
    - Acciones afirmativas aplicadas sobre propietarios (no rompen horizontal)
    """
    n_indigena    = math.ceil(TOTAL_FILAS * UMBRAL_INDIGENA)     # 15
    n_discap      = math.ceil(TOTAL_FILAS * UMBRAL_DISCAPACIDAD) #  5
    n_lgbtq       = math.ceil(TOTAL_FILAS * UMBRAL_LGBTQ)        #  5
    n_jovenes     = math.ceil(TOTAL_FILAS * UMBRAL_JUVENTUD)     #  5

    # Rangos de índices (sobre propietarios, 0-indexed) para cada acción afirmativa
    rango_indigena = (0, n_indigena)
    rango_discap   = (n_indigena, n_indigena + n_discap)
    rango_lgbtq    = (n_indigena + n_discap, n_indigena + n_discap + n_lgbtq)
    rango_jovenes  = (n_indigena + n_discap + n_lgbtq,
                      n_indigena + n_discap + n_lgbtq + n_jovenes)

    lines = [
        "nombre,genero,partido,cargo,tipo,posicion,distrito,"
        "indigena,discapacidad,fecha_nacimiento,lgbtq"
    ]

    for pos in range(1, FORMULAS + 1):
        idx_prop = pos - 1
        genero_prop = "M" if pos % 2 == 1 else "F"
        genero_sup  = "F" if genero_prop == "M" else "M"

        indigena    = "true" if rango_indigena[0]    <= idx_prop < rango_indigena[1]    else "false"
        discapacidad= "true" if rango_discap[0]      <= idx_prop < rango_discap[1]      else "false"
        lgbtq       = "true" if rango_lgbtq[0]       <= idx_prop < rango_lgbtq[1]       else "false"
        fecha_prop  = "2001-03-10" if rango_jovenes[0] <= idx_prop < rango_jovenes[1] else "1985-06-15"

        lines.append(
            f"Propietario {pos},{genero_prop},PAN,DIPUTADO_LOCAL,PROPIETARIO,{pos},D01,"
            f"{indigena},{discapacidad},{fecha_prop},{lgbtq}"
        )
        lines.append(
            f"Suplente {pos},{genero_sup},PAN,DIPUTADO_LOCAL,SUPLENTE,{pos},D01,"
            f"false,false,1988-03-20,false"
        )

    return "\n".join(lines).encode("utf-8")


def test_validar_csv_500_filas_bajo_budget():
    """
    Issue #1: el endpoint debe responder en <500ms con un CSV de 500 filas.
    Mide el wall clock del request completo (upload + parseo + validación + serialización).
    """
    csv_bytes = _build_500_row_csv()

    # Sanity checks del fixture generado
    assert csv_bytes.count(b"\n") == TOTAL_FILAS, (
        f"El CSV generado tiene {csv_bytes.count(b'\\n')} saltos de línea, "
        f"se esperaban {TOTAL_FILAS} (header + 500 filas de datos)."
    )

    # Warmup: primera llamada para pagar el costo de imports lazy / caches
    warmup = client.post(
        "/api/validar-csv",
        files={"archivo": ("candidaturas_500.csv", csv_bytes, "text/csv")},
    )
    assert warmup.status_code == 200, f"Warmup falló: {warmup.text}"

    # Medición real
    start = time.perf_counter()
    response = client.post(
        "/api/validar-csv",
        files={"archivo": ("candidaturas_500.csv", csv_bytes, "text/csv")},
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200, f"Endpoint falló: {response.text}"

    body = response.json()
    assert body["total_candidaturas"] == TOTAL_FILAS
    assert body["partido"] == "PAN"
    assert body["resultado_global"] == "SUCCESS", (
        f"El fixture de 500 filas no cumple paridad perfecta: "
        f"resultado={body['resultado_global']}, incumplimientos={body['incumplimientos']}"
    )

    assert elapsed_ms < PERFORMANCE_BUDGET_MS, (
        f"El endpoint tardó {elapsed_ms:.1f}ms con {TOTAL_FILAS} candidaturas, "
        f"excede el budget de {PERFORMANCE_BUDGET_MS}ms definido en Issue #1."
    )
