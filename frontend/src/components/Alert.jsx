const VARIANTS = {
  error: 'bg-danger-100 border-danger-500 text-danger-700',
  warning: 'bg-warning-100 border-warning-700 text-warning-700',
  info: 'bg-primary-50 border-primary-500 text-primary-700',
}

export default function Alert({ variant = 'error', title, detalles = [], onClose }) {
  return (
    <div className={`rounded-lg border-l-4 p-4 ${VARIANTS[variant]}`} role="alert">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-semibold">{title}</p>
          {detalles.length > 0 && (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
              {detalles.map((d, i) => (
                <li key={i}>{d}</li>
              ))}
            </ul>
          )}
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="shrink-0 text-lg font-bold leading-none opacity-60 hover:opacity-100"
            aria-label="Cerrar"
          >
            ×
          </button>
        )}
      </div>
    </div>
  )
}
