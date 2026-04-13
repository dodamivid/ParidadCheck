# GitHub Issues — ParidadCheck
## NexCode Solutions · 4º Hackathon de Ciberdemocracia 2026

---

# Issue #1

## Título
`[FEATURE] CSV Parser + Motor de Reglas de Paridad — Core del sistema`

## Labels
`feature` · `backend` · `core` · `priority: high`

## Responsable
**David Domínguez** (Backend Developer)

## Estimado
**6–8 horas**

---

## Descripción

Este issue representa el núcleo funcional de ParidadCheck. Sin este componente ninguna otra feature tiene sentido, por lo que es el **primer issue en desarrollarse** y debe quedar completamente estable antes de avanzar a los demás.

El motor de reglas debe recibir una lista de candidaturas (parseada desde un CSV), aplicar todas las validaciones de paridad y acciones afirmativas definidas en la legislación electoral mexicana, y retornar un objeto JSON estructurado con el resultado detallado de cada criterio validado, incluyendo el artículo legal exacto que se viola en cada incumplimiento.

### Contexto legal del problema

La legislación establece tres dimensiones de paridad que deben validarse de forma independiente:

- **Paridad horizontal**: Dentro de cada fórmula propietario-suplente, no pueden estar dos personas del mismo género. Fundamento: Art. 234 LGIPE.
- **Paridad vertical**: En la lista ordenada por posición numérica, los géneros deben alternarse (no pueden aparecer más de dos del mismo género consecutivos). Fundamento: Art. 233 LGIPE — criterio de alternancia.
- **Paridad transversal**: Del total de candidaturas del partido, exactamente el 50% (±1 por imparidad) deben ser mujeres y 50% hombres. Fundamento: Art. 232 párr. 3 LGIPE.

Además deben validarse las cuotas de acciones afirmativas:

- **Indígenas**: Al menos 1 de cada 10 candidaturas en distritos con población indígena significativa.
- **Discapacidad**: Al menos 1 candidatura por cada lista de representación proporcional.
- **Jóvenes (18-29)**: Al menos el 20% de las candidaturas deben ser de personas jóvenes (calculado con `fecha_nacimiento`).
- **LGBTQ+**: Al menos 1 candidatura por cada lista de representación proporcional.

---

## Criterios de Aceptación

- [ ] El endpoint `POST /api/validar` recibe un JSON con el array de candidaturas y retorna el resultado de validación completo
- [ ] El CSV parser lee correctamente el archivo, normaliza valores (trim, lowercase en booleanos) y detecta columnas faltantes con mensajes descriptivos
- [ ] El motor valida paridad **horizontal** y marca cada fórmula que incumple con el artículo legal correspondiente
- [ ] El motor valida paridad **vertical** usando ventana deslizante de 2 posiciones consecutivas
- [ ] El motor valida paridad **transversal** y calcula el delta real vs requerido en porcentaje
- [ ] El motor valida las 4 acciones afirmativas con sus respectivos umbrales
- [ ] El resultado global es `SUCCESS` solo si todos los criterios pasan; `WARNING` si hay incumplimientos menores; `DANGER` si hay incumplimiento de paridad de género
- [ ] Cada incumplimiento en el array `incumplimientos[]` incluye: tipo, candidatos_afectados[], descripción, artículo_legal, sugerencia_de_corrección
- [ ] El endpoint responde en menos de 500ms con un CSV de hasta 500 filas
- [ ] Existe un endpoint `GET /api/health` que retorna `{"status": "ok"}`
- [ ] El código tiene al menos 3 casos de prueba unitarios: lista perfecta, error de paridad vertical, acción afirmativa faltante

---

## Notas Técnicas de Implementación

```python
# Estructura de retorno esperada del motor
{
  "partido": str,
  "total_candidaturas": int,
  "resultado_global": "SUCCESS" | "WARNING" | "DANGER",
  "criterios": {
    "paridad_horizontal": {
      "status": "SUCCESS" | "WARNING" | "DANGER",
      "cumple": bool,
      "formulas_con_error": [],
      "articulo": "Art. 234 LGIPE"
    },
    "paridad_vertical": {
      "status": ...,
      "cumple": bool,
      "posiciones_conflictivas": [],
      "articulo": "Art. 233 LGIPE"
    },
    "paridad_transversal": {
      "status": ...,
      "cumple": bool,
      "mujeres": int,
      "hombres": int,
      "porcentaje_real": float,
      "articulo": "Art. 232 párr. 3 LGIPE"
    },
    "acciones_afirmativas": {
      "indigenas":    { "status": ..., "requerido": int, "registrado": int },
      "discapacidad": { "status": ..., "requerido": int, "registrado": int },
      "jovenes":      { "status": ..., "requerido": int, "registrado": int, "porcentaje": float },
      "lgbtq":        { "status": ..., "requerido": int, "registrado": int }
    }
  },
  "incumplimientos": [
    {
      "tipo": str,
      "candidatos_afectados": [str],
      "descripcion": str,
      "articulo": str,
      "sugerencia": str
    }
  ]
}
```

### Dependencias Python
```
fastapi==0.110.0
uvicorn==0.27.0
pandas==2.2.0
python-multipart==0.0.9
pydantic==2.6.0
```

### Consideraciones importantes
- Usar `pandas.read_csv()` con `dtype=str` para evitar inferencia automática de tipos.
- El cálculo de edad para "jóvenes" debe hacerse con `datetime.date.today()` relativo a `fecha_nacimiento`.
- El umbral de alternancia vertical: si `candidato[i].genero == candidato[i+1].genero`, hay violación.
- CORS habilitado para `localhost:5173` en desarrollo.

---

## Archivos a crear

```
backend/
├── main.py
├── models/
│   └── candidatura.py
├── services/
│   ├── csv_parser.py
│   └── motor_paridad.py
├── constants/
│   └── legislacion.py
├── tests/
│   └── test_motor.py
└── requirements.txt
```

---

---

# Issue #2

## Título
`[FEATURE] Dashboard de Resultados con Semáforo — Visualización principal`

## Labels
`feature` · `frontend` · `ui` · `priority: high`

## Responsable
**Diego Zamarrón** (Frontend Developer)

## Estimado
**5–7 horas**

**Dependencia:** Requiere Issue #1 funcional (o mockeado con datos de prueba)

---

## Descripción

El Dashboard es la pantalla más importante de ParidadCheck desde la perspectiva de los jueces del hackathón. Es lo primero que ven después de subir un CSV y debe comunicar el resultado de validación de forma **inmediata, visual e inequívoca** sin necesidad de que el usuario lea texto alguno.

El diseño debe equilibrar la seriedad institucional del contexto electoral con una experiencia de usuario moderna. Nada de tablas HTML planas y texto negro sobre blanco — cada elemento visual debe tener intención.

### Componentes principales del dashboard

1. **Header de resultado global**: Banner prominente verde/amarillo/rojo con el veredicto general y nombre del partido.
2. **Cards de criterios**: 6 cards individuales (paridad horizontal, vertical, transversal + 4 acciones afirmativas), cada una con su semáforo, porcentaje real vs requerido y el artículo legal.
3. **Tabla de candidaturas**: Lista completa con filas coloreadas según su estado de cumplimiento.
4. **Panel de incumplimientos**: Lista expandible de cada violación con descripción, artículo y sugerencia de corrección.
5. **Botón de descarga PDF**: CTA prominente para generar el reporte.

---

## Criterios de Aceptación

- [ ] El banner de resultado global es visualmente dominante: verde SUCCESS, amarillo WARNING, rojo DANGER con ícono y texto de veredicto
- [ ] Las 6 cards de criterios muestran: ícono de semáforo, nombre del criterio, porcentaje real vs requerido, y artículo legal en texto pequeño
- [ ] La tabla de candidaturas tiene: columnas ordenables, filtro por estado (todas/con error/sin error), filas con fondo rojo claro para candidatos con incumplimiento
- [ ] El panel de incumplimientos es colapsable por tipo de criterio y muestra la sugerencia de corrección
- [ ] El botón "Descargar Reporte PDF" llama al endpoint de Issue #3 y hace download automático
- [ ] El botón "Corregir candidaturas" regresa al formulario de upload con los datos ya cargados
- [ ] El dashboard es responsive (funciona correctamente en pantalla de laptop para la demo)
- [ ] Usa la paleta de colores definida en `tailwind.config.js` (primary-600, success-500, warning-500, danger-500)
- [ ] Los componentes usan shadcn/ui (Badge, Card, Table, Collapsible, Button)
- [ ] Todos los mensajes de error son descriptivos y accionables, no genéricos

---

## Notas Técnicas de Implementación

```jsx
// Estructura de componentes sugerida
src/components/dashboard/
  ResultadoGlobalBanner.jsx
  CriterioCard.jsx
  CriteriosGrid.jsx
  TablaCandidaturas.jsx
  PanelIncumplimientos.jsx
  BotonDescargaPDF.jsx
```

```jsx
// Lógica de colores por status — usar en todos los componentes
const statusConfig = {
  SUCCESS: { bg: 'bg-success-100', text: 'text-success-700', border: 'border-success-500', icon: '✅', label: 'Cumple' },
  WARNING: { bg: 'bg-warning-100', text: 'text-warning-700', border: 'border-warning-500', icon: '⚠️', label: 'Atención requerida' },
  DANGER:  { bg: 'bg-danger-100',  text: 'text-danger-700',  border: 'border-danger-500',  icon: '❌', label: 'Incumplimiento' }
}
```

### Mock de datos
Crear `src/mocks/resultadoEjemplo.json` con un resultado de validación completo (mezcla de SUCCESS, WARNING y DANGER) para desarrollar el UI sin depender del backend.

---

## Archivos a crear

```
frontend/src/
├── components/dashboard/
│   ├── ResultadoGlobalBanner.jsx
│   ├── CriterioCard.jsx
│   ├── CriteriosGrid.jsx
│   ├── TablaCandidaturas.jsx
│   ├── PanelIncumplimientos.jsx
│   └── BotonDescargaPDF.jsx
├── views/
│   └── DashboardView.jsx
├── mocks/
│   └── resultadoEjemplo.json
└── tailwind.config.js   ← agregar paleta de colores ParidadCheck
```

---

---

# Issue #3

## Título
`[FEATURE] Upload CSV + Formulario de Corrección + Reporte PDF Institucional`

## Labels
`feature` · `frontend` · `backend` · `pdf` · `priority: high`

## Responsable
**Carlos Alvarado** (Project Lead)

## Estimado
**7–9 horas**

**Dependencia:** Requiere Issue #1 funcional para la parte del PDF

---

## Descripción

Este issue agrupa dos responsabilidades de Carlos que están conectadas por el flujo del usuario: la **entrada de datos** (upload del CSV) y la **salida final** (reporte PDF descargable). Juntas cubren el inicio y el cierre del flujo completo de ParidadCheck.

### Parte A — Upload CSV + Preview + Formulario de Corrección

La primera interacción del usuario debe ser sin fricción. El flujo es:
1. El usuario llega a la pantalla de inicio y ve una zona de carga prominente
2. Arrastra su CSV o hace clic para buscarlo
3. El sistema valida el formato inmediatamente en el frontend
4. Preview de los primeros 10 registros para confirmación visual
5. El usuario puede editar cualquier candidato inline antes de validar
6. Botón "Validar Paridad" envía los datos al backend

El formulario de corrección también debe estar disponible **después** del dashboard para corregir y re-validar sin re-subir el CSV.

### Parte B — Generador de Reporte PDF Institucional (WeasyPrint)

El PDF es el deliverable tangible del sistema. Un funcionario del IEE debe poder imprimirlo y archivarlo. Se genera en el backend con WeasyPrint a partir de un template HTML/CSS.

**Contenido del PDF:**
- **Portada**: Logo, nombre del partido, fecha/hora, folio UUID, semáforo de resultado global
- **Resumen ejecutivo**: Tabla de 6 criterios con estatus, porcentaje real vs requerido y artículo legal
- **Detalle de candidaturas**: Tabla completa con filas marcadas en rojo donde hay incumplimiento
- **Pie legal**: Leyenda de responsabilidad y versión del sistema

---

## Criterios de Aceptación

### Parte A — Upload y formulario
- [ ] La zona de drag & drop cambia visualmente al arrastrar un archivo sobre ella (border dashed animado)
- [ ] Si el archivo no es CSV muestra: "Solo se aceptan archivos .csv"
- [ ] La validación de columnas se hace en el frontend antes de enviar al backend
- [ ] Si faltan columnas, el error especifica exactamente cuáles
- [ ] La preview muestra los primeros 10 registros con todas las columnas
- [ ] Cada fila tiene botón de edición que abre un modal con formulario para ese candidato
- [ ] El formulario de edición valida valores permitidos por campo (género: M, F, NB; booleanos: checkboxes)
- [ ] El botón "Validar Paridad" está deshabilitado hasta tener datos válidos
- [ ] El botón muestra spinner y "Validando..." durante el proceso (mínimo 800ms visible)
- [ ] Hay enlace para descargar el CSV de ejemplo
- [ ] Desde el Dashboard, "Corregir candidaturas" regresa aquí con datos pre-cargados

### Parte B — Reporte PDF
- [ ] El endpoint `POST /api/reporte` recibe el JSON de resultados y retorna `application/pdf`
- [ ] La portada incluye todos los campos requeridos con semáforo en el color correcto
- [ ] La tabla de resumen ejecutivo muestra los 6 criterios con su estatus visual
- [ ] Las filas con incumplimiento están marcadas visualmente en la tabla de candidaturas
- [ ] El PDF tiene header y footer en cada página (nombre del partido + número de página)
- [ ] El documento se ve profesional impreso en tamaño carta
- [ ] El nombre del archivo sigue el patrón: `ParidadCheck_{partido}_{fecha}.pdf`
- [ ] La generación toma menos de 3 segundos

---

## Notas Técnicas de Implementación

### Frontend — CSV parsing
```jsx
import Papa from 'papaparse'

const handleFileUpload = (file) => {
  Papa.parse(file, {
    header: true,
    skipEmptyLines: true,
    complete: (results) => {
      const columnsRequeridas = [
        'nombre', 'genero', 'partido', 'cargo', 'tipo',
        'posicion', 'distrito', 'indigena', 'discapacidad',
        'fecha_nacimiento', 'lgbtq'
      ]
      const columnasFaltantes = columnsRequeridas.filter(
        col => !results.meta.fields.includes(col)
      )
      if (columnasFaltantes.length > 0) {
        setError(`Columnas faltantes: ${columnasFaltantes.join(', ')}`)
        return
      }
      setCandidaturas(results.data)
    }
  })
}
```

### Backend — PDF con WeasyPrint
```python
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
import uuid
from datetime import datetime

def generar_reporte_pdf(resultado: dict) -> bytes:
    env = Environment(loader=FileSystemLoader('templates/'))
    template = env.get_template('reporte.html')
    html_content = template.render(
        resultado=resultado,
        folio=str(uuid.uuid4())[:8].upper(),
        fecha_generacion=datetime.now().strftime("%d de %B de %Y, %H:%M hrs"),
        version_sistema="1.0.0"
    )
    return HTML(string=html_content).write_pdf()

@app.post("/api/reporte")
async def generar_reporte(resultado: ResultadoValidacion):
    pdf_bytes = generar_reporte_pdf(resultado.dict())
    partido = resultado.partido.replace(" ", "_")
    fecha = datetime.now().strftime("%Y%m%d")
    filename = f"ParidadCheck_{partido}_{fecha}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

### Dependencias adicionales
```
# Frontend
papaparse

# Backend
weasyprint==62.1
jinja2==3.1.3
```

> ⚠️ WeasyPrint en Ubuntu/Debian: `apt-get install -y libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0`

### Colores del template PDF
- Azul institucional: `#1B2B5E` | Verde: `#16A34A` | Amarillo: `#CA8A04` | Rojo: `#DC2626`

---

## Archivos a crear

```
frontend/src/
├── components/upload/
│   ├── DropZone.jsx
│   ├── PreviewTable.jsx
│   ├── EditCandidatoModal.jsx
│   └── ValidarButton.jsx
├── views/
│   └── UploadView.jsx
├── utils/
│   └── csvValidator.js
└── examples/
    └── candidaturas_ejemplo.csv

backend/
├── services/
│   └── pdf_generator.py
├── templates/
│   ├── reporte.html
│   └── styles/
│       └── reporte.css
└── main.py   ← agregar endpoint POST /api/reporte
```

---

---

# Issue #4

## Título
`[QA] Plan de pruebas y validación end-to-end del sistema`

## Labels
`qa` · `testing` · `priority: high`

## Responsable
**Iván López** (QA Engineer)

## Estimado
**4–5 horas** (ejecutado en paralelo con los demás issues)

---

## Descripción

El QA de ParidadCheck es crítico porque el sistema toma decisiones con implicaciones legales. Un falso positivo (decir que cumple cuando no cumple) o un falso negativo (marcar error donde no lo hay) puede destruir la credibilidad del proyecto frente a los jueces.

Iván es responsable de diseñar y ejecutar el plan de pruebas completo, crear los datasets de prueba con casos específicos, documentar los bugs encontrados como issues secundarios, y validar que el flujo completo funcione sin errores antes de la presentación final.

---

## Criterios de Aceptación

- [ ] Existe `tests/casos_prueba.md` con al menos 10 casos de prueba documentados
- [ ] `candidaturas_OK.csv` — lista perfectamente válida, debe retornar SUCCESS en todos los criterios
- [ ] `candidaturas_paridad_vertical_error.csv` — violación de alternancia en posiciones 3 y 5
- [ ] `candidaturas_paridad_horizontal_error.csv` — fórmula propietario-suplente del mismo género
- [ ] `candidaturas_accion_afirmativa_faltante.csv` — sin candidaturas con discapacidad
- [ ] `candidaturas_todo_mal.csv` — múltiples violaciones para probar el caso DANGER completo
- [ ] `candidaturas_formato_invalido.csv` — columnas faltantes para probar validación de formato
- [ ] Cada caso documenta: input, resultado esperado, resultado obtenido, status PASS/FAIL
- [ ] Se prueba el flujo completo: upload → validación → dashboard → descarga PDF
- [ ] El PDF generado se abre correctamente y los datos coinciden con el dashboard
- [ ] Se prueba en Chrome y Firefox
- [ ] Sin errores en consola del navegador durante el flujo normal
- [ ] El sistema maneja correctamente: CSV vacío, CSV con 1 fila, CSV con 500 filas

---

## Notas Técnicas

### Estructura de casos de prueba

```markdown
## Caso #01 — Lista válida completa
- **Archivo:** candidaturas_OK.csv
- **Descripción:** 20 candidaturas con paridad perfecta y todas las acciones afirmativas cubiertas
- **Resultado esperado:** resultado_global = "SUCCESS", todos los criterios en verde
- **Resultado obtenido:** [completar durante ejecución]
- **Status:** [ ] PASS  [ ] FAIL
- **Notas:** [observaciones]

## Caso #02 — Violación de paridad vertical
- **Archivo:** candidaturas_paridad_vertical_error.csv
- **Descripción:** Posiciones 3 y 5 son del mismo género (M-M consecutivos)
- **Resultado esperado:** paridad_vertical.status = "DANGER", cita Art. 233 LGIPE
- **Resultado obtenido:** [completar]
- **Status:** [ ] PASS  [ ] FAIL
```

### Herramientas
- Backend: `pytest` con los archivos CSV de prueba
- Frontend: manual con DevTools abierto para monitorear errores de consola
- PDF: abrir en Chrome/Adobe Reader y verificar datos visualmente

### Cómo reportar bugs
```
**Descripción:** Qué pasó
**Pasos para reproducir:** 1. 2. 3.
**Resultado esperado:**
**Resultado obtenido:**
**CSV de prueba:** (adjuntar archivo)
```

---

## Archivos a crear

```
tests/
├── casos_prueba.md
├── csv/
│   ├── candidaturas_OK.csv
│   ├── candidaturas_paridad_vertical_error.csv
│   ├── candidaturas_paridad_horizontal_error.csv
│   ├── candidaturas_accion_afirmativa_faltante.csv
│   ├── candidaturas_todo_mal.csv
│   └── candidaturas_formato_invalido.csv
└── test_motor.py
```

---

*Generado para ParidadCheck — NexCode Solutions · 4º Hackathon de Ciberdemocracia 2026*
