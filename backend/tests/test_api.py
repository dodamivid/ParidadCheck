"""
Tests de integración HTTP para los endpoints de ParidadCheck.
Usan FastAPI TestClient (no requieren servidor corriendo).
"""
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper — payload mínimo válido con paridad perfecta y acciones afirmativas
# ---------------------------------------------------------------------------

def _payload_lista_perfecta() -> list[dict]:
    """
    10 candidaturas organizadas en 5 fórmulas propietario-suplente:
    - 5 propietarios alternando M/F por posición
    - 5 suplentes con género opuesto al propietario de su fórmula
    - 1 indígena, 1 discapacidad, 1 LGBTQ+, 1 joven (nacida en 2001)
    """
    candidaturas = []
    for i in range(1, 6):
        genero_prop = "M" if i % 2 == 1 else "F"
        genero_sup  = "F" if genero_prop == "M" else "M"
        candidaturas.append({
            "nombre": f"Propietario {i}",
            "genero": genero_prop,
            "partido": "PAN",
            "cargo": "DIPUTADO_LOCAL",
            "tipo": "PROPIETARIO",
            "posicion": i,
            "distrito": "D01",
            "indigena": i == 1,
            "discapacidad": i == 2,
            "lgbtq": i == 3,
            "fecha_nacimiento": "2001-05-15" if i == 4 else "1985-06-15",
        })
        candidaturas.append({
            "nombre": f"Suplente {i}",
            "genero": genero_sup,
            "partido": "PAN",
            "cargo": "DIPUTADO_LOCAL",
            "tipo": "SUPLENTE",
            "posicion": i,
            "distrito": "D01",
            "indigena": False,
            "discapacidad": False,
            "lgbtq": False,
            "fecha_nacimiento": "1988-03-20",
        })
    return candidaturas


# ---------------------------------------------------------------------------
# Test 1 — GET /api/health
# ---------------------------------------------------------------------------

def test_health_ok():
    """GET /api/health debe retornar 200 con status=ok."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


# ---------------------------------------------------------------------------
# Test 2 — POST /api/validar con JSON válido (SUCCESS)
# ---------------------------------------------------------------------------

def test_validar_json_lista_perfecta_success():
    """
    POST /api/validar con lista perfecta (paridad 100% y todas las acciones afirmativas)
    debe retornar 200 con resultado_global=SUCCESS y sin incumplimientos.
    """
    resp = client.post("/api/validar", json=_payload_lista_perfecta())
    assert resp.status_code == 200
    body = resp.json()
    assert body["partido"] == "PAN"
    assert body["total_candidaturas"] == 10
    assert body["resultado_global"] == "SUCCESS"
    assert body["criterios"]["paridad_horizontal"]["cumple"] is True
    assert body["criterios"]["paridad_vertical"]["cumple"] is True
    assert body["criterios"]["paridad_transversal"]["cumple"] is True
    assert body["incumplimientos"] == []


# ---------------------------------------------------------------------------
# Test 3 — POST /api/validar con lista vacía → 422
# ---------------------------------------------------------------------------

def test_validar_json_lista_vacia_422():
    """Una lista vacía debe ser rechazada con 422 antes de llegar al motor."""
    resp = client.post("/api/validar", json=[])
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test 4 — POST /api/validar con múltiples partidos → 422
# ---------------------------------------------------------------------------

def test_validar_json_multiples_partidos_422():
    """
    Una lista con candidaturas de más de un partido debe ser rechazada con 422
    (se espera un CSV/lista por partido).
    """
    payload = _payload_lista_perfecta()
    payload[5]["partido"] = "MORENA"
    resp = client.post("/api/validar", json=payload)
    assert resp.status_code == 422
    detalle = str(resp.json()).lower()
    assert "partido" in detalle or "morena" in detalle or "pan" in detalle
