const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

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

/** Sube el CSV a POST /api/validar-csv y devuelve el ResultadoValidacion. */
export async function validarCsv(file) {
  const form = new FormData()
  form.append('archivo', file)

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
