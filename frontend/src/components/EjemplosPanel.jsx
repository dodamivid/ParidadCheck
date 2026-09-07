import { EJEMPLOS } from '../demo/ejemplos.js'

/**
 * Panel de datos de ejemplo. Pensado para quien solo quiere ver cómo funciona
 * la herramienta (reclutadores, evaluadores) sin preparar ningún CSV.
 */
export default function EjemplosPanel({ onSeleccionar, loading }) {
  return (
    <section className="rounded-xl border border-neutral-200 bg-white p-5">
      <h2 className="font-semibold text-primary-600">🧪 ¿Solo quieres ver cómo funciona?</h2>
      <p className="mt-1 text-sm text-neutral-600">
        No necesitas preparar nada. Carga uno de estos conjuntos de datos de ejemplo —basados en
        listas del proceso electoral de Chihuahua— y revisa el análisis completo: semáforo,
        criterios de paridad, acciones afirmativas e incumplimientos con su fundamento legal.
      </p>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {EJEMPLOS.map((ej) => (
          <button
            key={ej.id}
            type="button"
            disabled={loading}
            onClick={() => onSeleccionar(ej)}
            className="flex flex-col rounded-lg border border-neutral-200 bg-neutral-50 p-3 text-left transition hover:border-primary-500 hover:bg-primary-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span className="flex items-center gap-2">
              <span className="font-semibold text-neutral-800">{ej.label}</span>
              <span className="rounded bg-primary-600 px-1.5 py-0.5 text-[10px] font-bold text-white">
                {ej.partido}
              </span>
            </span>
            <span className="mt-1 text-xs text-neutral-600">{ej.descripcion}</span>
            <span className="mt-2 text-xs font-medium text-accent-500">Cargar ejemplo →</span>
          </button>
        ))}
      </div>

      <p className="mt-3 text-xs text-neutral-400">
        Los mismos archivos están en <code className="text-neutral-600">examples/</code> del repositorio.
      </p>
    </section>
  )
}
