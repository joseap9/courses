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
        return ''
    return rut[:-1] + '-' + rut[-1]

def dividir_ruts_por_10(cadena):
    rut1_raw = cadena[:10]
    rut2_raw = cadena[10:]
    rut1 = formatear_rut(rut1_raw)
    rut2 = formatear_rut(rut2_raw) if rut2_raw else ''
    return rut1, rut2

# --- ARCHIVO 1: Titulares ---
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
        else:
            print(f"⚠️ Fecha/tipo movimiento mal formado o ausente: {posible_fecha}")

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
with open(ruta_parentesco, 'r', encoding='latin-1') as archivo:
    lineas = archivo.readlines()

registros_parentesco = []

for linea in lineas:
    linea = linea.strip()
    rut_matches = re.findall(r'^(\d+)(\d{1,})', linea)
    if not rut_matches:
        print(f"❌ RUTs no encontrados: {linea}")
        continue

    rut_titular_raw = rut_matches[0][0]
    rut_pariente_raw = rut_matches[0][1]
    rut_titular_fmt, rut_pariente_fmt = dividir_ruts_por_10(rut_titular_raw + rut_pariente_raw)

    resto = linea[len(rut_titular_raw + rut_pariente_raw):].strip()
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
with open(ruta_socios, 'r', encoding='latin-1') as archivo:
    lineas = archivo.readlines()

registros_socios = []

for linea in lineas:
    linea = linea.strip()
    rut_matches = re.findall(r'^(\d+)(\d{1,})', linea)
    if not rut_matches:
        print(f"❌ RUTs no encontrados en SOCIOS: {linea}")
        continue

    rut_titular_raw = rut_matches[0][0]
    rut_socio_raw = rut_matches[0][1]
    rut_titular_fmt, rut_socio_fmt = dividir_ruts_por_10(rut_titular_raw + rut_socio_raw)

    resto = linea[len(rut_titular_raw + rut_socio_raw):].strip()
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
        rut_titular_fmt,
        rut_socio_fmt,
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

# --- LIMPIEZA Y EXPORTACIÓN ---
df_titulares = df_titulares.applymap(limpiar_texto)
df_parentesco = df_parentesco.applymap(limpiar_texto)
df_socios = df_socios.applymap(limpiar_texto)

with pd.ExcelWriter(ruta_salida_excel, engine='openpyxl') as writer:
    df_titulares.to_excel(writer, sheet_name='Titulares', index=False)
    df_parentesco.to_excel(writer, sheet_name='Parentesco', index=False)
    df_socios.to_excel(writer, sheet_name='SOCIOS_SOCIEDADES', index=False)

# --- RESUMEN ---
print("✅ Exportación completada con las tres hojas.")
print(f"📄 Filas Titulares: {len(df_titulares)}")
print(f"📄 Filas Parentesco: {len(df_parentesco)}")
print(f"📄 Filas Socios-Sociedades: {len(df_socios)}")
first(split(trim(substring(outputs('Concat_Body_Text'), add(indexOf(outputs('Concat_Body_Text'), 'Área de Cumplimiento'), length('Área de Cumplimiento'))), 20), ' '))
