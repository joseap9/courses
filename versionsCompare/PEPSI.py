import pandas as pd
import re
import unicodedata

def limpiar_texto(texto):
    if not isinstance(texto, str):
        return texto
    texto = ''.join(c for c in texto if c.isprintable())
    texto = unicodedata.normalize('NFKC', texto)
    return texto

# --- ARCHIVO 1: Titulares ---
ruta_titulares = r'C:\Users\fxb8co\Documents\Otros\PEP SINACOFT\PTGENST2025010603.txt'
with open(ruta_titulares, 'r', encoding='latin-1') as archivo:
    lineas = archivo.readlines()

registros_titulares = []

for linea in lineas:
    linea = linea.strip()
    rut_match = re.match(r'^(\d+)', linea)
    if not rut_match:
        continue
    rut_numerico = rut_match.group(1)
    rut_con_formato = rut_numerico[:-1] + '-' + rut_numerico[-1]
    resto = linea[len(rut_numerico):].strip()
    partes = re.split(r'\s{2,}', resto)

    fecha = ''
    tipo_movimiento = ''
    if partes:
        posible_fecha = partes[-1]
        if re.match(r'\d{4}/\d{2}/\d{2}\d{2}', posible_fecha):
            fecha = posible_fecha[:-2]
            tipo_movimiento = posible_fecha[-2:]
            partes = partes[:-1]

    while len(partes) < 8:
        partes.append('')

    apellido_paterno       = partes[0]
    apellido_materno       = partes[1]
    nombres1               = partes[2]
    apellido_paterno_2     = partes[3]
    apellido_materno_2     = partes[4]
    nombres2               = partes[5]
    institucion            = partes[6]
    cargo                  = partes[7]
    apellidos_combinados = f"{apellido_paterno} {apellido_materno}".strip()

    registros_titulares.append([
        rut_con_formato,
        apellido_paterno,
        apellido_materno,
        nombres1,
        nombres2,
        apellido_paterno_2,
        apellido_materno_2,
        institucion,
        cargo,
        fecha,
        tipo_movimiento,
        apellidos_combinados
    ])

df_titulares = pd.DataFrame(registros_titulares, columns=[
    'RUT', 'Apellido Paterno', 'Apellido Materno', 'Nombres',
    'Nombres (2)', 'Apellido Paterno (2)', 'Apellido Materno (2)',
    'Institución', 'Cargo', 'Fecha', 'Tipo Movimiento', 'Apellidos'
])

# --- ARCHIVO 2: Parentesco ---
ruta_parentesco = r'C:\Users\fxb8co\Documents\Otros\PEP SINACOFT\PTGENRE2025010603.txt'
with open(ruta_parentesco, 'r', encoding='latin-1') as archivo:
    lineas = archivo.readlines()

registros_parentesco = []

for linea in lineas:
    linea = linea.strip()
    rut_matches = re.findall(r'^(\d+)(\d{1,})', linea)
    if not rut_matches:
        continue

    rut_titular = rut_matches[0][0]
    rut_pariente = rut_matches[0][1]
    rut_titular_fmt = rut_titular[:-1] + '-' + rut_titular[-1]
    rut_pariente_fmt = rut_pariente[:-1] + '-' + rut_pariente[-1]

    resto = linea[len(rut_titular + rut_pariente):].strip()
    partes = re.split(r'\s{2,}', resto)

    ult_campo = ''
    tipo_parentesco = ''
    fecha_mov = ''
    alta = ''
    if partes:
        ult_campo = partes[-1]
        if re.match(r'\d{2}\d{4}/\d{2}/\d{2}\d{2}', ult_campo):
            tipo_parentesco = ult_campo[:2]
            fecha_mov = ult_campo[2:12]
            alta = ult_campo[12:]
            partes = partes[:-1]

    while len(partes) < 6:
        partes.append('')

    apellido_paterno       = partes[0]
    apellido_materno       = partes[1]
    nombres1               = partes[2]
    apellido_paterno_2     = partes[3]
    apellido_materno_2     = partes[4]
    nombres2               = partes[5]
    apellidos_combinados = f"{apellido_paterno} {apellido_materno}".strip()

    registros_parentesco.append([
        rut_titular_fmt,
        rut_pariente_fmt,
        apellido_paterno,
        apellido_materno,
        nombres1,
        nombres2,
        apellido_paterno_2,
        apellido_materno_2,
        tipo_parentesco,
        fecha_mov,
        alta,
        apellidos_combinados
    ])

df_parentesco = pd.DataFrame(registros_parentesco, columns=[
    'RUT Titular', 'RUT Pariente', 'Apellido Paterno', 'Apellido Materno',
    'Nombres', 'Nombres (2)', 'Apellido Paterno (2)', 'Apellido Materno (2)',
    'Tipo Parentesco', 'Fecha Movimiento', 'Alta', 'Apellidos'
])

# --- ARCHIVO 3: Socios-Sociedades ---
ruta_socios = r'C:\Users\fxb8co\Documents\Otros\PEP SINACOFT\PTGENSS2025010603.txt'
with open(ruta_socios, 'r', encoding='latin-1') as archivo:
    lineas = archivo.readlines()

registros_socios = []

for linea in lineas:
    linea = linea.strip()
    rut_match = re.match(r'^(\d+)', linea)
    if not rut_match:
        continue

    rut_numerico = rut_match.group(1)
    rut_con_formato = rut_numerico[:-1] + '-' + rut_numerico[-1]
    resto = linea[len(rut_numerico):].strip()
    partes = re.split(r'\s{2,}', resto)

    fecha = ''
    tipo_movimiento = ''
    if partes:
        posible_fecha = partes[-1]
        if re.match(r'\d{4}/\d{2}/\d{2}\d{2}', posible_fecha):
            fecha = posible_fecha[:-2]
            tipo_movimiento = posible_fecha[-2:]
            partes = partes[:-1]

    while len(partes) < 8:
        partes.append('')

    apellido_paterno       = partes[0]
    apellido_materno       = partes[1]
    nombres1               = partes[2]
    apellido_paterno_2     = partes[3]
    apellido_materno_2     = partes[4]
    nombres2               = partes[5]
    institucion            = partes[6]
    cargo                  = partes[7]
    apellidos_combinados = f"{apellido_paterno} {apellido_materno}".strip()

    registros_socios.append([
        rut_con_formato,
        apellido_paterno,
        apellido_materno,
        nombres1,
        nombres2,
        apellido_paterno_2,
        apellido_materno_2,
        institucion,
        cargo,
        fecha,
        tipo_movimiento,
        apellidos_combinados
    ])

df_socios = pd.DataFrame(registros_socios, columns=[
    'RUT', 'Apellido Paterno', 'Apellido Materno', 'Nombres',
    'Nombres (2)', 'Apellido Paterno (2)', 'Apellido Materno (2)',
    'Sociedad', 'Cargo', 'Fecha', 'Tipo Movimiento', 'Apellidos'
])

# --- LIMPIEZA ---
df_titulares = df_titulares.applymap(limpiar_texto)
df_parentesco = df_parentesco.applymap(limpiar_texto)
df_socios = df_socios.applymap(limpiar_texto)

# --- Exportar a Excel ---
ruta_salida_excel = r'C:\Users\fxb8co\Documents\salida_final.xlsx'
with pd.ExcelWriter(ruta_salida_excel, engine='openpyxl') as writer:
    df_titulares.to_excel(writer, sheet_name='Titulares', index=False)
    df_parentesco.to_excel(writer, sheet_name='Parentesco', index=False)
    df_socios.to_excel(writer, sheet_name='SOCIOS_SOCIEDADES', index=False)

print("✅ Exportación completada con las tres hojas.")
