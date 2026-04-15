# Fuente única de verdad para artículos legales y umbrales numéricos.
# Ningún otro módulo debe tener strings legales ni números mágicos.

# --- Artículos legales ---
ART_PARIDAD_HORIZONTAL  = "Art. 234 LGIPE"
ART_PARIDAD_VERTICAL    = "Art. 233 LGIPE"
ART_PARIDAD_TRANSVERSAL = "Art. 232 LGIPE"
ART_ACCION_INDIGENA     = "Art. 14 LGIPE"
ART_ACCION_DISCAPACIDAD = "Art. 14 LGIPE"
ART_ACCION_JUVENTUD     = "Art. 14 LGIPE"
ART_ACCION_LGBTQ        = "Art. 14 LGIPE"

# --- Umbrales numéricos (fracciones, no porcentajes) ---
UMBRAL_TRANSVERSAL_TOLERANCIA = 0.05  # ±5% de tolerancia en paridad 50/50
UMBRAL_INDIGENA     = 0.03            # 3% mínimo de candidaturas indígenas
UMBRAL_DISCAPACIDAD = 0.01            # 1% mínimo de candidaturas con discapacidad
UMBRAL_JUVENTUD     = 0.01            # 1% mínimo de candidaturas de jóvenes
UMBRAL_LGBTQ        = 0.01            # 1% mínimo de candidaturas LGBTQ+

# --- Rango de nacimiento para "juventud" (18-29 años al 2026) ---
ANIO_JUVENTUD_MIN = 1997
ANIO_JUVENTUD_MAX = 2008

# --- Valores permitidos ---
GENEROS_VALIDOS = {"M", "F", "NB"}
TIPOS_VALIDOS   = {"PROPIETARIO", "SUPLENTE"}

COLUMNAS_REQUERIDAS = [
    "nombre",
    "genero",
    "partido",
    "cargo",
    "tipo",
    "posicion",
    "distrito",
    "indigena",
    "discapacidad",
    "fecha_nacimiento",
    "lgbtq",
]
