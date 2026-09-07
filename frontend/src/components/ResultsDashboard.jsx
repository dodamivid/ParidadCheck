import { useState } from 'react'
import Semaforo from './Semaforo.jsx'
import CriterioCard from './CriterioCard.jsx'
import IncumplimientosTable from './IncumplimientosTable.jsx'
import Alert from './Alert.jsx'
import { descargarReportePdf, ES_DEMO } from '../api.js'

const GRUPOS = [
  { titulo: 'Criterios de paridad', claves: ['paridad_horizontal', 'paridad_vertical', 'paridad_transversal'] },
  {
    titulo: 'Acciones afirmativas',
    claves: ['accion_indigena', 'accion_discapacidad', 'accion_juventud', 'accion_lgbtq'],
  },
]

export default function ResultsDashboard({ resultado, entrada, onReset }) {
  const [descargando, setDescargando] = useState(false)
  const [errorPdf, setErrorPdf] = useState(null)

  async function handlePdf() {
    // En modo demo no hay backend que genere el PDF con reportlab:
    // usamos el diálogo de impresión del navegador ("Guardar como PDF").
    if (ES_DEMO) {
      window.print()
      return
    }
    setErrorPdf(null)
    setDescargando(true)
    try {
      const { blob, filename } = await descargarReportePdf(entrada?.nombre, entrada?.texto)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      setErrorPdf(err.mensaje || 'No se pudo generar el reporte PDF.')
    } finally {
      setDescargando(false)
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-3 print:hidden">
        <h2 className="text-xl font-bold text-primary-600">Resultados de la validación</h2>
        <div className="flex gap-2">
          <button
            onClick={onReset}
            className="rounded-lg border border-neutral-200 bg-white px-4 py-2 text-sm font-medium text-neutral-800 hover:bg-neutral-100"
          >
            Cargar otro CSV
          </button>
          <button
            onClick={handlePdf}
            disabled={descargando}
            className="rounded-lg bg-accent-500 px-4 py-2 text-sm font-semibold text-white hover:bg-accent-600 disabled:opacity-60"
          >
            {ES_DEMO
              ? '🖨 Imprimir / Guardar PDF'
              : descargando
                ? 'Generando PDF…'
                : '⬇ Descargar Reporte PDF'}
          </button>
        </div>
      </div>

      {errorPdf && <Alert variant="error" title={errorPdf} onClose={() => setErrorPdf(null)} />}

      <Semaforo
        estado={resultado.resultado_global}
        partido={resultado.partido}
        total={resultado.total_candidaturas}
      />

      {GRUPOS.map((grupo) => (
        <section key={grupo.titulo}>
          <h3 className="mb-3 text-lg font-semibold text-neutral-800">{grupo.titulo}</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {grupo.claves
              .filter((c) => resultado.criterios?.[c])
              .map((c) => (
                <CriterioCard key={c} clave={c} data={resultado.criterios[c]} />
              ))}
          </div>
        </section>
      ))}

      <section>
        <h3 className="mb-3 text-lg font-semibold text-neutral-800">
          Incumplimientos ({resultado.incumplimientos?.length || 0})
        </h3>
        <IncumplimientosTable incumplimientos={resultado.incumplimientos} />
      </section>
    </div>
  )
}
