import math
from collections import defaultdict

from backend.constants.legislacion import (
    ANIO_JUVENTUD_MAX,
    ANIO_JUVENTUD_MIN,
    ART_ACCION_DISCAPACIDAD,
    ART_ACCION_INDIGENA,
    ART_ACCION_JUVENTUD,
    ART_ACCION_LGBTQ,
    ART_PARIDAD_HORIZONTAL,
    ART_PARIDAD_TRANSVERSAL,
    ART_PARIDAD_VERTICAL,
    UMBRAL_DISCAPACIDAD,
    UMBRAL_INDIGENA,
    UMBRAL_JUVENTUD,
    UMBRAL_LGBTQ,
    UMBRAL_TRANSVERSAL_TOLERANCIA,
)
from backend.models.candidatura import Candidatura, Incumplimiento, ResultadoValidacion


# ---------------------------------------------------------------------------
# Regla 1 — Paridad Horizontal (Art. 234 LGIPE)
# ---------------------------------------------------------------------------

def _paridad_horizontal(candidaturas: list[Candidatura]) -> tuple[dict, list[Incumplimiento]]:
    """
    Verifica que en cada fórmula propietario-suplente los géneros sean distintos.
    Solo aplica a pares M/F; si alguno es NB la fórmula queda exenta del check binario.
    Agrupa por (posicion, distrito, cargo).
    """
    formulas: dict[tuple, dict[str, Candidatura]] = defaultdict(dict)
    for c in candidaturas:
        llave = (c.posicion, c.distrito, c.cargo)
        formulas[llave][c.tipo] = c

    total_formulas = 0
    violaciones: list[Incumplimiento] = []

    for llave, miembros in formulas.items():
        propietario = miembros.get("PROPIETARIO")
        suplente    = miembros.get("SUPLENTE")

        if not propietario or not suplente:
            # Fórmula incompleta — no se valida paridad horizontal aquí
            continue

        total_formulas += 1
        pos, distrito, cargo = llave

        # Exentar fórmulas donde algún miembro es NB
        if propietario.genero == "NB" or suplente.genero == "NB":
            continue

        if propietario.genero == suplente.genero:
            violaciones.append(
                Incumplimiento(
                    tipo="PARIDAD_HORIZONTAL",
                    descripcion=(
                        f"La fórmula en posición {pos}, distrito '{distrito}', cargo '{cargo}' "
                        f"tiene propietario/a y suplente del mismo género ({propietario.genero})."
                    ),
                    candidatos_afectados=[propietario.nombre, suplente.nombre],
                    articulo=ART_PARIDAD_HORIZONTAL,
                    sugerencia=(
                        f"Cambiar el género del/la suplente '{suplente.nombre}' en posición {pos}, "
                        f"distrito '{distrito}' para que sea distinto al del/la propietario/a."
                    ),
                )
            )

    formulas_validas = total_formulas - len(violaciones)
    pct = (formulas_validas / total_formulas * 100) if total_formulas > 0 else 100.0

    criterio = {
        "cumple": len(violaciones) == 0,
        "porcentaje_cumplimiento": round(pct, 2),
        "articulo": ART_PARIDAD_HORIZONTAL,
        "descripcion": (
            "Cada fórmula propietario-suplente debe tener géneros distintos (M/F). "
            "Candidaturas con género NB están exentas del check binario."
        ),
        "formulas_revisadas": total_formulas,
        "formulas_con_violacion": len(violaciones),
    }
    return criterio, violaciones


# ---------------------------------------------------------------------------
# Regla 2 — Paridad Vertical (Art. 233 LGIPE)
# ---------------------------------------------------------------------------

def _paridad_vertical(candidaturas: list[Candidatura]) -> tuple[dict, list[Incumplimiento]]:
    """
    Verifica alternancia de géneros en listas ordenadas.
    Agrupa por (partido, cargo, tipo), ordena por posicion, aplica ventana deslizante de 2.
    IMPORTANTE: propietarios y suplentes se evalúan por separado — la alternancia
    de Art. 233 aplica a la lista ordenada de propietarios (y separadamente a la
    de suplentes), no a la mezcla de ambos.
    Candidaturas NB se excluyen del análisis de alternancia binaria.
    """
    listas: dict[tuple, list[Candidatura]] = defaultdict(list)
    for c in candidaturas:
        listas[(c.partido, c.cargo, c.tipo)].append(c)

    total_pares = 0
    violaciones: list[Incumplimiento] = []

    for (partido, cargo, tipo), lista in listas.items():
        # Solo M y F participan en la alternancia
        binarios = sorted(
            [c for c in lista if c.genero in ("M", "F")],
            key=lambda x: x.posicion,
        )

        if len(binarios) < 2:
            continue

        for i in range(len(binarios) - 1):
            total_pares += 1
            a = binarios[i]
            b = binarios[i + 1]
            if a.genero == b.genero:
                violaciones.append(
                    Incumplimiento(
                        tipo="PARIDAD_VERTICAL",
                        descripcion=(
                            f"Posiciones consecutivas {a.posicion} y {b.posicion} del cargo "
                            f"'{cargo}' (partido '{partido}', tipo '{tipo}') tienen el "
                            f"mismo género ({a.genero})."
                        ),
                        candidatos_afectados=[a.nombre, b.nombre],
                        articulo=ART_PARIDAD_VERTICAL,
                        sugerencia=(
                            f"Intercambiar la posición {b.posicion} ('{b.nombre}', {b.genero}) "
                            f"con alguna candidatura {tipo} de género distinto para lograr alternancia."
                        ),
                    )
                )

    pares_validos = total_pares - len(violaciones)
    pct = (pares_validos / total_pares * 100) if total_pares > 0 else 100.0

    criterio = {
        "cumple": len(violaciones) == 0,
        "porcentaje_cumplimiento": round(pct, 2),
        "articulo": ART_PARIDAD_VERTICAL,
        "descripcion": (
            "Las listas de candidaturas ordenadas deben alternar géneros M/F. "
            "Se evalúa con ventana deslizante de 2 posiciones consecutivas."
        ),
        "pares_revisados": total_pares,
        "pares_con_violacion": len(violaciones),
    }
    return criterio, violaciones


# ---------------------------------------------------------------------------
# Regla 3 — Paridad Transversal (Art. 232 LGIPE)
# ---------------------------------------------------------------------------

def _paridad_transversal(candidaturas: list[Candidatura]) -> tuple[dict, list[Incumplimiento]]:
    """
    Verifica que el total de candidaturas sea 50% M y 50% F (±5%).
    Candidaturas NB se excluyen del cálculo binario.
    """
    hombres = sum(1 for c in candidaturas if c.genero == "M")
    mujeres  = sum(1 for c in candidaturas if c.genero == "F")
    total_binarios = hombres + mujeres

    if total_binarios == 0:
        criterio = {
            "cumple": False,
            "porcentaje_cumplimiento": 0.0,
            "articulo": ART_PARIDAD_TRANSVERSAL,
            "descripcion": "No hay candidaturas con género M o F para evaluar paridad transversal.",
            "mujeres": 0,
            "hombres": 0,
        }
        return criterio, []

    pct_f = mujeres / total_binarios
    cumple = abs(pct_f - 0.5) <= UMBRAL_TRANSVERSAL_TOLERANCIA

    # Porcentaje de cumplimiento: 100% = exactamente 50/50; decrece si se aleja
    pct_cumplimiento = max(0.0, 100.0 - abs(pct_f - 0.5) * 200)

    incumplimientos: list[Incumplimiento] = []
    if not cumple:
        genero_minoritario = "F" if mujeres < hombres else "M"
        delta = math.ceil(abs(hombres - mujeres) / 2)
        incumplimientos.append(
            Incumplimiento(
                tipo="PARIDAD_TRANSVERSAL",
                descripcion=(
                    f"Distribución actual: {mujeres} mujeres ({pct_f*100:.1f}%) y "
                    f"{hombres} hombres ({(1-pct_f)*100:.1f}%). "
                    f"Se requiere 50% ±{UMBRAL_TRANSVERSAL_TOLERANCIA*100:.0f}%."
                ),
                candidatos_afectados=[],
                articulo=ART_PARIDAD_TRANSVERSAL,
                sugerencia=(
                    f"Agregar o sustituir al menos {delta} candidatura(s) de género "
                    f"'{genero_minoritario}' para alcanzar la paridad del 50% (tolerancia ±5%)."
                ),
            )
        )

    criterio = {
        "cumple": cumple,
        "porcentaje_cumplimiento": round(pct_cumplimiento, 2),
        "articulo": ART_PARIDAD_TRANSVERSAL,
        "descripcion": (
            "El total de candidaturas debe ser 50% mujeres y 50% hombres, con tolerancia del ±5%."
        ),
        "mujeres": mujeres,
        "hombres": hombres,
        "porcentaje_mujeres": round(pct_f * 100, 2),
    }
    return criterio, incumplimientos


# ---------------------------------------------------------------------------
# Reglas 4–7 — Acciones Afirmativas (Art. 14 LGIPE)
# ---------------------------------------------------------------------------

def _accion_afirmativa(
    candidaturas: list[Candidatura],
    campo: str,
    umbral: float,
    articulo: str,
    nombre_accion: str,
    tipo_incumplimiento: str,
    descripcion_criterio: str,
) -> tuple[dict, list[Incumplimiento]]:
    """Plantilla genérica para las 4 acciones afirmativas."""
    total = len(candidaturas)
    registrado = sum(1 for c in candidaturas if getattr(c, campo))
    requerido = math.ceil(total * umbral)

    cumple = registrado >= requerido
    pct = min(100.0, (registrado / requerido * 100) if requerido > 0 else 100.0)

    incumplimientos: list[Incumplimiento] = []
    if not cumple:
        faltantes = requerido - registrado
        incumplimientos.append(
            Incumplimiento(
                tipo=tipo_incumplimiento,
                descripcion=(
                    f"Se registraron {registrado} candidatura(s) de {nombre_accion}, "
                    f"pero se requieren al menos {requerido} "
                    f"({umbral*100:.0f}% de {total} candidaturas)."
                ),
                candidatos_afectados=[],
                articulo=articulo,
                sugerencia=(
                    f"Registrar al menos {faltantes} candidatura(s) adicional(es) "
                    f"de {nombre_accion}."
                ),
            )
        )

    criterio = {
        "cumple": cumple,
        "porcentaje_cumplimiento": round(pct, 2),
        "articulo": articulo,
        "descripcion": descripcion_criterio,
        "registrado": registrado,
        "requerido": requerido,
    }
    return criterio, incumplimientos


def _accion_juventud(candidaturas: list[Candidatura]) -> tuple[dict, list[Incumplimiento]]:
    """Acción afirmativa de juventud: nacidos entre ANIO_JUVENTUD_MIN y ANIO_JUVENTUD_MAX."""
    total = len(candidaturas)
    registrado = sum(
        1 for c in candidaturas
        if ANIO_JUVENTUD_MIN <= c.fecha_nacimiento.year <= ANIO_JUVENTUD_MAX
    )
    requerido = math.ceil(total * UMBRAL_JUVENTUD)
    cumple = registrado >= requerido
    pct = min(100.0, (registrado / requerido * 100) if requerido > 0 else 100.0)

    incumplimientos: list[Incumplimiento] = []
    if not cumple:
        faltantes = requerido - registrado
        incumplimientos.append(
            Incumplimiento(
                tipo="ACCION_JUVENTUD",
                descripcion=(
                    f"Se registraron {registrado} candidatura(s) de personas jóvenes "
                    f"(nacidas {ANIO_JUVENTUD_MIN}-{ANIO_JUVENTUD_MAX}), "
                    f"pero se requieren al menos {requerido} "
                    f"({UMBRAL_JUVENTUD*100:.0f}% de {total} candidaturas)."
                ),
                candidatos_afectados=[],
                articulo=ART_ACCION_JUVENTUD,
                sugerencia=(
                    f"Registrar al menos {faltantes} candidatura(s) adicional(es) "
                    f"de personas nacidas entre {ANIO_JUVENTUD_MIN} y {ANIO_JUVENTUD_MAX}."
                ),
            )
        )

    criterio = {
        "cumple": cumple,
        "porcentaje_cumplimiento": round(pct, 2),
        "articulo": ART_ACCION_JUVENTUD,
        "descripcion": (
            f"Al menos {UMBRAL_JUVENTUD*100:.0f}% de las candidaturas deben ser de personas "
            f"jóvenes (nacidas entre {ANIO_JUVENTUD_MIN} y {ANIO_JUVENTUD_MAX})."
        ),
        "registrado": registrado,
        "requerido": requerido,
    }
    return criterio, incumplimientos


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def validar(candidaturas: list[Candidatura]) -> ResultadoValidacion:
    """
    Aplica las 7 reglas de paridad y acciones afirmativas.
    Devuelve ResultadoValidacion con criterios, incumplimientos y semáforo global.
    """
    partido = candidaturas[0].partido if candidaturas else "DESCONOCIDO"
    total   = len(candidaturas)

    # Aplicar las 7 reglas
    c_horizontal,    v_horizontal    = _paridad_horizontal(candidaturas)
    c_vertical,      v_vertical      = _paridad_vertical(candidaturas)
    c_transversal,   v_transversal   = _paridad_transversal(candidaturas)

    c_indigena, v_indigena = _accion_afirmativa(
        candidaturas, "indigena", UMBRAL_INDIGENA, ART_ACCION_INDIGENA,
        "personas indígenas", "ACCION_INDIGENA",
        f"Al menos {UMBRAL_INDIGENA*100:.0f}% de las candidaturas deben ser de personas indígenas.",
    )
    c_discapacidad, v_discapacidad = _accion_afirmativa(
        candidaturas, "discapacidad", UMBRAL_DISCAPACIDAD, ART_ACCION_DISCAPACIDAD,
        "personas con discapacidad", "ACCION_DISCAPACIDAD",
        f"Al menos {UMBRAL_DISCAPACIDAD*100:.0f}% de las candidaturas deben ser de personas con discapacidad.",
    )
    c_juventud, v_juventud = _accion_juventud(candidaturas)
    c_lgbtq, v_lgbtq = _accion_afirmativa(
        candidaturas, "lgbtq", UMBRAL_LGBTQ, ART_ACCION_LGBTQ,
        "personas LGBTQ+", "ACCION_LGBTQ",
        f"Al menos {UMBRAL_LGBTQ*100:.0f}% de las candidaturas deben ser de personas LGBTQ+.",
    )

    # Semáforo global
    falla_paridad = (
        not c_horizontal["cumple"]
        or not c_vertical["cumple"]
        or not c_transversal["cumple"]
    )
    falla_afirmativa = (
        not c_indigena["cumple"]
        or not c_discapacidad["cumple"]
        or not c_juventud["cumple"]
        or not c_lgbtq["cumple"]
    )

    if falla_paridad:
        resultado_global = "DANGER"
    elif falla_afirmativa:
        resultado_global = "WARNING"
    else:
        resultado_global = "SUCCESS"

    todos_incumplimientos = (
        v_horizontal + v_vertical + v_transversal
        + v_indigena + v_discapacidad + v_juventud + v_lgbtq
    )

    return ResultadoValidacion(
        partido=partido,
        total_candidaturas=total,
        resultado_global=resultado_global,
        criterios={
            "paridad_horizontal":  c_horizontal,
            "paridad_vertical":    c_vertical,
            "paridad_transversal": c_transversal,
            "accion_indigena":     c_indigena,
            "accion_discapacidad": c_discapacidad,
            "accion_juventud":     c_juventud,
            "accion_lgbtq":        c_lgbtq,
        },
        incumplimientos=todos_incumplimientos,
    )
