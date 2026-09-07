function titulo(tipo) {
  return (tipo || '')
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/^\w/, (c) => c.toUpperCase())
}

export default function IncumplimientosTable({ incumplimientos }) {
  if (!incumplimientos?.length) {
    return (
      <div className="rounded-xl border border-success-500 bg-success-100 p-5 text-success-700">
        <p className="font-semibold">Sin incumplimientos detectados.</p>
        <p className="text-sm">
          La lista cumple con la normativa de paridad y acciones afirmativas aplicada.
        </p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-neutral-200 bg-white shadow-sm">
      <table className="w-full min-w-[720px] border-collapse text-left text-sm">
        <thead>
          <tr className="bg-primary-600 text-white">
            <th className="px-4 py-3 font-semibold">Tipo</th>
            <th className="px-4 py-3 font-semibold">Descripción</th>
            <th className="px-4 py-3 font-semibold">Candidaturas afectadas</th>
            <th className="px-4 py-3 font-semibold">Artículo</th>
            <th className="px-4 py-3 font-semibold">Sugerencia de corrección</th>
          </tr>
        </thead>
        <tbody>
          {incumplimientos.map((inc, i) => (
            <tr key={i} className={i % 2 ? 'bg-neutral-50' : 'bg-white'}>
              <td className="px-4 py-3 align-top">
                <span className="rounded bg-danger-100 px-2 py-1 text-xs font-bold text-danger-700">
                  {titulo(inc.tipo)}
                </span>
              </td>
              <td className="px-4 py-3 align-top text-neutral-800">{inc.descripcion}</td>
              <td className="px-4 py-3 align-top text-neutral-800">
                {inc.candidatos_afectados?.length ? (
                  <ul className="list-disc space-y-0.5 pl-4">
                    {inc.candidatos_afectados.map((n, j) => (
                      <li key={j}>{n}</li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-neutral-400">—</span>
                )}
              </td>
              <td className="px-4 py-3 align-top font-medium text-accent-500">{inc.articulo}</td>
              <td className="px-4 py-3 align-top text-neutral-800">{inc.sugerencia}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
