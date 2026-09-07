import logging

from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from backend.models.candidatura import Candidatura, ResultadoValidacion
from backend.services.csv_parser import parsear_csv
from backend.services.motor_paridad import validar
from backend.services.pdf_report import generar_pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ParidadCheck API",
    description="Verificación automática de paridad de género y acciones afirmativas en candidaturas electorales.",
    version="1.0.0",
)

# CORS — permite peticiones desde el frontend React en desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],  # el frontend lee el nombre del PDF
)


# ---------------------------------------------------------------------------
# Manejador personalizado de errores de validación (mensajes en español)
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Error de validación en la solicitud.",
            "errores": exc.errors(),
        },
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health", tags=["Sistema"])
async def health():
    """Verifica que la API esté en funcionamiento."""
    return {"status": "ok", "version": "1.0.0"}


@app.post(
    "/api/validar",
    response_model=ResultadoValidacion,
    tags=["Paridad"],
    summary="Valida paridad y acciones afirmativas de una lista de candidaturas (JSON)",
)
async def validar_json(
    candidaturas: list[Candidatura] = Body(
        ...,
        description="Array JSON de candidaturas. Todas deben pertenecer al mismo partido.",
    ),
) -> ResultadoValidacion:
    """
    Recibe un array JSON de candidaturas y devuelve el análisis completo de paridad.

    Cada elemento debe contener los campos del modelo `Candidatura`:
    nombre, genero (M|F|NB), partido, cargo, tipo (PROPIETARIO|SUPLENTE),
    posicion (int), distrito, indigena (bool), discapacidad (bool),
    fecha_nacimiento (YYYY-MM-DD), lgbtq (bool).
    """
    if not candidaturas:
        raise HTTPException(
            status_code=422,
            detail="La lista de candidaturas está vacía.",
        )

    # Validar partido único (coincide con el comportamiento del CSV parser)
    partidos = {c.partido for c in candidaturas}
    if len(partidos) > 1:
        raise HTTPException(
            status_code=422,
            detail=(
                f"La lista contiene múltiples partidos: {', '.join(sorted(partidos))}. "
                "Envíe una lista por partido."
            ),
        )

    logger.info(
        "Procesando %d candidaturas vía JSON (partido=%s)",
        len(candidaturas),
        next(iter(partidos)),
    )

    resultado = validar(candidaturas)

    logger.info(
        "Resultado para '%s': %s (%d candidaturas, %d incumplimientos)",
        resultado.partido,
        resultado.resultado_global,
        resultado.total_candidaturas,
        len(resultado.incumplimientos),
    )

    return resultado


@app.post(
    "/api/validar-csv",
    response_model=ResultadoValidacion,
    tags=["Paridad"],
    summary="Valida paridad y acciones afirmativas desde un archivo CSV (alternativo)",
)
async def validar_csv(archivo: UploadFile = File(...)):
    """
    Endpoint alternativo: recibe un archivo CSV con la lista de candidaturas.

    El CSV debe contener las columnas:
    nombre, genero, partido, cargo, tipo, posicion, distrito,
    indigena, discapacidad, fecha_nacimiento, lgbtq
    """
    if not archivo.filename or not archivo.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=422,
            detail="El archivo debe tener extensión .csv",
        )

    contenido = await archivo.read()

    if len(contenido) == 0:
        raise HTTPException(status_code=422, detail="El archivo CSV está vacío.")

    logger.info("Procesando archivo: %s (%d bytes)", archivo.filename, len(contenido))

    candidaturas = parsear_csv(contenido)
    resultado    = validar(candidaturas)

    logger.info(
        "Resultado para '%s': %s (%d candidaturas, %d incumplimientos)",
        resultado.partido,
        resultado.resultado_global,
        resultado.total_candidaturas,
        len(resultado.incumplimientos),
    )

    return resultado


def _validar_partido_unico(candidaturas: list[Candidatura]) -> None:
    partidos = {c.partido for c in candidaturas}
    if len(partidos) > 1:
        raise HTTPException(
            status_code=422,
            detail=(
                f"La lista contiene múltiples partidos: {', '.join(sorted(partidos))}. "
                "Envíe una lista por partido."
            ),
        )


def _respuesta_pdf(candidaturas: list[Candidatura]) -> Response:
    resultado = validar(candidaturas)
    pdf_bytes = generar_pdf(candidaturas, resultado)
    nombre = f"reporte-paridad-{resultado.partido}.pdf".replace(" ", "_")

    logger.info(
        "Reporte PDF generado para '%s': %s (%d bytes)",
        resultado.partido,
        resultado.resultado_global,
        len(pdf_bytes),
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@app.post(
    "/api/reporte-pdf",
    tags=["Reporte"],
    summary="Genera el reporte institucional en PDF a partir de un array JSON de candidaturas",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def reporte_pdf_json(
    candidaturas: list[Candidatura] = Body(
        ...,
        description="Array JSON de candidaturas (mismo formato que /api/validar).",
    ),
):
    """Recibe las candidaturas, ejecuta el motor de reglas y devuelve el PDF descargable."""
    if not candidaturas:
        raise HTTPException(status_code=422, detail="La lista de candidaturas está vacía.")
    _validar_partido_unico(candidaturas)
    return _respuesta_pdf(candidaturas)


@app.post(
    "/api/reporte-pdf-csv",
    tags=["Reporte"],
    summary="Genera el reporte institucional en PDF a partir de un archivo CSV",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def reporte_pdf_csv(archivo: UploadFile = File(...)):
    """Variante que recibe el mismo CSV que /api/validar-csv y devuelve el PDF descargable."""
    if not archivo.filename or not archivo.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="El archivo debe tener extensión .csv")

    contenido = await archivo.read()
    if len(contenido) == 0:
        raise HTTPException(status_code=422, detail="El archivo CSV está vacío.")

    candidaturas = parsear_csv(contenido)
    return _respuesta_pdf(candidaturas)


# ---------------------------------------------------------------------------
# Inicio de la aplicación
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    logger.info("ParidadCheck API iniciada correctamente.")
