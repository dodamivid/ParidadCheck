const ETIQUETAS = {
  paridad_horizontal: 'Paridad horizontal',
  paridad_vertical: 'Paridad vertical',
  paridad_transversal: 'Paridad transversal',
  accion_indigena: 'Acción afirmativa — Indígena',
  accion_discapacidad: 'Acción afirmativa — Discapacidad',
  accion_juventud: 'Acción afirmativa — Juventud',
  accion_lgbtq: 'Acción afirmativa — Diversidad sexual',
}

/** Extrae 1-2 métricas legibles de los campos extra de cada criterio. */
function metricas(clave, d) {
  if ('registrado' in d && 'requerido' in d) {
    return [`Registradas: ${d.registrado}`, `Requeridas: ${d.requerido}`]
  }
  if ('mujeres' in d && 'hombres' in d) {
    return [`Mujeres: ${d.mujeres}`, `Hombres: ${d.hombres}`]
  }
  if ('formulas_revisadas' in d) {
    return [`Fórmulas revisadas: ${d.formulas_revisadas}`, `Con violación: ${d.formulas_con_violacion}`]
  }
  if ('pares_revisados' in d) {
    return [`Pares revisados: ${d.pares_revisados}`, `Con violación: ${d.pares_con_violacion}`]
  }
  return []
}

export default function CriterioCard({ clave, data }) {
  const cumple = Boolean(data.cumple)
  const pct = Math.max(0, Math.min(100, Number(data.porcentaje_cumplimiento ?? 0)))

  return (
    <div className={`rounded-xl border bg-white p-5 shadow-sm ${cumple ? 'border-neutral-200' : 'border-danger-500'}`}>
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-semibold text-primary-600">{ETIQUETAS[clave] || clave}</h3>
        <span
          className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-bold ${
            cumple ? 'bg-success-100 text-success-700' : 'bg-danger-100 text-danger-700'
          }`}
        >
          {cumple ? '✓ Cumple' : '✗ No cumple'}
        </span>
      </div>

      <div className="mt-3">
        <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-100">
          <div
            className={`h-full rounded-full ${cumple ? 'bg-success-500' : 'bg-danger-500'}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="mt-1 text-right text-xs text-neutral-600">{pct.toFixed(0)}% de cumplimiento</p>
      </div>

      {data.descripcion && <p className="mt-3 text-sm text-neutral-800">{data.descripcion}</p>}

      <div className="mt-3 flex flex-wrap gap-2">
        {metricas(clave, data).map((m, i) => (
          <span key={i} className="rounded bg-neutral-100 px-2 py-0.5 text-xs text-neutral-800">
            {m}
          </span>
        ))}
      </div>

      {data.articulo && (
        <p className="mt-3 border-t border-neutral-100 pt-2 text-xs font-medium text-accent-500">
          ⚖️ {data.articulo}
        </p>
      )}
    </div>
  )
}
