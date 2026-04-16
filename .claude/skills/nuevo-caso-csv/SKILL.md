---
name: nuevo-caso-csv
description: Use when creating CSV test fixtures for ParidadCheck (candidaturas_*.csv files in tests/csv/), generating example candidatura data for a specific paridad scenario, debugging HTTPException 422 from the CSV parser in backend/services/csv_parser.py, or explaining the expected input format to a user. Covers the 11 required columns, valid values, boolean/date normalization, single-partido constraint, and canonical test case recipes (SUCCESS, WARNING, DANGER variants).
---

# Nuevo Caso CSV — ParidadCheck

Formato exacto del CSV que acepta ParidadCheck y recetas para generar casos de prueba. Úsala cuando crees un nuevo fixture en `tests/csv/`, debuggees un 422 del parser, o necesites explicar qué formato debe tener el archivo del usuario.

## Estructura del CSV

Las 11 columnas obligatorias están en `backend/constants/legislacion.py::COLUMNAS_REQUERIDAS`. **Esa es la lista autoritativa.** Si cambia ahí, los fixtures deben regenerarse.

| Columna | Tipo | Valores válidos | Normalización del parser |
|---|---|---|---|
| `nombre` | string | Texto libre, no vacío | `str_strip_whitespace` (Pydantic) + `strip()` |
| `genero` | string | `M`, `F`, `NB` | `strip().upper()` |
| `partido` | string | Siglas, **únicas por archivo** | `strip()` |
| `cargo` | string | Texto libre (ej: `DIPUTADO_LOCAL`) | `strip()` |
| `tipo` | string | `PROPIETARIO`, `SUPLENTE` | `strip().upper()` |
| `posicion` | int | Entero ≥ 1 | `int()` con try/except |
| `distrito` | string | Texto libre (ej: `D01`) | `strip()` |
| `indigena` | bool | Ver abajo | `_parse_bool()` |
| `discapacidad` | bool | Ver abajo | `_parse_bool()` |
| `fecha_nacimiento` | date | `YYYY-MM-DD` | `datetime.strptime(..., "%Y-%m-%d")` |
| `lgbtq` | bool | Ver abajo | `_parse_bool()` |

### Valores booleanos aceptados (case-insensitive)

- **True**: `true`, `1`, `si`, `sí`, `yes`
- **False**: `false`, `0`, `no`

Cualquier otro valor lanza `HTTPException(422)` con el número de fila (1-indexed, contando el encabezado como fila 1, así que los datos empiezan en fila 2).

### Restricciones de formato

- Encoding: **UTF-8**, BOM opcional (el parser usa `utf-8-sig` para tolerar el BOM que Excel agrega).
- **Un solo partido por archivo.** Múltiples partidos → 422 con mensaje listando los partidos encontrados.
- Cabecera obligatoria en la primera línea.
- Columnas faltantes → 422 con la lista exacta de columnas faltantes.
- `pandas.read_csv()` se llama con `dtype=str` y `keep_default_na=False` para evitar inferencia automática de tipos y preservar strings vacíos como strings.
- El parser acumula errores por fila antes de lanzar — un CSV con 10 errores reporta los 10, no solo el primero.

## Rangos y umbrales que afectan los fixtures

Todos en `backend/constants/legislacion.py`:

- **Juventud**: `fecha_nacimiento.year` entre `ANIO_JUVENTUD_MIN` (1997) y `ANIO_JUVENTUD_MAX` (2008). Usa una fecha como `2001-05-15` para crear una candidatura joven.
- **Umbral transversal**: 0.05 (±5% de tolerancia sobre 50/50 M-F).
- **Umbral indígena**: 0.03 (3%). Con 20 candidaturas, `math.ceil(20 * 0.03) = 1` indígena mínimo.
- **Umbrales discapacidad / juventud / lgbtq**: 0.01 (1%). Con 20 candidaturas, `math.ceil(20 * 0.01) = 1` mínimo cada uno.

**Tip para fixtures pequeños**: `math.ceil()` redondea hacia arriba, así que incluso con 10 candidaturas necesitas al menos 1 de cada acción afirmativa (ceil(10 * 0.01) = 1).

## Recetas de casos canónicos

### Caso A — Lista perfecta (SUCCESS)

Estructura: 10 fórmulas, 20 candidaturas totales.

- Propietarios alternando M (posiciones impares) / F (posiciones pares) 1-10.
- Suplentes con género opuesto al propietario de su misma fórmula.
- Mismo `partido`, mismo `cargo`, mismo `distrito` (ej: `PAN`, `DIPUTADO_LOCAL`, `D01`).
- Acciones afirmativas distribuidas sobre propietarios (para no romper paridad horizontal):
  - Propietario 1 (M, posición 1): `indigena=true`, `fecha_nacimiento=2001-03-10` (joven).
  - Propietario 3 (M, posición 3): `discapacidad=true`.
  - Propietario 5 (M, posición 5): `lgbtq=true`.

Esperado: `resultado_global = "SUCCESS"`, todos los criterios `cumple=True`, `incumplimientos=[]`.

### Caso B — Violación paridad vertical (DANGER)

Misma estructura que A, pero los géneros de propietarios siguen el patrón `["M","F","M","M","F","F","M","F","M","F"]`. Las posiciones consecutivas 3-4 son M-M y 5-6 son F-F → rompe alternancia del Art. 233.

Esperado: `DANGER`, `paridad_vertical.cumple=False`, los incumplimientos de tipo `PARIDAD_VERTICAL` citan `Art. 233 LGIPE`.

### Caso C — Violación paridad horizontal (DANGER)

Estructura A, pero la fórmula en posición 1 tiene propietario M y suplente M (mismo género).

Esperado: `DANGER`, `paridad_horizontal.cumple=False`, `candidatos_afectados` del incumplimiento incluye los nombres de ambos candidatos de la fórmula rota.

### Caso D — Acción afirmativa faltante (WARNING)

Estructura A, pero **todas** las filas con `discapacidad=false`. Paridad de género se mantiene perfecta.

Esperado: `WARNING` (no DANGER, porque la paridad sí cumple). `accion_discapacidad.cumple=False`, resto de criterios en verde. Prueba crítica del semáforo: valida que WARNING no se confunda con DANGER.

### Caso E — Columnas faltantes (422)

Omite `lgbtq` del header (deja solo 10 columnas). El parser debe lanzar `HTTPException(422)` con mensaje que mencione explícitamente la columna faltante. Ver `test_csv_columna_faltante_422` en `test_motor.py`.

### Caso F — Múltiples partidos (422)

Estructura A pero una fila con `partido=MORENA` y el resto `PAN`. Debe lanzar 422 con mensaje que liste ambos partidos.

### Caso G — Todo mal (DANGER con múltiples incumplimientos)

Combina paridad vertical rota + paridad horizontal rota + discapacidad faltante + transversal sesgada (ej: 70% M, 30% F). Útil para probar que `incumplimientos` acumula todos los errores, no solo el primero.

Esperado: `DANGER`, al menos 3 incumplimientos de tipos distintos.

## CSV mínimo válido (para smoke tests)

```csv
nombre,genero,partido,cargo,tipo,posicion,distrito,indigena,discapacidad,fecha_nacimiento,lgbtq
Ana Ramírez López,F,PAN,DIPUTADO_LOCAL,PROPIETARIO,1,D01,true,false,2001-03-15,false
Carlos Mendoza Ruiz,M,PAN,DIPUTADO_LOCAL,SUPLENTE,1,D01,false,true,1988-07-22,true
Roberto Sánchez Cruz,M,PAN,DIPUTADO_LOCAL,PROPIETARIO,2,D01,false,false,1975-11-08,false
María González Pérez,F,PAN,DIPUTADO_LOCAL,SUPLENTE,2,D01,false,false,1995-01-30,false
```

Este fixture cumple paridad horizontal (ambas fórmulas M-F) y vertical (propietarios M-F alternan por posición). No cumple transversal al 100% porque son solo 4 candidaturas, pero sirve como baseline para smoke tests del parser.

## Dónde guardar los fixtures

Según Issue #4, los CSV de prueba van en `tests/csv/` con nombres canónicos:

- `candidaturas_OK.csv`
- `candidaturas_paridad_vertical_error.csv`
- `candidaturas_paridad_horizontal_error.csv`
- `candidaturas_accion_afirmativa_faltante.csv`
- `candidaturas_todo_mal.csv`
- `candidaturas_formato_invalido.csv`

Cada caso debe estar documentado en `tests/casos_prueba.md` con: descripción, resultado esperado (resultado_global + criterios afectados + artículo citado), y relación con los criterios de aceptación del issue.

## Errores comunes al escribir CSVs de prueba

- **Usar `propietario` en minúsculas en el CSV.** El parser lo uppercasea, pero es mejor escribir `PROPIETARIO` directamente para que visualmente coincida con `TIPOS_VALIDOS`.
- **Fechas en formato `DD/MM/YYYY` o `MM-DD-YYYY`.** Solo se acepta ISO `YYYY-MM-DD`. Cualquier otro formato lanza 422.
- **Booleanos mezclados** (`true` en unas filas, `yes` en otras, `sí` en otras). Técnicamente funciona, pero confunde al lector. Sé consistente dentro del archivo — recomendado: siempre `true`/`false`.
- **Incluir columna `joven` o `edad`.** No existen. Juventud se deriva de `fecha_nacimiento.year` dentro del rango `ANIO_JUVENTUD_MIN`/`MAX`.
- **Dos partidos distintos en un solo CSV.** El sistema está diseñado para 1 partido por validación — si necesitas validar varios, crea un archivo por partido.
- **Olvidar rellenar una columna booleana.** El parser rechaza strings vacíos como bool inválido. Usa explícitamente `false`.
- **Crear el fixture `candidaturas_todo_mal.csv` rompiendo solo 1 cosa.** Debe tener múltiples violaciones simultáneas para probar el caso DANGER completo.
- **Fórmulas incompletas sin intención.** Si omites el suplente de una fórmula, el parser lo acepta pero el motor no valida paridad horizontal para esa fórmula. Si esto es intencional (para probar edge case), documéntalo; si no, agrega el suplente.
