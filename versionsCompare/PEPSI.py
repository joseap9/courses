import pandas as pd
import re

ruta_archivo = r'C:\Users\fxb8co\Documents\Otros\PEP SINACOFT\PTGENST2025010603.txt'

# Leer el archivo
with open(ruta_archivo, 'r', encoding='latin-1') as archivo:
    lineas = archivo.readlines()

registros = []

for linea in lineas:
    linea = linea.strip()

    # 1. Extraer RUT numérico del inicio
    rut_match = re.match(r'^(\d+)', linea)
    if not rut_match:
        print(f"❌ RUT no encontrado: {linea}")
        continue

    rut_numerico = rut_match.group(1)
    rut_con_formato = rut_numerico[:-1] + '-' + rut_numerico[-1]

    # 2. Resto de la línea (sin el RUT)
    resto = linea[len(rut_numerico):].strip()

    # 3. Separar el resto por 2 o más espacios
    partes = re.split(r'\s{2,}', resto)

    # 4. Intentar extraer fecha y tipo de movimiento del final
    fecha = ''
    tipo_movimiento = ''
    if partes:
        posible_fecha = partes[-1]
        if re.match(r'\d{4}/\d{2}/\d{2}\d{2}', posible_fecha):
            fecha = posible_fecha[:-2]
            tipo_movimiento = posible_fecha[-2:]
            partes = partes[:-1]  # eliminar fecha+tipo del arreglo
        else:
            print(f"⚠️ Fecha/tipo movimiento mal formado o ausente: {posible_fecha}")

    # 5. Rellenar campos faltantes
    while len(partes) < 8:
        partes.append('')

    # Asignar valores con protección
    apellido_paterno       = partes[0]
    apellido_materno       = partes[1]  # puede estar vacío
    nombres1               = partes[2]
    apellido_paterno_2     = partes[3]
    apellido_materno_2     = partes[4]  # puede estar vacío
    nombres2               = partes[5]
    institucion            = partes[6]
    cargo                  = partes[7]

    # 6. Apellidos combinados (columna 12)
    apellidos_combinados = f"{apellido_paterno} {apellido_materno}".strip()

    registros.append([
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

# 7. Crear DataFrame
df = pd.DataFrame(registros, columns=[
    'RUT', 'Apellido Paterno', 'Apellido Materno', 'Nombres',
    'Nombres (2)', 'Apellido Paterno (2)', 'Apellido Materno (2)',
    'Institución', 'Cargo', 'Fecha', 'Tipo Movimiento', 'Apellidos'
])

# 8. Exportar CSV
ruta_salida = r'C:\Users\fxb8co\Documents\salida_final.csv'
df.to_csv(ruta_salida, index=False, encoding='utf-8-sig')

print("✅ Exportación completada. Total de registros:", len(df))
