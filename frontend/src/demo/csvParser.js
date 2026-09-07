// Port a JavaScript de `backend/services/csv_parser.py`.
// Se usa SOLO en modo demo (GitHub Pages). Replica las mismas validaciones
// y mensajes de error que el parser de Python.
//
// Lanza un objeto { mensaje, detalles[] } que App.jsx sabe renderizar.

const COLUMNAS_REQUERIDAS = [
  'nombre', 'genero', 'partido', 'cargo', 'tipo', 'posicion',
  'distrito', 'indigena', 'discapacidad', 'fecha_nacimiento', 'lgbtq',
]
const GENEROS_VALIDOS = new Set(['M', 'F', 'NB'])
const TIPOS_VALIDOS = new Set(['PROPIETARIO', 'SUPLENTE'])
const BOOL_TRUE = new Set(['true', '1', 'si', 'sí', 'yes'])
const BOOL_FALSE = new Set(['false', '0', 'no'])

class ErrorCsv extends Error {
  constructor(mensaje, detalles = []) {
    super(mensaje)
    this.mensaje = mensaje
    this.detalles = detalles
  }
}

/** Divide una línea CSV respetando comillas dobles (RFC 4180 básico). */
function dividirLinea(linea) {
  const campos = []
  let actual = ''
  let enComillas = false
  for (let i = 0; i < linea.length; i += 1) {
    const ch = linea[i]
    if (enComillas) {
      if (ch === '"') {
        if (linea[i + 1] === '"') { actual += '"'; i += 1 } else { enComillas = false }
      } else {
        actual += ch
      }
    } else if (ch === '"') {
      enComillas = true
    } else if (ch === ',') {
      campos.push(actual)
      actual = ''
    } else {
      actual += ch
    }
  }
  campos.push(actual)
  return campos
}

function parseBool(value, columna, fila) {
  const norm = value.trim().toLowerCase()
  if (BOOL_TRUE.has(norm)) return true
  if (BOOL_FALSE.has(norm)) return false
  throw new Error(
    `Fila ${fila}: valor '${value}' en columna '${columna}' no es booleano válido ` +
    '(acepta: true/false, 1/0, si/no).',
  )
}

function esFechaValida(texto) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(texto.trim())
  if (!m) return false
  const [, y, mm, dd] = m.map(Number)
  const d = new Date(y, mm - 1, dd)
  return d.getFullYear() === y && d.getMonth() === mm - 1 && d.getDate() === dd
}

export function parsearCsv(texto) {
  const limpio = texto.replace(/^﻿/, '')
  const lineas = limpio
    .split(/\r\n|\r|\n/)
    .filter((l) => l.trim() !== '')

  if (lineas.length === 0) {
    throw new ErrorCsv('No se pudo leer el CSV: el archivo está vacío.')
  }

  const encabezados = dividirLinea(lineas[0]).map((h) => h.trim())

  const faltantes = COLUMNAS_REQUERIDAS.filter((c) => !encabezados.includes(c))
  if (faltantes.length) {
    throw new ErrorCsv(`Columnas faltantes en el CSV: ${faltantes.join(', ')}`)
  }

  const filasDatos = lineas.slice(1)
  if (filasDatos.length === 0) {
    throw new ErrorCsv('El CSV no contiene registros.')
  }

  // Construir objetos crudos + normalizar campos clave
  const registros = filasDatos.map((linea) => {
    const valores = dividirLinea(linea)
    const row = {}
    encabezados.forEach((col, i) => { row[col] = (valores[i] ?? '').trim() })
    row.genero = row.genero.toUpperCase()
    row.tipo = row.tipo.toUpperCase()
    return row
  })

  // Partido único
  const partidos = [...new Set(registros.map((r) => r.partido))]
  if (partidos.length > 1) {
    throw new ErrorCsv(
      `El CSV contiene múltiples partidos: ${partidos.join(', ')}. Suba un CSV por partido.`,
    )
  }

  const errores = []
  const candidaturas = []

  registros.forEach((row, idx) => {
    const fila = idx + 2 // 1-indexed contando encabezado
    const erroresFila = []

    if (!GENEROS_VALIDOS.has(row.genero)) {
      erroresFila.push(`Fila ${fila}: genero '${row.genero}' inválido. Valores permitidos: M, F, NB.`)
    }
    if (!TIPOS_VALIDOS.has(row.tipo)) {
      erroresFila.push(
        `Fila ${fila}: tipo '${row.tipo}' inválido. Valores permitidos: PROPIETARIO, SUPLENTE.`,
      )
    }

    let posicion = null
    if (/^-?\d+$/.test(row.posicion.trim())) {
      posicion = parseInt(row.posicion, 10)
    } else {
      erroresFila.push(`Fila ${fila}: posicion '${row.posicion}' no es un número entero.`)
    }

    if (!esFechaValida(row.fecha_nacimiento)) {
      erroresFila.push(
        `Fila ${fila}: fecha_nacimiento '${row.fecha_nacimiento}' inválida. Use el formato YYYY-MM-DD.`,
      )
    }

    const bools = {}
    for (const campo of ['indigena', 'discapacidad', 'lgbtq']) {
      try {
        bools[campo] = parseBool(row[campo], campo, fila)
      } catch (e) {
        erroresFila.push(e.message)
        bools[campo] = null
      }
    }

    if (erroresFila.length) {
      errores.push(...erroresFila)
      return
    }

    candidaturas.push({
      nombre: row.nombre,
      genero: row.genero,
      partido: row.partido,
      cargo: row.cargo,
      tipo: row.tipo,
      posicion,
      distrito: row.distrito,
      indigena: bools.indigena,
      discapacidad: bools.discapacidad,
      fecha_nacimiento: row.fecha_nacimiento.trim(),
      lgbtq: bools.lgbtq,
    })
  })

  if (errores.length) {
    throw new ErrorCsv('El CSV contiene errores de formato.', errores)
  }

  return candidaturas
}
