import pandas as pd
import re

ruta_archivo = r'C:\Users\fxb8co\Documents\Otros\PEP SINACOFT\PTGENST2025010603.txt'

# Leer archivo
with open(ruta_archivo, 'r', encoding='latin-1') as archivo:
    lineas = archivo.readlines()

registros = []

for linea in lineas:
    linea = linea.strip()

    # Separar RUT numérico inicial
    rut_match = re.match(r'^(\d+)', linea)
    if not rut_match:
        print(f"❌ RUT no encontrado: {linea}")
        continue

    rut_numerico = rut_match.group(1)
    rut_con_formato = rut_numerico[:-1] + '-' + rut_numerico[-1]

    # El resto de la línea
    resto = linea[len(rut_numerico):].strip()

    # Separar por 2 o más espacios
    partes = re.split(r'\s{2,}', resto)

    # Verificación mínima de 9 partes
    if len(partes) < 9:
        print(f"⚠️ Línea con menos de 9 partes, se rellenará: {linea}")
        while len(partes) < 9:
            partes.append('')

    # Asignar campos según posición
    apellido_paterno = partes[0]
    apellido_materno = partes[1]
    nombres1 = partes[2]
    apellido_paterno_2 = partes[3]
    apellido_materno_2 = partes[4]
    nombres2 = partes[5]
    institucion = partes[6]
    cargo = partes[7]

    # Fecha y tipo movimiento
    fecha = ''
    tipo_movimiento = ''
    if len(partes) >= 9:
        fecha_tipo = partes[8]
        if re.match(r'\d{4}/\d{2}/\d{2}\d{2}', fecha_tipo):
            fecha = fecha_tipo[:-2]
            tipo_movimiento = fecha_tipo[-2:]
        else:
            print(f"⚠️ Fecha y tipo mal formateado: {fecha_tipo}")

    # Columna 12: concatenación de apellido paterno + materno
    apellidos_combinados = f"{apellido_paterno} {apellido_materno}"

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

# Crear DataFrame
df = pd.DataFrame(registros, columns=[
    'RUT', 'Apellido Paterno', 'Apellido Materno', 'Nombres',
    'Nombres (2)', 'Apellido Paterno (2)', 'Apellido Materno (2)',
    'Institución', 'Cargo', 'Fecha', 'Tipo Movimiento', 'Apellidos'
])

# Exportar CSV
ruta_salida = r'C:\Users\fxb8co\Documents\salida_final.csv'
df.to_csv(ruta_salida, index=False, encoding='utf-8-sig')

print("✅ Archivo exportado correctamente a:", ruta_salida)
