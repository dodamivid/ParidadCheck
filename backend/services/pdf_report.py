"""
Generación del reporte institucional en PDF.

Usa reportlab (platypus) en lugar de WeasyPrint: reportlab se instala con una
sola rueda pura de Python y no depende de librerías nativas de GTK/Pango/Cairo,
que en Windows suelen romper la instalación.
"""
from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.models.candidatura import Candidatura, ResultadoValidacion

# --- Paleta (coincide con la del README / Tailwind) ---
PRIMARY = colors.HexColor("#1B2B5E")
ACCENT = colors.HexColor("#C2185B")
SUCCESS = colors.HexColor("#16A34A")
WARNING = colors.HexColor("#CA8A04")
DANGER = colors.HexColor("#DC2626")
NEUTRAL_50 = colors.HexColor("#F8FAFC")
NEUTRAL_200 = colors.HexColor("#E2E8F0")
NEUTRAL_600 = colors.HexColor("#475569")
NEUTRAL_800 = colors.HexColor("#1E293B")

_SEMAFORO = {
    "SUCCESS": (SUCCESS, "CUMPLE", "La lista satisface todos los criterios de paridad y acciones afirmativas."),
    "WARNING": (WARNING, "CUMPLIMIENTO PARCIAL", "La paridad se cumple, pero hay observaciones en acciones afirmativas."),
    "DANGER": (DANGER, "NO CUMPLE", "Se detectaron incumplimientos de paridad que pueden derivar en impugnación."),
}

_CRITERIOS_ETIQUETAS = {
    "paridad_horizontal": "Paridad horizontal",
    "paridad_vertical": "Paridad vertical",
    "paridad_transversal": "Paridad transversal",
    "accion_indigena": "Acción afirmativa — Indígena",
    "accion_discapacidad": "Acción afirmativa — Discapacidad",
    "accion_juventud": "Acción afirmativa — Juventud",
    "accion_lgbtq": "Acción afirmativa — Diversidad sexual",
}


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "portada_titulo": ParagraphStyle(
            "portada_titulo", parent=base["Title"], fontSize=30, textColor=PRIMARY,
            alignment=TA_CENTER, spaceAfter=6, leading=34,
        ),
        "portada_sub": ParagraphStyle(
            "portada_sub", parent=base["Normal"], fontSize=13, textColor=NEUTRAL_600,
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontSize=15, textColor=PRIMARY,
            spaceBefore=18, spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontSize=9.5, textColor=NEUTRAL_800,
            leading=13, alignment=TA_LEFT,
        ),
        "cell": ParagraphStyle(
            "cell", parent=base["Normal"], fontSize=8, textColor=NEUTRAL_800, leading=10,
        ),
        "cell_head": ParagraphStyle(
            "cell_head", parent=base["Normal"], fontSize=8, textColor=colors.white,
            leading=10, fontName="Helvetica-Bold",
        ),
        "small": ParagraphStyle(
            "small", parent=base["Normal"], fontSize=8, textColor=NEUTRAL_600, leading=10,
        ),
    }


def _portada(resultado: ResultadoValidacion, st: dict, folio: str) -> list:
    fecha = datetime.now().strftime("%d de %B de %Y, %H:%M")
    color, texto, _ = _SEMAFORO[resultado.resultado_global]
    return [
        Spacer(1, 4 * cm),
        Paragraph("ParidadCheck", st["portada_sub"]),
        Paragraph("Reporte de verificación de paridad", st["portada_titulo"]),
        Paragraph("de género y acciones afirmativas", st["portada_titulo"]),
        Spacer(1, 1.5 * cm),
        Table(
            [[Paragraph(f"<b>Partido:</b> {resultado.partido}", st["portada_sub"])],
             [Paragraph(f"<b>Total de candidaturas:</b> {resultado.total_candidaturas}", st["portada_sub"])],
             [Paragraph(f"<b>Fecha de emisión:</b> {fecha}", st["portada_sub"])],
             [Paragraph(f"<b>Folio de validación:</b> {folio}", st["portada_sub"])]],
            colWidths=[14 * cm],
            style=TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"),
                              ("TOPPADDING", (0, 0), (-1, -1), 4),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]),
        ),
        Spacer(1, 1.5 * cm),
        Table(
            [[Paragraph(f"<b>RESULTADO GLOBAL: {texto}</b>",
                        ParagraphStyle("sem", fontSize=16, textColor=colors.white,
                                       alignment=TA_CENTER, leading=20))]],
            colWidths=[12 * cm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                ("ROUNDEDCORNERS", [8, 8, 8, 8]),
            ]),
            hAlign="CENTER",
        ),
        PageBreak(),
    ]


def _resumen(resultado: ResultadoValidacion, st: dict) -> list:
    color, texto, glosa = _SEMAFORO[resultado.resultado_global]
    elems = [
        Paragraph("1. Resumen ejecutivo", st["h2"]),
        Paragraph(glosa, st["body"]),
        Spacer(1, 0.4 * cm),
    ]

    filas = [[Paragraph("Criterio", st["cell_head"]),
              Paragraph("Estado", st["cell_head"]),
              Paragraph("Cumplimiento", st["cell_head"]),
              Paragraph("Artículo", st["cell_head"])]]
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, NEUTRAL_200),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]
    for i, (clave, etiqueta) in enumerate(_CRITERIOS_ETIQUETAS.items(), start=1):
        crit = resultado.criterios.get(clave, {})
        cumple = bool(crit.get("cumple"))
        pct = crit.get("porcentaje_cumplimiento", 0.0)
        filas.append([
            Paragraph(etiqueta, st["cell"]),
            Paragraph("Cumple" if cumple else "No cumple", st["cell"]),
            Paragraph(f"{pct:.0f}%", st["cell"]),
            Paragraph(str(crit.get("articulo", "—")), st["cell"]),
        ])
        estilo.append(("TEXTCOLOR", (1, i), (1, i), SUCCESS if cumple else DANGER))
        if i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), NEUTRAL_50))

    tabla = Table(filas, colWidths=[7 * cm, 2.4 * cm, 2.6 * cm, 4 * cm])
    tabla.setStyle(TableStyle(estilo))
    elems.append(tabla)
    return elems


def _tabla_candidaturas(candidaturas: list[Candidatura], resultado: ResultadoValidacion, st: dict) -> list:
    afectados = {
        nombre
        for inc in resultado.incumplimientos
        for nombre in inc.candidatos_afectados
    }

    encabezados = ["#", "Nombre", "Gén.", "Cargo", "Tipo", "Pos.", "Distrito", "Acc. afirm."]
    filas = [[Paragraph(h, st["cell_head"]) for h in encabezados]]
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.4, NEUTRAL_200),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]

    orden = sorted(candidaturas, key=lambda c: (c.cargo, c.distrito, c.posicion, c.tipo))
    for i, c in enumerate(orden, start=1):
        acc = []
        if c.indigena:
            acc.append("Indígena")
        if c.discapacidad:
            acc.append("Discapacidad")
        if c.lgbtq:
            acc.append("LGBTQ+")
        if 1997 <= c.fecha_nacimiento.year <= 2008:
            acc.append("Joven")
        filas.append([
            Paragraph(str(i), st["cell"]),
            Paragraph(c.nombre, st["cell"]),
            Paragraph(c.genero, st["cell"]),
            Paragraph(c.cargo, st["cell"]),
            Paragraph(c.tipo.capitalize(), st["cell"]),
            Paragraph(str(c.posicion), st["cell"]),
            Paragraph(c.distrito, st["cell"]),
            Paragraph(", ".join(acc) or "—", st["cell"]),
        ])
        if c.nombre in afectados:
            estilo.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FEE2E2")))
        elif i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), NEUTRAL_50))

    tabla = Table(
        filas,
        colWidths=[0.9 * cm, 4.6 * cm, 1.1 * cm, 2.7 * cm, 2 * cm, 1 * cm, 2.6 * cm, 2.6 * cm],
        repeatRows=1,
    )
    tabla.setStyle(TableStyle(estilo))
    return [
        Paragraph("2. Tabla de candidaturas", st["h2"]),
        Paragraph(
            "Las filas resaltadas en rojo corresponden a candidaturas señaladas en algún incumplimiento.",
            st["small"],
        ),
        Spacer(1, 0.3 * cm),
        tabla,
    ]


def _detalle_incumplimientos(resultado: ResultadoValidacion, st: dict) -> list:
    elems = [Paragraph("3. Detalle de incumplimientos", st["h2"])]

    if not resultado.incumplimientos:
        elems.append(Paragraph(
            "No se detectaron incumplimientos. La lista de candidaturas cumple con la "
            "normativa de paridad y acciones afirmativas aplicada.",
            st["body"],
        ))
        return elems

    for idx, inc in enumerate(resultado.incumplimientos, start=1):
        afectados = ", ".join(inc.candidatos_afectados) if inc.candidatos_afectados else "—"
        bloque = Table(
            [
                [Paragraph(f"<b>{idx}. {inc.tipo.replace('_', ' ').title()}</b>", st["body"]),
                 Paragraph(f"<b>{inc.articulo}</b>", st["body"])],
                [Paragraph(f"<b>Descripción:</b> {inc.descripcion}", st["cell"]), ""],
                [Paragraph(f"<b>Candidaturas afectadas:</b> {afectados}", st["cell"]), ""],
                [Paragraph(f"<b>Sugerencia de corrección:</b> {inc.sugerencia}", st["cell"]), ""],
            ],
            colWidths=[12 * cm, 4 * cm],
            style=TableStyle([
                ("SPAN", (0, 1), (1, 1)),
                ("SPAN", (0, 2), (1, 2)),
                ("SPAN", (0, 3), (1, 3)),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FEE2E2")),
                ("LINEBELOW", (0, 0), (-1, 0), 1, DANGER),
                ("BOX", (0, 0), (-1, -1), 0.5, NEUTRAL_200),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]),
        )
        elems.append(KeepTogether([bloque, Spacer(1, 0.35 * cm)]))
    return elems


def _pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(NEUTRAL_600)
    canvas.drawString(
        2 * cm, 1.2 * cm,
        f"ParidadCheck — Documento generado automáticamente el {datetime.now():%Y-%m-%d %H:%M}",
    )
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    canvas.restoreState()


def generar_pdf(candidaturas: list[Candidatura], resultado: ResultadoValidacion) -> bytes:
    """Construye el reporte PDF y devuelve sus bytes."""
    folio = f"PC-{datetime.now():%Y%m%d%H%M%S}-{resultado.partido[:4].upper()}"
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
        title=f"Reporte ParidadCheck — {resultado.partido}",
        author="ParidadCheck",
    )
    st = _styles()
    story: list = []
    story += _portada(resultado, st, folio)
    story += _resumen(resultado, st)
    story.append(Spacer(1, 0.6 * cm))
    story += _tabla_candidaturas(candidaturas, resultado, st)
    story.append(PageBreak())
    story += _detalle_incumplimientos(resultado, st)

    doc.build(story, onFirstPage=_pie, onLaterPages=_pie)
    return buffer.getvalue()
