import { useRef, useState } from 'react'

export default function FileUpload({ onFile, loading }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [nombre, setNombre] = useState('')

  function handleFiles(fileList) {
    const file = fileList?.[0]
    if (!file) return
    setNombre(file.name)
    onFile(file)
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    if (!loading) handleFiles(e.dataTransfer.files)
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !loading && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && !loading && inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-14 text-center transition
          ${dragging ? 'border-accent-500 bg-accent-500/5' : 'border-neutral-200 bg-white hover:border-primary-500'}
          ${loading ? 'pointer-events-none opacity-60' : ''}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />

        {loading ? (
          <>
            <Spinner />
            <p className="mt-3 font-medium text-primary-600">Validando candidaturas…</p>
          </>
        ) : (
          <>
            <svg className="h-12 w-12 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 7.5 7.5 12M12 7.5V21" />
            </svg>
            <p className="mt-3 font-semibold text-primary-600">
              Arrastra y suelta el CSV de candidaturas
            </p>
            <p className="text-sm text-neutral-600">o haz clic para seleccionar el archivo</p>
            {nombre && (
              <p className="mt-3 rounded bg-neutral-100 px-3 py-1 text-sm text-neutral-800">
                {nombre}
              </p>
            )}
          </>
        )}
      </div>

      <p className="mt-3 text-xs text-neutral-600">
        Columnas requeridas: <code className="text-neutral-800">nombre, genero, partido, cargo, tipo,
        posicion, distrito, indigena, discapacidad, fecha_nacimiento, lgbtq</code>. Un solo partido por archivo.
      </p>
    </div>
  )
}

function Spinner() {
  return (
    <svg className="h-10 w-10 animate-spin text-accent-500" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.4 0 0 5.4 0 12h4z" />
    </svg>
  )
}
