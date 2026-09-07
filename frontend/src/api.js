import { parsearCsv } from './demo/csvParser.js'
import { validar } from './demo/motorParidad.js'

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

// Modo demo: el motor de reglas corre 100% en el navegador, sin backend.
// Se activa explícitamente con VITE_API_MODE=demo (build de GitHub Pages) o
// implícitamente cuando no hay ninguna URL de backend configurada.
const API_MODE =
  import.meta.env.VITE_API_MODE || (import.meta.env.VITE_API_URL ? 'api' : 'demo')
export const ES_DEMO = API_MODE === 'demo'

/** Ejecuta el motor de reglas en el navegador (modo demo). */
export function validarTextoLocal(texto) {
  return validar(parsearCsv(texto))
}

/**
 * Convierte el cuerpo de error de FastAPI (que puede ser string, objeto
 * {mensaje, errores[]}, o lista de errores de validación) en un objeto
 * { mensaje, detalles[] } fácil de renderizar.
 */
function parseError(payload, status) {
  if (!payload) {
    return { mensaje: `Error ${status} del servidor.`, detalles: [] }
  }

  const detail = payload.detail ?? payload
  const detallesExtra = Array.isArray(payload.errores)
    ? payload.errores.map((e) => (typeof e === 'string' ? e : e.msg || JSON.stringify(e)))
    : []

  if (typeof detail === 'string') {
    return { mensaje: detail, detalles: detallesExtra }
  }

  if (detail && typeof detail === 'object') {
    const detalles = Array.isArray(detail.errores)
      ? detail.errores.map((e) => (typeof e === 'string' ? e : e.msg || JSON.stringify(e)))
      : detallesExtra
    return {
      mensaje: detail.mensaje || 'El archivo contiene errores de formato.',
      detalles,
    }
  }

  if (Array.isArray(detail)) {
    return {
      mensaje: 'Error de validación en la solicitud.',
      detalles: detail.map((e) => e.msg || JSON.stringify(e)),
    }
  }

  return { mensaje: `Error ${status} del servidor.`, detalles: detallesExtra }
}

async function readErrorBody(res) {
  try {
    return parseError(await res.json(), res.status)
  } catch {
    return { mensaje: `Error ${res.status}: ${res.statusText || 'respuesta no válida del servidor'}.`, detalles: [] }
  }
}

function archivoCsv(nombre, texto) {
  return new File([texto], nombre || 'candidaturas.csv', { type: 'text/csv' })
}

/**
 * Valida un CSV (contenido en texto) y devuelve el ResultadoValidacion.
 * En modo demo corre el motor en el navegador; en modo api sube a FastAPI.
 */
export async function validarCsv(nombre, texto) {
  if (ES_DEMO) return validarTextoLocal(texto)

  const form = new FormData()
  form.append('archivo', archivoCsv(nombre, texto))

  let res
  try {
    res = await fetch(`${API_URL}/api/validar-csv`, { method: 'POST', body: form })
  } catch {
    throw {
      mensaje: `No se pudo conectar con el backend en ${API_URL}.`,
      detalles: ['Verifica que el servidor FastAPI esté corriendo (uvicorn backend.main:app --port 8000).'],
    }
  }

  if (!res.ok) throw await readErrorBody(res)
  return res.json()
}

/** Sube el CSV a POST /api/reporte-pdf-csv y devuelve un Blob PDF. */
export async function descargarReportePdf(nombre, texto) {
  const form = new FormData()
  form.append('archivo', archivoCsv(nombre, texto))

  let res
  try {
    res = await fetch(`${API_URL}/api/reporte-pdf-csv`, { method: 'POST', body: form })
  } catch {
    throw { mensaje: `No se pudo conectar con el backend en ${API_URL}.`, detalles: [] }
  }

  if (!res.ok) throw await readErrorBody(res)

  const blob = await res.blob()
  const dispo = res.headers.get('Content-Disposition') || ''
  const match = dispo.match(/filename="?([^"]+)"?/)
  return { blob, filename: match ? match[1] : 'reporte-paridad.pdf' }
}
