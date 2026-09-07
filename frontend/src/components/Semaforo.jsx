const CONFIG = {
  SUCCESS: {
    color: 'bg-success-500',
    ring: 'ring-success-500/30',
    texto: 'CUMPLE',
    glosa: 'La lista satisface todos los criterios de paridad y acciones afirmativas.',
    activa: 0,
  },
  WARNING: {
    color: 'bg-warning-500',
    ring: 'ring-warning-500/30',
    texto: 'CUMPLIMIENTO PARCIAL',
    glosa: 'La paridad se cumple, pero hay observaciones en acciones afirmativas.',
    activa: 1,
  },
  DANGER: {
    color: 'bg-danger-500',
    ring: 'ring-danger-500/30',
    texto: 'NO CUMPLE',
    glosa: 'Se detectaron incumplimientos de paridad que pueden derivar en impugnación.',
    activa: 2,
  },
}

export default function Semaforo({ estado, partido, total }) {
  const cfg = CONFIG[estado] || CONFIG.DANGER
  const luces = ['bg-danger-500', 'bg-warning-500', 'bg-success-500'] // rojo, amarillo, verde (top→bottom)
  const activaIdx = { DANGER: 0, WARNING: 1, SUCCESS: 2 }[estado]

  return (
    <div className="flex flex-col items-center gap-6 rounded-xl bg-white p-6 shadow-sm sm:flex-row sm:items-center sm:gap-10">
      <div className="flex flex-col gap-3 rounded-2xl bg-neutral-900 p-4">
        {luces.map((c, i) => (
          <span
            key={i}
            className={`h-12 w-12 rounded-full transition ${
              i === activaIdx ? `${c} ring-8 ${cfg.ring}` : 'bg-neutral-800'
            }`}
          />
        ))}
      </div>

      <div className="text-center sm:text-left">
        <p className="text-sm uppercase tracking-wide text-neutral-600">Resultado global</p>
        <p
          className={`mt-1 inline-block rounded-lg px-4 py-1.5 text-2xl font-extrabold text-white ${cfg.color}`}
        >
          {cfg.texto}
        </p>
        <p className="mt-3 max-w-md text-sm text-neutral-800">{cfg.glosa}</p>
        <p className="mt-2 text-sm text-neutral-600">
          Partido <span className="font-semibold text-primary-600">{partido}</span> ·{' '}
          {total} candidatura{total === 1 ? '' : 's'}
        </p>
      </div>
    </div>
  )
}
