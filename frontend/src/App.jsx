import { useState } from 'react'
import FileUpload from './components/FileUpload.jsx'
import ResultsDashboard from './components/ResultsDashboard.jsx'
import Alert from './components/Alert.jsx'
import { validarCsv } from './api.js'

export default function App() {
  const [estado, setEstado] = useState('idle') // idle | loading | done
  const [resultado, setResultado] = useState(null)
  const [file, setFile] = useState(null)
  const [error, setError] = useState(null)

  async function handleFile(nuevoArchivo) {
    setError(null)
    setResultado(null)
    setFile(nuevoArchivo)
    setEstado('loading')
    try {
      const data = await validarCsv(nuevoArchivo)
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

  function reset() {
    setEstado('idle')
    setResultado(null)
    setFile(null)
    setError(null)
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
        {estado !== 'done' && (
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
          </div>
        )}

        {estado === 'done' && resultado && (
          <ResultsDashboard resultado={resultado} file={file} onReset={reset} />
        )}
      </main>

      <footer className="mx-auto max-w-6xl px-4 py-8 text-center text-xs text-neutral-400">
        ParidadCheck · 4º Hackathon de Ciberdemocracia · IEE Chihuahua
      </footer>
    </div>
  )
}
