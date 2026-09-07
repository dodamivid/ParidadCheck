"""
Tests del endpoint de reporte PDF (/api/reporte-pdf y /api/reporte-pdf-csv).
"""
import io

from fastapi.testclient import TestClient

from backend.main import app
from backend.tests.test_api import _payload_lista_perfecta

client = TestClient(app)

_PDF_MAGIC = b"%PDF-"


def _csv_bytes() -> bytes:
    encabezado = (
        "nombre,genero,partido,cargo,tipo,posicion,distrito,"
        "indigena,discapacidad,fecha_nacimiento,lgbtq\n"
    )
    filas = []
    for c in _payload_lista_perfecta():
        filas.append(
            f"{c['nombre']},{c['genero']},{c['partido']},{c['cargo']},{c['tipo']},"
            f"{c['posicion']},{c['distrito']},{c['indigena']},{c['discapacidad']},"
            f"{c['fecha_nacimiento']},{c['lgbtq']}"
        )
    return (encabezado + "\n".join(filas) + "\n").encode("utf-8")


def test_reporte_pdf_json_devuelve_pdf_valido():
    """POST /api/reporte-pdf con JSON válido devuelve un PDF descargable no vacío."""
    resp = client.post("/api/reporte-pdf", json=_payload_lista_perfecta())

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "attachment" in resp.headers.get("content-disposition", "")
    assert len(resp.content) > 0
    assert resp.content.startswith(_PDF_MAGIC)


def test_reporte_pdf_csv_devuelve_pdf_valido():
    """POST /api/reporte-pdf-csv con un CSV válido devuelve un PDF descargable no vacío."""
    archivo = ("candidaturas.csv", io.BytesIO(_csv_bytes()), "text/csv")
    resp = client.post("/api/reporte-pdf-csv", files={"archivo": archivo})

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert len(resp.content) > 1000  # un PDF con portada + tablas pesa varios KB
    assert resp.content.startswith(_PDF_MAGIC)


def test_reporte_pdf_json_lista_vacia_422():
    """Una lista vacía se rechaza con 422 antes de generar el PDF."""
    resp = client.post("/api/reporte-pdf", json=[])
    assert resp.status_code == 422
