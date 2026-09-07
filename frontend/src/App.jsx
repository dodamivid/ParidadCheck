import { useState } from 'react'
import FileUpload from './components/FileUpload.jsx'
import Alert from './components/Alert.jsx'
import { validarCsv } from './api.js'

export default function App() {
  const [estado, setEstado] = useState('idle') // idle | loading | done
  const [resultado, setResultado] = useState(null)
  const [error, setError] = useState(null)

  async function handleFile(archivo) {
    setError(null)
    setResultado(null)
    setEstado('loading')
    try {
      const data = await validarCsv(archivo)
      setResultado(data)
      setEstado('done')
    } catch (err) {
      setError({
        mensaje: err.mensaje || 'Ocurrió un error al validar el archivo.',
        detalles: err.detalles || [],
      })
      setEstado('idle')
    }
  }

  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-800">
      <header className="bg-primary-600 text-white">
        <div className="mx-auto max-w-6xl px-4 py-6">
          <h1 className="text-2xl font-extrabold">⚖️ ParidadCheck</h1>
          <p className="text-sm text-primary-100">
            Verificación automática de paridad de género y acciones afirmativas en candidaturas electorales
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        <div className="mx-auto max-w-2xl space-y-5">
          <p className="text-neutral-600">
            Sube el CSV con la lista de candidaturas de un partido. El motor de reglas validará la
            paridad horizontal, vertical y transversal, y las cuotas de acciones afirmativas.
          </p>
          {error && (
            <Alert
              variant="error"
              title={error.mensaje}
              detalles={error.detalles}
              onClose={() => setError(null)}
            />
          )}
          <FileUpload onFile={handleFile} loading={estado === 'loading'} />

          {estado === 'done' && resultado && (
            <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm">
              <p className="font-semibold text-primary-600">
                Validación completada — {resultado.partido} · {resultado.resultado_global}
              </p>
              <p className="text-sm text-neutral-600">
                {resultado.total_candidaturas} candidaturas ·{' '}
                {resultado.incumplimientos?.length || 0} incumplimiento(s). El dashboard de
                resultados se agrega en el siguiente paso.
              </p>
            </div>
          )}
        </div>
      </main>

      <footer className="mx-auto max-w-6xl px-4 py-8 text-center text-xs text-neutral-400">
        ParidadCheck · 4º Hackathon de Ciberdemocracia · IEE Chihuahua
      </footer>
    </div>
  )
}
