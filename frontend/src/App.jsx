import { useState } from 'react'
import FileUpload from './components/FileUpload.jsx'
import ResultsDashboard from './components/ResultsDashboard.jsx'
import Alert from './components/Alert.jsx'
import EjemplosPanel from './components/EjemplosPanel.jsx'
import { validarCsv, ES_DEMO } from './api.js'

export default function App() {
  const [estado, setEstado] = useState('idle') // idle | loading | done
  const [resultado, setResultado] = useState(null)
  const [entrada, setEntrada] = useState(null) // { nombre, texto }
  const [error, setError] = useState(null)

  async function procesar(nombre, texto) {
    setError(null)
    setResultado(null)
    setEntrada({ nombre, texto })
    setEstado('loading')
    try {
      const data = await validarCsv(nombre, texto)
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

  async function handleFile(archivo) {
    try {
      const texto = await archivo.text()
      await procesar(archivo.name, texto)
    } catch {
      setError({ mensaje: 'No se pudo leer el archivo seleccionado.', detalles: [] })
      setEstado('idle')
    }
  }

  function reset() {
    setEstado('idle')
    setResultado(null)
    setEntrada(null)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-800">
      <header className="bg-primary-600 text-white print:hidden">
        <div className="mx-auto max-w-6xl px-4 py-6">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-extrabold">⚖️ ParidadCheck</h1>
            {ES_DEMO && (
              <span className="rounded-full bg-accent-500 px-2.5 py-1 text-xs font-bold">
                Modo demostración · sin servidor
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-primary-100">
            Verificación automática de paridad de género y acciones afirmativas en candidaturas electorales
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        {estado !== 'done' && (
          <div className="mx-auto max-w-2xl space-y-6">
            <p className="text-neutral-600">
              Sube el CSV con la lista de candidaturas de un partido. El motor de reglas validará la
              paridad horizontal, vertical y transversal, y las cuotas de acciones afirmativas.
              {ES_DEMO && ' Todo el análisis corre en tu navegador: no se sube ningún archivo a un servidor.'}
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

            <EjemplosPanel
              onSeleccionar={(ej) => procesar(ej.archivo, ej.contenido)}
              loading={estado === 'loading'}
            />
          </div>
        )}

        {estado === 'done' && resultado && (
          <ResultsDashboard resultado={resultado} entrada={entrada} onReset={reset} />
        )}
      </main>

      <footer className="mx-auto max-w-6xl px-4 py-8 text-center text-xs text-neutral-400 print:hidden">
        ParidadCheck · 4º Hackathon de Ciberdemocracia · IEE Chihuahua
      </footer>
    </div>
  )
}
