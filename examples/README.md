# CSV de ejemplo

## `candidaturas_ejemplo.csv`

Datos ficticios, mínimos, para probar el flujo end-to-end rápido (10 candidaturas,
1 partido, con un incumplimiento de paridad vertical intencional).

## `oficial_*.csv` — datos reales del IEE Chihuahua

Extractos convertidos de la base oficial **"Candidaturas Registradas"** del
Proceso Electoral Local 2023-2024 del Instituto Estatal Electoral de Chihuahua:

<https://www.ieechihuahua.org.mx/_candidaturas_registradas_2024>
(archivo fuente: `Candidaturas Registradas.xlsx`, 7 678 registros).

| Archivo | Contenido |
|---|---|
| `oficial_diputaciones_mr_MORENA.csv` | Diputaciones de mayoría relativa postuladas por MORENA (20 candidaturas) |
| `oficial_diputaciones_rp_MC.csv` | Lista de diputaciones de representación proporcional de Movimiento Ciudadano (10) |
| `oficial_ayuntamiento_chihuahua_PAN.csv` | Regidurías (MR y RP) del Ayuntamiento de Chihuahua por el PAN (18) |

### Mapeo de columnas

| Columna del CSV | Origen en el XLSX oficial |
|---|---|
| `nombre` | `Nombre Completo` |
| `genero` | `Género` (`N` → `NB`) |
| `partido` | `Partido o Coalición` |
| `cargo` | `Cargo` |
| `tipo` | `Tipo Cargo` (`Propietario`/`Suplente` → mayúsculas) |
| `posicion` | `Cargo Numero` |
| `distrito` | `Ambito` |
| `indigena` / `discapacidad` / `lgbtq` | derivadas de `Accion Afirmativa` |

### ⚠️ `fecha_nacimiento` es sintética

La base pública del IEE **no incluye la fecha de nacimiento** de las candidaturas.
En estos archivos se generó una fecha determinista a partir del nombre (hash), con
~10 % de las personas en el rango de juventud (1997-2008). Sirve para ejercitar la
cuota de juventud del motor, pero **no corresponde a la edad real** de las personas.
