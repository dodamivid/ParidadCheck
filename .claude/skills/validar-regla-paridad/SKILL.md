---
name: validar-regla-paridad
description: Use when working on the ParidadCheck rules engine (backend/services/motor_paridad.py), adding or modifying paridad / acciones afirmativas validations, debugging output from POST /api/validar, or writing tests for the rule engine. Covers the 7 legal rules, their LGIPE articles, thresholds, the ResultadoValidacion JSON schema, and the test patterns used in backend/tests/test_motor.py.
---

# Validar Regla de Paridad — ParidadCheck

Contexto preciso del motor de reglas de ParidadCheck: las 7 validaciones legales, sus umbrales, el shape del output JSON y los patrones de tests. Úsala antes de tocar `backend/services/motor_paridad.py`, agregar reglas nuevas, o explicar un resultado del endpoint `/api/validar`.

## Single source of truth

**Todas las constantes legales viven en `backend/constants/legislacion.py`.** Nunca hardcodees strings legales (`"Art. 233 LGIPE"`) ni números mágicos (`0.03`, `1997`) en otros archivos. Si necesitas una constante nueva, créala ahí primero e impórtala.

## Las 7 reglas del motor

### Paridad de género (3 reglas)

| Regla | Función | Constante artículo | Agrupación | Lógica |
|---|---|---|---|---|
| Horizontal | `_paridad_horizontal` | `ART_PARIDAD_HORIZONTAL` = "Art. 234 LGIPE" | `(posicion, distrito, cargo)` | Propietario y suplente deben tener géneros distintos. Fórmulas donde algún miembro es `NB` quedan exentas del check binario. Fórmulas incompletas (solo propietario o solo suplente) se saltan. |
| Vertical | `_paridad_vertical` | `ART_PARIDAD_VERTICAL` = "Art. 233 LGIPE" | `(partido, cargo, tipo)` | Ventana deslizante de 2. Alternancia M/F en listas ordenadas por `posicion`. **Propietarios y suplentes se evalúan por separado** — Art. 233 aplica a cada lista ordenada, no a la mezcla. `NB` se excluye del análisis binario. |
| Transversal | `_paridad_transversal` | `ART_PARIDAD_TRANSVERSAL` = "Art. 232 LGIPE" | Todas las candidaturas | 50% M / 50% F con tolerancia `UMBRAL_TRANSVERSAL_TOLERANCIA` = 0.05 (±5%). `NB` no cuenta en el denominador binario. |

### Acciones afirmativas (4 reglas, todas `Art. 14 LGIPE`)

| Campo de la candidatura | Constante umbral | Valor | Función |
|---|---|---|---|
| `indigena` (bool) | `UMBRAL_INDIGENA` | 0.03 (3%) | `_accion_afirmativa` (plantilla genérica) |
| `discapacidad` (bool) | `UMBRAL_DISCAPACIDAD` | 0.01 (1%) | `_accion_afirmativa` |
| juventud (derivada de `fecha_nacimiento`) | `UMBRAL_JUVENTUD` | 0.01 (1%) | `_accion_juventud` (especial) |
| `lgbtq` (bool) | `UMBRAL_LGBTQ` | 0.01 (1%) | `_accion_afirmativa` |

**Juventud es especial**: no usa un campo booleano, se calcula con `fecha_nacimiento.year` entre `ANIO_JUVENTUD_MIN` (1997) y `ANIO_JUVENTUD_MAX` (2008). Por eso tiene su propia función y no encaja en la plantilla `_accion_afirmativa`.

Las otras 3 acciones afirmativas reutilizan `_accion_afirmativa()` como plantilla genérica. **Si agregas una acción afirmativa nueva sobre un campo bool simple, llama a la plantilla desde `validar()` — no dupliques código.** Si la nueva acción requiere lógica derivada (como juventud), crea una función propia.

## Semáforo global — precedencia intencional

```python
if falla_paridad (horizontal OR vertical OR transversal):
    resultado_global = "DANGER"
elif falla_afirmativa (indigena OR discapacidad OR juventud OR lgbtq):
    resultado_global = "WARNING"
else:
    resultado_global = "SUCCESS"
```

**Esta precedencia es intencional y legal, no estética.** Paridad de género es incumplimiento GRAVE (impugnable ante TEPJF, puede invalidar toda la lista); acciones afirmativas son incumplimiento LEVE (advertencia, se puede subsanar). Nunca cambies esta precedencia sin justificación legal explícita del equipo.

## Shape del output (contrato con el frontend)

Definido en `backend/models/candidatura.py` con Pydantic. **Cualquier cambio al shape rompe el dashboard** (Issue #2). Si cambias, avisa.

```python
ResultadoValidacion {
    partido: str
    total_candidaturas: int
    resultado_global: Literal["SUCCESS", "WARNING", "DANGER"]
    criterios: {
        "paridad_horizontal":  {cumple, porcentaje_cumplimiento, articulo, descripcion, formulas_revisadas, formulas_con_violacion},
        "paridad_vertical":    {cumple, porcentaje_cumplimiento, articulo, descripcion, pares_revisados, pares_con_violacion},
        "paridad_transversal": {cumple, porcentaje_cumplimiento, articulo, descripcion, mujeres, hombres, porcentaje_mujeres},
        "accion_indigena":     {cumple, porcentaje_cumplimiento, articulo, descripcion, registrado, requerido},
        "accion_discapacidad": {...igual que indigena...},
        "accion_juventud":     {...igual que indigena...},
        "accion_lgbtq":        {...igual que indigena...},
    }
    incumplimientos: list[Incumplimiento]
}

Incumplimiento {
    tipo: str                       # "PARIDAD_HORIZONTAL", "ACCION_INDIGENA", etc.
    descripcion: str                # Texto humano explicando la violación
    candidatos_afectados: list[str] # Nombres; puede ser [] para reglas agregadas como transversal
    articulo: str                   # Debe venir de constants/legislacion.py
    sugerencia: str                 # Acción concreta para subsanar
}
```

**Campos mínimos por criterio**: `cumple: bool`, `porcentaje_cumplimiento: float`, `articulo: str`, `descripcion: str`. Cada regla puede agregar campos extras (conteos, deltas), pero los mínimos son obligatorios.

## Patrón de tests

Los tests viven en `backend/tests/test_motor.py` (unitarios del motor) y `backend/tests/test_api.py` (integración HTTP con `TestClient`). Dos helpers clave del archivo de tests unitarios:

```python
make_candidatura(**overrides) -> Candidatura
# Defaults válidos (PAN, DIPUTADO_LOCAL, M, PROPIETARIO, posicion=1, etc.).
# Solo override los campos que te importan para el caso bajo prueba.

formula(posicion, distrito, cargo, genero_prop, genero_sup,
        nombre_prop=None, nombre_sup=None) -> list[Candidatura]
# Crea una fórmula propietario-suplente completa (2 candidaturas).
```

**Regla de oro al modificar candidaturas ya construidas**: usa `candidatura.model_copy(update={...})`, NO reconstruyas con `make_candidatura(...)`. Reconstruir pierde los ajustes de paridad horizontal/vertical que ya coordinaste. Ver `test_lista_perfecta_success` en `test_motor.py` para el patrón correcto:

```python
candidaturas[0] = candidaturas[0].model_copy(update={
    "nombre": "Propietario Indígena",
    "indigena": True,
    "fecha_nacimiento": date(2001, 3, 10),
})
```

Los 5 tests de referencia que debes mantener pasando:
1. `test_lista_perfecta_success` — SUCCESS, todos los criterios en verde
2. `test_paridad_vertical_violacion_danger` — DANGER por alternancia rota
3. `test_accion_discapacidad_faltante_warning` — WARNING por acción afirmativa faltante, paridad OK
4. `test_paridad_horizontal_violacion_danger` — DANGER por fórmula M-M
5. `test_csv_columna_faltante_422` — HTTPException 422 con mención del campo

## Cómo agregar una regla nueva (checklist)

1. **Constantes**: agrega artículo (`ART_*`) y umbral (`UMBRAL_*`) a `constants/legislacion.py`.
2. **Función**:
   - Si es acción afirmativa sobre un bool simple → llama a `_accion_afirmativa()` desde `validar()`.
   - Si tiene lógica derivada → crea `_mi_regla(candidaturas) -> tuple[dict, list[Incumplimiento]]`.
3. **Agregación**: incluye el criterio en el dict `criterios` dentro de `validar()`.
4. **Semáforo**: decide si la regla suma a `falla_paridad` o `falla_afirmativa`. No cambies la precedencia sin razón legal.
5. **Output shape**: agrega cualquier campo extra del criterio al contrato. Si cambia el shape visible, avisa al frontend.
6. **Tests**: mínimo 2 casos en `test_motor.py` — uno que cumple, uno que no. Si toca el endpoint, agrega test HTTP en `test_api.py`.
7. **Constantes de tests**: si usas un umbral nuevo en los tests, impórtalo desde `legislacion.py`, no lo copies.

## Errores comunes a evitar

- **Hardcodear strings legales** (`"Art. 233 LGIPE"`) en vez de importar `ART_PARIDAD_VERTICAL`. Rompe la single source of truth y obliga a editar múltiples archivos cuando cambia la legislación.
- **Olvidar que `NB` no participa en checks binarios**: siempre filtra con `if c.genero in ("M", "F")` antes de contar pares para paridad horizontal/vertical/transversal.
- **Evaluar propietarios y suplentes juntos en paridad vertical.** Art. 233 aplica a cada lista ordenada por separado — agrupa por `(partido, cargo, tipo)`, no solo `(partido, cargo)`.
- **Cambiar la precedencia DANGER > WARNING > SUCCESS.** Es una regla legal, no de UX.
- **Sumar fórmulas incompletas al denominador de paridad horizontal.** Solo se cuentan las fórmulas que tienen propietario Y suplente.
- **Usar `datetime.today()` para juventud.** Usa `ANIO_JUVENTUD_MIN`/`MAX` fijos — si cambias el año de referencia, actualiza las constantes, no la lógica.
- **Reconstruir candidaturas en tests con `make_candidatura()` cuando ya las modificaste.** Usa `model_copy(update={...})`.
