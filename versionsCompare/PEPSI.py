import pandas as pd
import re
import unicodedata

# --- RUTAS DE ARCHIVOS ---
ruta_titulares = r'C:\Users\fxb8co\Documents\Otros\PEP SINACOFT\PTGENST2025010603.txt'
ruta_parentesco = r'C:\Users\fxb8co\Documents\Otros\PEP SINACOFT\PTGENRE2025010603.txt'
ruta_socios = r'C:\Users\fxb8co\Documents\Otros\PEP SINACOFT\PTGENSS2025010603.txt'
ruta_salida_excel = r'C:\Users\fxb8co\Documents\salida_final.xlsx'

# --- FUNCIONES ---
def limpiar_texto(texto):
    if not isinstance(texto, str):
        return texto
    texto = ''.join(c for c in texto if c.isprintable())
    texto = unicodedata.normalize('NFKC', texto)
    return texto

def formatear_rut(rut):
    rut = rut.lstrip('0')
    if len(rut) < 2:
        return rut
    return rut[:-1] + '-' + rut[-1]

def extraer_ruts_concatenados(cadena):
    cadena = cadena.lstrip('0')
    for i in range(2, len(cadena)-1):
        rut1_raw = cadena[:i]
        rut2_raw = cadena[i:]
        if len(rut1_raw) >= 2 and len(rut2_raw) >= 2:
            rut1 = formatear_rut(rut1_raw)
            rut2 = formatear_rut(rut2_raw)
            return rut1, rut2
    return None, None

# --- TITULARES ---
with open(ruta_titulares, 'r', encoding='latin-1') as archivo:
    lineas = archivo.readlines()

registros_titulares = []

for linea in lineas:
    linea = linea.strip()
    rut_match = re.match(r'^(\d+)', linea)
    if not rut_match:
        print(f"❌ RUT no encontrado: {linea}")
        continue

    rut_numerico = rut_match.group(1)
    rut_con_formato = formatear_rut(rut_numerico)
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
        else:
            print(f"⚠️ Fecha/tipo movimiento mal formado o ausente: {posible_fecha}")

    while len(partes) < 8:
        partes.append('')

    apellido_paterno     = partes[0]
    apellido_materno     = partes[1]
    nombres1             = partes[2]
    apellido_paterno_2   = partes[3]
    apellido_materno_2   = partes[4]
    nombres2             = partes[5]
    institucion          = partes[6]
    cargo                = partes[7]
    nombre_completo      = f"{nombres1} {apellido_paterno} {apellido_materno}".strip()

    registros_titulares.append([
        rut_con_formato,
        apellido_paterno,
        apellido_materno,
        nombres1,
        apellido_paterno_2,
        apellido_materno_2,
        nombres2,
        nombre_completo,
        institucion,
        cargo,
        fecha,
        tipo_movimiento
    ])

df_titulares = pd.DataFrame(registros_titulares, columns=[
    'RUT', 'Apellido Paterno', 'Apellido Materno', 'Nombres',
    'Apellido Paterno (2)', 'Apellido Materno (2)', 'Nombres (2)', 'Nombre Completo',
    'Institución', 'Cargo', 'Fecha', 'Tipo Movimiento'
])

# --- PARENTESCO ---
with open(ruta_parentesco, 'r', encoding='latin-1') as archivo:
    lineas = archivo.readlines()

registros_parentesco = []

for linea in lineas:
    linea = linea.strip()
    rut_match = re.match(r'^(\d+)', linea)
    if not rut_match:
        print(f"❌ RUTs no encontrados: {linea}")
        continue

    cadena_ruts = rut_match.group(1)
    rut_titular, rut_pariente = extraer_ruts_concatenados(cadena_ruts)
    if not rut_titular or not rut_pariente:
        print(f"❌ No se pudo separar correctamente los RUTs: {cadena_ruts}")
        continue

    resto = linea[len(cadena_ruts):].strip()
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
        else:
            print(f"⚠️ Campo parentesco mal formado o ausente: {ult_campo}")

    while len(partes) < 6:
        partes.append('')

    apellido_paterno     = partes[0]
    apellido_materno     = partes[1]
    nombres1             = partes[2]
    apellido_paterno_2   = partes[3]
    apellido_materno_2   = partes[4]
    nombres2             = partes[5]
    nombre_completo      = f"{nombres1} {apellido_paterno} {apellido_materno}".strip()

    registros_parentesco.append([
        rut_titular,
        rut_pariente,
        apellido_paterno,
        apellido_materno,
        nombres1,
        apellido_paterno_2,
        apellido_materno_2,
        nombres2,
        nombre_completo,
        tipo_parentesco,
        fecha_mov,
        alta
    ])

df_parentesco = pd.DataFrame(registros_parentesco, columns=[
    'RUT Titular', 'RUT Pariente', 'Apellido Paterno', 'Apellido Materno',
    'Nombres', 'Apellido Paterno (2)', 'Apellido Materno (2)', 'Nombres (2)',
    'Nombre Completo', 'Tipo Parentesco', 'Fecha Movimiento', 'Alta'
])

# --- SOCIOS-SOCIEDADES ---
with open(ruta_socios, 'r', encoding='latin-1') as archivo:
    lineas = archivo.readlines()

registros_socios = []

for linea in lineas:
    linea = linea.strip()
    rut_match = re.match(r'^(\d+)', linea)
    if not rut_match:
        print(f"❌ RUTs no encontrados en SOCIOS: {linea}")
        continue

    cadena_ruts = rut_match.group(1)
    rut_titular, rut_socio = extraer_ruts_concatenados(cadena_ruts)
    if not rut_titular or not rut_socio:
        print(f"❌ No se pudo separar correctamente los RUTs en SOCIOS: {cadena_ruts}")
        continue

    resto = linea[len(cadena_ruts):].strip()
    partes = re.split(r'\s{2,}', resto)

    campo_final = ''
    a = ''
    fecha = ''
    c = ''
    if partes:
        campo_final = partes[-1]
        if re.match(r'\d{2}\d{4}/\d{2}/\d{2}\d{2}', campo_final):
            a = campo_final[:2]
            fecha = campo_final[2:12]
            c = campo_final[12:]
            partes = partes[:-1]
        else:
            print(f"⚠️ Campo A/FECHA/C mal formado o ausente: {campo_final}")

    while len(partes) < 6:
        partes.append('')

    apellido_paterno     = partes[0]
    apellido_materno     = partes[1]
    nombres1             = partes[2]
    apellido_paterno_2   = partes[3]
    apellido_materno_2   = partes[4]
    nombres2             = partes[5]

    registros_socios.append([
        rut_titular,
        rut_socio,
        apellido_paterno,
        apellido_materno,
        nombres1,
        apellido_paterno_2,
        apellido_materno_2,
        nombres2,
        a,
        fecha,
        c
    ])

df_socios = pd.DataFrame(registros_socios, columns=[
    'RUT Titular', 'RUT Socio', 'Apellido Paterno', 'Apellido Materno',
    'Nombres', 'Apellido Paterno (2)', 'Apellido Materno (2)', 'Nombres (2)',
    'A', 'Fecha', 'C'
])

# --- LIMPIEZA ---
df_titulares = df_titulares.applymap(limpiar_texto)
df_parentesco = df_parentesco.applymap(limpiar_texto)
df_socios = df_socios.applymap(limpiar_texto)

# --- EXPORTACIÓN A EXCEL ---
with pd.ExcelWriter(ruta_salida_excel, engine='openpyxl') as writer:
    df_titulares.to_excel(writer, sheet_name='Titulares', index=False)
    df_parentesco.to_excel(writer, sheet_name='Parentesco', index=False)
    df_socios.to_excel(writer, sheet_name='SOCIOS_SOCIEDADES', index=False)

# --- RESUMEN DE FILAS ---
print("✅ Exportación completada con las tres hojas.")
print(f"📄 Filas Titulares: {len(df_titulares)}")
print(f"📄 Filas Parentesco: {len(df_parentesco)}")
print(f"📄 Filas Socios-Sociedades: {len(df_socios)}")
