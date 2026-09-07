// Port a JavaScript del motor de reglas de `backend/services/motor_paridad.py`.
// Se usa SOLO en modo demo (GitHub Pages), cuando no hay backend FastAPI.
// La lógica y los artículos legales replican 1:1 la implementación de Python;
// si cambias una regla en el backend, refléjala aquí.

// --- Artículos legales (backend/constants/legislacion.py) ---
const ART_PARIDAD_HORIZONTAL = 'Art. 234 LGIPE'
const ART_PARIDAD_VERTICAL = 'Art. 233 LGIPE'
const ART_PARIDAD_TRANSVERSAL = 'Art. 232 LGIPE'
const ART_ACCION = 'Art. 14 LGIPE'

// --- Umbrales numéricos ---
const UMBRAL_TRANSVERSAL_TOLERANCIA = 0.05
const UMBRAL_INDIGENA = 0.03
const UMBRAL_DISCAPACIDAD = 0.01
const UMBRAL_JUVENTUD = 0.01
const UMBRAL_LGBTQ = 0.01
const ANIO_JUVENTUD_MIN = 1997
const ANIO_JUVENTUD_MAX = 2008

const round2 = (x) => Math.round((x + Number.EPSILON) * 100) / 100
const anioNacimiento = (c) => parseInt(String(c.fecha_nacimiento).slice(0, 4), 10)

// ---------------------------------------------------------------------------
// Regla 1 — Paridad Horizontal (Art. 234 LGIPE)
// ---------------------------------------------------------------------------
function paridadHorizontal(candidaturas) {
  const formulas = new Map() // (posicion|distrito|cargo) -> { PROPIETARIO, SUPLENTE }
  for (const c of candidaturas) {
    const llave = `${c.posicion}|${c.distrito}|${c.cargo}`
    if (!formulas.has(llave)) formulas.set(llave, {})
    formulas.get(llave)[c.tipo] = c
  }

  let totalFormulas = 0
  const violaciones = []

  for (const [llave, miembros] of formulas) {
    const propietario = miembros.PROPIETARIO
    const suplente = miembros.SUPLENTE
    if (!propietario || !suplente) continue // fórmula incompleta

    totalFormulas += 1
    const [pos, distrito, cargo] = llave.split('|')

    if (propietario.genero === 'NB' || suplente.genero === 'NB') continue

    if (propietario.genero === suplente.genero) {
      violaciones.push({
        tipo: 'PARIDAD_HORIZONTAL',
        descripcion:
          `La fórmula en posición ${pos}, distrito '${distrito}', cargo '${cargo}' ` +
          `tiene propietario/a y suplente del mismo género (${propietario.genero}).`,
        candidatos_afectados: [propietario.nombre, suplente.nombre],
        articulo: ART_PARIDAD_HORIZONTAL,
        sugerencia:
          `Cambiar el género del/la suplente '${suplente.nombre}' en posición ${pos}, ` +
          `distrito '${distrito}' para que sea distinto al del/la propietario/a.`,
      })
    }
  }

  const formulasValidas = totalFormulas - violaciones.length
  const pct = totalFormulas > 0 ? (formulasValidas / totalFormulas) * 100 : 100.0

  const criterio = {
    cumple: violaciones.length === 0,
    porcentaje_cumplimiento: round2(pct),
    articulo: ART_PARIDAD_HORIZONTAL,
    descripcion:
      'Cada fórmula propietario-suplente debe tener géneros distintos (M/F). ' +
      'Candidaturas con género NB están exentas del check binario.',
    formulas_revisadas: totalFormulas,
    formulas_con_violacion: violaciones.length,
  }
  return [criterio, violaciones]
}

// ---------------------------------------------------------------------------
// Regla 2 — Paridad Vertical (Art. 233 LGIPE)
// ---------------------------------------------------------------------------
function paridadVertical(candidaturas) {
  const listas = new Map() // (partido|cargo|tipo) -> Candidatura[]
  for (const c of candidaturas) {
    const llave = `${c.partido}|${c.cargo}|${c.tipo}`
    if (!listas.has(llave)) listas.set(llave, [])
    listas.get(llave).push(c)
  }

  let totalPares = 0
  const violaciones = []

  for (const [llave, lista] of listas) {
    const binarios = lista
      .filter((c) => c.genero === 'M' || c.genero === 'F')
      .sort((a, b) => a.posicion - b.posicion)

    if (binarios.length < 2) continue

    const [partido, cargo, tipo] = llave.split('|')
    for (let i = 0; i < binarios.length - 1; i += 1) {
      totalPares += 1
      const a = binarios[i]
      const b = binarios[i + 1]
      if (a.genero === b.genero) {
        violaciones.push({
          tipo: 'PARIDAD_VERTICAL',
          descripcion:
            `Posiciones consecutivas ${a.posicion} y ${b.posicion} del cargo ` +
            `'${cargo}' (partido '${partido}', tipo '${tipo}') tienen el ` +
            `mismo género (${a.genero}).`,
          candidatos_afectados: [a.nombre, b.nombre],
          articulo: ART_PARIDAD_VERTICAL,
          sugerencia:
            `Intercambiar la posición ${b.posicion} ('${b.nombre}', ${b.genero}) ` +
            `con alguna candidatura ${tipo} de género distinto para lograr alternancia.`,
        })
      }
    }
  }

  const paresValidos = totalPares - violaciones.length
  const pct = totalPares > 0 ? (paresValidos / totalPares) * 100 : 100.0

  const criterio = {
    cumple: violaciones.length === 0,
    porcentaje_cumplimiento: round2(pct),
    articulo: ART_PARIDAD_VERTICAL,
    descripcion:
      'Las listas de candidaturas ordenadas deben alternar géneros M/F. ' +
      'Se evalúa con ventana deslizante de 2 posiciones consecutivas.',
    pares_revisados: totalPares,
    pares_con_violacion: violaciones.length,
  }
  return [criterio, violaciones]
}

// ---------------------------------------------------------------------------
// Regla 3 — Paridad Transversal (Art. 232 LGIPE)
// ---------------------------------------------------------------------------
function paridadTransversal(candidaturas) {
  const hombres = candidaturas.filter((c) => c.genero === 'M').length
  const mujeres = candidaturas.filter((c) => c.genero === 'F').length
  const totalBinarios = hombres + mujeres

  if (totalBinarios === 0) {
    return [
      {
        cumple: false,
        porcentaje_cumplimiento: 0.0,
        articulo: ART_PARIDAD_TRANSVERSAL,
        descripcion: 'No hay candidaturas con género M o F para evaluar paridad transversal.',
        mujeres: 0,
        hombres: 0,
      },
      [],
    ]
  }

  const pctF = mujeres / totalBinarios
  const cumple = Math.abs(pctF - 0.5) <= UMBRAL_TRANSVERSAL_TOLERANCIA
  const pctCumplimiento = Math.max(0.0, 100.0 - Math.abs(pctF - 0.5) * 200)

  const incumplimientos = []
  if (!cumple) {
    const generoMinoritario = mujeres < hombres ? 'F' : 'M'
    const delta = Math.ceil(Math.abs(hombres - mujeres) / 2)
    incumplimientos.push({
      tipo: 'PARIDAD_TRANSVERSAL',
      descripcion:
        `Distribución actual: ${mujeres} mujeres (${(pctF * 100).toFixed(1)}%) y ` +
        `${hombres} hombres (${((1 - pctF) * 100).toFixed(1)}%). ` +
        `Se requiere 50% ±${(UMBRAL_TRANSVERSAL_TOLERANCIA * 100).toFixed(0)}%.`,
      candidatos_afectados: [],
      articulo: ART_PARIDAD_TRANSVERSAL,
      sugerencia:
        `Agregar o sustituir al menos ${delta} candidatura(s) de género ` +
        `'${generoMinoritario}' para alcanzar la paridad del 50% (tolerancia ±5%).`,
    })
  }

  const criterio = {
    cumple,
    porcentaje_cumplimiento: round2(pctCumplimiento),
    articulo: ART_PARIDAD_TRANSVERSAL,
    descripcion:
      'El total de candidaturas debe ser 50% mujeres y 50% hombres, con tolerancia del ±5%.',
    mujeres,
    hombres,
    porcentaje_mujeres: round2(pctF * 100),
  }
  return [criterio, incumplimientos]
}

// ---------------------------------------------------------------------------
// Reglas 4–7 — Acciones Afirmativas (Art. 14 LGIPE)
// ---------------------------------------------------------------------------
function accionAfirmativa(candidaturas, campo, umbral, nombreAccion, tipoIncumplimiento, descripcionCriterio) {
  const total = candidaturas.length
  const registrado = candidaturas.filter((c) => Boolean(c[campo])).length
  const requerido = Math.ceil(total * umbral)

  const cumple = registrado >= requerido
  const pct = Math.min(100.0, requerido > 0 ? (registrado / requerido) * 100 : 100.0)

  const incumplimientos = []
  if (!cumple) {
    const faltantes = requerido - registrado
    incumplimientos.push({
      tipo: tipoIncumplimiento,
      descripcion:
        `Se registraron ${registrado} candidatura(s) de ${nombreAccion}, ` +
        `pero se requieren al menos ${requerido} ` +
        `(${(umbral * 100).toFixed(0)}% de ${total} candidaturas).`,
      candidatos_afectados: [],
      articulo: ART_ACCION,
      sugerencia: `Registrar al menos ${faltantes} candidatura(s) adicional(es) de ${nombreAccion}.`,
    })
  }

  const criterio = {
    cumple,
    porcentaje_cumplimiento: round2(pct),
    articulo: ART_ACCION,
    descripcion: descripcionCriterio,
    registrado,
    requerido,
  }
  return [criterio, incumplimientos]
}

function accionJuventud(candidaturas) {
  const total = candidaturas.length
  const registrado = candidaturas.filter((c) => {
    const anio = anioNacimiento(c)
    return anio >= ANIO_JUVENTUD_MIN && anio <= ANIO_JUVENTUD_MAX
  }).length
  const requerido = Math.ceil(total * UMBRAL_JUVENTUD)
  const cumple = registrado >= requerido
  const pct = Math.min(100.0, requerido > 0 ? (registrado / requerido) * 100 : 100.0)

  const incumplimientos = []
  if (!cumple) {
    const faltantes = requerido - registrado
    incumplimientos.push({
      tipo: 'ACCION_JUVENTUD',
      descripcion:
        `Se registraron ${registrado} candidatura(s) de personas jóvenes ` +
        `(nacidas ${ANIO_JUVENTUD_MIN}-${ANIO_JUVENTUD_MAX}), ` +
        `pero se requieren al menos ${requerido} ` +
        `(${(UMBRAL_JUVENTUD * 100).toFixed(0)}% de ${total} candidaturas).`,
      candidatos_afectados: [],
      articulo: ART_ACCION,
      sugerencia:
        `Registrar al menos ${faltantes} candidatura(s) adicional(es) ` +
        `de personas nacidas entre ${ANIO_JUVENTUD_MIN} y ${ANIO_JUVENTUD_MAX}.`,
    })
  }

  const criterio = {
    cumple,
    porcentaje_cumplimiento: round2(pct),
    articulo: ART_ACCION,
    descripcion:
      `Al menos ${(UMBRAL_JUVENTUD * 100).toFixed(0)}% de las candidaturas deben ser de personas ` +
      `jóvenes (nacidas entre ${ANIO_JUVENTUD_MIN} y ${ANIO_JUVENTUD_MAX}).`,
    registrado,
    requerido,
  }
  return [criterio, incumplimientos]
}

// ---------------------------------------------------------------------------
// Función principal
// ---------------------------------------------------------------------------
export function validar(candidaturas) {
  const partido = candidaturas.length ? candidaturas[0].partido : 'DESCONOCIDO'
  const total = candidaturas.length

  const [cHorizontal, vHorizontal] = paridadHorizontal(candidaturas)
  const [cVertical, vVertical] = paridadVertical(candidaturas)
  const [cTransversal, vTransversal] = paridadTransversal(candidaturas)

  const [cIndigena, vIndigena] = accionAfirmativa(
    candidaturas, 'indigena', UMBRAL_INDIGENA, 'personas indígenas', 'ACCION_INDIGENA',
    `Al menos ${(UMBRAL_INDIGENA * 100).toFixed(0)}% de las candidaturas deben ser de personas indígenas.`,
  )
  const [cDiscapacidad, vDiscapacidad] = accionAfirmativa(
    candidaturas, 'discapacidad', UMBRAL_DISCAPACIDAD, 'personas con discapacidad', 'ACCION_DISCAPACIDAD',
    `Al menos ${(UMBRAL_DISCAPACIDAD * 100).toFixed(0)}% de las candidaturas deben ser de personas con discapacidad.`,
  )
  const [cJuventud, vJuventud] = accionJuventud(candidaturas)
  const [cLgbtq, vLgbtq] = accionAfirmativa(
    candidaturas, 'lgbtq', UMBRAL_LGBTQ, 'personas LGBTQ+', 'ACCION_LGBTQ',
    `Al menos ${(UMBRAL_LGBTQ * 100).toFixed(0)}% de las candidaturas deben ser de personas LGBTQ+.`,
  )

  const fallaParidad = !cHorizontal.cumple || !cVertical.cumple || !cTransversal.cumple
  const fallaAfirmativa =
    !cIndigena.cumple || !cDiscapacidad.cumple || !cJuventud.cumple || !cLgbtq.cumple

  let resultadoGlobal = 'SUCCESS'
  if (fallaParidad) resultadoGlobal = 'DANGER'
  else if (fallaAfirmativa) resultadoGlobal = 'WARNING'

  const incumplimientos = [
    ...vHorizontal, ...vVertical, ...vTransversal,
    ...vIndigena, ...vDiscapacidad, ...vJuventud, ...vLgbtq,
  ]

  return {
    partido,
    total_candidaturas: total,
    resultado_global: resultadoGlobal,
    criterios: {
      paridad_horizontal: cHorizontal,
      paridad_vertical: cVertical,
      paridad_transversal: cTransversal,
      accion_indigena: cIndigena,
      accion_discapacidad: cDiscapacidad,
      accion_juventud: cJuventud,
      accion_lgbtq: cLgbtq,
    },
    incumplimientos,
  }
}
