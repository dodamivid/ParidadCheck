// Conjuntos de datos de ejemplo empaquetados en el bundle (import `?raw` de Vite).
// Permiten probar ParidadCheck sin preparar ningún archivo — útil para
// reclutadores y para el demo público en GitHub Pages.

import ejemploBasico from './ejemplos/candidaturas_ejemplo.csv?raw'
import ayuntamientoPan from './ejemplos/oficial_ayuntamiento_chihuahua_PAN.csv?raw'
import diputacionesMorena from './ejemplos/oficial_diputaciones_mr_MORENA.csv?raw'
import diputacionesMc from './ejemplos/oficial_diputaciones_rp_MC.csv?raw'

export const EJEMPLOS = [
  {
    id: 'basico',
    archivo: 'candidaturas_ejemplo.csv',
    label: 'Ejemplo básico',
    partido: 'PAN',
    descripcion: '10 candidaturas a diputación. Caso didáctico para ver el flujo completo.',
    contenido: ejemploBasico,
  },
  {
    id: 'ayuntamiento-pan',
    archivo: 'oficial_ayuntamiento_chihuahua_PAN.csv',
    label: 'Ayuntamiento de Chihuahua',
    partido: 'PAN',
    descripcion: '18 regidurías RP con datos del proceso electoral de Chihuahua.',
    contenido: ayuntamientoPan,
  },
  {
    id: 'dip-mr-morena',
    archivo: 'oficial_diputaciones_mr_MORENA.csv',
    label: 'Diputaciones MR',
    partido: 'MORENA',
    descripcion: '20 candidaturas de mayoría relativa en distintos distritos.',
    contenido: diputacionesMorena,
  },
  {
    id: 'dip-rp-mc',
    archivo: 'oficial_diputaciones_rp_MC.csv',
    label: 'Diputaciones RP',
    partido: 'MC',
    descripcion: '10 candidaturas de representación proporcional con alternancia.',
    contenido: diputacionesMc,
  },
]
